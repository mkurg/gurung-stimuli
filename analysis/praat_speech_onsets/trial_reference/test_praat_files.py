import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from import_recording import place_registered_files
from praat_files import check_praat_targets, place_praat_files, praat_targets
from recording_library import atomic_json, file_hash


class PraatFileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.eeg = self.root / "Desktop" / "EEG recs" / "081i"
        self.eeg.mkdir(parents=True)
        self.header = self.eeg / "081i.vhdr"
        self.header.write_bytes(b"original header")
        self.directory = self.root / "recordings" / ("a" * 20)
        self.directory.mkdir(parents=True)
        self.wav = self.directory / "081i.wav"
        self.grid = self.directory / "081i_annotations.TextGrid"
        self.wav.write_bytes(b"unchanged audio")
        self.grid.write_bytes(b"saved onset and transcription")
        self.config = {"vhdr": str(self.header), "stimtrak_wav": str(self.wav), "textgrid": str(self.grid)}

    def tearDown(self):
        self.temp.cleanup()

    def test_working_files_directly_beside_header_with_exact_bytes(self):
        check_praat_targets(self.header)
        config = place_praat_files(self.config)
        self.assertEqual(Path(config["stimtrak_wav"]), self.eeg / "081i.wav")
        self.assertEqual(Path(config["textgrid"]), self.eeg / "081i_annotations.TextGrid")
        self.assertEqual(Path(config["textgrid"]).read_bytes(), self.grid.read_bytes())
        self.assertEqual(Path(config["stimtrak_wav"]).read_bytes(), self.wav.read_bytes())
        self.assertTrue(self.grid.is_file())

    def test_collision_does_not_overwrite_or_partially_publish(self):
        target = praat_targets(self.header)["textgrid"]
        target.write_bytes(b"existing manual annotations")
        with self.assertRaisesRegex(ValueError, "already exists"):
            check_praat_targets(self.header)
        with self.assertRaisesRegex(ValueError, "already exists"):
            place_praat_files(self.config)
        self.assertEqual(target.read_bytes(), b"existing manual annotations")
        self.assertFalse(praat_targets(self.header)["stimtrak_wav"].exists())

    def test_idempotent_relocation_never_replaces_changed_annotation(self):
        placed = place_praat_files(self.config)
        self.assertEqual(place_praat_files(self.config, reuse_identical=True), placed)
        Path(placed["textgrid"]).write_bytes(b"new user annotations")
        with self.assertRaisesRegex(ValueError, "already exists"):
            place_praat_files(self.config, reuse_identical=True)
        self.assertEqual(Path(placed["textgrid"]).read_bytes(), b"new user annotations")

    def test_registered_paths_and_provenance_updated_without_source_changes(self):
        identity = "a" * 64
        atomic_json(self.directory / "config.json", self.config)
        atomic_json(self.directory / "registration.json", {"session_id": identity})
        atomic_json(self.directory / "provenance.json", {"stimtrak_wav": {"sha256": file_hash(self.wav), "path": str(self.wav)}})
        before = (file_hash(self.wav), file_hash(self.grid), file_hash(self.header))
        with patch("import_recording.build_session", return_value=({"session_id": identity}, {})), \
                patch("import_recording.AnnotationReader") as reader:
            reader.return_value.read.return_value = {"state": "ready"}
            result = place_registered_files(self.directory, log=lambda message: None, output_root=self.eeg.parent)
        self.assertEqual(json.loads((self.directory / "config.json").read_text()), result)
        provenance = json.loads((self.directory / "provenance.json").read_text())
        self.assertEqual(provenance["stimtrak_wav"]["path"], result["stimtrak_wav"])
        self.assertTrue(provenance["relocations"][0]["original_copies_kept"])
        self.assertEqual(before, (file_hash(self.wav), file_hash(self.grid), file_hash(self.header)))

    def test_source_header_elsewhere_still_uses_desktop_recording_folder(self):
        elsewhere = self.root / "Downloads" / "081i.vhdr"
        elsewhere.parent.mkdir()
        elsewhere.write_bytes(self.header.read_bytes())
        config = dict(self.config, vhdr=str(elsewhere))
        result = place_praat_files(config, output_root=self.eeg.parent)
        self.assertEqual(Path(result["stimtrak_wav"]), self.eeg / "081i.wav")
        self.assertEqual(Path(result["textgrid"]), self.eeg / "081i_annotations.TextGrid")


if __name__ == "__main__":
    unittest.main()
