#!/usr/bin/env python3
"""
evaluation.py — Generisches Eval-System für den gitea-agent Workflow.

Liest `agent/config/agent_eval.json` (neu) oder `tests/agent_eval.json` (Legacy)
aus dem Zielprojekt und führt definierte HTTP-Tests gegen den konfigurierten
Server aus. Vergleicht Score mit baseline.json.

Aufgerufen von:
    agent_start.py -> cmd_pr() — vor jedem PR

Standalone:
    python3 evaluation.py [--update-baseline] [--project /pfad/zum/projekt]
"""

import argparse
import datetime
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

EVAL_CONFIG = "tests/agent_eval.json"
BASELINE = "tests/baseline.json"
SCORE_HISTORY = "tests/score_history.json"
HISTORY_MAX = 90
DEFAULT_CHAT = "/chat"
TIMEOUT = 10  # Sekunden pro Request


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------


@dataclass
class TestResult:
    name: str
    weight: int
    passed: bool
    skipped: bool = False
    reason: str = ""
    category: str = (
        ""  # timeout | server_error | empty_response | keyword_miss | pi5_offline
    )
    actual_response: str = ""  # tatsächliche LLM-Antwort (leer bei None)
    step_details: list = field(
        default_factory=list
    )  # bei steps-Tests: [{msg, expected, actual, passed}]
    tag: str = ""
    response_ms: float = 0.0  # Gemessene Antwortzeit in Millisekunden
    max_response_ms: float | None = None  # Maximal erlaubte Antwortzeit aus config


@dataclass
class EvalResult:
    passed: bool = False
    skipped: bool = False  # kein agent_eval.json gefunden
    warned: bool = False  # Infrastruktur offline
    baseline_created: bool = False  # erster Lauf, Baseline gespeichert
    baseline_raised: bool = False  # Score > alter Baseline → auto-aktualisiert
    score: float = 0.0
    baseline_score: float = 0.0
    max_score: int = 0
    warn_reasons: list[str] = field(default_factory=list)
    failed_tests: list[TestResult] = field(default_factory=list)
    all_tests: list[TestResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _ping(url: str) -> bool:
    """Prüft ob eine URL erreichbar ist (GET, ignoriert HTTP-Fehlercode)."""
    try:
        urllib.request.urlopen(url, timeout=TIMEOUT)
        return True
    except urllib.error.HTTPError:
        return True  # Server antwortet → erreichbar
    except Exception:
        return False


def _chat(server_url: str, endpoint: str, message: str, eval_user: str) -> str | None:
    """
    Sendet eine Nachricht an server.py und gibt die Antwort zurück.

    Args:
        server_url: Basis-URL, z.B. "http://localhost:8000"
        endpoint:   Pfad, z.B. "/chat" (aus agent_eval.json)
        message:    Nachrichtentext
        eval_user:  Eindeutige User-ID pro Eval-Lauf (verhindert Kontext-Bleeding)

    Returns:
        Antworttext als String oder None bei Fehler.
    """
    url = server_url.rstrip("/") + endpoint
    body = json.dumps({"prompt": message, "user": eval_user}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())
            for key in ("response", "reply", "text", "message"):
                if key in data:
                    return str(data[key])
            return str(data)
    except Exception:
        return None


def _keywords_match(text: str, keywords: list[str]) -> bool:
    """Prüft ob alle Keywords (case-insensitive) im Text vorkommen."""
    text_lower = text.lower()
    return all(kw.lower() in text_lower for kw in keywords)


def _categorize(
    response: str | None, keywords: list[str], pi5_skipped: bool = False
) -> str:
    """
    Klassifiziert einen Testfehler objektiv — kein LLM, nur regelbasiert.

    Kategorien:
        pi5_offline   — Pi5 nicht erreichbar (Test übersprungen)
        timeout       — keine Antwort von server.py (response is None)
        server_error  — HTTP 5xx erkannt in Antwort
        empty_response — leere Antwort
        keyword_miss  — Antwort vorhanden, aber Keywords fehlen

    Args:
        response:    Antworttext oder None
        keywords:    Erwartete Keywords
        pi5_skipped: True wenn Test wegen Pi5-Offline übersprungen wurde

    Returns:
        str: Kategorie-Bezeichner
    """
    if pi5_skipped:
        return "pi5_offline"
    if response is None:
        return "timeout"
    if not response.strip():
        return "empty_response"
    if any(code in response for code in ("500", "502", "503", "504")):
        # Heuristik: HTTP-Fehlercodes in Antworttext → server_error
        return "server_error"
    return "keyword_miss"


def _run_steps(
    server_url: str, endpoint: str, steps: list[dict], eval_user: str
) -> tuple[bool, str, list]:
    """
    Führt einen mehrstufigen Test sequenziell aus.

    Jeder Step kann entweder:
    - ``expect_stored: true``  — Nachricht senden, nur Antwort (kein Fehler) erwartet
    - ``expected_keywords: [...]`` — Antwort wird auf Keywords geprüft

    Aufgerufen von:
        run() für Tests mit "steps"-Schlüssel

    Args:
        server_url: Basis-URL von server.py
        endpoint:   Chat-Endpunkt (z.B. "/chat")
        steps:      Liste von Step-Dicts aus agent_eval.json
        eval_user:  Eindeutige User-ID pro Eval-Lauf

    Returns:
        Tuple (passed: bool, reason: str, step_details: list)
        step_details: Liste von Dicts mit {msg, expected, actual, passed, stored}
    """
    step_details = []
    for i, step in enumerate(steps, start=1):
        if i > 1:
            time.sleep(2)  # Jetson Zeit geben zwischen Steps (LLM-Inferenz-Cooldown)

        message = step.get("message", "")
        keywords = step.get("expected_keywords", [])
        stored = step.get("expect_stored", False)

        response = _chat(server_url, endpoint, message, eval_user)
        if response is None:
            step_details.append(
                {
                    "msg": message,
                    "expected": keywords,
                    "actual": None,
                    "passed": False,
                    "stored": stored,
                }
            )
            return False, f"Step {i}: Keine Antwort von server.py", step_details

        if stored:
            step_details.append(
                {
                    "msg": message,
                    "expected": [],
                    "actual": response,
                    "passed": True,
                    "stored": True,
                }
            )
            continue

        step_passed = not keywords or _keywords_match(response, keywords)
        step_details.append(
            {
                "msg": message,
                "expected": keywords,
                "actual": response,
                "passed": step_passed,
                "stored": False,
            }
        )

        if not step_passed:
            return (
                False,
                f"Step {i}: Keywords {keywords!r} nicht in Antwort",
                step_details,
            )

    return True, "", step_details


def _resolve_path(project_root: Path, new_rel: str, legacy_rel: str) -> Path:
    """Gibt project_root/data/<new_rel> zurück (existierend oder für Neuanlage)."""
    path = Path(project_root) / "data" / new_rel
    return path


def _resolve_config(project_root: Path) -> Path:
    """Gibt den Pfad zu config/agent_eval.json zurück."""
    return Path(project_root) / "config" / "agent_eval.json"


def _load_config(project_root: Path) -> dict | None:
    """Lädt agent_eval.json aus dem Zielprojekt. None wenn nicht vorhanden."""
    cfg_path = _resolve_config(project_root)
    if not cfg_path.exists():
        return None
    with cfg_path.open(encoding="utf-8") as f:
        return json.load(f)


def _load_baseline(project_root: Path) -> float | None:
    """Lädt den gespeicherten Baseline-Score. None wenn nicht vorhanden."""
    bl_path = _resolve_path(project_root, "baseline.json", BASELINE)
    if not bl_path.exists():
        return None
    with bl_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("score")


def _save_baseline(project_root: Path, score: float) -> None:
    """Speichert aktuellen Score als neue Baseline."""
    bl_path = _resolve_path(project_root, "baseline.json", BASELINE)
    bl_path.parent.mkdir(parents=True, exist_ok=True)
    with bl_path.open("w", encoding="utf-8") as f:
        json.dump({"score": score}, f, indent=2)


def _get_commit_hash() -> str:
    """Gibt den aktuellen Git-Commit-Hash zurück. Leerer String bei Fehler."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%H"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _save_score_history(project_root: Path, result: "EvalResult", trigger: str) -> None:
    """
    Hängt einen Eintrag an tests/score_history.json an. Max HISTORY_MAX Einträge.

    Args:
        project_root: Pfad zum Zielprojekt
        result:       EvalResult des aktuellen Laufs
        trigger:      "pr", "watch" oder "manual"
    """
    hist_path = _resolve_path(project_root, "score_history.json", SCORE_HISTORY)
    hist_path.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if hist_path.exists():
        try:
            with hist_path.open(encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    
    commit_hash = _get_commit_hash()
    entry = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "commit": commit_hash,
        "trigger": trigger,
        "score": result.score,
        "max_score": result.max_score,
        "baseline": result.baseline_score,
        "passed": result.passed,
        "failed": [{"name": t.name, "reason": t.reason, "tag": t.tag} for t in result.failed_tests],
        "latencies": [{"name": t.name, "ms": t.response_ms, "max_ms": t.max_response_ms, "tag": t.tag} for t in result.all_tests if t.response_ms > 0],
    }
    history.append(entry)
    history = history[-HISTORY_MAX:]  # nur die letzten 90 behalten

    with hist_path.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Kern
# ---------------------------------------------------------------------------


def run(
    project_root: Path, update_baseline: bool = False, trigger: str = "manual"
) -> EvalResult:
    """
    Führt alle Eval-Tests aus dem Zielprojekt aus.

    Aufgerufen von:
        agent_start.py -> cmd_pr()   (trigger="pr")
        agent_start.py -> cmd_watch() (trigger="watch")
        __main__ (standalone)         (trigger="manual")

    Args:
        project_root:     Pfad zum Zielprojekt (PROJECT-Variable in agent_start.py)
        update_baseline:  Wenn True → aktuellen Score als neue Baseline speichern
        trigger:          Auslöser des Laufs — "pr", "watch" oder "manual"

    Returns:
        EvalResult mit passed/skipped/warned/failed + Score-Details

    Seiteneffekte:
        Schreibt tests/baseline.json wenn nicht vorhanden oder --update-baseline
        Schreibt tests/score_history.json (max 90 Einträge)
    """
    result = EvalResult()

    # 1. Konfiguration laden
    cfg = _load_config(project_root)
    if cfg is None:
        result.skipped = True
        return result

    server_url = cfg.get("server_url")
    if not server_url:
        result.skipped = True
        return result
    # secondary_url: generischer Alias, pi5_url bleibt als Legacy-Fallback
    secondary_url = cfg.get("secondary_url") or cfg.get("pi5_url")
    endpoint = cfg.get("chat_endpoint", DEFAULT_CHAT)
    tests = cfg.get("tests", [])

    # 2. Erreichbarkeit prüfen
    server_ok = _ping(server_url)
    if not server_ok:
        result.warned = True
        result.warn_reasons.append(
            f"Server nicht erreichbar ({server_url}) — Eval übersprungen"
        )
        return result

    secondary_ok = True
    if secondary_url:
        secondary_ok = _ping(secondary_url)
        if not secondary_ok:
            result.warned = True
            result.warn_reasons.append(
                f"Sekundärer Dienst nicht erreichbar ({secondary_url}) — abhängige Tests werden übersprungen"
            )

    # 3. Tests ausführen — eindeutiger User pro Lauf verhindert Kontext-Bleeding
    eval_user = f"eval-{uuid.uuid4().hex[:8]}"
    total_weight = 0
    earned_weight = 0

    for t in tests:
        name = t.get("name", "?")
        weight = t.get("weight", 1)
        message = t.get("message", "")
        keywords = t.get("expected_keywords", [])
        # secondary_required: generischer Alias, pi5_required bleibt als Legacy-Fallback
        secondary_req = t.get("secondary_required") or t.get("pi5_required", False)
        max_resp_ms = t.get("max_response_ms")
        tag = t.get("tag", "")
        total_weight += weight

        if secondary_req and not secondary_ok:
            tr = TestResult(
                name=name,
                weight=weight,
                passed=False,
                skipped=True,
                reason="Sekundärer Dienst offline",
                category="secondary_offline",
                tag=tag,
            )
            result.all_tests.append(tr)
            continue

        steps = t.get("steps")
        if steps:
            t_start = time.perf_counter()
            passed, reason, step_details = _run_steps(
                server_url, endpoint, steps, eval_user
            )
            resp_ms = round((time.perf_counter() - t_start) * 1000, 2)
            # Kategorie aus letztem fehlgeschlagenen Step ableiten
            last_actual = None
            if not passed and step_details:
                last_actual = step_details[-1].get("actual")
            category = _categorize(last_actual, keywords) if not passed else ""
            tr = TestResult(
                name=name,
                weight=weight,
                passed=passed,
                reason=reason,
                category=category,
                step_details=step_details,
                response_ms=resp_ms,
                max_response_ms=max_resp_ms,
                tag=tag,
            )
        else:
            t_start = time.perf_counter()
            response = _chat(server_url, endpoint, message, eval_user)
            resp_ms = round((time.perf_counter() - t_start) * 1000, 2)
            if response is None:
                tr = TestResult(
                    name=name,
                    weight=weight,
                    passed=False,
                    reason="Keine Antwort vom Server",
                    category="timeout",
                    actual_response="",
                    response_ms=resp_ms,
                    max_response_ms=max_resp_ms,
                    tag=tag,
                )
                result.all_tests.append(tr)
                result.failed_tests.append(tr)
                continue
            passed = _keywords_match(response, keywords)
            reason = "" if passed else f"Keywords {keywords!r} nicht in Antwort"
            category = "" if passed else _categorize(response, keywords)
            tr = TestResult(
                name=name,
                weight=weight,
                passed=passed,
                reason=reason,
                category=category,
                actual_response=response,
                response_ms=resp_ms,
                max_response_ms=max_resp_ms,
                tag=tag,
            )
        result.all_tests.append(tr)
        if passed:
            earned_weight += weight
        else:
            result.failed_tests.append(tr)

    result.max_score = total_weight
    result.score = earned_weight

    # 4. Baseline vergleichen
    baseline = _load_baseline(project_root)
    if baseline is None or update_baseline:
        _save_baseline(project_root, result.score)
        result.baseline_created = True
        result.baseline_score = result.score
        result.passed = True
        _save_score_history(project_root, result, trigger)
        return result

    result.baseline_score = baseline
    result.passed = result.score >= baseline

    # Score verbessert → Baseline automatisch hochsetzen (nie runter)
    if result.passed and result.score > baseline:
        _save_baseline(project_root, result.score)
        result.baseline_raised = True

    _save_score_history(project_root, result, trigger)
    return result


# ---------------------------------------------------------------------------
# Formatierte Ausgabe (für agent_start.py Kommentar + Terminal)
# ---------------------------------------------------------------------------


def format_terminal(r: EvalResult) -> str:
    """Gibt kompakte Zusammenfassung für Terminal aus."""
    if r.skipped:
        return "[Eval] Kein agent_eval.json gefunden — übersprungen."
    if r.warned and not r.all_tests:
        return "[Eval] " + " | ".join(r.warn_reasons)

    lines = [
        f"[Eval] Score: {r.score:.0f}/{r.max_score} (Baseline: {r.baseline_score:.0f})"
    ]
    if r.warn_reasons:
        lines += [f"  ⚠  {w}" for w in r.warn_reasons]
    if r.baseline_created:
        lines.append("  ✓ Baseline angelegt (erster Lauf).")
    if r.baseline_raised:
        lines.append(
            f"  ✓ Baseline aktualisiert: {r.baseline_score:.0f} → {r.score:.0f}"
        )
    if r.failed_tests:
        lines.append("  Fehlgeschlagen:")
        for t in r.failed_tests:
            lines.append(f"    ✗ {t.name} (Gewicht {t.weight}): {t.reason}")
    status = "✓ PASS" if r.passed else "✗ FAIL"
    lines.insert(1, f"[Eval] {status}")
    return "\n".join(lines)


def format_gitea_comment(r: EvalResult) -> str:
    """Erzeugt Gitea-Kommentar bei FAIL (für cmd_pr)."""
    lines = [
        "## ❌ Eval FAIL — PR blockiert",
        "",
        f"**Score:** {r.score:.0f}/{r.max_score} (Baseline: {r.baseline_score:.0f})",
        "",
    ]
    if r.warn_reasons:
        lines += [f"> ⚠ {w}" for w in r.warn_reasons]
        lines.append("")

    if r.failed_tests:
        lines.append("**Fehlgeschlagene Tests:**")
        for t in r.failed_tests:
            lines.append(f"- {t.name} (Gewicht {t.weight}): {t.reason}")
        lines.append("")

    lines.append("→ Fehler beheben und erneut `--pr` aufrufen.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standalone
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Eval-System für gitea-agent")
    parser.add_argument("--project", default=".", help="Pfad zum Zielprojekt")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Aktuellen Score als neue Baseline speichern",
    )
    args = parser.parse_args()

    project_root = Path(args.project).resolve()
    result = run(project_root, update_baseline=args.update_baseline)
    print(format_terminal(result))
    sys.exit(0 if (result.passed or result.skipped or result.warned) else 1)


if __name__ == "__main__":
    main()
