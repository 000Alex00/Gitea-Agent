"""
tests/test_health.py — Unit-Tests für plugins/health.py
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.health import (
    CheckResult,
    HealthResult,
    _check_disk,
    _check_http,
    _check_process,
    _check_tcp,
    format_terminal,
    run_checks,
)


class TestCheckResult(unittest.TestCase):
    def test_defaults(self):
        cr = CheckResult(name="DB", type="tcp", passed=True)
        self.assertEqual(cr.message, "")
        self.assertEqual(cr.consecutive_failures, 0)

    def test_failed(self):
        cr = CheckResult(name="DB", type="tcp", passed=False, message="Timeout", consecutive_failures=2)
        self.assertFalse(cr.passed)
        self.assertEqual(cr.consecutive_failures, 2)


class TestHealthResult(unittest.TestCase):
    def test_all_passed_empty(self):
        r = HealthResult()
        self.assertTrue(r.all_passed)

    def test_all_passed_with_failures(self):
        r = HealthResult()
        r.failures.append(CheckResult(name="X", type="tcp", passed=False))
        self.assertFalse(r.all_passed)


class TestCheckHttp(unittest.TestCase):
    def test_ok_response(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            ok, msg = _check_http("http://localhost/health")
        self.assertTrue(ok)
        self.assertIn("200", msg)

    def test_server_error(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
            url="", code=503, msg="Service Unavailable", hdrs=None, fp=None
        )):
            ok, msg = _check_http("http://localhost/health")
        self.assertFalse(ok)
        self.assertIn("503", msg)

    def test_client_error_is_ok(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
            url="", code=404, msg="Not Found", hdrs=None, fp=None
        )):
            ok, msg = _check_http("http://localhost/health")
        self.assertTrue(ok)   # 404 < 500 → OK

    def test_connection_error(self):
        with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError("refused")):
            ok, msg = _check_http("http://localhost/health")
        self.assertFalse(ok)


class TestCheckTcp(unittest.TestCase):
    def test_reachable(self):
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        with patch("socket.create_connection", return_value=mock_conn):
            ok, msg = _check_tcp("localhost:5432")
        self.assertTrue(ok)
        self.assertIn("5432", msg)

    def test_unreachable(self):
        with patch("socket.create_connection", side_effect=ConnectionRefusedError("refused")):
            ok, msg = _check_tcp("localhost:5432")
        self.assertFalse(ok)

    def test_invalid_target(self):
        ok, msg = _check_tcp("no-colon")
        self.assertFalse(ok)


class TestCheckProcess(unittest.TestCase):
    def test_found(self):
        with patch("subprocess.check_output", return_value=b"1234\n5678"):
            ok, msg = _check_process("myapp.py")
        self.assertTrue(ok)
        self.assertIn("1234", msg)

    def test_not_found(self):
        import subprocess
        with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "pgrep")):
            ok, msg = _check_process("myapp.py")
        self.assertFalse(ok)


class TestCheckDisk(unittest.TestCase):
    def test_below_threshold(self):
        mock_usage = MagicMock()
        mock_usage.used = 50
        mock_usage.total = 100
        with patch("shutil.disk_usage", return_value=mock_usage):
            ok, msg = _check_disk("/", threshold=90)
        self.assertTrue(ok)
        self.assertIn("50%", msg)

    def test_above_threshold(self):
        mock_usage = MagicMock()
        mock_usage.used = 95
        mock_usage.total = 100
        with patch("shutil.disk_usage", return_value=mock_usage):
            ok, msg = _check_disk("/", threshold=90)
        self.assertFalse(ok)

    def test_path_error(self):
        with patch("shutil.disk_usage", side_effect=FileNotFoundError("not found")):
            ok, msg = _check_disk("/nonexistent")
        self.assertFalse(ok)


class TestRunChecks(unittest.TestCase):
    def _make_config(self, tmp_path: Path, checks: list, threshold: int = 3) -> Path:
        cfg = {"consecutive_failures_before_issue": threshold, "checks": checks}
        cfg_file = tmp_path / "config" / "health_checks.json"
        cfg_file.parent.mkdir(parents=True, exist_ok=True)
        cfg_file.write_text(json.dumps(cfg), encoding="utf-8")
        return tmp_path

    def test_no_config(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            result = run_checks(Path(td))
        self.assertEqual(result.checks, [])
        self.assertTrue(result.all_passed)

    def test_http_check_passes(self):
        import tempfile
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with tempfile.TemporaryDirectory() as td:
            root = self._make_config(Path(td), [
                {"name": "Test", "type": "http", "target": "http://localhost/health"}
            ])
            with patch("urllib.request.urlopen", return_value=mock_resp):
                result = run_checks(root)
        self.assertEqual(len(result.checks), 1)
        self.assertTrue(result.checks[0].passed)
        self.assertTrue(result.all_passed)

    def test_consecutive_failures_threshold(self):
        """Failure below threshold should not appear in result.failures."""
        import tempfile
        import socket
        with tempfile.TemporaryDirectory() as td:
            root = self._make_config(Path(td), [
                {"name": "DB", "type": "tcp", "target": "localhost:9999"}
            ], threshold=3)
            with patch("socket.create_connection", side_effect=ConnectionRefusedError):
                # First failure: consecutive=1, threshold=3 → not in failures
                result = run_checks(root)
        self.assertEqual(len(result.checks), 1)
        self.assertFalse(result.checks[0].passed)
        self.assertEqual(result.checks[0].consecutive_failures, 1)
        self.assertEqual(result.failures, [])

    def test_consecutive_failures_exceed_threshold(self):
        """Failures at or above threshold appear in result.failures."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = self._make_config(Path(td), [
                {"name": "DB", "type": "tcp", "target": "localhost:9999"}
            ], threshold=2)
            # Pre-populate state with 1 existing failure
            state_dir = root / "agent" / "data"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "health_state.json").write_text(
                json.dumps({"DB": 1}), encoding="utf-8"
            )
            with patch("socket.create_connection", side_effect=ConnectionRefusedError):
                result = run_checks(root)
        self.assertEqual(result.checks[0].consecutive_failures, 2)
        self.assertEqual(len(result.failures), 1)

    def test_recovery_clears_state(self):
        """Passing check removes name from persisted state."""
        import tempfile
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        with tempfile.TemporaryDirectory() as td:
            root = self._make_config(Path(td), [
                {"name": "DB", "type": "tcp", "target": "localhost:5432"}
            ])
            state_dir = root / "agent" / "data"
            state_dir.mkdir(parents=True, exist_ok=True)
            state_file = state_dir / "health_state.json"
            state_file.write_text(json.dumps({"DB": 2}), encoding="utf-8")
            with patch("socket.create_connection", return_value=mock_conn):
                result = run_checks(root)
            self.assertTrue(result.checks[0].passed)
            state = json.loads(state_file.read_text())
            self.assertNotIn("DB", state)


class TestFormatTerminal(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(format_terminal(HealthResult()), "")

    def test_passed(self):
        r = HealthResult()
        r.checks.append(CheckResult(name="Web", type="http", passed=True, message="HTTP 200"))
        out = format_terminal(r)
        self.assertIn("Web", out)
        self.assertIn("✅", out)

    def test_failed(self):
        r = HealthResult()
        r.checks.append(CheckResult(name="DB", type="tcp", passed=False,
                                    message="refused", consecutive_failures=2))
        out = format_terminal(r)
        self.assertIn("❌", out)
        self.assertIn("2x", out)


if __name__ == "__main__":
    unittest.main()
