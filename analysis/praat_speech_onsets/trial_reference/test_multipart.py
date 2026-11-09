import copy
import csv
import io
import json
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from annotations import AnnotationReader, analysis_csv, textgrid_io
from server import build_session, library_counts
from brainvision_to_praat import read_markers, textgrid_text
from recording_library import RecordingLibrary, bundle
from suitability import SuitabilityStore


class MultipartTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.audio = self.root / "audio"
        self.audio.mkdir()
        self.experiment = self.root / "experiment"
        (self.experiment / "Conds").mkdir(parents=True)
        self.parts = []
        groups = [(200, 1, 11, 202), (200, 1, 12, 202), (200, 1, 13, 202)]
        self.write_csv(self.audio / "eeg_triggers.csv", [
            {"serial_sent": "1", "trigger_index": str(index + 1), "trigger_code": str(code), "label": label}
            for index, (code, label) in enumerate(
                (pair for number, codes in enumerate(groups, 1)
                 for pair in zip(codes, [f"isolated_trial{number:03d}_target_onset", f"isolated_trial{number:03d}_condition_1",
                                         f"isolated_trial{number:03d}_item{codes[2]:03d}", f"isolated_trial{number:03d}_end"])))])
        values = struct.pack("<1000h", *range(1000))
        self.write_wav(self.audio / "full_session.wav", values, 100)
        segments, conditions = [], []
        for number, start in ((1, 100), (2, 300), (3, 500)):
            stem = f"001_isolated_main_l1_trial{number:03d}_imageset{number:02d}_cond_tr"
            self.write_wav(self.audio / (stem + ".wav"), values[start * 2:(start + 100) * 2], 100)
            segments.append({"stem": stem, "status": "written", "onset_sample": start + 10,
                             "stop_sample": start + 90, "clip_start_sample": start,
                             "clip_end_sample": start + 100, "n_frames": 100})
            (self.experiment / f"picture{number}.jpg").write_bytes(b"fixture picture")
            conditions.append({"item_trigger": number + 10, "dataset_number": number,
                               "condition_id": "tr_coh", "condition_trigger": 1, "stimulus_set": 1,
                               "target_image": f"picture{number}.jpg", "dataset_label": "sit_wash_dish"})
        self.write_csv(self.audio / "recording_segments.csv", segments)
        self.write_csv(self.experiment / "Conds/isolated_main_list1_all_120.csv", conditions)
        (self.experiment / "Conds/isolated_practice.csv").write_text("practice_index,target_image,target_role\n")
        self.make_part("001i", [(200, 1), (1, 1.2), (11, 1.4), (202, 2.5), (200, 3), (1, 3.2), (12, 3.4)])
        self.make_part("001ipt2", [(202, .5), (200, 1), (1, 1.2), (13, 1.4), (202, 2.5)])
        self.config = dict(self.parts[0], parts=self.parts, audio_dir=str(self.audio), experiment_dir=str(self.experiment))
        self.session, self.assets = build_session(self.config)

    def tearDown(self):
        self.temp.cleanup()

    def write_wav(self, path, payload, rate):
        with wave.open(str(path), "wb") as wav:
            wav.setparams((1, 2, rate, 0, "NONE", "not compressed"))
            wav.writeframes(payload)

    def write_csv(self, path, rows):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def make_part(self, stem, markers):
        header = self.root / (stem + ".vhdr")
        marker = self.root / (stem + ".vmrk")
        (self.root / (stem + ".eeg")).write_bytes(b"\0\0" * 4000)
        header.write_text(f"Brain Vision Data Exchange Header File Version 1.0\n[Common Infos]\nCodepage=UTF-8\nDataFile={stem}.eeg\nMarkerFile={stem}.vmrk\nDataFormat=BINARY\nDataOrientation=MULTIPLEXED\nNumberOfChannels=1\nSamplingInterval=1000\n[Binary Infos]\nBinaryFormat=INT_16\n[Channel Infos]\nCh1=AUX1,,1,uV\n")
        marker.write_text(f"BrainVision Data Exchange Marker File Version 1.0\n[Common Infos]\nCodepage=UTF-8\nDataFile={stem}.eeg\n[Marker Infos]\n" +
                          "".join(f"Mk{i}=Stimulus,S {code},{round(time * 1000) + 1},1,0\n" for i, (code, time) in enumerate(markers, 1)))
        wav = self.root / (stem + ".wav")
        self.write_wav(wav, b"\0\0" * 4000, 1000)
        grid = self.root / (stem + "_annotations.TextGrid")
        parsed = read_markers(marker, 4000, 1, 1000)
        grid.write_text(textgrid_text(parsed, 4), encoding="utf-8")
        self.parts.append({"vhdr": str(header), "stimtrak_wav": str(wav), "textgrid": str(grid)})

    def save_annotations(self, part, points, intervals):
        path = Path(self.parts[part]["textgrid"])
        grid = textgrid_io.parseTextgridStr(path.read_text(encoding="utf-8"), includeEmptyIntervals=True)
        grid["tiers"][0]["entries"] = [(float(time), label) for time, label in grid["tiers"][0]["entries"]]
        grid["tiers"][1]["entries"] = points
        grid["tiers"][2]["entries"] = intervals
        path.write_text(textgrid_io.getTextgridAsStr(grid, format="long_textgrid", includeBlankSpaces=True), encoding="utf-8")

    def fill_both(self):
        self.save_annotations(0, [(1.6, "s"), (3.6, "s")], [(0, 1.6, ""), (1.6, 2, "first"), (2, 3.6, ""), (3.6, 4, "boundary")])
        self.save_annotations(1, [(.3, "s"), (1.8, "s")], [(0, .7, "continuation"), (.7, 1.8, ""), (1.8, 2.7, "third"), (2.7, 4, "")])

    def test_builder_preserves_local_times_and_identifies_boundary(self):
        self.assertEqual(self.session["recording"], "001i")
        self.assertEqual(self.session["validation"]["main_trials"], 3)
        self.assertEqual(self.session["validation"]["matched_triggers"], 12)
        self.assertEqual(len(self.session["eeg_parts"]), 2)
        first, boundary, third = self.session["trials"]
        self.assertEqual((first["start"], third["start"]), (1, 1))
        self.assertEqual(third["eeg_part"], "001ipt2")
        self.assertTrue(boundary["recording_interrupted"])
        self.assertEqual(boundary["start"], 3)
        self.assertIsNone(boundary["end"])
        self.assertEqual(boundary["end_in_eeg_part"], .5)
        self.assertEqual(boundary["annotation_end"], 4)
        self.assertEqual(len({t["marker_id"] for t in self.session["triggers"]}), 12)

    def test_both_textgrids_supply_only_same_part_latencies(self):
        self.fill_both()
        snapshot = AnnotationReader(self.parts[0]["textgrid"], self.session).read()
        self.assertEqual(snapshot["state"], "ready", snapshot.get("message"))
        self.assertEqual(len(snapshot["trials"]), 3)
        for number, latency in ((1, 600), (2, 600), (3, 800)):
            self.assertAlmostEqual(snapshot["trials"][f"main-{number:03d}"]["latency_ms"], latency)
        self.assertEqual(snapshot["trials"]["main-003"]["eeg_part"], "001ipt2")
        self.assertEqual(snapshot["trials"]["main-002"]["transcription"], "boundary")
        self.assertTrue(snapshot["trials"]["main-002"]["warnings"])
        self.assertEqual(snapshot["unassigned_onsets"][0]["eeg_part"], "001ipt2")
        self.assertEqual(snapshot["unassigned_transcriptions"][0]["text"], "continuation")

    def test_saving_second_grid_refreshes_without_changing_first(self):
        self.fill_both()
        reader = AnnotationReader(self.parts[0]["textgrid"], self.session)
        before = reader.read()
        self.save_annotations(1, [(1.9, "s")], [(0, 1.9, ""), (1.9, 2.7, "updated third"), (2.7, 4, "")])
        after = reader.read()
        self.assertNotEqual(before["sha256"], after["sha256"])
        self.assertEqual(before["parts"][0]["sha256"], after["parts"][0]["sha256"])
        self.assertAlmostEqual(after["trials"]["main-003"]["latency_ms"], 900)
        self.assertEqual(after["trials"]["main-003"]["transcription"], "updated third")

    def test_invalid_second_grid_does_not_return_stale_latencies(self):
        self.fill_both()
        reader = AnnotationReader(self.parts[0]["textgrid"], self.session)
        self.assertEqual(reader.read()["state"], "ready")
        Path(self.parts[1]["textgrid"]).write_text("incomplete save")
        after = reader.read()
        self.assertEqual(after["state"], "error")
        self.assertEqual(after["trials"], {})

    def test_exports_name_the_correct_grid_and_keep_interruption_explicit(self):
        self.fill_both()
        snapshot = AnnotationReader(self.parts[0]["textgrid"], self.session).read()
        exported = list(csv.DictReader(io.StringIO(analysis_csv(self.session, {}, snapshot).decode("utf-8-sig"))))
        self.assertEqual(exported[2]["textgrid_path"], self.parts[1]["textgrid"])
        self.assertEqual(exported[2]["textgrid_sha256"], snapshot["parts"][1]["sha256"])
        self.assertEqual(exported[1]["recording_interrupted"], "1")
        self.assertEqual(exported[1]["trial_end_eeg_s"], "")
        self.assertEqual(exported[1]["trial_end_in_eeg_part_s"], "0.5")
        self.assertEqual(exported[1]["trial_end_eeg_part"], "001ipt2")

    def test_global_counts_include_participant_once_and_do_not_mutate_flags(self):
        self.fill_both()
        current = bundle(self.session, self.assets, self.config, self.root / "snapshots")
        library = RecordingLibrary(self.root / "library", current, build_session, self.root / "snapshots")
        store = SuitabilityStore(self.root / "flags.sqlite3")
        store.set_flag(self.session["session_id"], "main-002", "ergative", True)
        counts = library_counts(library, store)
        self.assertEqual(counts["recordings"], 1)
        self.assertEqual(counts["counts"], {"itr": 0, "tr_erg": 1, "tr_zero": 2})
        self.assertEqual(store.read(self.session["session_id"]), {})

    def test_part_order_and_completeness_must_match_the_log(self):
        altered = copy.deepcopy(self.config)
        altered["parts"].reverse()
        altered.update(altered["parts"][0])
        with self.assertRaisesRegex(ValueError, "sequence mismatch"):
            build_session(altered)
        marker = self.root / "001ipt2.vmrk"
        lines = marker.read_text().splitlines()
        marker.write_text("\n".join(lines[:-1]) + "\n")
        with self.assertRaisesRegex(ValueError, "counts disagree"):
            build_session(self.config)


if __name__ == "__main__":
    unittest.main()
