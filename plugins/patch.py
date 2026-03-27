"""plugins/patch.py — SEARCH/REPLACE Protokoll (Issue #58)."""

import ast
import sys
from pathlib import Path

_HERE = Path(__file__).parent.parent  # gitea-agent/
sys.path.insert(0, str(_HERE))

class _LazyGitea:
    _mod = None

    def __getattr__(self, name: str):
        if self.__class__._mod is None:
            import gitea_api
            self.__class__._mod = gitea_api
        return getattr(self.__class__._mod, name)

gitea = _LazyGitea()  # noqa: E402
import settings  # noqa: E402
from log import get_logger  # noqa: E402

log = get_logger(__name__)


def _project_root() -> Path:
    if settings.PROJECT_ROOT:
        p = Path(settings.PROJECT_ROOT)
        if p.exists():
            return p
    return _HERE.parent


PROJECT = _project_root()

_SR_SEARCH = "<<<<<<< SEARCH"
_SR_SEP    = "======="
_SR_REPLACE = ">>>>>>> REPLACE"


def _normalize_ws(text: str) -> str:
    """Whitespace-Normalisierung: trailing spaces + CRLF → LF."""
    return "\n".join(l.rstrip() for l in text.splitlines())


def _parse_search_replace(text: str) -> list[dict]:
    """
    Parst SEARCH/REPLACE-Blöcke aus einem Text.

    Format:
        ## datei.py
        <<<<<<< SEARCH
        [alter Code]
        =======
        [neuer Code]
        >>>>>>> REPLACE

    Returns:
        Liste von {"file": str, "search": str, "replace": str}
    """
    patches = []
    current_file: str | None = None
    state = "idle"
    search_lines: list[str] = []
    replace_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.rstrip()
        # Datei-Header: ## path/to/file.py
        if state == "idle" and stripped.startswith("## ") and stripped.endswith(".py"):
            current_file = stripped[3:].strip()
        elif stripped == _SR_SEARCH and current_file:
            state = "search"
            search_lines = []
        elif stripped == _SR_SEP and state == "search":
            state = "replace"
            replace_lines = []
        elif stripped == _SR_REPLACE and state == "replace":
            patches.append({
                "file": current_file,
                "search": "\n".join(search_lines),
                "replace": "\n".join(replace_lines),
            })
            state = "idle"
            search_lines = []
            replace_lines = []
        elif state == "search":
            search_lines.append(line)
        elif state == "replace":
            replace_lines.append(line)

    return patches


def _apply_patch(
    patch: dict, dry_run: bool = False
) -> tuple[bool, str]:
    """
    Wendet einen einzelnen SEARCH/REPLACE-Patch auf eine Datei an.

    Sicherheits-Kette:
        1. SEARCH matcht exakt (mit Whitespace-Normalisierung)
        2. REPLACE einfügen → neuen Inhalt erzeugen
        3. ast.parse(new_content) — Syntax-Check
        4. Backup erstellen (.bak)
        5. Datei schreiben

    Args:
        patch:   {"file": str, "search": str, "replace": str}
        dry_run: True → nichts schreiben, nur prüfen

    Returns:
        (success, message)
    """
    rel = patch["file"]
    path = PROJECT / rel
    if not path.exists():
        return False, f"Datei nicht gefunden: {rel}"

    original = path.read_text(encoding="utf-8")
    norm_orig = _normalize_ws(original)
    norm_search = _normalize_ws(patch["search"])
    norm_replace = _normalize_ws(patch["replace"])

    if norm_search not in norm_orig:
        return False, (
            f"SEARCH nicht gefunden in `{rel}` — "
            "Inhalt stimmt nicht überein (evtl. Datei inzwischen geändert)"
        )

    new_norm = norm_orig.replace(norm_search, norm_replace, 1)

    # Syntax-Check
    if rel.endswith(".py"):
        try:
            ast.parse(new_norm)
        except SyntaxError as e:
            return False, f"Syntax-Fehler nach REPLACE in `{rel}`: {e}"

    if dry_run:
        lines_changed = abs(
            norm_replace.count("\n") - norm_search.count("\n")
        )
        return True, (
            f"[dry-run] `{rel}`: SEARCH gefunden, "
            f"REPLACE würde {lines_changed:+d} Zeilen ändern"
        )

    # Backup
    backup = path.with_suffix(path.suffix + ".bak")
    backup.write_text(original, encoding="utf-8")

    # Schreiben — Zeilenenden des Originals beibehalten
    path.write_text(new_norm, encoding="utf-8")
    log.info(f"SEARCH/REPLACE angewendet: {rel}")
    return True, f"`{rel}` gepatcht ({backup.name} als Backup)"


def cmd_apply_patch(number: int, dry_run: bool = False) -> None:
    """
    Liest SEARCH/REPLACE-Blöcke aus Issue-Kommentaren und wendet sie an.

    Schritte:
        1. Kommentare des Issues laden
        2. Blöcke parsen (neuester zuerst)
        3. Jeden Patch validieren + anwenden
        4. Ergebnis als Kommentar ins Issue posten
    """
    comments = gitea.get_comments(number)
    # Neueste Kommentare zuerst durchsuchen
    patches: list[dict] = []
    for c in reversed(comments):
        body = c.get("body", "")
        if _SR_SEARCH in body:
            patches = _parse_search_replace(body)
            if patches:
                break

    if not patches:
        print(f"[!] Keine SEARCH/REPLACE-Blöcke in Issue #{number} gefunden.")
        return

    print(f"[→] {len(patches)} Patch(es) gefunden — {'DRY-RUN' if dry_run else 'anwenden'}...")
    results: list[str] = []
    all_ok = True
    for p in patches:
        ok, msg = _apply_patch(p, dry_run=dry_run)
        icon = "✅" if ok else "❌"
        results.append(f"{icon} {msg}")
        if not ok:
            all_ok = False
        print(f"  {icon} {msg}")

    # Kommentar posten
    mode = "Dry-Run" if dry_run else "Angewendet"
    status = "PASS" if all_ok else "FAIL"
    comment_body = (
        f"## SEARCH/REPLACE — {mode} ({status})\n\n"
        + "\n".join(results)
        + ("\n\n> Kein Commit — dry-run Modus." if dry_run else "")
    )
    gitea.post_comment(number, comment_body)
    print(f"[✓] Ergebnis in Issue #{number} gepostet.")

    if not dry_run and all_ok:
        print("[→] Patches angewendet — jetzt committen:")
        changed = [p["file"] for p in patches]
        print(f"    git add {' '.join(changed)}")
        print(f'    git commit -m "patch: SEARCH/REPLACE via Issue #{number}"')
