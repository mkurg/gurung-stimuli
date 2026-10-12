import csv
import hashlib
import io
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from annotations import AnnotationReader, analysis_csv, map_annotations
from praatio.utilities import textgrid_io
from server import ROOT, build_session
import json


def annotation_session():
    triggers = []
    trials = []
    for number, start, end in [(1, 1.0, 4.0), (2, 5.0, 8.0)]:
        trial_id = f"main-{number:03d}"
        for code, time, role in [(200, start, "target_onset"), (1, start + .2, "condition"),
                                 (number + 70, start + .4, "item"), (202, end, "end")]:
            triggers.append({"marker_id": f"Mk{len(triggers)+1}", "code": code, "time": time,
                             "role": role, "trial_id": trial_id})
        trials.append({"id": trial_id, "kind": "main", "number": number, "start": start, "end": end,
                       "item": number + 70, "condition": "it_coh", "audio_filename": f"trial{number}.wav"})
    trials.append({"id": "practice-01", "kind": "practice", "number": 1, "start": None, "end": None,
                   "item": None, "condition": "practice", "audio_filename": "practice.wav"})
    return {"session_id": "annotation-test", "recording": "test", "participant": "001", "list": 1,
            "sample_rate": 10000, "duration": 10.0, "triggers": triggers, "trials": trials}


def annotation_grid(points=None, intervals=None, old_labels=False):
    session = annotation_session()
    triggers = [(marker["time"], f"Mk{index}: Stimulus/S {marker['code']}" if old_labels else f"S {marker['code']}")
                for index, marker in enumerate(session["triggers"], 1)]
    return {"xmin": 0.0, "xmax": 10.0, "tiers": [
        {"name": "triggers", "class": "TextTier", "xmin": 0.0, "xmax": 10.0, "entries": triggers},
        {"name": "speech_onset", "class": "TextTier", "xmin": 0.0, "xmax": 10.0, "entries": points or []},
        {"name": "transcription", "class": "IntervalTier", "xmin": 0.0, "xmax": 10.0,
         "entries": intervals or [(0, 10, "")]},
    ]}


class AnnotationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="praat-reference-test-")
        self.root = Path(self.temporary.name)
        self.path = self.root / "saved.TextGrid"
        self.session = annotation_session()
        self.reader = AnnotationReader(self.path, self.session, self.root / "snapshots")

    def tearDown(self):
        self.temporary.cleanup()

    def save(self, grid, format="long_textgrid", encoding="utf-8"):
        self.path.write_text(textgrid_io.getTextgridAsStr(grid, format=format, includeBlankSpaces=True), encoding=encoding)

    def test_latency_from_marked_point_not_transcription_boundary(self):
        self.save(annotation_grid([(2.375, "s")], [(0, 2.5, ""), (2.5, 3.5, "sentence"), (3.5, 10, "")]))
        snapshot = self.reader.read()
        first = snapshot["trials"]["main-001"]
        self.assertEqual(snapshot["state"], "ready")
        self.assertEqual(first["latency_s"], 1.375)
        self.assertEqual(first["latency_ms"], 1375)
        self.assertEqual(first["speech_onset_eeg_s"], 2.375)
        self.assertEqual(first["transcription"], "sentence")

    def test_legacy_and_short_labels_unicode_long_and_short_formats(self):
        sentence = 'thagu "quoted" lurisy\u00f5\nsecond line'
        for old_labels in (False, True):
            for format, encoding in [("long_textgrid", "utf-16"), ("short_textgrid", "utf-8")]:
                with self.subTest(old_labels=old_labels, format=format):
                    self.save(annotation_grid([(2, "s")], [(0, 2, ""), (2, 3, sentence), (3, 10, "")], old_labels), format, encoding)
                    snapshot = self.reader.read()
                    self.assertEqual(snapshot["state"], "ready", snapshot.get("message"))
                    self.assertEqual(snapshot["trials"]["main-001"]["transcription"], sentence)

    def test_multiple_points_do_not_choose_first(self):
        self.save(annotation_grid([(2, "s"), (3, "s")]))
        first = self.reader.read()["trials"]["main-001"]
        self.assertEqual(first["status"], "multiple_onsets")
        self.assertEqual(first["onset_count"], 2)
        self.assertIsNone(first["latency_s"])
        self.assertIsNone(first["speech_onset_eeg_s"])

    def test_missing_and_practice_are_not_zero_latency(self):
        self.save(annotation_grid())
        snapshot = self.reader.read()
        self.assertEqual(snapshot["trials"]["main-001"]["status"], "missing_onset")
        self.assertIsNone(snapshot["trials"]["main-001"]["latency_s"])
        self.assertEqual(snapshot["trials"]["practice-01"]["status"], "no_eeg_triggers")
        self.assertIsNone(snapshot["trials"]["practice-01"]["latency_s"])

    def test_no_nearest_preceding_trigger_guess_in_gaps(self):
        self.save(annotation_grid([(0.5, "s"), (4.0, "s"), (4.5, "s"), (5.0, "")]))
        snapshot = self.reader.read()
        self.assertEqual(len(snapshot["unassigned_onsets"]), 3)
        self.assertEqual(snapshot["trials"]["main-002"]["latency_s"], 0)
        self.assertIsNone(snapshot["trials"]["main-001"]["latency_s"])

    def test_transcription_end_can_cross_s202_and_next_s200(self):
        for end in (4.0, 4.5, 5.0, 6.0, 9.0, 10.0):
            with self.subTest(end=end):
                intervals = [(0, 2, ""), (2, end, "first response")]
                if end < 10:
                    intervals.append((end, 10, ""))
                self.save(annotation_grid([(2.375, "s"), (5.5, "s")], intervals))
                snapshot = self.reader.read()
                first = snapshot["trials"]["main-001"]
                second = snapshot["trials"]["main-002"]
                self.assertEqual(snapshot["state"], "ready")
                self.assertEqual(snapshot["unassigned_transcriptions"], [])
                self.assertEqual(first["transcription"], "first response")
                self.assertEqual(first["intervals"][0]["end"], end)
                self.assertEqual(second["transcription"], "")
                self.assertEqual(first["warnings"], [])
                self.assertEqual(second["warnings"], [])
                self.assertEqual(first["latency_ms"], 1375)
                self.assertEqual(second["latency_ms"], 500)

    def test_interval_start_at_next_s200_belongs_to_next_trial(self):
        self.save(annotation_grid(intervals=[(0, 2, ""), (2, 5, "first"), (5, 9, "second"), (9, 10, "")]))
        snapshot = self.reader.read()
        self.assertEqual(snapshot["trials"]["main-001"]["transcription"], "first")
        self.assertEqual(snapshot["trials"]["main-002"]["transcription"], "second")
        self.assertEqual(snapshot["unassigned_transcriptions"], [])

    def test_transcription_start_in_gap_is_not_guessed_from_end(self):
        self.save(annotation_grid(intervals=[(0, 4.5, ""), (4.5, 6, "gap start"), (6, 10, "")]))
        snapshot = self.reader.read()
        self.assertEqual(len(snapshot["unassigned_transcriptions"]), 1)
        self.assertEqual(snapshot["trials"]["main-001"]["transcription"], "")
        self.assertEqual(snapshot["trials"]["main-002"]["transcription"], "")

    def test_extended_transcription_is_exported_without_changing_latency(self):
        self.save(annotation_grid([(2, "s")], [(0, 2, ""), (2, 6, "continued response"), (6, 10, "")]))
        snapshot = self.reader.read()
        exported = list(csv.DictReader(io.StringIO(analysis_csv(self.session, {}, snapshot).decode("utf-8-sig"))))
        self.assertEqual(exported[0]["transcription"], "continued response")
        self.assertEqual(json.loads(exported[0]["transcription_intervals_json"])[0]["end"], 6)
        self.assertEqual(exported[0]["speech_latency_ms"], "1000.0")
        self.assertEqual(exported[0]["annotation_mapping_version"], "2")
        self.assertEqual(exported[0]["annotation_warnings"], "")
        self.assertEqual(exported[1]["transcription"], "")

    def test_new_mapping_snapshot_preserves_older_mapping_record(self):
        self.save(annotation_grid(intervals=[(0, 2, ""), (2, 6, "continued response"), (6, 10, "")]))
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        snapshots = self.root / "snapshots"
        snapshots.mkdir()
        legacy = snapshots / f"{digest}.json"
        legacy.write_text('{"mapping_version": 1}', encoding="utf-8")
        snapshot = self.reader.read()
        self.assertEqual(snapshot["mapping_version"], 2)
        self.assertEqual(json.loads(legacy.read_text())["mapping_version"], 1)
        self.assertEqual(json.loads((snapshots / f"{digest}_mapping_v2.json").read_text())["mapping_version"], 2)

    def test_transcription_without_onset_does_not_invent_latency(self):
        self.save(annotation_grid(intervals=[(0, 2, ""), (2, 3, "sentence"), (3, 10, "")]))
        first = self.reader.read()["trials"]["main-001"]
        self.assertEqual(first["transcription"], "sentence")
        self.assertIsNone(first["latency_s"])

    def test_changed_or_missing_trigger_invalidates_entire_import(self):
        for altered in ("time", "code", "missing"):
            grid = annotation_grid([(2, "s")])
            if altered == "time":
                grid["tiers"][0]["entries"][0] = (1.0001, "S 200")
            elif altered == "code":
                grid["tiers"][0]["entries"][0] = (1.0, "S 201")
            else:
                grid["tiers"][0]["entries"].pop()
            self.save(grid)
            snapshot = self.reader.read()
            self.assertEqual(snapshot["state"], "error")
            self.assertEqual(snapshot["trials"], {})
            with self.assertRaises(ValueError):
                analysis_csv(self.session, {}, snapshot)

    def test_crop_duplicate_tier_and_incomplete_intervals_rejected(self):
        grid = annotation_grid()
        grid["xmax"] = 9
        with self.assertRaises(ValueError):
            map_annotations(grid, self.session)
        grid = annotation_grid()
        grid["tiers"].append(grid["tiers"][0])
        with self.assertRaises(ValueError):
            map_annotations(grid, self.session)
        grid = annotation_grid()
        grid["tiers"][2]["entries"] = [(0, 9, "")]
        with self.assertRaises(ValueError):
            map_annotations(grid, self.session)

    def test_saved_file_updates_and_keeps_reproducible_read_only_snapshots(self):
        self.assertEqual(self.reader.read()["state"], "missing")
        self.save(annotation_grid([(2, "s")]))
        before = self.path.read_bytes()
        first = self.reader.read()
        self.assertEqual(first["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(self.path.read_bytes(), before)
        self.save(annotation_grid([(2.5, "s")]))
        second = self.reader.read()
        self.assertNotEqual(first["sha256"], second["sha256"])
        self.assertEqual(second["trials"]["main-001"]["latency_s"], 1.5)
        self.assertEqual((self.root / "snapshots" / f"{first['sha256']}.TextGrid").read_bytes(), before)
        self.path.write_text("half-written file", encoding="utf-8")
        self.assertEqual(self.reader.read()["state"], "error")
        self.save(annotation_grid([(2.75, "s")]))
        self.assertEqual(self.reader.read()["trials"]["main-001"]["latency_s"], 1.75)

    def test_combined_csv_preserves_unicode_transcript_and_review(self):
        sentence = 'thagu, "quoted" lurisy\u00f5\nsecond line'
        self.save(annotation_grid([(2, "s")], [(0, 2, ""), (2, 3, sentence), (3, 10, "")]))
        snapshot = self.reader.read()
        exported = list(csv.DictReader(io.StringIO(analysis_csv(self.session, {"main-001": {"unsuitable": True}}, snapshot).decode("utf-8-sig"))))
        first = exported[0]
        self.assertEqual(first["transcription"], sentence)
        self.assertEqual(first["speech_latency_ms"], "1000.0")
        self.assertEqual(first["unsuitable"], "1")
        self.assertEqual(first["textgrid_sha256"], snapshot["sha256"])
        self.assertEqual(exported[1]["speech_latency_ms"], "")
        self.assertEqual(exported[2]["annotation_status"], "no_eeg_triggers")

    def test_current_user_grid_reads_without_any_source_changes(self):
        config = json.loads((ROOT / "session_config.json").read_text(encoding="utf-8"))
        session, _ = build_session(config)
        path = Path(config["textgrid"])
        before = path.read_bytes()
        snapshot = AnnotationReader(path, session).read()
        self.assertEqual(snapshot["state"], "ready", snapshot["message"])
        self.assertEqual(len(snapshot["trials"]), 130)
        self.assertEqual(path.read_bytes(), before)

    def test_archive_failure_does_not_claim_source_file_is_missing(self):
        self.save(annotation_grid([(2, "s")]))
        with patch.object(Path, "write_bytes", side_effect=FileNotFoundError("archive path unavailable")):
            snapshot = self.reader.read()
        self.assertEqual(snapshot["state"], "error")
        self.assertIn("archive", snapshot["message"])
        self.assertTrue(self.path.is_file())


if __name__ == "__main__":
    unittest.main()
