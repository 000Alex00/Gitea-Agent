"""
plugins/healing.py — Autonomous Self-Healing Loop (Issue #60).

Erkennt fehlgeschlagene Eval-Tests, generiert Fixes via LLM,
validiert auf Temp-Branch und cherry-picked bei Erfolg.

⚠️ Risikostufe 4/4 — Autonome Schreibzyklen.
   Erfordert zwingend LLM-Backend (CLAUDE_API_ENABLED oder lokal).
   Budget-Deckel via max_healing_tokens verhindert unkontrollierten Verbrauch.

Aufgerufen von:
    agent_start.py → cmd_watch() wenn FEATURES["healing"] aktiv
    agent_start.py → cmd_heal() via --heal <issue-nr>
"""

from __future__ import annotations

import json
import subprocess
import hashlib
import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Konfiguration aus agent_eval.json
# ---------------------------------------------------------------------------

HEALING_DEFAULTS = {
    "max_healing_attempts": 3,
    "max_healing_tokens": 50000,
    "healing_llm_url": "http://localhost:11434/api/generate",
    "healing_llm_model": "llama3",
    "healing_llm_timeout": 60,
}


def _load_healing_cfg(project_root: Path) -> dict:
    for rel in ("tests/agent_eval.json", "agent_eval.json"):
        p = project_root / rel
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                cfg = dict(HEALING_DEFAULTS)
                cfg.update({k: data[k] for k in HEALING_DEFAULTS if k in data})
                cfg["claude_api_enabled"] = data.get("claude_api_enabled", False)
                cfg["claude_model"] = data.get("claude_model", "claude-sonnet-4-6")
                return cfg
            except Exception:
                pass
    return dict(HEALING_DEFAULTS)


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------

@dataclass
class HealingAttempt:
    attempt_no: int
    fix_description: str
    files_changed: list[str]
    eval_passed: bool
    eval_score: float
    tokens_used: int
    error: str = ""


@dataclass
class HealingResult:
    test_name: str
    project_root: str
    success: bool = False
    skipped: bool = False
    skip_reason: str = ""
    attempts: list[HealingAttempt] = field(default_factory=list)
    temp_branch: str = ""
    target_branch: str = ""
    tokens_total: int = 0
    issue_number: Optional[int] = None

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)


# ---------------------------------------------------------------------------
# Git-Operationen
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: Path) -> str:
    return subprocess.check_output(
        ["git"] + args, cwd=cwd, stderr=subprocess.DEVNULL
    ).decode().strip()


def _git_run(args: list[str], cwd: Path) -> bool:
    return subprocess.run(
        ["git"] + args, cwd=cwd,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ).returncode == 0


def _current_branch(project_root: Path) -> str:
    return _git(["rev-parse", "--abbrev-ref", "HEAD"], project_root)


def _short_hash(project_root: Path) -> str:
    try:
        return _git(["rev-parse", "--short", "HEAD"], project_root)
    except Exception:
        return hashlib.md5(datetime.datetime.now().isoformat().encode()).hexdigest()[:7]


def _create_temp_branch(project_root: Path) -> str:
    h = _short_hash(project_root)
    branch = f"fix-attempt-{h}"
    _git_run(["checkout", "-b", branch], project_root)
    return branch


def _delete_branch(project_root: Path, branch: str) -> None:
    current = _current_branch(project_root)
    if current == branch:
        # Zurück zum Ausgangszustand
        _git_run(["checkout", "-"], project_root)
    _git_run(["branch", "-D", branch], project_root)


def _cherry_pick(project_root: Path, from_branch: str, onto_branch: str) -> bool:
    try:
        # Commits auf from_branch seit gemeinsamen Ancestor
        merge_base = _git(["merge-base", onto_branch, from_branch], project_root)
        commits = _git(
            ["log", "--format=%H", f"{merge_base}..{from_branch}"],
            project_root
        ).splitlines()
        if not commits:
            return False
        _git_run(["checkout", onto_branch], project_root)
        for c in reversed(commits):
            if not _git_run(["cherry-pick", c], project_root):
                _git_run(["cherry-pick", "--abort"], project_root)
                return False
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# LLM-Aufruf
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Näherung: 4 Zeichen ~ 1 Token."""
    return len(text) // 4


def _call_llm_local(url: str, model: str, prompt: str, timeout: int) -> str:
    import urllib.request
    payload = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.1, "num_predict": 1024},
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read()).get("response", "").strip()


def _call_llm_claude(model: str, prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model, max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def _build_fix_prompt(
    test_name: str,
    test_reason: str,
    log_excerpt: str,
    previous_attempts: list[HealingAttempt],
    project_root: Path,
) -> str:
    history = ""
    for a in previous_attempts:
        status = "✅ Pass" if a.eval_passed else "❌ Fail"
        history += f"\nVersuch {a.attempt_no}: {status} — {a.fix_description}"
        if a.error:
            history += f"\n  Fehler: {a.error}"

    return f"""Du bist ein autonomer Bug-Fix-Agent. Analysiere den fehlgeschlagenen Test und schlage einen präzisen Fix vor.

## Fehlgeschlagener Test
Name: {test_name}
Grund: {test_reason}

## Log-Auszug (letzte 30 Zeilen)
{log_excerpt}

## Vorherige Versuche
{history or "Keine"}

## Anforderungen
- Schlage EINEN konkreten Fix vor (Dateiname + Zeilenbereich + korrekter Code)
- Format: exakt ein SEARCH/REPLACE-Block pro Datei
- Keine Erklärungen, nur den Fix

## Format
```
FILE: <relativer-pfad>
SEARCH:
<alter Code>
REPLACE:
<neuer Code>
```
"""


def _parse_fix(llm_output: str) -> list[dict]:
    """Parst FILE:/SEARCH:/REPLACE:-Blöcke aus LLM-Ausgabe."""
    fixes = []
    import re
    pattern = re.compile(
        r"FILE:\s*(.+?)\n+SEARCH:\n(.*?)\nREPLACE:\n(.*?)(?=\nFILE:|\Z)",
        re.DOTALL,
    )
    for m in pattern.finditer(llm_output):
        fixes.append({
            "file": m.group(1).strip(),
            "search": m.group(2).strip(),
            "replace": m.group(3).strip(),
        })
    return fixes


def _apply_fixes(project_root: Path, fixes: list[dict]) -> tuple[bool, list[str], str]:
    """Wendet SEARCH/REPLACE-Fixes an. Gibt (success, changed_files, error) zurück."""
    changed = []
    for fix in fixes:
        p = project_root / fix["file"]
        if not p.exists():
            return False, changed, f"Datei nicht gefunden: {fix['file']}"
        content = p.read_text(encoding="utf-8")
        if fix["search"] not in content:
            return False, changed, f"SEARCH-Text nicht gefunden in {fix['file']}"
        new_content = content.replace(fix["search"], fix["replace"], 1)
        p.write_text(new_content, encoding="utf-8")
        changed.append(fix["file"])
    return True, changed, ""


# ---------------------------------------------------------------------------
# Eval-Integration (lightweight)
# ---------------------------------------------------------------------------

def _run_eval(project_root: Path) -> tuple[bool, float, str]:
    """
    Führt evaluation.run() aus. Gibt (passed, score, error) zurück.
    Importiert evaluation dynamisch um Abhängigkeit zu vermeiden.
    """
    try:
        import sys
        agent_dir = str(project_root.parent) if (project_root.parent / "agent_start.py").exists() \
            else str(Path(__file__).parent.parent)
        if agent_dir not in sys.path:
            sys.path.insert(0, agent_dir)
        import evaluation
        result = evaluation.run(project_root, trigger="healing")
        return result.passed, result.score / max(result.max_score, 1), ""
    except Exception as e:
        return False, 0.0, str(e)


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------

def run_healing_loop(
    project_root: Path,
    test_name: str,
    test_reason: str,
    log_excerpt: str = "",
) -> HealingResult:
    """
    Versucht einen fehlgeschlagenen Test autonom zu beheben.

    Args:
        project_root:  Pfad zum Zielprojekt
        test_name:     Name des fehlgeschlagenen Tests
        test_reason:   Fehlermeldung / Grund
        log_excerpt:   Letzten N Zeilen des Logs (optional)

    Returns:
        HealingResult mit Erfolgs-/Fehlerstatus und Versuchs-Historie
    """
    cfg = _load_healing_cfg(project_root)
    result = HealingResult(
        test_name=test_name,
        project_root=str(project_root),
    )

    # LLM-Verfügbarkeit prüfen
    use_claude = cfg.get("claude_api_enabled", False)
    if not use_claude:
        # Lokale LLM erreichbar?
        try:
            import urllib.request
            urllib.request.urlopen(
                cfg["healing_llm_url"].rsplit("/", 1)[0],
                timeout=2
            )
        except Exception:
            result.skipped = True
            result.skip_reason = (
                "Kein LLM-Backend erreichbar. "
                "CLAUDE_API_ENABLED=true setzen oder lokale LLM starten."
            )
            return result

    max_attempts = int(cfg["max_healing_attempts"])
    max_tokens = int(cfg["max_healing_tokens"])

    # Ausgangsbranch merken, Temp-Branch erstellen
    original_branch = _current_branch(project_root)
    try:
        result.target_branch = original_branch
        result.temp_branch = _create_temp_branch(project_root)
    except Exception as e:
        result.skipped = True
        result.skip_reason = f"Temp-Branch konnte nicht erstellt werden: {e}"
        return result

    try:
        for attempt_no in range(1, max_attempts + 1):
            # Budget prüfen
            if result.tokens_total >= max_tokens:
                break

            # LLM um Fix bitten
            prompt = _build_fix_prompt(
                test_name, test_reason, log_excerpt,
                result.attempts, project_root
            )
            token_estimate = _estimate_tokens(prompt)

            try:
                if use_claude:
                    llm_output = _call_llm_claude(cfg["claude_model"], prompt)
                else:
                    llm_output = _call_llm_local(
                        cfg["healing_llm_url"], cfg["healing_llm_model"],
                        prompt, int(cfg["healing_llm_timeout"])
                    )
                token_estimate += _estimate_tokens(llm_output)
            except Exception as exc:
                result.attempts.append(HealingAttempt(
                    attempt_no=attempt_no,
                    fix_description="LLM-Aufruf fehlgeschlagen",
                    files_changed=[], eval_passed=False, eval_score=0.0,
                    tokens_used=token_estimate, error=str(exc),
                ))
                result.tokens_total += token_estimate
                break

            result.tokens_total += token_estimate

            # Fix parsen und anwenden
            fixes = _parse_fix(llm_output)
            if not fixes:
                result.attempts.append(HealingAttempt(
                    attempt_no=attempt_no,
                    fix_description="Kein valider SEARCH/REPLACE-Block gefunden",
                    files_changed=[], eval_passed=False, eval_score=0.0,
                    tokens_used=token_estimate,
                    error="LLM-Ausgabe enthielt keinen verwertbaren Fix",
                ))
                continue

            # Änderungen committen
            ok, changed, err = _apply_fixes(project_root, fixes)
            if not ok:
                result.attempts.append(HealingAttempt(
                    attempt_no=attempt_no,
                    fix_description=fixes[0]["file"] if fixes else "?",
                    files_changed=changed, eval_passed=False, eval_score=0.0,
                    tokens_used=token_estimate, error=err,
                ))
                continue

            # Commit auf Temp-Branch
            try:
                subprocess.run(
                    ["git", "add"] + changed, cwd=project_root,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                subprocess.run(
                    ["git", "commit", "-m",
                     f"heal(attempt-{attempt_no}): fix {test_name}"],
                    cwd=project_root,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except Exception as exc:
                result.attempts.append(HealingAttempt(
                    attempt_no=attempt_no,
                    fix_description=str(fixes[0].get("file", "?")),
                    files_changed=changed, eval_passed=False, eval_score=0.0,
                    tokens_used=token_estimate, error=f"Git-Commit fehlgeschlagen: {exc}",
                ))
                continue

            # Eval ausführen
            passed, score, eval_err = _run_eval(project_root)
            fix_desc = f"{fixes[0]['file']}: {fixes[0]['replace'][:60]}…"
            attempt = HealingAttempt(
                attempt_no=attempt_no,
                fix_description=fix_desc,
                files_changed=changed,
                eval_passed=passed,
                eval_score=score,
                tokens_used=token_estimate,
                error=eval_err,
            )
            result.attempts.append(attempt)

            if passed:
                # Erfolg: Cherry-Pick auf Ausgangsbranch
                result.success = _cherry_pick(
                    project_root, result.temp_branch, original_branch
                )
                break

    finally:
        # Immer: Temp-Branch aufräumen
        try:
            _delete_branch(project_root, result.temp_branch)
        except Exception:
            pass
        # Zurück zum Ausgangsbranch
        _git_run(["checkout", original_branch], project_root)

    return result


# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------

def format_terminal(result: HealingResult) -> str:
    if result.skipped:
        return f"[Healing] übersprungen: {result.skip_reason}"

    lines = [f"[Healing] {result.test_name} — {result.attempt_count} Versuch(e)"]
    for a in result.attempts:
        status = "✅" if a.eval_passed else "❌"
        lines.append(
            f"  {status} Versuch {a.attempt_no}: {a.fix_description[:60]}"
            f"  (Score: {a.eval_score:.0%}, ~{a.tokens_used:,} Token)"
        )
        if a.error:
            lines.append(f"       Fehler: {a.error}")
    lines.append(
        f"  {'✅ Geheilt' if result.success else '❌ Nicht geheilt'} "
        f"— Gesamt: ~{result.tokens_total:,} Token"
    )
    return "\n".join(lines)
