import csv
import io
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import handler_class
from suitability import SuitabilityStore, suitability_csv


def fixture_session():
    return {
        "session_id": "test-session", "recording": "test", "participant": "001", "list": 1,
        "trials": [{"id": "main-001", "kind": "main", "number": 1, "item": 73, "condition": "it_coh",
                    "start": 449.4709, "end": 453.9473, "audio_filename": "trial001.wav"}],
    }


class SuitabilityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="trial-suitability-test-")
        self.path = Path(self.temporary.name) / "reviews.sqlite3"
        self.store = SuitabilityStore(self.path)

    def tearDown(self):
        self.temporary.cleanup()

    def test_save_reopen_and_undo(self):
        self.assertEqual(self.store.read("a"), {})
        self.store.set("a", "main-001", True)
        reopened = SuitabilityStore(self.path)
        self.assertTrue(reopened.read("a")["main-001"]["unsuitable"])
        reopened.set("a", "main-001", False)
        self.assertFalse(self.store.read("a")["main-001"]["unsuitable"])
        self.assertTrue(self.store.read("a")["main-001"]["updated_at_utc"])

    def test_recordings_are_isolated(self):
        self.store.set("session-a", "main-001", True)
        self.assertEqual(self.store.read("session-b"), {})
        self.store.set("session-b", "main-001", False)
        self.assertTrue(self.store.read("session-a")["main-001"]["unsuitable"])
        self.assertFalse(self.store.read("session-b")["main-001"]["unsuitable"])

    def test_rejects_non_boolean_decisions(self):
        for value in [1, 0, "true", None, []]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.store.set("a", "main-001", value)
        self.assertEqual(self.store.read("a"), {})

    def test_parallel_saves_do_not_lose_other_trials(self):
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(lambda number: self.store.set("a", f"main-{number:03d}", True), range(20)))
        self.assertEqual(len(self.store.read("a")), 20)

    def test_csv_does_not_call_unreviewed_trials_suitable(self):
        session = fixture_session()
        unreviewed = list(csv.DictReader(io.StringIO(suitability_csv(session, {}).decode("utf-8-sig"))))[0]
        self.assertEqual((unreviewed["unsuitable"], unreviewed["decision_saved"]), ("0", "0"))
        marked = list(csv.DictReader(io.StringIO(suitability_csv(session, {"main-001": {"unsuitable": True, "updated_at_utc": "test"}}).decode("utf-8-sig"))))[0]
        self.assertEqual((marked["unsuitable"], marked["decision_saved"]), ("1", "1"))
        self.assertEqual(marked["item_trigger"], "S 73")
        self.assertEqual(marked["stimulus_onset_eeg_s"], "449.4709")


class SuitabilityHttpTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="trial-suitability-http-")
        self.store = SuitabilityStore(Path(self.temporary.name) / "reviews.sqlite3")
        handler = handler_class(fixture_session(), {}, {"lucide": "missing.js"}, self.store)
        handler.log_message = lambda *args: None
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temporary.cleanup()

    def post(self, value, origin=True):
        headers = {"Content-Type": "application/json"}
        if origin is True:
            headers["Origin"] = self.url
        elif origin:
            headers["Origin"] = origin
        request = Request(self.url + "/api/suitability", data=json.dumps(value).encode(), headers=headers)
        try:
            with urlopen(request) as response:
                return response.status, response.read()
        except HTTPError as error:
            return error.code, error.read()

    def test_save_read_and_download(self):
        status, body = self.post({"session_id": "test-session", "trial_id": "main-001", "unsuitable": True})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["decision"]["unsuitable"])
        with urlopen(self.url + "/api/session") as response:
            self.assertTrue(json.load(response)["suitability"]["main-001"]["unsuitable"])
        with urlopen(self.url + "/api/suitability.csv") as response:
            self.assertIn("attachment", response.headers["Content-Disposition"])
            exported = list(csv.DictReader(io.StringIO(response.read().decode("utf-8-sig"))))
            self.assertEqual(exported[0]["unsuitable"], "1")

    def test_stale_session_cannot_write_to_new_recording(self):
        status, _ = self.post({"session_id": "other-session", "trial_id": "main-001", "unsuitable": True})
        self.assertEqual(status, 409)
        self.assertEqual(self.store.read("test-session"), {})

    def test_bad_trial_or_boolean_is_rejected(self):
        for trial, flag in [("main-999", True), ("main-001", "true")]:
            status, _ = self.post({"session_id": "test-session", "trial_id": trial, "unsuitable": flag})
            self.assertEqual(status, 400)
        self.assertEqual(self.store.read("test-session"), {})

    def test_remote_or_missing_origin_cannot_write(self):
        for origin in [False, "https://example.com", "null"]:
            status, _ = self.post({"session_id": "test-session", "trial_id": "main-001", "unsuitable": True}, origin=origin)
            self.assertEqual(status, 403)
        self.assertEqual(self.store.read("test-session"), {})


if __name__ == "__main__":
    unittest.main()
