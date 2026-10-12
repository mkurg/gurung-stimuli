"""One local import at a time, with progress available to the viewer."""

import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from recording_library import atomic_json


class ImportJobs:
    def __init__(self, root, importer=None):
        self.root = Path(root)
        self.importer = importer
        self.lock = threading.Lock()
        self.jobs = {}

    def start(self, value):
        from import_recording import run_import, validate_paths
        validate_paths(value)
        with self.lock:
            if any(job["state"] == "running" for job in self.jobs.values()):
                raise ValueError("Another recording is being imported. Wait for it to finish.")
            job_id = uuid.uuid4().hex
            self.jobs[job_id] = {"id": job_id, "state": "running", "log": [], "result": None,
                                 "started_at_utc": datetime.now(timezone.utc).isoformat()}

        def record(message):
            with self.lock:
                self.jobs[job_id]["log"].append(str(message))
            with (self.root / f"{job_id}.log").open("a", encoding="utf-8") as handle:
                handle.write(str(message) + "\n")

        def work():
            try:
                self.root.mkdir(parents=True, exist_ok=True)
                result = (self.importer or run_import)(value, log=record)
                with self.lock:
                    self.jobs[job_id].update(state="complete", result=result)
            except Exception as error:
                with self.lock:
                    self.jobs[job_id].update(state="error", error=str(error))
                try:
                    record(f"Import stopped: {error}")
                except OSError:
                    pass
            finally:
                try:
                    atomic_json(self.root / f"{job_id}.json", self.get(job_id))
                except OSError:
                    pass

        threading.Thread(target=work, name=f"import-{job_id[:8]}", daemon=True).start()
        return self.get(job_id)

    def get(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                raise KeyError("Unknown import job.")
            return dict(job, log=job["log"][-60:])
