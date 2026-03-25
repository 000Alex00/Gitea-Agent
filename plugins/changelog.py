"""plugins/changelog.py — Changelog-Generator aus git-History."""

import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).parent.parent  # gitea-agent/
sys.path.insert(0, str(_HERE))

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

_COMMIT_GROUPS = {
    "feat":     "### Features",
    "fix":      "### Bugfixes",
    "docs":     "### Dokumentation",
    "refactor": "### Refactoring",
    "test":     "### Tests",
    "chore":    "### Wartung",
    "perf":     "### Performance",
    "ci":       "### CI/CD",
    "style":    "### Style",
}
_GROUP_ORDER = ["feat", "fix", "refactor", "perf", "test", "docs", "ci", "style", "chore"]


def _git_log_since_tag(cwd: Path) -> list[dict]:
    """
    Gibt alle Commits seit dem letzten Tag zurück.
    Ohne Tag: alle Commits der aktuellen Branch.
    Format je Commit: {"hash": str, "subject": str, "body": str}
    """
    # letzten Tag ermitteln
    try:
        last_tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        rev_range = f"{last_tag}..HEAD"
    except subprocess.CalledProcessError:
        last_tag = None
        rev_range = "HEAD"

    try:
        raw = subprocess.check_output(
            ["git", "log", rev_range, "--pretty=format:%H\x1f%s\x1f%b\x1e"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except subprocess.CalledProcessError as e:
        log.warning(f"git log fehlgeschlagen: {e}")
        return []

    commits = []
    for entry in raw.split("\x1e"):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("\x1f", 2)
        commits.append({
            "hash":    parts[0].strip()[:8] if len(parts) > 0 else "?",
            "subject": parts[1].strip() if len(parts) > 1 else "",
            "body":    parts[2].strip() if len(parts) > 2 else "",
        })
    return commits, last_tag


def _classify_commit(subject: str) -> tuple[str, str]:
    """
    Gibt (typ, beschreibung) zurück.
    Erkennt Conventional-Commit-Präfixe: feat:, fix(scope): etc.
    """
    import re
    m = re.match(r"^(\w+)(?:\([^)]*\))?!?:\s*(.*)", subject)
    if m:
        typ = m.group(1).lower()
        desc = m.group(2)
        return typ, desc
    return "other", subject


def _build_changelog_block(commits: list[dict], version: str, date: str) -> str:
    """Formatiert einen CHANGELOG-Abschnitt für eine Version."""
    groups: dict[str, list[str]] = {k: [] for k in _GROUP_ORDER}
    groups["other"] = []

    for c in commits:
        typ, desc = _classify_commit(c["subject"])
        key = typ if typ in groups else "other"
        groups[key].append(f"- {desc} (`{c['hash']}`)")

    lines = [f"## [{version}] — {date}", ""]
    for key in _GROUP_ORDER:
        if groups[key]:
            lines.append(_COMMIT_GROUPS.get(key, f"### {key.capitalize()}"))
            lines.extend(groups[key])
            lines.append("")
    if groups["other"]:
        lines.append("### Sonstiges")
        lines.extend(groups["other"])
        lines.append("")

    return "\n".join(lines)


def cmd_changelog(version: str | None = None, update_file: bool = True) -> str:
    """
    Generiert/aktualisiert CHANGELOG.md aus git-History seit letztem Tag.

    Args:
        version:     Versions-String (z.B. "1.2.0"). Ohne Angabe: "Unreleased".
        update_file: True → CHANGELOG.md schreiben/prependen.

    Returns:
        Den generierten Changelog-Block als String.
    """
    from datetime import date as _date

    result = _git_log_since_tag(PROJECT)
    commits, last_tag = result

    ver_label = version or "Unreleased"
    today = _date.today().strftime("%Y-%m-%d")

    if not commits:
        print(f"[!] Keine Commits seit letztem Tag ({last_tag or 'kein Tag'}) gefunden.")
        log.info("Changelog: keine neuen Commits gefunden")
        return ""

    block = _build_changelog_block(commits, ver_label, today)

    if update_file:
        changelog_path = PROJECT / "CHANGELOG.md"
        if changelog_path.exists():
            existing = changelog_path.read_text(encoding="utf-8")
            # Header erhalten, neuen Block darunter einfügen
            if existing.startswith("# Changelog"):
                header_end = existing.index("\n", existing.index("\n") + 1)
                new_content = existing[: header_end + 1] + "\n" + block + existing[header_end + 1 :]
            else:
                new_content = block + "\n\n" + existing
        else:
            new_content = "# Changelog\n\nAlle nennenswerten Änderungen werden hier festgehalten.\n\n" + block

        changelog_path.write_text(new_content, encoding="utf-8")
        print(f"[✓] CHANGELOG.md aktualisiert ({len(commits)} Commits, Version: {ver_label})")
        log.info(f"CHANGELOG.md aktualisiert: {len(commits)} Commits, Version {ver_label}")
    else:
        print(block)

    return block
