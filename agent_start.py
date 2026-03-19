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
import os
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
import gitea_api as gitea
import settings
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


def save_plan_context(issue: dict) -> Path:
    """
    Speichert einen kompakten Kontext für die Plan-Phase.

    Erstellt contexts/issue-{num}.md mit Status ⏳.
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
    ctx = _context_dir()
    ctx.mkdir(parents=True, exist_ok=True)
    out = ctx / f"issue-{num}.md"
    out.write_text(content, encoding="utf-8")
    log.info(f"Kontext gespeichert: {out}")
    return out


def save_implement_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:
    """
    Speichert Kontext + Quellcode für die Implementierungs-Phase.

    Erstellt:
        contexts/issue-{num}.md       — Metadaten, Status 🔧 READY
        contexts/issue-{num}-files.md — Quellcode (max settings.MAX_FILE_LINES pro Datei)

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
(Quellcode: issue-{num}-files.md)

## Checkliste
- [ ] Quellcode lesen (issue-{num}-files.md)
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

    ctx = _context_dir()
    ctx.mkdir(parents=True, exist_ok=True)

    ctx_file   = ctx / f"issue-{num}.md"
    files_file = ctx / f"issue-{num}-files.md"

    ctx_file.write_text(ctx_content, encoding="utf-8")
    files_file.write_text(
        f"# Dateien — Issue #{num}\n\n" + "\n\n".join(parts) + "\n",
        encoding="utf-8"
    )

    log.info(f"Kontext gespeichert: {ctx_file}, {files_file}")
    return ctx_file, files_file


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

    log.info(f"Poste Plan-Kommentar für Issue #{number}")
    print("\n[→] Poste Plan-Kommentar auf Gitea...")
    gitea.post_comment(number, build_plan_comment(issue))
    gitea.swap_label(number, settings.LABEL_READY, settings.LABEL_PROPOSED)

    out = save_plan_context(issue)
    print(f"[✓] Kommentar gepostet: {gitea.GITEA_URL}/{gitea.REPO}/issues/{number}")
    print(f"[✓] Kontext: {out}")
    print(f"[→] Freigabe: mit 'ok' oder 'ja' kommentieren")


def cmd_implement(number: int) -> None:
    """
    Schritt 2: Freigabe prüfen + Branch erstellen + Implementierungskontext ausgeben.

    Ablauf:
        1. Prüfen ob Freigabe-Kommentar vorhanden (ok/ja/✅)
        2. Falls ja: Branch erstellen, Label → in-progress, Kontext ausgeben
    """
    issue = gitea.get_issue(number)

    if not gitea.check_approval(number):
        log.warning(f"Keine Freigabe für Issue #{number}")
        print(f"[✗] Keine Freigabe für Issue #{number}.")
        print(f"    Kommentiere 'ok' auf: {gitea.GITEA_URL}/{gitea.REPO}/issues/{number}")
        sys.exit(1)

    log.info(f"Freigabe erhalten für Issue #{number} — starte Implementierung")
    print(f"[✓] Freigabe erhalten — starte Implementierung.")
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

    files_dict = {
        str(f.relative_to(PROJECT)): f.read_text(encoding="utf-8")
        for f in relevant_files(issue)
    }
    ctx_file, files_file = save_implement_context(issue, files_dict)
    print(f"[✓] Kontext: {ctx_file.name} + {files_file.name} — bereit zur Implementierung")


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
    log.info(f"Erstelle PR für Issue #{number} von Branch '{branch}'")
    pr     = gitea.create_pr(branch=branch, title=title, body=pr_body)
    pr_url = pr.get("html_url", "?")

    gitea.swap_label(number, settings.LABEL_PROGRESS, settings.LABEL_REVIEW)

    summary_block = ("### Was wurde gemacht\n" + summary) if summary else ""
    gitea.post_comment(number, f"""## Implementierung abgeschlossen

**Branch:** `{branch}`
**PR:** {pr_url}

{summary_block}

**Nächster Schritt:** {settings.COMPLETION_NEXT_STEP}""")

    log.info(f"PR erstellt: {pr_url}")
    print(f"[✓] PR erstellt: {pr_url}")
    print(f"[✓] Kommentar in Issue #{number} gepostet.")


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

    did_something = False

    # Freigegebene Pläne implementieren
    proposed = gitea.get_issues(label=settings.LABEL_PROPOSED)
    approved = sorted(
        [i for i in proposed if gitea.check_approval(i["number"])],
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
    waiting     = [i for i in proposed if not gitea.check_approval(i["number"])]

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

def main():
    from log import setup as log_setup
    log_setup(log_file=settings.LOG_FILE, level=settings.LOG_LEVEL)

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
    parser.add_argument("--pr",        type=int,  metavar="NR",    help="PR erstellen (mit --branch)")
    parser.add_argument("--branch",    type=str,  metavar="BRANCH",help="Branch-Name für --pr")
    parser.add_argument("--summary",   type=str,  metavar="TEXT",  help="Zusammenfassung für Issue-Kommentar", default="")
    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.issue:
        cmd_plan(args.issue)
    elif args.implement:
        cmd_implement(args.implement)
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
