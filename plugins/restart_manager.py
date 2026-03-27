"""
plugins/restart_manager.py — Granulares Service-Neustart-Management.

Löst das Problem: nicht jeder Dienst darf automatisch neugestartet werden.
  - Dienste mit auto_restart=true → werden gestartet, Ergebnis geloggt
  - Dienste mit auto_restart=false → Issue wird erstellt, kein Neustart

Konfiguration in agent_eval.json:
  "services": [
    {"name": "api-worker",   "cmd": "./scripts/restart_worker.sh",   "auto_restart": true,  "wait_seconds": 2},
    {"name": "main-server",  "cmd": "./scripts/restart_server.sh",   "auto_restart": false, "on_regression": "issue"},
    {"name": "cache",        "cmd": "systemctl restart redis",       "auto_restart": true}
  ]

Rückwärtskompatibel: wenn kein "services"-Array, wird "restart_script" (altes Feld) genutzt.

Aufgerufen von:
  agent_start.py → _restart_server_for_eval()  (--restart-before-eval)
  agent_start.py → cmd_watch()                 (Szenario 2: Inaktivität + neue Commits)
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Datenstrukturen
# ---------------------------------------------------------------------------

@dataclass
class ServiceResult:
    name: str
    cmd: str
    auto_restart: bool
    success: Optional[bool] = None   # None = nicht versucht
    returncode: Optional[int] = None
    error: str = ""


@dataclass
class RestartReport:
    restarted: list[ServiceResult] = field(default_factory=list)    # auto=True, erfolgreich
    failed: list[ServiceResult] = field(default_factory=list)       # auto=True, Fehler
    skipped: list[ServiceResult] = field(default_factory=list)      # auto=False
    warnings: list[str] = field(default_factory=list)               # allgemeine Warnungen
    legacy_mode: bool = False                                        # restart_script Fallback

    @property
    def has_manual_required(self) -> bool:
        return bool(self.skipped)

    @property
    def has_failures(self) -> bool:
        return bool(self.failed)

    @property
    def total_services(self) -> int:
        return len(self.restarted) + len(self.failed) + len(self.skipped)

    def to_markdown(self) -> str:
        """Erstellt Markdown-Block für Gitea-Issues und PR-Kommentare."""
        if self.legacy_mode and not self.restarted and not self.failed and not self.skipped:
            return ""

        lines = ["### Service-Neustart-Report\n"]

        if self.restarted:
            lines.append("**Automatisch neugestartet:**")
            for s in self.restarted:
                lines.append(f"- ✅ `{s.name}` — {s.cmd}")
            lines.append("")

        if self.failed:
            lines.append("**Fehler beim Neustart:**")
            for s in self.failed:
                err = f" — {s.error}" if s.error else f" (exit {s.returncode})"
                lines.append(f"- ❌ `{s.name}`{err}")
            lines.append("")

        if self.skipped:
            lines.append("**Manueller Neustart erforderlich:**")
            for s in self.skipped:
                lines.append(f"- ⚠️ `{s.name}` — `auto_restart: false` in agent_eval.json")
                lines.append(f"  ```")
                lines.append(f"  {s.cmd}")
                lines.append(f"  ```")
            lines.append("")
            lines.append("> Diese Dienste wurden **nicht** automatisch neugestartet.")
            lines.append("> Manueller Eingriff erforderlich bevor Eval korrekt ist.")
            lines.append("")

        if self.warnings:
            for w in self.warnings:
                lines.append(f"> ⚠️ {w}")

        return "\n".join(lines)

    def to_terminal(self) -> str:
        """Kompakte Terminal-Ausgabe."""
        parts = []
        if self.restarted:
            parts.append(f"[Restart] {len(self.restarted)} gestartet: " +
                         ", ".join(s.name for s in self.restarted))
        if self.failed:
            parts.append(f"[Restart] ❌ {len(self.failed)} fehlgeschlagen: " +
                         ", ".join(s.name for s in self.failed))
        if self.skipped:
            names = ", ".join(s.name for s in self.skipped)
            parts.append(f"[!] Manueller Neustart erforderlich: {names}")
        if not parts:
            return ""
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Konfiguration lesen
# ---------------------------------------------------------------------------

def _load_services(eval_cfg: dict) -> list[dict]:
    """
    Liest Services-Array aus agent_eval.json.
    Fallback: restart_script → einzelner Auto-Restart-Service.
    """
    services = eval_cfg.get("services")
    if services and isinstance(services, list):
        return services

    # Rückwärtskompatibilität: altes restart_script-Feld
    restart_script = eval_cfg.get("restart_script")
    if restart_script:
        return [{"name": "server", "cmd": restart_script, "auto_restart": True}]

    return []


# ---------------------------------------------------------------------------
# Neustart-Ausführung
# ---------------------------------------------------------------------------

def restart_services(
    eval_cfg: dict,
    project_root: Optional[Path] = None,
    trigger: str = "manual",
) -> RestartReport:
    """
    Führt Service-Neustarts gemäß services-Matrix durch.

    Args:
        eval_cfg:     Geladene agent_eval.json als dict
        project_root: Für relative cmd-Pfade (optional)
        trigger:      Auslöser für Logs (z.B. "watch", "pr", "manual")

    Returns:
        RestartReport mit Ergebnissen + Markdown-Output
    """
    report = RestartReport()
    services = _load_services(eval_cfg)

    if not services:
        report.warnings.append("Keine Services in agent_eval.json konfiguriert (services-Array fehlt)")
        return report

    # Legacy-Modus erkennen (nur restart_script, kein services-Array)
    if not eval_cfg.get("services") and eval_cfg.get("restart_script"):
        report.legacy_mode = True

    for svc in services:
        name = svc.get("name", "unnamed")
        cmd = svc.get("cmd", "")
        auto_restart = svc.get("auto_restart", True)
        wait_seconds = svc.get("wait_seconds", 0)

        sr = ServiceResult(name=name, cmd=cmd, auto_restart=auto_restart)

        if not auto_restart:
            sr.success = None  # nicht versucht
            report.skipped.append(sr)
            continue

        if not cmd:
            sr.success = False
            sr.error = "cmd leer"
            report.failed.append(sr)
            continue

        try:
            # cmd kann Shell-String oder Pfad sein
            result = subprocess.run(
                cmd, shell=isinstance(cmd, str), check=False,
                cwd=project_root,
                capture_output=True, text=True,
            )
            sr.returncode = result.returncode
            if result.returncode == 0:
                sr.success = True
                report.restarted.append(sr)
            else:
                sr.success = False
                sr.error = (result.stderr or result.stdout or "").strip()[:200]
                report.failed.append(sr)
        except Exception as e:
            sr.success = False
            sr.error = str(e)[:200]
            report.failed.append(sr)

        if wait_seconds > 0:
            time.sleep(wait_seconds)

    return report


# ---------------------------------------------------------------------------
# Issue-Titel für manuelle Neustarts
# ---------------------------------------------------------------------------

def build_manual_restart_issue(report: RestartReport, trigger: str = "") -> tuple[str, str]:
    """
    Erstellt Titel + Body für ein Gitea-Issue wenn manuelle Neustarts nötig sind.

    Returns:
        (title, body)  oder  ("", "") wenn kein Issue nötig
    """
    if not report.skipped:
        return "", ""

    names = ", ".join(s.name for s in report.skipped)
    trigger_str = f" nach {trigger}" if trigger else ""
    title = f"[Auto] Manueller Neustart erforderlich{trigger_str}: {names}"

    body_lines = [
        "## Manueller Neustart erforderlich\n",
        f"Folgende Dienste wurden **nicht** automatisch neugestartet, "
        f"da `auto_restart: false` in `agent_eval.json`:\n",
    ]
    for s in report.skipped:
        body_lines.append(f"### `{s.name}`")
        body_lines.append(f"```bash\n{s.cmd}\n```")
        body_lines.append("")

    body_lines += [
        "### Hintergrund",
        "Der Watch-Agent hat eine Änderung erkannt, die einen Service-Neustart erfordern würde.",
        "Da dieser Dienst kritisch ist (`auto_restart: false`), wurde kein automatischer Neustart durchgeführt.",
        "",
        "### Nächste Schritte",
        "1. Dienst manuell neustarten (Befehl oben)",
        "2. Eval prüfen: `python3 agent_start.py --project <path> --eval`",
        "3. Issue schließen wenn Eval grün",
        "",
        "> Automatisch erstellt vom Watch-Agenten.",
    ]

    if report.failed:
        body_lines.append("\n### Fehlgeschlagene Auto-Neustarts")
        for s in report.failed:
            body_lines.append(f"- ❌ `{s.name}`: {s.error or f'exit {s.returncode}'}")

    return title, "\n".join(body_lines)
