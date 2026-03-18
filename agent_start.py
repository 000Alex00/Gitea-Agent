#!/usr/bin/env python3
"""
agent_start.py — LLM-agnostischer Agent-Einstiegspunkt für Gitea Issue-Workflows.

MVP-Workflow:
    1. --issue <NR>     → Agent liest Issue, analysiert Code, postet Plan als Kommentar
                          \"OK zum Implementieren?\" → wartet auf Antwort in Gitea
    2. --implement <NR> → Prüft ob Freigabe im Kommentar vorhanden, dann Branch + Kontext

Verwendung:
    python3 agent_start.py --list               # Alle ready-for-agent Issues
    python3 agent_start.py --issue 16           # Plan erstellen + Gitea-Kommentar posten
    python3 agent_start.py --implement 16       # Nach OK: Branch erstellen + Kontext
    python3 agent_start.py --pr 16 --branch fix/issue-16-xyz  # PR erstellen

LLM-agnostisch:
    Für Claude Code (Zed): direkt im Terminal ausführen
    Für andere LLMs:       Output als System-Prompt + Dateiinhalte als Kontext übergeben

Auth:
    Liest GITEA_TOKEN aus .env (selbes Verzeichnis oder cwd).
    Fallback: interaktiver Passwort-Prompt.

Konfiguration (.env):
    GITEA_URL  = http://your-gitea-host:3000
    GITEA_USER = your-username
    GITEA_TOKEN = your-api-token
    GITEA_REPO = owner/repo-name
"""

import argparse
import subprocess
import sys
from pathlib import Path

import gitea_api as gitea

# Label-Konstanten (müssen im Gitea-Repo existieren)
LABEL_READY    = "ready-for-agent"
LABEL_PROGRESS = "in-progress"
LABEL_PROPOSED = "agent-proposed"
LABEL_REVIEW   = "needs-review"


# ---------------------------------------------------------------------------
# Risiko-Klassifikation
# ---------------------------------------------------------------------------

def risk_level(issue: dict) -> tuple[int, str]:
    """
    Bestimmt die Risikostufe eines Issues (1=niedrig bis 4=kritisch).

    Stufe 1 — NIEDRIG: Docs, Cleanup, Kommentare → direkte Implementierung möglich
    Stufe 2 — MITTEL:  Enhancements, Refactoring → Plan vor Implementierung
    Stufe 3 — HOCH:    Bugs, neue Features → Plan + Freigabe erforderlich
    Stufe 4 — KRITISCH: Breaking Changes, Security → manuell, kein Auto-Deploy

    Args:
        issue: Issue-dict aus Gitea API

    Returns:
        Tuple (stufe: int, beschreibung: str)
    """
    labels = [l["name"] for l in issue.get("labels", [])]
    title  = issue.get("title", "").lower()

    safe_keywords = ["docstring", "docs", "kommentar", "dead code", "toten code", "cleanup", "import entfernen"]

    if "bug" in labels:
        return 3, "HOCH — Bug (Plan + Freigabe erforderlich)"
    if "Feature request" in labels:
        return 3, "HOCH — Neues Feature (Plan + Freigabe erforderlich)"
    if "enhancement" in labels:
        if any(w in title for w in safe_keywords):
            return 1, "NIEDRIG — Dokumentation/Cleanup (direkte Implementierung möglich)"
        return 2, "MITTEL — Enhancement (Plan vor Implementierung)"
    return 2, "MITTEL — Unbekannt (Plan vor Implementierung)"


# ---------------------------------------------------------------------------
# Relevante Dateien aus Issue-Body extrahieren
# ---------------------------------------------------------------------------

def relevant_files(issue: dict, project_root: Path) -> list[Path]:
    """
    Extrahiert Dateipfade aus dem Issue-Body (Backtick-Erwähnungen).

    Sucht nach `datei.py` Mustern im Issue-Body und prüft ob die Datei existiert.

    Args:
        issue:        Issue-dict
        project_root: Wurzelverzeichnis des Projekts

    Returns:
        Liste existierender Dateipfade (dedupliziert).
    """
    body  = issue.get("body", "")
    found = []
    for line in body.splitlines():
        for part in line.split("`"):
            p = project_root / part.strip()
            if p.exists() and p.is_file() and p.suffix in (".py", ".js", ".ts", ".sh", ".yaml", ".yml", ".md", ".json"):
                found.append(p)
    return list(dict.fromkeys(found))


# ---------------------------------------------------------------------------
# Branch-Name generieren
# ---------------------------------------------------------------------------

def branch_name(issue: dict) -> str:
    """
    Generiert einen Branch-Namen aus Issue-Nummer und Titel.

    Beispiele:
        \"fix/issue-16-ritual-http-call\"
        \"feat/issue-7-easter-egg\"
        \"docs/issue-20-docstrings-server\"

    Args:
        issue: Issue-dict

    Returns:
        Branch-Name als String.
    """
    num    = issue["number"]
    title  = issue.get("title", "").lower()
    labels = [l["name"] for l in issue.get("labels", [])]

    if "bug" in labels:
        prefix = "fix"
    elif "Feature request" in labels:
        prefix = "feat"
    else:
        prefix = "chore"

    if any(w in title for w in ["docs", "docstring", "dokumentation"]):
        prefix = "docs"

    slug = title
    for ch in " /()→.:,äöüß":
        slug = slug.replace(ch, "-")
    slug = slug.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    slug = "-".join(w for w in slug.split("-") if w)[:40]
    return f"{prefix}/issue-{num}-{slug}"


# ---------------------------------------------------------------------------
# Plan-Kommentar bauen
# ---------------------------------------------------------------------------

def build_plan_comment(issue: dict, project_root: Path) -> str:
    """
    Erstellt das Plan-Kommentar-Template das auf Gitea gepostet wird.

    Der Implementierungsplan-Abschnitt ist ein Platzhalter — der LLM-Agent
    muss ihn nach Code-Analyse ausfüllen BEVOR er postet.

    Args:
        issue:        Issue-dict
        project_root: Wurzelverzeichnis des Projekts

    Returns:
        Markdown-Text für den Gitea-Kommentar.
    """
    num         = issue["number"]
    stufe, desc = risk_level(issue)
    files       = relevant_files(issue, project_root)
    branch      = branch_name(issue)

    file_list = "\n".join(f"- `{f.relative_to(project_root)}`" for f in files) \
                or "- Keine automatisch erkannt — bitte manuell prüfen"

    return f"""## 🤖 Agent-Analyse — Issue #{num}

**Risikostufe:** {stufe}/4 — {desc}

### Betroffene Dateien
{file_list}

### Implementierungsplan
> ⚠️ Dieser Abschnitt wird vom LLM-Agenten nach Code-Analyse ausgefüllt.
> Der Agent liest die Dateien, mappt Abhängigkeiten und beschreibt konkret:
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
Bei Änderungswünschen: einfach kommentieren, ich passe den Plan an.
"""


# ---------------------------------------------------------------------------
# Terminal-Ausgabe für LLM-Kontext
# ---------------------------------------------------------------------------

def print_context(issue: dict, project_root: Path) -> None:
    """
    Gibt strukturierten Kontext für den LLM-Agenten im Terminal aus.

    Für Claude Code: direkt lesbar im Terminal.
    Für andere LLMs: Output als System-Prompt verwenden.

    Args:
        issue:        Issue-dict
        project_root: Wurzelverzeichnis des Projekts
    """
    num         = issue["number"]
    title       = issue.get("title", "")
    body        = issue.get("body", "")
    stufe, desc = risk_level(issue)
    files       = relevant_files(issue, project_root)
    branch      = branch_name(issue)

    print("=" * 70)
    print(f"  GITEA AGENT — ISSUE #{num}")
    print("=" * 70)
    print(f"\nTitel:       {title}")
    print(f"Risikostufe: {stufe}/4 — {desc}")
    print(f"\n--- Issue-Beschreibung ---\n{body}")

    print("\n--- Pflicht vor Implementierung ---")
    print("""
1. Quellcode der betroffenen Dateien lesen
2. grep: Gibt es ähnliche Funktionen bereits? (Anti-Duplikat-Regel)
3. Plan als Gitea-Kommentar posten (VOR erster Code-Änderung)
4. Branch erstellen (siehe unten)
5. Nach JEDER Datei-Änderung: sofort committen (Token-Checkpoint)
6. PR öffnen → Mensch reviewt → Merge
""")

    if files:
        print("--- Erkannte relevante Dateien ---")
        for f in files:
            rel     = f.relative_to(project_root)
            size_kb = f.stat().st_size // 1024 + 1
            print(f"  {rel}  ({size_kb} KB)")

    print(f"\n--- Branch ---")
    print(f"  git checkout -b {branch}")

    print(f"\n--- Gitea Issue ---")
    print(f"  {gitea.GITEA_URL}/{gitea.REPO}/issues/{num}")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_list() -> None:
    """Listet alle Issues mit Label 'ready-for-agent' auf."""
    issues = gitea.get_issues(label=LABEL_READY)
    if not issues:
        print(f"Keine Issues mit Label '{LABEL_READY}' gefunden.")
        print(f"Label setzen in: {gitea.GITEA_URL}/{gitea.REPO}/issues")
        return

    print(f"\n{'#':>4}  {'Risiko':>7}  Titel")
    print("-" * 70)
    for i in sorted(issues, key=lambda x: risk_level(x)[0]):
        stufe, _ = risk_level(i)
        print(f"#{i['number']:>3}  Stufe {stufe}  {i['title'][:55]}")
    print(f"\n{len(issues)} Issue(s) bereit.")
    print(f"\nPlan erstellen:         python3 agent_start.py --issue <NR>")
    print(f"Nach OK implementieren: python3 agent_start.py --implement <NR>")


def cmd_plan(number: int, project_root: Path) -> None:
    """
    Schritt 1: Issue analysieren + Plan als Gitea-Kommentar posten.

    Ablauf:
        1. Issue laden + im Terminal ausgeben (Kontext für LLM)
        2. Plan-Kommentar-Template generieren + auf Gitea posten
        3. Label: ready-for-agent → agent-proposed
        4. Link zum Kommentar ausgeben

    Args:
        number:       Issue-Nummer
        project_root: Wurzelverzeichnis des Projekts
    """
    issue = gitea.get_issue(number)
    print_context(issue, project_root)

    print("\n[→] Poste Plan-Kommentar auf Gitea...")
    comment_body = build_plan_comment(issue, project_root)
    gitea.post_comment(number, comment_body)
    gitea.swap_label(number, LABEL_READY, LABEL_PROPOSED)

    print(f"[✓] Kommentar gepostet:")
    print(f"    {gitea.GITEA_URL}/{gitea.REPO}/issues/{number}")
    print(f"\n[→] Nächster Schritt:")
    print(f"    1. Kommentar prüfen und ggf. anpassen")
    print(f"    2. Mit 'ok' oder 'ja' freigeben")
    print(f"    3. python3 agent_start.py --implement {number}")


def cmd_implement(number: int, project_root: Path) -> None:
    """
    Schritt 2: Freigabe prüfen + Branch erstellen + Implementierungskontext ausgeben.

    Ablauf:
        1. Prüfen ob Freigabe-Kommentar vorhanden (ok/ja/✅)
        2. Falls nein: Abbruch mit Hinweis
        3. Falls ja: Branch erstellen + Implementierungs-Prompt ausgeben
        4. Label: agent-proposed → in-progress

    Hinweis:
        Die eigentliche Implementierung führt der LLM-Agent durch — dieses Script
        gibt nur den strukturierten Kontext und erstellt den Branch.

    Args:
        number:       Issue-Nummer
        project_root: Wurzelverzeichnis des Projekts
    """
    issue = gitea.get_issue(number)

    print(f"[→] Prüfe Freigabe für Issue #{number}...")
    if not gitea.check_approval(number):
        print(f"[✗] Keine Freigabe gefunden.")
        print(f"    Bitte kommentiere 'ok' oder 'ja' auf:")
        print(f"    {gitea.GITEA_URL}/{gitea.REPO}/issues/{number}")
        sys.exit(1)

    print(f"[✓] Freigabe erhalten — starte Implementierung.")

    branch = branch_name(issue)
    print(f"\n[→] Branch erstellen: {branch}")

    try:
        result = subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=project_root, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"[✓] Branch '{branch}' erstellt.")
        else:
            print(f"[!] Branch existiert bereits oder Fehler: {result.stderr.strip()}")
            subprocess.run(["git", "checkout", branch], cwd=project_root)
    except FileNotFoundError:
        print("[!] git nicht gefunden — Branch manuell erstellen.")

    gitea.swap_label(number, LABEL_PROPOSED, LABEL_PROGRESS)
    print_context(issue, project_root)

    print(f"""
[→] Implementierungs-Checkliste:
    [ ] Quellcode der betroffenen Dateien lesen
    [ ] grep: Ähnliche Funktionen vorhanden?
    [ ] Änderung vornehmen
    [ ] Nach jeder Datei: git add <datei> && git commit -m \"...\"
    [ ] git push origin {branch}
    [ ] PR erstellen: python3 agent_start.py --pr {number} --branch {branch}

Commit-Template:
    <typ>: <beschreibung> (closes #{number})
""")


def cmd_pr(number: int, branch: str) -> None:
    """
    Schritt 3: PR erstellen nach Implementierung.

    Args:
        number: Issue-Nummer
        branch: Feature-Branch der gemergt werden soll
    """
    issue = gitea.get_issue(number)
    title = f"{issue['title']} (closes #{number})"
    body  = f"""## Änderungen
Implementierung für Issue #{number}.

## Checkliste
- [ ] Code geändert
- [ ] Dokumentation aktualisiert
- [ ] Kein toter Code hinzugefügt
- [ ] Getestet (soweit möglich)

## Issue
{gitea.GITEA_URL}/{gitea.REPO}/issues/{number}
"""
    pr = gitea.create_pr(branch=branch, title=title, body=body)
    gitea.swap_label(number, LABEL_PROGRESS, LABEL_REVIEW)

    print(f"[✓] PR erstellt: {pr.get('html_url', '?')}")
    print(f"[→] Bitte reviewen und mergen.")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def cmd_auto(project_root: Path) -> None:
    """
    Standard-Modus (kein Argument): Scannt alle Workflow-States in Gitea
    und verarbeitet automatisch was möglich ist.

    Reihenfolge:
        1. agent-proposed + Freigabe vorhanden → implement
        2. ready-for-agent → Plan posten
        3. Sonst → Status-Übersicht

    Args:
        project_root: Wurzelverzeichnis des Projekts
    """
    print("=" * 70)
    print("  GITEA AGENT — AUTO-SCAN")
    print("=" * 70)

    # Schritt 1: Freigegebene Pläne implementieren
    proposed = gitea.get_issues(label=LABEL_PROPOSED)
    approved  = [i for i in proposed if gitea.check_approval(i["number"])]
    if approved:
        approved.sort(key=lambda x: risk_level(x)[0])
        issue = approved[0]
        print(f"\n[✓] Freigabe für Issue #{issue['number']}: {issue['title'][:55]}")
        cmd_implement(issue["number"], project_root)
        return

    # Schritt 2: Neue Issues planen
    ready = gitea.get_issues(label=LABEL_READY)
    if ready:
        ready.sort(key=lambda x: risk_level(x)[0])
        print(f"\n[→] {len(ready)} Issue(s) bereit — poste Pläne:\n")
        for issue in ready:
            stufe, _ = risk_level(issue)
            print(f"    #{issue['number']} (Stufe {stufe}) {issue['title'][:55]}")
            cmd_plan(issue["number"], project_root)
            print()
        print(f"[→] Issues in Gitea freigeben ('ok' kommentieren):")
        print(f"    {gitea.GITEA_URL}/{gitea.REPO}/issues")
        return

    # Schritt 3: Status-Übersicht
    in_progress = gitea.get_issues(label=LABEL_PROGRESS)
    waiting     = gitea.get_issues(label=LABEL_PROPOSED)

    if not any([in_progress, waiting]):
        print("\n[✓] Nichts zu tun — keine Issues mit Workflow-Labels.")
        print(f"    {gitea.GITEA_URL}/{gitea.REPO}/issues")
        return

    print("\n--- Status ---\n")
    if in_progress:
        print(f"In Arbeit ({len(in_progress)}):")
        for i in in_progress:
            print(f"  #{i['number']} {i['title'][:60]}")
    if waiting:
        print(f"\nWartet auf Freigabe ({len(waiting)}):")
        for i in waiting:
            flag = "✅ Freigabe vorhanden" if gitea.check_approval(i["number"]) else "⏳ Wartet auf 'ok'"
            print(f"  #{i['number']} {i['title'][:50]}  [{flag}]")


def main():
    parser = argparse.ArgumentParser(
        description="Gitea Agent — automatischer Issue-Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ohne Argumente: Auto-Modus — scannt Gitea und arbeitet selbständig.

Manuell:
  python3 agent_start.py --list               → Status-Übersicht
  python3 agent_start.py --issue 16           → Plan für Issue #16 posten
  python3 agent_start.py --implement 16       → Branch + Implementierungskontext
  python3 agent_start.py --pr 16 --branch fix/issue-16-xyz  → PR erstellen
        """
    )
    parser.add_argument("--list",      action="store_true",        help="Alle Workflow-Issues auflisten")
    parser.add_argument("--issue",     type=int,  metavar="NR",    help="Issue analysieren + Plan posten")
    parser.add_argument("--implement", type=int,  metavar="NR",    help="Nach OK: Branch erstellen + Kontext")
    parser.add_argument("--pr",        type=int,  metavar="NR",    help="PR erstellen (mit --branch)")
    parser.add_argument("--branch",    type=str,  metavar="BRANCH",help="Branch-Name für --pr")
    parser.add_argument("--root",      type=Path, metavar="DIR",   help="Projektverzeichnis (Standard: cwd)", default=Path.cwd())
    args = parser.parse_args()

    project_root = args.root.resolve()

    if args.list:
        cmd_list()
    elif args.issue:
        cmd_plan(args.issue, project_root)
    elif args.implement:
        cmd_implement(args.implement, project_root)
    elif args.pr:
        if not args.branch:
            print("[✗] --pr benötigt --branch <branch-name>")
            sys.exit(1)
        cmd_pr(args.pr, args.branch)
    else:
        cmd_auto(project_root)


if __name__ == "__main__":
    main()
