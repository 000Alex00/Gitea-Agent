# Dateien — Issue #18

## agent_start.py
```
#!/usr/bin/env python3
"""
agent_start.py — Universeller Agent-Einstiegspunkt für den Gitea Issue-Workflow.

Workflow:
    1. Ohne Argumente: Auto-Modus — scannt Gitea und arbeitet selbständig
       - ready-for-agent Issues  → Plan-Kommentar posten
       - agent-proposed + "ok"   → Branch erstellen + Kontext ausgeben
       - in-progress             → Status anzeigen

    2. Manuell:
       --list               → Alle ready-for-agent Issues anzeigen
       --issue <NR>         → Plan für ein Issue posten
       --implement <NR>     → Nach Freigabe: Branch + Implementierungskontext
       --pr <NR> --branch X → PR erstellen + Abschluss-Kommentar

Konfiguration (.env im selben Verzeichnis):
    Alle konfigurierbaren Werte kommen aus settings.py / .env.
    Secrets (Tokens) gehören in .env — nicht in settings.py.

LLM-agnostisch:
    Für Claude Code: direkt im Terminal ausführen
    Für andere LLMs: Output als System-Prompt + Dateiinhalte als Kontext übergeben
"""

import argparse
import ast
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
import gitea_api as gitea
import settings
import evaluation
from log import get_logger

log = get_logger(__name__)

# Projektroot: aus .env oder Elternverzeichnis des Scripts
def _project_root() -> Path:
    """
    Bestimmt das Projektverzeichnis das bearbeitet wird.

    Reihenfolge:
        1. PROJECT_ROOT aus .env (falls gesetzt und existiert)
        2. Elternverzeichnis von agent_start.py (Standard)

    Returns:
        Absoluter Pfad zum Projektroot.
    """
    env_file = _HERE / ".env"
    if settings.PROJECT_ROOT:
        p = Path(settings.PROJECT_ROOT)
        if p.exists():
            log.debug(f"PROJECT_ROOT aus settings: {p}")
            return p
        log.warning(f"PROJECT_ROOT '{settings.PROJECT_ROOT}' existiert nicht — verwende Standard")
    p = _HERE.parent
    log.debug(f"PROJECT_ROOT (Standard): {p}")
    return p

PROJECT = _project_root()


# ---------------------------------------------------------------------------
# Risiko-Klassifikation
# ---------------------------------------------------------------------------

def risk_level(issue: dict) -> tuple[int, str]:
    """
    Bestimmt die Risikostufe eines Issues (1=niedrig bis 4=kritisch).

    Args:
        issue: Issue-dict aus Gitea API

    Returns:
        Tuple (stufe: int, beschreibung: str)
    """
    labels = [l["name"] for l in issue.get("labels", [])]
    title  = issue.get("title", "").lower()

    if any(lb in labels for lb in settings.RISK_BUG_LABELS):
        return 3, "HOCH — Bug (Plan erforderlich)"
    if any(lb in labels for lb in settings.RISK_FEAT_LABELS):
        return 3, "HOCH — Neues Feature (Plan + Freigabe erforderlich)"
    if any(lb in labels for lb in settings.RISK_ENAK_LABELS):
        if any(w in title for w in settings.SAFE_KEYWORDS):
            return 1, "NIEDRIG — Dokumentation/Cleanup"
        return 2, "MITTEL — Enhancement (Plan vor Implementierung)"
    return 2, "MITTEL — (Plan vor Implementierung)"


def issue_type(issue: dict) -> str:
    """Leitet den Issue-Typ aus den Gitea-Labels ab."""
    labels = [l["name"] for l in issue.get("labels", [])]
    title  = issue.get("title", "").lower()
    if any(lb in labels for lb in settings.RISK_BUG_LABELS):
        return "bug"
    if any(lb in labels for lb in settings.RISK_FEAT_LABELS):
        return "feature_request"
    if any(lb in labels for lb in settings.RISK_ENAK_LABELS):
        if any(w in title for w in settings.SAFE_KEYWORDS):
            return "docs"
        return "enhancement"
    return "task"


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def relevant_files(issue: dict) -> list[Path]:
    """
    Extrahiert Dateipfade aus dem Issue-Body (Backtick-Erwähnungen).

    Args:
        issue: Issue-dict

    Returns:
        Liste existierender Dateipfade (dedupliziert).
    """
    body      = issue.get("body", "")
    exts      = tuple(settings.CODE_EXTENSIONS)
    found     = []
    for line in body.splitlines():
        for part in line.split("`"):
            p = PROJECT / part.strip()
            if p.exists() and p.is_file() and p.suffix in exts:
                found.append(p)
    return list(dict.fromkeys(found))


def branch_name(issue: dict) -> str:
    """
    Generiert einen Branch-Namen aus Issue-Nummer und Titel.

    Returns:
        z.B. "fix/issue-16-bug-beschreibung"
    """
    num    = issue["number"]
    title  = issue.get("title", "").lower()
    labels = [l["name"] for l in issue.get("labels", [])]

    if any(lb in labels for lb in settings.RISK_BUG_LABELS):
        prefix = settings.PREFIX_FIX
    elif any(lb in labels for lb in settings.RISK_FEAT_LABELS):
        prefix = settings.PREFIX_FEAT
    else:
        prefix = settings.PREFIX_DEFAULT

    if any(w in title for w in settings.DOCS_KEYWORDS):
        prefix = settings.PREFIX_DOCS

    slug = title
    for ch in " /()→.:,äöüß":
        slug = slug.replace(ch, "-")
    slug = slug.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    slug = "-".join(w for w in slug.split("-") if w)[:35]
    return f"{prefix}/issue-{num}-{slug}"


# ---------------------------------------------------------------------------
# Plan-Kommentar
# ---------------------------------------------------------------------------

def build_plan_comment(issue: dict) -> str:
    """
    Erstellt den Plan-Kommentar der auf Gitea gepostet wird.

    Args:
        issue: Issue-dict

    Returns:
        Markdown-Text für den Gitea-Kommentar.
    """
    num         = issue["number"]
    stufe, desc = risk_level(issue)
    files       = relevant_files(issue)
    branch      = branch_name(issue)

    file_list = "\n".join(f"- `{f.relative_to(PROJECT)}`" for f in files) \
                or "- Keine automatisch erkannt — bitte manuell prüfen"

    return f"""## Agent-Analyse — Issue #{num}

**Risikostufe:** {stufe}/4 — {desc}

### Betroffene Dateien
{file_list}

### Implementierungsplan
{settings.PLAN_PLACEHOLDER_TEXT}

### Geplanter Branch
`{branch}`

### Commit-Template
```
<typ>: <beschreibung> (closes #{num})
```

---

**OK zum Implementieren?**
{settings.APPROVAL_PROMPT}

## Nächste Schritte
- Plan prüfen
- Mit `ok` oder `ja` kommentieren → Implementierung startet
"""


# ---------------------------------------------------------------------------
# Terminal-Ausgabe für LLM-Kontext
# ---------------------------------------------------------------------------

def print_context(issue: dict) -> None:
    """
    Gibt strukturierten Kontext für den LLM-Agenten im Terminal aus.

    Für Claude Code: direkt lesbar im Terminal.
    Für andere LLMs: als System-Prompt verwenden.
    """
    num         = issue["number"]
    title       = issue.get("title", "")
    body        = issue.get("body", "")
    stufe, desc = risk_level(issue)
    files       = relevant_files(issue)
    branch      = branch_name(issue)

    print("=" * 70)
    print(f"  AGENT — ISSUE #{num}")
    print("=" * 70)
    print(f"\nTitel:       {title}")
    print(f"Risikostufe: {stufe}/4 — {desc}")
    print(f"\n--- Issue-Beschreibung ---\n{body}")

    if files:
        print("\n--- Erkannte relevante Dateien ---")
        for f in files:
            size_kb = f.stat().st_size // 1024 + 1
            print(f"  {f.relative_to(PROJECT)}  ({size_kb} KB)")

    print(f"\n--- Branch ---")
    print(f"  git checkout -b {branch}")
    print(f"\n--- Gitea Issue ---")
    print(f"  {gitea.GITEA_URL}/{gitea.REPO}/issues/{num}")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Kontext-Dateien
# ---------------------------------------------------------------------------

def _context_dir() -> Path:
    """
    Gibt den Pfad zum contexts/-Verzeichnis zurück.

    Relativ → wird relativ zu agent_start.py aufgelöst.
    Absolut → wird direkt verwendet.

    Returns:
        Absoluter Pfad zum Kontext-Verzeichnis.
    """
    p = Path(settings.CONTEXT_DIR)
    return p if p.is_absolute() else _HERE / p


def _issue_dir(issue: dict) -> Path:
    """Gibt den Issue-Unterordner zurück und erstellt ihn falls nötig.

    Format: contexts/{num}-{typ}/  z.B. contexts/32-feature_request/
    """
    d = _context_dir() / f"{issue['number']}-{issue_type(issue)}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _find_issue_dir(number: int) -> Path | None:
    """Findet den Issue-Ordner anhand der Nummer (Typ unbekannt → glob)."""
    matches = list(_context_dir().glob(f"{number}-*"))
    return matches[0] if matches else None


def _done_dir() -> Path:
    """Gibt den done/-Ordner zurück und erstellt ihn falls nötig."""
    d = _context_dir() / "done"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_plan_context(issue: dict) -> Path:
    """

[... gekürzt — 1339 Zeilen weggelassen ...]
```
