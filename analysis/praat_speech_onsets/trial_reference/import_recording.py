"""One import: AUX extraction, validation, provenance, and viewer registration."""

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from brainvision_to_praat import linked_file, read_brainvision_ini
from annotations import AnnotationReader
from recording_library import atomic_json, file_hash, import_lock
from pipeline_runtime import checked_mne_python
from praat_files import check_praat_targets, place_praat_files
from server import build_session, validate_full_recording


def settings():
    return json.loads((ROOT / "pipeline_config.json").read_text(encoding="utf-8"))


def source_identity(vhdr, audio_dir):
    header = read_brainvision_ini(vhdr)
    marker = linked_file(vhdr, header["Common Infos"]["MarkerFile"])
    paths = [vhdr, marker, audio_dir / "eeg_triggers.csv", audio_dir / "full_session.wav"]
    identity = [file_hash(path) for path in paths]
    return hashlib.sha256(json.dumps(identity).encode()).hexdigest(), header


def resolve_channel(header, requested):
    names = [next(csv.reader([value], quoting=csv.QUOTE_NONE))[0].replace(r"\1", ",")
             for value in header["Channel Infos"].values()]
    if requested in names:
        return requested
    if requested.isdigit() and 1 <= int(requested) <= len(names):
        return names[int(requested) - 1]
    raise ValueError(f"Microphone channel '{requested}' not found. Recorded channels: {', '.join(names)}")


def validate_paths(value):
    if set(value) != {"vhdr", "audio_dir", "experiment_dir", "channel"} or not all(isinstance(v, str) for v in value.values()):
        raise ValueError("Expected vhdr, audio_dir, experiment_dir and channel.")
    output = {}
    for key in ("vhdr", "audio_dir", "experiment_dir"):
        path = Path(value[key].strip().strip('"'))
        if not path.is_absolute():
            raise ValueError(f"Use an absolute local path for {key}.")
        output[key] = path.resolve()
    if output["vhdr"].suffix.lower() != ".vhdr" or not output["vhdr"].is_file():
        raise ValueError("Select the original .vhdr file, with its linked .eeg and .vmrk nearby.")
    for filename in ("full_session.wav", "eeg_triggers.csv", "recording_segments.csv"):
        if not (output["audio_dir"] / filename).is_file():
            raise ValueError(f"Missing PsychoPy file: {filename}. Choose its actual session folder.")
    if not (output["experiment_dir"] / "Conds" / "isolated_practice.csv").is_file():
        raise ValueError("This importer supports the isolated task. Select its matching experiment folder containing Conds.")
    if not any(output["audio_dir"].glob("*_isolated_main_l*_trial*_imageset*_cond_*.wav")):
        raise ValueError("No isolated-task trial WAVs found. Discourse/different protocols need a separate adapter.")
    output["channel"] = value["channel"].strip()
    return output


def register(config, channel, library_root, log, export_metadata=None, builder=build_session, expected_identity=None):
    log("Validating EEG triggers, picture mapping and all full-WAV sample locations...")
    session, _ = builder(config)
    reconciliation = session.get("trigger_reconciliation", {})
    if reconciliation:
        log(f"Split-recording check: {reconciliation['matched_triggers']} EEG triggers match the full remaining log exactly. "
            f"{len(reconciliation['unrecorded_initial_rest'])} initial resting-state log entries are absent from this EEG file; "
            "kept in provenance without EEG timestamps. No timing offset applied.")
    for item in session.get("full_recording", {}).get("unreadable_practice_wavs", []):
        log(f"Warning: {item['filename']} is unreadable ({item['error']}). Practice playback uses the intact full WAV and logged sample bounds; original short WAV kept unchanged.")
    for item in session.get("full_recording", {}).get("unreadable_main_wavs", []):
        log(f"Warning: {item['filename']} is unreadable ({item['error']}). Playback uses the full WAV and logged sample bounds, "
            f"validated by {', '.join(item['validated_by_trials'])}; original short WAV and EEG timing kept unchanged.")
    if expected_identity and session["session_id"] != expected_identity:
        raise ValueError("Source identity changed during import. No recording was registered.")
    annotations = AnnotationReader(config["textgrid"], session).read()
    if annotations["state"] != "ready":
        raise ValueError(annotations["message"])
    destination = Path(library_root) / session["session_id"][:20]
    destination.mkdir(parents=True, exist_ok=True)
    registration = destination / "registration.json"
    if registration.exists():
        old = json.loads(registration.read_text(encoding="utf-8"))
        if old["session_id"] != session["session_id"]:
            raise ValueError("Recording-directory identity collision; nothing was replaced.")
        log("Already in the library. Existing audio and manual annotations were kept.")
        return dict(old, already_registered=True, textgrid=config["textgrid"], stimtrak_wav=config["stimtrak_wav"])
    header = read_brainvision_ini(Path(config["vhdr"]))
    eeg = linked_file(Path(config["vhdr"]), header["Common Infos"]["DataFile"])
    log("Hashing original EEG data and extraction outputs for provenance...")
    provenance = {
        "pipeline_version": 3, "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "session_id": session["session_id"], "channel": channel,
        "source_files": session["sources"] + [{"path": str(eeg), "sha256": file_hash(eeg), "bytes": eeg.stat().st_size}],
        "stimtrak_wav": {"path": config["stimtrak_wav"], "sha256": file_hash(config["stimtrak_wav"])},
        "initial_textgrid_sha256": annotations["sha256"], "extraction": export_metadata,
        "tool_sha256": {name: file_hash(ROOT.parent / name if name == "brainvision_to_praat.py" else ROOT / name)
                        for name in ("brainvision_to_praat.py", "server.py", "annotations.py", "import_recording.py", "praat_files.py", "pipeline_runtime.py")},
        "annotation_reader": "praatio==6.2.0", "python_importer": sys.version,
        "timing": "Unchanged EEG samples; markers=(position_1based-1)/sample_rate; latency=marked onset-S200",
        "praat_output_policy": "Working WAV and annotation TextGrid in Desktop/EEG recs/<recording>; existing files never overwritten",
    }
    if reconciliation:
        provenance["trigger_reconciliation"] = reconciliation
    if session.get("full_recording", {}).get("unreadable_main_wavs"):
        provenance["main_audio_fallbacks"] = session["full_recording"]["unreadable_main_wavs"]
    atomic_json(destination / "config.json", config)
    atomic_json(destination / "manifest.json", session)
    atomic_json(destination / "provenance.json", provenance)
    value = {"session_id": session["session_id"], "recording": session["recording"],
             "participant": session["participant"], "list": session["list"], "protocol": "isolated",
             "main_trials": session["validation"]["main_trials"], "channel": channel,
             "registered_at_utc": provenance["registered_at_utc"]}
    # Publish last: an interrupted or failed import never appears as a ready recording.
    atomic_json(registration, value)
    log(f"Added {session['recording']}: {session['validation']['main_trials']} trials. Ready in the recording selector.")
    return dict(value, already_registered=False, textgrid=config["textgrid"], stimtrak_wav=config["stimtrak_wav"])


def _run_import(value, log, library_root, runtime):
    runtime = runtime or settings()
    library_root = Path(library_root) if library_root else ROOT / "recordings"
    paths = validate_paths(value)
    log("Checking linked EEG files and recording identity...")
    identity, header = source_identity(paths["vhdr"], paths["audio_dir"])
    channel = resolve_channel(header, paths["channel"])
    destination = library_root / identity[:20]
    registration = destination / "registration.json"
    if registration.exists():
        old = json.loads(registration.read_text(encoding="utf-8"))
        if old["session_id"] != identity or old["channel"] != channel:
            raise ValueError("This recording is registered with a different identity/channel; existing annotations were not changed.")
        config = json.loads((destination / "config.json").read_text(encoding="utf-8"))
        if Path(config["experiment_dir"]).resolve() != paths["experiment_dir"]:
            raise ValueError("This recording already uses a different experiment folder. Existing mapping was not replaced.")
        log("Already imported: no AUX extraction or annotation overwrite needed.")
        return dict(old, already_registered=True, textgrid=config["textgrid"], stimtrak_wav=config["stimtrak_wav"])
    output_root = runtime.get("praat_output_root", str(Path.home() / "Desktop" / "EEG recs"))
    validate_full_recording(paths["audio_dir"] / "full_session.wav")
    check_praat_targets(paths["vhdr"], output_root)
    python = checked_mne_python(runtime)
    destination.mkdir(parents=True, exist_ok=True)
    result_file = destination / "extraction_result.json"
    log(f"Extracting {channel} with MNE; constant gain, no cropping/filtering/resampling...")
    command = [str(python), str(ROOT.parent / "brainvision_to_praat.py"), str(paths["vhdr"]),
               "--channel", channel, "--output-dir", str(destination / "aux"), "--result-json", str(result_file)]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1"),
                          creationflags=flags) as process:
        for line in process.stdout:
            if line.strip():
                log(line.rstrip())
        if process.wait() != 0:
            raise ValueError("AUX extraction failed. See the import log; no recording was registered.")
    output = Path(json.loads(result_file.read_text(encoding="utf-8"))["output_folder"])
    stem = paths["vhdr"].stem
    annotated_grid = output / f"{stem}_annotations.TextGrid"
    with annotated_grid.open("xb") as handle:
        handle.write((output / f"{stem}.TextGrid").read_bytes())
    template = json.loads((ROOT / "session_config.json").read_text(encoding="utf-8"))
    config = {"vhdr": str(paths["vhdr"]), "audio_dir": str(paths["audio_dir"]),
              "experiment_dir": str(paths["experiment_dir"]), "stimtrak_wav": str(output / f"{stem}.wav"),
              "textgrid": str(annotated_grid), "lucide": template["lucide"]}
    metadata = json.loads((output / f"{stem}_export.json").read_text(encoding="utf-8"))
    # Validate staged outputs before placing the working files in the EEG folder.
    session, _ = build_session(config)
    if session["session_id"] != identity:
        raise ValueError("Source identity changed during import. No recording was registered.")
    annotations = AnnotationReader(config["textgrid"], session).read()
    if annotations["state"] != "ready":
        raise ValueError(annotations["message"])
    config = place_praat_files(config, output_root=output_root)
    log(f"Praat WAV: {config['stimtrak_wav']}\nPraat TextGrid: {config['textgrid']}")
    return register(config, channel, library_root, log, metadata, expected_identity=identity)


def place_registered_files(directory, log=print, output_root=None):
    directory = Path(directory).resolve()
    with import_lock(directory.parent):
        old_config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
        registration = json.loads((directory / "registration.json").read_text(encoding="utf-8"))
        provenance = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
        if file_hash(old_config["stimtrak_wav"]) != provenance["stimtrak_wav"]["sha256"]:
            raise ValueError("StimTrak WAV changed since import; no files were relocated.")
        session, _ = build_session(old_config)
        if session["session_id"] != registration["session_id"]:
            raise ValueError("Recording identity changed; no files were relocated.")
        annotations = AnnotationReader(old_config["textgrid"], session).read()
        if annotations["state"] != "ready":
            raise ValueError(annotations["message"])
        output_root = output_root or settings().get("praat_output_root", str(Path.home() / "Desktop" / "EEG recs"))
        config = place_praat_files(old_config, reuse_identical=True, output_root=output_root)
        if config == old_config:
            return config
        provenance.setdefault("relocations", []).append({
            "at_utc": datetime.now(timezone.utc).isoformat(),
            "files": [{"old_path": old_config[key], "new_path": config[key], "sha256": file_hash(config[key])}
                      for key in ("stimtrak_wav", "textgrid")],
            "original_copies_kept": True,
        })
        provenance["stimtrak_wav"]["path"] = config["stimtrak_wav"]
        atomic_json(directory / "provenance.json", provenance)
        atomic_json(directory / "config.json", config)
        log(f"Working Praat files placed in the Desktop recording folder: {config['stimtrak_wav']}\n{config['textgrid']}\nOriginal copies kept as backups. Restart the viewer to watch the new path.")
        return config


def run_import(value, log=print, library_root=None, runtime=None):
    library_root = Path(library_root) if library_root else ROOT / "recordings"
    with import_lock(library_root):
        return _run_import(value, log, library_root, runtime)


def gui_import():
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog
    root = tk.Tk()
    root.withdraw()
    runtime = settings()
    vhdr = filedialog.askopenfilename(title="Choose original BrainVision header", filetypes=[("BrainVision header", "*.vhdr")])
    if not vhdr:
        return
    audio = filedialog.askdirectory(title="Choose PsychoPy session folder containing full_session.wav", initialdir=str(Path(vhdr).parent))
    if not audio:
        return
    experiment = runtime["default_experiment_dir"]
    if not messagebox.askyesno("Matching experiment", f"Use this experiment folder?\n\n{experiment}"):
        experiment = filedialog.askdirectory(title="Choose matching isolated-task experiment folder")
        if not experiment:
            return
    channel = simpledialog.askstring("Microphone channel", "Exact microphone channel name or number:", initialvalue=runtime["default_channel"])
    if not channel:
        return
    root.destroy()
    result = run_import({"vhdr": vhdr, "audio_dir": audio, "experiment_dir": experiment, "channel": channel})
    print(f"\nPraat WAV: {result['stimtrak_wav']}\nPraat TextGrid: {result['textgrid']}")
    print("Open these together in Praat. The same web interface now lists this recording.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--existing-config", type=Path, help="Register a validated existing export without regenerating its annotations")
    parser.add_argument("--place-praat-files", type=Path, help="Place an existing registration's working Praat files beside its EEG header")
    parser.add_argument("--vhdr")
    parser.add_argument("--audio-dir")
    parser.add_argument("--experiment-dir")
    parser.add_argument("--channel", default="AUX1")
    args = parser.parse_args()
    if args.place_praat_files:
        place_registered_files(args.place_praat_files)
    elif args.gui:
        gui_import()
    elif args.existing_config:
        config = json.loads(args.existing_config.read_text(encoding="utf-8"))
        result = register(config, args.channel, ROOT / "recordings", print)
        print(json.dumps(result, indent=2))
    else:
        runtime = settings()
        result = run_import({"vhdr": args.vhdr or "", "audio_dir": args.audio_dir or "",
                             "experiment_dir": args.experiment_dir or runtime["default_experiment_dir"], "channel": args.channel})
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyboardInterrupt) as error:
        print(f"Import stopped: {error}", file=sys.stderr)
        sys.exit(1)
