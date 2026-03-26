## Staleness-Check (Server-Code-Freshness)

Issue wenn Server-Code älter als letzter Commit.

---

### Voraussetzungen

> [!IMPORTANT]
> - Watch-Modus aktiv ([Rezept 14](14-watch-mode-tmux.md))
> - Server-Code in git-Repo

---

### Problem

Agent testet Server-Version von gestern, obwohl heute Fixes committed wurden. Du willst automatischen Check: "Ist Server aktuell?"

---

### Lösung

```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "staleness_check": true,
  "staleness_check_interval": 7200,
  "server_repo_path": "/home/user/mein-server",
  "tests": [
    {
      "name": "Version-Check",
      "message": "/version",
      "expected_keywords": ["version"],
      "weight": 1,
      "tag": "health"
    }
  ]
}
```

**Watch-Modus Verhalten:**

```bash
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --watch \
  --eval-interval 1800

# ──────────────────────────────────────────────────────────
# Szenario: Server nicht neu gestartet nach Commit
# ──────────────────────────────────────────────────────────
# 10:00 — Commit in ~/mein-server: "Fix RAG-Bug"
# 10:30 — Agent Eval-Lauf:
#         [!] Server-Code veraltet:
#             Letzter Commit: 10:00
#             Server gestartet: 09:00 (1 Stunde alt)
#         
#         Issue #55 erstellt:
#         Titel: "[STALENESS] Server-Code nicht aktuell"
#         Body:
#         Der Server verwendet Code von vor 1 Stunde.
#         
#         Letzter Commit: abc123 "Fix RAG-Bug" (10:00)
#         Server gestartet: 09:00
#         
#         Aktion erforderlich:
#         sudo systemctl restart mein-server
```

---

### Erklärung

**Staleness-Check Logik:**

```python
# evaluation.py (vereinfacht)
import subprocess
from datetime import datetime

def check_staleness(repo_path, server_start_time):
    # Letzter Commit-Timestamp
    result = subprocess.run(
        ["git", "-C", repo_path, "log", "-1", "--format=%ct"],
        capture_output=True, text=True
    )
    last_commit_time = int(result.stdout.strip())
    
    if last_commit_time > server_start_time:
        delta = last_commit_time - server_start_time
        return {
            "stale": True,
            "age_seconds": delta,
            "last_commit": last_commit_time
        }
    
    return {"stale": False}
```

**Server-Start-Zeit ermitteln:**

1. **Systemd:**
   ```bash
   systemctl show mein-server.service --property=ActiveEnterTimestamp
   ```

2. **Process-Start:**
   ```bash
   ps -p <pid> -o lstart=
   ```

3. **Health-Endpunkt:**
   ```json
   GET /health
   {"status": "ok", "uptime_seconds": 3600, "started_at": "2024-01-15T09:00:00Z"}
   ```

**Staleness-Interval:**

- `staleness_check_interval: 7200` (2 Stunden)
- Check wird nicht **bei jedem** Eval-Lauf ausgeführt
- Nur alle 2 Stunden (reduziert git-Overhead)

---

### Best Practice

> [!TIP]
> **Health-Endpunkt mit Start-Zeit:**
> ```python
> # server.py
> import time
> 
> SERVER_START_TIME = time.time()
> 
> @app.route("/health")
> def health():
>     return {
>         "status": "ok",
>         "uptime": time.time() - SERVER_START_TIME,
>         "started_at": datetime.fromtimestamp(SERVER_START_TIME).isoformat()
>     }
> ```

> [!TIP]
> **Auto-Restart nach Commit (Git-Hook):**
> ```bash
> # ~/mein-server/.git/hooks/post-commit
> #!/bin/bash
> echo "Commit detected, restarting server..."
> sudo systemctl restart mein-server
> ```

> [!TIP]
> **Staleness nur bei kritischen Änderungen:**
> ```json
> {
>   "staleness_check": true,
>   "staleness_check_paths": [
>     "src/core/**",
>     "src/api/**"
>   ]
> }
> ```
> → Ignore: README, Tests, Docs

---

### Warnung

> [!WARNING]
> **Server-Repo-Path falsch:**
> ```json
> {"server_repo_path": "/home/user/nicht-existiert"}
> ```
> → Staleness-Check schlägt fehl
> → Keine Issues, aber Feature inaktiv

> [!WARNING]
> **Hot-Reload Server:**
> ```
> Server nutzt Hot-Reload (Flask --reload, nodemon)
> → Process-Start-Zeit ändert sich NICHT
> → Staleness-Check funktioniert NICHT
> ```
> → Expliziten /version-Endpunkt mit git-hash implementieren

> [!WARNING]
> **Zu kurzes Interval:**
> ```json
> {"staleness_check_interval": 60}  // 1 Minute
> ```
> → git-log bei jedem Eval → I/O-Last
> → Minimum: 1800 (30 Minuten)

---

### Nächste Schritte

✅ Staleness-Check konfiguriert  
→ [20 — AST-Skeleton](20-ast-skeleton.md)  
→ [24 — Gitea-Version-Compare](24-gitea-version-compare.md)  
→ [36 — Watch-Modus Crashes](36-watch-mode-crashes.md)
