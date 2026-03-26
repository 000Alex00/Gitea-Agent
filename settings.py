"""
settings.py — Zentrale Konfiguration für gitea-agent.

Alle Werte können über .env oder Umgebungsvariablen überschrieben werden.
Secrets (Tokens, Passwörter) gehören in .env — nicht hier.

Reihenfolge: Umgebungsvariable → .env → Standardwert
"""

import os
from pathlib import Path

_ENV_FILE = Path(os.environ.get("AGENT_ENV_FILE", str(Path(__file__).parent / ".env")))


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
LABEL_HELP     = _env("LABEL_HELP",     "help wanted")

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

# Auto-Approve für Claude Code Tool-Calls (schreibt .claude/settings.local.json)
AUTO_APPROVE = _env_bool("AUTO_APPROVE", False)

# ---------------------------------------------------------------------------
# Textbausteine / Templates
# ---------------------------------------------------------------------------

# Projekt-Root (überschreibt Elternverzeichnis von agent_start.py)
PROJECT_ROOT = _env("PROJECT_ROOT", "")

# Verzeichnis für Kontext-Dateien (relativ zu agent_start.py oder absolut) — Legacy
CONTEXT_DIR = _env("CONTEXT_DIR", "contexts")

# ---------------------------------------------------------------------------
# Pfad-Auflösung: wenn PROJECT_ROOT/agent/ existiert → neue Struktur
#   agent/config/  ← agent_eval.json, log_analyzer.py
#   agent/data/    ← contexts/, logs, session, baseline, history
# sonst → Fallback: Pfade relativ zu agent_start.py
# ---------------------------------------------------------------------------

_HERE_SETTINGS = Path(__file__).parent
_AGENT_DIR: "Path | None" = None

if PROJECT_ROOT:
    _candidate = Path(PROJECT_ROOT) / "agent"
    if _candidate.exists():
        _AGENT_DIR = _candidate

if _AGENT_DIR:
    CONTEXT_DIR_PATH   = _AGENT_DIR / "data" / "contexts"
    LOG_FILE_PATH      = _AGENT_DIR / "data" / "gitea-agent.log"
    SESSION_FILE_PATH  = _AGENT_DIR / "data" / "session.json"
    DOCTOR_RESULT_PATH = _AGENT_DIR / "data" / "doctor_last.json"
    DASHBOARD_PATH     = _AGENT_DIR / "data" / "dashboard.html"
    LOG_ANALYZER_PATH  = _AGENT_DIR / "config" / "log_analyzer.py"
else:
    # Fallback: alte Pfade relativ zum Skript-Verzeichnis
    CONTEXT_DIR_PATH   = _HERE_SETTINGS / _env("CONTEXT_DIR", "contexts")
    LOG_FILE_PATH      = _HERE_SETTINGS / _env("LOG_FILE", "gitea-agent.log")
    SESSION_FILE_PATH  = _HERE_SETTINGS / "contexts" / "session.json"
    DOCTOR_RESULT_PATH = _HERE_SETTINGS / "doctor_last.json"
    DASHBOARD_PATH     = _HERE_SETTINGS / "dashboard.html"
    LOG_ANALYZER_PATH  = None  # agent_start.py prüft PROJECT/tools/ als Fallback

# Freigabe-Aufforderung am Ende des Plan-Kommentars
APPROVAL_PROMPT = _env(
    "APPROVAL_PROMPT",
    "Antworte mit `ok`, `ja` oder `✅` um die Implementierung zu starten.",
)

# Platzhalter im Plan-Kommentar (vom LLM auszufüllen)
# Mehrzeilig — direkt hier editieren, nicht via .env
PLAN_PLACEHOLDER_TEXT = (
    "> Dieser Abschnitt wird vom LLM-Agenten nach Code-Analyse ausgefüllt.\n"
    "> Der Agent liest die Dateien, mappt Abhängigkeiten und beschreibt:\n"
    "> - Root-Cause / Was genau geändert wird\n"
    "> - Welche Funktionen/Zeilen betroffen sind\n"
    "> - Mögliche Seiteneffekte / Regressionsrisiko\n"
    "> - Vorgehensweise Schritt für Schritt"
)

# PR-Checkliste (kommagetrennt → wird als "- [ ] ..." gerendert)
PR_CHECKLIST = _env_list(
    "PR_CHECKLIST",
    "Code geändert,Dokumentation aktualisiert,Kein toter Code hinzugefügt,Getestet",
)

# Text am Ende des Abschluss-Kommentars nach PR-Erstellung
COMPLETION_NEXT_STEP = _env(
    "COMPLETION_NEXT_STEP",
    "PR reviewen und mergen.\nNach dem Merge: Issue schließen.",
)

# ---------------------------------------------------------------------------
# Eval nach Neustart (Issue #10)
# ---------------------------------------------------------------------------

# URL des Servers der nach Neustart gepollt wird
SERVER_URL          = _env("SERVER_URL",          "http://localhost:8000")
SERVER_WAIT_TIMEOUT = _env_int("SERVER_WAIT_TIMEOUT", 300)   # Sekunden
SERVER_WAIT_INTERVAL = _env_int("SERVER_WAIT_INTERVAL", 10)  # Sekunden

# ---------------------------------------------------------------------------
# Session-Tracking (Issue #13)
# ---------------------------------------------------------------------------

# Maximale abgeschlossene Issues pro Claude-Session bevor Drift-Warnung
SESSION_LIMIT       = _env_int("SESSION_LIMIT",       2)
# Stunden ohne Aktivität nach denen session.json zurückgesetzt wird
SESSION_RESET_HOURS = _env_int("SESSION_RESET_HOURS", 4)

# ---------------------------------------------------------------------------
# Prozess-Enforcement (Issue #6)
# ---------------------------------------------------------------------------

# Pflichtregeln-Block der in jede starter.md eingefügt wird (Maßnahme 2+3)
STARTER_MD_PFLICHTREGELN = """\
## PFLICHTREGELN (bei Kontext-Drift: neue Session starten)
> ⚠️ **Technische Schranken haben Vorrang vor Prompt-Regeln.**
> `cmd_pr()` prüft Vorbedingungen automatisch — kein manueller Bypass möglich.

- NIEMALS `curl` statt `agent_start.py` verwenden
- NIEMALS Schritte überspringen
- NIEMALS PR manuell erstellen

⚠️ **Sessions-Limit:** Nach 2 Issues neue Claude-Session empfohlen.
Kontext-Drift Symptome: curl statt agent_start.py, fehlende Metadata, übersprungene Schritte.

## SELBST-CHECK vor jedem Schritt
- [ ] Vorheriger Schritt vollständig abgeschlossen?
- [ ] `agent_start.py` verwendet (nicht curl)?
- [ ] Metadata-Block vorhanden?
- [ ] Eval gelaufen?

Wenn Checkbox offen → **STOPP**. Schritt nachholen oder neue Session.

## Kontext

Die relevanten Dateien wurden automatisch erkannt:
- Backtick-Erwähnungen im Issue-Text
- Import-Analyse (AST)
- Keyword-Suche (grep)

⚠️ **NICHT selbst im Repo suchen** — der Kontext ist vollständig.
Falls etwas fehlt: im Issue nachfragen, nicht raten.

---
"""

# ---------------------------------------------------------------------------
# Output-Validierung (Issue #8)
# ---------------------------------------------------------------------------

# Pflichtfelder pro Kommentar-Typ — _validate_comment() prüft ob alle enthalten
COMMENT_REQUIRED_FIELDS: dict[str, list[str]] = {
    "plan":       ["Risikostufe", "Betroffene Dateien", "OK zum Implementieren?"],
    "completion": ["Implementierung abgeschlossen", "Verlauf", "Neustart erforderlich", "Eval", "Score"],
    "eval_fail":  ["Eval FAIL", "Score", "Fehlgeschlagene Tests"],
    "auto_issue": ["Auto", "Score", "Verlauf"],
}
