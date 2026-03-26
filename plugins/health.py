"""
plugins/health.py — Generische Health-Check-Engine (Issue #87).

Liest agent/config/health_checks.json und führt konfigurierbare Checks aus.
Unterstützte Typen: http, tcp, process, disk.

Aufgerufen von:
    agent_start.py -> cmd_watch() wenn FEATURES["health_checks"] aktiv
"""

import json
import socket
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# Bekannte DB-Defaults für --setup Wizard
DB_DEFAULTS = {
    "postgresql": [{"name": "PostgreSQL", "type": "tcp",  "target": "localhost:5432"}],
    "redis":      [{"name": "Redis",      "type": "tcp",  "target": "localhost:6379"}],
    "mongodb":    [{"name": "MongoDB",    "type": "tcp",  "target": "localhost:27017"}],
    "chroma":     [
        {"name": "Chroma",     "type": "tcp",  "target": "localhost:8000"},
        {"name": "Chroma API", "type": "http", "target": "http://localhost:8000/api/v1/heartbeat"},
    ],
    "mysql":      [{"name": "MySQL",      "type": "tcp",  "target": "localhost:3306"}],
}

CONFIG_PATH_NEW    = "agent/config/health_checks.json"
CONFIG_PATH_LEGACY = "health_checks.json"


@dataclass
class CheckResult:
    name: str
    type: str
    passed: bool
    message: str = ""
    consecutive_failures: int = 0


@dataclass
class HealthResult:
    checks: list[CheckResult] = field(default_factory=list)
    failures: list[CheckResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return len(self.failures) == 0


def _load_config(project_root: Path) -> dict | None:
    for rel in (CONFIG_PATH_NEW, CONFIG_PATH_LEGACY):
        p = project_root / rel
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return None
    return None


def _check_http(target: str, timeout: int = 5) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(target, timeout=timeout) as resp:
            return resp.status < 500, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        ok = e.code < 500
        return ok, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)


def _check_tcp(target: str, timeout: int = 3) -> tuple[bool, str]:
    try:
        host, port_str = target.rsplit(":", 1)
        port = int(port_str)
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"{host}:{port} erreichbar"
    except Exception as e:
        return False, str(e)


def _check_process(target: str) -> tuple[bool, str]:
    try:
        out = subprocess.check_output(["pgrep", "-f", target],
                                      stderr=subprocess.DEVNULL).decode().strip()
        pids = out.splitlines()
        return bool(pids), f"PID(s): {', '.join(pids)}" if pids else "nicht gefunden"
    except subprocess.CalledProcessError:
        return False, f"Prozess '{target}' nicht gefunden"
    except Exception as e:
        return False, str(e)


def _check_disk(target: str, threshold: int = 90) -> tuple[bool, str]:
    try:
        import shutil
        usage = shutil.disk_usage(target)
        pct = int(usage.used / usage.total * 100)
        ok = pct < threshold
        return ok, f"{pct}% belegt (Limit: {threshold}%)"
    except Exception as e:
        return False, str(e)


def run_checks(project_root: Path) -> HealthResult:
    """Führt alle konfigurierten Health-Checks aus."""
    result = HealthResult()
    cfg = _load_config(project_root)
    if cfg is None:
        return result

    threshold = cfg.get("consecutive_failures_before_issue", 3)
    state_file = project_root / "agent" / "data" / "health_state.json"

    # Persistierten Fehler-Zustand laden
    state: dict[str, int] = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    for check in cfg.get("checks", []):
        name    = check.get("name", "?")
        kind    = check.get("type", "http")
        target  = check.get("target", "")
        timeout = check.get("timeout", 5)

        if kind == "http":
            passed, msg = _check_http(target, timeout)
        elif kind == "tcp":
            passed, msg = _check_tcp(target, timeout)
        elif kind == "process":
            passed, msg = _check_process(target)
        elif kind == "disk":
            passed, msg = _check_disk(target, check.get("threshold", 90))
        else:
            passed, msg = False, f"Unbekannter Check-Typ: {kind}"

        if passed:
            state.pop(name, None)
            consecutive = 0
        else:
            state[name] = state.get(name, 0) + 1
            consecutive = state[name]

        cr = CheckResult(name=name, type=kind, passed=passed,
                         message=msg, consecutive_failures=consecutive)
        result.checks.append(cr)
        if not passed and consecutive >= threshold:
            result.failures.append(cr)

    # Zustand persistieren
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass

    return result


def format_terminal(result: HealthResult) -> str:
    if not result.checks:
        return ""
    lines = ["[Health-Checks]"]
    for c in result.checks:
        icon = "✅" if c.passed else f"❌ ({c.consecutive_failures}x)"
        lines.append(f"  {icon}  {c.name:<20} {c.message}")
    return "\n".join(lines)
