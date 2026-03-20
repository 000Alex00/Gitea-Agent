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
    Speichert einen kompakten Kontext für die Plan-Phase.

    Erstellt contexts/{num}-{typ}/starter.md mit Status ⏳.
    Kein Quellcode — nur Metadaten für den Plan-Schritt.

    Args:
        issue: Issue-dict aus Gitea API

    Returns:
        Pfad zur geschriebenen Datei.
    """
    num         = issue["number"]
    title       = issue.get("title", "")
    body        = (issue.get("body", "") or "").strip()
    stufe, desc = risk_level(issue)
    files       = relevant_files(issue)
    branch      = branch_name(issue)

    body_short = body[:200] + ("..." if len(body) > 200 else "")
    file_list  = "\n".join(f"- {f.relative_to(PROJECT)}" for f in files) \
                 or "- keine erkannt"

    content = f"""# Issue #{num} — {title}
Status: ⏳ Wartet auf Freigabe
Risiko: {stufe}/4 — {desc}
Branch: {branch}

## Ziel
{body_short}

## Dateien
{file_list}

## Checkliste
- [ ] Quellcode lesen
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei committen
- [ ] git push origin {branch}

## Commit-Template
<typ>: <beschreibung> (closes #{num})

## PR-Befehl
python3 agent_start.py --pr {num} --branch {branch} --summary "..."

## Gitea
{gitea.GITEA_URL}/{gitea.REPO}/issues/{num}
"""
    out = _issue_dir(issue) / "starter.md"
    out.write_text(content, encoding="utf-8")
    log.info(f"Kontext gespeichert: {out}")
    return out


def save_implement_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:
    """
    Speichert Kontext + Quellcode für die Implementierungs-Phase.

    Erstellt:
        contexts/{num}-{typ}/starter.md — Metadaten, Status 🔧 READY
        contexts/{num}-{typ}/files.md   — Quellcode (max settings.MAX_FILE_LINES pro Datei)

    Args:
        issue:      Issue-dict aus Gitea API
        files_dict: {relativer Pfad: Dateiinhalt}

    Returns:
        Tuple (kontext_datei, code_datei).
    """
    num         = issue["number"]
    title       = issue.get("title", "")
    body        = (issue.get("body", "") or "").strip()
    stufe, desc = risk_level(issue)
    branch      = branch_name(issue)

    body_short = body[:200] + ("..." if len(body) > 200 else "")
    file_list  = "\n".join(f"- {name}" for name in files_dict) \
                 or "- keine erkannt"

    ctx_content = f"""# Issue #{num} — {title}
Status: 🔧 READY — Implementierung starten
Risiko: {stufe}/4 — {desc}
Branch: {branch}

## Ziel
{body_short}

## Dateien
{file_list}
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin {branch}

## Commit-Template
<typ>: <beschreibung> (closes #{num})

## PR-Befehl
python3 agent_start.py --pr {num} --branch {branch} --summary "..."

## Gitea
{gitea.GITEA_URL}/{gitea.REPO}/issues/{num}
"""

    limit = settings.MAX_FILE_LINES
    parts = []
    for name, text in files_dict.items():
        lines = text.splitlines()
        if len(lines) > limit:
            code = "\n".join(lines[:limit])
            code += f"\n\n[... gekürzt — {len(lines) - limit} Zeilen weggelassen ...]"
        else:
            code = "\n".join(lines)
        parts.append(f"## {name}\n```\n{code}\n```")

    idir       = _issue_dir(issue)
    ctx_file   = idir / "starter.md"
    files_file = idir / "files.md"

    ctx_file.write_text(ctx_content, encoding="utf-8")
    files_file.write_text(
        f"# Dateien — Issue #{num}\n\n" + "\n\n".join(parts) + "\n",
        encoding="utf-8"
    )

    log.info(f"Kontext gespeichert: {ctx_file}, {files_file}")
    return ctx_file, files_file


# ---------------------------------------------------------------------------
# Analyse-Kommentar für Stufe 2/3
# ---------------------------------------------------------------------------

def _build_analyse_comment(issue: dict, files: list[Path]) -> str:
    """
    Erstellt einen Analyse-Kommentar für Stufe-2/3-Issues.

    Scannt Python-Importe der betroffenen Dateien um zusätzlich betroffene
    Module zu finden. Generiert label-spezifische Rückfragen.

    Aufgerufen von:
        cmd_plan() für Stufe 2/3 Issues

    Args:
        issue: Issue-dict aus Gitea API
        files: Bereits erkannte relevante Dateipfade

    Returns:
        Markdown-String für den Gitea-Kommentar.
    """
    num    = issue["number"]
    labels = [l["name"] for l in issue.get("labels", [])]

    # Zusätzliche betroffene Module via Import-Analyse
    extra_files = []
    for f in files:
        if f.suffix != ".py":
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    parts = node.module.split(".")
                    candidate = PROJECT / Path(*parts).with_suffix(".py")
                    if candidate.exists() and candidate not in files and candidate not in extra_files:
                        extra_files.append(candidate)
        except Exception:
            pass

    if any(lb in labels for lb in settings.RISK_BUG_LABELS):
        questions = [
            "Ist der Fehler reproduzierbar? Unter welchen Bedingungen tritt er auf?",
            "Welche Systemzustände / Konfigurationen sind betroffen?",
            "Gibt es einen bekannten Workaround?",
            "Welche anderen Komponenten könnten durch den Fix beeinflusst werden?",
        ]
        typ = "Bug"
    elif any(lb in labels for lb in settings.RISK_FEAT_LABELS):
        questions = [
            "Welche bestehenden Funktionen werden durch dieses Feature berührt?",
            "Gibt es ähnliche Funktionalität die erweitert werden könnte statt neu zu bauen?",
            "Wie soll das Feature konfigurierbar sein?",
            "Was ist der Fallback wenn das Feature fehlschlägt?",
        ]
        typ = "Feature Request"
    else:
        questions = [
            "Welche Funktionen / Klassen sind konkret betroffen?",
            "Gibt es Abhängigkeiten zu anderen Modulen die mitgeändert werden müssen?",
            "Muss die Dokumentation aktualisiert werden?",
            "Gibt es Regressions-Risiken?",
        ]
        typ = "Enhancement"

    questions_md = "\n".join(f"- [ ] {q}" for q in questions)

    extra_md = ""
    if extra_files:
        extra_list = "\n".join(f"- `{f.relative_to(PROJECT)}`" for f in extra_files)
        extra_md = f"""
### Zusätzlich möglicherweise betroffene Dateien
(via Import-Analyse — bitte prüfen ob relevant)
{extra_list}
"""

    return f"""## 🔍 Analyse — Issue #{num} ({typ})

**Label:** `{settings.LABEL_HELP}` gesetzt — bitte vor Implementierung beantworten.
{extra_md}
### Offene Fragen
{questions_md}

### Potenzielle Seiteneffekte
- [ ] Betroffene Module prüfen (siehe Dateien oben)
- [ ] Regressions-Risiko einschätzen

---
*Fragen beantworten oder kommentieren, dann `ok` für Freigabe.*

## Nächste Schritte
- Fragen oben als Kommentar beantworten
- Für neue Diskussionsrunde: `python3 agent_start.py --issue {num}` erneut starten
- Wenn Konzept steht: Label `{settings.LABEL_HELP}` manuell entfernen
- Dann `ok` kommentieren → Implementierung startet"""


# ---------------------------------------------------------------------------
# Plan- und Diskussions-Hilfsfunktionen
# ---------------------------------------------------------------------------

def _has_detailed_plan(number: int) -> bool:
    """Prüft ob in Gitea bereits ein befüllter Plan-Kommentar existiert.

    Verhindert doppeltes Posten des Analyse-Kommentars wenn Plan schon vorhanden.

    Aufgerufen von:
        cmd_plan() vor dem Posten des Analyse-Kommentars

    Args:
        number: Issue-Nummer

    Returns:
        True wenn befüllter Plan-Kommentar gefunden (kein Platzhalter).
    """
    comments = gitea.get_comments(number)
    for c in comments:
        body = c.get("body", "")
        if "Implementierungsplan" in body and "<!-- CLAUDE:" not in body:
            return True
    return False


def _update_discussion(issue: dict, starter_path: Path) -> None:
    """Liest Gitea-Kommentarhistorie und aktualisiert die starter.md.

    Wird beim Re-Run von --issue aufgerufen wenn Plan-Draft schon existiert.
    Ersetzt den ## Kommentarhistorie Block in starter.md.

    Aufgerufen von:
        cmd_plan() wenn plan.md bereits existiert (Diskussions-Runde)

    Args:
        issue:        Issue-dict aus Gitea API
        starter_path: Pfad zur starter.md
    """
    comments = gitea.get_comments(issue["number"])
    if not comments:
        return

    lines = []
    for c in comments:
        user       = c.get("user", {}).get("login", "")
        body       = c.get("body", "")
        ts         = c.get("created_at", "")[:10]
        body_short = body[:1500] + ("..." if len(body) > 1500 else "")
        lines.append(f"**[{ts}] {user}:**\n{body_short}")

    current = starter_path.read_text(encoding="utf-8")
    if "## Kommentarhistorie" in current:
        current = current[:current.index("## Kommentarhistorie")]

    starter_path.write_text(
        current.rstrip() + "\n\n## Kommentarhistorie\n\n" + "\n\n---\n\n".join(lines) + "\n",
        encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_list() -> None:
    """
    Listet alle Issues mit Label 'ready-for-agent' auf, sortiert nach Risiko.

    Aufgerufen von:
        main() wenn --list gesetzt
    """
    issues = gitea.get_issues(label=settings.LABEL_READY)
    if not issues:
        print(f"Keine Issues mit Label '{settings.LABEL_READY}' gefunden.")
        print(f"Label setzen in: {gitea.GITEA_URL}/{gitea.REPO}/issues")
        return

    print(f"\n{'#':>4}  {'Risiko':>4}  Titel")
    print("-" * 70)
    for i in sorted(issues, key=lambda x: risk_level(x)[0]):
        stufe, _ = risk_level(i)
        print(f"#{i['number']:>3}  Stufe {stufe}  {i['title'][:55]}")
    print(f"\n{len(issues)} Issue(s) bereit.")


def cmd_plan(number: int) -> None:
    """
    Schritt 1: Issue analysieren + Plan als Gitea-Kommentar posten.

    Ablauf:
        1. Issue laden + im Terminal ausgeben (Kontext für LLM)
        2. Plan-Kommentar auf Gitea posten
        3. Label: ready-for-agent → agent-proposed
    """
    issue = gitea.get_issue(number)

    stufe, _ = risk_level(issue)
    files    = relevant_files(issue)

    # Metadaten-Block (collapsible) aufbauen
    file_stats  = []
    total_chars = 0
    for f in files:
        try:
            text  = f.read_text(encoding="utf-8")
            chars = len(text)
            total_chars += chars
            file_stats.append(f"  {f.relative_to(PROJECT)} ({text.count(chr(10))} Zeilen, ~{chars // 4:,} Tokens)")
        except Exception:
            file_stats.append(f"  {f.relative_to(PROJECT)} (nicht lesbar)")

    total_tokens = total_chars // 4
    timestamp    = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    model        = os.environ.get("CLAUDE_MODEL", os.environ.get("MODEL", "unbekannt"))
    try:
        branch_cur = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT, stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        branch_cur = "unbekannt"

    file_lines = "\n".join(file_stats) or "  keine Dateien erkannt"
    metadata = f"""
---

<details>
<summary>🤖 Agent-Metadaten</summary>

| | |
|---|---|
| **Zeitstempel** | {timestamp} |
| **Modell** | {model} |
| **Git-Branch** | `{branch_cur}` |
| **Tokens geladen (est.)** | ~{total_tokens:,} (Dateiinhalt) |

**Analysierte Dateien:**
{file_lines}

> Token-Schätzung: 1 Token ≈ 4 Zeichen. Kontext-Limit Claude Sonnet: ~200.000 Token.

</details>"""

    log.info(f"Poste Plan-Kommentar für Issue #{number}")
    print("\n[→] Poste Plan-Kommentar auf Gitea...")
    gitea.post_comment(number, build_plan_comment(issue) + metadata)
    gitea.swap_label(number, settings.LABEL_READY, settings.LABEL_PROPOSED)

    out = save_plan_context(issue)
    print(f"[✓] Plan gepostet: {gitea.GITEA_URL}/{gitea.REPO}/issues/{number}")
    print(f"[✓] Kontext: {out.name}")

    if stufe >= 2:
        if not _has_detailed_plan(number):
            analyse_body = _build_analyse_comment(issue, files)
            gitea.post_comment(number, analyse_body)
            gitea.add_label(number, settings.LABEL_HELP)
            gitea.remove_label(number, settings.LABEL_PROPOSED)  # Plan noch nicht freigegeben
            out.write_text(out.read_text(encoding="utf-8") + "\n## Analyse\n" + analyse_body, encoding="utf-8")
            log.info(f"Analyse-Kommentar gepostet, Label '{settings.LABEL_HELP}' gesetzt, '{settings.LABEL_PROPOSED}' entfernt")
            print(f"[✓] Analyse-Kommentar gepostet, Label '{settings.LABEL_HELP}' gesetzt, '{settings.LABEL_PROPOSED}' entfernt")
        else:
            print(f"[!] Gitea hat bereits befüllten Plan — kein Analyse-Kommentar gepostet")

    print(f"[→] Freigabe: mit 'ok' oder 'ja' kommentieren")


def cmd_implement(number: int) -> None:
    """
    Schritt 2: Freigabe prüfen + Branch erstellen + Implementierungskontext ausgeben.

    Ablauf:
        1. Prüfen ob Freigabe-Kommentar vorhanden (ok/ja/✅)
        2. Falls ja: Branch erstellen, Label → in-progress, Kontext ausgeben
    """
    issue = gitea.get_issue(number)

    if not gitea.check_approval(number, settings.LABEL_HELP):
        log.warning(f"Keine Freigabe für Issue #{number}")
        print(f"[✗] Keine Freigabe für Issue #{number}.")
        print(f"    Kommentiere 'ok' auf: {gitea.GITEA_URL}/{gitea.REPO}/issues/{number}")
        sys.exit(1)

    log.info(f"Freigabe erhalten für Issue #{number} — starte Implementierung")
    print(f"[✓] Freigabe erhalten — starte Implementierung.")
    gitea.remove_label(number, settings.LABEL_HELP)
    branch = branch_name(issue)

    try:
        result = subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=PROJECT, capture_output=True, text=True
        )
        if result.returncode == 0:
            log.info(f"Branch '{branch}' erstellt")
            print(f"[✓] Branch '{branch}' erstellt.")
        else:
            log.warning(f"Branch existiert bereits: {result.stderr.strip()}")
            print(f"[!] Branch existiert bereits: {result.stderr.strip()}")
            subprocess.run(["git", "checkout", branch], cwd=PROJECT)
    except FileNotFoundError:
        log.warning("git nicht gefunden — Branch manuell erstellen")
        print("[!] git nicht gefunden — Branch manuell erstellen.")

    gitea.swap_label(number, settings.LABEL_PROPOSED, settings.LABEL_PROGRESS)

    typ = issue_type(issue)
    num = issue["number"]
    gitea.post_comment(number, f"""## ✅ Implementierung gestartet

**Branch:** `{branch}`

## Nächste Schritte
- Branch auschecken: `git checkout {branch}`
- Kontext lesen: `contexts/{num}-{typ}/starter.md`
- Implementieren + nach jeder Datei committen
- PR erstellen: `python3 agent_start.py --pr {num} --branch {branch} --summary "..."`
""")

    files_dict = {
        str(f.relative_to(PROJECT)): f.read_text(encoding="utf-8")
        for f in relevant_files(issue)
    }
    ctx_file, files_file = save_implement_context(issue, files_dict)
    _idir2 = _find_issue_dir(num)
    print(f"[✓] Kontext: {_idir2.name if _idir2 else ''}/starter.md + files.md — bereit zur Implementierung")


def cmd_pr(number: int, branch: str, summary: str = "") -> None:
    """
    Schritt 3: PR erstellen + Abschluss-Kommentar ins Issue posten.

    Args:
        number:  Issue-Nummer
        branch:  Feature-Branch
        summary: Optionale Zusammenfassung was gemacht wurde
    """
    issue   = gitea.get_issue(number)
    title   = f"{issue['title']} (closes #{number})"
    checklist = "\n".join(f"- [ ] {item}" for item in settings.PR_CHECKLIST)
    pr_body = f"""## Änderungen
Implementierung für Issue #{number}.

## Checkliste
{checklist}

## Issue
{gitea.GITEA_URL}/{gitea.REPO}/issues/{number}
"""
    # Prüfen ob Documentation/ seit Abzweig von main aktualisiert wurde
    docs_warning = ""
    try:
        changed  = subprocess.check_output(
            ["git", "diff", "--name-only", f"main...{branch}"],
            cwd=PROJECT, stderr=subprocess.DEVNULL
        ).decode().splitlines()
        code_changed = [f for f in changed if not f.startswith("Documentation/")]
        docs_changed = [f for f in changed if f.startswith("Documentation/")]
        if code_changed and not docs_changed:
            log.warning("Code geändert aber Documentation/ nicht aktualisiert")
            print("[!] Warnung: Code geändert aber keine Documentation/*.md aktualisiert.")
            docs_warning = "\n> ⚠️ **Hinweis:** `Documentation/` wurde nicht aktualisiert — bitte vor dem Merge nachholen."
    except Exception:
        pass

    # Eval ausführen — blockiert PR bei FAIL
    try:
        eval_result = evaluation.run(PROJECT, trigger="pr")
        print(evaluation.format_terminal(eval_result))
        if eval_result.skipped:
            log.info("Eval übersprungen (kein agent_eval.json)")
        elif eval_result.warned and not eval_result.all_tests:
            log.warning("Eval: Infrastruktur offline — PR wird trotzdem erstellt")
        elif not eval_result.passed:
            gitea.post_comment(number, evaluation.format_gitea_comment(eval_result))
            gitea.swap_label(number, settings.LABEL_REVIEW, settings.LABEL_PROGRESS)
            log.error(f"Eval FAIL — PR blockiert (Score {eval_result.score}/{eval_result.max_score})")
            print(f"[✗] PR blockiert. Kommentar in Issue #{number} gepostet.")
            return
    except Exception as e:
        msg = f"⚠️ **Eval-Fehler** — Evaluation konnte nicht ausgeführt werden:\n```\n{e}\n```\nPR wurde trotzdem erstellt — bitte `evaluation.py` prüfen."
        gitea.post_comment(number, msg)
        log.warning(f"Eval-Fehler (Warnung gepostet): {e}")
        print(f"[!] Eval-Fehler (Warnung gepostet): {e}")

    log.info(f"Erstelle PR für Issue #{number} von Branch '{branch}'")
    pr     = gitea.create_pr(branch=branch, title=title, body=pr_body)
    pr_url = pr.get("html_url", "?")

    gitea.swap_label(number, settings.LABEL_PROGRESS, settings.LABEL_REVIEW)

    summary_block = f"## Was diese Änderung bewirkt\n{summary}" if summary else \
        "> ⚠️ Keine Zusammenfassung angegeben — beim nächsten Mal `--summary \"...\"` mitgeben."
    history_block = _format_history_block(PROJECT)
    gitea.post_comment(number, f"""## Implementierung abgeschlossen

**Branch:** `{branch}`
**PR:** {pr_url}
{docs_warning}

{summary_block}

{history_block}

**Nächster Schritt:** {settings.COMPLETION_NEXT_STEP}
- Bei Revert: `Documentation/` synchron zurücksetzen""")

    idir = _find_issue_dir(number)
    if idir and idir.exists():
        shutil.move(str(idir), str(_done_dir() / idir.name))

    log.info(f"PR erstellt: {pr_url}")
    print(f"[✓] PR erstellt: {pr_url}")
    print(f"[✓] Kommentar in Issue #{number} gepostet.")


def cmd_fixup(number: int) -> None:
    """
    Nach einem Bugfix-Commit auf einem in-progress Issue:
    - Liest die letzte Commit-Message
    - Postet Bugfix-Kommentar ins Gitea-Issue
    - Setzt Label: in-progress → needs-review
    """
    try:
        commit_msg = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s%n%n%b"],
            cwd=PROJECT, stderr=subprocess.DEVNULL
        ).decode().strip()
        commit_sha = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%h"],
            cwd=PROJECT, stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception as e:
        log.warning(f"git log fehlgeschlagen: {e}")
        commit_msg = "(Commit-Message nicht lesbar)"
        commit_sha = "?"

    body = (
        f"## 🔧 Bugfix committed\n\n"
        f"**Commit:** `{commit_sha}`\n\n"
        f"```\n{commit_msg}\n```\n\n"
        f"## Nächste Schritte\n"
        f"- Bitte erneut testen\n"
        f"- Bei OK: PR mergen + Issue schließen"
    )
    gitea.post_comment(number, body)
    gitea.swap_label(number, settings.LABEL_PROGRESS, settings.LABEL_REVIEW)
    log.info(f"Bugfix-Kommentar gepostet für Issue #{number}")
    print(f"[✓] Bugfix-Kommentar gepostet + Label → needs-review")
    print(f"    {gitea.GITEA_URL}/{gitea.REPO}/issues/{number}")


# ---------------------------------------------------------------------------
# Watch-Modus
# ---------------------------------------------------------------------------

def _auto_issue_exists(test_name: str) -> bool:
    """Prüft ob ein offenes [Auto]-Issue für diesen Test bereits existiert."""
    issues = gitea.get_issues(state="open")
    marker = f"[Auto] {test_name}"
    return any(marker in i.get("title", "") for i in issues)


def _close_resolved_auto_issues(result: "evaluation.EvalResult") -> None:
    """Schließt [Auto]-Issues deren Test jetzt wieder besteht."""
    passed_names = {t.name for t in result.all_tests if t.passed}
    issues = gitea.get_issues(state="open")
    for issue in issues:
        title = issue.get("title", "")
        if not title.startswith("[Auto]"):
            continue
        for name in passed_names:
            if name in title:
                gitea.close_issue(issue["number"])
                log.info(f"[Auto]-Issue #{issue['number']} geschlossen — Test '{name}' besteht wieder")
                print(f"[✓] Auto-Issue #{issue['number']} geschlossen ({name} wieder OK)")


def _format_history_block(project_root: Path, n: int = 5) -> str:
    """
    Liest die letzten n Einträge aus score_history.json und gibt
    einen Markdown-Block für Gitea-Kommentare zurück.

    Args:
        project_root: Pfad zum Zielprojekt
        n:            Anzahl Einträge (Standard: 5)

    Returns:
        Markdown-String oder leer wenn keine History vorhanden.
    """
    hist_path = project_root / evaluation.SCORE_HISTORY
    if not hist_path.exists():
        return ""
    try:
        with hist_path.open(encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return ""
    if not history:
        return ""

    recent = history[-n:][::-1]  # letzte n, neueste zuerst
    lines = ["**Verlauf (letzte 5):**", "```"]
    for e in recent:
        ts      = e.get("timestamp", "?")[:16].replace("T", " ")
        score   = int(e.get("score", 0))
        max_s   = int(e.get("max_score", 0))
        trigger = e.get("trigger", "?")
        failed  = e.get("failed", [])
        failed_str = ", ".join(f["name"] for f in failed) if failed else "—"
        lines.append(f"{ts} | {score}/{max_s} | {trigger:<6} | {failed_str}")
    lines.append("```")
    return "\n".join(lines)


def cmd_watch(interval_minutes: int = 60) -> None:
    """
    Periodischer Eval-Loop: läuft alle interval_minutes Minuten.

    Bei Score-Verlust: erstellt automatisch ein Gitea-Issue mit Label ready-for-agent.
    Bei Erholung: schließt das [Auto]-Issue wieder.
    Deduplication: pro Test nur ein offenes [Auto]-Issue (Titel-Check).

    Aufgerufen von:
        main() wenn --watch gesetzt
    """
    print(f"[→] Watch-Modus gestartet — Interval: {interval_minutes} Minuten")
    print(f"    Abbrechen mit Ctrl+C\n")
    log.info(f"Watch-Modus gestartet (Interval: {interval_minutes}min)")

    while True:
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] Eval läuft...")

        try:
            result = evaluation.run(PROJECT, trigger="watch")
            print(evaluation.format_terminal(result))

            if not result.skipped and not result.warned:
                _close_resolved_auto_issues(result)

                for failed in result.failed_tests:
                    if failed.skipped:
                        continue
                    if _auto_issue_exists(failed.name):
                        log.debug(f"[Auto]-Issue für '{failed.name}' bereits offen — kein Duplikat")
                        continue

                    try:
                        commit = subprocess.check_output(
                            ["git", "log", "-1", "--pretty=%h %s"],
                            cwd=PROJECT, stderr=subprocess.DEVNULL
                        ).decode().strip()
                    except Exception:
                        commit = "unbekannt"

                    history_block = _format_history_block(PROJECT)
                    body = (
                        f"## Score-Verlust erkannt\n\n"
                        f"**Test:** {failed.name} (Gewicht {failed.weight})\n"
                        f"**Fehler:** {failed.reason}\n"
                        f"**Score:** {result.score:.0f}/{result.max_score} (Baseline: {result.baseline_score:.0f})\n\n"
                        f"**Letzter Commit:** `{commit}`\n\n"
                        f"{history_block}\n\n"
                        f"> Automatisch erkannt durch Watch-Modus.\n"
                        f"> Wird automatisch geschlossen wenn der Test wieder besteht."
                    )
                    issue = gitea.create_issue(
                        title=f"[Auto] {failed.name} fehlgeschlagen — Score-Verlust erkannt",
                        body=body,
                        label=settings.LABEL_READY,
                    )
                    log.warning(f"Auto-Issue erstellt: #{issue['number']} für '{failed.name}'")
                    print(f"[!] Auto-Issue erstellt: #{issue['number']} — {failed.name}")

        except Exception as e:
            log.error(f"Watch-Lauf Fehler: {e}")
            print(f"[!] Fehler in Watch-Lauf: {e}")

        print(f"    Nächster Lauf in {interval_minutes} Minute(n)...\n")
        time.sleep(interval_minutes * 60)


# ---------------------------------------------------------------------------
# Auto-Modus
# ---------------------------------------------------------------------------

def cmd_auto() -> None:
    """
    Standard-Modus (kein Argument): Scannt Gitea und verarbeitet alle Issues.

    Reihenfolge:
        1. agent-proposed + Freigabe → implementieren (alle)
        2. ready-for-agent → Plan posten (alle, nach Risiko sortiert)
        3. Status-Übersicht anzeigen
    """
    print("=" * 70)
    print("  GITEA AGENT — AUTO-SCAN")
    print("=" * 70)
    log.info("Auto-Scan gestartet")

    # Aufräumen: geschlossene Issues → contexts/done/
    contexts = _context_dir()
    if contexts.exists():
        for idir in contexts.iterdir():
            if not idir.is_dir() or idir.name == "done":
                continue
            try:
                num   = int(idir.name.split("-")[0])
                issue = gitea.get_issue(num)
                if issue.get("state") == "closed":
                    shutil.move(str(idir), str(_done_dir() / idir.name))
                    log.info(f"Issue #{num} geschlossen → contexts/done/{idir.name}/")
                    print(f"[✓] Issue #{num} geschlossen → contexts/done/{idir.name}/")
            except Exception:
                pass

    did_something = False

    # Freigegebene Pläne implementieren
    proposed = gitea.get_issues(label=settings.LABEL_PROPOSED)
    approved = sorted(
        [i for i in proposed if gitea.check_approval(i["number"], settings.LABEL_HELP)],
        key=lambda x: risk_level(x)[0]
    )
    if approved:
        print(f"\n[✓] {len(approved)} freigegebene Issue(s) — starte Implementierung:\n")
        for issue in approved:
            log.info(f"Implementiere Issue #{issue['number']}: {issue['title'][:60]}")
            print(f"  → #{issue['number']} {issue['title'][:60]}")
            cmd_implement(issue["number"])
            print()
        did_something = True

    # Neue Issues planen
    ready = sorted(gitea.get_issues(label=settings.LABEL_READY), key=lambda x: risk_level(x)[0])
    if ready:
        print(f"\n[→] {len(ready)} Issue(s) bereit — poste Pläne:\n")
        for issue in ready:
            stufe, _ = risk_level(issue)
            log.info(f"Plane Issue #{issue['number']} (Stufe {stufe}): {issue['title'][:55]}")
            print(f"  → #{issue['number']} (Stufe {stufe}) {issue['title'][:55]}")
            cmd_plan(issue["number"])
            print()
        print(f"[→] Freigabe mit 'ok' kommentieren: {gitea.GITEA_URL}/{gitea.REPO}/issues")
        did_something = True

    # Status-Übersicht
    in_progress = gitea.get_issues(label=settings.LABEL_PROGRESS)
    waiting     = [i for i in proposed if not gitea.check_approval(i["number"], settings.LABEL_HELP)]

    if in_progress:
        print(f"\nIn Arbeit ({len(in_progress)}):")
        for i in in_progress:
            print(f"  #{i['number']} {i['title'][:60]}")
        did_something = True

    if waiting:
        print(f"\nWartet auf Freigabe ({len(waiting)}):")
        for i in waiting:
            print(f"  #{i['number']} {i['title'][:60]}  [⏳ 'ok' kommentieren]")
        did_something = True

    if not did_something:
        log.info("Auto-Scan: Nichts zu tun")
        print("\n[✓] Nichts zu tun.")
        print(f"    {gitea.GITEA_URL}/{gitea.REPO}/issues")
    print()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def _apply_auto_approve() -> None:
    """Schreibt .claude/settings.local.json basierend auf AUTO_APPROVE in .env."""
    import json
    claude_dir  = _HERE / ".claude"
    claude_dir.mkdir(exist_ok=True)
    target = claude_dir / "settings.local.json"

    if settings.AUTO_APPROVE:
        data = {"permissions": {"allow": ["Bash(*)", "Read(*)", "Write(*)", "Edit(*)", "Glob(*)", "Grep(*)", "Agent(*)", "WebFetch(*)", "WebSearch(*)"]}}
    else:
        data = {"permissions": {"allow": []}}

    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    log.debug(f"AUTO_APPROVE={'true' if settings.AUTO_APPROVE else 'false'} → {target}")


def main():
    from log import setup as log_setup
    log_setup(log_file=settings.LOG_FILE, level=settings.LOG_LEVEL)
    _apply_auto_approve()

    parser = argparse.ArgumentParser(
        description="Gitea Agent — automatischer Issue-Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ohne Argumente: automatischer Modus.

  python3 agent_start.py                              → Auto-Scan
  python3 agent_start.py --list                       → Status-Übersicht
  python3 agent_start.py --issue 16                   → Plan posten
  python3 agent_start.py --implement 16               → Implementieren
  python3 agent_start.py --pr 16 --branch fix/issue-16-xyz  → PR erstellen
        """
    )
    parser.add_argument("--list",      action="store_true",        help="Alle ready-for-agent Issues auflisten")
    parser.add_argument("--issue",     type=int,  metavar="NR",    help="Plan für Issue posten")
    parser.add_argument("--implement", type=int,  metavar="NR",    help="Nach OK: Branch + Implementierungskontext")
    parser.add_argument("--fixup",     type=int,  metavar="NR",    help="Nach Bugfix: Kommentar + needs-review setzen")
    parser.add_argument("--pr",        type=int,  metavar="NR",    help="PR erstellen (mit --branch)")
    parser.add_argument("--branch",    type=str,  metavar="BRANCH",help="Branch-Name für --pr")
    parser.add_argument("--summary",   type=str,  metavar="TEXT",  help="Zusammenfassung für Issue-Kommentar", default="")
    parser.add_argument("--watch",         action="store_true",         help="Periodischer Eval-Loop mit Auto-Issues")
    parser.add_argument("--interval",      type=int,  metavar="MIN",   help="Interval für --watch in Minuten (Standard: 60)", default=60)
    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.issue:
        cmd_plan(args.issue)
    elif args.implement:
        cmd_implement(args.implement)
    elif args.fixup:
        cmd_fixup(args.fixup)
    elif args.watch:
        cmd_watch(args.interval)
    elif args.pr:
        if not args.branch:
            log.error("--pr benötigt --branch <branch-name>")
            print("[✗] --pr benötigt --branch <branch-name>")
            sys.exit(1)
        cmd_pr(args.pr, args.branch, args.summary)
    else:
        cmd_auto()


if __name__ == "__main__":
    main()
