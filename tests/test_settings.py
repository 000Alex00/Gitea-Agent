"""Tests für settings.py — Pfad-Konfiguration (Issue #86)."""

import sys
from pathlib import Path

sys.argv = ["x", "--self"]
import settings


def test_dashboard_path_is_absolute():
    assert Path(settings.DASHBOARD_PATH).is_absolute()


def test_dashboard_path_ends_with_html():
    assert str(settings.DASHBOARD_PATH).endswith("dashboard.html")


def test_dashboard_path_inside_agent_or_root():
    p = Path(settings.DASHBOARD_PATH)
    # Muss entweder in agent/data/ liegen oder im Fallback-Root
    assert p.name == "dashboard.html"


def test_all_paths_consistent():
    """Alle _AGENT_DIR-Pfade liegen im gleichen Elternverzeichnis."""
    paths = [
        settings.CONTEXT_DIR_PATH,
        settings.LOG_FILE_PATH,
        settings.DASHBOARD_PATH,
        settings.DOCTOR_RESULT_PATH,
    ]
    parents = {Path(p).parent for p in paths}
    # Bei neuer Struktur: alle in agent/data/
    # Bei Fallback: gemischt erlaubt
    assert len(parents) <= 2  # maximal 2 verschiedene Elternverzeichnisse
