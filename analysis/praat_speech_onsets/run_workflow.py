"""Run the configured viewer or recording importer from a portable checkout."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--add-recording", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    viewer = Path(__file__).resolve().parent / "trial_reference"
    config = viewer / "pipeline_config.json"
    if not config.is_file():
        parser.error("Run backup_work.py restore first. See RESTORE.md.")
    runtime = json.loads(config.read_text(encoding="utf-8"))
    if args.add_recording:
        command = [runtime["mne_python"], str(viewer / "import_recording.py"), "--gui"]
    else:
        command = [runtime["viewer_python"], str(viewer / "launch_workflow.py")]
        if args.no_browser:
            command.append("--no-browser")
    return subprocess.run(command, cwd=viewer).returncode


if __name__ == "__main__":
    sys.exit(main())
