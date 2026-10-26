import copy
import json
import unittest
from pathlib import Path

from server import ROOT, build_session, byte_range, match_trigger_sequence, playback_window


class ReferenceTests(unittest.TestCase):
    def split_recording_fixture(self):
        codes = [200, 2, 17, 202, 200, 1, 98, 202]
        markers = [{"type": "Stimulus", "description": f"S {code}", "marker_id": f"Mk{i + 3}",
                    "onset_seconds": i + 142.9237, "position_1based": i * 10000 + 1429238}
                   for i, code in enumerate(codes)]
        labels = ["rest_eyes_open_start", "rest_eyes_open_finish", "rest_eyes_closed_start", "rest_eyes_closed_finish"]
        logged = [{"serial_sent": "1", "trigger_index": str(i + 1), "trigger_code": "150", "label": label}
                  for i, label in enumerate(labels)]
        logged.extend({"serial_sent": "1", "trigger_index": str(i + 5), "trigger_code": str(code), "label": f"trial_marker_{i}"}
                      for i, code in enumerate(codes))
        return markers, logged

    def test_complete_unrecorded_initial_rest_keeps_exact_eeg_times_and_log_indices(self):
        markers, logged = self.split_recording_fixture()
        before = copy.deepcopy((markers, logged))
        reconciliation = {}
        linked = match_trigger_sequence(markers, logged, reconciliation)
        self.assertEqual([row["code"] for row in linked], [200, 2, 17, 202, 200, 1, 98, 202])
        self.assertEqual(linked[0]["log_index"], 5)
        self.assertEqual(linked[0]["time"], markers[0]["onset_seconds"])
        self.assertEqual(linked[0]["sample_1based"], markers[0]["position_1based"])
        self.assertEqual(len(reconciliation["unrecorded_initial_rest"]), 4)
        self.assertEqual(reconciliation["sent_log_count"], 12)
        self.assertTrue(all("time" not in row for row in reconciliation["unrecorded_initial_rest"]))
        self.assertEqual((markers, logged), before)

    def test_missing_initial_rest_still_requires_every_remaining_code_in_order(self):
        markers, logged = self.split_recording_fixture()
        markers[-2]["description"] = "S 99"
        reconciliation = {}
        with self.assertRaisesRegex(ValueError, "sequence mismatch"):
            match_trigger_sequence(markers, logged, reconciliation)
        self.assertEqual(reconciliation, {})

    def test_missing_initial_rest_does_not_allow_partial_blocks_or_missing_trials(self):
        markers, logged = self.split_recording_fixture()
        for candidate_markers, candidate_log in ((markers, logged[1:]), (markers[:-4], logged), ([], logged[:4])):
            with self.subTest(markers=len(candidate_markers), logged=len(candidate_log)):
                with self.assertRaisesRegex(ValueError, "counts disagree"):
                    match_trigger_sequence(candidate_markers, candidate_log)

    def test_unmatched_prefix_must_be_the_specific_pre_task_rest_block(self):
        markers, logged = self.split_recording_fixture()
        for field, value in (("label", "post_rest_eyes_open_start"), ("trigger_code", "200")):
            changed = copy.deepcopy(logged)
            changed[0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "counts disagree"):
                match_trigger_sequence(markers, changed)

    def test_exact_sequence_needs_no_rest_exception(self):
        markers, logged = self.split_recording_fixture()
        reconciliation = {}
        linked = match_trigger_sequence(markers, logged[4:], reconciliation)
        self.assertEqual(len(linked), 8)
        self.assertEqual(reconciliation, {})

    def test_sequence_requires_matching_count(self):
        with self.assertRaisesRegex(ValueError, "counts disagree"):
            match_trigger_sequence([], [{"serial_sent": "1"}])

    def test_sequence_requires_matching_order(self):
        marker = {"type": "Stimulus", "description": "S 73"}
        with self.assertRaisesRegex(ValueError, "sequence mismatch"):
            match_trigger_sequence([marker], [{"serial_sent": "1", "trigger_code": "40"}])

    def test_range_for_audio_seeking(self):
        self.assertEqual(byte_range("bytes=10-19", 100), (10, 19, True))
        self.assertEqual(byte_range("bytes=90-", 100), (90, 99, True))
        self.assertEqual(byte_range("bytes=-20", 100), (80, 99, True))
        self.assertEqual(byte_range("bytes=90-999", 100), (90, 99, True))
        self.assertEqual(byte_range(None, 100), (0, 99, False))

    def test_invalid_ranges(self):
        for header in ["bytes=100-", "bytes=15-10", "bytes=-0", "bytes=-", "bytes=0-1,8-9"]:
            with self.subTest(header=header), self.assertRaises(ValueError):
                byte_range(header, 100)

    def test_context_is_three_seconds_each_side(self):
        window = playback_window(10000, 14000, 1000, 20000)
        self.assertEqual((window["start"], window["end"]), (7, 17))
        self.assertEqual((window["trial_start"], window["trial_end"]), (10, 14))
        self.assertEqual((window["before_seconds"], window["after_seconds"]), (3, 3))

    def test_context_clamps_to_full_file_bounds(self):
        window = playback_window(1000, 9000, 1000, 10000)
        self.assertEqual((window["start"], window["end"]), (0, 10))
        self.assertEqual((window["before_seconds"], window["after_seconds"]), (1, 1))
        with self.assertRaises(ValueError):
            playback_window(1000, 11000, 1000, 10000)

    def test_real_session_and_known_trial(self):
        config = json.loads((ROOT / "session_config.json").read_text())
        session, assets = build_session(config)
        self.assertEqual(session["validation"], {"matched_triggers": 484, "main_trials": 120, "practice_trials": 10, "unsent_log_entries": 4})
        first = session["trials"][0]
        self.assertEqual(first["id"], "main-001")
        self.assertEqual(first["item"], 73)
        self.assertEqual((first["image_set"], first["stimulus_set"], first["condition"]), (19, 1, "it_coh"))
        self.assertEqual([t["code"] for t in first["triggers"]], [200, 2, 73, 202])
        self.assertAlmostEqual(first["start"], 449.4709, places=4)
        self.assertTrue(first["image_path"].endswith("19_sit_crack egg\\1\\it_target.jpg"))
        self.assertTrue(all(path.is_file() for path in assets.values()))
        self.assertEqual(session["full_recording"]["verified_segments"], 130)
        self.assertEqual(session["full_recording"]["filename"], "full_session.wav")
        self.assertEqual(session["full_recording"]["sample_count"], 46507968)
        self.assertAlmostEqual(first["playback"]["start"], 21095688 / 48000 - 3)
        self.assertAlmostEqual(first["playback"]["end"], 21310689 / 48000 + 3)
        for trial in session["trials"]:
            self.assertIn(trial["audio"].removeprefix("/media/"), assets)
            self.assertIn(trial["image"].removeprefix("/media/"), assets)
            self.assertEqual((trial["playback"]["before_seconds"], trial["playback"]["after_seconds"]), (3, 3))
            if trial["kind"] == "practice":
                self.assertIsNone(trial["start"])
                self.assertEqual(trial["triggers"], [])


if __name__ == "__main__":
    unittest.main()
