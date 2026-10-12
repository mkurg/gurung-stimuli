"""Offline checks of export logic; these do not test MNE's BrainVision reader."""

import contextlib
import csv
import hashlib
import io
import json
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

import brainvision_to_praat as converter


class SyntheticRaw:
    def __init__(self, samples, sfreq=1000):
        self.samples = samples.copy()
        self.n_times = np.int64(samples.shape[1])
        self.ch_names = ["Cz", "Microphone"]
        self.info = {"sfreq": sfreq}

    def pick(self, names):
        self.samples = self.samples[[self.ch_names.index(name) for name in names]]
        self.ch_names = list(names)

    def get_data(self, start, stop):
        return self.samples[:, start:stop]


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="praat-converter-check-")
        self.root = Path(self.temporary.name)
        self.vhdr = self.root / "test.vhdr"
        self.eeg = self.root / "test.eeg"
        self.vmrk = self.root / "test.vmrk"
        self.vhdr.write_text(
            "Brain Vision Data Exchange Header File Version 1.0\n"
            "[Common Infos]\nCodepage=UTF-8\nDataFile=test.eeg\n"
            "MarkerFile=test.vmrk\nDataFormat=BINARY\n"
            "DataOrientation=MULTIPLEXED\nNumberOfChannels=2\nSamplingInterval=1000\n"
            "[Binary Infos]\nBinaryFormat=INT_16\n"
            "[Channel Infos]\nCh1=Cz,,1,uV\nCh2=Microphone,,1,uV\n"
            "[Comment]\nArbitrary comment without an equals sign\n",
            encoding="utf-8",
        )
        self.eeg.write_bytes(b"Synthetic source data preserved unchanged")
        self.vmrk.write_text(
            "Brain Vision Data Exchange Marker File Version 1.0\n"
            "[Common Infos]\nCodepage=UTF-8\nDataFile=test.eeg\n"
            "[Marker Infos]\n"
            "Mk1=New Segment,,1,1,0,20261001220000000000\n"
            "Mk2=Stimulus,S  1,1001,1,0\n"
            "Mk3=Response,R  2,1001,1,0\n"
            'Mk4=Comment,caf\u00e9 \\1 "quoted",2001,25,2\n'
            "Mk5=Stimulus,S  3,3001,1,0\n",
            encoding="utf-8",
        )
        self.samples = np.array([
            np.zeros(3001),
            np.sin(np.arange(3001) * 0.05) * 0.000003,
        ])

    def tearDown(self):
        self.temporary.cleanup()

    def fake_mne(self, sfreq=1000):
        return SimpleNamespace(
            __version__="synthetic-test-double",
            io=SimpleNamespace(read_raw_brainvision=lambda *args, **kwargs: SyntheticRaw(self.samples, sfreq)),
        )

    def export(self, sfreq=1000):
        with patch.dict("sys.modules", {"mne": self.fake_mne(sfreq)}), contextlib.redirect_stdout(io.StringIO()):
            return converter.export_recording(self.vhdr, "Microphone")

    def test_full_export_preserves_samples_times_codes_and_sources(self):
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.vhdr, self.eeg, self.vmrk)}
        output = self.export()
        with wave.open(str(output / "test.wav"), "rb") as wav:
            self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()), (1, 2, 1000, 3001))
            audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")
        expected = self.samples[1] / np.max(np.abs(self.samples[1])) * (0.95 * 32767)
        self.assertLessEqual(float(np.max(np.abs(audio - expected))), 0.500001)
        with (output / "test_markers.tsv").open(encoding="utf-8-sig", newline="") as table:
            rows = list(csv.DictReader(table, delimiter="\t"))
        self.assertEqual([float(row["onset_seconds"]) for row in rows], [0, 1, 1, 2, 3])
        self.assertEqual([row["position_1based"] for row in rows], ["1", "1001", "1001", "2001", "3001"])
        self.assertEqual(rows[3]["description"], 'caf\u00e9 , "quoted"')
        self.assertEqual(rows[3]["size_samples"], "25")
        self.assertEqual(rows[3]["channel"], "2")
        grid = (output / "test.TextGrid").read_text(encoding="utf-8")
        self.assertIn("xmax = 3.0009999999999999", grid)
        self.assertIn("points: size = 4", grid)
        self.assertIn('mark = "S 1 | R 2"', grid)
        self.assertNotIn("Mk2: Stimulus/", grid)
        self.assertIn('name = "speech_onset"', grid)
        self.assertIn('name = "speech_onset"\n        xmin = 0\n        xmax = 3.0009999999999999\n        points: size = 0', grid)
        self.assertIn('class = "IntervalTier"\n        name = "transcription"', grid)
        self.assertIn("intervals: size = 1", grid)
        self.assertTrue(grid.rstrip().endswith('text = ""'))
        metadata = json.loads((output / "test_export.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["marker_count"], 5)
        for path, digest in before.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_second_export_does_not_overwrite_annotations(self):
        first = self.export()
        annotation = first / "test_annotated.TextGrid"
        annotation.write_text("Existing manual annotations", encoding="utf-8")
        second = self.export()
        self.assertNotEqual(first, second)
        self.assertEqual(annotation.read_text(encoding="utf-8"), "Existing manual annotations")

    def test_compact_labels_keep_codes_and_blank_non_trigger_times(self):
        markers = converter.read_markers(self.vmrk, 3001, 2, 1000)
        self.assertEqual([converter.marker_code_label(m) for m in markers], ["", "S 1", "R 2", "", "S 3"])
        grid = converter.textgrid_text(markers, 3.001)
        self.assertIn('number = 2', grid)
        self.assertIn('points: size = 4', grid)

    def test_numpy_sample_count_serializes_as_json_integer(self):
        output = self.export()
        metadata = json.loads((output / "test_export.json").read_text(encoding="utf-8"))
        self.assertIs(type(metadata["sample_count"]), int)
        self.assertEqual(metadata["sample_count"], 3001)
        self.assertEqual(metadata["duration_seconds"], 3.001)

    def test_out_of_range_marker_stops_before_creating_output(self):
        with self.vmrk.open("a", encoding="utf-8") as markers:
            markers.write("Mk6=Stimulus,S  4,3002,1,0\n")
        with self.assertRaisesRegex(ValueError, "outside"):
            self.export()
        self.assertFalse((self.root / "praat_export").exists())

    def test_fractional_rate_is_not_silently_rounded(self):
        with self.assertRaisesRegex(ValueError, "not an exact integer"):
            self.export(1000.001)
        self.assertFalse((self.root / "praat_export").exists())

    def test_missing_linked_file_stops(self):
        self.eeg.unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            self.export()

    def test_silent_channel_stops_before_creating_output(self):
        self.samples[1] = 0
        with self.assertRaisesRegex(ValueError, "entirely zero"):
            self.export()
        self.assertFalse((self.root / "praat_export").exists())


if __name__ == "__main__":
    unittest.main()
