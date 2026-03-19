#!/usr/bin/env python3
"""
evaluation.py — Generisches Eval-System für den gitea-agent Workflow.

Liest `tests/agent_eval.json` aus dem Zielprojekt und führt definierte
HTTP-Tests gegen server.py aus. Vergleicht Score mit `tests/baseline.json`.

Aufgerufen von:
    agent_start.py -> cmd_pr() — vor jedem PR

Standalone:
    python3 evaluation.py [--update-baseline] [--project /pfad/zum/projekt]
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

EVAL_CONFIG  = "tests/agent_eval.json"
BASELINE     = "tests/baseline.json"
DEFAULT_CHAT = "/chat"
TIMEOUT      = 10  # Sekunden pro Request


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    name:    str
    weight:  int
    passed:  bool
    skipped: bool   = False
    reason:  str    = ""


@dataclass
class EvalResult:
    passed:           bool         = False
    skipped:          bool         = False  # kein agent_eval.json gefunden
    warned:           bool         = False  # Infrastruktur offline
    baseline_created: bool         = False  # erster Lauf, Baseline gespeichert
    score:            float        = 0.0
    baseline_score:   float        = 0.0
    max_score:        int          = 0
    warn_reasons:     list[str]    = field(default_factory=list)
    failed_tests:     list[TestResult] = field(default_factory=list)
    all_tests:        list[TestResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _ping(url: str) -> bool:
    """Prüft ob eine URL erreichbar ist (HEAD oder GET)."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        urllib.request.urlopen(req, timeout=TIMEOUT)
        return True
    except Exception:
        try:
            urllib.request.urlopen(url, timeout=TIMEOUT)
            return True
        except Exception:
            return False


def _chat(server_url: str, endpoint: str, message: str) -> str | None:
    """
    Sendet eine Nachricht an server.py und gibt die Antwort zurück.

    Args:
        server_url: Basis-URL, z.B. "http://localhost:8000"
        endpoint:   Pfad, z.B. "/chat" (aus agent_eval.json)
        message:    Nachrichtentext

    Returns:
        Antworttext als String oder None bei Fehler.
    """
    url  = server_url.rstrip("/") + endpoint
    body = json.dumps({"message": message}).encode()
    req  = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())
            # Antwort kann unter "response", "reply", "text" oder "message" liegen
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


def _load_config(project_root: Path) -> dict | None:
    """Lädt agent_eval.json aus dem Zielprojekt. None wenn nicht vorhanden."""
    cfg_path = project_root / EVAL_CONFIG
    if not cfg_path.exists():
        return None
    with cfg_path.open(encoding="utf-8") as f:
        return json.load(f)


def _load_baseline(project_root: Path) -> float | None:
    """Lädt den gespeicherten Baseline-Score. None wenn nicht vorhanden."""
    bl_path = project_root / BASELINE
    if not bl_path.exists():
        return None
    with bl_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("score")


def _save_baseline(project_root: Path, score: float) -> None:
    """Speichert aktuellen Score als neue Baseline."""
    bl_path = project_root / BASELINE
    bl_path.parent.mkdir(parents=True, exist_ok=True)
    with bl_path.open("w", encoding="utf-8") as f:
        json.dump({"score": score}, f, indent=2)


# ---------------------------------------------------------------------------
# Kern
# ---------------------------------------------------------------------------

def run(project_root: Path, update_baseline: bool = False) -> EvalResult:
    """
    Führt alle Eval-Tests aus dem Zielprojekt aus.

    Aufgerufen von:
        agent_start.py -> cmd_pr()
        __main__ (standalone)

    Args:
        project_root:     Pfad zum Zielprojekt (PROJECT-Variable in agent_start.py)
        update_baseline:  Wenn True → aktuellen Score als neue Baseline speichern

    Returns:
        EvalResult mit passed/skipped/warned/failed + Score-Details

    Seiteneffekte:
        Schreibt tests/baseline.json wenn nicht vorhanden oder --update-baseline
    """
    result = EvalResult()

    # 1. Konfiguration laden
    cfg = _load_config(project_root)
    if cfg is None:
        result.skipped = True
        return result

    server_url = cfg.get("server_url", "http://localhost:8000")
    pi5_url    = cfg.get("pi5_url")
    endpoint   = cfg.get("chat_endpoint", DEFAULT_CHAT)
    tests      = cfg.get("tests", [])

    # 2. Erreichbarkeit prüfen
    server_ok = _ping(server_url)
    if not server_ok:
        result.warned = True
        result.warn_reasons.append(f"server.py nicht erreichbar ({server_url}) — Eval übersprungen")
        return result

    pi5_ok = True
    if pi5_url:
        pi5_ok = _ping(pi5_url)
        if not pi5_ok:
            result.warned = True
            result.warn_reasons.append(f"Pi5 nicht erreichbar ({pi5_url}) — Pi5-Tests werden übersprungen")

    # 3. Tests ausführen
    total_weight  = 0
    earned_weight = 0

    for t in tests:
        name     = t.get("name", "?")
        weight   = t.get("weight", 1)
        message  = t.get("message", "")
        keywords = t.get("expected_keywords", [])
        pi5_req  = t.get("pi5_required", False)
        total_weight += weight

        if pi5_req and not pi5_ok:
            tr = TestResult(name=name, weight=weight, passed=False, skipped=True,
                            reason="Pi5 offline")
            result.all_tests.append(tr)
            continue

        response = _chat(server_url, endpoint, message)
        if response is None:
            tr = TestResult(name=name, weight=weight, passed=False,
                            reason="Keine Antwort von server.py")
            result.all_tests.append(tr)
            result.failed_tests.append(tr)
            continue

        passed = _keywords_match(response, keywords)
        tr = TestResult(
            name=name, weight=weight, passed=passed,
            reason="" if passed else f"Keywords {keywords!r} nicht in Antwort"
        )
        result.all_tests.append(tr)
        if passed:
            earned_weight += weight
        else:
            result.failed_tests.append(tr)

    result.max_score = total_weight
    result.score     = earned_weight

    # 4. Baseline vergleichen
    baseline = _load_baseline(project_root)
    if baseline is None or update_baseline:
        _save_baseline(project_root, result.score)
        result.baseline_created = True
        result.baseline_score   = result.score
        result.passed           = True
        return result

    result.baseline_score = baseline
    result.passed         = (result.score >= baseline)
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

    lines = [f"[Eval] Score: {r.score:.0f}/{r.max_score} (Baseline: {r.baseline_score:.0f})"]
    if r.warn_reasons:
        lines += [f"  ⚠  {w}" for w in r.warn_reasons]
    if r.baseline_created:
        lines.append("  ✓ Baseline angelegt (erster Lauf).")
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
    parser.add_argument("--update-baseline", action="store_true",
                        help="Aktuellen Score als neue Baseline speichern")
    args = parser.parse_args()

    project_root = Path(args.project).resolve()
    result = run(project_root, update_baseline=args.update_baseline)
    print(format_terminal(result))
    sys.exit(0 if (result.passed or result.skipped or result.warned) else 1)


if __name__ == "__main__":
    main()
