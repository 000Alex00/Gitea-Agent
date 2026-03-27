"""
plugins/log_anomaly.py — Log-Anomalie-Detektor mit Auto-Issue-Erstellung.

Unterschied zu config/log_analyzer.py:
  log_analyzer.py  → terminale Ausgabe pro Watch-Zyklus, kein State
  log_anomaly.py   → persistenter State, erstellt Gitea-Issues bei neuen Anomalien,
                     optionale LLM-Lösungsvorschläge

Ohne LLM-API:
  - Regelbasierte Anomalie-Erkennung (Fehlerhäufung, Timeouts, Crash-Muster)
  - State-Tracking: nur NEUE Anomalien werden als Issue gepostet
  - Gitea-Issue mit: Muster, Häufigkeit, betroffene Zeilen, Zeitstempel

Mit LLM-API (CLAUDE_API_ENABLED=true oder routing.json):
  - LLM analysiert den Anomalie-Kontext
  - Erstellt Root-Cause-Hypothese + Lösungsvorschlag
  - Bereichert das Auto-Issue mit LLM-Analyse

Aufgerufen von:
  agent_start.py → cmd_watch() wenn FEATURES["health_checks"] aktiv
  oder direkt: python3 plugins/log_anomaly.py --project /pfad/zum/projekt
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Anomalie-Muster (regelbasiert, kein LLM nötig)
# ---------------------------------------------------------------------------

_PATTERNS: list[dict] = [
    {
        "tag": "crash",
        "pattern": re.compile(r"(Traceback \(most recent call last\)|Fatal error|Segmentation fault)", re.I),
        "severity": 3,
        "hypothesis": "Unbehandelte Exception oder fataler Fehler",
        "suggestion": "Stack-Trace analysieren, Exception-Handler prüfen",
    },
    {
        "tag": "timeout",
        "pattern": re.compile(r"(timeout|timed out|connection refused|ETIMEDOUT)", re.I),
        "severity": 2,
        "hypothesis": "Dienst nicht erreichbar oder zu langsam",
        "suggestion": "Netzwerk/Service-Verfügbarkeit prüfen, Timeout-Werte anpassen",
    },
    {
        "tag": "oom",
        "pattern": re.compile(r"(MemoryError|out of memory|OOMKilled|killed)", re.I),
        "severity": 3,
        "hypothesis": "Speichermangel",
        "suggestion": "Memory-Profiling durchführen, Batch-Größen reduzieren",
    },
    {
        "tag": "auth",
        "pattern": re.compile(r"(401|403|unauthorized|forbidden|invalid token|authentication failed)", re.I),
        "severity": 2,
        "hypothesis": "Authentifizierungsfehler",
        "suggestion": "API-Token und Berechtigungen prüfen",
    },
    {
        "tag": "db_error",
        "pattern": re.compile(r"(database error|sql error|connection pool|deadlock|duplicate key)", re.I),
        "severity": 2,
        "hypothesis": "Datenbankfehler",
        "suggestion": "DB-Verbindung und Query-Logik prüfen",
    },
    {
        "tag": "error_spike",
        "pattern": re.compile(r"\b(ERROR|CRITICAL|FATAL)\b"),
        "severity": 1,
        "hypothesis": "Erhöhte Fehlerrate",
        "suggestion": "Fehler-Log auf Muster untersuchen",
    },
]

# Mindestanzahl gleichartiger Treffer um als Anomalie zu gelten
_SPIKE_THRESHOLD = 3


# ---------------------------------------------------------------------------
# Datenstrukturen
# ---------------------------------------------------------------------------

@dataclass
class Anomaly:
    tag: str
    severity: int          # 1=niedrig, 2=mittel, 3=hoch
    count: int
    first_line: str
    hypothesis: str
    suggestion: str
    fingerprint: str       # Hash für State-Deduplication
    llm_analysis: str = ""


@dataclass
class AnomalyResult:
    log_path: str = ""
    lines_analyzed: int = 0
    anomalies: list[Anomaly] = field(default_factory=list)
    new_anomalies: list[Anomaly] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""
    api_used: bool = False

    @property
    def has_new(self) -> bool:
        return len(self.new_anomalies) > 0

    @property
    def max_severity(self) -> int:
        if not self.new_anomalies:
            return 0
        return max(a.severity for a in self.new_anomalies)


# ---------------------------------------------------------------------------
# State-Persistence (welche Anomalien wurden bereits gemeldet)
# ---------------------------------------------------------------------------

def _state_path(project_root: Path) -> Path:
    return project_root / "data" / "log_anomaly_state.json"


def _load_state(project_root: Path) -> set[str]:
    p = _state_path(project_root)
    if not p.exists():
        return set()
    try:
        return set(json.loads(p.read_text(encoding="utf-8")).get("reported", []))
    except Exception:
        return set()


def _save_state(project_root: Path, reported: set[str]) -> None:
    p = _state_path(project_root)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"reported": list(reported)}, indent=2), encoding="utf-8")
    except Exception:
        pass


def _fingerprint(tag: str, first_line: str) -> str:
    return hashlib.md5(f"{tag}:{first_line[:120]}".encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Regelbasierte Analyse
# ---------------------------------------------------------------------------

def _analyze_rules(lines: list[str]) -> list[Anomaly]:
    tag_hits: dict[str, list[str]] = {}

    for line in lines:
        for pat in _PATTERNS:
            if pat["pattern"].search(line):
                tag_hits.setdefault(pat["tag"], []).append(line.rstrip())

    anomalies = []
    for pat in _PATTERNS:
        tag = pat["tag"]
        hits = tag_hits.get(tag, [])
        if tag == "error_spike":
            if len(hits) < _SPIKE_THRESHOLD:
                continue
        elif not hits:
            continue

        first = hits[0]
        fp = _fingerprint(tag, first)
        anomalies.append(Anomaly(
            tag=tag,
            severity=pat["severity"],
            count=len(hits),
            first_line=first,
            hypothesis=pat["hypothesis"],
            suggestion=pat["suggestion"],
            fingerprint=fp,
        ))

    return anomalies


# ---------------------------------------------------------------------------
# LLM-Analyse (optional — nur mit API)
# ---------------------------------------------------------------------------

def _llm_available(project_root: Path) -> bool:
    """Prüft ob LLM-API konfiguriert ist."""
    try:
        import sys
        sys.path.insert(0, str(project_root))
        import settings
        if settings.CLAUDE_API_ENABLED:
            return True
        from plugins.llm import _load_routing
        routing = _load_routing()
        return bool(routing.get("tasks", {}).get("log_analysis") or routing.get("default"))
    except Exception:
        return False


def _call_llm(project_root: Path, prompt: str) -> str:
    """Ruft LLM für Anomalie-Analyse auf (Claude API oder lokale LLM)."""
    try:
        import sys
        sys.path.insert(0, str(project_root))
        import settings
        from plugins.llm import _load_routing, _resolve_task_config, _load_system_prompt

        routing = _load_routing()
        cfg = _resolve_task_config("log_analysis", routing)
        provider = cfg.get("provider", "")
        model = cfg.get("model", settings.CLAUDE_MODEL)
        system_prompt = _load_system_prompt(cfg)

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        if provider == "claude" or settings.CLAUDE_API_ENABLED:
            import anthropic
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model=model, max_tokens=512,
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
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read()).get("response", "").strip()
    except Exception as e:
        return f"[LLM-Fehler: {e}]"
    return ""


def _enrich_with_llm(anomaly: Anomaly, log_excerpt: str, project_root: Path) -> str:
    prompt = f"""Analysiere diese Log-Anomalie und gib eine kurze Root-Cause-Hypothese + Lösungsvorschlag.

Anomalie-Typ: {anomaly.tag} (Häufigkeit: {anomaly.count}x)
Erste Zeile: {anomaly.first_line}
Regelbasierte Hypothese: {anomaly.hypothesis}

Log-Kontext (letzte 20 relevante Zeilen):
{log_excerpt}

Antworte in max. 3 Sätzen: Root Cause + konkreter nächster Schritt."""
    return _call_llm(project_root, prompt)


# ---------------------------------------------------------------------------
# Haupt-Funktion
# ---------------------------------------------------------------------------

def run(project_root: Path, log_path: Optional[Path] = None,
        tail_lines: int = 200) -> AnomalyResult:
    """
    Analysiert Log auf neue Anomalien.

    Ohne LLM-API: regelbasiert, State-Tracking, Gitea-Issue-fähig.
    Mit LLM-API:  zusätzlich Root-Cause + Lösungsvorschlag pro Anomalie.

    Args:
        project_root: Projekt-Root (für State + Settings)
        log_path:     Log-Datei (None → aus agent_eval.json lesen)
        tail_lines:   Letzte N Zeilen analysieren

    Returns:
        AnomalyResult mit neuen Anomalien
    """
    result = AnomalyResult()

    # Log-Pfad aus agent_eval.json falls nicht angegeben
    if log_path is None:
        try:
            import sys
            sys.path.insert(0, str(project_root))
            import evaluation
            cfg = evaluation._load_config(project_root) or {}
            lp = cfg.get("log_path", "")
            if not lp:
                result.skipped = True
                result.skip_reason = "log_path in agent_eval.json nicht konfiguriert"
                return result
            log_path = Path(lp)
        except Exception as e:
            result.skipped = True
            result.skip_reason = f"Konfiguration nicht lesbar: {e}"
            return result

    if not log_path.exists():
        result.skipped = True
        result.skip_reason = f"Log-Datei nicht gefunden: {log_path}"
        return result

    result.log_path = str(log_path)

    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()[-tail_lines:]
        result.lines_analyzed = len(lines)
    except Exception as e:
        result.skipped = True
        result.skip_reason = f"Lesefehler: {e}"
        return result

    # Regelbasierte Analyse
    result.anomalies = _analyze_rules(lines)

    # State-Deduplication: nur neue Anomalien
    reported = _load_state(project_root)
    for anomaly in result.anomalies:
        if anomaly.fingerprint not in reported:
            result.new_anomalies.append(anomaly)

    if not result.new_anomalies:
        return result

    # LLM-Anreicherung (optional)
    if _llm_available(project_root):
        result.api_used = True
        log_excerpt = "\n".join(lines[-20:])
        for anomaly in result.new_anomalies:
            anomaly.llm_analysis = _enrich_with_llm(anomaly, log_excerpt, project_root)

    # State aktualisieren
    for anomaly in result.new_anomalies:
        reported.add(anomaly.fingerprint)
    _save_state(project_root, reported)

    return result


def build_issue_body(result: AnomalyResult) -> str:
    """Erstellt Gitea-Issue-Body für neue Anomalien."""
    lines = ["## Log-Anomalie erkannt\n"]
    lines.append(f"Log: `{result.log_path}` — {result.lines_analyzed} Zeilen analysiert\n")

    api_note = "" if result.api_used else (
        "\n> ℹ️ **LLM-API nicht konfiguriert** — nur regelbasierte Analyse. "
        "Mit `CLAUDE_API_ENABLED=true` werden Root-Cause-Hypothesen automatisch generiert.\n"
    )
    if api_note:
        lines.append(api_note)

    for i, a in enumerate(result.new_anomalies, 1):
        sev = {1: "🟡 niedrig", 2: "🟠 mittel", 3: "🔴 hoch"}.get(a.severity, "?")
        lines.append(f"### Anomalie {i}: `{a.tag}` — Schweregrad {sev} ({a.count}x)")
        lines.append(f"```\n{a.first_line[:200]}\n```")
        lines.append(f"**Hypothese:** {a.hypothesis}")
        lines.append(f"**Vorschlag:** {a.suggestion}")
        if a.llm_analysis:
            lines.append(f"\n**LLM-Analyse:**\n> {a.llm_analysis}")
        lines.append("")

    lines.append("> Automatisch erkannt durch Log-Anomalie-Detektor.")
    lines.append("> Wird geschlossen wenn Anomalie nicht mehr auftritt.")
    return "\n".join(lines)


def format_terminal(result: AnomalyResult) -> str:
    if result.skipped:
        return f"[Log-Anomalie] übersprungen: {result.skip_reason}"
    if not result.new_anomalies:
        return f"[Log-Anomalie] {result.lines_analyzed} Zeilen — keine neuen Anomalien"

    api_hint = "" if result.api_used else " (kein LLM — regelbasiert)"
    lines = [f"[Log-Anomalie]{api_hint} {len(result.new_anomalies)} neue Anomalie(n):"]
    for a in result.new_anomalies:
        sev = {1: "🟡", 2: "🟠", 3: "🔴"}.get(a.severity, "?")
        lines.append(f"  {sev} {a.tag} ({a.count}x) — {a.suggestion}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Log-Anomalie-Detektor")
    parser.add_argument("--project", default=".", help="Projekt-Root")
    parser.add_argument("--log", help="Log-Datei (überschreibt agent_eval.json)")
    parser.add_argument("--tail", type=int, default=200, help="Letzte N Zeilen")
    parser.add_argument("--reset-state", action="store_true", help="State zurücksetzen")
    args = parser.parse_args()

    root = Path(args.project).resolve()

    if args.reset_state:
        _save_state(root, set())
        print("[✓] State zurückgesetzt")

    log_p = Path(args.log) if args.log else None
    r = run(root, log_p, args.tail)
    print(format_terminal(r))
    if r.new_anomalies:
        print("\n--- Issue-Body Vorschau ---")
        print(build_issue_body(r))
