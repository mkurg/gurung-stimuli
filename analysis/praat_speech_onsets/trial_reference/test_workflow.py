import copy
import csv
import hashlib
import io
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from annotations import AnnotationReader, textgrid_io
from import_recording import register, run_import, source_identity
from recording_library import RecordingLibrary, atomic_json, bundle, file_hash, import_lock
from server import handler_class
from suitability import SuitabilityStore, suitability_csv
from test_annotations import annotation_grid, annotation_session


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="speech-workflow-test-")
        self.root = Path(self.temp.name)
        self.library_root = self.root / "recordings"
        self.vhdr = self.root / "test.vhdr"
        self.vhdr.write_text("Brain Vision Data Exchange Header File Version 1.0\n[Common Infos]\nDataFile=test.eeg\nMarkerFile=test.vmrk\n[Channel Infos]\nCh1=AUX1,,1,uV\n", encoding="utf-8")
        (self.root / "test.eeg").write_bytes(b"original EEG")
        (self.root / "test.vmrk").write_bytes(b"original markers")
        self.audio = self.root / "psychopy"
        self.audio.mkdir()
        for filename in ("full_session.wav", "eeg_triggers.csv", "recording_segments.csv", "001_isolated_main_l1_trial001_imageset1_cond_it.wav"):
            (self.audio / filename).write_bytes(b"fixture source")
        self.experiment = self.root / "experiment"
        (self.experiment / "Conds").mkdir(parents=True)
        (self.experiment / "Conds" / "isolated_practice.csv").write_text("practice_index\n1\n")
        self.grid = self.root / "saved.TextGrid"
        self.save_grid(annotation_grid([(2, "s")]))
        self.wav = self.root / "aux.wav"
        self.wav.write_bytes(b"fixture AUX WAV")
        self.config = {"vhdr": str(self.vhdr), "textgrid": str(self.grid), "stimtrak_wav": str(self.wav),
                       "audio_dir": str(self.audio), "experiment_dir": str(self.experiment), "lucide": "missing.js"}
        self.session = annotation_session()
        self.session["session_id"] = source_identity(self.vhdr, self.audio)[0]
        self.session["sources"] = []
        self.session["validation"] = {"main_trials": 2}
        self.session["trials"][1]["condition"] = "tr_coh"
        self.session["trials"][1]["triggers"] = [{"role": "condition", "code": 1}]
        self.session["trials"][0]["triggers"] = [{"role": "condition", "code": 2}]
        self.session["trials"][2]["triggers"] = []
        self.logs = []

    def tearDown(self):
        self.temp.cleanup()

    def save_grid(self, grid):
        self.grid.write_text(textgrid_io.getTextgridAsStr(grid, format="long_textgrid", includeBlankSpaces=True), encoding="utf-8")

    def builder(self, config):
        return copy.deepcopy(self.session), {}

    def test_registration_retains_sources_and_provenance(self):
        before = file_hash(self.grid)
        result = register(self.config, "AUX1", self.library_root, self.logs.append, builder=self.builder)
        directory = self.library_root / result["session_id"][:20]
        self.assertTrue((directory / "registration.json").is_file())
        provenance = json.loads((directory / "provenance.json").read_text())
        self.assertEqual(provenance["initial_textgrid_sha256"], before)
        self.assertEqual(file_hash(self.grid), before)
        self.assertTrue(provenance["source_files"][0]["sha256"])
        self.assertEqual(provenance["pipeline_version"], 3)

    def test_duplicate_import_does_not_reextract_or_overwrite(self):
        register(self.config, "AUX1", self.library_root, self.logs.append, builder=self.builder)
        self.save_grid(annotation_grid([(2.75, "s")]))
        before = file_hash(self.grid)
        with patch("import_recording.subprocess.Popen", side_effect=AssertionError("Must not extract again")):
            result = run_import({"vhdr": str(self.vhdr), "audio_dir": str(self.audio), "experiment_dir": str(self.experiment), "channel": "AUX1"},
                                self.logs.append, self.library_root, {"mne_python": "not-installed"})
        self.assertTrue(result["already_registered"])
        self.assertEqual(file_hash(self.grid), before)

    def test_full_import_publishes_and_watches_desktop_files(self):
        output_root = self.root / "Desktop" / "EEG recs"

        def extract(command, **kwargs):
            output = Path(command[command.index("--output-dir") + 1]) / "test_AUX1"
            output.mkdir(parents=True)
            (output / "test.wav").write_bytes(self.wav.read_bytes())
            (output / "test.TextGrid").write_bytes(self.grid.read_bytes())
            atomic_json(output / "test_export.json", {"channel": "AUX1"})
            atomic_json(Path(command[command.index("--result-json") + 1]), {"output_folder": str(output)})
            process = MagicMock()
            process.__enter__.return_value = process
            process.stdout = ["fixture extraction complete\n"]
            process.wait.return_value = 0
            return process

        def validated_register(config, channel, library_root, log, metadata, **kwargs):
            return register(config, channel, library_root, log, metadata, builder=self.builder, **kwargs)

        inputs = {"vhdr": str(self.vhdr), "audio_dir": str(self.audio), "experiment_dir": str(self.experiment), "channel": "AUX1"}
        runtime = {"mne_python": "fixture", "praat_output_root": str(output_root)}
        with patch("import_recording.checked_mne_python", return_value=Path("fixture-python")), \
                patch("import_recording.subprocess.Popen", side_effect=extract), \
                patch("import_recording.build_session", side_effect=self.builder), \
                patch("import_recording.register", side_effect=validated_register):
            result = run_import(inputs, self.logs.append, self.library_root, runtime)
        expected_grid = output_root / "test" / "test_annotations.TextGrid"
        self.assertEqual(Path(result["textgrid"]), expected_grid)
        self.assertEqual(Path(result["stimtrak_wav"]), output_root / "test" / "test.wav")
        saved_config = json.loads((self.library_root / result["session_id"][:20] / "config.json").read_text())
        self.assertEqual(saved_config["textgrid"], str(expected_grid))
        expected_grid.write_bytes(self.grid.read_bytes() + b"\n")
        before = file_hash(expected_grid)
        with patch("import_recording.subprocess.Popen", side_effect=AssertionError("Must not extract again")):
            repeated = run_import(inputs, self.logs.append, self.library_root, runtime)
        self.assertTrue(repeated["already_registered"])
        self.assertEqual(file_hash(expected_grid), before)

    def test_desktop_collision_stops_before_extraction(self):
        output_root = self.root / "Desktop" / "EEG recs"
        conflict = output_root / "test" / "test_annotations.TextGrid"
        conflict.parent.mkdir(parents=True)
        conflict.write_bytes(b"manual annotations")
        with patch("import_recording.checked_mne_python", side_effect=AssertionError("Must stop before runtime probe")):
            with self.assertRaisesRegex(ValueError, "already exists"):
                run_import({"vhdr": str(self.vhdr), "audio_dir": str(self.audio), "experiment_dir": str(self.experiment), "channel": "AUX1"},
                           self.logs.append, self.library_root, {"praat_output_root": str(output_root)})
        self.assertEqual(conflict.read_bytes(), b"manual annotations")

    def test_invalid_grid_never_publishes_registration(self):
        self.grid.write_text("incomplete TextGrid")
        with self.assertRaises(ValueError):
            register(self.config, "AUX1", self.library_root, self.logs.append, builder=self.builder)
        self.assertEqual(list(self.library_root.glob("*/registration.json")), [])

    def test_changed_identity_never_publishes_registration(self):
        with self.assertRaisesRegex(ValueError, "identity changed"):
            register(self.config, "AUX1", self.library_root, self.logs.append, builder=self.builder, expected_identity="different")
        self.assertEqual(list(self.library_root.glob("*/registration.json")), [])

    def test_library_discovers_new_registration_without_server_restart(self):
        default = bundle(self.session, {}, self.config, self.root / "snapshots")
        library = RecordingLibrary(self.library_root, default, self.builder, self.root / "snapshots")
        self.assertEqual(len(library.listing()["sessions"]), 1)
        second = copy.deepcopy(self.session)
        second["session_id"] = hashlib.sha256(b"second").hexdigest()
        second["recording"] = "second"
        directory = self.library_root / second["session_id"][:20]
        atomic_json(directory / "config.json", self.config)
        atomic_json(directory / "registration.json", {"session_id": second["session_id"], "recording": "second",
                    "participant": "002", "list": 1, "main_trials": 2, "protocol": "isolated"})
        self.assertEqual(len(library.listing()["sessions"]), 2)
        library.loader = lambda config: (second, {})
        self.assertEqual(library.get(second["session_id"])["session"]["recording"], "second")
        with self.assertRaises(KeyError):
            library.get("unknown")

    def test_new_flags_persist_and_are_independent(self):
        store = SuitabilityStore(self.root / "flags.sqlite3")
        store.set_flag("a", "main-001", "need_help", True)
        store.set_flag("a", "main-001", "ergative", True)
        store.set("a", "main-001", True)
        store.set_flag("a", "main-001", "need_help", False)
        reopened = SuitabilityStore(self.root / "flags.sqlite3")
        self.assertFalse(reopened.read_flags("a", "need_help")["main-001"]["marked"])
        self.assertTrue(reopened.read_flags("a", "ergative")["main-001"]["marked"])
        self.assertTrue(reopened.read("a")["main-001"]["unsuitable"])
        self.assertEqual(reopened.read_flags("b", "ergative"), {})
        with self.assertRaises(ValueError):
            store.set_flag("a", "main-001", "need_help", "true")
        exported = list(csv.DictReader(io.StringIO(suitability_csv(self.session, {}, store.read_flags("a", "ergative"), store.read_flags("a", "need_help")).decode("utf-8-sig"))))
        self.assertEqual(exported[0]["ergative"], "1")
        self.assertEqual(exported[0]["need_help"], "0")
        self.assertEqual(exported[1]["ergative"], "")

    def test_import_lock_prevents_overlap_and_releases_after_failure(self):
        with self.assertRaisesRegex(RuntimeError, "fixture failure"):
            with import_lock(self.library_root):
                with self.assertRaisesRegex(ValueError, "Another recording import"):
                    with import_lock(self.library_root):
                        self.fail("Concurrent import acquired the lock")
                raise RuntimeError("fixture failure")
        with import_lock(self.library_root):
            self.assertTrue((self.library_root / "import.lock").is_file())

    def changed_source_library(self):
        library = RecordingLibrary(self.library_root, bundle(self.session, {}, self.config, self.root / "snapshots"),
                                   self.builder, self.root / "snapshots")
        second = copy.deepcopy(self.session)
        second["session_id"] = hashlib.sha256(b"changed-source-fixture").hexdigest()
        second["sources"] = [{"sha256": "original"}]
        directory = self.library_root / second["session_id"][:20]
        atomic_json(directory / "config.json", self.config)
        atomic_json(directory / "registration.json", {"session_id": second["session_id"]})
        atomic_json(directory / "manifest.json", second)
        atomic_json(directory / "provenance.json", {"stimtrak_wav": {"sha256": file_hash(self.wav)}})
        return library, second

    def test_changed_source_mapping_is_rejected(self):
        library, second = self.changed_source_library()
        changed = copy.deepcopy(second)
        changed["sources"][0]["sha256"] = "changed"
        library.loader = lambda config: (changed, {})
        with self.assertRaisesRegex(ValueError, "experiment tables changed"):
            library.get(second["session_id"])

    def test_changed_aux_wav_is_rejected(self):
        library, second = self.changed_source_library()
        library.loader = lambda config: (second, {})
        self.wav.write_bytes(b"changed AUX")
        with self.assertRaisesRegex(ValueError, "StimTrak WAV changed"):
            library.get(second["session_id"])


class FlagHttpTests(WorkflowTests):
    def setUp(self):
        super().setUp()
        self.store = SuitabilityStore(self.root / "flags.sqlite3")
        library = RecordingLibrary(self.library_root, bundle(self.session, {}, self.config, self.root / "snapshots"), self.builder, self.root / "snapshots")
        handler = handler_class(self.session, {}, self.config, self.store, library=library)
        handler.log_message = lambda *args: None
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        super().tearDown()

    def post(self, endpoint, trial, field, value, origin=None):
        data = {"session_id": self.session["session_id"], "trial_id": trial, field: value}
        request = Request(self.url + endpoint, data=json.dumps(data).encode(), headers={"Content-Type": "application/json", "Origin": origin or self.url})
        try:
            with urlopen(request) as response:
                return response.status
        except HTTPError as error:
            return error.code

    def test_ergative_is_only_allowed_for_s1_transitive_trials(self):
        self.assertEqual(self.post("/api/ergative", "main-001", "ergative", True), 400)
        self.assertEqual(self.post("/api/ergative", "main-002", "ergative", True), 200)
        self.assertEqual(self.post("/api/ergative", "practice-01", "ergative", True), 400)

    def test_need_help_is_available_for_main_and_practice(self):
        for trial in ("main-001", "main-002", "practice-01"):
            self.assertEqual(self.post("/api/need-help", trial, "need_help", True), 200)
        self.assertEqual(len(self.store.read_flags(self.session["session_id"], "need_help")), 3)

    def test_cross_origin_flags_and_import_requests_rejected(self):
        self.assertEqual(self.post("/api/need-help", "main-001", "need_help", True, "https://example.com"), 403)
        self.assertEqual(self.post("/api/import", "main-001", "need_help", True, "https://example.com"), 403)

    def test_unknown_session_is_not_fallback_to_default(self):
        with self.assertRaises(HTTPError) as caught:
            urlopen(self.url + "/api/session?session=unknown")
        self.assertEqual(caught.exception.code, 404)

    def test_combined_export_has_flags_and_measurements(self):
        self.post("/api/need-help", "main-001", "need_help", True)
        self.post("/api/ergative", "main-002", "ergative", True)
        with urlopen(self.url + "/api/library-analysis.csv") as response:
            records = list(csv.DictReader(io.StringIO(response.read().decode("utf-8-sig"))))
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["speech_latency_ms"], "1000.0")
        self.assertEqual(records[0]["need_help"], "1")
        self.assertEqual(records[1]["ergative"], "1")

    def test_global_counts_endpoint_is_independent_of_selected_session(self):
        self.save_grid(annotation_grid([(2, "s"), (6, "s")],
                       [(0, 2, ""), (2, 3, "intransitive sentence"), (3, 6, ""),
                        (6, 7, "transitive sentence"), (7, 10, "")]))
        self.post("/api/need-help", "main-001", "need_help", True)
        self.post("/api/ergative", "main-002", "ergative", True)
        with urlopen(self.url + "/api/library-counts?session=ignored") as response:
            result = json.loads(response.read())
        self.assertEqual(result["counts"], {"itr": 1, "tr_erg": 1, "tr_zero": 0})
        self.post("/api/suitability", "main-001", "unsuitable", True)
        with urlopen(self.url + "/api/library-counts") as response:
            self.assertEqual(json.loads(response.read())["counts"]["itr"], 0)

    def test_global_counts_update_on_textgrid_saves_and_ignore_incomplete_annotations(self):
        def counts():
            with urlopen(self.url + "/api/library-counts") as response:
                return json.loads(response.read())["counts"]

        self.assertEqual(counts(), {"itr": 0, "tr_erg": 0, "tr_zero": 0})
        self.save_grid(annotation_grid([(2, "s")], [(0, 2, ""), (2, 3, "sentence"), (3, 10, "")]))
        self.assertEqual(counts(), {"itr": 1, "tr_erg": 0, "tr_zero": 0})
        self.save_grid(annotation_grid([(2, "s"), (3, "s")], [(0, 2, ""), (2, 3, "sentence"), (3, 10, "")]))
        self.assertEqual(counts(), {"itr": 0, "tr_erg": 0, "tr_zero": 0})
        self.save_grid(annotation_grid([], [(0, 2, ""), (2, 3, "sentence"), (3, 10, "")]))
        self.assertEqual(counts(), {"itr": 0, "tr_erg": 0, "tr_zero": 0})


if __name__ == "__main__":
    unittest.main()
