import copy
import unittest
from unittest.mock import patch

from seminar_stats import collect, latency_summary, report, summarize, trial_rows


def fixture():
    trials = [{"id": f"main-{i:03d}", "kind": "main", "number": i,
               "condition": "it_coh" if i == 1 else "tr_coh", "item": 30 + i} for i in range(1, 7)]
    trials.append({"id": "practice-01", "kind": "practice"})
    session = {"session_id": "a" * 64, "recording": "001i", "participant": "001", "list": 1,
               "trials": trials, "suitability": {"main-003": {"unsuitable": True}},
               "ergative": {"main-002": {"marked": True}, "main-004": {"marked": False}},
               "need_help": {"main-001": {"marked": True}, "main-003": {"marked": True}}}
    annotations = {t["id"]: {"status": "ok", "onset_count": 1, "speech_onset_eeg_s": 2.,
                             "s200_eeg_s": 1., "latency_ms": 1000., "transcription": "sentence"}
                   for t in trials if t["kind"] == "main"}
    annotations["main-005"].update(status="multiple_onsets", onset_count=2, speech_onset_eeg_s=None, latency_ms=None)
    annotations["main-006"]["transcription"] = "   "
    grid = {"trials": annotations, "sha256": "b" * 64, "path": "saved.TextGrid", "saved_at_utc": "2026-10-13T10:00:00Z",
            "unassigned_onsets": [], "unassigned_transcriptions": []}
    return {"generated_at_utc": "2026-10-13T10:00:00+00:00", "bundles": [{"session": session, "annotations": grid}],
            "viewer_counts": {"counts": {"itr": 1, "tr_erg": 1, "tr_zero": 1}, "recordings": 1}}


class SeminarStatsTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = fixture()
        self.rows = trial_rows(self.snapshot)

    def test_main_only_and_eligibility_require_both_annotations(self):
        self.assertEqual(len(self.rows), 6)
        self.assertEqual([r["trial_id"] for r in self.rows if r["eligible"]], ["main-001", "main-002", "main-004"])

    def test_help_is_not_an_exclusion_and_overlaps_unsuitable(self):
        result = summarize(self.rows, self.snapshot)["totals"]
        self.assertEqual(result["need_help_all_main"], 2)
        self.assertEqual(result["need_help_eligible"], 1)
        self.assertEqual(result["need_help_unsuitable"], 1)

    def test_readiness_counts_are_mutually_exclusive(self):
        result = summarize(self.rows, self.snapshot)["totals"]
        self.assertEqual((result["eligible"], result["unsuitable"], result["pending_not_unsuitable"]), (3, 1, 2))
        self.assertEqual(sum(result[k] for k in ("eligible", "unsuitable", "pending_not_unsuitable")), result["main_trials"])

    def test_cutoff_boundary_is_inclusive(self):
        result = summarize(self.rows, self.snapshot)["timing_cutoffs"]
        self.assertEqual(result[0]["retained"], 3)
        self.assertEqual(result[1]["retained"], 0)

    def test_zero_flag_and_missing_decision_are_distinguishable(self):
        by_id = {r["trial_id"]: r for r in self.rows}
        self.assertEqual(by_id["main-004"]["category"], "Tr zero")
        self.assertTrue(by_id["main-004"]["ergative_flag_saved"])
        self.assertFalse(by_id["main-006"]["ergative_flag_saved"])

    def test_source_latency_must_match_s200_difference(self):
        self.snapshot["bundles"][0]["annotations"]["trials"]["main-001"]["latency_ms"] = 500.
        with self.assertRaisesRegex(ValueError, "Invalid SOL"):
            trial_rows(self.snapshot)

    def test_duplicate_trials_are_rejected(self):
        self.snapshot["bundles"].append(copy.deepcopy(self.snapshot["bundles"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate trial"):
            trial_rows(self.snapshot)

    def test_totals_are_cross_checked_against_viewer(self):
        self.snapshot["viewer_counts"]["counts"]["itr"] = 9
        with self.assertRaisesRegex(ValueError, "do not match"):
            summarize(self.rows, self.snapshot)

    def test_summary_uses_sample_sd_and_linear_quartiles(self):
        s = latency_summary([1000, 2000, 3000, 4000])
        self.assertEqual((s["mean_ms"], s["median_ms"], s["q1_ms"], s["q3_ms"]), (2500, 2500, 1750, 3250))
        self.assertAlmostEqual(s["sd_ms"], 1290.9944487358057)
        self.assertEqual(latency_summary([])["n"], 0)

    def test_collection_defaults_to_all_loaded_recordings(self):
        bundle = self.snapshot["bundles"][0]
        grid = dict(bundle["annotations"], state="ready")
        responses = {"/api/sessions": {"sessions": [{"session_id": "a" * 64}]},
                     "/api/session": bundle["session"], "/api/annotations": grid,
                     "/api/library-counts": self.snapshot["viewer_counts"]}
        with patch("seminar_stats.get_json", side_effect=lambda base, endpoint, sid=None: responses[endpoint]):
            result = collect("http://local-fixture")
            self.assertEqual(len(result["bundles"]), 1)
            with self.assertRaisesRegex(ValueError, "Expected 10"):
                collect("http://local-fixture", 10)

    def test_report_does_not_treat_unannotated_recording_as_zero_latency(self):
        result = summarize(self.rows, self.snapshot)
        blank = copy.deepcopy(result["participants"][0])
        blank.update(recording="002i", eligible=0, sol=latency_summary([]))
        result["participants"].append(blank)
        result["totals"]["participants"] = 2
        result["source_annotations"].append(dict(result["source_annotations"][0], recording="002i"))
        text = report(result, [])
        self.assertIn("All 2 loaded recordings", text)
        self.assertIn("| n.a. | n.a. |", text)


if __name__ == "__main__":
    unittest.main()
