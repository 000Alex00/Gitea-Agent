"""
tests/test_token_budget.py — Tests für Token-Budget-Tracker (Issue #85)
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import settings


class TestEstimateSliceTokens(unittest.TestCase):
    def setUp(self):
        # Import after sys.path set
        from agent_start import _estimate_slice_tokens
        self.fn = _estimate_slice_tokens

    def test_range(self):
        # 50 Zeilen × TOKEN_LINES_FACTOR
        tokens = self.fn("agent_start.py:100-149")
        self.assertEqual(tokens, 50 * settings.TOKEN_LINES_FACTOR)

    def test_single_line(self):
        tokens = self.fn("settings.py:42")
        self.assertEqual(tokens, 1 * settings.TOKEN_LINES_FACTOR)

    def test_large_range(self):
        tokens = self.fn("foo.py:1-300")
        self.assertEqual(tokens, 300 * settings.TOKEN_LINES_FACTOR)

    def test_invalid_spec(self):
        # Kein Doppelpunkt → 0 Token, kein Absturz
        tokens = self.fn("nodots")
        self.assertEqual(tokens, 0)

    def test_invalid_range(self):
        tokens = self.fn("foo.py:abc-xyz")
        self.assertEqual(tokens, 0)


class TestTokenBudgetSettings(unittest.TestCase):
    def test_warn_threshold_positive(self):
        self.assertGreater(settings.TOKEN_BUDGET_WARN, 0)

    def test_lines_factor_positive(self):
        self.assertGreater(settings.TOKEN_LINES_FACTOR, 0)

    def test_defaults(self):
        self.assertEqual(settings.TOKEN_BUDGET_WARN, 150000)
        self.assertEqual(settings.TOKEN_LINES_FACTOR, 10)


class TestTokenAccumulation(unittest.TestCase):
    """Prüft dass mehrere Slices korrekt aufaddiert werden."""

    def test_cumulative_sum(self):
        from agent_start import _estimate_slice_tokens
        specs = [
            "a.py:1-100",   # 100 Zeilen
            "b.py:1-200",   # 200 Zeilen
            "c.py:50-99",   # 50 Zeilen
        ]
        total = sum(_estimate_slice_tokens(s) for s in specs)
        self.assertEqual(total, 350 * settings.TOKEN_LINES_FACTOR)

    def test_threshold_detection(self):
        """Simuliert: Gesamt-Token >= 90% Schwellwert → Warnung erwartet."""
        from agent_start import _estimate_slice_tokens
        # Erzeuge genug Slices um 90% zu erreichen
        factor = settings.TOKEN_LINES_FACTOR
        threshold = settings.TOKEN_BUDGET_WARN
        lines_needed = int(threshold * 0.9 / factor) + 1
        tokens = _estimate_slice_tokens(f"big.py:1-{lines_needed}")
        self.assertGreaterEqual(tokens, int(threshold * 0.9))


if __name__ == "__main__":
    unittest.main()
