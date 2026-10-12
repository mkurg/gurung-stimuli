import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from server import library_counts
from suitability import SuitabilityStore


class Library:
    def __init__(self):
        self.sessions = {"a": {"session_id": "a", "recording": "a", "trials": [
            {"id": "main-001", "kind": "main", "condition": "it_coh"},
            {"id": "main-002", "kind": "main", "condition": "tr_coh"},
            {"id": "main-003", "kind": "main", "condition": "tr_coh"},
            {"id": "practice-01", "kind": "practice", "condition": "tr_coh"},
            {"id": "event-01", "kind": "events", "condition": "it_coh"},
        ]}}
        self.annotations = {}

    def listing(self):
        return {"sessions": [{"session_id": key} for key in self.sessions]}

    def get(self, key):
        self.annotations.setdefault(key, {"state": "ready", "trials": {
            trial["id"]: {"status": "ok", "onset_count": 1, "speech_onset_eeg_s": 2.0, "transcription": "sentence"}
            for trial in self.sessions[key]["trials"]}})
        return {"session": self.sessions[key], "reader": SimpleNamespace(read=lambda: self.annotations[key])}


class CountTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SuitabilityStore(Path(self.temp.name) / "flags.sqlite3")
        self.library = Library()

    def tearDown(self):
        self.temp.cleanup()

    def counts(self):
        return library_counts(self.library, self.store)["counts"]

    def test_annotated_trials_without_flags_included_practice_and_events_excluded(self):
        self.assertEqual(self.counts(), {"itr": 1, "tr_erg": 0, "tr_zero": 2})

    def test_both_nonblank_transcription_and_unique_onset_are_required(self):
        self.library.get("a")
        trials = self.library.annotations["a"]["trials"]
        trials["main-001"]["transcription"] = " \n\t"
        trials["main-002"].update(status="missing_onset", onset_count=0, speech_onset_eeg_s=None)
        trials["main-003"].update(status="multiple_onsets", onset_count=2, speech_onset_eeg_s=None)
        self.assertEqual(self.counts(), {"itr": 0, "tr_erg": 0, "tr_zero": 0})
        trials["main-001"]["transcription"] = "transcribed sentence"
        self.assertEqual(self.counts(), {"itr": 1, "tr_erg": 0, "tr_zero": 0})
        trials["main-002"].update(status="ok", onset_count=1, speech_onset_eeg_s=6.0)
        self.assertEqual(self.counts(), {"itr": 1, "tr_erg": 0, "tr_zero": 1})

    def test_zero_second_onset_is_not_treated_as_missing(self):
        self.library.get("a")
        self.library.annotations["a"]["trials"]["main-001"]["speech_onset_eeg_s"] = 0.0
        self.assertEqual(self.counts()["itr"], 1)

    def test_ergative_flag_alone_does_not_count_unannotated_sentence(self):
        self.library.get("a")
        self.library.annotations["a"]["trials"]["main-002"]["transcription"] = ""
        self.store.set_flag("a", "main-002", "ergative", True)
        self.assertEqual(self.counts(), {"itr": 1, "tr_erg": 0, "tr_zero": 1})

    def test_invalid_textgrid_does_not_produce_fresh_partial_totals(self):
        self.library.get("a")
        self.library.annotations["a"] = {"state": "error", "message": "TextGrid is incomplete"}
        with self.assertRaisesRegex(ValueError, "TextGrid is incomplete"):
            self.counts()

    def test_need_help_does_not_change_any_counts(self):
        before = self.counts()
        for trial in self.library.sessions["a"]["trials"]:
            self.store.set_flag("a", trial["id"], "need_help", True)
        self.assertEqual(self.counts(), before)

    def test_ergative_moves_transitive_between_categories(self):
        self.store.set_flag("a", "main-002", "ergative", True)
        self.assertEqual(self.counts(), {"itr": 1, "tr_erg": 1, "tr_zero": 1})
        self.store.set_flag("a", "main-002", "ergative", False)
        self.assertEqual(self.counts(), {"itr": 1, "tr_erg": 0, "tr_zero": 2})

    def test_unsuitable_excludes_all_three_categories_and_can_be_undone(self):
        self.store.set_flag("a", "main-002", "ergative", True)
        for trial in ("main-001", "main-002", "main-003"):
            self.store.set("a", trial, True)
        self.assertEqual(self.counts(), {"itr": 0, "tr_erg": 0, "tr_zero": 0})
        self.store.set("a", "main-002", False)
        self.assertEqual(self.counts(), {"itr": 0, "tr_erg": 1, "tr_zero": 0})

    def test_new_recordings_included_and_flags_are_session_scoped(self):
        self.store.set("a", "main-001", True)
        self.store.set_flag("a", "main-002", "ergative", True)
        second = copy.deepcopy(self.library.sessions["a"])
        second.update(session_id="b", recording="b")
        self.library.sessions["b"] = second
        result = library_counts(self.library, self.store)
        self.assertEqual(result["recordings"], 2)
        self.assertEqual(result["counts"], {"itr": 1, "tr_erg": 1, "tr_zero": 3})

    def test_invalid_recording_or_condition_not_silently_skipped(self):
        self.library.sessions["b"] = {"session_id": "b", "recording": "b", "trials": [
            {"id": "main-001", "kind": "main", "condition": "unknown"}]}
        with self.assertRaisesRegex(ValueError, "Unknown main-trial condition"):
            self.counts()
        self.library.get = lambda key: (_ for _ in ()).throw(ValueError("unavailable"))
        with self.assertRaisesRegex(ValueError, "unavailable"):
            self.counts()


if __name__ == "__main__":
    unittest.main()
