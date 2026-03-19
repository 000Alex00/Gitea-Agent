"""
settings.py — Zentrale Konfiguration für gitea-agent.

Alle Werte können über .env oder Umgebungsvariablen überschrieben werden.
Secrets (Tokens, Passwörter) gehören in .env — nicht hier.

Reihenfolge: Umgebungsvariable → .env → Standardwert
"""

import os
from pathlib import Path

_ENV_FILE = Path(__file__).parent / ".env"


def _env(key: str, default: str = "") -> str:
    """Liest einen Wert aus Umgebungsvariable oder .env-Datei."""
    if key in os.environ:
        return os.environ[key]
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    return default


def _env_list(key: str, default: str) -> list[str]:
    """Liest eine kommagetrennte Liste aus .env."""
    return [v.strip() for v in _env(key, default).split(",") if v.strip()]


def _env_int(key: str, default: int) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    return _env(key, str(default)).lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------
# Gitea Workflow — Label-Namen
# ---------------------------------------------------------------------------

LABEL_READY    = _env("LABEL_READY",    "ready-for-agent")
LABEL_PROPOSED = _env("LABEL_PROPOSED", "agent-proposed")
LABEL_PROGRESS = _env("LABEL_PROGRESS", "in-progress")
LABEL_REVIEW   = _env("LABEL_REVIEW",   "needs-review")

# ---------------------------------------------------------------------------
# Risiko-Klassifikation
# ---------------------------------------------------------------------------

# Label-Namen die Risikostufe 3 (Bug / Feature) auslösen
RISK_BUG_LABELS  = _env_list("RISK_BUG_LABELS",  "bug")
RISK_FEAT_LABELS = _env_list("RISK_FEAT_LABELS", "Feature request")
RISK_ENAK_LABELS = _env_list("RISK_ENAK_LABELS", "enhancement")

# Schlüsselwörter im Titel die ein Enhancement als Stufe 1 (sicher) einstufen
SAFE_KEYWORDS = _env_list("SAFE_KEYWORDS", "docstring,docs,comment,dead code,cleanup,import")

# ---------------------------------------------------------------------------
# Branch-Generierung
# ---------------------------------------------------------------------------

PREFIX_FIX     = _env("PREFIX_FIX",     "fix")
PREFIX_FEAT    = _env("PREFIX_FEAT",    "feat")
PREFIX_DOCS    = _env("PREFIX_DOCS",    "docs")
PREFIX_DEFAULT = _env("PREFIX_DEFAULT", "chore")

# Schlüsselwörter im Titel die docs-Präfix auslösen
DOCS_KEYWORDS = _env_list("DOCS_KEYWORDS", "docs,docstring,comment")

# ---------------------------------------------------------------------------
# Datei-Analyse
# ---------------------------------------------------------------------------

# Erlaubte Dateiendungen für Code-Analyse und relevant_files()
CODE_EXTENSIONS = _env_list("CODE_EXTENSIONS", ".py,.js,.sh,.yaml,.md")

# Maximale Zeilenanzahl die pro Datei im Terminal ausgegeben wird
MAX_FILE_LINES = _env_int("MAX_FILE_LINES", 300)

# ---------------------------------------------------------------------------
# Gitea API — Verhalten
# ---------------------------------------------------------------------------

# Maximale Anzahl Issues die pro Abfrage geladen werden
ISSUE_LIMIT = _env_int("ISSUE_LIMIT", 50)

# Standard-Ziel-Branch für Pull Requests
PR_BASE_BRANCH = _env("PR_BASE_BRANCH", "main")

# Kommentare die als Freigabe gewertet werden (case-insensitive)
APPROVAL_KEYWORDS = set(_env_list("APPROVAL_KEYWORDS", "ok,yes,ja,approved,freigabe,👍,✅"))

# Text im Agent-Kommentar der den "letzten Agent-Kommentar" markiert
AGENT_MARKER = _env("AGENT_MARKER", "OK zum Implementieren?")

# ---------------------------------------------------------------------------
# Claude API (optional — deaktiviert bis CLAUDE_API_ENABLED=true)
# ---------------------------------------------------------------------------

CLAUDE_API_ENABLED = _env_bool("CLAUDE_API_ENABLED", False)
CLAUDE_MODEL       = _env("CLAUDE_MODEL",       "claude-sonnet-4-6")
CLAUDE_MAX_TOKENS  = _env_int("CLAUDE_MAX_TOKENS", 4096)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_LEVEL = _env("LOG_LEVEL", "INFO")   # DEBUG, INFO, WARNING, ERROR
LOG_FILE  = _env("LOG_FILE",  "gitea-agent.log")
