"""
tests/test_healing.py — Tests für plugins/healing.py (Issue #60)
"""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.healing import (
    HealingAttempt,
    HealingResult,
    _apply_fixes,
    _build_fix_prompt,
    _estimate_tokens,
    _parse_fix,
    format_terminal,
    run_healing_loop,
)


class TestEstimateTokens(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(_estimate_tokens(""), 0)

    def test_approximation(self):
        text = "a" * 400
        self.assertEqual(_estimate_tokens(text), 100)


class TestParseFix(unittest.TestCase):
    def test_valid_block(self):
        output = """FILE: mymodule.py
SEARCH:
def foo():
    return 1
REPLACE:
def foo():
    return 2
"""
        fixes = _parse_fix(output)
        self.assertEqual(len(fixes), 1)
        self.assertEqual(fixes[0]["file"], "mymodule.py")
        self.assertIn("return 1", fixes[0]["search"])
        self.assertIn("return 2", fixes[0]["replace"])

    def test_no_block(self):
        fixes = _parse_fix("Hier steht nur Text ohne Format.")
        self.assertEqual(fixes, [])

    def test_multiple_blocks(self):
        output = """FILE: a.py
SEARCH:
x = 1
REPLACE:
x = 2
FILE: b.py
SEARCH:
y = 3
REPLACE:
y = 4
"""
        fixes = _parse_fix(output)
        self.assertEqual(len(fixes), 2)
        self.assertEqual(fixes[0]["file"], "a.py")
        self.assertEqual(fixes[1]["file"], "b.py")


class TestApplyFixes(unittest.TestCase):
    def test_successful_replace(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "module.py"
            f.write_text("def foo():\n    return 1\n", encoding="utf-8")
            fixes = [{"file": "module.py", "search": "return 1", "replace": "return 2"}]
            ok, changed, err = _apply_fixes(Path(td), fixes)
        self.assertTrue(ok)
        self.assertIn("module.py", changed)
        self.assertEqual(err, "")

    def test_file_not_found(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            fixes = [{"file": "nonexistent.py", "search": "x", "replace": "y"}]
            ok, changed, err = _apply_fixes(Path(td), fixes)
        self.assertFalse(ok)
        self.assertIn("nicht gefunden", err)

    def test_search_not_found(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "module.py"
            f.write_text("def foo(): pass\n", encoding="utf-8")
            fixes = [{"file": "module.py", "search": "NOT_IN_FILE", "replace": "x"}]
            ok, changed, err = _apply_fixes(Path(td), fixes)
        self.assertFalse(ok)
        self.assertIn("nicht gefunden", err)


class TestBuildFixPrompt(unittest.TestCase):
    def test_contains_test_name(self):
        prompt = _build_fix_prompt(
            "Basis-Antwort", "HTTP 500", "ERROR: crash",
            [], Path("/tmp")
        )
        self.assertIn("Basis-Antwort", prompt)
        self.assertIn("HTTP 500", prompt)

    def test_contains_attempt_history(self):
        attempts = [
            HealingAttempt(
                attempt_no=1, fix_description="first try",
                files_changed=["x.py"], eval_passed=False, eval_score=0.0,
                tokens_used=100, error="failed",
            )
        ]
        prompt = _build_fix_prompt("test", "reason", "log", attempts, Path("/tmp"))
        self.assertIn("Versuch 1", prompt)
        self.assertIn("failed", prompt)


class TestRunHealingLoopSkipped(unittest.TestCase):
    def test_feature_not_enabled_skipped_if_no_llm(self):
        """Ohne LLM-Backend wird Healing übersprungen."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Kein agent_eval.json → Default-Config → lokale LLM nicht erreichbar
            with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError):
                result = run_healing_loop(root, "TestA", "HTTP 500")
        self.assertTrue(result.skipped)
        self.assertIn("LLM", result.skip_reason)

    def test_git_error_skipped(self):
        """Wenn Temp-Branch nicht erstellt werden kann → übersprungen."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("urllib.request.urlopen"):  # LLM erreichbar
                with patch("plugins.healing._current_branch", return_value="main"):
                    with patch("plugins.healing._create_temp_branch",
                               side_effect=Exception("git error")):
                        result = run_healing_loop(root, "TestA", "HTTP 500")
        self.assertTrue(result.skipped)
        self.assertIn("Temp-Branch", result.skip_reason)


class TestHealingResult(unittest.TestCase):
    def test_attempt_count(self):
        r = HealingResult(test_name="T", project_root="/tmp")
        self.assertEqual(r.attempt_count, 0)
        r.attempts.append(HealingAttempt(
            attempt_no=1, fix_description="x",
            files_changed=[], eval_passed=False, eval_score=0.0, tokens_used=100
        ))
        self.assertEqual(r.attempt_count, 1)


class TestFormatTerminal(unittest.TestCase):
    def test_skipped(self):
        r = HealingResult(test_name="T", project_root="/tmp",
                          skipped=True, skip_reason="kein LLM")
        out = format_terminal(r)
        self.assertIn("übersprungen", out)

    def test_success(self):
        r = HealingResult(test_name="T", project_root="/tmp", success=True)
        r.attempts.append(HealingAttempt(
            attempt_no=1, fix_description="fixed it",
            files_changed=["a.py"], eval_passed=True, eval_score=1.0,
            tokens_used=1000,
        ))
        out = format_terminal(r)
        self.assertIn("✅", out)
        self.assertIn("Geheilt", out)

    def test_failure(self):
        r = HealingResult(test_name="T", project_root="/tmp", success=False)
        r.attempts.append(HealingAttempt(
            attempt_no=1, fix_description="nope",
            files_changed=[], eval_passed=False, eval_score=0.0,
            tokens_used=500, error="Eval fehlgeschlagen",
        ))
        out = format_terminal(r)
        self.assertIn("❌", out)
        self.assertIn("Nicht geheilt", out)


if __name__ == "__main__":
    unittest.main()
