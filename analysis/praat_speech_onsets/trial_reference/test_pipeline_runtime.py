import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline_runtime import checked_mne_python


class RuntimeTests(unittest.TestCase):
    runtime = {"mne_python": "installed/python.exe"}

    def test_denied_path_has_actionable_message(self):
        with patch.object(Path, "is_file", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(ValueError, "START_WORKFLOW.cmd"):
                checked_mne_python(self.runtime)

    def test_denied_launch_has_actionable_message(self):
        with patch.object(Path, "is_file", return_value=True), patch("pipeline_runtime.subprocess.run", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(ValueError, "does not need to be reinstalled"):
                checked_mne_python(self.runtime)

    def test_missing_runtime_is_not_a_permission_error(self):
        with patch.object(Path, "is_file", return_value=False):
            with self.assertRaisesRegex(ValueError, "executable missing"):
                checked_mne_python(self.runtime)

    def test_success_probes_the_exact_executable_without_a_shell(self):
        result = subprocess.CompletedProcess([], 0, "Python 3.14.4", "")
        with patch.object(Path, "is_file", return_value=True), patch("pipeline_runtime.subprocess.run", return_value=result) as run:
            self.assertEqual(checked_mne_python(self.runtime), Path(self.runtime["mne_python"]))
            self.assertEqual(run.call_args.args[0], [str(Path(self.runtime["mne_python"])), "--version"])
            self.assertNotIn("shell", run.call_args.kwargs)

    def test_failed_runtime_and_timeout_are_explicit(self):
        result = subprocess.CompletedProcess([], 1, "", "fixture failure")
        with patch.object(Path, "is_file", return_value=True), patch("pipeline_runtime.subprocess.run", return_value=result):
            with self.assertRaisesRegex(ValueError, "fixture failure"):
                checked_mne_python(self.runtime)
        with patch.object(Path, "is_file", return_value=True), patch("pipeline_runtime.subprocess.run", side_effect=subprocess.TimeoutExpired("python", 10)):
            with self.assertRaisesRegex(ValueError, "timed out"):
                checked_mne_python(self.runtime)

    def test_launcher_checks_access_before_starting_or_reusing_a_viewer(self):
        import launch_workflow
        with patch("sys.argv", ["launch_workflow.py", "--no-browser"]), patch("launch_workflow.checked_mne_python", side_effect=ValueError("denied")), patch("launch_workflow.running_url") as running:
            with self.assertRaisesRegex(ValueError, "denied"):
                launch_workflow.main()
            running.assert_not_called()


if __name__ == "__main__":
    unittest.main()
