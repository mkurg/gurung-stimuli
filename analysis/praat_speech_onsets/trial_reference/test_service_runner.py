import logging
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch
from types import SimpleNamespace

from service_runner import APPLICATION, ensure_server, health_matches, read_health, server_command


class ServiceRunnerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.logger = Mock(spec=logging.Logger)

    def test_health_requires_this_application_and_library(self):
        valid = {"application": APPLICATION, "root": str(self.root)}
        self.assertTrue(health_matches(valid, self.root))
        for payload in (None, {}, {**valid, "application": "other"},
                        {**valid, "root": str(self.root / "other")},
                        {**valid, "root": None}):
            with self.subTest(payload=payload):
                self.assertFalse(health_matches(payload, self.root))

    def test_running_owned_process_is_not_duplicated_or_killed(self):
        child, probe, popen = Mock(), Mock(), Mock()
        child.poll.return_value = None
        self.assertIs(ensure_server(child, self.root, "pythonw.exe", 8765, self.logger,
                                    probe=probe, popen=popen), child)
        probe.assert_not_called()
        popen.assert_not_called()
        child.terminate.assert_not_called()

    def test_existing_server_from_same_library_is_adopted(self):
        probe = Mock(return_value={"application": APPLICATION, "root": str(self.root)})
        popen = Mock()
        self.assertIsNone(ensure_server(None, self.root, "pythonw.exe", 8765, self.logger,
                                        probe=probe, popen=popen))
        popen.assert_not_called()

    def test_another_library_is_left_untouched(self):
        probe = Mock(return_value={"application": APPLICATION, "root": str(self.root / "other")})
        popen = Mock()
        self.assertIsNone(ensure_server(None, self.root, "pythonw.exe", 8765, self.logger,
                                        probe=probe, popen=popen))
        popen.assert_not_called()

    def test_exited_server_restarts_on_the_fixed_port(self):
        old, new = Mock(), Mock()
        old.poll.return_value = 1
        old.returncode = 1
        popen = Mock(return_value=new)
        self.assertIs(ensure_server(old, self.root, "pythonw.exe", 8765, self.logger,
                                    probe=Mock(return_value=None), popen=popen), new)
        self.assertEqual(popen.call_args.args[0], server_command(self.root, "pythonw.exe", 8765))
        self.assertIn("--strict-port", popen.call_args.args[0])
        old.terminate.assert_not_called()

    def test_unreachable_health_is_not_a_running_server(self):
        with patch("service_runner.LOCAL_HTTP.open", side_effect=TimeoutError):
            self.assertIsNone(read_health(8765))

    def test_health_probe_uses_loopback_only(self):
        payload = {"application": APPLICATION, "root": str(self.root)}
        response = io.BytesIO(json.dumps(payload).encode())
        with patch("service_runner.LOCAL_HTTP.open", return_value=response) as opener:
            self.assertEqual(read_health(8765), payload)
        opener.assert_called_once_with("http://127.0.0.1:8765/api/health", timeout=3)

    def test_invalid_health_response_is_not_adopted(self):
        with patch("service_runner.LOCAL_HTTP.open", return_value=io.BytesIO(b"not JSON")):
            self.assertIsNone(read_health(8765))

    def test_health_endpoint_does_not_read_recordings_or_annotations(self):
        from server import ROOT, handler_class
        reader, library = Mock(), Mock()
        handler = handler_class({}, {}, {"lucide": __file__}, Mock(),
                                annotation_reader=reader, library=library)
        request = handler.__new__(handler)
        request.path = "/api/health"
        request.server = SimpleNamespace(server_port=8765)
        request.headers = {"Host": "127.0.0.1:8765"}
        request.send_json = Mock()
        request.send_content()
        request.send_json.assert_called_once_with(
            {"application": APPLICATION, "pid": os.getpid(), "root": str(ROOT.resolve())}, head=False)
        library.listing.assert_not_called()
        reader.read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
