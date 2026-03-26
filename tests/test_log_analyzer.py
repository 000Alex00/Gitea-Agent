"""
tests/test_log_analyzer.py — Unit-Tests für log_analyzer.template.py
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Template direkt als Modul laden
import importlib.util
_TEMPLATE = Path(__file__).parent.parent / "config" / "log_analyzer.py"
spec = importlib.util.spec_from_file_location("log_analyzer", _TEMPLATE)
la = importlib.util.module_from_spec(spec)
spec.loader.exec_module(la)


class TestKnownPatterns(unittest.TestCase):
    def test_connection_refused(self):
        lines = ["2024-01-01 ERROR ConnectionRefusedError: [Errno 111]"]
        findings = la._analyze_rules(lines)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].tag, "connectivity")

    def test_timeout(self):
        lines = ["socket.timeout: timed out"]
        findings = la._analyze_rules(lines)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].tag, "timeout")

    def test_memory_error(self):
        lines = ["MemoryError: unable to allocate"]
        findings = la._analyze_rules(lines)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].tag, "memory")

    def test_import_error(self):
        lines = ["ModuleNotFoundError: No module named 'torch'"]
        findings = la._analyze_rules(lines)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].tag, "import")

    def test_permission_error(self):
        lines = ["PermissionError: [Errno 13] Permission denied: '/var/log/app.log'"]
        findings = la._analyze_rules(lines)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].tag, "permission")

    def test_no_match(self):
        lines = ["INFO: Server gestartet auf Port 8080", "DEBUG: Request verarbeitet"]
        findings = la._analyze_rules(lines)
        self.assertEqual(findings, [])

    def test_one_finding_per_line(self):
        """Eine Zeile mit mehreren Mustern → nur ein Finding."""
        lines = ["ERROR ConnectionRefusedError und TimeoutError"]
        findings = la._analyze_rules(lines)
        self.assertEqual(len(findings), 1)

    def test_line_numbers(self):
        lines = ["INFO: ok", "ERROR: Traceback", "INFO: ok"]
        findings = la._analyze_rules(lines)
        self.assertEqual(findings[0].line_no, 2)


class TestRunSkipped(unittest.TestCase):
    def test_no_log_path_in_config(self):
        with patch.object(la, "_load_eval_cfg", return_value={}):
            result = la.run()
        self.assertTrue(result.skipped)
        self.assertIn("log_path", result.skip_reason)

    def test_log_file_missing(self):
        with patch.object(la, "_load_eval_cfg", return_value={"log_path": "/nonexistent/app.log"}):
            result = la.run()
        self.assertTrue(result.skipped)
        self.assertIn("nicht gefunden", result.skip_reason)


class TestRunWithLog(unittest.TestCase):
    def _make_log(self, tmp_path, content: str) -> Path:
        p = Path(tmp_path) / "app.log"
        p.write_text(content, encoding="utf-8")
        return p

    def test_clean_log(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            log_file = self._make_log(td, "INFO: alles gut\nDEBUG: request ok\n")
            with patch.object(la, "_load_eval_cfg", return_value={
                "log_path": str(log_file),
                "log_analysis": {"tail_lines": 100, "llm_enabled": False},
            }):
                result = la.run()
        self.assertFalse(result.skipped)
        self.assertEqual(result.findings, [])
        self.assertEqual(result.lines_analyzed, 2)

    def test_log_with_errors(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            log_file = self._make_log(td, "ERROR: ConnectionRefusedError\nINFO: ok\n")
            with patch.object(la, "_load_eval_cfg", return_value={
                "log_path": str(log_file),
                "log_analysis": {"tail_lines": 100, "llm_enabled": False},
            }):
                result = la.run()
        self.assertFalse(result.skipped)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].tag, "connectivity")

    def test_tail_lines_respected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            content = "INFO: ok\n" * 500 + "ERROR: Traceback\n"
            log_file = self._make_log(td, content)
            with patch.object(la, "_load_eval_cfg", return_value={
                "log_path": str(log_file),
                "log_analysis": {"tail_lines": 10, "llm_enabled": False},
            }):
                result = la.run()
        self.assertEqual(result.lines_analyzed, 10)
        # Traceback-Zeile ist die letzte → in den letzten 10 → finding vorhanden
        self.assertEqual(len(result.findings), 1)

    def test_llm_enabled_no_server(self):
        """LLM aktiviert aber nicht erreichbar → llm_error gesetzt, Ergebnis trotzdem zurück."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            log_file = self._make_log(td, "WARNING: slow response\nERROR: unknown issue\n")
            with patch.object(la, "_load_eval_cfg", return_value={
                "log_path": str(log_file),
                "log_analysis": {"tail_lines": 100, "llm_enabled": True,
                                 "llm_url": "http://localhost:9999/api/generate",
                                 "llm_timeout": 1},
            }):
                result = la.run()
        self.assertFalse(result.skipped)
        self.assertNotEqual(result.llm_error, "")

    def test_llm_local_called(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            log_file = self._make_log(td, "CRITICAL: unknown crash pattern foo\n")
            with patch.object(la, "_load_eval_cfg", return_value={
                "log_path": str(log_file),
                "log_analysis": {"tail_lines": 100, "llm_enabled": True,
                                 "llm_url": "http://localhost:11434/api/generate",
                                 "llm_model": "llama3", "llm_timeout": 5},
                "claude_api_enabled": False,
            }):
                with patch.object(la, "_call_llm_local", return_value="Root-Cause: Test") as mock_llm:
                    result = la.run()
        self.assertEqual(result.llm_summary, "Root-Cause: Test")
        self.assertEqual(result.llm_error, "")
        mock_llm.assert_called_once()

    def test_claude_api_called(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            log_file = self._make_log(td, "CRITICAL: unknown custom failure xyz123\n")
            with patch.object(la, "_load_eval_cfg", return_value={
                "log_path": str(log_file),
                "log_analysis": {"tail_lines": 100, "llm_enabled": True},
                "claude_api_enabled": True,
                "claude_model": "claude-sonnet-4-6",
            }):
                with patch.object(la, "_call_llm_claude", return_value="Claude sagt: ...") as mock_claude:
                    result = la.run()
        self.assertEqual(result.llm_summary, "Claude sagt: ...")
        mock_claude.assert_called_once()


class TestFormatTerminal(unittest.TestCase):
    def test_skipped(self):
        r = la.LogAnalysisResult(skipped=True, skip_reason="kein log_path")
        out = la.format_terminal(r)
        self.assertIn("übersprungen", out)

    def test_clean(self):
        r = la.LogAnalysisResult(log_path="/app.log", lines_analyzed=50)
        out = la.format_terminal(r)
        self.assertIn("✅", out)

    def test_with_findings(self):
        r = la.LogAnalysisResult(log_path="/app.log", lines_analyzed=50)
        r.findings.append(la.LogFinding(
            line_no=5, line="ERROR: Timeout", tag="timeout",
            hypothesis="Timeout-Fehler", suggestion="Timeout erhöhen",
        ))
        out = la.format_terminal(r)
        self.assertIn("timeout", out)
        self.assertIn("Timeout-Fehler", out)

    def test_with_llm_summary(self):
        r = la.LogAnalysisResult(log_path="/app.log", lines_analyzed=50,
                                 llm_summary="Mögliche Ursache: X")
        out = la.format_terminal(r)
        self.assertIn("LLM-Analyse", out)
        self.assertIn("Mögliche Ursache", out)

    def test_with_llm_error(self):
        r = la.LogAnalysisResult(log_path="/app.log", lines_analyzed=50,
                                 llm_error="Connection refused")
        out = la.format_terminal(r)
        self.assertIn("nicht erreichbar", out)

    def test_max_10_findings_shown(self):
        r = la.LogAnalysisResult(log_path="/app.log", lines_analyzed=100)
        for i in range(15):
            r.findings.append(la.LogFinding(
                line_no=i, line=f"ERROR {i}", tag=f"tag_{i}",
                hypothesis="h", suggestion="s",
            ))
        out = la.format_terminal(r)
        self.assertIn("weitere Treffer", out)


if __name__ == "__main__":
    unittest.main()
