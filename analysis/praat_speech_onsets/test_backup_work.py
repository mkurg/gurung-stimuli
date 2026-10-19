import copy
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import backup_work as work

sys.path.insert(0, str(work.ROOT / "trial_reference"))
import annotations
import suitability
from test_annotations import annotation_grid, annotation_session


class LatestBackupTests(unittest.TestCase):
    def test_legacy_snapshot_is_default_without_pointer(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(work, "ROOT", Path(tmp)):
            self.assertEqual(work.default_backup(), Path(tmp) / "saved_work")

    def test_pointer_selects_current_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(work, "ROOT", Path(tmp)):
            (Path(tmp) / "latest_backup.json").write_bytes(work.json_bytes(
                {"format_version": 1, "directory": "saved_work_20261019"}))
            self.assertEqual(work.default_backup(), Path(tmp) / "saved_work_20261019")

    def test_pointer_cannot_escape_checkout(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(work, "ROOT", Path(tmp)):
            (Path(tmp) / "latest_backup.json").write_bytes(work.json_bytes(
                {"format_version": 1, "directory": "../other"}))
            with self.assertRaisesRegex(ValueError, "escapes"):
                work.default_backup()

    def test_unknown_pointer_format_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(work, "ROOT", Path(tmp)):
            (Path(tmp) / "latest_backup.json").write_bytes(work.json_bytes(
                {"format_version": 2, "directory": "saved_work"}))
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                work.default_backup()


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "original"
        viewer = self.source / "trial_reference"
        (viewer / "recordings").mkdir(parents=True)
        self.old_recordings = self.root / "old" / "EEG recs"
        self.new_recordings = self.root / "new" / "EEG recs"
        for root in (self.old_recordings, self.new_recordings):
            (root / "001i" / "psychopy").mkdir(parents=True)
            (root / "001i" / "001i.wav").write_bytes(b"unchanged AUX waveform")
        self.config = {"vhdr": str(self.old_recordings / "001i" / "001i.vhdr"),
                       "stimtrak_wav": str(self.old_recordings / "001i" / "001i.wav"),
                       "textgrid": str(self.old_recordings / "001i" / "001i_annotations.TextGrid"),
                       "audio_dir": str(self.old_recordings / "001i" / "psychopy")}
        (viewer / "session_config.json").write_bytes(work.json_bytes(self.config))
        self.payload = annotations.textgrid_io.getTextgridAsStr(
            annotation_grid([(2, "s")]), format="long_textgrid", includeBlankSpaces=True).encode("utf-8")
        Path(self.config["textgrid"]).write_bytes(self.payload)
        self.session = annotation_session()
        self.session.update(session_id="a" * 64, recording="001i", sources=[])
        for trial in self.session["trials"]:
            trial.setdefault("condition", "it_coh")
        self.server = SimpleNamespace(build_session=lambda config: (copy.deepcopy(self.session), {}),
                                      file_hash=lambda path: work.sha256(Path(path).read_bytes()))
        self.patcher = patch.object(work, "modules", return_value=(self.server, annotations, suitability))
        self.patcher.start()
        store = suitability.SuitabilityStore(viewer / "suitability.sqlite3")
        store.set(self.session["session_id"], "main-001", False)
        store.set_flag(self.session["session_id"], "main-002", "ergative", True)
        store.set_flag(self.session["session_id"], "main-001", "need_help", True)
        self.backup = self.root / "saved_work"
        work.capture(self.source, self.old_recordings, self.backup)
        self.workspace = self.root / "fresh-checkout" / "analysis" / "praat_speech_onsets"
        (self.workspace / "trial_reference").mkdir(parents=True)

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def recover(self, **kwargs):
        return work.restore(self.backup, self.new_recordings, workspace=self.workspace, **kwargs)

    def test_exact_bytes_and_database_flags_survive_relocation(self):
        self.recover()
        viewer = self.workspace / "trial_reference"
        restored = work.read_json(viewer / "session_config.json")
        self.assertEqual(Path(restored["textgrid"]).read_bytes(), self.payload)
        self.assertTrue(Path(restored["vhdr"]).is_relative_to(self.new_recordings))
        self.assertEqual(Path(restored["experiment_dir"]), self.workspace.parents[1] / "isolated part")
        before = work.decisions(self.backup / "trial_decisions.sqlite3", self.session["session_id"])
        self.assertEqual(before, work.decisions(viewer / "suitability.sqlite3", self.session["session_id"]))
        self.assertTrue(before[1]["main-002"]["marked"])
        self.assertTrue(before[2]["main-001"]["marked"])

    def test_dry_run_does_not_write_annotations_or_configuration(self):
        self.recover(dry_run=True)
        self.assertFalse((self.new_recordings / "001i" / "001i_annotations.TextGrid").exists())
        self.assertEqual(list((self.workspace / "trial_reference").iterdir()), [])

    def test_changed_annotations_are_never_overwritten(self):
        path = self.new_recordings / "001i" / "001i_annotations.TextGrid"
        path.write_bytes(b"newer manual work")
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            self.recover()
        self.assertEqual(path.read_bytes(), b"newer manual work")
        self.assertFalse((self.workspace / "trial_reference" / "suitability.sqlite3").exists())

    def test_wrong_recording_identity_is_rejected_before_writing(self):
        self.session["session_id"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "Different original recording"):
            self.recover()
        self.assertEqual(list((self.workspace / "trial_reference").iterdir()), [])

    def test_changed_wav_is_rejected(self):
        (self.new_recordings / "001i" / "001i.wav").write_bytes(b"shifted waveform")
        with self.assertRaisesRegex(ValueError, "Different StimTrak WAV"):
            self.recover()

    def test_corrupt_backup_is_rejected(self):
        path = self.backup / "recordings" / "001i" / "001i_annotations.TextGrid"
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            work.verify(self.backup)

    def test_backup_checksum_includes_exact_newlines(self):
        index = work.verify(self.backup)
        relative = "recordings/001i/001i_annotations.TextGrid"
        self.assertEqual(index["sha256"][relative], work.sha256(self.payload))

    def test_an_existing_snapshot_cannot_be_replaced(self):
        with self.assertRaisesRegex(ValueError, "already exists"):
            work.capture(self.source, self.old_recordings, self.backup)

    def test_absolute_and_traversal_paths_are_rejected(self):
        for relative in ("../escape", "/escape", "C:/escape", "", "nested/../../escape"):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                work.checked_join(self.root, relative)

    def test_active_database_is_not_replaced(self):
        path = self.workspace / "trial_reference" / "suitability.sqlite3-wal"
        path.write_bytes(b"active work")
        with self.assertRaisesRegex(ValueError, "Stop the existing viewer"):
            self.recover()


if __name__ == "__main__":
    unittest.main()
