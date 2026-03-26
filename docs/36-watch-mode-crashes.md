## Watch-Modus Crashes debuggen

Network-Timeout, Disk-Full, Memory-Leaks.

---

### Voraussetzungen

> [!IMPORTANT]
> - Watch-Modus konfiguriert ([Rezept 14](14-watch-mode-tmux.md))
> - Crashes treten auf

---

### Problem

Watch-Modus läuft, crasht nach X Stunden. Warum?

---

### Lösung

```bash
# ══════════════════════════════════════════════════════════
# Problem 1: Network-Timeout
# ══════════════════════════════════════════════════════════
# Watch-Modus crasht nach 12h

# Logs:
tail -f ~/mein-projekt/agent/data/agent.log
# [2024-01-15 03:00] Starting eval-run
# [2024-01-15 03:05] requests.exceptions.Timeout: HTTPConnectionPool

# Ursache: LLM-Server sleept (Inaktivität), wacht nicht auf

# Debugging:
curl http://localhost:8000/health
# → keine Antwort

# Lösung A: Timeout erhöhen
nano ~/mein-projekt/.env
# HTTP_TIMEOUT=120  # 2 Minuten statt 30 Sekunden

# Lösung B: Retry-Logic
nano ~/mein-projekt/.env
# HTTP_RETRIES=5
# HTTP_RETRY_DELAY=10

# Lösung C: Server-Warmup
# agent_start.py: Vor Eval-Run ein Health-Check

# ══════════════════════════════════════════════════════════
# Problem 2: Disk-Full
# ══════════════════════════════════════════════════════════
# Watch-Modus stoppt, keine Logs mehr

# Debugging:
df -h
# /dev/sda1  100%  (voll!)

du -sh ~/mein-projekt/agent/data/*
# 15G  agent.log

# Ursache: Log-Rotation fehlt

# Lösung:
nano ~/mein-projekt/.env
# LOG_MAX_SIZE=10  # MB
# LOG_BACKUP_COUNT=5

# Oder systemd logrotate:
sudo nano /etc/logrotate.d/gitea-agent
# /home/user/mein-projekt/agent/data/*.log {
#   daily
#   rotate 7
#   compress
#   missingok
# }

# ══════════════════════════════════════════════════════════
# Problem 3: Memory-Leak
# ══════════════════════════════════════════════════════════
# Watch-Modus wird langsamer, dann OOM-Kill

# Debugging:
top -p $(pgrep -f agent_start.py)
# PID    MEM     TIME
# 1234   3.2G    12:34  ← Memory steigt kontinuierlich

# Logs:
dmesg | grep -i oom
# Out of memory: Killed process 1234 (python3)

# Ursache: Context-Accumulation (alte Eval-Results nicht freigegeben)

# Lösung A: Eval-History begrenzen
nano ~/mein-projekt/agent/config/agent_eval.json
# {
#   "score_history_max_entries": 1000
# }

# Lösung B: Garbage-Collection forcieren
# agent_start.py: Nach jedem Eval
import gc
gc.collect()

# Lösung C: Restart täglich (systemd-Timer)
sudo systemctl edit --full gitea-agent-night.service
# [Service]
# RuntimeMaxSec=86400  # 24 Stunden, dann Restart

# ══════════════════════════════════════════════════════════
# Problem 4: Git-Lock
# ══════════════════════════════════════════════════════════
# Watch-Modus crasht mit "fatal: Unable to create '.git/index.lock'"

# Debugging:
ls -la ~/mein-projekt/.git/
# -rw-r--r-- 1 user user 0 Jan 15 03:00 index.lock

# Ursache: Vorheriger Agent-Crash ließ Lock zurück

# Lösung:
rm ~/mein-projekt/.git/index.lock

# Prävention: Cleanup on Startup
# agent_start.py:
def cleanup_git_locks(repo_path):
    lock_file = Path(repo_path) / ".git" / "index.lock"
    if lock_file.exists():
        lock_file.unlink()

# ══════════════════════════════════════════════════════════
# Problem 5: Credential-Expiry
# ══════════════════════════════════════════════════════════
# Watch-Modus läuft 48h, dann keine PRs mehr

# Logs:
# [✗] Gitea API: 401 Unauthorized

# Debugging:
curl -H "Authorization: token $GITEA_TOKEN" \
  https://gitea.example.com/api/v1/user
# {"message": "token is expired"}

# Ursache: Token hat Expiry-Date

# Lösung A: Token ohne Expiry erstellen
# Gitea → Settings → Applications → No expiration

# Lösung B: Token-Rotation
# Cron-Job lädt neuen Token aus Secret-Manager

# ══════════════════════════════════════════════════════════
# Problem 6: Exception-Loop
# ══════════════════════════════════════════════════════════
# Watch-Modus crasht sofort nach Start

# Logs:
# [2024-01-15 10:00] Starting watch...
# [2024-01-15 10:00] ERROR: KeyError: 'tests'
# [2024-01-15 10:00] Restarting...
# [2024-01-15 10:00] ERROR: KeyError: 'tests'
# → Loop

# Debugging:
python3 agent_start.py --project ~/proj --doctor
# [✗] Config invalid: agent_eval.json missing 'tests' field

# Lösung:
nano ~/mein-projekt/agent/config/agent_eval.json
# {"tests": []}  ← Feld hinzufügen
```

---

### Erklärung

**Häufige Crash-Ursachen:**

| Ursache | Symptom | Lösung |
|---------|---------|--------|
| Network-Timeout | Crash nach X Stunden | Timeout erhöhen, Retry |
| Disk-Full | Logs stoppen | Log-Rotation |
| Memory-Leak | OOM-Kill | History begrenzen, GC |
| Git-Lock | "Unable to create lock" | Lock-File löschen |
| Credential-Expiry | 401 nach Tagen | Token ohne Expiry |
| Exception-Loop | Instant-Crash, Restart-Loop | Config validieren |

**Monitoring-Setup:**

```bash
# Systemd-Service mit Auto-Restart
[Service]
Restart=on-failure
RestartSec=60
RuntimeMaxSec=86400  # Max 24h Laufzeit

# Memory-Limit
MemoryMax=2G

# Logs
StandardOutput=journal
StandardError=journal
```

---

### Best Practice

> [!TIP]
> **Health-Checks in Watch-Loop:**
> ```python
> while watch_mode:
>     # Pre-Flight-Checks
>     if not check_disk_space():
>         log.error("Disk space low, pausing...")
>         time.sleep(3600)
>         continue
>     
>     if not check_server_health():
>         log.warning("Server unreachable, skipping...")
>         time.sleep(eval_interval)
>         continue
>     
>     run_eval()
> ```

> [!TIP]
> **Graceful-Shutdown:**
> ```python
> import signal
> 
> def signal_handler(sig, frame):
>     print("[Agent] Shutting down gracefully...")
>     cleanup_git_locks()
>     sys.exit(0)
> 
> signal.signal(signal.SIGINT, signal_handler)
> signal.signal(signal.SIGTERM, signal_handler)
> ```

> [!TIP]
> **Monitoring-Dashboard:**
> ```bash
> # Prometheus-Exporter
> GET /metrics
> 
> agent_uptime_seconds 43200
> agent_eval_runs_total 12
> agent_crashes_total 0
> agent_memory_bytes 256000000
> ```

---

### Warnung

> [!WARNING]
> **RuntimeMaxSec zu kurz:**
> ```ini
> RuntimeMaxSec=3600  # 1 Stunde
> → Service wird mitten in Eval-Lauf gekillt
> ```
> → Minimum: 2× eval_interval

> [!WARNING]
> **Memory-Limit zu niedrig:**
> ```ini
> MemoryMax=512M
> → OOM-Kill bei großen Repos
> ```
> → Test mit realistischem Workload

> [!WARNING]
> **Auto-Restart ohne Fix:**
> ```
> Exception-Loop + Restart=always
> → Agent crashed/restarted 1000× in Logs
> → System-Last
> ```
> → RestartSec=60 + MaxStartups=3

---

### Nächste Schritte

✅ Watch-Modus stabilisiert  
→ [14 — Watch-Modus tmux](14-watch-mode-tmux.md)  
→ [15 — Systemd-Service](15-watch-mode-systemd.md)  
→ [34 — Eval-Debugging](34-debug-eval-fail.md)
