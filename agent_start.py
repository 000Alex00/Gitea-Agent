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
import time
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
    slug = slug.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    slug = re.sub(r"[^a-z0-9-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug[:35].strip("-")
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
    return settings.CONTEXT_DIR_PATH


def _issue_dir(issue: dict) -> Path:
    """Gibt den Issue-Unterordner zurück und erstellt ihn falls nötig.

    Format: contexts/open/{num}-{typ}/  z.B. contexts/open/32-feature_request/
    """
    d = _context_dir() / "open" / f"{issue['number']}-{issue_type(issue)}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _find_issue_dir(number: int) -> Path | None:
    """Findet den Issue-Ordner anhand der Nummer (Typ unbekannt → glob).

    Sucht zuerst in contexts/open/, dann direkt in contexts/ (Fallback für alte Struktur).
    """
    matches = list((_context_dir() / "open").glob(f"{number}-*"))
    if matches:
        return matches[0]
    # Fallback: alte Struktur ohne open/
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

    content = f"""{settings.STARTER_MD_PFLICHTREGELN}# Issue #{num} — {title}
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

    # Issue-Kommentare laden (ohne Bot-Kommentare)
    comments = gitea.get_comments(num)
    bot_user = getattr(settings, "GITEA_BOT_USER", None) or "working-bot"
    discussion_parts = []
    for c in comments:
        # Bot-Kommentare überspringen (nach Username, nicht Inhalt)
        if c.get("user", {}).get("login") == bot_user:
            continue
        c_body = c.get("body", "")
        user = c.get("user", {}).get("login", "?")
        text = c_body[:500] + ("..." if len(c_body) > 500 else "")
        discussion_parts.append(f"**{user}:** {text}")
    discussion = "\n\n".join(discussion_parts) if discussion_parts else "— keine —"

    ctx_content = f"""{settings.STARTER_MD_PFLICHTREGELN}# Issue #{num} — {title}
Status: 🔧 READY — Implementierung starten
Risiko: {stufe}/4 — {desc}
Branch: {branch}

## Ziel
{body_short}

## Diskussion
{discussion}

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
        size_kb = len(text.encode("utf-8")) / 1024
        if size_kb > _MAX_FILE_SIZE_KB:
            code = "\n".join(lines[:500])
            code += f"\n\n# [GEKÜRZT: {len(lines)} Zeilen, {size_kb:.0f}KB — nur erste 500 Zeilen]"
        elif len(lines) > limit:
            code = "\n".join(lines[:limit])
            code += f"\n\n[... gekürzt — {len(lines) - limit} Zeilen weggelassen ...]"
        else:
            code = "\n".join(lines)
        parts.append(f"## {name}\n```\n{code}\n```")

    idir       = _issue_dir(issue)
    ctx_file   = idir / "starter.md"
    files_file = idir / "files.md"

    ctx_file.write_text(ctx_content, encoding="utf-8")
    files_header = (
        f"# Dateien — Issue #{num}\n"
        f"> Automatisch erkannt via Backtick-Erwähnungen, Import-Analyse (AST) und Keyword-Suche (grep).\n"
        f"> Zusätzliche Suche im Repo ist nicht nötig — der Kontext ist vollständig.\n\n"
    )
    files_file.write_text(
        files_header + "\n\n".join(parts) + "\n",
        encoding="utf-8"
    )

    log.info(f"Kontext gespeichert: {ctx_file}, {files_file}")
    return ctx_file, files_file


# ---------------------------------------------------------------------------
# Kontext-Loader: Import-Analyse + Keyword-Suche
# ---------------------------------------------------------------------------

_EXCLUDE_DIRS_DEFAULT = {
    "node_modules", ".git", "__pycache__", "venv", ".venv",
    "Backup", "backup",
    "vendor", "llama-cpp-python-build",
    "agent", "contexts", ".claude",
    "Documentation",
    ".mypy_cache", ".pytest_cache",
    "dist", "build",
}


def _get_exclude_dirs(project: Path) -> set[str]:
    """
    Gibt die kombinierten Exclude-Verzeichnisse zurück.

    Lädt project/agent/config/agent_eval.json und liest context_loader.exclude_dirs
    falls vorhanden. Kombiniert mit _EXCLUDE_DIRS_DEFAULT.
    Bei Fehler: nur Default zurückgeben.

    Args:
        project: Projekt-Root-Pfad

    Returns:
        Set von Verzeichnisnamen die beim Keyword-Scan ignoriert werden.
    """
    try:
        cfg_path = Path(project) / "agent" / "config" / "agent_eval.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        extra = cfg.get("context_loader", {}).get("exclude_dirs", [])
        return _EXCLUDE_DIRS_DEFAULT | set(extra)
    except Exception:
        return _EXCLUDE_DIRS_DEFAULT

_KEYWORD_SEARCH_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".yaml", ".yml", ".json"}

_EXCLUDE_FILES = {
    # Lock-Dateien
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    # Laufzeit-Output
    "output.json",
    # Generierte Dateien (Glob-Muster)
    "*.min.js",
    "*.min.css",
    "*.map",
}

_MAX_FILE_SIZE_KB = 50


def _find_imports(files: list[Path], depth: int = 1) -> list[Path]:
    """
    Findet zusätzliche Dateien via AST-Import-Analyse der übergebenen Python-Dateien.

    Aufgerufen von:
        cmd_implement() — für files.md
        _build_analyse_comment() — für Gitea-Kommentar

    Args:
        files: Bereits erkannte relevante Dateipfade
        depth: Import-Tiefe (1 = nur direkte Imports der Ausgangsdateien)

    Returns:
        Liste zusätzlicher Dateipfade (existierend, nicht in files, dedupliziert).
    """
    found = []
    to_process = list(files)

    for _ in range(depth):
        next_level = []
        for f in to_process:
            if f.suffix != ".py":
                continue
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        parts = node.module.split(".")
                        candidate = PROJECT / Path(*parts).with_suffix(".py")
                        if candidate.exists() and candidate not in files and candidate not in found:
                            found.append(candidate)
                            next_level.append(candidate)
            except Exception:
                pass
        to_process = next_level

    return found


def _search_keywords(issue_text: str, repo_path: Path) -> list[Path]:
    """
    Findet Dateien via Keyword-Suche (grep) über den Issue-Text.

    Extrahiert Wörter aus Backtick-Spans im Issue-Text als Suchterme.
    Ignoriert Verzeichnisse aus _EXCLUDE_DIRS.

    Aufgerufen von:
        cmd_implement() — für files.md

    Args:
        issue_text: Issue-Body (Markdown)
        repo_path:  Wurzel des Repositories

    Returns:
        Liste gefundener Dateipfade (existierend, dedupliziert).
    """
    # Suchterme: Wörter aus Backtick-Spans (Funktions-/Klassennamen, etc.)
    terms = re.findall(r"`([^`]+)`", issue_text)
    keywords = []
    for term in terms:
        # Nur alphanumerische Terme ≥ 4 Zeichen — vermeidet false positives bei Kurzwörtern
        for word in re.split(r"[^a-zA-Z0-9_]", term):
            if len(word) >= 4 and word not in keywords:
                keywords.append(word)

    if not keywords:
        return []

    found = []

    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in _KEYWORD_SEARCH_EXTENSIONS:
            continue
        if any(ex in path.parts for ex in _get_exclude_dirs(repo_path)):
            continue
        if path.name in _EXCLUDE_FILES or any(
            path.name.endswith(p.replace("*", "")) for p in _EXCLUDE_FILES if "*" in p
        ):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            if any(kw in content for kw in keywords):
                if path not in found:
                    found.append(path)
        except Exception:
            pass

    return found


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
    extra_files = _find_imports(files)

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


# ---------------------------------------------------------------------------
# Prozess-Enforcement (Issue #6)
# ---------------------------------------------------------------------------

def _check_pr_preconditions(number: int, branch: str) -> None:
    """
    Maßnahme 1 (höchste Priorität): Technische Schranke vor cmd_pr().

    Technische Schranken haben Vorrang vor Prompt-Regeln — diese Prüfung
    kann nicht durch LLM-Kontext-Drift umgangen werden.

    Prüfungen (in Reihenfolge):
        1. Branch ist nicht main/master
        2. Plan-Kommentar existiert im Issue (enthält "Implementierungsplan" oder "Agent-Analyse")
        3. Metadata-Block im Plan-Kommentar vorhanden (enthält "Agent-Metadaten")
        4. Eval nach letztem Commit ausgeführt (score_history.json Timestamp > letzter Commit)

    Args:
        number: Issue-Nummer
        branch: Feature-Branch-Name

    Raises:
        SystemExit(1) wenn eine Prüfung fehlschlägt.
    """
    fehler = []

    # 1. Branch ≠ main/master
    if branch.strip().lower() in ("main", "master"):
        fehler.append("Branch ist 'main'/'master' — PR von main verboten")

    # 2. Plan-Kommentar existiert
    try:
        comments = gitea.get_comments(number)
        plan_kommentar = any(
            ("Implementierungsplan" in c.get("body", "") or "Agent-Analyse" in c.get("body", ""))
            for c in comments
        )
        if not plan_kommentar:
            fehler.append("Kein Plan-Kommentar im Issue gefunden (cmd_plan ausgeführt?)")
        else:
            # 3. Metadata-Block im Plan-Kommentar
            meta_vorhanden = any(
                "Agent-Metadaten" in c.get("body", "")
                for c in comments
                if "Implementierungsplan" in c.get("body", "") or "Agent-Analyse" in c.get("body", "")
            )
            if not meta_vorhanden:
                fehler.append("Plan-Kommentar ohne Metadata-Block (cmd_plan neu ausführen)")
    except Exception as e:
        log.warning(f"Kommentar-Prüfung fehlgeschlagen: {e}")

    # 4. Eval nach letztem Commit — nur wenn agent_eval.json existiert
    eval_cfg  = evaluation._resolve_config(PROJECT)
    hist_path = evaluation._resolve_path(PROJECT, "score_history.json", evaluation.SCORE_HISTORY)
    if eval_cfg.exists():
        if hist_path.exists():
            try:
                with hist_path.open(encoding="utf-8") as f:
                    history = json.load(f)
                if history:
                    last_eval_ts = history[-1].get("timestamp", "")
                    last_commit_ts = subprocess.check_output(
                        ["git", "log", "-1", "--pretty=%cI"],
                        cwd=PROJECT, stderr=subprocess.DEVNULL
                    ).decode().strip()
                    if last_eval_ts < last_commit_ts:
                        fehler.append(
                            f"Eval nicht nach letztem Commit ausgeführt "
                            f"(letzter Eval: {last_eval_ts[:16]}, letzter Commit: {last_commit_ts[:16]})"
                        )
                else:
                    fehler.append("score_history.json leer — Eval noch nie ausgeführt")
            except Exception as e:
                log.warning(f"score_history Prüfung fehlgeschlagen: {e}")
        else:
            fehler.append("score_history.json nicht gefunden — Eval noch nie ausgeführt")
    else:
        log.debug("Kein agent_eval.json — Eval-Prüfung übersprungen")

    if fehler:
        print("\n❌ cmd_pr abgebrochen — Prozess nicht vollständig:")
        for f in fehler:
            print(f"   • {f}")
        print("\n→ Fehlende Schritte nachholen, dann erneut ausführen.")
        sys.exit(1)


def _validate_pr_completion(number: int, branch: str, pr_url: str, idir_moved: bool) -> None:
    """
    Maßnahme 4: Validiert nach cmd_pr() ob alle Pflichtschritte erfolgt sind.

    Prüft:
        - PR-URL vorhanden (nicht "?")
        - Label 'needs-review' gesetzt
        - Context-Ordner verschoben

    Bei fehlenden Schritten: Terminal-Warnung + Gitea-Kommentar.

    Args:
        number:     Issue-Nummer
        branch:     Feature-Branch
        pr_url:     URL des erstellten PR
        idir_moved: True wenn Context-Ordner erfolgreich verschoben wurde
    """
    fehlend = []

    if pr_url == "?":
        fehlend.append("PR-URL fehlt — PR möglicherweise nicht erstellt")

    try:
        issue = gitea.get_issue(number)
        label_names = [l["name"] for l in issue.get("labels", [])]
        if settings.LABEL_REVIEW not in label_names:
            fehlend.append(f"Label '{settings.LABEL_REVIEW}' nicht gesetzt")
    except Exception as e:
        log.warning(f"Label-Prüfung fehlgeschlagen: {e}")

    if not idir_moved:
        fehlend.append("Context-Ordner nicht verschoben (contexts/ → contexts/done/)")

    if fehlend:
        warnung = "⚠️ **Prozess unvollständig** — folgende Schritte fehlen:\n" + \
                  "\n".join(f"- {s}" for s in fehlend)
        print(f"\n[!] {warnung.replace('**', '')}")
        try:
            gitea.post_comment(number, warnung)
        except Exception as e:
            log.warning(f"Abschluss-Validierung Kommentar fehlgeschlagen: {e}")


def _validate_comment(body: str, comment_type: str, *, critical: bool = False) -> None:
    """
    Prüft ob ein Kommentar alle Pflichtfelder enthält (Output-Validierung, Issue #8).

    Aufgerufen von:
        cmd_plan(), cmd_pr() nach jedem post_comment()

    Args:
        body:         Kommentar-Body der geprüft werden soll
        comment_type: Typ aus settings.COMMENT_REQUIRED_FIELDS (z.B. "plan", "completion")
        critical:     True → sys.exit(1) bei fehlenden Feldern, False → Warnung + weiter
    """
    required = settings.COMMENT_REQUIRED_FIELDS.get(comment_type, [])
    missing  = [f for f in required if f.lower() not in body.lower()]
    if not missing:
        return
    msg = f"[!] Kommentar-Validierung '{comment_type}': fehlende Felder: {', '.join(missing)}"
    log.warning(msg)
    print(msg)
    if critical:
        print("→ Kommentar unvollständig — Prozess abgebrochen. Bitte erneut ausführen.")
        sys.exit(1)


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
    plan_body = build_plan_comment(issue) + metadata
    comment   = gitea.post_comment(number, plan_body)
    _validate_comment(comment.get("body", ""), "plan")
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

    # Maßnahme 5: Vorbedingungen prüfen
    stufe, _ = risk_level(issue)
    if stufe >= 4:
        print(f"[✗] Issue #{number} hat Risikostufe 4 — kein automatischer Implement-Start.")
        print(f"    Bitte manuell implementieren und mit --pr abschließen.")
        sys.exit(1)

    idir_existing = _find_issue_dir(number)
    if not idir_existing:
        print(f"[✗] Kein Kontext-Ordner für Issue #{number} gefunden.")
        print(f"    Zuerst ausführen: python3 agent_start.py --issue {number}")
        sys.exit(1)

    starter = idir_existing / "starter.md"
    if not starter.exists():
        print(f"[✗] starter.md nicht gefunden in {idir_existing}.")
        print(f"    Zuerst ausführen: python3 agent_start.py --issue {number}")
        sys.exit(1)

    if "PFLICHTREGELN" not in starter.read_text(encoding="utf-8"):
        print(f"[!] Warnung: starter.md enthält keinen PFLICHTREGELN-Block.")
        print(f"    Bitte --issue {number} erneut ausführen um aktuellen Kontext zu laden.")

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

    base_files   = relevant_files(issue)
    import_files = _find_imports(base_files)
    kw_files     = _search_keywords(issue.get("body", "") or "", PROJECT)

    all_files = list(dict.fromkeys(base_files + import_files + kw_files))
    files_dict = {
        str(f.relative_to(PROJECT)): f.read_text(encoding="utf-8")
        for f in all_files
    }
    ctx_file, files_file = save_implement_context(issue, files_dict)
    _idir2 = _find_issue_dir(num)
    print(f"[✓] Kontext: {_idir2.name if _idir2 else ''}/starter.md + files.md — bereit zur Implementierung")


_RESTART_PATTERNS = ("server.py", "bot.js", "nanoclaw/", "whatsapp-bot/", "router.py", "analyst_worker.py")


def _neustart_required(changed_files: list[str]) -> str:
    """Gibt 'Ja' zurück wenn server-seitige Dateien geändert wurden, sonst 'Nein'."""
    for f in changed_files:
        if any(pat in f for pat in _RESTART_PATTERNS):
            return "Ja"
    return "Nein"


def cmd_pr(number: int, branch: str, summary: str = "",
           force: bool = False, restart_before_eval: bool = False) -> None:
    """
    Schritt 3: PR erstellen + Abschluss-Kommentar ins Issue posten.

    Args:
        number:               Issue-Nummer
        branch:               Feature-Branch
        summary:              Optionale Zusammenfassung was gemacht wurde
        force:                Staleness-Check überspringen (--force)
        restart_before_eval:  Server neu starten vor Eval (--restart-before-eval)
    """
    # Maßnahme 1: Vorbedingungen prüfen (blockiert bei Prozess-Verletzung)
    _check_pr_preconditions(number, branch)

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
    changed = []
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

    # Server-Aktualitäts-Check: Commit neuer als Server-Start? (Issue #30)
    if restart_before_eval:
        _restart_server_for_eval()
    else:
        _check_server_staleness(branch, force=force)

    # Eval ausführen — blockiert PR bei FAIL
    # Risikostufe 1: Eval überspringen (kein Risk-Gate nötig)
    stufe, _ = risk_level(issue)
    eval_result = None
    if stufe <= 1:
        print("[Eval] Risikostufe 1 — übersprungen.")
        log.info("Eval übersprungen — Risikostufe 1")
    else:
        try:
            eval_result = evaluation.run(PROJECT, trigger="pr")
            print(evaluation.format_terminal(eval_result))
            if eval_result.skipped:
                log.info("Eval übersprungen (kein agent_eval.json)")
            elif eval_result.warned and not eval_result.all_tests:
                log.warning("Eval: Infrastruktur offline — PR wird trotzdem erstellt")
            elif not eval_result.passed:
                eval_comment = evaluation.format_gitea_comment(eval_result)
                gitea.post_comment(number, eval_comment)
                _validate_comment(eval_comment, "eval_fail", critical=True)
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

    # Eval-Ergebnis für Abschluss-Kommentar
    # "Score:" muss im Text enthalten sein (COMMENT_REQUIRED_FIELDS["completion"])
    if eval_result is None:
        eval_line = "⏭️ Eval: übersprungen (Risikostufe 1) — Score: n/a"
    elif eval_result.skipped:
        eval_line = "⏭️ Eval: übersprungen (kein agent_eval.json) — Score: n/a"
    elif eval_result.passed:
        eval_line = f"✅ Eval PASS — Score: {eval_result.score}/{eval_result.max_score} (Baseline: {eval_result.baseline_score})"
    else:
        eval_line = f"⚠️ Eval WARN — Score: {eval_result.score}/{eval_result.max_score} (Baseline: {eval_result.baseline_score})"

    # Session-Status (Änderung 3)
    try:
        session_data = _session_increment()
        session_line = _session_status_line(session_data)
    except Exception as e:
        log.warning(f"Session-Tracking fehlgeschlagen: {e}")
        session_line = "⚪ Session: unbekannt"

    # Metadata-Block (Änderung 2)
    metadata = _build_metadata(branch=branch)

    abschluss = (
        f"## Implementierung abgeschlossen\n\n"
        f"{eval_line}\n\n"
        f"{session_line}\n\n"
        f"**Branch:** `{branch}`\n"
        f"**PR:** {pr_url}\n"
        f"{docs_warning}\n\n"
        f"{summary_block}\n\n"
        f"{history_block}\n\n"
        f"**Neustart erforderlich:** {_neustart_required(changed)}\n\n"
        f"**Nächster Schritt:** {settings.COMPLETION_NEXT_STEP}\n"
        f"- Bei Revert: `Documentation/` synchron zurücksetzen"
        f"{metadata}"
    )
    comment = gitea.post_comment(number, abschluss)
    _validate_comment(comment.get("body", ""), "completion", critical=True)

    idir = _find_issue_dir(number)
    idir_moved = False
    if idir and idir.exists():
        shutil.move(str(idir), str(_done_dir() / idir.name))
        idir_moved = True

    log.info(f"PR erstellt: {pr_url}")
    print(f"[✓] PR erstellt: {pr_url}")
    print(f"[✓] Kommentar in Issue #{number} gepostet.")

    # Maßnahme 4: Abschluss-Validierung
    _validate_pr_completion(number, branch, pr_url, idir_moved)


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
        f"{_build_metadata()}"
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


def _build_metadata(
    branch: str = "",
    changed_paths: list[str] | None = None,
    files_read: list[Path] | None = None,
) -> str:
    """
    Erzeugt einen aufklappbaren Metadata-Block für Gitea-Kommentare.

    Inhalt: Modell, Dateien gelesen, Token-Schätzung, Branch, Commit, Zeitstempel.

    Args:
        branch:        Git-Branch-Name (leer = aktueller Branch via git)
        changed_paths: Liste geänderter Dateipfade (optional, für Abschluss-Kommentar)
        files_read:    Liste gelesener Path-Objekte für Token-Schätzung (optional)

    Returns:
        Markdown-String mit <details>-Block für Gitea-Kommentar
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    model = os.environ.get("CLAUDE_MODEL", os.environ.get("MODEL", settings.CLAUDE_MODEL))
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT, stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        commit = "unbekannt"
    if not branch:
        try:
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=PROJECT, stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            branch = "unbekannt"

    # Token-Schätzung (~10 Tokens/Wort)
    file_count = len(files_read) if files_read else 0
    if files_read:
        words = 0
        for f in files_read:
            try:
                words += len(f.read_text(encoding="utf-8", errors="ignore").split())
            except Exception:
                pass
        estimated_tokens = words * 10
        token_line = f"**Geschätzte Tokens:** ~{estimated_tokens:,} _(Schätzung: ~10 Tokens/Wort, kein offizielles Token-API)_"
    else:
        token_line = "**Geschätzte Tokens:** — _(keine Dateien übergeben)_"

    files_changed_line = ""
    if changed_paths:
        files_changed_line = f"\n**Geänderte Dateien:** " + ", ".join(f"`{p}`" for p in changed_paths)

    return (
        f"\n\n<details>\n<summary>🤖 Agent-Metadaten</summary>\n\n"
        f"**Modell:** {model}  \n"
        f"**Dateien gelesen:** {file_count}  \n"
        f"{token_line}  \n"
        f"\n"
        f"**Branch:** `{branch}`  \n"
        f"**Commit:** `{commit}`  \n"
        f"**Zeitstempel:** {timestamp}  \n"
        f"{files_changed_line}\n"
        f"\n</details>"
    )


def _session_path() -> Path:
    """Gibt den Pfad zur session.json zurück (neu: agent/data/, Fallback: contexts/)."""
    return settings.SESSION_FILE_PATH


def _session_load() -> dict:
    """
    Liest session.json. Erstellt neu wenn fehlend oder nach SESSION_RESET_HOURS inaktiv.

    Returns:
        dict mit keys: started, issues_completed, last_activity
    """
    path = _session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            last = datetime.datetime.fromisoformat(data.get("last_activity", ""))
            if (now - last).total_seconds() / 3600 < settings.SESSION_RESET_HOURS:
                return data
        except Exception:
            pass
    data = {"started": now.isoformat(), "issues_completed": 0, "last_activity": now.isoformat()}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def _session_increment() -> dict:
    """Erhöht issues_completed um 1 und aktualisiert last_activity."""
    data = _session_load()
    data["issues_completed"] = data.get("issues_completed", 0) + 1
    data["last_activity"] = datetime.datetime.now().isoformat()
    path = _session_path()
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        log.warning(f"session.json schreiben fehlgeschlagen: {e}")
    return data


def _session_status_line(data: dict) -> str:
    """
    Gibt eine Statuszeile mit Ampel-Emoji zurück basierend auf issues_completed.

    🟢 = unter Limit | 🟡 = am Limit | 🔴 = über Limit
    """
    count = data.get("issues_completed", 0)
    limit = settings.SESSION_LIMIT
    if count < limit:
        return f"🟢 Session: Issue {count}/{limit} — OK"
    elif count == limit:
        return f"🟡 Session: Issue {count}/{limit} — Neue Session empfohlen"
    else:
        return f"🔴 Session: Issue {count}/{limit} — Kontext-Drift Risiko hoch"


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
    hist_path = evaluation._resolve_path(project_root, "score_history.json", evaluation.SCORE_HISTORY)
    if not hist_path.exists():
        return "**Verlauf:** keine Einträge"
    try:
        with hist_path.open(encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return "**Verlauf:** keine Einträge"
    if not history:
        return "**Verlauf:** keine Einträge"

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


def _last_chat_inactive_minutes(log_path: str | Path) -> float | None:
    """
    Liest log_path rückwärts und gibt Minuten seit letzter Nicht-Eval-Aktivität zurück.

    Sucht nach Zeilen mit Zeitstempel-Muster (ISO8601 oder HH:MM), überspringt
    Eval-Marker ("EVAL", "eval", "score_history"). Gibt None zurück wenn log_path
    nicht existiert oder kein passender Eintrag gefunden wird.

    Aufgerufen von:
        cmd_watch() — Szenario 2
    """
    log_path = Path(log_path)
    if not log_path.exists():
        return None

    import re
    ts_pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2})"   # ISO: 2026-03-20T14:32 oder mit Leerzeichen
        r"|(\d{2}:\d{2}:\d{2})"                   # HH:MM:SS
    )
    eval_markers = ("EVAL", "eval", "score_history", "agent_eval", "trigger")

    try:
        lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return None

    for line in reversed(lines):
        if any(m in line for m in eval_markers):
            continue
        m = ts_pattern.search(line)
        if not m:
            continue
        raw = m.group(1) or m.group(2)
        try:
            if len(raw) > 8:  # ISO-Format
                dt = datetime.datetime.fromisoformat(raw.replace("T", " "))
            else:  # HH:MM:SS — heutiges Datum annehmen
                today = datetime.date.today()
                h, mi, s = raw.split(":")
                dt = datetime.datetime(today.year, today.month, today.day, int(h), int(mi), int(s))
            delta = datetime.datetime.now() - dt
            return delta.total_seconds() / 60
        except Exception:
            continue
    return None


def _server_start_time(log_path: str | Path) -> datetime.datetime | None:
    """
    Ermittelt den letzten Server-Start-Zeitpunkt anhand des log_path.

    Sucht rückwärts nach typischen Startup-Mustern (uvicorn, FastAPI, custom).
    Extrahiert den ISO-Timestamp aus der gefundenen Zeile.

    Aufgerufen von:
        _check_server_staleness()

    Args:
        log_path: Pfad zur Logdatei des Servers (aus agent_eval.json)

    Returns:
        datetime ohne Zeitzone oder None wenn nicht ermittelbar.
    """
    _STARTUP_PATTERNS = (
        "application startup complete",
        "uvicorn running on",
        "started server process",
        "started reloader process",
        "server started",
        "starting server",
        "skynet online",
        "started listening",
    )

    log_path = Path(log_path)
    if not log_path.exists():
        return None

    import re
    ts_re = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")

    try:
        lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return None

    for line in reversed(lines):
        if any(p in line.lower() for p in _STARTUP_PATTERNS):
            m = ts_re.search(line)
            if m:
                try:
                    return datetime.datetime.fromisoformat(m.group().replace("T", " "))
                except Exception:
                    pass
    return None


def _check_server_staleness(branch: str, force: bool = False) -> None:
    """
    Prüft ob der laufende Server den aktuellen Branch-Code hat.

    Vergleicht Timestamp des letzten Commits auf branch mit dem Server-Start-Zeitpunkt
    (aus log_path in agent_eval.json). Bei Commit neuer als Server-Start:
    Warnung + SystemExit(1) — außer force=True.

    Wird übersprungen wenn log_path nicht konfiguriert oder Server-Start nicht parsebar.

    Aufgerufen von:
        cmd_pr() — vor Eval

    Args:
        branch: Feature-Branch-Name
        force:  True → Warnung ausgeben aber nicht abbrechen (--force)
    """
    eval_cfg = evaluation._load_config(PROJECT) or {}
    log_path = eval_cfg.get("log_path")
    if not log_path:
        return  # Nicht konfiguriert → überspringen

    server_start = _server_start_time(log_path)
    if server_start is None:
        log.info("Server-Start-Zeitpunkt nicht ermittelbar — Staleness-Check übersprungen")
        return

    try:
        commit_ts_raw = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%cI", branch],
            cwd=PROJECT, stderr=subprocess.DEVNULL
        ).decode().strip()
        # Zeitzone entfernen für Vergleich
        commit_ts = datetime.datetime.fromisoformat(commit_ts_raw)
        if commit_ts.tzinfo:
            import datetime as _dt
            commit_ts = commit_ts.replace(tzinfo=None) + commit_ts.utcoffset()
            commit_ts = commit_ts.replace(tzinfo=None)
    except Exception as e:
        log.info(f"Commit-Timestamp nicht ermittelbar — Staleness-Check übersprungen ({e})")
        return

    if commit_ts <= server_start:
        return  # Server ist aktuell

    msg = (
        f"\n[!] Server-Code veraltet\n"
        f"    Letzter Commit: {commit_ts.strftime('%Y-%m-%d %H:%M')} ({branch[:60]})\n"
        f"    Server gestartet: {server_start.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"    → Server neu starten, dann erneut --pr aufrufen.\n"
        f"      Oder: --restart-before-eval (automatisch) / --force (überspringen)"
    )
    print(msg)
    log.warning(f"Server-Code veraltet: commit {commit_ts} > server_start {server_start}")
    if not force:
        sys.exit(1)
    print("[!] --force: Staleness-Check übersprungen — Eval läuft trotzdem.")


def _restart_server_for_eval() -> None:
    """
    Startet den Server neu (via restart_script aus agent_eval.json) und wartet bis bereit.

    Aufgerufen von:
        cmd_pr() — bei --restart-before-eval

    Seiteneffekte:
        subprocess.run(restart_script), _wait_for_server()
    """
    eval_cfg = evaluation._load_config(PROJECT) or {}
    restart_sc = eval_cfg.get("restart_script")
    if not restart_sc:
        print("[!] --restart-before-eval: kein restart_script in agent_eval.json konfiguriert")
        log.warning("--restart-before-eval: restart_script fehlt in agent_eval.json")
        return
    print(f"[→] --restart-before-eval: Neustart via {restart_sc}...")
    log.info(f"Neustart via {restart_sc}")
    subprocess.run([restart_sc], check=False)
    server_url = eval_cfg.get("server_url", settings.SERVER_URL)
    _wait_for_server(url=server_url)


def _has_new_commits_since_last_eval(project_root: Path) -> bool:
    """
    Gibt True zurück wenn seit dem letzten Eval-Lauf neue Commits existieren.

    Liest den Timestamp des letzten Eintrags aus score_history.json und prüft
    via git log --after ob neue Commits vorhanden sind.

    Aufgerufen von:
        cmd_watch() — Szenario 2
    """
    hist_path = project_root / "tests" / "score_history.json"
    if not hist_path.exists():
        return False
    try:
        history = json.loads(hist_path.read_text(encoding="utf-8"))
        if not history:
            return False
        last_ts = history[-1].get("timestamp", "")
        if not last_ts:
            return False
        out = subprocess.check_output(
            ["git", "log", "--oneline", f"--after={last_ts}"],
            cwd=project_root, stderr=subprocess.DEVNULL
        ).decode().strip()
        return bool(out)
    except Exception:
        return False


def _wait_for_server(url: str | None = None, timeout_sec: int | None = None,
                     interval_sec: int | None = None) -> bool:
    """
    Pollt url bis der Server antwortet oder timeout_sec abgelaufen ist.

    Werte kommen aus settings wenn nicht explizit übergeben.

    Aufgerufen von:
        cmd_eval_after_restart()

    Args:
        url:          Server-URL (Standard: settings.SERVER_URL)
        timeout_sec:  Maximale Wartezeit in Sekunden (Standard: settings.SERVER_WAIT_TIMEOUT)
        interval_sec: Polling-Intervall in Sekunden (Standard: settings.SERVER_WAIT_INTERVAL)

    Returns:
        True wenn Server erreichbar, False bei Timeout.
    """
    import time
    import urllib.request
    import urllib.error

    url          = url          or settings.SERVER_URL
    timeout_sec  = timeout_sec  if timeout_sec  is not None else settings.SERVER_WAIT_TIMEOUT
    interval_sec = interval_sec if interval_sec is not None else settings.SERVER_WAIT_INTERVAL

    elapsed = 0
    while elapsed < timeout_sec:
        try:
            urllib.request.urlopen(url, timeout=5)
            return True
        except urllib.error.HTTPError:
            return True  # Server antwortet mit HTTP-Fehler → trotzdem erreichbar
        except Exception:
            pass
        time.sleep(interval_sec)
        elapsed += interval_sec
        print(f"  [{elapsed}s] Server noch nicht bereit...")
    return False


def cmd_eval_after_restart(number: int | None = None) -> None:
    """
    Führt Eval nach einem Server-Neustart aus und postet das Ergebnis ins Issue.

    Ablauf:
        1. _wait_for_server() — Polling bis Server bereit (settings.SERVER_WAIT_TIMEOUT)
        2. evaluation.run(PROJECT, trigger="restart")
        3. Falls number gesetzt: Kommentar mit Score ins Gitea-Issue posten

    Szenario 1 (manuell, --eval-after-restart <NR>):
        Nach manuellem Neustart des Servers — Score ins Issue posten.
    Szenario 2 (ohne NR, --eval-after-restart):
        Automatisch nach Neustart — nur Eval, kein Issue-Kommentar.

    Aufgerufen von:
        main() wenn --eval-after-restart gesetzt
    """
    import importlib.util

    print(f"[eval-after-restart] Warte auf Server ({settings.SERVER_URL}, max {settings.SERVER_WAIT_TIMEOUT}s)...")
    if not _wait_for_server():
        print(f"[eval-after-restart] ❌ Timeout — Server nicht erreichbar nach {settings.SERVER_WAIT_TIMEOUT}s.")
        sys.exit(1)
    print("[eval-after-restart] ✅ Server bereit — starte Eval...")

    eval_path = _HERE / "evaluation.py"
    if not eval_path.exists():
        print("[eval-after-restart] evaluation.py nicht gefunden — abgebrochen.")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("evaluation", eval_path)
    ev   = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)

    result = ev.run(PROJECT, trigger="restart")
    print(ev.format_terminal(result))

    if number:
        status        = "✅ PASS" if result.passed else "❌ FAIL"
        history_block = _format_history_block(PROJECT)
        body          = (
            f"## 🔄 Eval nach Neustart — {status}\n\n"
            f"**Score:** {result.score:.0f}/{result.max_score} "
            f"(Baseline: {result.baseline_score:.0f})\n"
        )
        if result.failed_tests:
            body += "\n**Fehlgeschlagene Tests:**\n"
            for t in result.failed_tests:
                body += f"- {t.name}: {t.reason}\n"
        if result.warn_reasons:
            body += "\n**Warnungen:**\n"
            for w in result.warn_reasons:
                body += f"- {w}\n"
        body += f"\n{history_block}"
        gitea.post_comment(number, body)
        log.info(f"[eval-after-restart] Kommentar gepostet → Issue #{number}")
        print(f"[eval-after-restart] Kommentar gepostet → Issue #{number}")


def _build_auto_issue_body(
    failed: "evaluation.TestResult",
    result: "evaluation.EvalResult",
    commit: str,
    history_block: str,
) -> str:
    """
    Erstellt den strukturierten Body für ein Auto-Issue aus dem Watch-Modus.

    Enthält:
    - Erwartung vs. Realität (Tabelle für einfache Tests)
    - Step-Tabelle für steps-Tests (alle Steps mit Status)
    - Fehler-Kategorie (regelbasiert, kein LLM)
    - Letzte 3 Scores aus History

    Args:
        failed:        TestResult des fehlgeschlagenen Tests
        result:        Gesamtergebnis des Eval-Laufs
        commit:        Letzter Commit-Hash + Subject
        history_block: Formatierter Verlaufs-Block (_format_history_block)

    Returns:
        Markdown-String für Gitea Issue Body
    """
    lines = [
        f"## [Auto] {failed.name} fehlgeschlagen",
        "",
        f"**Test:** {failed.name} (Gewicht {failed.weight})",
        f"**Score:** {result.score:.0f}/{result.max_score} (Baseline: {result.baseline_score:.0f})",
        f"**Letzter Commit:** `{commit}`",
        "",
    ]

    # Step-Details (multi-step Tests)
    if failed.step_details:
        total = len(failed.step_details)
        failed_step_idx = next(
            (i + 1 for i, s in enumerate(failed.step_details) if not s.get("passed")), total
        )
        lines.append(f"**Step {failed_step_idx}/{total} fehlgeschlagen**")
        lines.append("")
        lines.append("| Schritt | Nachricht | Erwartet | Ergebnis |")
        lines.append("|---------|-----------|----------|----------|")
        for i, s in enumerate(failed.step_details, start=1):
            msg      = s.get("msg", "")[:60]
            stored   = s.get("stored", False)
            expected = ", ".join(s.get("expected", [])) if s.get("expected") else "(gespeichert)"
            actual   = s.get("actual") or "—"
            actual   = str(actual)[:80]
            icon     = "✅" if s.get("passed") else "❌"
            if stored:
                lines.append(f"| {i} | `{msg}` | (gespeichert) | {icon} OK |")
            else:
                lines.append(f"| {i} | `{msg}` | `{expected}` | {icon} `{actual}` |")
        lines.append("")
    else:
        # Einfacher Test: Erwartung vs. Realität
        lines.append("| Erwartet | Ergebnis |")
        lines.append("|----------|----------|")
        actual = failed.actual_response[:100] if failed.actual_response else "—"
        lines.append(f"| `{failed.reason}` | `{actual}` |")
        lines.append("")

    # Fehler-Kategorie
    if failed.category:
        lines.append(f"**Kategorie:** `{failed.category}`")
        lines.append("")

    # Letzte 3 Scores (kompakter als der 5er-Block)
    hist_path = evaluation._resolve_path(PROJECT, "score_history.json", evaluation.SCORE_HISTORY)
    if hist_path.exists():
        try:
            with hist_path.open(encoding="utf-8") as f:
                hist = json.load(f)
            recent3 = hist[-3:][::-1]
            lines.append("**Letzte 3 Scores:**")
            lines.append("```")
            for e in recent3:
                ts      = e.get("timestamp", "?")[:16].replace("T", " ")
                score   = int(e.get("score", 0))
                max_s   = int(e.get("max_score", 0))
                trigger = e.get("trigger", "?")
                passed  = "✓" if e.get("passed") else "✗"
                lines.append(f"{ts} | {score}/{max_s} | {trigger:<6} | {passed}")
            lines.append("```")
            lines.append("")
        except Exception:
            pass

    lines.append("> Automatisch erkannt durch Watch-Modus.")
    lines.append("> Wird automatisch geschlossen wenn der Test wieder besteht.")
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

                    body = _build_auto_issue_body(failed, result, commit, "")
                    _validate_comment(body, "auto_issue")
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

        # Optionaler Log-Analyzer: neue Struktur (agent/config/) oder Legacy (tools/)
        analyzer_path = (
            settings.LOG_ANALYZER_PATH
            if settings.LOG_ANALYZER_PATH and settings.LOG_ANALYZER_PATH.exists()
            else PROJECT / "tools" / "log_analyzer.py"
        )
        if analyzer_path.exists():
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("log_analyzer", analyzer_path)
                la   = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(la)
                la_result = la.run()
                print(la.format_terminal(la_result))
            except Exception as e:
                log.warning(f"Log-Analyzer Fehler: {e}")
                print(f"[!] Log-Analyzer Fehler: {e}")

        # Szenario 2: Automatischer Neustart bei Chat-Inaktivität + neuen Commits
        eval_cfg   = evaluation._load_config(PROJECT) or {}
        restart_sc = eval_cfg.get("restart_script")
        log_path   = eval_cfg.get("log_path")
        threshold  = eval_cfg.get("inactivity_minutes", 5)
        if restart_sc and log_path:
            inactive = _last_chat_inactive_minutes(log_path)
            if inactive is not None and inactive >= threshold:
                if _has_new_commits_since_last_eval(PROJECT):
                    print(f"[Watch] Chat inaktiv {inactive:.1f}min + neue Commits → Neustart")
                    log.info(f"Szenario 2: Neustart via {restart_sc}")
                    subprocess.run([restart_sc], check=False)
                    cmd_eval_after_restart()

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
    log_setup(log_file=str(settings.LOG_FILE_PATH), level=settings.LOG_LEVEL)
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
    parser.add_argument("--watch",              action="store_true",       help="Periodischer Eval-Loop mit Auto-Issues")
    parser.add_argument("--interval",           type=int,  metavar="MIN", help="Interval für --watch in Minuten (überschreibt watch_interval_minutes aus agent_eval.json)", default=None)
    parser.add_argument("--eval-after-restart",   type=int,  metavar="NR",  help="Nach Neustart: Eval ausführen + Score ins Issue (NR optional)", nargs="?", const=0)
    parser.add_argument("--force",                action="store_true",       help="Staleness-Check vor Eval überspringen (--pr)")
    parser.add_argument("--restart-before-eval",  action="store_true",       help="Server via restart_script neu starten vor Eval (--pr)")
    args = parser.parse_args()

    if args.eval_after_restart is not None:
        nr = args.eval_after_restart if args.eval_after_restart != 0 else None
        cmd_eval_after_restart(nr)
    elif args.list:
        cmd_list()
    elif args.issue:
        cmd_plan(args.issue)
    elif args.implement:
        cmd_implement(args.implement)
    elif args.fixup:
        cmd_fixup(args.fixup)
    elif args.watch:
        # Interval: CLI-Arg > agent_eval.json > Fallback 60
        interval = args.interval
        if interval is None:
            try:
                cfg_path = PROJECT / "tests" / "agent_eval.json"
                with cfg_path.open(encoding="utf-8") as f:
                    cfg = json.load(f)
                interval = cfg.get("watch_interval_minutes", 60)
            except Exception:
                interval = 60
        cmd_watch(interval)
    elif args.pr:
        if not args.branch:
            log.error("--pr benötigt --branch <branch-name>")
            print("[✗] --pr benötigt --branch <branch-name>")
            sys.exit(1)
        cmd_pr(args.pr, args.branch, args.summary,
               force=args.force,
               restart_before_eval=args.restart_before_eval)
    else:
        cmd_auto()


if __name__ == "__main__":
    main()
