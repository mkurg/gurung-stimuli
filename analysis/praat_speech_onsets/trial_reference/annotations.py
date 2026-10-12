"""Read saved Praat annotations without changing their EEG timebase."""

import csv
import hashlib
import io
import json
import math
import re
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAPPING_VERSION = 2
sys.path.insert(0, str(ROOT / "vendor"))
from praatio.utilities import textgrid_io

from suitability import suitability_csv


def finite(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("TextGrid contains a non-finite time.")
    return number


def trigger_code(label):
    match = re.fullmatch(r"(?:Mk\d+:\s*Stimulus/)?\s*S\s*(\d+)", label.strip(), re.I)
    return int(match[1]) if match else None


def map_annotations(grid, session):
    tolerance = 0.5 / session["sample_rate"]
    if abs(finite(grid["xmin"])) > tolerance or abs(finite(grid["xmax"]) - session["duration"]) > tolerance:
        raise ValueError("TextGrid duration differs from the full EEG/StimTrak timeline. Do not use a cropped or shifted grid.")
    tiers = {}
    for tier in grid["tiers"]:
        if tier["name"] in tiers:
            raise ValueError(f"Duplicate TextGrid tier: {tier['name']}")
        tiers[tier["name"]] = tier
    for name, kind in [("triggers", "TextTier"), ("speech_onset", "TextTier"), ("transcription", "IntervalTier")]:
        if name not in tiers or tiers[name]["class"] != kind:
            raise ValueError(f"Expected {kind} named '{name}'.")
        if abs(finite(tiers[name]["xmin"])) > tolerance or abs(finite(tiers[name]["xmax"]) - session["duration"]) > tolerance:
            raise ValueError(f"Tier '{name}' has a different timeline.")

    recorded = []
    for time, label in tiers["triggers"]["entries"]:
        code = trigger_code(label)
        if code is not None:
            recorded.append((finite(time), code))
        elif re.search(r"Stimulus/|^\s*S\s*\d", label, re.I):
            raise ValueError(f"Unrecognised stimulus label in triggers tier: {label}")
    expected = session["triggers"]
    if len(recorded) != len(expected):
        raise ValueError(f"TextGrid stimulus count differs from EEG: {len(recorded)} vs {len(expected)}.")
    s200 = {}
    for (time, code), marker in zip(recorded, expected):
        if code != marker["code"] or abs(time - marker["time"]) > tolerance:
            raise ValueError(f"TextGrid trigger mismatch at {marker['marker_id']}; original EEG times/codes must stay unchanged.")
        if marker["role"] == "target_onset":
            s200[marker["trial_id"]] = time

    main = [trial for trial in session["trials"] if trial["kind"] == "main"]
    result = {trial["id"]: {
        "status": "missing_onset" if trial["kind"] == "main" else "no_eeg_triggers",
        "s200_eeg_s": s200.get(trial["id"]), "speech_onset_eeg_s": None,
        "latency_s": None, "latency_ms": None, "onset_count": 0,
        "onset_points": [], "transcription": "", "intervals": [], "warnings": [],
    } for trial in session["trials"]}
    unassigned_points, unassigned_intervals = [], []
    previous = -math.inf
    for time, label in tiers["speech_onset"]["entries"]:
        time = finite(time)
        if time <= previous or not 0 <= time <= session["duration"]:
            raise ValueError("Speech-onset points are out of order or outside the recording.")
        previous = time
        point = {"time": time, "label": label}
        matches = [trial for trial in main if s200[trial["id"]] <= time < trial["end"]]
        if len(matches) == 1:
            result[matches[0]["id"]]["onset_points"].append(point)
        else:
            unassigned_points.append(point)

    previous = 0.0
    for start, end, label in tiers["transcription"]["entries"]:
        start, end = finite(start), finite(end)
        if abs(start - previous) > tolerance or end <= start or end > session["duration"] + tolerance:
            raise ValueError("Transcription intervals do not form a complete, ordered timeline. Save a complete TextGrid as text.")
        previous = end
        if not label.strip():
            continue
        interval = {"start": start, "end": end, "text": label}
        # Responses can continue after the picture changes; their start identifies the trial.
        matches = [trial for trial in main if s200[trial["id"]] - tolerance <= start < trial["end"]]
        if len(matches) == 1:
            result[matches[0]["id"]]["intervals"].append(interval)
        else:
            unassigned_intervals.append(interval)
    if abs(previous - session["duration"]) > tolerance:
        raise ValueError("Transcription tier is incomplete; wait for Praat to finish saving.")

    for trial in main:
        annotation = result[trial["id"]]
        annotation["onset_count"] = len(annotation["onset_points"])
        annotation["transcription"] = "\n".join(interval["text"] for interval in annotation["intervals"])
        if annotation["onset_count"] == 1:
            onset = annotation["onset_points"][0]["time"]
            latency = onset - annotation["s200_eeg_s"]
            annotation.update(status="ok", speech_onset_eeg_s=onset, latency_s=latency, latency_ms=latency * 1000)
        elif annotation["onset_count"] > 1:
            annotation["status"] = "multiple_onsets"
            annotation["warnings"].append("Multiple speech-onset points; no single latency selected.")
    return {"trials": result, "unassigned_onsets": unassigned_points, "unassigned_transcriptions": unassigned_intervals}


class AnnotationReader:
    def __init__(self, path, session, snapshot_dir=None):
        self.path = Path(path).resolve() if path else None
        self.session = session
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else None
        self.lock = threading.Lock()
        self.cached = None

    def read(self):
        with self.lock:
            base = {"session_id": self.session["session_id"], "path": str(self.path) if self.path else None,
                    "filename": self.path.name if self.path else None, "trials": {}}
            if self.path is None:
                return dict(base, state="unconfigured", message="No saved TextGrid configured.")
            source_read = False
            try:
                before = self.path.stat()
                if before.st_size > 16 * 1024 * 1024:
                    raise ValueError("TextGrid is larger than the 16 MB reading limit.")
                payload = self.path.read_bytes()
                after = self.path.stat()
                source_read = True
                if (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size) or len(payload) != after.st_size:
                    raise ValueError("Praat is saving the TextGrid; waiting for a complete file.")
                digest = hashlib.sha256(payload).hexdigest()
                saved_at = datetime.fromtimestamp(after.st_mtime, timezone.utc).isoformat()
                if self.cached and self.cached["sha256"] == digest:
                    return dict(self.cached, saved_at_utc=saved_at)
                if payload.startswith(b"ooBinaryFile"):
                    raise ValueError("Save the TextGrid as a text file in Praat, not as a binary file.")
                encoding = "utf-16" if payload.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
                grid = textgrid_io.parseTextgridStr(payload.decode(encoding), includeEmptyIntervals=True)
                mapped = map_annotations(grid, self.session)
                snapshot = dict(base, **mapped, state="ready", sha256=digest, saved_at_utc=saved_at,
                                mapping_version=MAPPING_VERSION, message="Saved TextGrid synced")
                if self.snapshot_dir:
                    self.snapshot_dir.mkdir(parents=True, exist_ok=True)
                    destination = self.snapshot_dir / f"{digest}.TextGrid"
                    if not destination.exists():
                        destination.write_bytes(payload)
                    (self.snapshot_dir / f"{digest}_mapping_v{MAPPING_VERSION}.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                self.cached = snapshot
                return snapshot
            except FileNotFoundError as error:
                if source_read:
                    return dict(base, state="error", message=f"Could not archive saved TextGrid: {error}")
                return dict(base, state="missing", message="Saved TextGrid not found. Save to the configured filename.")
            except Exception as error:
                # Invalid or half-written saves must not produce fresh-looking latencies.
                return dict(base, state="error", message=f"TextGrid not synced: {error}")


def analysis_csv(session, decisions, annotations, ergative=None, need_help=None):
    if annotations["state"] != "ready":
        raise ValueError(annotations["message"])
    original = list(csv.DictReader(io.StringIO(suitability_csv(session, decisions, ergative, need_help).decode("utf-8-sig"))))
    extra = ["textgrid_path", "textgrid_sha256", "textgrid_saved_at_utc", "annotation_mapping_version",
             "s200_textgrid_eeg_s", "speech_onset_eeg_s", "speech_latency_s", "speech_latency_ms",
             "onset_count", "annotation_status", "transcription", "annotation_warnings",
             "onset_points_json", "transcription_intervals_json", "unassigned_onsets_count", "unassigned_transcriptions_count"]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(original[0]) + extra)
    writer.writeheader()
    for row in original:
        annotation = annotations["trials"][row["trial_id"]]
        row.update(textgrid_path=annotations["path"], textgrid_sha256=annotations["sha256"],
                   textgrid_saved_at_utc=annotations["saved_at_utc"], annotation_mapping_version=annotations["mapping_version"],
                   s200_textgrid_eeg_s=annotation["s200_eeg_s"], speech_onset_eeg_s=annotation["speech_onset_eeg_s"],
                   speech_latency_s=annotation["latency_s"], speech_latency_ms=annotation["latency_ms"],
                   onset_count=annotation["onset_count"], annotation_status=annotation["status"],
                   transcription=annotation["transcription"], annotation_warnings="; ".join(annotation["warnings"]),
                   onset_points_json=json.dumps(annotation["onset_points"], ensure_ascii=False),
                   transcription_intervals_json=json.dumps(annotation["intervals"], ensure_ascii=False),
                   unassigned_onsets_count=len(annotations["unassigned_onsets"]),
                   unassigned_transcriptions_count=len(annotations["unassigned_transcriptions"]))
        writer.writerow(row)
    return output.getvalue().encode("utf-8-sig")
