"""Start or reopen the same local recording library."""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

from pipeline_runtime import checked_mne_python

ROOT = Path(__file__).resolve().parent


def running_url():
    try:
        status = json.loads((ROOT / "server_status.json").read_text(encoding="utf-8"))
        url = status["url"]
        if not url.startswith("http://127.0.0.1:"):
            return None
        with urllib.request.urlopen(url + "/api/sessions", timeout=2) as response:
            if json.load(response).get("application") == "praat-trial-reference":
                return url
    except (OSError, ValueError):
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    runtime = json.loads((ROOT / "pipeline_config.json").read_text(encoding="utf-8"))
    checked_mne_python(runtime)
    url = running_url()
    if not url:
        python = Path(runtime["viewer_python"])
        if os.name == "nt":
            python = python.with_name("pythonw.exe")
        with (ROOT / "server.log").open("w") as output, (ROOT / "server_error.log").open("w") as error:
            process = subprocess.Popen([str(python), str(ROOT / "server.py")], cwd=ROOT, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=error, close_fds=True,
                                       creationflags=(subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == "nt" else 0)
        for _ in range(60):
            url = running_url()
            if url:
                break
            if process.poll() is not None:
                raise ValueError("Viewer could not start. See trial_reference/server_error.log.")
            time.sleep(.5)
        else:
            raise ValueError("Viewer startup timed out. Check the server log before launching again.")
    print(f"Recording library: {url}")
    if not args.no_browser:
        webbrowser.open(url)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
