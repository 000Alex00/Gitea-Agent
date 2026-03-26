"""
log_analyzer.template.py — Vorlage für projektspezifische Log-Analyse.

Kopieren nach:
    agent/config/log_analyzer.py   (neue Struktur)
    tools/log_analyzer.py          (Legacy)

Konfiguration (agent_eval.json):
    "log_path":    "/pfad/zu/app.log"
    "log_analysis_interval_minutes": 120
    "log_analysis": {
        "tail_lines":  200,
        "llm_enabled": false,
        "llm_url":     "http://localhost:11434/api/generate",
        "llm_model":   "llama3",
        "llm_timeout": 30
    }

Aufgerufen von:
    agent_start.py → cmd_watch() nach jedem Eval-Zyklus
    Erwartet: run() → LogAnalysisResult, format_terminal(result) → str
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Konfiguration — wird aus agent_eval.json geladen
# ---------------------------------------------------------------------------

_AGENT_EVAL_PATHS = [
    Path(__file__).parent.parent / "tests" / "agent_eval.json",   # neue Struktur
    Path(__file__).parent.parent / "agent_eval.json",             # Legacy
]


def _load_eval_cfg() -> dict:
    for p in _AGENT_EVAL_PATHS:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {}


# ---------------------------------------------------------------------------
# Bekannte Fehlermuster (regelbasiert)
# ---------------------------------------------------------------------------

KNOWN_PATTERNS: list[dict] = [
    {
        "pattern": re.compile(r"(ConnectionRefusedError|Connection refused)", re.IGNORECASE),
        "tag": "connectivity",
        "hypothesis": "Zieldienst nicht erreichbar",
        "suggestion": "Dienst prüfen: systemctl status, Ports prüfen, Firewall-Regeln",
    },
    {
        "pattern": re.compile(r"(TimeoutError|timed out|timeout)", re.IGNORECASE),
        "tag": "timeout",
        "hypothesis": "Anfrage-Timeout — Dienst antwortet zu langsam",
        "suggestion": "Timeout-Werte erhöhen oder Dienst-Performance prüfen",
    },
    {
        "pattern": re.compile(r"(MemoryError|OOMKilled|Killed|out of memory)", re.IGNORECASE),
        "tag": "memory",
        "hypothesis": "Speicher-Erschöpfung",
        "suggestion": "RAM-Nutzung analysieren, Modell-Parameter (n_ctx, n_batch) reduzieren",
    },
    {
        "pattern": re.compile(r"(CUDA|GPU|cuda error|device-side assert)", re.IGNORECASE),
        "tag": "gpu",
        "hypothesis": "GPU/CUDA-Fehler",
        "suggestion": "nvidia-smi prüfen, GPU-Treiber, VRAM-Auslastung kontrollieren",
    },
    {
        "pattern": re.compile(r"(ImportError|ModuleNotFoundError|No module named)", re.IGNORECASE),
        "tag": "import",
        "hypothesis": "Fehlende Abhängigkeit",
        "suggestion": "pip install prüfen, virtualenv aktiviert? requirements.txt aktuell?",
    },
    {
        "pattern": re.compile(r"(PermissionError|Permission denied)", re.IGNORECASE),
        "tag": "permission",
        "hypothesis": "Berechtigungsfehler beim Dateizugriff",
        "suggestion": "Dateirechte prüfen (chmod/chown), Pfade validieren",
    },
    {
        "pattern": re.compile(r"(Traceback|Exception|Error:)", re.IGNORECASE),
        "tag": "exception",
        "hypothesis": "Unbehandelte Ausnahme im Code",
        "suggestion": "Stack-Trace analysieren, Fehler-Handling ergänzen",
    },
]


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------

@dataclass
class LogFinding:
    line_no: int
    line: str
    tag: str
    hypothesis: str
    suggestion: str
    llm_generated: bool = False


@dataclass
class LogAnalysisResult:
    log_path: str = ""
    lines_analyzed: int = 0
    findings: list[LogFinding] = field(default_factory=list)
    llm_summary: str = ""
    llm_error: str = ""
    skipped: bool = False
    skip_reason: str = ""

    @property
    def error_count(self) -> int:
        return len(self.findings)

    @property
    def tags(self) -> list[str]:
        return list({f.tag for f in self.findings})


# ---------------------------------------------------------------------------
# Regelbasierte Analyse
# ---------------------------------------------------------------------------

def _analyze_rules(lines: list[str]) -> list[LogFinding]:
    findings: list[LogFinding] = []
    matched_lines: set[int] = set()

    for i, line in enumerate(lines, 1):
        for pat in KNOWN_PATTERNS:
            if pat["pattern"].search(line):
                if i not in matched_lines:
                    findings.append(LogFinding(
                        line_no=i,
                        line=line.rstrip(),
                        tag=pat["tag"],
                        hypothesis=pat["hypothesis"],
                        suggestion=pat["suggestion"],
                    ))
                    matched_lines.add(i)
                break  # ein Treffer pro Zeile

    return findings


# ---------------------------------------------------------------------------
# LLM-gestützte Analyse (optional)
# ---------------------------------------------------------------------------

def _call_llm_local(url: str, model: str, prompt: str, timeout: int) -> str:
    """HTTP-Aufruf gegen lokale LLM-API (Ollama-Format)."""
    import urllib.request
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 512},
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
        return data.get("response", "").strip()


def _call_llm_claude(model: str, prompt: str, max_tokens: int = 512) -> str:
    """Claude API via anthropic SDK."""
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def _analyze_llm(lines: list[str], rule_findings: list[LogFinding], cfg: dict) -> tuple[str, str]:
    """
    Sendet unbekannte Log-Zeilen an LLM.
    Gibt (summary, error) zurück.
    """
    la_cfg = cfg.get("log_analysis", {})
    llm_url   = la_cfg.get("llm_url",     "http://localhost:11434/api/generate")
    llm_model = la_cfg.get("llm_model",   "llama3")
    llm_timeout = int(la_cfg.get("llm_timeout", 30))
    use_claude  = cfg.get("claude_api_enabled", False)
    claude_model = cfg.get("claude_model", "claude-sonnet-4-6")

    # Zeilen die nicht durch Regeln erfasst wurden
    known_line_nos = {f.line_no for f in rule_findings}
    unknown_lines = [
        f"[{i}] {l.rstrip()}"
        for i, l in enumerate(lines, 1)
        if i not in known_line_nos and any(kw in l.lower() for kw in ("error", "warn", "exception", "fail", "critical"))
    ][:30]  # max. 30 Zeilen ans LLM

    if not unknown_lines:
        return "", ""

    prompt = (
        "Analysiere folgende Log-Zeilen aus einer Produktionsanwendung.\n"
        "Identifiziere Root-Cause-Hypothesen und konkrete Lösungsvorschläge.\n"
        "Antworte auf Deutsch. Sei präzise und praxisorientiert.\n\n"
        "Log-Zeilen:\n"
        + "\n".join(unknown_lines)
        + "\n\nAnalyse:"
    )

    try:
        if use_claude:
            summary = _call_llm_claude(claude_model, prompt, max_tokens=512)
        else:
            summary = _call_llm_local(llm_url, llm_model, prompt, llm_timeout)
        return summary, ""
    except Exception as exc:
        return "", str(exc)


# ---------------------------------------------------------------------------
# Haupt-Einstiegspunkt
# ---------------------------------------------------------------------------

def run() -> LogAnalysisResult:
    """
    Analysiert das konfigurierte Log-File.
    Wird von agent_start.py cmd_watch() aufgerufen.
    """
    result = LogAnalysisResult()
    cfg = _load_eval_cfg()
    log_path_str = cfg.get("log_path", "")

    if not log_path_str:
        result.skipped = True
        result.skip_reason = "log_path in agent_eval.json nicht konfiguriert"
        return result

    log_path = Path(log_path_str)
    if not log_path.exists():
        result.skipped = True
        result.skip_reason = f"Log-Datei nicht gefunden: {log_path}"
        return result

    result.log_path = str(log_path)

    la_cfg = cfg.get("log_analysis", {})
    tail_lines = int(la_cfg.get("tail_lines", 200))
    llm_enabled = bool(la_cfg.get("llm_enabled", False))

    # Letzte N Zeilen lesen
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()[-tail_lines:]
        result.lines_analyzed = len(lines)
    except Exception as exc:
        result.skipped = True
        result.skip_reason = f"Lesefehler: {exc}"
        return result

    # Regelbasierte Analyse
    result.findings = _analyze_rules(lines)

    # Optionale LLM-Analyse
    if llm_enabled:
        summary, err = _analyze_llm(lines, result.findings, cfg)
        result.llm_summary = summary
        result.llm_error = err

    return result


# ---------------------------------------------------------------------------
# Ausgabe-Formatierung
# ---------------------------------------------------------------------------

def format_terminal(result: LogAnalysisResult) -> str:
    if result.skipped:
        return f"[Log-Analyse] übersprungen: {result.skip_reason}"

    lines = [f"[Log-Analyse] {result.log_path} — {result.lines_analyzed} Zeilen analysiert"]

    if not result.findings:
        lines.append("  ✅ Keine bekannten Fehlermuster gefunden")
    else:
        seen_tags: set[str] = set()
        for f in result.findings[:10]:  # max. 10 Findings anzeigen
            if f.tag not in seen_tags:
                icon = "🤖" if f.llm_generated else "🔍"
                lines.append(f"  {icon} [{f.tag}] Z.{f.line_no}: {f.hypothesis}")
                lines.append(f"       → {f.suggestion}")
                seen_tags.add(f.tag)
        if len(result.findings) > 10:
            lines.append(f"  … und {len(result.findings) - 10} weitere Treffer")

    if result.llm_summary:
        lines.append("\n  [LLM-Analyse]")
        for ln in result.llm_summary.splitlines()[:8]:
            lines.append(f"  {ln}")

    if result.llm_error:
        lines.append(f"  ⚠️  LLM nicht erreichbar: {result.llm_error}")

    return "\n".join(lines)
