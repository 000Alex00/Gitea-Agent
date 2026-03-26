"""
tests/test_slice_gate.py — Tests für Slice-Gate (Issue #94)
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import settings


class TestSliceGateSettings(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertFalse(settings.SLICE_GATE_ENABLED)

    def test_min_lines_default(self):
        self.assertEqual(settings.SLICE_GATE_MIN_LINES, 100)


class TestWarnSlicesNotRequested(unittest.TestCase):
    def setUp(self):
        from agent_start import _warn_slices_not_requested
        self.fn = _warn_slices_not_requested

    def _patch_diff(self, changed_files: list[str]):
        return patch(
            "subprocess.check_output",
            return_value="\n".join(changed_files).encode(),
        )

    def test_no_py_files_changed(self):
        with self._patch_diff(["README.md", "docs/index.html"]):
            result = self.fn(1, "feat/test")
        self.assertFalse(result)

    def test_small_files_ignored(self):
        """Dateien unter SLICE_GATE_MIN_LINES → kein Befund."""
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            # Kleine Datei (< 100 Zeilen)
            small_file = Path(td) / "small.py"
            small_file.write_text("\n".join(["x=1"] * 50), encoding="utf-8")

            with self._patch_diff(["small.py"]):
                with patch("agent_start.PROJECT", Path(td)):
                    with patch("agent_start._find_issue_dir", return_value=None):
                        result = self.fn(1, "feat/test")
        self.assertFalse(result)

    def test_large_file_no_slices(self):
        """Große Datei geändert, keine Slices → Verletzung."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            large_file = Path(td) / "big.py"
            large_file.write_text("\n".join(["x=1"] * 200), encoding="utf-8")

            with self._patch_diff(["big.py"]):
                with patch("agent_start.PROJECT", Path(td)):
                    with patch("agent_start._find_issue_dir", return_value=None):
                        with patch("agent_start.gitea") as mock_gitea:
                            result = self.fn(1, "feat/test")
        self.assertTrue(result)

    def test_large_file_with_matching_slice(self):
        """Große Datei geändert, passender Slice vorhanden → kein Befund."""
        import tempfile, json
        with tempfile.TemporaryDirectory() as td:
            large_file = Path(td) / "mymodule.py"
            large_file.write_text("\n".join(["x=1"] * 200), encoding="utf-8")

            idir = Path(td) / "issue_1"
            idir.mkdir()
            session = {"slices_requested": [
                {"spec": "mymodule.py:1-100", "estimated_tokens": 100}
            ]}
            (idir / "session.json").write_text(json.dumps(session), encoding="utf-8")

            with self._patch_diff(["mymodule.py"]):
                with patch("agent_start.PROJECT", Path(td)):
                    with patch("agent_start._find_issue_dir", return_value=idir):
                        result = self.fn(1, "feat/test")
        self.assertFalse(result)

    def test_gate_blocks_when_enabled(self):
        """SLICE_GATE_ENABLED=True → Verletzung muss in fehler[] landen."""
        # Wir testen hier nur dass _warn_slices_not_requested True zurückgibt
        # und settings.SLICE_GATE_ENABLED=True die Integration im PR-Gate auslöst
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            large_file = Path(td) / "module.py"
            large_file.write_text("\n".join(["x=1"] * 150), encoding="utf-8")

            with self._patch_diff(["module.py"]):
                with patch("agent_start.PROJECT", Path(td)):
                    with patch("agent_start._find_issue_dir", return_value=None):
                        with patch("agent_start.gitea"):
                            result = self.fn(1, "feat/test")
        # Verletzung erkannt — Gate-Logik in _check_pr_preconditions verwertet True
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
