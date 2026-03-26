## Log-Analyzer (Custom-Integration)

Eigenen Analyzer für Server-Logs einbinden.

---

### Voraussetzungen

> [!IMPORTANT]
> - Python 3.10+ (stdlib only)
> - Server schreibt strukturierte Logs

---

### Problem

Eval failt, aber warum? Server-Logs haben Details. Du willst: automatische Log-Analyse im Issue.

---

### Lösung

```python
# ──────────────────────────────────────────────────────────
# Schritt 1: Custom-Analyzer schreiben
# ──────────────────────────────────────────────────────────
# ~/mein-projekt/agent/plugins/log_analyzer.py

import re
from pathlib import Path
from datetime import datetime, timedelta

def analyze_logs(test_name, test_time, log_dir):
    """Analyze server logs for test failures.
    
    Args:
        test_name: Name of failed test
        test_time: Timestamp when test ran
        log_dir: Path to server log directory
    
    Returns:
        dict with analysis results
    """
    # 1. Relevante Logs finden (±5 Minuten um test_time)
    start = test_time - timedelta(minutes=5)
    end = test_time + timedelta(minutes=5)
    
    errors = []
    warnings = []
    
    log_file = Path(log_dir) / "server.log"
    
    with open(log_file) as f:
        for line in f:
            # Parse Log-Line
            match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+) \| (.+)', line)
            if not match:
                continue
            
            timestamp_str, level, message = match.groups()
            timestamp = datetime.fromisoformat(timestamp_str)
            
            # Nur Logs im Zeitfenster
            if not (start <= timestamp <= end):
                continue
            
            # Errors/Warnings sammeln
            if level == "ERROR":
                errors.append({
                    "time": timestamp_str,
                    "message": message
                })
            elif level == "WARNING":
                warnings.append({
                    "time": timestamp_str,
                    "message": message
                })
    
    # 2. Root-Cause identifizieren
    root_cause = None
    
    for error in errors:
        if "ChromaDB" in error["message"]:
            root_cause = "Vector-DB connection failed"
        elif "Model not loaded" in error["message"]:
            root_cause = "LLM model initialization failed"
        elif "KeyError" in error["message"]:
            root_cause = "Missing configuration key"
    
    return {
        "test_name": test_name,
        "errors": errors,
        "warnings": warnings,
        "root_cause": root_cause,
        "log_snippet": errors[:3] if errors else warnings[:3]
    }

# ──────────────────────────────────────────────────────────
# Schritt 2: Agent-Konfiguration
# ──────────────────────────────────────────────────────────
# ~/mein-projekt/agent/config/agent_eval.json

{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "log_analyzer": {
    "enabled": true,
    "module": "plugins.log_analyzer",
    "function": "analyze_logs",
    "log_dir": "/var/log/mein-server"
  },
  "tests": [
    {
      "name": "RAG-Query",
      "message": "Was steht in Kapitel 1?",
      "expected_keywords": ["Kapitel"],
      "weight": 2,
      "tag": "rag"
    }
  ]
}

# ──────────────────────────────────────────────────────────
# Schritt 3: Watch-Modus mit Log-Analyse
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --watch \
  --eval-interval 3600

# Bei Test-Failure:
# ──────────────────────────────────────────────────────────
# [12:00] Eval-Run: Test "RAG-Query" FAIL
# [12:00] Running log analyzer...
# [12:00] Log analysis complete
# [12:00] Issue #101 created with log analysis

# ──────────────────────────────────────────────────────────
# Issue #101: RAG-Query fehlschlägt
# ──────────────────────────────────────────────────────────
# Test "RAG-Query" schlug fehl.
# 
# ## Log-Analyse
# 
# **Root-Cause:** Vector-DB connection failed
# 
# **Errors (11:58-12:02):**
# ```
# 2024-01-15 11:59:23 | ERROR | ChromaDB connection timeout
# 2024-01-15 11:59:25 | ERROR | Retrying connection... (1/3)
# 2024-01-15 11:59:30 | ERROR | Max retries exceeded
# ```
# 
# **Warnings (11:58-12:02):**
# ```
# 2024-01-15 11:58:45 | WARNING | High memory usage: 92%
# 2024-01-15 12:00:12 | WARNING | Slow query: 3.5s
# ```
# 
# **Empfohlene Aktion:**
# 1. ChromaDB-Service prüfen: `systemctl status chroma`
# 2. Memory-Leak untersuchen (92% usage)
# 3. Connection-Timeout erhöhen (Config)
```

---

### Erklärung

**Analyzer-Interface:**

```python
def analyze_logs(test_name: str, test_time: datetime, log_dir: str) -> dict:
    """
    Args:
        test_name: Name des fehlgeschlagenen Tests
        test_time: Zeitpunkt des Test-Laufs
        log_dir: Pfad zu Server-Log-Verzeichnis
    
    Returns:
        {
            "test_name": str,
            "errors": List[dict],
            "warnings": List[dict],
            "root_cause": Optional[str],
            "log_snippet": List[dict]
        }
    """
```

**Agent-Integration:**

```python
# agent_start.py (vereinfacht)
if test_failed:
    if config.get("log_analyzer", {}).get("enabled"):
        # Dynamisch laden
        module = importlib.import_module(config["log_analyzer"]["module"])
        analyzer_func = getattr(module, config["log_analyzer"]["function"])
        
        # Ausführen
        analysis = analyzer_func(
            test_name=test["name"],
            test_time=datetime.now(),
            log_dir=config["log_analyzer"]["log_dir"]
        )
        
        # In Issue integrieren
        issue_body += f"\n\n## Log-Analyse\n{format_analysis(analysis)}"
```

**Log-Format-Beispiele:**

### JSON-Logs:
```python
import json

with open(log_file) as f:
    for line in f:
        log = json.loads(line)
        if log["level"] == "ERROR":
            errors.append(log)
```

### Syslog:
```python
import re

pattern = r'(\w+ \d+ \d{2}:\d{2}:\d{2}) \w+ (\w+)\[\d+\]: (.+)'
match = re.match(pattern, line)
```

---

### Best Practice

> [!TIP]
> **Stacktrace-Extraktion:**
> ```python
> def extract_stacktrace(log_lines):
>     in_trace = False
>     trace = []
>     
>     for line in log_lines:
>         if "Traceback" in line:
>             in_trace = True
>         if in_trace:
>             trace.append(line)
>             if not line.startswith(" "):
>                 break
>     
>     return "\n".join(trace)
> ```

> [!TIP]
> **Log-Aggregation über Tags:**
> ```python
> # Bei tag-aggregierten Issues ([Rezept 18](18-tag-aggregation.md))
> def analyze_logs(test_names, test_time, log_dir):
>     # Alle Tests mit Tag "rag" → gemeinsame Log-Analyse
>     ...
> ```

> [!TIP]
> **Log-Rotation beachten:**
> ```python
> log_files = [
>     log_dir / "server.log",
>     log_dir / "server.log.1",  # rotiert
>     log_dir / "server.log.2.gz"  # komprimiert
> ]
> ```

---

### Warnung

> [!WARNING]
> **Log-Parsing Performance:**
> ```python
> # ✗ Ganze Log-Datei (10 GB) lesen
> with open(log_file) as f:
>     all_lines = f.readlines()
> 
> # ✓ Nur relevantes Zeitfenster
> with open(log_file) as f:
>     for line in f:
>         if timestamp in time_window:
>             process(line)
> ```

> [!WARNING]
> **Sensitive Daten in Logs:**
> ```
> ERROR | Auth failed: token=secret123
> → wird in Issue gepostet
> ```
> → Logs sanieren vor Issue-Post

> [!WARNING]
> **Log-Pfad-Permissions:**
> ```bash
> ls -la /var/log/mein-server/
> -rw------- 1 root root  # Agent kann nicht lesen
> ```
> → Agent-User zur log-Gruppe hinzufügen

---

### Nächste Schritte

✅ Log-Analyzer integriert  
→ [31 — Plugin-Architektur](31-plugin-architecture.md)  
→ [18 — Tag-Aggregation](18-tag-aggregation.md)  
→ [36 — Watch-Modus Crashes](36-watch-mode-crashes.md)
