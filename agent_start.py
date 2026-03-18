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
    GITEA_URL       = http://your-gitea:3000
    GITEA_USER      = username
    GITEA_TOKEN     = api-token
    GITEA_REPO      = owner/repo
    GITEA_BOT_USER  = bot-username   (optional)
    GITEA_BOT_TOKEN = bot-api-token  (optional)
    PROJECT_ROOT    = /path/to/project  (optional, Standard: Elternverzeichnis)

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
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("PROJECT_ROOT="):
                p = Path(line.split("=", 1)[1].strip())
                if p.exists():
                    return p
    return _HERE.parent

PROJECT = _project_root()

LABEL_READY    = "ready-for-agent"
LABEL_PROPOSED = "agent-proposed"
LABEL_PROGRESS = "in-progress"
LABEL_REVIEW   = "needs-review"


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
    safe   = ["docstring", "docs", "comment", "dead code", "cleanup", "import"]

    if "bug" in labels:
        return 3, "HOCH — Bug (Plan erforderlich)"
    if "Feature request" in labels:
        return 3, "HOCH — Neues Feature (Plan + Freigabe erforderlich)"
    if "enhancement" in labels:
        if any(w in title for w in safe):
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
    body  = issue.get("body", "")
    found = []
    for line in body.splitlines():
        for part in line.split("`"):
            p = PROJECT / part.strip()
            if p.exists() and p.is_file() and p.suffix in (".py", ".js", ".sh", ".yaml", ".md"):
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

    prefix = "fix" if "bug" in labels else "feat" if "Feature request" in labels else "chore"
    if any(w in title for w in ["docs", "docstring", "comment"]):
        prefix = "docs"

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
> Dieser Abschnitt wird vom LLM-Agenten nach Code-Analyse ausgefüllt.
> Der Agent liest die Dateien, mappt Abhängigkeiten und beschreibt:
> - Root-Cause / Was genau geändert wird
> - Welche Funktionen/Zeilen betroffen sind
> - Mögliche Seiteneffekte / Regressionsrisiko
> - Vorgehensweise Schritt für Schritt

### Geplanter Branch
`{branch}`

### Commit-Template
```
<typ>: <beschreibung> (closes #{num})
```

---

**OK zum Implementieren?**
Antworte mit `ok`, `ja` oder `✅` um die Implementierung zu starten.
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
# Subcommands
# ---------------------------------------------------------------------------

def cmd_list() -> None:
    """
    Listet alle Issues mit Label 'ready-for-agent' auf, sortiert nach Risiko.

    Aufgerufen von:
        main() wenn --list gesetzt
    """
    issues = gitea.get_issues(label=LABEL_READY)
    if not issues:
        print("Keine Issues mit Label 'ready-for-agent' gefunden.")
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
    print_context(issue)

    print("\n[→] Poste Plan-Kommentar auf Gitea...")
    gitea.post_comment(number, build_plan_comment(issue))
    gitea.swap_label(number, LABEL_READY, LABEL_PROPOSED)

    print(f"[✓] Kommentar gepostet: {gitea.GITEA_URL}/{gitea.REPO}/issues/{number}")
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
        print(f"[✗] Keine Freigabe für Issue #{number}.")
        print(f"    Kommentiere 'ok' auf: {gitea.GITEA_URL}/{gitea.REPO}/issues/{number}")
        sys.exit(1)

    print(f"[✓] Freigabe erhalten — starte Implementierung.")
    branch = branch_name(issue)

    try:
        result = subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=PROJECT, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"[✓] Branch '{branch}' erstellt.")
        else:
            print(f"[!] Branch existiert bereits: {result.stderr.strip()}")
            subprocess.run(["git", "checkout", branch], cwd=PROJECT)
    except FileNotFoundError:
        print("[!] git nicht gefunden — Branch manuell erstellen.")

    gitea.swap_label(number, LABEL_PROPOSED, LABEL_PROGRESS)
    print_context(issue)

    print(f"""
[→] Implementierungs-Checkliste:
    [ ] Quellcode der betroffenen Dateien lesen
    [ ] Ähnliche Funktionen per grep prüfen
    [ ] Änderung vornehmen
    [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
    [ ] git push origin {branch}
    [ ] PR erstellen: python3 agent_start.py --pr {number} --branch {branch}
""")


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
    pr_body = f"""## Änderungen
Implementierung für Issue #{number}.

## Checkliste
- [ ] Code geändert
- [ ] Dokumentation aktualisiert
- [ ] Kein toter Code hinzugefügt
- [ ] Getestet

## Issue
{gitea.GITEA_URL}/{gitea.REPO}/issues/{number}
"""
    pr     = gitea.create_pr(branch=branch, title=title, body=pr_body)
    pr_url = pr.get("html_url", "?")

    gitea.swap_label(number, LABEL_PROGRESS, LABEL_REVIEW)

    summary_block = ("### Was wurde gemacht\n" + summary) if summary else ""
    gitea.post_comment(number, f"""## Implementierung abgeschlossen

**Branch:** `{branch}`
**PR:** {pr_url}

{summary_block}

**Nächster Schritt:** PR reviewen und mergen.
Nach dem Merge: Issue schließen.""")

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

    did_something = False

    # Freigegebene Pläne implementieren
    proposed = gitea.get_issues(label=LABEL_PROPOSED)
    approved = sorted(
        [i for i in proposed if gitea.check_approval(i["number"])],
        key=lambda x: risk_level(x)[0]
    )
    if approved:
        print(f"\n[✓] {len(approved)} freigegebene Issue(s) — starte Implementierung:\n")
        for issue in approved:
            print(f"  → #{issue['number']} {issue['title'][:60]}")
            cmd_implement(issue["number"])
            print()
        did_something = True

    # Neue Issues planen
    ready = sorted(gitea.get_issues(label=LABEL_READY), key=lambda x: risk_level(x)[0])
    if ready:
        print(f"\n[→] {len(ready)} Issue(s) bereit — poste Pläne:\n")
        for issue in ready:
            stufe, _ = risk_level(issue)
            print(f"  → #{issue['number']} (Stufe {stufe}) {issue['title'][:55]}")
            cmd_plan(issue["number"])
            print()
        print(f"[→] Freigabe mit 'ok' kommentieren: {gitea.GITEA_URL}/{gitea.REPO}/issues")
        did_something = True

    # Status-Übersicht
    in_progress = gitea.get_issues(label=LABEL_PROGRESS)
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
        print("\n[✓] Nichts zu tun.")
        print(f"    {gitea.GITEA_URL}/{gitea.REPO}/issues")
    print()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
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
            print("[✗] --pr benötigt --branch <branch-name>")
            sys.exit(1)
        cmd_pr(args.pr, args.branch, args.summary)
    else:
        cmd_auto()


if __name__ == "__main__":
    main()
