"""Local trial reference and suitability decisions. Recordings stay read-only."""

import argparse
import csv
import hashlib
import io
import json
import mimetypes
import os
import re
import sqlite3
import sys
import wave
from collections import defaultdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from brainvision_to_praat import linked_file, read_brainvision_ini, read_markers
from suitability import SuitabilityStore, suitability_csv
from annotations import AnnotationReader, analysis_csv
from recording_library import RecordingLibrary, bundle, file_hash
from import_jobs import ImportJobs


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def stimulus_code(marker):
    match = re.fullmatch(r"S\s*(\d+)", marker["description"].strip())
    if marker["type"] != "Stimulus" or not match:
        raise ValueError(f"Unexpected stimulus marker: {marker}")
    return int(match[1])


def match_trigger_sequence(markers, logged):
    recorded = [m for m in markers if m["type"] == "Stimulus"]
    sent = [row for row in logged if row["serial_sent"] == "1"]
    if len(recorded) != len(sent):
        raise ValueError(f"Trigger counts disagree: EEG {len(recorded)}, sent log {len(sent)}. No mapping made.")
    linked = []
    for index, (marker, row) in enumerate(zip(recorded, sent), 1):
        code = stimulus_code(marker)
        if code != int(row["trigger_code"]):
            raise ValueError(f"Trigger sequence mismatch at {index}: EEG S {code}, log S {row['trigger_code']}. No mapping made.")
        linked.append({
            "marker_id": marker["marker_id"], "code": code, "display": f"S {code}",
            "time": marker["onset_seconds"], "sample_1based": marker["position_1based"],
            "label": row["label"], "log_index": int(row["trigger_index"]),
        })
    return linked


def playback_window(onset_sample, stop_sample, sample_rate, sample_count, padding=3):
    if not 0 <= onset_sample < stop_sample <= sample_count:
        raise ValueError("Trial recording bounds are outside full_session.wav.")
    if padding < 0:
        raise ValueError("Playback padding cannot be negative.")
    pad_samples = round(padding * sample_rate)
    first = max(0, onset_sample - pad_samples)
    last = min(sample_count, stop_sample + pad_samples)
    return {
        "start_sample": first, "end_sample": last,
        "start": first / sample_rate, "end": last / sample_rate,
        "trial_start": onset_sample / sample_rate, "trial_end": stop_sample / sample_rate,
        "before_seconds": (onset_sample - first) / sample_rate,
        "after_seconds": (last - stop_sample) / sample_rate,
    }


def attach_full_playback(trials, segment_rows, full_path, padding=3):
    segments = {}
    for row in segment_rows:
        if row["stem"] in segments:
            raise ValueError(f"Duplicate recording segment: {row['stem']}")
        segments[row["stem"]] = row
    with wave.open(str(full_path), "rb") as full:
        sample_rate, sample_count = full.getframerate(), full.getnframes()
        verified = 0
        for trial in trials:
            row = segments.get(Path(trial["audio_filename"]).stem)
            if not row or row["status"] != "written":
                raise ValueError(f"No written recording segment for {trial['id']}.")
            onset, stop = int(row["onset_sample"]), int(row["stop_sample"])
            trial["playback"] = playback_window(onset, stop, sample_rate, sample_count, padding)
            clip_start, clip_end = int(row["clip_start_sample"]), int(row["clip_end_sample"])
            if not 0 <= clip_start < clip_end <= sample_count or clip_end - clip_start != int(row["n_frames"]):
                raise ValueError(f"Invalid clip bounds for {trial['id']}.")
            with wave.open(trial["audio_path"], "rb") as clip:
                if (clip.getframerate(), clip.getnchannels(), clip.getsampwidth(), clip.getnframes()) != (sample_rate, full.getnchannels(), full.getsampwidth(), clip_end - clip_start):
                    raise ValueError(f"Trial WAV format differs from full_session.wav: {trial['id']}.")
                full.setpos(clip_start)
                if clip.readframes(clip.getnframes()) != full.readframes(clip_end - clip_start):
                    raise ValueError(f"Logged clip samples do not match full_session.wav: {trial['id']}.")
            verified += 1
    return {"filename": full_path.name, "path": str(full_path), "sample_rate": sample_rate,
            "sample_count": sample_count, "duration": sample_count / sample_rate,
            "padding_seconds": padding, "verified_segments": verified}


def build_session(config):
    vhdr, audio_dir, experiment = (Path(config[key]).resolve() for key in ("vhdr", "audio_dir", "experiment_dir"))
    header = read_brainvision_ini(vhdr)
    common = header["Common Infos"]
    sfreq = 1e6 / float(common["SamplingInterval"])
    with wave.open(str(Path(config["stimtrak_wav"])), "rb") as wav:
        if wav.getframerate() != sfreq:
            raise ValueError("StimTrak WAV sample rate differs from the EEG header.")
        count = wav.getnframes()
    data_file = linked_file(vhdr, common["DataFile"])
    widths = {"INT_16": 2, "INT_32": 4, "IEEE_FLOAT_32": 4}
    binary_format = header["Binary Infos"]["BinaryFormat"].upper()
    if common.get("DataFormat", "").upper() != "BINARY" or common.get("DataOrientation", "").upper() != "MULTIPLEXED" or binary_format not in widths:
        raise ValueError("Unsupported EEG layout; cannot verify the StimTrak sample count.")
    frame_bytes = int(common["NumberOfChannels"]) * widths[binary_format]
    sample_count, remainder = divmod(data_file.stat().st_size, frame_bytes)
    if remainder or count != sample_count:
        raise ValueError("StimTrak WAV sample count differs from the original EEG recording.")
    marker_file = linked_file(vhdr, common["MarkerFile"])
    markers = read_markers(marker_file, count, int(common["NumberOfChannels"]), sfreq)
    log_path = audio_dir / "eeg_triggers.csv"
    logged = rows(log_path)
    triggers = match_trigger_sequence(markers, logged)
    assets = {}
    sources = [vhdr, marker_file, log_path]

    def asset(path, prefix):
        path = path.resolve()
        if not path.is_file():
            raise ValueError(f"Required {prefix} file missing: {path}")
        key = prefix + "-" + hashlib.sha256(str(path).encode()).hexdigest()[:20]
        assets[key] = path
        return "/media/" + key

    main_pattern = re.compile(r"(.+)_isolated_main_l(\d+)_trial(\d+)_imageset(\d+)_cond_(it|tr)\.wav", re.I)
    recordings = {}
    participant = None
    list_number = None
    for wav in sorted(audio_dir.glob("*.wav")):
        match = main_pattern.fullmatch(wav.name)
        if not match:
            continue
        tag, listing, number, image_set, condition = match.groups()
        if participant is not None and (tag != participant or int(listing) != list_number):
            raise ValueError("Mixed participants or lists in the audio folder.")
        participant, list_number = tag, int(listing)
        number = int(number)
        if number in recordings:
            raise ValueError(f"Duplicate WAV for trial {number}.")
        recordings[number] = (wav, int(image_set), condition.lower())
    if not recordings:
        raise ValueError("No matching PsychoPy main trial WAVs found.")

    condition_path = experiment / "Conds" / f"isolated_main_list{list_number}_all_120.csv"
    sources.append(condition_path)
    conditions = {}
    for row in rows(condition_path):
        item = int(row["item_trigger"])
        if item in conditions:
            raise ValueError(f"Ambiguous item trigger S {item} in the condition table.")
        conditions[item] = row
    grouped = defaultdict(dict)
    for trigger in triggers:
        match = re.fullmatch(r"isolated_trial(\d+)_(target_onset|condition_\d+|item\d+|end)", trigger["label"])
        if match:
            number, role = int(match[1]), match[2]
            role = "condition" if role.startswith("condition") else "item" if role.startswith("item") else role
            if role in grouped[number]:
                raise ValueError(f"Duplicate {role} marker for trial {number}.")
            trigger["role"] = role
            trigger["trial_id"] = f"main-{number:03d}"
            grouped[number][role] = trigger
    if set(recordings) != set(grouped):
        raise ValueError("The main WAV trial numbers and logged EEG trials do not agree.")

    trials = []
    for number, group in sorted(grouped.items()):
        if set(group) != {"target_onset", "condition", "item", "end"}:
            raise ValueError(f"Incomplete trigger group for trial {number}.")
        if group["target_onset"]["code"] != 200 or group["end"]["code"] != 202:
            raise ValueError(f"Unexpected onset/end codes in trial {number}.")
        item = group["item"]["code"]
        if item not in conditions:
            raise ValueError(f"No image-table entry for S {item}.")
        condition = conditions[item]
        wav, image_set, transitivity = recordings[number]
        if int(condition["dataset_number"]) != image_set or condition["condition_id"].split("_")[0] != transitivity:
            raise ValueError(f"WAV metadata disagrees with picture table for trial {number}.")
        if int(condition["condition_trigger"]) != group["condition"]["code"]:
            raise ValueError(f"Condition trigger disagrees with picture table for trial {number}.")
        ordered = [group[role] for role in ("target_onset", "condition", "item", "end")]
        if any(b["time"] <= a["time"] for a, b in zip(ordered, ordered[1:])):
            raise ValueError(f"Trigger order invalid for trial {number}.")
        picture = (experiment / condition["target_image"]).resolve()
        trials.append({
            "id": f"main-{number:03d}", "kind": "main", "number": number,
            "image_set": image_set, "stimulus_set": int(condition["stimulus_set"]),
            "condition": condition["condition_id"], "scene": condition["dataset_label"].replace("_", " "),
            "image": asset(picture, "picture"), "image_path": str(picture),
            "image_filename": picture.name, "image_source": "Item trigger + experiment condition table",
            "audio": asset(wav, "audio"), "audio_filename": wav.name, "audio_path": str(wav),
            "triggers": ordered, "start": ordered[0]["time"], "end": ordered[-1]["time"],
            "item": item,
        })

    practice_path = experiment / "Conds" / "isolated_practice.csv"
    sources.append(practice_path)
    practice_rows = {int(row["practice_index"]): row for row in rows(practice_path)}
    for wav in sorted(audio_dir.glob(f"{participant}_practice_*_pic01.wav")):
        match = re.fullmatch(re.escape(participant) + r"_practice_(\d+)_pic01\.wav", wav.name)
        if not match:
            continue
        number = int(match[1])
        row = practice_rows.get(number)
        if not row:
            raise ValueError(f"No practice-table entry for practice {number}.")
        picture = (experiment / row["target_image"]).resolve()
        trials.append({
            "id": f"practice-{number:02d}", "kind": "practice", "number": number,
            "scene": row["target_role"].replace("_", " "), "condition": "practice",
            "image": asset(picture, "picture"), "image_path": str(picture), "image_filename": picture.name,
            "image_source": "Sequential practice table; no EEG trial triggers",
            "audio": asset(wav, "audio"), "audio_filename": wav.name, "audio_path": str(wav),
            "triggers": [], "start": None, "end": None, "item": None,
        })
    for trigger in triggers:
        trigger.setdefault("role", "session")
        trigger.setdefault("trial_id", None)
    full_path = (audio_dir / "full_session.wav").resolve()
    segments_path = audio_dir / "recording_segments.csv"
    full_recording = attach_full_playback(trials, rows(segments_path), full_path)
    full_recording["audio"] = asset(full_path, "full-audio")
    sources.extend([segments_path, full_path])
    source_records = [{"path": str(path), "sha256": file_hash(path)} for path in sources]
    # Content identity keeps decisions distinct while allowing recordings to be relocated.
    identity = [source_records[index]["sha256"] for index in (0, 1, 2, len(source_records) - 1)]
    session_id = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
    return {
        "participant": participant, "list": list_number, "recording": vhdr.stem,
        "session_id": session_id,
        "sample_rate": sfreq, "duration": count / sfreq, "trials": trials, "triggers": triggers,
        "full_recording": full_recording,
        "validation": {"matched_triggers": len(triggers), "main_trials": len(grouped),
                       "practice_trials": len(trials) - len(grouped),
                       "unsent_log_entries": sum(row["serial_sent"] != "1" for row in logged)},
        "sources": source_records,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }, assets


def byte_range(header, size):
    if not header:
        return 0, size - 1, False
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", header)
    if not match or (not match[1] and not match[2]):
        raise ValueError("Invalid range")
    if not match[1]:
        suffix = int(match[2])
        if suffix <= 0:
            raise ValueError("Invalid suffix")
        start, end = max(0, size - suffix), size - 1
    else:
        start = int(match[1])
        end = min(int(match[2]), size - 1) if match[2] else size - 1
    if start >= size or start > end:
        raise ValueError("Unsatisfiable range")
    return start, end, True


def library_counts(library, store):
    counts = {"itr": 0, "tr_erg": 0, "tr_zero": 0}
    entries = library.listing()["sessions"]
    for entry in entries:
        session_id = entry["session_id"]
        loaded = library.get(session_id)
        current = loaded["session"]
        annotations = loaded["reader"].read()
        if annotations["state"] != "ready":
            raise ValueError(f"{current['recording']}: {annotations['message']}")
        decisions = store.read(session_id)
        ergative = store.read_flags(session_id, "ergative")
        for trial in current["trials"]:
            if trial["kind"] != "main" or decisions.get(trial["id"], {}).get("unsuitable", False):
                continue
            annotation = annotations["trials"][trial["id"]]
            if (annotation["status"] != "ok" or annotation["onset_count"] != 1
                    or annotation["speech_onset_eeg_s"] is None or not annotation["transcription"].strip()):
                continue
            if trial["condition"].startswith("it_"):
                counts["itr"] += 1
            elif trial["condition"].startswith("tr_"):
                key = "tr_erg" if ergative.get(trial["id"], {}).get("marked", False) else "tr_zero"
                counts[key] += 1
            else:
                raise ValueError(f"Unknown main-trial condition in {current['recording']}: {trial['condition']}")
    return {"counts": counts, "recordings": len(entries), "updated_at_utc": datetime.now(timezone.utc).isoformat()}


def handler_class(session, assets, config, store, annotation_reader=None, library=None, imports=None):
    annotation_reader = annotation_reader or AnnotationReader(config.get("textgrid"), session,
                                                              ROOT / "annotation_snapshots" / session["session_id"][:20])
    library = library or RecordingLibrary(ROOT / "recordings", bundle(session, assets, config,
                                         ROOT / "annotation_snapshots", annotation_reader),
                                         build_session, ROOT / "annotation_snapshots")
    files = {"/": ROOT / "index.html", "/app.js": ROOT / "app.js", "/style.css": ROOT / "style.css",
             "/lucide.js": Path(config["lucide"])}

    class Handler(BaseHTTPRequestHandler):
        def permitted(self, writing=False):
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            origins = {f"http://{host}" for host in allowed}
            origin = self.headers.get("Origin")
            if self.headers.get("Host") not in allowed or (origin and origin not in origins) or (writing and origin not in origins):
                self.send_error(403)
                return False
            return True

        def send_json(self, value, status=200, head=False):
            payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            try:
                self.end_headers()
                if not head:
                    self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def do_POST(self):
            if not self.permitted(writing=True):
                return
            path = urlsplit(self.path).path
            if path not in ("/api/suitability", "/api/ergative", "/api/need-help", "/api/import"):
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8192 or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise ValueError("Expected a small JSON request.")
                value = json.loads(self.rfile.read(length))
                if path == "/api/import":
                    if imports is None:
                        raise ValueError("Imports are not enabled in this server.")
                    self.send_json(imports.start(value), status=202)
                    return
                field = "ergative" if path == "/api/ergative" else "need_help" if path == "/api/need-help" else "unsuitable"
                if not isinstance(value, dict) or set(value) != {"session_id", "trial_id", field}:
                    raise ValueError(f"Expected session_id, trial_id and {field}.")
                active = library.get(self.requested_session())
                current = active["session"]
                if value["session_id"] != current["session_id"]:
                    self.send_json({"error": "Session changed. Refresh the page before saving."}, status=409)
                    return
                trial = next((trial for trial in current["trials"] if trial["id"] == value["trial_id"]), None)
                if not isinstance(value["trial_id"], str) or trial is None:
                    raise ValueError("Unknown trial.")
                if field == "ergative":
                    if not any(t["role"] == "condition" and t["code"] == 1 for t in trial.get("triggers", [])) or not trial["condition"].startswith("tr_"):
                        raise ValueError("Ergative coding is available only for S 1 transitive trials.")
                    decision = store.set_flag(current["session_id"], value["trial_id"], field, value[field])
                elif field == "need_help":
                    decision = store.set_flag(current["session_id"], value["trial_id"], field, value[field])
                else:
                    decision = store.set(current["session_id"], value["trial_id"], value[field])
                self.send_json({"trial_id": value["trial_id"], "decision": decision})
            except (ValueError, UnicodeDecodeError, KeyError) as error:
                self.send_json({"error": str(error)}, status=400)
            except (OSError, sqlite3.Error):
                self.send_json({"error": "Could not save the trial decision."}, status=500)

        def requested_session(self):
            values = parse_qs(urlsplit(self.path).query).get("session", [])
            if len(values) > 1:
                raise ValueError("Specify one recording.")
            return values[0] if values else None

        def do_HEAD(self):
            self.send_content(head=True)

        def do_GET(self):
            self.send_content(head=False)

        def send_content(self, head=False):
            if not self.permitted():
                return
            path = urlsplit(self.path).path
            if path == "/api/sessions":
                try:
                    self.send_json(library.listing(), head=head)
                except (ValueError, OSError) as error:
                    self.send_json({"error": str(error)}, status=500, head=head)
                return
            if path == "/api/import-defaults":
                defaults = json.loads((ROOT / "pipeline_config.json").read_text(encoding="utf-8"))
                self.send_json({"experiment_dir": defaults["default_experiment_dir"], "channel": defaults["default_channel"]}, head=head)
                return
            if path == "/api/library-counts":
                try:
                    self.send_json(library_counts(library, store), head=head)
                except (ValueError, KeyError, OSError, sqlite3.Error) as error:
                    self.send_json({"error": f"Overall counts unavailable; no recordings skipped: {error}"}, status=409, head=head)
                return
            if path.startswith("/api/import/"):
                try:
                    if imports is None:
                        raise KeyError("Imports unavailable.")
                    self.send_json(imports.get(path.removeprefix("/api/import/")), head=head)
                except KeyError as error:
                    self.send_json({"error": str(error)}, status=404, head=head)
                return
            if path in ("/api/session", "/api/annotations", "/api/suitability.csv", "/api/analysis.csv"):
                try:
                    active = library.get(self.requested_session())
                    current = active["session"]
                    reader = active["reader"]
                except (ValueError, KeyError, OSError) as error:
                    self.send_json({"error": str(error)}, status=404, head=head)
                    return
            if path == "/api/session":
                self.send_json(dict(current, suitability=store.read(current["session_id"]),
                                    ergative=store.read_flags(current["session_id"], "ergative"),
                                    need_help=store.read_flags(current["session_id"], "need_help"),
                                    praat_files={"wav": active["config"].get("stimtrak_wav"), "textgrid": active["config"].get("textgrid")}), head=head)
                return
            if path == "/api/annotations":
                self.send_json(reader.read(), head=head)
                return
            if path in ("/api/suitability.csv", "/api/analysis.csv"):
                decisions = store.read(current["session_id"])
                ergative = store.read_flags(current["session_id"], "ergative")
                need_help = store.read_flags(current["session_id"], "need_help")
                if path == "/api/analysis.csv":
                    try:
                        payload = analysis_csv(current, decisions, reader.read(), ergative, need_help)
                    except ValueError as error:
                        self.send_json({"error": str(error)}, status=409, head=head)
                        return
                    suffix = "_trial_analysis.csv"
                else:
                    payload = suitability_csv(current, decisions, ergative, need_help)
                    suffix = "_suitability.csv"
                filename = re.sub(r"[^A-Za-z0-9_.-]", "_", current["recording"]) + suffix
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                if not head:
                    self.wfile.write(payload)
                return
            if path == "/api/library-analysis.csv":
                try:
                    combined = []
                    for entry in library.listing()["sessions"]:
                        loaded = library.get(entry["session_id"])
                        data = analysis_csv(loaded["session"], store.read(entry["session_id"]), loaded["reader"].read(),
                                            store.read_flags(entry["session_id"], "ergative"), store.read_flags(entry["session_id"], "need_help"))
                        combined.extend(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
                    output = io.StringIO(newline="")
                    writer = csv.DictWriter(output, fieldnames=list(combined[0]))
                    writer.writeheader()
                    writer.writerows(combined)
                    payload = output.getvalue().encode("utf-8-sig")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", 'attachment; filename="all_recordings_trial_analysis.csv"')
                    self.send_header("Content-Length", str(len(payload)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    if not head:
                        self.wfile.write(payload)
                except (ValueError, KeyError, OSError) as error:
                    self.send_json({"error": f"Combined export stopped; no recordings skipped: {error}"}, status=409, head=head)
                return
            if path.startswith("/media/"):
                file = library.media(path.removeprefix("/media/"))
            else:
                file = files.get(path)
            if not file or not file.is_file():
                self.send_error(404)
                return
            size = file.stat().st_size
            try:
                start, end, partial = byte_range(self.headers.get("Range"), size)
            except ValueError:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(206 if partial else 200)
            self.send_header("Content-Type", mimetypes.guess_type(file.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-cache")
            if partial:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            if not head:
                try:
                    with file.open("rb") as handle:
                        handle.seek(start)
                        remaining = end - start + 1
                        while remaining:
                            block = handle.read(min(65536, remaining))
                            if not block:
                                break
                            self.wfile.write(block)
                            remaining -= len(block)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "session_config.json")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    session, assets = build_session(config)
    (ROOT / "session_manifest.json").write_text(json.dumps(session, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifests = ROOT / "session_manifests"
    manifests.mkdir(exist_ok=True)
    (manifests / f"{session['session_id'][:20]}.json").write_text(json.dumps(session, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(session["validation"]), flush=True)
    if args.check:
        if config.get("textgrid"):
            annotations = AnnotationReader(config["textgrid"], session).read()
            if annotations["state"] != "ready":
                raise ValueError(annotations["message"])
            print(f"TextGrid validated: {annotations['filename']}", flush=True)
        return
    store = SuitabilityStore(ROOT / "suitability.sqlite3")
    handler = handler_class(session, assets, config, store, imports=ImportJobs(ROOT / "import_logs"))
    for port in range(args.port, args.port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), handler)
            break
        except OSError as error:
            if error.errno not in (98, 10048) and getattr(error, "winerror", None) != 10048:
                raise
    else:
        raise ValueError("No free local port found.")
    url = f"http://127.0.0.1:{server.server_port}"
    (ROOT / "server_status.json").write_text(json.dumps({"url": url, "pid": os.getpid()}), encoding="utf-8")
    print(f"Trial reference ready: {url}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
