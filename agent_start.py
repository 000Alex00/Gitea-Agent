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

# --self: .env.agent statt .env laden (vor allen anderen Imports)
if "--self" in sys.argv:
    _agent_env = _HERE / ".env.agent"
    if _agent_env.exists():
        for _line in _agent_env.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())
        os.environ["AGENT_ENV_FILE"] = str(_agent_env)

sys.path.insert(0, str(_HERE))
import evaluation
import dashboard
import gitea_api as gitea
import settings
from log import get_logger
from plugins.patch import (
    _SR_SEARCH, _SR_SEP, _SR_REPLACE,
    _normalize_ws, _parse_search_replace, _apply_patch, cmd_apply_patch,
)
from plugins.changelog import (
    _COMMIT_GROUPS, _GROUP_ORDER,
    _git_log_since_tag, _classify_commit, _build_changelog_block, cmd_changelog,
)

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
        log.warning(
            f"PROJECT_ROOT '{settings.PROJECT_ROOT}' existiert nicht — verwende Standard"
        )
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
    title = issue.get("title", "").lower()

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
    title = issue.get("title", "").lower()
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
    body = issue.get("body", "")
    exts = tuple(settings.CODE_EXTENSIONS)
    found = []
    for line in body.splitlines():
        for part in line.split("`"):
            p = PROJECT / part.strip()
            if p.exists() and p.is_file() and p.suffix in exts:
                found.append(p)
    return list(dict.fromkeys(found))


def find_relevant_files_advanced(issue: dict) -> list[Path]:
    """
    Extrahiert Dateipfade aus dem Issue-Body (Backtick-Erwähnungen).
    Zukünftig erweitert um AST-Analyse und Keyword-Suche.
    """
    body = issue.get("body", "")
    
    # 1. Backtick-Erwähnungen (wie bisher)
    exts = tuple(settings.CODE_EXTENSIONS)
    backtick_files = []
    for line in body.splitlines():
        for part in line.split("`"):
            p = PROJECT / part.strip()
            if p.exists() and p.is_file() and p.suffix in exts:
                backtick_files.append(p)

    # 2. Keyword-Suche (grep)
    keyword_files = _search_keywords(body, PROJECT)

    # 3. AST-Importanalyse
    # _find_imports erwartet eine Liste von Path-Objekten
    all_initial_files = list(dict.fromkeys(backtick_files + keyword_files))
    import_files = _find_imports(all_initial_files)

    # 4. Zusammenführen und Deduplizieren
    found = all_initial_files + import_files
    return list(dict.fromkeys(found))


def branch_name(issue: dict) -> str:
    """
    Generiert einen Branch-Namen aus Issue-Nummer und Titel.

    Returns:
        z.B. "fix/issue-16-bug-beschreibung"
    """
    num = issue["number"]
    title = issue.get("title", "").lower()
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
    slug = (
        slug.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    )
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
    num = issue["number"]
    stufe, desc = risk_level(issue)
    files = find_relevant_files_advanced(issue)
    branch = branch_name(issue)

    file_list = (
        "\n".join(f"- `{f.relative_to(PROJECT)}`" for f in files)
        or "- Keine automatisch erkannt — bitte manuell prüfen"
    )

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
    num = issue["number"]
    title = issue.get("title", "")
    body = issue.get("body", "")
    stufe, desc = risk_level(issue)
    files = find_relevant_files_advanced(issue)
    branch = branch_name(issue)

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
    num = issue["number"]
    title = issue.get("title", "")
    body = (issue.get("body", "") or "").strip()
    stufe, desc = risk_level(issue)
    files = find_relevant_files_advanced(issue)
    branch = branch_name(issue)

    body_short = body[:200] + ("..." if len(body) > 200 else "")
    file_list = (
        "\n".join(f"- {f.relative_to(PROJECT)}" for f in files) or "- keine erkannt"
    )

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



def save_tests_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:
    num = issue["number"]
    title = issue.get("title", "")
    body = (issue.get("body", "") or "").strip()
    
    typ_match = re.search(r"^\\[([^\\]]+)\\]", title)
    typ = (typ_match.group(1).lower().replace(" ", "-") if typ_match else "task")
    folder = _working_dir() / f"{num}-{typ}-tests"
    folder.mkdir(parents=True, exist_ok=True)
    
    ctx_file = folder / "tests_prompt.md"
    files_file = folder / "files.md"

    files_content = [f"# Dateien für Issue #{num}"]
    for rel_path, text in files_dict.items():
        lines = text.splitlines()
        if len(lines) > settings.MAX_FILE_LINES:
            text = "\n".join(lines[:settings.MAX_FILE_LINES]) + "\n... (abgeschnitten)"
        ext = Path(rel_path).suffix.lstrip(".")
        files_content.append(f"\n## {rel_path}\n```{ext}\n{text}\n```")
    files_file.write_text("\n".join(files_content), encoding="utf-8")

    prompt_content = f"""# Test-Generierung für Issue #{num}: {title}

{body}

Bitte generiere basierend auf den bereitgestellten Dateien in `files.md` folgende Test-Artefakte:

1. **Unit-Tests (`pytest`)**: Falls Python-Code vorhanden ist, schreibe passende Unit-Tests. Achte auf gute Abdeckung der Randfälle.
2. **Integrationstests**: Schreibe übergreifende Funktionstests, falls das Feature mehrere Komponenten betrifft.
3. **agent_eval.json Einträge**: Erstelle für das interne Evaluierungssystem neue JSON-Einträge.
   **WICHTIG**: Jeder Test-Eintrag in `agent_eval.json` MUSS zwingend ein Feld `tag` enthalten, das den abgedeckten Bereich benennt (z.B. `tag: "chroma_retrieval"`, `tag: "system_prompt"`, `tag: "context_window"`).

Gehe schrittweise vor und erstelle oder aktualisiere die entsprechenden Dateien direkt im Dateisystem.
"""
    ctx_file.write_text(prompt_content, encoding="utf-8")
    return ctx_file, files_file

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
    num = issue["number"]
    title = issue.get("title", "")
    body = (issue.get("body", "") or "").strip()
    stufe, desc = risk_level(issue)
    branch = branch_name(issue)

    body_short = body[:200] + ("..." if len(body) > 200 else "")
    file_list = "\n".join(f"- {name}" for name in files_dict) or "- keine erkannt"

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

    parts = []

    idir = _issue_dir(issue)
    skeleton_map = _load_skeleton_map(idir)

    for name in files_dict:  # only need keys, not content
        entry = skeleton_map.get(name)
        if entry and not entry.get("truncated"):
            symbols = entry.get("symbols", [])
            total_lines = entry.get("lines", "?")
            if symbols:
                sym_lines = "\n".join(
                    f"  - {'Klasse' if s['type']=='class' else 'Funktion'} `{s['name']}` Zeilen {s['lines']}  `{s['signature']}`"
                    for s in symbols
                )
            else:
                sym_lines = "  *(keine Klassen/Funktionen erkannt)*"
            slice_hint = f"python3 agent_start.py --get-slice {name}:1-{total_lines}"
            parts.append(
                f"## {name}  *({total_lines} Zeilen)*\n"
                f"{sym_lines}\n"
                f"> Volltext: `{slice_hint}`"
            )
        elif entry and entry.get("truncated"):
            parts.append(
                f"## {name}  *(zu groß — {entry.get('reason', '')})*\n"
                f"> Volltext: `python3 agent_start.py --get-slice {name}:1-?`"
            )
        else:
            # Kein Skelett-Eintrag: Volltext als Fallback (kleine/neue Dateien)
            text = files_dict[name]
            lines = text.splitlines()
            code = "\n".join(lines[:300])
            if len(lines) > 300:
                code += f"\n\n[... {len(lines)-300} weitere Zeilen — --get-slice für vollständigen Code ...]"
            ext = Path(name).suffix.lstrip(".")
            parts.append(f"## {name}\n```{ext}\n{code}\n```")

    ctx_file = idir / "starter.md"
    files_file = idir / "files.md"

    ctx_file.write_text(ctx_content, encoding="utf-8")
    files_header = (
        f"# Dateien — Issue #{num}\n"
        f"> Skelett-Modus aktiv — **kein Volltext**. Nutze `--get-slice datei.py:START-END` für Code-Details.\n"
        f"> Automatisch erkannt via Backtick-Erwähnungen, Import-Analyse (AST) und Keyword-Suche (grep).\n\n"
    )

    # repo_skeleton.md einbetten falls vorhanden
    skeleton_md_path = idir / "repo_skeleton.md"
    skeleton_section = ""
    if skeleton_md_path.exists():
        skeleton_section = skeleton_md_path.read_text(encoding="utf-8") + "\n\n---\n\n"

    files_file.write_text(files_header + skeleton_section + "\n\n".join(parts) + "\n", encoding="utf-8")

    log.info(f"Kontext gespeichert: {ctx_file}, {files_file}")
    return ctx_file, files_file


# ---------------------------------------------------------------------------
# Kontext-Loader: Import-Analyse + Keyword-Suche
# ---------------------------------------------------------------------------

_EXCLUDE_DIRS_DEFAULT = {
    "node_modules",
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "Backup",
    "backup",
    "vendor",
    "llama-cpp-python-build",
    "agent",
    "contexts",
    ".claude",
    "Documentation",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
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

_MAX_SKELETON_FILE_SIZE_KB = 20 # Neue Konstante für Skeleton-Dateigröße

_PROJECT_SKELETON = PROJECT / "repo_skeleton.json"

def _extract_ast_symbols(content: str) -> list[dict]:
    """Extrahiert ClassDef/FunctionDef aus Python-Quellcode via AST."""
    symbols = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return symbols
    lines = content.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            # Zeilennummern
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            # Signatur: erste Zeile des Blocks
            sig = lines[start - 1].strip() if start <= len(lines) else ""
            entry = {
                "type": "class" if isinstance(node, ast.ClassDef) else "function",
                "name": node.name,
                "lines": f"{start}-{end}",
                "signature": sig,
            }
            symbols.append(entry)
    return symbols


def _create_repo_skeleton(files: list[Path], output_dir: Path, max_size_kb: int = _MAX_SKELETON_FILE_SIZE_KB) -> Path:
    """
    Generiert repo_skeleton.json + repo_skeleton.md für die gegebenen Dateien.

    Für Python-Dateien: AST-Extraktion (ClassDef/FunctionDef mit Name, Zeilen, Signatur).
    Große Dateien werden als truncated markiert.

    Args:
        files:      Liste der relevanten Dateipfade
        output_dir: Verzeichnis für repo_skeleton.json / repo_skeleton.md

    Returns:
        Pfad zur erstellten repo_skeleton.json
    """
    skeleton_data = []
    for f in files:
        try:
            rel_path = str(f.relative_to(PROJECT))
            size_kb = f.stat().st_size // 1024
            if size_kb > max_size_kb:
                skeleton_data.append({
                    "path": rel_path,
                    "truncated": True,
                    "size_kb": size_kb,
                    "reason": f"Datei zu groß ({size_kb}KB > {max_size_kb}KB)",
                    "symbols": [],
                })
            else:
                content = f.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
                symbols = _extract_ast_symbols(content) if f.suffix == ".py" else []
                skeleton_data.append({
                    "path": rel_path,
                    "truncated": False,
                    "lines": len(lines),
                    "size_kb": size_kb,
                    "symbols": symbols,
                })
        except Exception:
            skeleton_data.append({
                "path": str(f.relative_to(PROJECT)),
                "truncated": True,
                "reason": "Fehler beim Lesen oder Verarbeiten der Datei",
                "symbols": [],
            })

    json_path = output_dir / "repo_skeleton.json"
    json_path.write_text(json.dumps(skeleton_data, indent=2), encoding="utf-8")

    # repo_skeleton.md für LLM-Prompt erzeugen
    md_path = output_dir / "repo_skeleton.md"
    md_path.write_text(_skeleton_to_md(skeleton_data), encoding="utf-8")

    log.info(f"Repo-Skelett erstellt: {json_path}")
    return json_path


def _skeleton_to_md(skeleton_data: list[dict]) -> str:
    """Erzeugt eine menschenlesbare Markdown-Übersicht aus repo_skeleton.json."""
    lines = ["# Repo-Skelett\n"]
    for entry in skeleton_data:
        path = entry.get("path", "?")
        if entry.get("truncated"):
            lines.append(f"## {path}  *(zu groß — {entry.get('reason', '')})*\n")
            continue
        total = entry.get("lines", 0)
        lines.append(f"## {path}  *({total} Zeilen)*\n")
        symbols = entry.get("symbols", [])
        if symbols:
            for sym in symbols:
                kind = "Klasse" if sym["type"] == "class" else "Funktion"
                lines.append(f"- **{kind}** `{sym['name']}` Zeilen {sym['lines']}")
                lines.append(f"  `{sym['signature']}`")
        else:
            lines.append("*(keine Klassen/Funktionen erkannt)*")
        lines.append("")
    return "\n".join(lines)


def cmd_build_skeleton() -> None:
    """Scannt alle .py-Dateien im PROJECT und schreibt repo_skeleton.json ins Projektroot."""
    exclude_dirs = {".git", "venv", "__pycache__", ".tox", "node_modules", "dist", "build"}
    py_files = [
        f for f in PROJECT.rglob("*.py")
        if not any(part in exclude_dirs for part in f.parts)
    ]
    _create_repo_skeleton(py_files, PROJECT, max_size_kb=10_000)  # kein Limit für projektweites Skelett
    print(f"[✓] Skelett erstellt: {len(py_files)} .py-Dateien → {_PROJECT_SKELETON}")


def _update_skeleton_incremental(changed_files: list[str]) -> None:
    """Aktualisiert repo_skeleton.json für die geänderten .py-Dateien inkrementell."""
    if not _PROJECT_SKELETON.exists():
        cmd_build_skeleton()
        return
    try:
        skeleton_data = json.loads(_PROJECT_SKELETON.read_text(encoding="utf-8"))
        skeleton_map = {entry["path"]: entry for entry in skeleton_data}
        updated = []
        for fname in changed_files:
            if not fname.endswith(".py"):
                continue
            fpath = PROJECT / fname
            if not fpath.exists():
                continue
            content = fpath.read_text(encoding="utf-8", errors="ignore")
            symbols = _extract_ast_symbols(content)
            lines = content.splitlines()
            skeleton_map[fname] = {
                "path": fname,
                "truncated": False,
                "lines": len(lines),
                "size_kb": len(content.encode("utf-8")) / 1024,
                "symbols": symbols,
            }
            updated.append(fname)
        _PROJECT_SKELETON.write_text(
            json.dumps(list(skeleton_map.values()), indent=2), encoding="utf-8"
        )
        if updated:
            log.info(f"Skelett inkrementell aktualisiert: {updated}")
    except Exception as e:
        log.warning(f"_update_skeleton_incremental Fehler: {e}")


def _load_skeleton_map(issue_dir: Path | None = None) -> dict:
    """Lädt repo_skeleton.json und gibt {path_str: entry_dict} zurück."""
    for candidate in [_PROJECT_SKELETON] + (
        [issue_dir / "repo_skeleton.json"] if issue_dir else []
    ):
        try:
            if candidate.exists():
                data = json.loads(candidate.read_text(encoding="utf-8"))
                return {item["path"]: item for item in data}
        except Exception as e:
            log.warning(f"_load_skeleton_map: {candidate} nicht lesbar: {e}")
    return {}


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
                        if (
                            candidate.exists()
                            and candidate not in files
                            and candidate not in found
                        ):
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
    num = issue["number"]
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


def _parse_diff_changed_lines(branch: str) -> dict[str, list[int]]:
    """
    Wertet `git diff --unified=0 main...HEAD` aus.

    Returns:
        {relativer_pfad: [geänderte_zeilennummern, ...]}
    """
    try:
        raw = subprocess.check_output(
            ["git", "diff", "--unified=0", f"main...{branch}"],
            cwd=PROJECT,
            stderr=subprocess.DEVNULL,
        ).decode(errors="ignore")
    except Exception:
        return {}

    result: dict[str, list[int]] = {}
    current_file: str | None = None
    for line in raw.splitlines():
        # +++ b/path/to/file.py
        if line.startswith("+++ b/"):
            current_file = line[6:]
            result.setdefault(current_file, [])
        # @@ -OLD +NEW,COUNT @@ ...
        elif line.startswith("@@") and current_file is not None:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2)) if m.group(2) is not None else 1
                for ln in range(start, start + max(count, 1)):
                    result[current_file].append(ln)
    return result


def _warn_diff_out_of_scope(number: int, branch: str) -> None:
    """
    Schritt 7 in _check_pr_preconditions: Warnung wenn LLM Zeilen außerhalb
    des AST-Skeletts geändert hat.

    Nicht-blockierend — Entwickler entscheidet. Postet Kommentar bei Fund.
    """
    # Kontext-Verzeichnis des Issues suchen
    idir = _find_issue_dir(number)
    if not idir:
        log.debug("Diff-Validierung: kein Kontext-Verzeichnis gefunden — übersprungen")
        return
    skeleton_path = idir / "repo_skeleton.json"
    if not skeleton_path.exists():
        log.debug("Diff-Validierung: repo_skeleton.json nicht gefunden — übersprungen")
        return

    try:
        skeleton_data = json.loads(skeleton_path.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning(f"Diff-Validierung: repo_skeleton.json nicht lesbar: {e}")
        return

    # Skelett als {pfad: [(start, end), ...]} aufbauen
    skeleton_ranges: dict[str, list[tuple[int, int]]] = {}
    for entry in skeleton_data:
        path = entry.get("path", "")
        if entry.get("truncated"):
            continue
        ranges = []
        for sym in entry.get("symbols", []):
            parts = sym.get("lines", "").split("-")
            if len(parts) == 2:
                try:
                    ranges.append((int(parts[0]), int(parts[1])))
                except ValueError:
                    pass
        # Auch die gesamte Datei als erlaubten Bereich eintragen
        # (falls keine Symbole: gesamte Datei ist in scope)
        total = entry.get("lines", 0)
        if not ranges and total:
            ranges = [(1, total)]
        if ranges:
            skeleton_ranges[path] = ranges

    changed = _parse_diff_changed_lines(branch)
    if not changed:
        return

    warnings: list[str] = []
    for file_path, changed_lines in changed.items():
        if not file_path.endswith(".py"):
            continue
        if file_path not in skeleton_ranges:
            # Datei war nicht im Kontext — potenziell out-of-scope
            warnings.append(
                f"- `{file_path}`: **nicht im Skelett** — {len(changed_lines)} Zeile(n) geändert"
            )
            continue
        ranges = skeleton_ranges[file_path]
        out = [
            ln for ln in changed_lines
            if not any(s <= ln <= e for s, e in ranges)
        ]
        if out:
            warnings.append(
                f"- `{file_path}`: {len(out)} Zeile(n) außerhalb AST-Bereich: {out[:10]}"
            )

    if not warnings:
        log.debug("Diff-Validierung: alle Änderungen im Skelett-Scope")
        return

    msg = (
        "⚠️ **Diff-Validierung: Scope-Warnung**\n\n"
        "Folgende Änderungen liegen außerhalb des freigegebenen AST-Bereichs:\n\n"
        + "\n".join(warnings)
        + "\n\n> Kein harter Abbruch — bitte prüfen ob diese Änderungen beabsichtigt sind."
    )
    print(f"\n[!] Diff-Validierung: {len(warnings)} Scope-Warnung(en):")
    for w in warnings:
        print(f"    {w}")
    try:
        gitea.post_comment(number, msg)
        log.info(f"Diff-Validierung Warnung in Issue #{number} gepostet")
    except Exception as e:
        log.warning(f"Diff-Validierung: Kommentar konnte nicht gepostet werden: {e}")


def _warn_slices_not_requested(number: int, branch: str) -> bool:
    """
    Schritt 8 in _check_pr_preconditions: Warnung wenn .py-Dateien geändert wurden
    ohne entsprechende --get-slice Anfragen.

    Gibt True zurück wenn eine Verletzung gefunden wurde (für SLICE_GATE_ENABLED).
    Berücksichtigt Dateigrößen: Dateien < SLICE_GATE_MIN_LINES werden ignoriert.
    """
    try:
        diff_out = subprocess.check_output(
            ["git", "diff", "--name-only", f"main...{branch}"],
            cwd=PROJECT, stderr=subprocess.DEVNULL
        ).decode().strip()
        changed_py = [f for f in diff_out.splitlines() if f.endswith(".py")]
        if not changed_py:
            return False

        min_lines = settings.SLICE_GATE_MIN_LINES
        large_files = []
        for rel_path in changed_py:
            abs_path = PROJECT / rel_path
            if abs_path.exists():
                try:
                    line_count = len(abs_path.read_text(encoding="utf-8", errors="ignore").splitlines())
                    if line_count >= min_lines:
                        large_files.append((rel_path, line_count))
                except Exception:
                    large_files.append((rel_path, 0))
            else:
                large_files.append((rel_path, 0))

        if not large_files:
            log.debug("Slice-Gate: alle geänderten Dateien unter Größen-Schwellwert")
            return False

        idir = _find_issue_dir(number)
        slices_requested: list[dict] = []
        if idir:
            session_path = idir / "session.json"
            if session_path.exists():
                try:
                    data = json.loads(session_path.read_text(encoding="utf-8"))
                    slices_requested = data.get("slices_requested", [])
                except Exception:
                    pass

        requested_specs = [s.get("spec", "") for s in slices_requested]
        gate_mode = settings.SLICE_GATE_ENABLED
        label = "❌ **Slice-Gate**" if gate_mode else "⚠️ **Slice-Warnung**"

        if not slices_requested:
            file_list = "\n".join(f"- `{f}` ({lc} Zeilen)" for f, lc in large_files)
            msg = (
                f"{label}: Keine `--get-slice` Anfragen in session.json gefunden.\n\n"
                f"Geänderte Dateien (≥{min_lines} Zeilen):\n{file_list}\n\n"
                + ("> **Harter Abbruch aktiviert** (SLICE_GATE_ENABLED=true)."
                   if gate_mode else
                   "> Bitte prüfen ob Code-Slices angefordert wurden.")
            )
            print(f"\n[!] Slice-Warnung: keine --get-slice Anfragen gefunden")
            try:
                gitea.post_comment(number, msg)
            except Exception as e:
                log.warning(f"Slice-Warnung: Kommentar konnte nicht gepostet werden: {e}")
            return True

        missing = [(f, lc) for f, lc in large_files
                   if not any(f in spec for spec in requested_specs)]
        if not missing:
            log.debug("Slice-Gate: alle großen Dateien hatten Slice-Anfragen")
            return False

        if not _PROJECT_SKELETON.exists() and not gate_mode:
            return False

        n = len(missing)
        file_list = "\n".join(f"- `{f}` ({lc} Zeilen)" for f, lc in missing)
        msg = (
            f"{label}: {n} Datei(en) geändert ohne `--get-slice` (≥{min_lines} Zeilen):\n\n"
            + file_list
            + ("\n\n> **Harter Abbruch aktiviert** (SLICE_GATE_ENABLED=true)."
               if gate_mode else
               "\n\n> Kein harter Abbruch — bitte prüfen ob Slices angefordert wurden.")
        )
        print(f"\n[!] Slice-Warnung: {n} Datei(en) ohne Slice: {[f for f,_ in missing]}")
        try:
            gitea.post_comment(number, msg)
        except Exception as e:
            log.warning(f"Slice-Warnung: Kommentar konnte nicht gepostet werden: {e}")
        return True

    except Exception as e:
        log.debug(f"_warn_slices_not_requested übersprungen: {e}")
        return False


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
            (
                "Implementierungsplan" in c.get("body", "")
                or "Agent-Analyse" in c.get("body", "")
            )
            for c in comments
        )
        if not plan_kommentar:
            fehler.append(
                "Kein Plan-Kommentar im Issue gefunden (cmd_plan ausgeführt?)"
            )
        else:
            # 3. Metadata-Block im Plan-Kommentar
            meta_vorhanden = any(
                "Agent-Metadaten" in c.get("body", "")
                for c in comments
                if "Implementierungsplan" in c.get("body", "")
                or "Agent-Analyse" in c.get("body", "")
            )
            if not meta_vorhanden:
                fehler.append(
                    "Plan-Kommentar ohne Metadata-Block (cmd_plan neu ausführen)"
                )
    except Exception as e:
        log.warning(f"Kommentar-Prüfung fehlgeschlagen: {e}")

    # 4. Eval nach letztem Commit — nur wenn agent_eval.json existiert
    eval_cfg = evaluation._resolve_config(PROJECT)
    hist_path = evaluation._resolve_path(
        PROJECT, "score_history.json", evaluation.SCORE_HISTORY
    )
    if eval_cfg.exists():
        if hist_path.exists():
            try:
                with hist_path.open(encoding="utf-8") as f:
                    history = json.load(f)
                if history:
                    last_eval_ts = history[-1].get("timestamp", "")
                    last_commit_ts = (
                        subprocess.check_output(
                            ["git", "log", "-1", "--pretty=%cI"],
                            cwd=PROJECT,
                            stderr=subprocess.DEVNULL,
                        )
                        .decode()
                        .strip()
                    )
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
            fehler.append(
                "score_history.json nicht gefunden — Eval noch nie ausgeführt"
            )
    else:
        log.debug("Kein agent_eval.json — Eval-Prüfung übersprungen")

    # 5. Pflicht-Kette: Server-Neustart vor PR (nur wenn restart_script konfiguriert)
    if eval_cfg.exists():
        try:
            with eval_cfg.open(encoding="utf-8") as f:
                cfg_data = json.load(f)
            restart_script = cfg_data.get("restart_script")
            if restart_script and Path(restart_script).exists():
                # Prüfen ob Server seit letztem Commit neu gestartet wurde
                # (heuristisch: wenn Eval nach letztem Commit fehlt, wurde
                # vermutlich auch nicht neu gestartet)
                if fehler and any("Eval nicht nach letztem Commit" in e for e in fehler):
                    fehler.append(
                        f"Server-Neustart empfohlen vor PR — restart_script: {restart_script}\n"
                        f"    → Lösung: --restart-before-eval beim PR-Aufruf verwenden"
                    )
        except Exception as e:
            log.warning(f"restart_script Prüfung fehlgeschlagen: {e}")

    # 6. Agent-Self-Check (if agent code is modified)
    try:
        changed_files = (
            subprocess.check_output(
                ["git", "diff", "--name-only", "main...HEAD"],
                cwd=PROJECT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .splitlines()
        )
        agent_files = {"agent_start.py", "settings.py", "gitea_api.py"}
        if any(f in agent_files for f in changed_files):
            log.info(
                "Agent code modification detected, running self-consistency check..."
            )
            try:
                subprocess.check_call(["python3", "agent_self_check.py"], cwd=PROJECT)
            except subprocess.CalledProcessError:
                fehler.append(
                    "Agent Self-Consistency Check fehlgeschlagen (siehe Logs)"
                )
    except Exception as e:
        log.warning(f"Konnte Git Diff für Self-Check nicht abfragen: {e}")

    # 7. Diff-Validierung: geänderte Zeilen gegen repo_skeleton.json prüfen (Warnung)
    _warn_diff_out_of_scope(number, branch)

    # 8. Slice-Warnung: geänderte Dateien ohne --get-slice Anfragen (Warnung)
    slice_violation = _warn_slices_not_requested(number, branch)
    if slice_violation and settings.SLICE_GATE_ENABLED:
        fehler.append(
            f"Slice-Gate aktiv (SLICE_GATE_ENABLED=true): "
            f"{settings.SLICE_GATE_MIN_LINES}+ Zeilen-Dateien ohne --get-slice geändert"
        )

    if fehler:
        print("\n❌ cmd_pr abgebrochen — Prozess nicht vollständig:")
        for f in fehler:
            print(f"   • {f}")
        print("\n→ Fehlende Schritte nachholen, dann erneut ausführen.")
        sys.exit(1)


def _validate_pr_completion(
    number: int, branch: str, pr_url: str, idir_moved: bool
) -> None:
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
        warnung = (
            "⚠️ **Prozess unvollständig** — folgende Schritte fehlen:\n"
            + "\n".join(f"- {s}" for s in fehlend)
        )
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
    missing = [f for f in required if f.lower() not in body.lower()]
    if not missing:
        return
    msg = f"[!] Kommentar-Validierung '{comment_type}': fehlende Felder: {', '.join(missing)}"
    log.warning(msg)
    print(msg)
    if critical:
        print(
            "→ Kommentar unvollständig — Prozess abgebrochen. Bitte erneut ausführen."
        )
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
        user = c.get("user", {}).get("login", "")
        body = c.get("body", "")
        ts = c.get("created_at", "")[:10]
        body_short = body[:1500] + ("..." if len(body) > 1500 else "")
        lines.append(f"**[{ts}] {user}:**\n{body_short}")

    current = starter_path.read_text(encoding="utf-8")
    if "## Kommentarhistorie" in current:
        current = current[: current.index("## Kommentarhistorie")]

    starter_path.write_text(
        current.rstrip()
        + "\n\n## Kommentarhistorie\n\n"
        + "\n\n---\n\n".join(lines)
        + "\n",
        encoding="utf-8",
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

    files = find_relevant_files_advanced(issue)

    # Repo-Skelett generieren
    issue_dir = _issue_dir(issue)
    _create_repo_skeleton(files, issue_dir)


    # Metadaten-Block (collapsible) aufbauen
    file_stats = []
    total_chars = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
            chars = len(text)
            total_chars += chars
            file_stats.append(
                f"  {f.relative_to(PROJECT)} ({text.count(chr(10))} Zeilen, ~{chars // 4:,} Tokens)"
            )
        except Exception:
            file_stats.append(f"  {f.relative_to(PROJECT)} (nicht lesbar)")

    total_tokens = total_chars // 4
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    model = os.environ.get("CLAUDE_MODEL", os.environ.get("MODEL", "unbekannt"))
    try:
        branch_cur = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=PROJECT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
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
    comment = gitea.post_comment(number, plan_body)
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
            gitea.remove_label(
                number, settings.LABEL_PROPOSED
            )  # Plan noch nicht freigegeben
            out.write_text(
                out.read_text(encoding="utf-8") + "\n## Analyse\n" + analyse_body,
                encoding="utf-8",
            )
            log.info(
                f"Analyse-Kommentar gepostet, Label '{settings.LABEL_HELP}' gesetzt, '{settings.LABEL_PROPOSED}' entfernt"
            )
            print(
                f"[✓] Analyse-Kommentar gepostet, Label '{settings.LABEL_HELP}' gesetzt, '{settings.LABEL_PROPOSED}' entfernt"
            )
        else:
            print(
                f"[!] Gitea hat bereits befüllten Plan — kein Analyse-Kommentar gepostet"
            )

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
        print(
            f"[✗] Issue #{number} hat Risikostufe 4 — kein automatischer Implement-Start."
        )
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
        print(
            f"    Bitte --issue {number} erneut ausführen um aktuellen Kontext zu laden."
        )

    if not gitea.check_approval(number, settings.LABEL_HELP):
        log.warning(f"Keine Freigabe für Issue #{number}")
        print(f"[✗] Keine Freigabe für Issue #{number}.")
        print(
            f"    Kommentiere 'ok' auf: {gitea.GITEA_URL}/{gitea.REPO}/issues/{number}"
        )
        sys.exit(1)

    log.info(f"Freigabe erhalten für Issue #{number} — starte Implementierung")
    print(f"[✓] Freigabe erhalten — starte Implementierung.")
    gitea.remove_label(number, settings.LABEL_HELP)
    branch = branch_name(issue)

    try:
        result = subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=PROJECT,
            capture_output=True,
            text=True,
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
    gitea.post_comment(
        number,
        f"""## ✅ Implementierung gestartet

**Branch:** `{branch}`

## Nächste Schritte
- Branch auschecken: `git checkout {branch}`
- Kontext lesen: `contexts/{num}-{typ}/starter.md`
- Implementieren + nach jeder Datei committen
- PR erstellen: `python3 agent_start.py --pr {num} --branch {branch} --summary "..."`
""",
    )

    base_files = find_relevant_files_advanced(issue)
    import_files = _find_imports(base_files)
    # Kommentare für Keyword-Suche einbeziehen
    comments = gitea.get_comments(issue["number"])
    bot_user = getattr(settings, "GITEA_BOT_USER", None) or "working-bot"
    user_comments = [
        c.get("body", "")
        for c in comments
        if c.get("user", {}).get("login") != bot_user
    ]
    full_text = (issue.get("body", "") or "") + "\n" + "\n".join(user_comments)
    kw_files = _search_keywords(full_text, PROJECT)

    all_files = list(dict.fromkeys(base_files + import_files + kw_files))
    files_dict = {
        str(f.relative_to(PROJECT)): f.read_text(encoding="utf-8") for f in all_files
    }
    ctx_file, files_file = save_implement_context(issue, files_dict)
    _idir2 = _find_issue_dir(num)
    print(
        f"[✓] Kontext: {_idir2.name if _idir2 else ''}/starter.md + files.md — bereit zur Implementierung"
    )

    # Kontext-Zusammenfassung als Gitea-Kommentar posten
    context_summary_parts = []

    if user_comments:
        from_comments: set[str] = set()
        for comment in user_comments:
            words = re.findall(r"`([^`]+)`", comment)
            words += re.findall(r"\b([A-Za-z_][A-Za-z0-9_]{3,})\b", comment)
            from_comments.update(w.lower() for w in words if len(w) >= 4)
        if from_comments:
            context_summary_parts.append(
                f"**Keywords aus Kommentaren:** {', '.join(sorted(from_comments)[:10])}"
            )

    if files_dict:
        file_list = list(files_dict.keys())[:15]
        context_summary_parts.append(
            f"**Erkannte Dateien ({len(files_dict)}):**\n"
            + "\n".join(f"- `{f}`" for f in file_list)
        )
        if len(files_dict) > 15:
            context_summary_parts.append(f"  _... und {len(files_dict) - 15} weitere_")

    if user_comments:
        context_summary_parts.append(
            f"**Diskussion:** {len(user_comments)} Kommentar(e) einbezogen"
        )

    if context_summary_parts:
        context_comment = (
            "## 📎 Kontext-Loader\n\n"
            + "\n\n".join(context_summary_parts)
            + "\n\n---\n_Kontext bereit in `starter.md` + `files.md`_"
        )
        gitea.post_comment(number, context_comment)


_RESTART_PATTERNS = (
    "server.py",
    "bot.js",
    "nanoclaw/",
    "whatsapp-bot/",
    "router.py",
    "analyst_worker.py",
)


def _neustart_required(changed_files: list[str]) -> str:
    """Gibt 'Ja' zurück wenn server-seitige Dateien geändert wurden, sonst 'Nein'."""
    for f in changed_files:
        if any(pat in f for pat in _RESTART_PATTERNS):
            return "Ja"
    return "Nein"


def cmd_pr(
    number: int,
    branch: str,
    summary: str = "",
    force: bool = False,
    restart_before_eval: bool = False,
) -> None:
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

    issue = gitea.get_issue(number)
    title = f"{issue['title']} (closes #{number})"
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
        changed = (
            subprocess.check_output(
                ["git", "diff", "--name-only", f"main...{branch}"],
                cwd=PROJECT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .splitlines()
        )
        code_changed = [f for f in changed if not f.startswith("Documentation/")]
        docs_changed = [f for f in changed if f.startswith("Documentation/")]
        if code_changed and not docs_changed:
            log.warning("Code geändert aber Documentation/ nicht aktualisiert")
            print(
                "[!] Warnung: Code geändert aber keine Documentation/*.md aktualisiert."
            )
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
                log.error(
                    f"Eval FAIL — PR blockiert (Score {eval_result.score}/{eval_result.max_score})"
                )
                print(f"[✗] PR blockiert. Kommentar in Issue #{number} gepostet.")
                return
        except Exception as e:
            msg = f"⚠️ **Eval-Fehler** — Evaluation konnte nicht ausgeführt werden:\n```\n{e}\n```\nPR wurde trotzdem erstellt — bitte `evaluation.py` prüfen."
            gitea.post_comment(number, msg)
            log.warning(f"Eval-Fehler (Warnung gepostet): {e}")
            print(f"[!] Eval-Fehler (Warnung gepostet): {e}")

    log.info(f"Erstelle PR für Issue #{number} von Branch '{branch}'")
    pr = gitea.create_pr(branch=branch, title=title, body=pr_body)
    pr_url = pr.get("html_url", "?")

    gitea.swap_label(number, settings.LABEL_PROGRESS, settings.LABEL_REVIEW)

    summary_block = (
        f"## Was diese Änderung bewirkt\n{summary}"
        if summary
        else '> ⚠️ Keine Zusammenfassung angegeben — beim nächsten Mal `--summary "..."` mitgeben.'
    )
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

    # CHANGELOG.md automatisch mit "Unreleased"-Block aktualisieren
    try:
        cmd_changelog(version=None, update_file=True)
    except Exception as e:
        log.warning(f"CHANGELOG-Update fehlgeschlagen (nicht kritisch): {e}")
        print(f"[!] CHANGELOG-Update fehlgeschlagen: {e}")

    _dashboard_event("cmd_pr abgeschlossen")

    # Maßnahme 4: Abschluss-Validierung
    _validate_pr_completion(number, branch, pr_url, idir_moved)



def cmd_generate_tests(number: int) -> None:
    print(f"[→] Erstelle Test-Generierungs-Kontext für Issue #{number}...")
    log.info(f"Starte Test-Generierung für Issue #{number}")
    
    issue = gitea.get_issue(number)
    
    base_files = find_relevant_files_advanced(issue)
    import_files = _find_imports(base_files)
    
    comments = gitea.get_comments(number)
    bot_user = getattr(settings, "GITEA_BOT_USER", None) or "working-bot"
    user_comments = [c.get("body", "") for c in comments if c.get("user", {}).get("login") != bot_user]
    full_text = (issue.get("body", "") or "") + "\n" + "\n".join(user_comments)
    kw_files = _search_keywords(full_text, PROJECT)
    
    all_files = list(dict.fromkeys(base_files + import_files + kw_files))
    files_dict = {str(f.relative_to(PROJECT)): f.read_text(encoding="utf-8") for f in all_files}
    
    ctx_file, files_file = save_tests_context(issue, files_dict)
    
    print(f"[✓] Kontextdateien für Tests erstellt in {ctx_file.parent.name}/")
    print(f"\n    → Führe nun Claude Code aus, um die Tests zu generieren:\n")
    print(f"    claude -p {ctx_file.relative_to(PROJECT)}\n")
    
    msg = f"🤖 **Test-Generierung gestartet**\n\nDie relevanten Dateien wurden gesammelt. Du kannst die Tests nun lokal mit folgendem Befehl generieren lassen:\n\n```bash\nclaude -p {ctx_file.relative_to(PROJECT)}\n```\n\n*Der Prompt enthält strikte Vorgaben für pytest, Integrationstests und `agent_eval.json` Einträge inkl. `tag`-Feld.*"
    gitea.post_comment(number, msg)

def _current_issue_from_branch() -> int | None:
    """Extrahiert Issue-Nummer aus dem aktuellen Branch-Namen."""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT, stderr=subprocess.DEVNULL
        ).decode().strip()
        m = re.search(r'[/-]issue-(\d+)[/-]', branch)
        if m:
            return int(m.group(1))
        m = re.search(r'-(\d+)-', branch)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None


def _estimate_slice_tokens(spec: str) -> int:
    """Schätzt die Token-Anzahl eines Slices anhand der Zeilenzahl (Zeilen × TOKEN_LINES_FACTOR)."""
    try:
        _, range_part = spec.rsplit(":", 1)
        if "-" in range_part:
            start, end = (int(x) for x in range_part.split("-", 1))
            line_count = max(0, end - start + 1)
        else:
            line_count = 1
        return line_count * settings.TOKEN_LINES_FACTOR
    except Exception:
        return 0


def _log_slice_request(spec: str) -> None:
    """Loggt eine --get-slice Anfrage in session.json und summiert Token-Schätzung."""
    try:
        issue_num = _current_issue_from_branch()
        if issue_num is None:
            return
        idir = _find_issue_dir(issue_num)
        if not idir:
            return
        session_path = idir / "session.json"
        data: dict = {}
        if session_path.exists():
            try:
                data = json.loads(session_path.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        slices = data.get("slices_requested", [])
        token_estimate = _estimate_slice_tokens(spec)
        slices.append({
            "spec": spec,
            "timestamp": datetime.datetime.now().isoformat(),
            "estimated_tokens": token_estimate,
        })
        data["slices_requested"] = slices
        total_tokens = sum(s.get("estimated_tokens", 0) for s in slices)
        data["estimated_tokens"] = total_tokens
        data["budget_warn_threshold"] = settings.TOKEN_BUDGET_WARN
        session_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        threshold = settings.TOKEN_BUDGET_WARN
        if total_tokens >= threshold:
            print(
                f"[!] Token-Budget: ~{total_tokens:,} / {threshold:,} — "
                f"Limit erreicht. Neue Session empfohlen."
            )
            log.warning(f"Token-Budget überschritten: {total_tokens} >= {threshold}")
        elif total_tokens >= int(threshold * 0.9):
            print(
                f"[!] Token-Budget: ~{total_tokens:,} / {threshold:,} — "
                f"Nächster Slice könnte Limit überschreiten."
            )
    except Exception:
        pass


def cmd_get_slice(spec: str) -> None:
    """
    Gibt einen exakten Zeilenbereich einer Datei aus.

    Args:
        spec: "datei.py:START-END" oder "datei.py:START"
    """
    if ":" not in spec:
        print(f"[✗] Format: --get-slice datei.py:START-END  (z.B. agent_start.py:45-90)")
        sys.exit(1)
    file_part, range_part = spec.rsplit(":", 1)
    path = PROJECT / file_part
    if not path.exists():
        print(f"[✗] Datei nicht gefunden: {path}")
        sys.exit(1)
    try:
        if "-" in range_part:
            start, end = (int(x) for x in range_part.split("-", 1))
        else:
            start = end = int(range_part)
    except ValueError:
        print(f"[✗] Ungültiger Bereich: {range_part!r}  (erwartet: START-END oder START)")
        sys.exit(1)
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    total = len(lines)
    start = max(1, start)
    end = min(total, end)
    print(f"# {file_part}  Zeilen {start}-{end}  (Datei: {total} Zeilen)\n")
    for i, line in enumerate(lines[start - 1 : end], start=start):
        print(f"{i:5}  {line}")
    _log_slice_request(spec)


# SEARCH/REPLACE Protokoll → plugins/patch.py


# Changelog-Generator → plugins/changelog.py


def cmd_fixup(number: int) -> None:
    """
    Nach einem Bugfix-Commit auf einem in-progress Issue:
    - Liest die letzte Commit-Message
    - Postet Bugfix-Kommentar ins Gitea-Issue
    - Setzt Label: in-progress → needs-review
    """
    try:
        commit_msg = (
            subprocess.check_output(
                ["git", "log", "-1", "--pretty=%s%n%n%b"],
                cwd=PROJECT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
        commit_sha = (
            subprocess.check_output(
                ["git", "log", "-1", "--pretty=%h"],
                cwd=PROJECT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
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

def _auto_perf_issue_exists(test_name: str) -> bool:
    """Prüft ob ein offenes [Auto-Perf]-Issue für diesen Test bereits existiert."""
    issues = gitea.get_issues(state="open")
    marker = f"[Auto-Perf] {test_name}"
    return any(marker in i.get("title", "") for i in issues)



def _auto_improvement_issue_exists(tag: str) -> bool:
    issues = gitea.get_issues(state="open")
    marker = f"[Auto-Improvement] Systematische Schwäche bei Tag: {tag}"
    return any(marker in i.get("title", "") for i in issues)

def _check_systematic_tag_failures(project_root) -> None:
    try:
        cfg = evaluation._load_config(project_root)
        if not cfg: return
        
        threshold = cfg.get("tag_failure_threshold", 3)
        window = cfg.get("tag_failure_window", 5)
        hints = cfg.get("improvement_hints", {})
        
        hist_path = evaluation._resolve_path(project_root, "score_history.json", evaluation.SCORE_HISTORY)
        if not hist_path.exists(): return
        
        import json
        with hist_path.open(encoding="utf-8") as f:
            history = json.load(f)
            
        if not history: return
        
        recent_history = history[-window:]
        tag_failures = {}
        
        for run_entry in recent_history:
            failed_tags_in_run = set()
            for ftest in run_entry.get("failed", []):
                tag = ftest.get("tag", "")
                if tag:
                    failed_tags_in_run.add(tag)
            
            for tag in failed_tags_in_run:
                tag_failures[tag] = tag_failures.get(tag, 0) + 1
                
        for tag, count in tag_failures.items():
            if count >= threshold:
                if _auto_improvement_issue_exists(tag):
                    log.debug(f"[Auto-Improvement]-Issue für Tag '{tag}' bereits offen.")
                    continue
                    
                hint = hints.get(tag, "Keine spezifischen Hinweise in agent_eval.json (Feld 'improvement_hints') definiert.")
                
                # Sammle alle fehlerhaften Tests für diesen Tag als Kontext
                failed_tests_for_tag = set()
                for run_entry in recent_history:
                    for ftest in run_entry.get("failed", []):
                        if ftest.get("tag", "") == tag:
                            failed_tests_for_tag.add(ftest.get("name", "Unbekannter Test"))
                
                tests_list = "\n".join(f"- {t}" for t in failed_tests_for_tag)
                
                # Suche nach betroffenen Dateien in der Konfiguration
                affected_files_cfg = cfg.get("affected_files", {}).get(tag, [])
                files_list = "\n".join(f"- `{f}`" for f in affected_files_cfg) if affected_files_cfg else "- *(Keine Dateien in `affected_files` Konfiguration hinterlegt)*"

                body = (
                    f"Der Test-Tag **{tag}** ist in den letzten {len(recent_history)} Evaluierungs-Läufen {count}-mal fehlgeschlagen.\n\n"
                    f"Dies deutet auf eine systematische Schwäche oder Regression in diesem Code-Bereich hin.\n\n"
                    f"**Betroffene Tests:**\n"
                    f"{tests_list}\n\n"
                    f"**Betroffene Dateien (laut Konfiguration):**\n"
                    f"{files_list}\n\n"
                    f"**Vorgeschlagene Hebel / Lösungsansätze:**\n"
                    f"{hint}\n\n"
                    f"Bitte den betroffenen Bereich analysieren und nachhaltig stabilisieren."
                )
                
                issue = gitea.create_issue(
                    title=f"[Auto-Improvement] Systematische Schwäche bei Tag: {tag}",
                    body=body,
                    label=settings.LABEL_READY,
                )
                log.warning(f"Auto-Improvement Issue erstellt: #{issue['number']} für Tag '{tag}'")
                print(f"[!] Auto-Improvement Issue erstellt: #{issue['number']} — Tag {tag}")
                
    except Exception as e:
        log.error(f"Fehler bei systematischer Tag-Analyse: {e}")
        print(f"[!] Fehler bei systematischer Tag-Analyse: {e}")


def _sync_closed_contexts() -> None:
    """Verschiebt Context-Ordner von open/ nach done/ für bereits geschlossene Issues.

    Läuft beim Watch-Start, um Drift zu korrigieren wenn Issues außerhalb des Agents
    geschlossen wurden und der Context-Ordner liegen geblieben ist.
    Prüft jede Issue-Nummer einzeln per API statt alle geschlossenen Issues zu laden.
    """
    open_dir = _context_dir() / "open"
    if not open_dir.exists():
        return
    moved = 0
    for d in open_dir.iterdir():
        if not d.is_dir():
            continue
        try:
            num = int(d.name.split("-")[0])
        except ValueError:
            continue
        issue = gitea.get_issue(num)
        if issue and issue.get("state") == "closed":
            dest = _done_dir() / d.name
            shutil.move(str(d), str(dest))
            log.info(f"_sync_closed_contexts: {d.name} → done/")
            moved += 1
    if moved:
        print(f"[✓] {moved} verwaiste Context(s) nach done/ verschoben")


def _consecutive_passes_for_test(test_name: str) -> int:
    """Zählt aufeinanderfolgende Passes eines Tests aus score_history (rückwärts).

    Bricht beim ersten Eintrag ab, in dem der Test in ``failed`` vorkommt.
    """
    hist_path = evaluation._resolve_path(
        PROJECT, "score_history.json", evaluation.SCORE_HISTORY
    )
    if not hist_path.exists():
        return 0
    try:
        with hist_path.open(encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return 0

    count = 0
    for entry in reversed(history):
        test_failed = any(
            f["name"] == test_name for f in entry.get("failed", [])
        )
        if not test_failed:
            count += 1
        else:
            break
    return count


def _close_resolved_auto_issues(result: "evaluation.EvalResult") -> None:
    """Schließt [Auto]-Issues deren Test jetzt wieder besteht (und Perf-Issues).

    Unterstützt ``close_after_consecutive_passes`` aus agent_eval.json:
    Ein Auto-Issue wird erst geschlossen, wenn der zugehörige Test N-mal
    hintereinander bestanden hat.  Standard: 1 (bisheriges Verhalten).
    """
    cfg = evaluation._load_config(PROJECT) or {}
    threshold = cfg.get("close_after_consecutive_passes", 1)

    passed_names = {t.name for t in result.all_tests if t.passed}
    perf_passed_names = {t.name for t in result.all_tests if t.max_response_ms is None or t.response_ms <= t.max_response_ms}
    issues = gitea.get_issues(state="open")
    for issue in issues:
        title = issue.get("title", "")
        matched_name: str | None = None

        if title.startswith("[Auto]"):
            for name in passed_names:
                if name in title:
                    matched_name = name
                    break
        elif title.startswith("[Auto-Perf]"):
            for name in perf_passed_names:
                if name in title:
                    matched_name = name
                    break
        else:
            continue

        if matched_name is None:
            continue

        # --- Consecutive-Pass Gate ---
        consec = _consecutive_passes_for_test(matched_name)

        if consec < threshold:
            # Fortschritts-Kommentar — aber nur wenn sich der Zähler geändert hat
            progress_tag = f"Test besteht ({consec}/{threshold})"
            existing = gitea.get_comments(issue["number"])
            already_posted = any(progress_tag in c.get("body", "") for c in existing)
            if not already_posted:
                gitea.post_comment(
                    issue["number"],
                    f"⏳ {progress_tag} — warte auf Bestätigung",
                )
                log.info(
                    f"[Auto]-Issue #{issue['number']}: {progress_tag}"
                )
                print(f"[⏳] Auto-Issue #{issue['number']}: {progress_tag}")
            continue

        # --- Threshold erreicht → schließen ---
        gitea.close_issue(issue["number"])
        for lbl in [
            settings.LABEL_READY,
            settings.LABEL_PROPOSED,
            settings.LABEL_PROGRESS,
        ]:
            try:
                gitea.remove_label(issue["number"], lbl)
            except Exception:
                pass
        close_msg = (
            f"nach {consec} aufeinanderfolgenden Passes"
            if threshold > 1
            else f"Test '{matched_name}' besteht wieder"
        )
        log.info(
            f"[Auto]-Issue #{issue['number']} geschlossen — {close_msg}"
        )
        print(
            f"[✓] Auto-Issue #{issue['number']} geschlossen ({close_msg})"
        )
        _dashboard_event("Auto-Issue geschlossen")
        idir = _find_issue_dir(issue["number"])
        if idir and idir.exists():
            dest = _done_dir() / idir.name
            shutil.move(str(idir), str(dest))
            log.info(f"Context verschoben: {idir.name} → done/")


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
    model = os.environ.get(
        "CLAUDE_MODEL", os.environ.get("MODEL", settings.CLAUDE_MODEL)
    )
    try:
        commit = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=PROJECT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        commit = "unbekannt"
    if not branch:
        try:
            branch = (
                subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=PROJECT,
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
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
        files_changed_line = f"\n**Geänderte Dateien:** " + ", ".join(
            f"`{p}`" for p in changed_paths
        )

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
    data = {
        "started": now.isoformat(),
        "issues_completed": 0,
        "last_activity": now.isoformat(),
    }
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
    hist_path = evaluation._resolve_path(
        project_root, "score_history.json", evaluation.SCORE_HISTORY
    )
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
        ts = e.get("timestamp", "?")[:16].replace("T", " ")
        score = int(e.get("score", 0))
        max_s = int(e.get("max_score", 0))
        trigger = e.get("trigger", "?")
        failed = e.get("failed", [])
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
        r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2})"  # ISO: 2026-03-20T14:32 oder mit Leerzeichen
        r"|(\d{2}:\d{2}:\d{2})"  # HH:MM:SS
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
                dt = datetime.datetime(
                    today.year, today.month, today.day, int(h), int(mi), int(s)
                )
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
        log.info(
            "Server-Start-Zeitpunkt nicht ermittelbar — Staleness-Check übersprungen"
        )
        return

    try:
        commit_ts_raw = (
            subprocess.check_output(
                ["git", "log", "-1", "--pretty=%cI", branch],
                cwd=PROJECT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
        # Zeitzone entfernen für Vergleich
        commit_ts = datetime.datetime.fromisoformat(commit_ts_raw)
        if commit_ts.tzinfo:
            import datetime as _dt

            commit_ts = commit_ts.replace(tzinfo=None) + commit_ts.utcoffset()
            commit_ts = commit_ts.replace(tzinfo=None)
    except Exception as e:
        log.info(
            f"Commit-Timestamp nicht ermittelbar — Staleness-Check übersprungen ({e})"
        )
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
    log.warning(
        f"Server-Code veraltet: commit {commit_ts} > server_start {server_start}"
    )
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
        print(
            "[!] --restart-before-eval: kein restart_script in agent_eval.json konfiguriert"
        )
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
        out = (
            subprocess.check_output(
                ["git", "log", "--oneline", f"--after={last_ts}"],
                cwd=project_root,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
        return bool(out)
    except Exception:
        return False


def _wait_for_server(
    url: str | None = None,
    timeout_sec: int | None = None,
    interval_sec: int | None = None,
) -> bool:
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
    import urllib.error
    import urllib.request

    url = url or settings.SERVER_URL
    timeout_sec = (
        timeout_sec if timeout_sec is not None else settings.SERVER_WAIT_TIMEOUT
    )
    interval_sec = (
        interval_sec if interval_sec is not None else settings.SERVER_WAIT_INTERVAL
    )

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

    print(
        f"[eval-after-restart] Warte auf Server ({settings.SERVER_URL}, max {settings.SERVER_WAIT_TIMEOUT}s)..."
    )
    if not _wait_for_server():
        print(
            f"[eval-after-restart] ❌ Timeout — Server nicht erreichbar nach {settings.SERVER_WAIT_TIMEOUT}s."
        )
        sys.exit(1)
    print("[eval-after-restart] ✅ Server bereit — starte Eval...")

    eval_path = _HERE / "evaluation.py"
    if not eval_path.exists():
        print("[eval-after-restart] evaluation.py nicht gefunden — abgebrochen.")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("evaluation", eval_path)
    ev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)

    result = ev.run(PROJECT, trigger="restart")
    print(ev.format_terminal(result))

    if number:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        history_block = _format_history_block(PROJECT)
        body = (
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

    _dashboard_event("eval-after-restart")


def _ast_diff(old_content: str, new_content: str) -> list[str]:
    """
    Vergleicht AST-Skelette zweier Dateiversionen.

    Returns:
        Liste von menschenlesbaren Diff-Zeilen:
            "+ neu: func_name (Zeilen X-Y)"
            "- entfernt: func_name"
            "~ gewachsen: func_name (45→78 Zeilen)"
            "~ geschrumpft: func_name (78→45 Zeilen)"
    """
    def _sym_map(content: str) -> dict[str, dict]:
        syms = _extract_ast_symbols(content)
        return {s["name"]: s for s in syms}

    old_map = _sym_map(old_content)
    new_map = _sym_map(new_content)
    diffs = []

    for name, sym in new_map.items():
        if name not in old_map:
            diffs.append(f"+ neu: `{name}` ({sym['lines']} Zeilen)")
        else:
            old_sym = old_map[name]
            def _len(s: dict) -> int:
                parts = s.get("lines", "1-1").split("-")
                try:
                    return int(parts[1]) - int(parts[0]) + 1
                except (ValueError, IndexError):
                    return 0
            old_len, new_len = _len(old_sym), _len(sym)
            if new_len > old_len + 5:
                diffs.append(f"~ gewachsen: `{name}` ({old_len}→{new_len} Zeilen)")
            elif old_len > new_len + 5:
                diffs.append(f"~ geschrumpft: `{name}` ({old_len}→{new_len} Zeilen)")

    for name in old_map:
        if name not in new_map:
            diffs.append(f"- entfernt: `{name}`")

    return diffs


def _gitea_version_compare(commit: str, changed_files: list[str]) -> str:
    """
    Lädt relevante Dateiversionen vor dem Commit und vergleicht AST-Skelette.

    Liest agent_eval.json auf "gitea_version_compare.enabled".
    Deaktiviert per Default.

    Args:
        commit:        Commit-Hash (kurz oder lang)
        changed_files: Liste geänderter .py-Dateien (relativ zum PROJECT)

    Returns:
        Markdown-Block mit AST-Diff oder "" wenn deaktiviert/kein Diff.
    """
    # Konfiguration prüfen
    eval_cfg_path = evaluation._resolve_config(PROJECT)
    if not eval_cfg_path.exists():
        return ""
    try:
        cfg = json.loads(eval_cfg_path.read_text(encoding="utf-8"))
        vc_cfg = cfg.get("gitea_version_compare", {})
        if not vc_cfg.get("enabled", False):
            return ""
        base_ref = vc_cfg.get("base_ref", "main")
    except Exception:
        return ""

    py_files = [f for f in changed_files if f.endswith(".py")]
    if not py_files:
        return ""

    diff_lines: list[str] = []
    for rel_path in py_files[:5]:  # max 5 Dateien
        try:
            old_content = gitea.get_file_contents(rel_path, base_ref)
            new_content = gitea.get_file_contents(rel_path, commit)
            if not old_content or not new_content:
                continue
            file_diffs = _ast_diff(old_content, new_content)
            if file_diffs:
                diff_lines.append(f"**{rel_path}:**")
                diff_lines.extend(f"  {d}" for d in file_diffs)
        except Exception as e:
            log.debug(f"Version compare fehlgeschlagen für {rel_path}: {e}")

    if not diff_lines:
        return ""

    return (
        "\n\n### Struktureller AST-Diff (`" + base_ref + "` → `" + commit[:8] + "`)\n"
        + "\n".join(diff_lines)
    )


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
            (i + 1 for i, s in enumerate(failed.step_details) if not s.get("passed")),
            total,
        )
        lines.append(f"**Step {failed_step_idx}/{total} fehlgeschlagen**")
        lines.append("")
        lines.append("| Schritt | Nachricht | Erwartet | Ergebnis |")
        lines.append("|---------|-----------|----------|----------|")
        for i, s in enumerate(failed.step_details, start=1):
            msg = s.get("msg", "")[:60]
            stored = s.get("stored", False)
            expected = (
                ", ".join(s.get("expected", []))
                if s.get("expected")
                else "(gespeichert)"
            )
            actual = s.get("actual") or "—"
            actual = str(actual)[:80]
            icon = "✅" if s.get("passed") else "❌"
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
    hist_path = evaluation._resolve_path(
        PROJECT, "score_history.json", evaluation.SCORE_HISTORY
    )
    if hist_path.exists():
        try:
            with hist_path.open(encoding="utf-8") as f:
                hist = json.load(f)
            recent3 = hist[-3:][::-1]
            lines.append("**Letzte 3 Scores:**")
            lines.append("```")
            for e in recent3:
                ts = e.get("timestamp", "?")[:16].replace("T", " ")
                score = int(e.get("score", 0))
                max_s = int(e.get("max_score", 0))
                trigger = e.get("trigger", "?")
                passed = "✓" if e.get("passed") else "✗"
                lines.append(f"{ts} | {score}/{max_s} | {trigger:<6} | {passed}")
            lines.append("```")
            lines.append("")
        except Exception:
            pass

    lines.append("> Automatisch erkannt durch Watch-Modus.")
    lines.append("> Wird automatisch geschlossen wenn der Test wieder besteht.")

    # AST-Diff anhängen (wenn gitea_version_compare aktiviert)
    commit_hash = commit.split()[0] if commit else ""
    if commit_hash:
        try:
            changed_files = (
                subprocess.check_output(
                    ["git", "diff", "--name-only", f"{commit_hash}^", commit_hash],
                    cwd=PROJECT, stderr=subprocess.DEVNULL,
                ).decode().splitlines()
            )
            ast_diff_block = _gitea_version_compare(commit_hash, changed_files)
            if ast_diff_block:
                lines.append(ast_diff_block)
        except Exception as e:
            log.debug(f"AST-Diff in auto issue fehlgeschlagen: {e}")

    return "\n".join(lines)


def cmd_watch(interval_minutes: int = 60, patch_mode: bool = False) -> None:
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
    _sync_closed_contexts()

    while True:
        ts = time.strftime("%H:%M:%S")

        try:
            if not settings.FEATURES.get("eval", True):
                print(f"[{ts}] Eval deaktiviert (project.json: eval=false) — übersprungen")
                result = evaluation.EvalResult()
                result.skipped = True
            else:
                print(f"[{ts}] Eval läuft...")
                result = evaluation.run(PROJECT, trigger="watch")
                print(evaluation.format_terminal(result))

            if not result.skipped and not result.warned:
                try:
                    dashboard.generate(PROJECT)
                except Exception as e:
                    pass

                if not patch_mode and settings.FEATURES.get("auto_issues", True):
                    _close_resolved_auto_issues(result)

                for t in result.all_tests:
                    if patch_mode:
                        continue
                    if not settings.FEATURES.get("auto_issues", True):
                        continue
                    if t.skipped:
                        continue
                        
                    # 1. Funktionale Regression (Score Verlust)
                    if not t.passed:
                        if _auto_issue_exists(t.name):
                            log.debug(f"[Auto]-Issue für '{t.name}' bereits offen — kein Duplikat")
                        else:
                            try:
                                commit = subprocess.check_output(["git", "log", "-1", "--pretty=%h %s"], cwd=PROJECT, stderr=subprocess.DEVNULL).decode().strip()
                            except Exception:
                                commit = "unbekannt"
                            body = _build_auto_issue_body(t, result, commit, "")
                            _validate_comment(body, "auto_issue")
                            issue = gitea.create_issue(
                                title=f"[Auto] {t.name} fehlgeschlagen — Score-Verlust erkannt",
                                body=body,
                                label=settings.LABEL_READY,
                            )
                            log.warning(f"Auto-Issue erstellt: #{issue['number']} für '{t.name}'")
                            print(f"[!] Auto-Issue erstellt: #{issue['number']} — {t.name}")
                            _dashboard_event("Auto-Issue erstellt")

                    # 2. Performance Regression
                    if t.max_response_ms is not None and t.response_ms > t.max_response_ms:
                        if _auto_perf_issue_exists(t.name):
                            log.debug(f"[Auto-Perf]-Issue für '{t.name}' bereits offen — kein Duplikat")
                        else:
                            try:
                                commit = subprocess.check_output(["git", "log", "-1", "--pretty=%h %s"], cwd=PROJECT, stderr=subprocess.DEVNULL).decode().strip()
                            except Exception:
                                commit = "unbekannt"
                            body = f"Performance-Regression im Test **{t.name}**.\nErlaubte Zeit: {t.max_response_ms}ms\nGemessene Zeit: **{t.response_ms}ms**\n\nBitte prüfen."
                            _validate_comment(body, "auto_issue")
                            issue = gitea.create_issue(
                                title=f"[Auto-Perf] {t.name} Latenz überschritten",
                                body=body,
                                label=settings.LABEL_READY,
                            )
                            log.warning(f"Auto-Perf Issue erstellt: #{issue['number']} für '{t.name}'")
                            print(f"[!] Auto-Perf Issue erstellt: #{issue['number']} — {t.name}")
                            _dashboard_event("Auto-Perf-Issue erstellt")

        except Exception as e:
            log.error(f"Watch-Lauf Fehler: {e}")
            print(f"[!] Fehler in Watch-Lauf: {e}")

        # Skelett inkrementell aktualisieren (nach jedem Eval-Zyklus)
        try:
            changed_out = subprocess.check_output(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                cwd=PROJECT, stderr=subprocess.DEVNULL
            ).decode().strip()
            if changed_out:
                _update_skeleton_incremental(changed_out.splitlines())
        except Exception as e:
            log.debug(f"Skelett-Update übersprungen: {e}")

        if not patch_mode:
            _check_systematic_tag_failures(PROJECT)

        # Optionaler Log-Analyzer: neue Struktur (agent/config/) oder Legacy (tools/)
        analyzer_path = (
            settings.LOG_ANALYZER_PATH
            if settings.LOG_ANALYZER_PATH and settings.LOG_ANALYZER_PATH.exists()
            else PROJECT / "tools" / "log_analyzer.py"
        )
        if analyzer_path.exists():
            try:
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "log_analyzer", analyzer_path
                )
                la = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(la)
                la_result = la.run()
                print(la.format_terminal(la_result))
            except Exception as e:
                log.warning(f"Log-Analyzer Fehler: {e}")
                print(f"[!] Log-Analyzer Fehler: {e}")

        # Szenario 2: Automatischer Neustart bei Chat-Inaktivität + neuen Commits
        eval_cfg = evaluation._load_config(PROJECT) or {}
        restart_sc = eval_cfg.get("restart_script")
        log_path = eval_cfg.get("log_path")
        threshold = eval_cfg.get("inactivity_minutes", 5)
        if restart_sc and log_path:
            inactive = _last_chat_inactive_minutes(log_path)
            if patch_mode or (inactive is not None and inactive >= threshold):
                inactive_str = f"{inactive:.1f}min" if inactive is not None else "N/A"
                if _has_new_commits_since_last_eval(PROJECT):
                    print(
                        f"[Watch] Chat inaktiv ({inactive_str}) + neue Commits → Neustart (Patch: {patch_mode})"
                    )
                    log.info(f"Szenario 2: Neustart via {restart_sc}")
                    subprocess.run([restart_sc], check=False)
                    cmd_eval_after_restart()

        # ── Self-Healing (plugins/healing.py) ───────────────────────────
        if settings.FEATURES.get("healing", False) and not result.skipped:
            if not result.passed and result.failed_tests:
                try:
                    from plugins.healing import run_healing_loop, format_terminal as heal_fmt
                    eval_cfg_h = evaluation._load_config(PROJECT) or {}
                    log_path_h = eval_cfg_h.get("log_path", "")
                    log_excerpt_h = ""
                    if log_path_h:
                        try:
                            log_lines = Path(log_path_h).read_text(
                                encoding="utf-8", errors="replace"
                            ).splitlines()[-30:]
                            log_excerpt_h = "\n".join(log_lines)
                        except Exception:
                            pass
                    for t in result.failed_tests[:1]:  # max. 1 pro Watch-Zyklus
                        hr = run_healing_loop(
                            project_root=PROJECT,
                            test_name=t.name,
                            test_reason=getattr(t, "reason", ""),
                            log_excerpt=log_excerpt_h,
                        )
                        print(heal_fmt(hr))
                        if hr.success:
                            log.info(f"Watch-Healing: {t.name} geheilt")
                            _dashboard_event("Self-Healing erfolgreich")
                except Exception as e:
                    log.warning(f"Self-Healing Fehler: {e}")

        print(f"    Nächster Lauf in {interval_minutes} Minute(n)...\n")
        time.sleep(interval_minutes * 60)


# ---------------------------------------------------------------------------
# Dashboard-Event-Helper
# ---------------------------------------------------------------------------


def _dashboard_event(context: str = "") -> None:
    """Dashboard nach signifikantem Event sofort aktualisieren."""
    try:
        dashboard.generate(PROJECT)
        if context:
            log.debug(f"Dashboard aktualisiert ({context})")
    except Exception as e:
        log.warning(f"Dashboard-Update fehlgeschlagen ({context}): {e}")


# ---------------------------------------------------------------------------
# Service-Installation
# ---------------------------------------------------------------------------

_UNIT_TEMPLATE = """\
[Unit]
Description=gitea-agent {mode} mode
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={workdir}
ExecStart={python} {agent_start} --watch{patch_flag}
Restart=on-failure
RestartSec=30
Environment=PATH={path}

[Install]
WantedBy=multi-user.target
"""


def cmd_install_service() -> None:
    """Installiert die systemd-Units gitea-agent-night und gitea-agent-patch."""
    import getpass

    user = getpass.getuser()
    python = sys.executable
    agent_start = str(_HERE / "agent_start.py")
    workdir = str(_HERE)
    path = os.environ.get("PATH", "/usr/bin:/bin")

    units = {
        "gitea-agent-night": _UNIT_TEMPLATE.format(
            mode="night", user=user, workdir=workdir,
            python=python, agent_start=agent_start,
            patch_flag="", path=path,
        ),
        "gitea-agent-patch": _UNIT_TEMPLATE.format(
            mode="patch", user=user, workdir=workdir,
            python=python, agent_start=agent_start,
            patch_flag=" --patch", path=path,
        ),
    }

    for name, content in units.items():
        unit_path = Path(f"/etc/systemd/system/{name}.service")
        print(f"[→] Schreibe {unit_path}")
        try:
            unit_path.write_text(content, encoding="utf-8")
        except PermissionError:
            print(f"[!] Keine Schreibrechte — versuche mit sudo...")
            subprocess.run(
                ["sudo", "tee", str(unit_path)],
                input=content.encode(),
                stdout=subprocess.DEVNULL,
                check=True,
            )
        print(f"[✓] {name}.service installiert")

    subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
    print("[✓] systemd daemon-reload")
    print()
    print("Nutzung:")
    print("  start_night.sh  → Night-Modus starten")
    print("  start_patch.sh  → Patch-Modus starten")
    print("  stop_agent.sh   → Alles stoppen")
    print("  agent_status.sh → Status anzeigen")


# ---------------------------------------------------------------------------
# Auto-Modus
# ---------------------------------------------------------------------------


def cmd_dashboard() -> None:
    print(f"[→] Generiere Live-Dashboard...")
    try:
        dashboard.generate(PROJECT)
        print(f"[✓] Dashboard erfolgreich erstellt: {settings.DASHBOARD_PATH}")
    except Exception as e:
        print(f"[!] Fehler bei Dashboard-Generierung: {e}")

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
                num = int(idir.name.split("-")[0])
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
        key=lambda x: risk_level(x)[0],
    )
    if approved:
        print(
            f"\n[✓] {len(approved)} freigegebene Issue(s) — starte Implementierung:\n"
        )
        for issue in approved:
            log.info(f"Implementiere Issue #{issue['number']}: {issue['title'][:60]}")
            print(f"  → #{issue['number']} {issue['title'][:60]}")
            cmd_implement(issue["number"])
            print()
        did_something = True

    # Neue Issues planen
    ready = sorted(
        gitea.get_issues(label=settings.LABEL_READY), key=lambda x: risk_level(x)[0]
    )
    if ready:
        print(f"\n[→] {len(ready)} Issue(s) bereit — poste Pläne:\n")
        for issue in ready:
            stufe, _ = risk_level(issue)
            log.info(
                f"Plane Issue #{issue['number']} (Stufe {stufe}): {issue['title'][:55]}"
            )
            print(f"  → #{issue['number']} (Stufe {stufe}) {issue['title'][:55]}")
            cmd_plan(issue["number"])
            print()
        print(
            f"[→] Freigabe mit 'ok' kommentieren: {gitea.GITEA_URL}/{gitea.REPO}/issues"
        )
        did_something = True

    # Status-Übersicht
    in_progress = gitea.get_issues(label=settings.LABEL_PROGRESS)
    waiting = [
        i
        for i in proposed
        if not gitea.check_approval(i["number"], settings.LABEL_HELP)
    ]

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

    claude_dir = _HERE / ".claude"
    claude_dir.mkdir(exist_ok=True)
    target = claude_dir / "settings.local.json"

    if settings.AUTO_APPROVE:
        data = {
            "permissions": {
                "allow": [
                    "Bash(*)",
                    "Read(*)",
                    "Write(*)",
                    "Edit(*)",
                    "Glob(*)",
                    "Grep(*)",
                    "Agent(*)",
                    "WebFetch(*)",
                    "WebSearch(*)",
                ]
            }
        }
    else:
        data = {"permissions": {"allow": []}}

    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    log.debug(f"AUTO_APPROVE={'true' if settings.AUTO_APPROVE else 'false'} → {target}")


# ---------------------------------------------------------------------------
# Health-Check
# ---------------------------------------------------------------------------

def cmd_heal(test_name: str = "", log_lines: int = 30) -> None:
    """
    --heal: Startet den Autonomous Self-Healing Loop für einen fehlgeschlagenen Test.

    Ablauf:
      1. Eval ausführen → fehlgeschlagene Tests ermitteln
      2. Für jeden fehlgeschlagenen Test: Temp-Branch + LLM-Fix + Eval-Validierung
      3. Bei Erfolg: Cherry-Pick auf aktuellen Branch
      4. Bei Abbruch: Temp-Branch löschen + Gitea-Issue erstellen

    Erfordert LLM-Backend (CLAUDE_API_ENABLED=true oder lokale LLM via agent_eval.json).

    ⚠️ Risikostufe 4/4 — Autonome Schreibzyklen. Nur mit explizitem Feature-Flag nutzen.

    Aufgerufen von:
        main() wenn --heal gesetzt
    """
    from plugins.healing import run_healing_loop, format_terminal as heal_fmt

    if not settings.FEATURES.get("healing", False):
        print("[!] Self-Healing deaktiviert (project.json: healing=false)")
        print("    Aktivieren: healing=true in agent/config/project.json setzen")
        return

    print("[→] Self-Healing Loop gestartet\n")

    # Eval ausführen um fehlgeschlagene Tests zu ermitteln
    try:
        eval_result = evaluation.run(PROJECT, trigger="healing")
        failed = eval_result.failed_tests
        if not failed:
            print("[✅] Keine fehlgeschlagenen Tests — kein Heilungsbedarf")
            return
    except Exception as e:
        if test_name:
            # Fallback: Direkt mit übergebenem Test-Namen arbeiten
            failed = [type("T", (), {"name": test_name, "reason": "unbekannt", "tag": ""})()]
        else:
            print(f"[!] Eval fehlgeschlagen: {e}")
            return

    # Log-Auszug lesen
    eval_cfg = evaluation._load_config(PROJECT) or {}
    log_path_str = eval_cfg.get("log_path", "")
    log_excerpt = ""
    if log_path_str:
        try:
            lines = Path(log_path_str).read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()[-log_lines:]
            log_excerpt = "\n".join(lines)
        except Exception:
            pass

    # Healing-Loop für jeden fehlgeschlagenen Test (max. 3 Tests pro Aufruf)
    healed = 0
    failed_heals = []
    for t in failed[:3]:
        if test_name and t.name != test_name:
            continue
        print(f"[→] Heile Test: {t.name}")
        result = run_healing_loop(
            project_root=PROJECT,
            test_name=t.name,
            test_reason=getattr(t, "reason", ""),
            log_excerpt=log_excerpt,
        )
        print(heal_fmt(result))

        if result.success:
            healed += 1
            log.info(f"Self-Healing erfolgreich: {t.name} in {result.attempt_count} Versuch(en)")
        elif result.skipped:
            log.warning(f"Self-Healing übersprungen: {result.skip_reason}")
        else:
            failed_heals.append(result)
            # Gitea-Issue erstellen bei Abbruch
            if settings.FEATURES.get("auto_issues", True):
                body = (
                    f"**Healing-Loop fehlgeschlagen** für Test `{t.name}`.\n\n"
                    f"- Versuche: {result.attempt_count} / {result.attempt_count}\n"
                    f"- Token verbraucht: ~{result.tokens_total:,}\n"
                    + "\n".join(
                        f"- Versuch {a.attempt_no}: {a.error or a.fix_description}"
                        for a in result.attempts
                    )
                    + "\n\nManueller Eingriff erforderlich."
                )
                try:
                    issue = gitea.create_issue(
                        title=f"[Healing] Loop fehlgeschlagen — {t.name}",
                        body=body,
                        label=settings.LABEL_HELP,
                    )
                    print(f"[!] Healing-Issue erstellt: #{issue['number']}")
                    log.warning(f"Healing-Issue erstellt: #{issue['number']}")
                except Exception as exc:
                    log.warning(f"Healing-Issue konnte nicht erstellt werden: {exc}")

    print(f"\n[Healing] Abgeschlossen: {healed} geheilt, {len(failed_heals)} fehlgeschlagen")


def cmd_doctor() -> None:
    """--doctor: Vollständigen Zustand des Agents prüfen und Report ausgeben."""
    import datetime as _dt

    checks: list[dict] = []

    def _chk(name: str, status: str, detail: str = "", fix: str = "") -> None:
        checks.append({"name": name, "status": status, "detail": detail, "fix": fix})

    # 1. Gitea-Verbindung
    try:
        info = gitea._request("GET", f"/repos/{gitea.REPO}") or {}
        _chk("Gitea-Verbindung", "ok", f"{gitea.GITEA_URL} → {info.get('full_name','?')}")
    except Exception as exc:
        _chk("Gitea-Verbindung", "fail", str(exc), "GITEA_URL / GITEA_TOKEN prüfen")

    # 2. Projekt-Verzeichnis
    proj = settings.PROJECT_ROOT
    if proj and Path(proj).is_dir():
        if (Path(proj) / ".git").exists():
            _chk("Projekt-Verzeichnis", "ok", str(proj))
        else:
            _chk("Projekt-Verzeichnis", "warn", f"{proj} ist kein git-Repo", "git init oder PROJECT_ROOT korrigieren")
    else:
        _chk("Projekt-Verzeichnis", "fail", str(proj), "PROJECT_ROOT in .env setzen")

    # 3. repo_skeleton.json
    skel = PROJECT / "repo_skeleton.json"
    if skel.exists():
        size = skel.stat().st_size
        _chk("repo_skeleton.json", "ok", f"{size} Bytes")
    else:
        _chk("repo_skeleton.json", "warn", "Nicht vorhanden",
             "python3 agent_start.py --build-skeleton ausführen")

    # 4. agent_eval.json (neue Struktur: agent/config/, Fallback: tests/)
    eval_cfg = (PROJECT / "agent" / "config" / "agent_eval.json"
                if (PROJECT / "agent" / "config" / "agent_eval.json").exists()
                else PROJECT / "tests" / "agent_eval.json")
    if eval_cfg.exists():
        try:
            with eval_cfg.open(encoding="utf-8") as f:
                cfg = json.load(f)
            _chk("agent_eval.json", "ok", f"server_url={cfg.get('server_url','?')}")
        except Exception as exc:
            _chk("agent_eval.json", "warn", f"Ungültig: {exc}", "agent_eval.json reparieren")
    else:
        _chk("agent_eval.json", "warn", "Nicht vorhanden",
             "python3 agent_start.py --setup oder manuell erstellen")

    # 5. Labels
    required = {settings.LABEL_READY, settings.LABEL_PROPOSED,
                settings.LABEL_PROGRESS, settings.LABEL_REVIEW, settings.LABEL_HELP}
    try:
        existing = set(gitea.get_all_labels().keys())
        missing = required - existing
        if missing:
            _chk("Labels", "warn", f"Fehlend: {', '.join(sorted(missing))}",
                 "python3 agent_start.py --setup ausführen")
        else:
            _chk("Labels", "ok", f"Alle {len(required)} vorhanden")
    except Exception as exc:
        _chk("Labels", "fail", str(exc), "Gitea-Verbindung prüfen")

    # 6. .env
    env_file = PROJECT / ".env"
    if env_file.exists():
        _chk(".env", "ok", str(env_file))
    else:
        _chk(".env", "fail", ".env fehlt", "cp .env.example .env && python3 agent_start.py --setup")

    # Ausgabe
    summary = {"ok": 0, "warn": 0, "fail": 0}
    for c in checks:
        summary[c["status"]] = summary.get(c["status"], 0) + 1

    _ICONS = {"ok": "✅", "warn": "⚠️", "fail": "❌"}
    print(f"\n{'═' * 60}")
    print("  gitea-agent Health-Check")
    print(f"{'═' * 60}")
    for c in checks:
        icon = _ICONS.get(c["status"], "?")
        print(f"  {icon}  {c['name']:<25} {c['detail']}")
        if c["fix"] and c["status"] != "ok":
            print(f"       → {c['fix']}")
    print(f"{'─' * 60}")
    print(f"  ✅ {summary['ok']}  ⚠️  {summary['warn']}  ❌ {summary['fail']}")

    # Feature-Flags anzeigen
    feat_on  = [k for k, v in settings.FEATURES.items() if v]
    feat_off = [k for k, v in settings.FEATURES.items() if not v]
    if feat_off:
        print(f"\n  Features aktiv:      {', '.join(feat_on)}")
        print(f"  Features deaktiviert: {', '.join(feat_off)}")
    else:
        print(f"\n  Features: alle aktiv ({', '.join(feat_on)})")
    print(f"  Projekttyp: {settings.PROJECT_TYPE}")
    print()

    # Ergebnis speichern
    result = {
        "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "checks": checks,
    }
    out = getattr(settings, "DOCTOR_RESULT_PATH", None)
    if out:
        try:
            Path(out).write_text(json.dumps(result, indent=2, ensure_ascii=False),
                                 encoding="utf-8")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Setup-Wizard
# ---------------------------------------------------------------------------

def cmd_setup() -> None:
    """--setup: Interaktiver Einrichtungs-Wizard für neue Projekte (Issue #77)."""
    import base64

    def _ask(prompt: str, default: str = "") -> str:
        disp = f" [{default}]" if default else ""
        val = input(f"  {prompt}{disp}: ").strip()
        return val or default

    def _api_get_raw(url, user, token, path):
        import urllib.request, urllib.error
        req = urllib.request.Request(
            f"{url.rstrip('/')}/api/v1{path}",
            headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())

    def _api_post_raw(url, user, token, path, data: dict):
        import urllib.request
        payload = json.dumps(data).encode()
        req = urllib.request.Request(
            f"{url.rstrip('/')}/api/v1{path}",
            data=payload,
            headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())

    print(f"\n{'═' * 60}")
    print("  gitea-agent Setup-Wizard")
    print(f"{'═' * 60}\n")

    # ── Schritt 1: Gitea-Verbindung ────────────────────────────────
    print("Schritt 1/6 — Gitea-Verbindung\n")
    gitea_url   = _ask("Gitea URL (z.B. http://192.168.1.x:3001)")
    gitea_user  = _ask("Gitea Benutzername")
    gitea_token = _ask("Gitea API-Token")
    bot_user    = _ask("Bot-User (leer = kein Bot)", "")
    bot_token   = _ask("Bot-Token (leer = kein Bot)", "") if bot_user else ""

    try:
        _api_get_raw(gitea_url, gitea_user, gitea_token, "/user")
        print("  ✅ Verbindung erfolgreich\n")
    except Exception as exc:
        print(f"  ❌ Verbindungsfehler: {exc}")
        print("  ⚠️  Fortfahren trotz Fehler?\n")

    # ── Schritt 2: Repository ──────────────────────────────────────
    print("Schritt 2/6 — Repository\n")
    gitea_repo = _ask("Repository (user/name, z.B. admin/myproject)")
    try:
        _api_get_raw(gitea_url, gitea_user, gitea_token, f"/repos/{gitea_repo}")
        print("  ✅ Repository gefunden\n")
    except Exception as exc:
        print(f"  ❌ Repo nicht gefunden: {exc}\n")

    # ── Schritt 3: Projektverzeichnis ─────────────────────────────
    print("Schritt 3/6 — Projektverzeichnis\n")
    project_root = _ask("Lokaler Pfad zum Projekt-Repo")
    if Path(project_root).is_dir():
        if (Path(project_root) / ".git").exists():
            print("  ✅ git-Repo gefunden\n")
        else:
            print("  ⚠️  Kein git-Repo — PROJECT_ROOT trotzdem gesetzt\n")
    else:
        print("  ❌ Verzeichnis existiert nicht\n")

    # ── Schritt 4: Labels ─────────────────────────────────────────
    print("Schritt 4/6 — Labels\n")
    required_labels = [
        (settings.LABEL_READY,    "0075ca", "Bereit für Agent-Bearbeitung"),
        (settings.LABEL_PROPOSED, "e4e669", "Agent hat Plan vorgeschlagen"),
        (settings.LABEL_PROGRESS, "d93f0b", "Agent arbeitet daran"),
        (settings.LABEL_REVIEW,   "0e8a16", "Bereit für Code-Review"),
        (settings.LABEL_HELP,     "ee0701", "Manuelle Hilfe benötigt"),
    ]

    try:
        existing_resp = _api_get_raw(gitea_url, gitea_user, gitea_token,
                                     f"/repos/{gitea_repo}/labels")
        existing_names = {lbl["name"] for lbl in existing_resp}
        missing = [(n, c, d) for n, c, d in required_labels if n not in existing_names]

        if not missing:
            print(f"  ✅ Alle {len(required_labels)} Labels bereits vorhanden\n")
        else:
            print(f"  Fehlende Labels: {', '.join(n for n,_,_ in missing)}")
            confirm = input("  Jetzt anlegen? [J/n]: ").strip().lower()
            if confirm in ("", "j", "y"):
                for name, color, desc in missing:
                    _api_post_raw(gitea_url, gitea_user, gitea_token,
                                  f"/repos/{gitea_repo}/labels",
                                  {"name": name, "color": f"#{color}", "description": desc})
                    print(f"  ✅ Label '{name}' angelegt")
            print()
    except Exception as exc:
        print(f"  ❌ Label-Prüfung fehlgeschlagen: {exc}\n")

    # ── Schritt 5: agent_eval.json ────────────────────────────────
    print("Schritt 5/6 — agent_eval.json\n")
    eval_file = PROJECT / "tests" / "agent_eval.json"
    write_eval = True
    if eval_file.exists():
        confirm = input(f"  {eval_file} existiert bereits — überschreiben? [j/N]: ").strip().lower()
        write_eval = confirm in ("j", "y")

    if write_eval:
        server_url  = _ask("Server-URL für Eval (z.B. http://localhost:8080)")
        log_path    = _ask("Log-Pfad (z.B. /home/user/llm-chat/gitea-agent.log)")
        start_script = _ask("Start-Script (z.B. /home/user/start_llm.sh)", "")
        eval_data = {
            "server_url": server_url,
            "log_path": log_path,
            "start_script": start_script,
            "watch_interval_minutes": 60,
        }
        eval_file.parent.mkdir(parents=True, exist_ok=True)
        eval_file.write_text(json.dumps(eval_data, indent=2), encoding="utf-8")
        print(f"  ✅ {eval_file} geschrieben\n")
    else:
        print("  Übersprungen\n")

    # ── Schritt 6: .env schreiben ─────────────────────────────────
    print("Schritt 6/6 — .env\n")
    env_file = PROJECT / ".env"
    write_env = True
    if env_file.exists():
        confirm = input(f"  {env_file} existiert bereits — überschreiben? [j/N]: ").strip().lower()
        write_env = confirm in ("j", "y")

    if write_env:
        env_lines = [
            f"GITEA_URL={gitea_url}",
            f"GITEA_USER={gitea_user}",
            f"GITEA_TOKEN={gitea_token}",
            f"GITEA_REPO={gitea_repo}",
            f"GITEA_BOT_USER={bot_user}",
            f"GITEA_BOT_TOKEN={bot_token}",
            f"PROJECT_ROOT={project_root}",
        ]
        env_file.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
        print(f"  ✅ .env geschrieben: {env_file}")
        print("  ⚠️  .env enthält Secrets — nicht in Git commiten!\n")
    else:
        print("  Übersprungen\n")

    # ── Schritt 7: Projekttyp + Feature-Flags ──────────────────────
    print("Schritt 7/7 — Projekttyp & Feature-Flags\n")
    print("  Projekttypen:")
    print("    1) web_api    — REST-API / Web-Server")
    print("    2) llm_chat   — LLM-Chat mit Eval-Tests")
    print("    3) cli_tool   — Kommandozeilen-Tool")
    print("    4) library    — Python-Bibliothek")
    print("    5) custom     — Eigene Konfiguration")
    type_map = {"1": "web_api", "2": "llm_chat", "3": "cli_tool", "4": "library", "5": "custom"}
    type_choice = _ask("Projekttyp (1-5)", "1")
    proj_type = type_map.get(type_choice, "custom")

    feature_defaults = {
        "web_api":  {"eval": True,  "health_checks": True,  "auto_issues": True,  "changelog": True, "watch": True,  "pr_workflow": True},
        "llm_chat": {"eval": True,  "health_checks": True,  "auto_issues": True,  "changelog": True, "watch": True,  "pr_workflow": True},
        "cli_tool": {"eval": False, "health_checks": False, "auto_issues": True,  "changelog": True, "watch": False, "pr_workflow": True},
        "library":  {"eval": False, "health_checks": False, "auto_issues": True,  "changelog": True, "watch": False, "pr_workflow": True},
        "custom":   {"eval": True,  "health_checks": False, "auto_issues": True,  "changelog": True, "watch": True,  "pr_workflow": True},
    }
    features = feature_defaults.get(proj_type, feature_defaults["custom"])
    print(f"\n  Voreinstellungen für '{proj_type}':")
    for k, v in features.items():
        print(f"    {k:<15} {'✅ aktiv' if v else '❌ deaktiviert'}")

    confirm = _ask("\n  Features übernehmen? (ja/nein)", "ja")
    if confirm.lower() not in ("ja", "j", "yes", "y"):
        print("  Manuelle Konfiguration: project.json nach agent/config/ kopieren und anpassen.")
    else:
        project_json = {
            "type": proj_type,
            "features": features,
        }
        agent_config = Path(project_root) / "agent" / "config"
        agent_config.mkdir(parents=True, exist_ok=True)
        proj_file = agent_config / "project.json"
        if proj_file.exists():
            overwrite = _ask(f"  project.json existiert bereits. Überschreiben? (ja/nein)", "nein")
            if overwrite.lower() not in ("ja", "j", "yes", "y"):
                print("  Übersprungen\n")
                proj_file = None
        if proj_file:
            proj_file.write_text(json.dumps(project_json, indent=4, ensure_ascii=False), encoding="utf-8")
            print(f"  ✅ project.json geschrieben: {proj_file}\n")

    # ── Health-Check zum Abschluss ────────────────────────────────
    print(f"{'═' * 60}")
    print("  SETUP ABGESCHLOSSEN — starte Health-Check...\n")
    cmd_doctor()


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
        """,
    )
    parser.add_argument(
        "--build-skeleton",
        action="store_true",
        dest="build_skeleton",
        help="Projekt-weites repo_skeleton.json erstellen",
    )
    parser.add_argument(
        "--generate-tests",
        type=int,
        metavar="NR",
        help="Tests basierend auf Issue generieren",
    )
    parser.add_argument(
        "--list", action="store_true", help="Alle ready-for-agent Issues auflisten"
    )
    parser.add_argument("--issue", type=int, metavar="NR", help="Plan für Issue posten")
    parser.add_argument(
        "--get-slice",
        type=str,
        metavar="DATEI:START-END",
        dest="get_slice",
        help="Exakten Zeilenbereich ausgeben, z.B. agent_start.py:45-90",
    )
    parser.add_argument(
        "--apply-patch",
        type=int,
        metavar="NR",
        dest="apply_patch",
        help="SEARCH/REPLACE-Blöcke aus Issue-Kommentar anwenden",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Mit --apply-patch: Patch prüfen ohne zu schreiben",
    )
    parser.add_argument(
        "--implement",
        type=int,
        metavar="NR",
        help="Nach OK: Branch + Implementierungskontext",
    )
    parser.add_argument(
        "--fixup",
        type=int,
        metavar="NR",
        help="Nach Bugfix: Kommentar + needs-review setzen",
    )
    parser.add_argument(
        "--pr", type=int, metavar="NR", help="PR erstellen (mit --branch)"
    )
    parser.add_argument(
        "--branch", type=str, metavar="BRANCH", help="Branch-Name für --pr"
    )
    parser.add_argument(
        "--summary",
        type=str,
        metavar="TEXT",
        help="Zusammenfassung für Issue-Kommentar",
        default="",
    )

    parser.add_argument(
        "--patch",
        action="store_true",
        help="Aktiviert den Patch-Modus im Watch-Loop (unterdrückt Auto-Issues, ignoriert Inaktivität)",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Generiert das Live-Dashboard manuell",
    )
    parser.add_argument(
        "--watch", action="store_true", help="Periodischer Eval-Loop mit Auto-Issues"
    )
    parser.add_argument(
        "--interval",
        type=int,
        metavar="MIN",
        help="Interval für --watch in Minuten (überschreibt watch_interval_minutes aus agent_eval.json)",
        default=None,
    )
    parser.add_argument(
        "--eval-after-restart",
        type=int,
        metavar="NR",
        help="Nach Neustart: Eval ausführen + Score ins Issue (NR optional)",
        nargs="?",
        const=0,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Staleness-Check vor Eval überspringen (--pr)",
    )
    parser.add_argument(
        "--restart-before-eval",
        action="store_true",
        help="Server via restart_script neu starten vor Eval (--pr)",
    )
    parser.add_argument(
        "--self",
        action="store_true",
        help="gitea-agent Eigenentwicklung: lädt .env.agent statt .env",
    )
    parser.add_argument(
        "--install-service",
        action="store_true",
        help="Systemd-Units für Night- und Patch-Modus installieren",
    )
    parser.add_argument(
        "--changelog",
        nargs="?",
        const="Unreleased",
        metavar="VERSION",
        help="CHANGELOG.md generieren/aktualisieren (z.B. --changelog 1.2.0)",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Health-Check: Vollständigen Zustand des Agents prüfen und Report ausgeben",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Interaktiver Einrichtungs-Wizard für neue Projekte",
    )
    parser.add_argument(
        "--heal",
        metavar="TEST",
        nargs="?",
        const="",
        help="Autonomous Self-Healing Loop: fehlgeschlagenen Test autonom fixen (erfordert LLM)",
    )
    args = parser.parse_args()

    if args.setup:
        cmd_setup()
    elif args.doctor:
        cmd_doctor()
    elif args.build_skeleton:
        cmd_build_skeleton()
    elif args.install_service:
        cmd_install_service()
    elif args.eval_after_restart is not None:
        nr = args.eval_after_restart if args.eval_after_restart != 0 else None
        cmd_eval_after_restart(nr)
    elif args.list:
        cmd_list()
    elif args.get_slice:
        cmd_get_slice(args.get_slice)
    elif args.apply_patch:
        cmd_apply_patch(args.apply_patch, dry_run=args.dry_run)
    elif args.issue:
        cmd_plan(args.issue)
    elif args.implement:
        cmd_implement(args.implement)
    elif args.generate_tests:
        cmd_generate_tests(args.generate_tests)
    elif args.fixup:
        cmd_fixup(args.fixup)
    elif args.heal is not None:
        cmd_heal(test_name=args.heal or "")
    elif args.dashboard:
        cmd_dashboard()
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
        cmd_watch(interval, patch_mode=args.patch)
    elif args.pr:
        if not args.branch:
            log.error("--pr benötigt --branch <branch-name>")
            print("[✗] --pr benötigt --branch <branch-name>")
            sys.exit(1)
        cmd_pr(
            args.pr,
            args.branch,
            args.summary,
            force=args.force,
            restart_before_eval=args.restart_before_eval,
        )
    elif args.changelog is not None:
        cmd_changelog(version=args.changelog if args.changelog != "Unreleased" else None)
    else:
        cmd_auto()


if __name__ == "__main__":
    main()
