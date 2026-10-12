"""Capture saved annotation work, or reconnect it on another device."""

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parent
PATH_KEYS = ("vhdr", "stimtrak_wav", "textgrid", "audio_dir")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def checked_join(root, relative):
    relative = str(relative)
    if not relative or PureWindowsPath(relative).drive or Path(relative).is_absolute():
        raise ValueError(f"Expected a relative path: {relative}")
    target = (Path(root) / relative).resolve()
    if not target.is_relative_to(Path(root).resolve()) or target == Path(root).resolve():
        raise ValueError(f"Path escapes its root: {relative}")
    return target


def modules(source):
    sys.path.insert(0, str(Path(source) / "trial_reference"))
    sys.path.insert(0, str(source))
    import server
    import annotations
    import suitability
    return server, annotations, suitability


def stable_bytes(path):
    path = Path(path)
    before = path.stat()
    payload = path.read_bytes()
    after = path.stat()
    if (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size):
        raise ValueError(f"File changed during backup; save and retry: {path}")
    return payload


def decisions(database, session_id):
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True)) as db:
        unsuitable = {trial: {"unsuitable": bool(value), "updated_at_utc": updated}
                      for trial, value, updated in db.execute(
                          "SELECT trial_id, unsuitable, updated_at_utc FROM suitability WHERE session_id=?",
                          (session_id,))}
        flags = {field: {} for field in ("ergative", "need_help")}
        for trial, field, value, updated in db.execute(
                "SELECT trial_id, field, marked, updated_at_utc FROM trial_flags WHERE session_id=?",
                (session_id,)):
            flags[field][trial] = {"marked": bool(value), "updated_at_utc": updated}
    return unsuitable, flags["ergative"], flags["need_help"]


def capture(source, recordings_root, output):
    source, recordings_root, output = (Path(p).resolve() for p in (source, recordings_root, output))
    if output.exists():
        raise ValueError("Backup destination already exists. Use a new destination to preserve the old snapshot.")
    server, annotations, suitability = modules(source)
    viewer = source / "trial_reference"
    default_config = read_json(viewer / "session_config.json")
    configs = [(default_config, None)]
    for registration in sorted((viewer / "recordings").glob("*/registration.json")):
        configs.append((read_json(registration.parent / "config.json"), registration.parent))
    output.mkdir(parents=True)
    database = output / "trial_decisions.sqlite3"
    # SQLite's backup API includes committed WAL contents without touching the live database.
    with closing(sqlite3.connect((viewer / "suitability.sqlite3").as_uri() + "?mode=ro", uri=True)) as live:
        with closing(sqlite3.connect(database)) as backup:
            live.backup(backup)
            backup.execute("PRAGMA journal_mode=DELETE")
            backup.commit()
            if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Trial decision database failed integrity checking.")
    entries, seen = [], set()
    for config, registration_dir in configs:
        session, _ = server.build_session(config)
        sid, recording = session["session_id"], session["recording"]
        if sid in seen:
            continue
        if not re.fullmatch(r"[a-f0-9]{64}", sid) or not re.fullmatch(r"[A-Za-z0-9_-]+", recording):
            raise ValueError("Unsafe recording identity.")
        seen.add(sid)
        if registration_dir:
            original = read_json(registration_dir / "manifest.json")
            if sid != original["session_id"] or [s["sha256"] for s in session["sources"]] != [s["sha256"] for s in original["sources"]]:
                raise ValueError(f"Source identity changed since import: {recording}")
        relative_config = {key: Path(config[key]).resolve().relative_to(recordings_root).as_posix() for key in PATH_KEYS}
        relative = Path("recordings") / recording
        directory = output / relative
        directory.mkdir(parents=True)
        payload = stable_bytes(config["textgrid"])
        grid_name = f"{recording}_annotations.TextGrid"
        (directory / grid_name).write_bytes(payload)
        mapped = annotations.AnnotationReader(directory / grid_name, session).read()
        if mapped["state"] != "ready" or mapped["sha256"] != sha256(payload):
            raise ValueError(f"Invalid saved annotations for {recording}: {mapped.get('message')}")
        mapped.update(path=str(config["textgrid"]), filename=Path(config["textgrid"]).name,
                      saved_at_utc=datetime.fromtimestamp(Path(config["textgrid"]).stat().st_mtime, timezone.utc).isoformat())
        flags = decisions(database, sid)
        (directory / "session.json").write_bytes(json_bytes(session))
        (directory / "paths.json").write_bytes(json_bytes(relative_config))
        (directory / "annotations.json").write_bytes(json_bytes(mapped))
        (directory / "trial_analysis.csv").write_bytes(annotations.analysis_csv(session, flags[0], mapped, flags[1], flags[2]))
        (directory / "trial_flags.csv").write_bytes(suitability.suitability_csv(session, *flags))
        if registration_dir:
            for name in ("registration.json", "provenance.json", "extraction_result.json"):
                original = registration_dir / name
                if original.is_file():
                    (directory / name).write_bytes(stable_bytes(original))
        metadata_paths = {}
        for item in session["sources"]:
            path = Path(item["path"])
            if path.is_relative_to(recordings_root) and path.suffix.lower() in (".vhdr", ".vmrk", ".csv"):
                destination = checked_join(directory / "source_metadata", path.name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(stable_bytes(path))
                metadata_paths[path.relative_to(recordings_root).as_posix()] = path.name
        (directory / "source_metadata.json").write_bytes(json_bytes(metadata_paths))
        main = [t for t in session["trials"] if t["kind"] == "main"]
        eligible = [t for t in main if not flags[0].get(t["id"], {}).get("unsuitable", False)
                    and mapped["trials"][t["id"]]["status"] == "ok"
                    and mapped["trials"][t["id"]]["transcription"].strip()]
        counts = {"itr": 0, "tr_erg": 0, "tr_zero": 0}
        for trial in eligible:
            key = "itr" if trial["condition"].startswith("it_") else (
                "tr_erg" if flags[1].get(trial["id"], {}).get("marked", False) else "tr_zero")
            counts[key] += 1
        entry = {"recording": recording, "session_id": sid, "directory": relative.as_posix(),
                 "textgrid": grid_name, "paths": relative_config, "main_trials": len(main),
                 "transcribed_trials": sum(bool(mapped["trials"][t["id"]]["transcription"].strip()) for t in main),
                 "eligible_counts": counts, "annotation_sha256": sha256(payload),
                 "stimtrak_wav_sha256": server.file_hash(config["stimtrak_wav"]),
                 "unassigned_onsets": len(mapped["unassigned_onsets"]),
                 "unassigned_transcriptions": len(mapped["unassigned_transcriptions"])}
        entries.append(entry)
        print(f"Captured {recording}: {entry['transcribed_trials']} transcribed; {counts}")
    with closing(sqlite3.connect(database)) as db:
        tables = {name: [dict(zip([c[1] for c in db.execute(f'PRAGMA table_info({name})')], row))
                         for row in db.execute(f"SELECT * FROM {name} ORDER BY session_id, trial_id")]
                  for name in ("suitability", "trial_flags")}
    (output / "trial_decisions.json").write_bytes(json_bytes(tables))
    checksums = {p.relative_to(output).as_posix(): sha256(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    index = {"format_version": 1, "captured_at_utc": datetime.now(timezone.utc).isoformat(),
             "default_session_id": entries[0]["session_id"], "raw_eeg_and_audio_included": False,
             "recordings": sorted(entries, key=lambda e: e["recording"]), "sha256": checksums}
    (output / "backup.json").write_bytes(json_bytes(index))
    return index


def verify(backup):
    backup = Path(backup).resolve()
    index = read_json(backup / "backup.json")
    if index["format_version"] != 1:
        raise ValueError("Unsupported backup format.")
    for relative, expected in index["sha256"].items():
        if sha256(checked_join(backup, relative).read_bytes()) != expected:
            raise ValueError(f"Backup checksum mismatch: {relative}")
    database = checked_join(backup, "trial_decisions.sqlite3")
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Backup database integrity check failed.")
    return index


def preflight(writes):
    for target, payload in writes.items():
        if target.exists() and (not target.is_file() or target.read_bytes() != payload):
            raise ValueError(f"Refusing to overwrite different existing work: {target}")


def restore(backup, recordings_root, workspace=ROOT, python=sys.executable, praat=None, dry_run=False):
    backup, recordings_root, workspace = (Path(p).resolve() for p in (backup, recordings_root, workspace))
    python = str(Path(python).resolve())
    if not Path(python).is_file():
        raise ValueError("Python executable not found.")
    index = verify(backup)
    server, annotations, _ = modules(workspace)
    viewer = workspace / "trial_reference"
    experiment = workspace.parents[1] / "isolated part"
    writes, default_config = {}, None
    for entry in index["recordings"]:
        directory = checked_join(backup, entry["directory"])
        config = {key: str(checked_join(recordings_root, entry["paths"][key])) for key in PATH_KEYS}
        config.update(experiment_dir=str(experiment), lucide=str(viewer / "vendor" / "lucide" / "lucide.min.js"))
        try:
            session, _ = server.build_session(config)
        except (OSError, ValueError) as error:
            raise ValueError(f"Cannot reconnect {entry['recording']}. Copy the unchanged private EEG/audio folders first: {error}") from error
        if session["session_id"] != entry["session_id"]:
            raise ValueError(f"Different original recording: {entry['recording']}. Flags cannot be transferred.")
        old = read_json(directory / "session.json")
        if [s["sha256"] for s in old["sources"]] != [s["sha256"] for s in session["sources"]]:
            raise ValueError(f"Source logs or stimulus tables differ: {entry['recording']}")
        if server.file_hash(config["stimtrak_wav"]) != entry["stimtrak_wav_sha256"]:
            raise ValueError(f"Different StimTrak WAV: {entry['recording']}")
        grid_path = checked_join(directory, entry["textgrid"])
        mapped = annotations.AnnotationReader(grid_path, session).read()
        if mapped["state"] != "ready":
            raise ValueError(mapped["message"])
        writes[Path(config["textgrid"])] = grid_path.read_bytes()
        registered = viewer / "recordings" / entry["session_id"][:20]
        writes[registered / "config.json"] = json_bytes(config)
        for name in ("registration.json", "provenance.json", "extraction_result.json"):
            path = directory / name
            if path.is_file():
                writes[registered / name] = path.read_bytes()
        # The saved manifest contains only unchanged source hashes used by the loader.
        writes[registered / "manifest.json"] = (directory / "session.json").read_bytes()
        if entry["session_id"] == index["default_session_id"]:
            default_config = config
        print(f"Verified {entry['recording']}: original identity, triggers, WAV and saved annotations")
    if default_config is None:
        raise ValueError("Default recording absent from backup.")
    writes[viewer / "session_config.json"] = json_bytes(default_config)
    runtime = {"mne_python": python, "viewer_python": python, "default_channel": "AUX1",
               "praat_output_root": str(recordings_root), "default_experiment_dir": str(experiment),
               "praat": str(Path(praat).resolve()) if praat else ""}
    writes[viewer / "pipeline_config.json"] = json_bytes(runtime)
    writes[viewer / "suitability.sqlite3"] = (backup / "trial_decisions.sqlite3").read_bytes()
    for suffix in ("-wal", "-shm"):
        if (viewer / ("suitability.sqlite3" + suffix)).exists():
            raise ValueError("Stop the existing viewer before restoring its database.")
    preflight(writes)
    if not dry_run:
        for path, payload in writes.items():
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as handle:
                    handle.write(payload)
    print(f"{'Dry run succeeded' if dry_run else 'Restored'}: {len(index['recordings'])} recordings. Existing different files are never overwritten.")
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("capture")
    export.add_argument("--source", type=Path, default=ROOT)
    export.add_argument("--recordings-root", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("verify")
    check.add_argument("--backup", type=Path, default=ROOT / "saved_work")
    recover = commands.add_parser("restore")
    recover.add_argument("--backup", type=Path, default=ROOT / "saved_work")
    recover.add_argument("--recordings-root", type=Path, required=True)
    recover.add_argument("--python", default=sys.executable)
    recover.add_argument("--praat")
    recover.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "capture":
        capture(args.source, args.recordings_root, args.output)
    elif args.command == "verify":
        result = verify(args.backup)
        print(f"Verified {len(result['recordings'])} recordings and {len(result['sha256'])} saved files.")
    else:
        restore(args.backup, args.recordings_root, python=args.python, praat=args.praat, dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, sqlite3.Error) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
