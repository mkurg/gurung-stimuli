"""Check that the current process can launch the installed extraction runtime."""

import os
import subprocess
from pathlib import Path


ACCESS_MESSAGE = (
    "This viewer cannot access the installed MNE-Python. Restart the viewer "
    "outside the restricted tool environment using START_WORKFLOW.cmd in Windows, "
    "then retry. MNE does not need to be reinstalled; source files were not changed."
)


def checked_mne_python(runtime):
    python = Path(runtime["mne_python"])
    try:
        if not python.is_file():
            raise ValueError("MNE-Python executable missing. Update mne_python in pipeline_config.json.")
        result = subprocess.run(
            [str(python), "--version"], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except PermissionError as error:
        raise ValueError(ACCESS_MESSAGE) from error
    except subprocess.TimeoutExpired as error:
        raise ValueError("MNE-Python startup check timed out. Check the installed Python runtime.") from error
    if result.returncode != 0:
        raise ValueError("MNE-Python could not start: " + (result.stderr or result.stdout).strip())
    return python
