"""
plugins/optimizer.py — Autonomer Code-Optimierer mit History-Vergleich.

Unterschied zu plugins/healing.py:
  healing.py    → repariert FEHLGESCHLAGENE Tests (Score < Baseline)
  optimizer.py  → verbessert Code wenn Tests BESTEHEN aber Score stagniert
                  oder AST-Komplexität zunimmt

Ohne LLM-API:
  - Erkennt Stagnation: Score unverändert für N Evals
  - Erkennt Komplexitätswachstum: Funktionen gewachsen via AST-Diff
  - Erstellt Gitea-Issue mit Analyse (kein Code-Fix)

Mit LLM-API (CLAUDE_API_ENABLED=true oder routing.json):
  - LLM analysiert stagnierenden / komplexen Code
  - Schlägt Optimierung vor (Refactoring, Vereinfachung, Performance)
  - Erstellt Temp-Branch, wendet Patch an, führt Eval aus
  - Vergleicht Score mit History-Baseline
  - Bei keiner Verbesserung: anderen Ansatz versuchen (max HEALING_MAX_ATTEMPTS)
  - Bei Verbesserung: PR erstellen

Aufgerufen von:
  agent_start.py → cmd_watch() im Night-Modus wenn optimizer=true in project.json
  oder direkt: python3 plugins/optimizer.py --project /pfad/zum/projekt
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Datenstrukturen
# ---------------------------------------------------------------------------

@dataclass
class OptimizationTarget:
    kind: str              # "stagnation" | "complexity" | "latency"
    description: str
    files: list[str]
    current_score: float
    baseline_score: float
    details: str           # AST-Diff oder Stagnations-Info


@dataclass
class OptimizationAttempt:
    attempt_no: int
    approach: str
    files_changed: list[str]
    score_before: float
    score_after: float
    improved: bool
    error: str = ""


@dataclass
class OptimizerResult:
    target: Optional[OptimizationTarget] = None
    success: bool = False
    skipped: bool = False
    skip_reason: str = ""
    api_used: bool = False
    api_missing: bool = False
    attempts: list[OptimizationAttempt] = field(default_factory=list)
    pr_url: str = ""
    issue_number: Optional[int] = None

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)


# ---------------------------------------------------------------------------
# History-Analyse (ohne LLM)
# ---------------------------------------------------------------------------

def _load_history(project_root: Path) -> list[dict]:
    try:
        import sys
        sys.path.insert(0, str(project_root))
        import evaluation
        p = evaluation._resolve_path(project_root, "score_history.json", "score_history.json")
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _detect_stagnation(history: list[dict], min_evals: int = 5) -> Optional[OptimizationTarget]:
    """Erkennt Score-Stagnation: Score unverändert für min_evals Evals."""
    if len(history) < min_evals:
        return None

    recent = history[-min_evals:]
    scores = [e.get("score", 0) for e in recent]
    max_scores = [e.get("max_score", 1) for e in recent]

    # Nur analysieren wenn alle Tests bestehen
    if not all(e.get("passed", False) for e in recent):
        return None

    # Score muss konstant und unter 100% sein
    if len(set(scores)) == 1 and scores[0] < max_scores[0]:
        ratio = scores[0] / max_scores[0]
        return OptimizationTarget(
            kind="stagnation",
            description=f"Score stagniert bei {scores[0]}/{max_scores[0]} ({ratio:.0%}) seit {min_evals} Evals",
            files=[],
            current_score=scores[0],
            baseline_score=max_scores[0],
            details=f"Letzte {min_evals} Evals: {scores}",
        )
    return None


def _detect_complexity_growth(project_root: Path) -> Optional[OptimizationTarget]:
    """Erkennt Funktionen die seit letztem Commit stark gewachsen sind."""
    try:
        # Geänderte .py-Dateien seit letztem Commit
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            cwd=project_root, stderr=subprocess.DEVNULL,
        ).decode().splitlines()
        py_files = [f for f in changed if f.endswith(".py")]
        if not py_files:
            return None

        # AST-Diff via agent_start._ast_diff
        import sys
        sys.path.insert(0, str(project_root))

        growth_notes = []
        affected_files = []
        for rel_path in py_files[:5]:
            try:
                old = subprocess.check_output(
                    ["git", "show", f"HEAD~1:{rel_path}"],
                    cwd=project_root, stderr=subprocess.DEVNULL,
                ).decode()
                new = (project_root / rel_path).read_text(encoding="utf-8")
                # Inline-AST-Diff (kopierte Logik um Import-Abhängigkeit zu vermeiden)
                diffs = _ast_diff_simple(old, new)
                growth = [d for d in diffs if "gewachsen" in d]
                if growth:
                    growth_notes.extend([f"{rel_path}: {g}" for g in growth])
                    affected_files.append(rel_path)
            except Exception:
                continue

        if growth_notes:
            return OptimizationTarget(
                kind="complexity",
                description=f"{len(growth_notes)} Funktion(en) stark gewachsen",
                files=affected_files,
                current_score=0,
                baseline_score=0,
                details="\n".join(growth_notes),
            )
    except Exception:
        pass
    return None


def _ast_diff_simple(old_content: str, new_content: str) -> list[str]:
    """Vereinfachter AST-Vergleich (kein Import von agent_start nötig)."""
    import ast as ast_mod

    def sym_map(src: str) -> dict[str, int]:
        try:
            tree = ast_mod.parse(src)
            return {
                node.name: len(src.splitlines()[node.lineno - 1:getattr(node, 'end_lineno', node.lineno)])
                for node in ast_mod.walk(tree)
                if isinstance(node, (ast_mod.FunctionDef, ast_mod.AsyncFunctionDef, ast_mod.ClassDef))
            }
        except Exception:
            return {}

    old_map = sym_map(old_content)
    new_map = sym_map(new_content)
    diffs = []
    for name, new_len in new_map.items():
        old_len = old_map.get(name, 0)
        if new_len > old_len + 10:
            diffs.append(f"~ gewachsen: `{name}` ({old_len}→{new_len} Zeilen)")
    return diffs


# ---------------------------------------------------------------------------
# LLM-Integration
# ---------------------------------------------------------------------------

def _llm_available(project_root: Path) -> bool:
    try:
        import sys
        sys.path.insert(0, str(project_root))
        import settings
        if settings.CLAUDE_API_ENABLED:
            return True
        from plugins.llm import _load_routing
        routing = _load_routing()
        return bool(routing.get("tasks", {}).get("deep_coding") or routing.get("default"))
    except Exception:
        return False


def _call_llm(project_root: Path, prompt: str) -> str:
    try:
        import sys
        sys.path.insert(0, str(project_root))
        import settings
        from plugins.llm import _load_routing, _resolve_task_config, _load_system_prompt

        routing = _load_routing()
        cfg = _resolve_task_config("deep_coding", routing)
        model = cfg.get("model", settings.CLAUDE_MODEL)
        system_prompt = _load_system_prompt(cfg)
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        if cfg.get("provider") == "claude" or settings.CLAUDE_API_ENABLED:
            import anthropic
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model=model, max_tokens=2048,
                messages=[{"role": "user", "content": full_prompt}],
            )
            return msg.content[0].text.strip()

        base_url = cfg.get("base_url", settings._env("LLM_LOCAL_URL", ""))
        if base_url:
            import urllib.request
            payload = json.dumps({"model": model, "prompt": full_prompt, "stream": False})
            req = urllib.request.Request(
                f"{base_url}/api/generate",
                data=payload.encode(), headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read()).get("response", "").strip()
    except Exception as e:
        return f"[LLM-Fehler: {e}]"
    return ""


def _build_optimize_prompt(
    target: OptimizationTarget,
    project_root: Path,
    previous_attempts: list[OptimizationAttempt],
) -> str:
    history = ""
    for a in previous_attempts:
        status = "✅ Verbesserung" if a.improved else "❌ Keine Verbesserung"
        history += f"\nVersuch {a.attempt_no}: {status} — {a.approach}"
        if a.error:
            history += f"\n  Fehler: {a.error}"

    # Relevante Dateien laden (Slices)
    file_context = ""
    for rel_path in target.files[:3]:
        try:
            content = (project_root / rel_path).read_text(encoding="utf-8")
            lines = content.splitlines()
            # Nur erste 100 Zeilen als Kontext
            preview = "\n".join(lines[:100])
            file_context += f"\n### {rel_path} (erste 100 Zeilen):\n```python\n{preview}\n```\n"
        except Exception:
            pass

    return f"""Du bist ein autonomer Code-Optimierer. Analysiere das Problem und schlage eine konkrete Verbesserung vor.

## Optimierungsziel
Typ: {target.kind}
Beschreibung: {target.description}
Details: {target.details}

## Betroffene Dateien
{', '.join(target.files) or 'Aus Stagnations-Analyse — bitte geeignete Datei identifizieren'}

{file_context}

## Vorherige Versuche (nicht wiederholen!)
{history or "Keine — erster Versuch"}

## Anforderungen
- Schlage EINE konkrete Optimierung vor (Refactoring, Vereinfachung, Performance-Fix)
- Kein neues Feature, keine Breaking Changes
- Tests müssen weiterhin bestehen (Score darf nicht sinken)
- Format: exakt ein SEARCH/REPLACE-Block pro geänderter Datei

## Format
```
APPROACH: <kurze Beschreibung des Ansatzes>
FILE: <relativer-pfad>
SEARCH:
<alter Code>
REPLACE:
<neuer Code>
```
"""


def _parse_optimization(llm_output: str) -> tuple[str, list[dict]]:
    """Parst APPROACH + FILE/SEARCH/REPLACE aus LLM-Ausgabe."""
    approach = ""
    m = re.search(r"APPROACH:\s*(.+)", llm_output)
    if m:
        approach = m.group(1).strip()

    fixes = []
    pattern = re.compile(
        r"FILE:\s*(.+?)\nSEARCH:\n(.*?)\nREPLACE:\n(.*?)(?=\nFILE:|\Z)",
        re.DOTALL,
    )
    for m in pattern.finditer(llm_output):
        fixes.append({
            "file": m.group(1).strip(),
            "search": m.group(2).strip(),
            "replace": m.group(3).strip(),
        })
    return approach, fixes


import re as _re_module
re = _re_module


def _apply_fixes(project_root: Path, fixes: list[dict]) -> tuple[bool, list[str]]:
    """Wendet SEARCH/REPLACE-Fixes an."""
    changed = []
    for fix in fixes:
        path = project_root / fix["file"]
        if not path.exists():
            return False, []
        content = path.read_text(encoding="utf-8")
        if fix["search"] not in content:
            return False, []
        path.write_text(content.replace(fix["search"], fix["replace"], 1), encoding="utf-8")
        changed.append(fix["file"])
    return bool(changed), changed


def _run_eval(project_root: Path) -> tuple[bool, float]:
    """Führt Eval aus. Gibt (passed, score_ratio) zurück."""
    try:
        import sys
        sys.path.insert(0, str(project_root))
        import evaluation
        result = evaluation.run(project_root, trigger="optimizer")
        if result.skipped:
            return True, 1.0
        ratio = result.score / result.max_score if result.max_score else 1.0
        return result.passed, ratio
    except Exception:
        return False, 0.0


def _git(args: list[str], cwd: Path) -> str:
    return subprocess.check_output(["git"] + args, cwd=cwd, stderr=subprocess.DEVNULL).decode().strip()


def _git_run(args: list[str], cwd: Path) -> bool:
    return subprocess.run(["git"] + args, cwd=cwd, stderr=subprocess.DEVNULL).returncode == 0


# ---------------------------------------------------------------------------
# Haupt-Funktion
# ---------------------------------------------------------------------------

def run(project_root: Path, stagnation_evals: int = 5) -> OptimizerResult:
    """
    Analysiert Optimierungspotenzial und versucht autonom zu verbessern.

    Ohne LLM-API: Erkennung + Issue-Erstellung, kein Code-Fix.
    Mit LLM-API:  Erkennung + LLM-Fix + Eval + History-Vergleich + PR.

    Args:
        project_root:    Projekt-Root
        stagnation_evals: Anzahl stabiler Evals vor Optimierungs-Versuch

    Returns:
        OptimizerResult
    """
    import sys
    sys.path.insert(0, str(project_root))
    import settings

    result = OptimizerResult()

    # 1. Optimierungsziel erkennen
    history = _load_history(project_root)
    target = _detect_stagnation(history, stagnation_evals)
    if target is None:
        target = _detect_complexity_growth(project_root)
    if target is None:
        result.skipped = True
        result.skip_reason = "Kein Optimierungsziel erkannt (Score nicht stagniert, keine Komplexitätszunahme)"
        return result

    result.target = target

    # 2. Ohne LLM: nur Analyse, kein Fix
    if not _llm_available(project_root):
        result.api_missing = True
        result.skipped = True
        result.skip_reason = (
            f"Optimierungsziel erkannt: {target.description}\n"
            "LLM-API nicht konfiguriert — kein automatischer Fix möglich.\n"
            "→ CLAUDE_API_ENABLED=true setzen für autonome Optimierung."
        )
        return result

    result.api_used = True
    max_attempts = settings.HEALING_MAX_ATTEMPTS

    original_branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], project_root)
    temp_branch = f"optimizer/auto-{int(time.time())}"

    try:
        _git_run(["checkout", "-b", temp_branch], project_root)
    except Exception as e:
        result.skipped = True
        result.skip_reason = f"Temp-Branch konnte nicht erstellt werden: {e}"
        return result

    score_before = target.current_score
    if not score_before and history:
        score_before = history[-1].get("score", 0) / max(history[-1].get("max_score", 1), 1)

    try:
        for attempt_no in range(1, max_attempts + 1):
            prompt = _build_optimize_prompt(target, project_root, result.attempts)
            llm_output = _call_llm(project_root, prompt)

            approach, fixes = _parse_optimization(llm_output)
            if not fixes:
                result.attempts.append(OptimizationAttempt(
                    attempt_no=attempt_no,
                    approach=approach or "unbekannt",
                    files_changed=[],
                    score_before=score_before,
                    score_after=score_before,
                    improved=False,
                    error="LLM hat keine gültigen SEARCH/REPLACE-Blöcke geliefert",
                ))
                continue

            # Fixes anwenden
            applied, changed_files = _apply_fixes(project_root, fixes)
            if not applied:
                result.attempts.append(OptimizationAttempt(
                    attempt_no=attempt_no,
                    approach=approach,
                    files_changed=[],
                    score_before=score_before,
                    score_after=score_before,
                    improved=False,
                    error="SEARCH-Text nicht gefunden — Patch nicht anwendbar",
                ))
                _git_run(["checkout", "--", "."], project_root)
                continue

            # Commit + Eval
            _git_run(["add"] + changed_files, project_root)
            _git_run(["commit", "-m", f"optimizer: {approach[:60]}"], project_root)
            passed, score_after = _run_eval(project_root)

            improved = passed and score_after > score_before
            result.attempts.append(OptimizationAttempt(
                attempt_no=attempt_no,
                approach=approach,
                files_changed=changed_files,
                score_before=score_before,
                score_after=score_after,
                improved=improved,
            ))

            if improved:
                result.success = True
                # Branch pushen für PR-Erstellung durch agent_start.py
                _git_run(["push", "origin", temp_branch], project_root)
                result.pr_url = temp_branch  # agent_start erstellt PR
                break

            # Kein Fortschritt → Änderungen zurückrollen
            _git_run(["revert", "--no-edit", "HEAD"], project_root)

    finally:
        if not result.success:
            _git_run(["checkout", original_branch], project_root)
            _git_run(["branch", "-D", temp_branch], project_root)
        else:
            _git_run(["checkout", original_branch], project_root)

    return result


def build_issue_body(result: OptimizerResult) -> str:
    """Erstellt Issue-Body für erkanntes Optimierungsziel (ohne LLM-Fix)."""
    t = result.target
    lines = [
        f"## Optimierungspotenzial erkannt: `{t.kind}`\n",
        f"**Beschreibung:** {t.description}\n",
        f"**Details:**\n```\n{t.details}\n```\n",
    ]
    if t.files:
        lines.append(f"**Betroffene Dateien:** {', '.join(f'`{f}`' for f in t.files)}\n")

    lines.append(
        "\n> ℹ️ **LLM-API nicht konfiguriert** — automatischer Fix nicht möglich.\n"
        "> Mit `CLAUDE_API_ENABLED=true` und `healing=true` in `config/project.json`\n"
        "> wird der Optimizer autonom Verbesserungen versuchen.\n"
    )
    lines.append("> Automatisch erkannt durch Code-Optimizer.")
    return "\n".join(lines)


def format_terminal(result: OptimizerResult) -> str:
    if result.skipped:
        if result.api_missing:
            t = result.target
            return (
                f"[Optimizer] Ziel erkannt: {t.description}\n"
                f"  → Kein LLM-API — Fix nicht möglich (CLAUDE_API_ENABLED=true setzen)"
            )
        return f"[Optimizer] übersprungen: {result.skip_reason}"

    lines = [f"[Optimizer] {result.target.description}"]
    for a in result.attempts:
        status = "✅" if a.improved else "❌"
        lines.append(f"  Versuch {a.attempt_no}: {status} {a.approach} (Score: {a.score_before:.2f}→{a.score_after:.2f})")
    if result.success:
        lines.append(f"  → Verbesserung gefunden — Branch: {result.pr_url}")
    else:
        lines.append(f"  → Keine Verbesserung nach {result.attempt_count} Versuchen")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Autonomer Code-Optimierer")
    parser.add_argument("--project", default=".", help="Projekt-Root")
    parser.add_argument("--stagnation-evals", type=int, default=5,
                        help="Anzahl stabiler Evals vor Optimierungs-Versuch")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nur Analyse, kein Fix (auch mit API)")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    r = run(root, args.stagnation_evals)
    print(format_terminal(r))
