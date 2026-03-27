"""
plugins/docstring_check.py — Prüft ob geänderte Python-Funktionen Docstrings haben.

Analysiert per AST welche Funktionen/Klassen in geänderten .py-Dateien keinen
Docstring haben. Erstellt Gitea-Issue oder gibt Warnung im PR-Kommentar aus.

Aufgerufen von:
  agent_start.py → cmd_pr() wenn FEATURES["docstring_check"] aktiv
"""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class MissingDocstring:
    """Einzelner Fund: Funktion oder Klasse ohne Docstring."""

    file: str
    name: str
    kind: str        # "function" | "class" | "method"
    line: int


@dataclass
class DocstringReport:
    """Ergebnis eines Docstring-Checks über geänderte Dateien."""

    missing: list[MissingDocstring] = field(default_factory=list)
    checked_files: int = 0
    skipped: bool = False
    skip_reason: str = ""

    @property
    def has_missing(self) -> bool:
        """True wenn mindestens ein fehlender Docstring gefunden wurde."""
        return bool(self.missing)

    def to_markdown(self) -> str:
        """Markdown-Block für Gitea-PR-Kommentare."""
        if not self.missing:
            return ""
        lines = ["### Fehlende Docstrings\n"]
        by_file: dict[str, list[MissingDocstring]] = {}
        for m in self.missing:
            by_file.setdefault(m.file, []).append(m)
        for fpath, items in by_file.items():
            lines.append(f"**`{fpath}`**")
            for m in items:
                lines.append(f"- Zeile {m.line}: `{m.kind} {m.name}` — kein Docstring")
            lines.append("")
        lines.append("> Docstrings hinzufügen bevor gemergt wird.")
        return "\n".join(lines)

    def to_terminal(self) -> str:
        """Kompakte Terminal-Ausgabe der fehlenden Docstrings."""
        if not self.missing:
            return ""
        by_file: dict[str, list[MissingDocstring]] = {}
        for m in self.missing:
            by_file.setdefault(m.file, []).append(m)
        parts = [f"[!] Fehlende Docstrings in {len(by_file)} Datei(en):"]
        for fpath, items in by_file.items():
            parts.append(f"  {fpath}:")
            for m in items:
                parts.append(f"    Zeile {m.line}: {m.kind} {m.name}")
        return "\n".join(parts)


def _check_file(path: Path, rel_path: str) -> list[MissingDocstring]:
    """Analysiert eine .py-Datei per AST auf fehlende Docstrings."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []

    missing = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = "method" if "." in node.name else "function"
            if not (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                # Dunder-Methoden und private Helfer (_, __) überspringen
                if not node.name.startswith("_"):
                    missing.append(MissingDocstring(
                        file=rel_path, name=node.name, kind=kind, line=node.lineno
                    ))
        elif isinstance(node, ast.ClassDef):
            if not (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                missing.append(MissingDocstring(
                    file=rel_path, name=node.name, kind="class", line=node.lineno
                ))
    return missing


def check_changed_files(
    project_root: Path,
    branch: str,
    base_branch: str = "main",
    exclude_prefixes: Optional[list[str]] = None,
) -> DocstringReport:
    """
    Prüft alle geänderten .py-Dateien zwischen branch und base_branch.

    Args:
        project_root:    Projekt-Root (für git-Befehle)
        branch:          Feature-Branch
        base_branch:     Basis-Branch (Standard: main)
        exclude_prefixes: Pfad-Präfixe die übersprungen werden (z.B. ["tests/"])

    Returns:
        DocstringReport mit fehlenden Docstrings
    """
    report = DocstringReport()
    exclude = exclude_prefixes or ["tests/", "data/"]

    try:
        raw = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base_branch}...{branch}"],
            cwd=project_root,
            stderr=subprocess.DEVNULL,
        ).decode().splitlines()
    except Exception as e:
        report.skipped = True
        report.skip_reason = f"git diff fehlgeschlagen: {e}"
        return report

    py_files = [
        f for f in raw
        if f.endswith(".py") and not any(f.startswith(p) for p in exclude)
    ]

    for rel in py_files:
        abs_path = project_root / rel
        if abs_path.exists():
            report.missing.extend(_check_file(abs_path, rel))
            report.checked_files += 1

    return report
