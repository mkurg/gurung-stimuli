"""Validated recordings shared by one local viewer."""

import hashlib
import json
import os
import re
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path

from annotations import AnnotationReader


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def import_lock(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / "import.lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ValueError("Another recording import is running. Wait for it to finish.") from error
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def bundle(session, assets, config, snapshot_root, reader=None):
    return {"session": session, "assets": assets, "config": config,
            "reader": reader or AnnotationReader(config.get("textgrid"), session,
                                                  Path(snapshot_root) / session["session_id"][:20])}


class RecordingLibrary:
    def __init__(self, root, default_bundle, loader, snapshot_root):
        self.root = Path(root)
        self.default_id = default_bundle["session"]["session_id"]
        self.loaded = {self.default_id: default_bundle}
        self.loader = loader
        self.snapshot_root = Path(snapshot_root)
        self.lock = threading.RLock()
        self.entries = {}
        self.errors = {}

    def refresh(self):
        with self.lock:
            entries = {}
            for path in sorted(self.root.glob("*/registration.json")):
                value = json.loads(path.read_text(encoding="utf-8"))
                session_id = value["session_id"]
                if not re.fullmatch(r"[a-f0-9]{64}", session_id) or path.parent.name != session_id[:20]:
                    raise ValueError(f"Invalid recording registration: {path}")
                entries[session_id] = dict(value, directory=path.parent)
            self.entries = entries

    def listing(self):
        self.refresh()
        with self.lock:
            session = self.loaded[self.default_id]["session"]
            entries = {self.default_id: {"session_id": self.default_id, "recording": session["recording"],
                       "participant": session["participant"], "list": session["list"],
                       "main_trials": session["validation"]["main_trials"], "protocol": "isolated"}}
            for session_id, entry in self.entries.items():
                entries[session_id] = {key: entry[key] for key in
                                      ("session_id", "recording", "participant", "list", "main_trials", "protocol")}
            return {"application": "praat-trial-reference", "default_session_id": self.default_id,
                    "sessions": [dict(value, error=self.errors.get(key)) for key, value in
                                 sorted(entries.items(), key=lambda item: (item[1]["recording"], item[0]))]}

    def get(self, session_id=None):
        session_id = session_id or self.default_id
        with self.lock:
            if session_id in self.loaded:
                return self.loaded[session_id]
            self.refresh()
            entry = self.entries.get(session_id)
            if not entry:
                raise KeyError("Unknown recording. Select a registered recording.")
            try:
                config = json.loads((entry["directory"] / "config.json").read_text(encoding="utf-8"))
                session, assets = self.loader(config)
                if session["session_id"] != session_id:
                    raise ValueError("Source recording changed since import. Revalidate the original files.")
                manifest_path = entry["directory"] / "manifest.json"
                if manifest_path.is_file():
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    if [source["sha256"] for source in session["sources"]] != [source["sha256"] for source in manifest["sources"]]:
                        raise ValueError("Source logs or experiment tables changed since import. Existing mapping was not replaced.")
                provenance_path = entry["directory"] / "provenance.json"
                if provenance_path.is_file():
                    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
                    if file_hash(config["stimtrak_wav"]) != provenance["stimtrak_wav"]["sha256"]:
                        raise ValueError("StimTrak WAV changed since import. Use the unchanged extraction.")
                loaded = bundle(session, assets, config, self.snapshot_root)
                self.loaded[session_id] = loaded
                self.errors.pop(session_id, None)
                return loaded
            except Exception as error:
                self.errors[session_id] = str(error)
                raise ValueError(f"Recording unavailable: {error}") from error

    def media(self, key):
        with self.lock:
            return next((loaded["assets"][key] for loaded in self.loaded.values() if key in loaded["assets"]), None)
