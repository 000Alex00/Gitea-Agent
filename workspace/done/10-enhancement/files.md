# Dateien — Issue #10

## Documentation/COOKBOOK.md
```
# gitea-agent COOKBOOK

Schritt-für-Schritt-Rezepte für häufige Aufgaben.
Referenzprojekt: Skynet (LLM WhatsApp-Bot, Jetson Nano + Raspberry Pi 5).

---

## Inhaltsverzeichnis

1. [Agent auf neues Projekt portieren](#1-agent-auf-neues-projekt-portieren)
2. [Standard-Workflow: Issue → PR](#2-standard-workflow-issue--pr)
3. [Bugfix auf in-progress Issue (--fixup)](#3-bugfix-auf-in-progress-issue---fixup)
4. [Ersten Test schreiben (agent_eval.json)](#4-ersten-test-schreiben-agent_evaljson)
5. [Mehrstufigen Test schreiben (steps)](#5-mehrstufigen-test-schreiben-steps)
6. [Eval-Baseline neu setzen](#6-eval-baseline-neu-setzen)
7. [Watch-Modus einrichten (tmux + Dauerbetrieb)](#7-watch-modus-einrichten-tmux--dauerbetrieb)
8. [Systemd-Timer: Eval nach Nachtsync](#8-systemd-timer-eval-nach-nachtsync)
9. [Eval nach Neustart (--eval-after-restart)](#9-eval-nach-neustart---eval-after-restart)
10. [Auto-Issue manuell schließen](#10-auto-issue-manuell-schließen)

---

## 1. Agent auf neues Projekt portieren

**Kontext:** Du willst den gitea-agent für ein neues Projekt nutzen.

**Dateien:** `.env`, `tests/agent_eval.json` (im Zielprojekt)

**Schritte:**

```bash
# 1. gitea-agent klonen (oder bestehende Kopie verwenden)
git clone http://192.168.1.60:3001/Alexmistrator/gitea-agent
cd gitea-agent

# 2. .env befüllen
cp .env.example .env
```

```ini
# .env — Werte anpassen (NICHT committen)
GITEA_URL=http://192.168.1.60:3001
GITEA_USER=dein-username
GITEA_TOKEN=abc123xxxxxxxxxxxxx   # Gitea → Settings → Applications → Token
GITEA_REPO=username/mein-projekt
PROJECT_ROOT=/home/user/mein-projekt
```

```bash
# 3. Labels in Gitea anlegen
# Gitea → Repo → Issues → Labels → folgende erstellen:
#   ready-for-agent   (grün)
#   agent-proposed    (blau)
#   in-progress       (gelb)
#   needs-review      (orange)

# 4. Ersten Testlauf
python3 agent_start.py --list
```

**Pitfalls:**
- `PROJECT_ROOT` muss absoluter Pfad zum Zielprojekt sein — nicht zum gitea-agent-Verzeichnis
- Token braucht Scopes: `issue` (read+write) + `repository` (read+write)
- Labels müssen exakt so heißen wie in `settings.py → LABEL_*`

---

## 2. Standard-Workflow: Issue → PR

**Kontext:** Normaler Entwicklungszyklus für ein neues Feature oder einen Bug.

**Dateien:** `agent_start.py`, Gitea Issue

**Schritte:**

```bash
# Schritt 1: Issue schreiben
# In Gitea: Neue Issue → Body mit betroffenen Dateien in Backticks:
# "Bitte Timeout in `nanoclaw/plugins/web_search.py` auf 8s setzen."
# Label: ready-for-agent

# Schritt 2: Plan generieren
python3 agent_start.py --issue 61

# → Postet Plan-Kommentar ins Issue
# → Label: ready-for-agent → agent-proposed
# → Gibt contexts/open/61-bug/starter.md aus

# Schritt 3: Plan freigeben
# In Gitea: Issue → Kommentar: "ok"

# Schritt 4: Implementierung starten
python3 agent_start.py --implement 61

# → Erstellt Branch: fix/issue-61-...
# → Label: agent-proposed → in-progress
# [LLM implementiert Code, committed]

# Schritt 5: PR erstellen (nach Implementierung)
python3 agent_start.py --pr 61 --branch fix/issue-61-web-search-timeout \
  --summary "DDGS.text() blockierte asyncio — run_in_executor + wait_for(8s)"

# → Eval läuft automatisch (Risiko ≥ 2)
# → Bei PASS: PR erstellt, Abschluss-Kommentar, Label: needs-review
# → Bei FAIL: PR blockiert, Kommentar ins Issue
```

**Pitfalls:**
- `--branch` muss exakt dem Branch-Namen entsprechen (`git branch` zeigt aktuellen)
- `--summary` weglassen → Warnung im Kommentar (nicht blockierend)

---

## 3. Bugfix auf in-progress Issue (--fixup)

**Kontext:** Du hast einen Commit auf einem in-progress Branch gemacht und willst den Reviewer benachrichtigen.

**Dateien:** `agent_start.py`

**Schritte:**

```bash
# Commit gemacht, jetzt Kommentar ins Issue:
git add nanoclaw/plugins/web_search.py
git commit -m "fix: DDGS run_in_executor + wait_for(8s) (closes #61)"

python3 agent_start.py --fixup 61

# → Liest letzten Commit automatisch aus git log
# → Postet Bugfix-Kommentar mit Commit-SHA ins Issue
# → Label: in-progress → needs-review
```

**Pitfalls:**
- `--fixup` liest `git log -1` — immer erst committen, dann aufrufen
- Label-Wechsel passiert automatisch, kein manueller Schritt nötig

---

## 4. Ersten Test schreiben (agent_eval.json)

**Kontext:** Du willst das Verhalten deines Servers absichern.

**Dateien:** `tests/agent_eval.json` (im Zielprojekt)

**Schritte:**

```bash
mkdir -p /home/user/mein-projekt/tests
```

```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "watch_interval_minutes": 60,
  "tests": [
    {
      "name": "Einfache Antwort",
      "weight": 1,
      "pi5_required": false,
      "message": "Was ist 2 plus 2?",
      "expected_keywords": ["4"]
    },
    {
      "name": "Server antwortet",
      "weight": 1,
      "pi5_required": false,
      "message": "Hallo",
      "expected_keywords": []
    }
  ]
}
```

```bash
# Ersten Lauf — Baseline wird automatisch angelegt
python3 evaluation.py --project /home/user/mein-projekt
# → Schreibt tests/baseline.json mit aktuellem Score
```

**Pitfalls:**
- `expected_keywords: []` = nur prüfen ob Server antwortet (kein Keyword-Check)
- `weight` beeinflusst wie stark ein FAIL die Baseline unterschreitet
- Baseline-Datei nicht versionieren (maschinenspezifisch)

---

## 5. Mehrstufigen Test schreiben (steps)

**Kontext:** Du willst Kontext-Persistenz testen — z.B. ob etwas gespeichert und später abrufbar ist.

**Referenz:** Skynet-Projekt, ChromaDB-Kontext-Test

**Dateien:** `tests/agent_eval.json`

```json
{
  "server_url": "http://192.168.1.179:8000",
  "chat_endpoint": "/chat",
  "pi5_url": "http://192.168.1.148:1235",
  "watch_interval_minutes": 60,
  "log_path": "/home/user/mein-projekt/logs/system.log",
  "tests": [
    {
      "name": "Routing einfach",
      "weight": 1,
      "pi5_required": false,
      "message": "Was ist 2 plus 2?",
      "expected_keywords": ["4"]
    },
    {
      "name": "Kontext-Persistenz",
      "weight": 2,
      "pi5_required": true,
      "steps": [
        {
          "message": "Mein Name ist TestUser",
          "expect_stored": true
        },
        {
          "message": "Wie heiße ich?",
          "expected_keywords": ["TestUser"]
        }
      ]
    },
    {
      "name": "Stilles Failure",
      "weight": 2,
      "pi5_required": true,
      "steps": [
        {
          "message": "Mein Lieblingstier ist ein Pinguin",
          "expect_stored": true
        },
        {
          "message": "Was ist mein Lieblingstier?",
          "expected_keywords": ["Pinguin"]
        }
      ]
    },
    {
      "name": "Web Search",
      "weight": 1,
      "pi5_required": true,
      "message": "Was gibt es aktuell Neues?",
      "expected_keywords": []
    }
  ]
}
```

**Erklärung:**
- `steps`: sequenzielle Schritte mit derselben User-ID (verhindert Kontext-Bleeding zwischen Tests)
- `expect_stored: true`: Antwort darf leer sein — prüft nur ob der Server nicht abstürzt (Schreib-Schritt)
- `pi5_required: true`: Test wird übersprungen wenn Backend-Worker offline (kein FAIL)
- Zwischen Steps: 2s Wartezeit (LLM-Cooldown)

**Pitfalls:**
- Jeder Lauf bekommt eine neue `eval-XXXXXXXX` User-ID → kein Bleeding zwischen Läufen
- `pi5_url` fehlt → `pi5_required: true` Tests laufen trotzdem (werden nicht als offline erkannt)

---

## 6. Eval-Baseline neu setzen

**Kontext:** Du hast bewusst einen neuen Test hinzugefügt oder ein Feature entfernt — die alte Baseline passt nicht mehr.

**Dateien:** `tests/baseline.json`, `evaluation.py`

**Schritte:**

```bash
# Aktuellen Score anzeigen (ohne Baseline zu ändern)
python3 evaluation.py --project /home/user/mein-projekt

# Neue Baseline setzen (nur wenn du weißt was du tust)
python3 evaluation.py --project /home/user/mein-projekt --update-baseline

# Prüfen was gesetzt wurde
cat /home/user/mein-projekt/tests/baseline.json
# → {"score": 7.0}
```

**Wann neu setzen:**
- Neuer Test hinzugefügt → Score steigt → Baseline automatisch erhöht (kein manueller Schritt nötig)
- Test entfernt → Score sinkt → manuell neu setzen
- Hardware-Umbau → neue Infrastruktur hat anderen Basis-Score

**Pitfalls:**
- Baseline auto-erhöht sich bei `score > baseline` — nie runter (außer manuell)
- `--update-baseline` schreibt sofort — kein Bestätigungsprompt

---

## 7. Watch-Modus einrichten (tmux + Dauerbetrieb)

**Kontext:** Kontinuierliche Überwachung im Hintergrund, Auto-Issues bei Score-Verlust.

**Dateien:** `agent_start.py`, `tests/agent_eval.json`

[... gekürzt — 171 Zeilen weggelassen ...]
```

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

[... gekürzt — 1086 Zeilen weggelassen ...]
```

## evaluation.py
```
#!/usr/bin/env python3
"""
evaluation.py — Generisches Eval-System für den gitea-agent Workflow.

Liest `tests/agent_eval.json` aus dem Zielprojekt und führt definierte
HTTP-Tests gegen server.py aus. Vergleicht Score mit `tests/baseline.json`.

Aufgerufen von:
    agent_start.py -> cmd_pr() — vor jedem PR

Standalone:
    python3 evaluation.py [--update-baseline] [--project /pfad/zum/projekt]
"""

import argparse
import datetime
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path

EVAL_CONFIG    = "tests/agent_eval.json"
BASELINE       = "tests/baseline.json"
SCORE_HISTORY  = "tests/score_history.json"
HISTORY_MAX    = 90
DEFAULT_CHAT   = "/chat"
TIMEOUT        = 10  # Sekunden pro Request


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    name:    str
    weight:  int
    passed:  bool
    skipped: bool   = False
    reason:  str    = ""


@dataclass
class EvalResult:
    passed:           bool         = False
    skipped:          bool         = False  # kein agent_eval.json gefunden
    warned:           bool         = False  # Infrastruktur offline
    baseline_created: bool         = False  # erster Lauf, Baseline gespeichert
    baseline_raised:  bool         = False  # Score > alter Baseline → auto-aktualisiert
    score:            float        = 0.0
    baseline_score:   float        = 0.0
    max_score:        int          = 0
    warn_reasons:     list[str]    = field(default_factory=list)
    failed_tests:     list[TestResult] = field(default_factory=list)
    all_tests:        list[TestResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _ping(url: str) -> bool:
    """Prüft ob eine URL erreichbar ist (GET, ignoriert HTTP-Fehlercode)."""
    try:
        urllib.request.urlopen(url, timeout=TIMEOUT)
        return True
    except urllib.error.HTTPError:
        return True  # Server antwortet → erreichbar
    except Exception:
        return False


def _chat(server_url: str, endpoint: str, message: str, eval_user: str) -> str | None:
    """
    Sendet eine Nachricht an server.py und gibt die Antwort zurück.

    Args:
        server_url: Basis-URL, z.B. "http://localhost:8000"
        endpoint:   Pfad, z.B. "/chat" (aus agent_eval.json)
        message:    Nachrichtentext
        eval_user:  Eindeutige User-ID pro Eval-Lauf (verhindert Kontext-Bleeding)

    Returns:
        Antworttext als String oder None bei Fehler.
    """
    url  = server_url.rstrip("/") + endpoint
    body = json.dumps({"prompt": message, "user": eval_user}).encode()
    req  = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())
            for key in ("response", "reply", "text", "message"):
                if key in data:
                    return str(data[key])
            return str(data)
    except Exception:
        return None


def _keywords_match(text: str, keywords: list[str]) -> bool:
    """Prüft ob alle Keywords (case-insensitive) im Text vorkommen."""
    text_lower = text.lower()
    return all(kw.lower() in text_lower for kw in keywords)


def _run_steps(server_url: str, endpoint: str, steps: list[dict], eval_user: str) -> tuple[bool, str]:
    """
    Führt einen mehrstufigen Test sequenziell aus.

    Jeder Step kann entweder:
    - ``expect_stored: true``  — Nachricht senden, nur Antwort (kein Fehler) erwartet
    - ``expected_keywords: [...]`` — Antwort wird auf Keywords geprüft

    Aufgerufen von:
        run() für Tests mit "steps"-Schlüssel

    Args:
        server_url: Basis-URL von server.py
        endpoint:   Chat-Endpunkt (z.B. "/chat")
        steps:      Liste von Step-Dicts aus agent_eval.json

    Returns:
        Tuple (passed: bool, reason: str)
    """
    for i, step in enumerate(steps, start=1):
        if i > 1:
            time.sleep(2)  # Jetson Zeit geben zwischen Steps (LLM-Inferenz-Cooldown)

        message  = step.get("message", "")
        keywords = step.get("expected_keywords", [])
        stored   = step.get("expect_stored", False)

        response = _chat(server_url, endpoint, message, eval_user)
        if response is None:
            return False, f"Step {i}: Keine Antwort von server.py"

        if stored:
            # Nur prüfen ob server geantwortet hat — kein Keyword-Check
            continue

        if keywords and not _keywords_match(response, keywords):
            return False, f"Step {i}: Keywords {keywords!r} nicht in Antwort"

    return True, ""


def _load_config(project_root: Path) -> dict | None:
    """Lädt agent_eval.json aus dem Zielprojekt. None wenn nicht vorhanden."""
    cfg_path = project_root / EVAL_CONFIG
    if not cfg_path.exists():
        return None
    with cfg_path.open(encoding="utf-8") as f:
        return json.load(f)


def _load_baseline(project_root: Path) -> float | None:
    """Lädt den gespeicherten Baseline-Score. None wenn nicht vorhanden."""
    bl_path = project_root / BASELINE
    if not bl_path.exists():
        return None
    with bl_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("score")


def _save_baseline(project_root: Path, score: float) -> None:
    """Speichert aktuellen Score als neue Baseline."""
    bl_path = project_root / BASELINE
    bl_path.parent.mkdir(parents=True, exist_ok=True)
    with bl_path.open("w", encoding="utf-8") as f:
        json.dump({"score": score}, f, indent=2)


def _save_score_history(project_root: Path, result: "EvalResult", trigger: str) -> None:
    """
    Hängt einen Eintrag an tests/score_history.json an. Max HISTORY_MAX Einträge.

    Args:
        project_root: Pfad zum Zielprojekt
        result:       EvalResult des aktuellen Laufs
        trigger:      "pr", "watch" oder "manual"
    """
    hist_path = project_root / SCORE_HISTORY
    hist_path.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if hist_path.exists():
        try:
            with hist_path.open(encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    entry = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "trigger":   trigger,
        "score":     result.score,
        "max_score": result.max_score,
        "baseline":  result.baseline_score,
        "passed":    result.passed,
        "failed":    [{"name": t.name, "reason": t.reason} for t in result.failed_tests],
    }
    history.append(entry)
    history = history[-HISTORY_MAX:]  # nur die letzten 90 behalten

    with hist_path.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Kern
# ---------------------------------------------------------------------------

def run(project_root: Path, update_baseline: bool = False, trigger: str = "manual") -> EvalResult:
    """
    Führt alle Eval-Tests aus dem Zielprojekt aus.

    Aufgerufen von:
        agent_start.py -> cmd_pr()   (trigger="pr")
        agent_start.py -> cmd_watch() (trigger="watch")
        __main__ (standalone)         (trigger="manual")

    Args:
        project_root:     Pfad zum Zielprojekt (PROJECT-Variable in agent_start.py)
        update_baseline:  Wenn True → aktuellen Score als neue Baseline speichern
        trigger:          Auslöser des Laufs — "pr", "watch" oder "manual"

    Returns:
        EvalResult mit passed/skipped/warned/failed + Score-Details

    Seiteneffekte:
        Schreibt tests/baseline.json wenn nicht vorhanden oder --update-baseline
        Schreibt tests/score_history.json (max 90 Einträge)
    """
    result = EvalResult()

    # 1. Konfiguration laden
    cfg = _load_config(project_root)
    if cfg is None:
        result.skipped = True
        return result

    server_url = cfg.get("server_url", "http://localhost:8000")
    pi5_url    = cfg.get("pi5_url")
    endpoint   = cfg.get("chat_endpoint", DEFAULT_CHAT)
    tests      = cfg.get("tests", [])

    # 2. Erreichbarkeit prüfen
    server_ok = _ping(server_url)
    if not server_ok:
        result.warned = True
        result.warn_reasons.append(f"server.py nicht erreichbar ({server_url}) — Eval übersprungen")
        return result

    pi5_ok = True
    if pi5_url:
        pi5_ok = _ping(pi5_url)
        if not pi5_ok:
            result.warned = True
            result.warn_reasons.append(f"Pi5 nicht erreichbar ({pi5_url}) — Pi5-Tests werden übersprungen")

    # 3. Tests ausführen — eindeutiger User pro Lauf verhindert Kontext-Bleeding
    eval_user     = f"eval-{uuid.uuid4().hex[:8]}"
    total_weight  = 0
    earned_weight = 0

    for t in tests:
        name     = t.get("name", "?")
        weight   = t.get("weight", 1)
        message  = t.get("message", "")
        keywords = t.get("expected_keywords", [])
        pi5_req  = t.get("pi5_required", False)
        total_weight += weight

        if pi5_req and not pi5_ok:
            tr = TestResult(name=name, weight=weight, passed=False, skipped=True,
                            reason="Pi5 offline")
            result.all_tests.append(tr)
            continue

        steps = t.get("steps")
        if steps:
            passed, reason = _run_steps(server_url, endpoint, steps, eval_user)
        else:
            response = _chat(server_url, endpoint, message, eval_user)
            if response is None:
                tr = TestResult(name=name, weight=weight, passed=False,
                                reason="Keine Antwort von server.py")
                result.all_tests.append(tr)
                result.failed_tests.append(tr)
                continue

[... gekürzt — 102 Zeilen weggelassen ...]
```
