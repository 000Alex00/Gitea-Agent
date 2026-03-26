## Systemd-Service (--install-service)

Agent als Hintergrund-Daemon mit Auto-Restart.

---

### Voraussetzungen

> [!IMPORTANT]
> - Linux-System mit systemd (Debian, Ubuntu, Fedora, Arch)
> - Root-Rechte oder sudo
> - Agent getestet ([Rezept 04](04-health-check.md))

---

### Problem

tmux läuft nur während SSH-Session. Bei Neustart/Logout stoppt der Agent. Du willst systemd-Integration für 24/7-Betrieb.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Installation: Night-Modus Service
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
sudo python3 agent_start.py \
  --project ~/mein-projekt \
  --install-service night

# Output:
# [✓] Service-Datei erstellt: /etc/systemd/system/gitea-agent-night.service
# [✓] Service aktiviert (start bei Boot)
# [✓] Service gestartet

# Verifikation:
sudo systemctl status gitea-agent-night

# ──────────────────────────────────────────────────────────
# Installation: Patch-Modus Service
# ──────────────────────────────────────────────────────────
sudo python3 agent_start.py \
  --project ~/mein-projekt \
  --install-service patch \
  --watch-interval 300

# → Service: gitea-agent-patch.service
# → Scan alle 5 Minuten

# ──────────────────────────────────────────────────────────
# Logs anzeigen
# ──────────────────────────────────────────────────────────
sudo journalctl -u gitea-agent-night -f --since "1 hour ago"

# ──────────────────────────────────────────────────────────
# Service stoppen / starten / neustarten
# ──────────────────────────────────────────────────────────
sudo systemctl stop gitea-agent-night
sudo systemctl start gitea-agent-night
sudo systemctl restart gitea-night

# ──────────────────────────────────────────────────────────
# Service deaktivieren (kein Auto-Start mehr)
# ──────────────────────────────────────────────────────────
sudo systemctl disable gitea-agent-night

# ──────────────────────────────────────────────────────────
# Service entfernen
# ──────────────────────────────────────────────────────────
sudo systemctl stop gitea-agent-night
sudo systemctl disable gitea-agent-night
sudo rm /etc/systemd/system/gitea-agent-night.service
sudo systemctl daemon-reload
```

---

### Erklärung

**Generierte Service-Datei:**
```ini
# /etc/systemd/system/gitea-agent-night.service
[Unit]
Description=Gitea Agent Night Mode
After=network.target

[Service]
Type=simple
User=q366400
WorkingDirectory=/home/q366400/Gitea-Agent
ExecStart=/usr/bin/python3 agent_start.py \
  --project /home/q366400/mein-projekt \
  --watch \
  --night-mode \
  --eval-interval 14400

Restart=on-failure
RestartSec=60

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Wichtige Felder:**

| Feld | Bedeutung |
|------|-----------|
| `User=q366400` | Agent läuft als dieser User (nicht root) |
| `WorkingDirectory=...` | Agent-Code-Verzeichnis |
| `ExecStart=...` | Kommando zum Starten |
| `Restart=on-failure` | Auto-Restart bei Crash |
| `RestartSec=60` | 60 Sekunden Pause vor Restart |
| `StandardOutput=journal` | Logs in systemd-journal |

**Modi:**

1. **Night-Modus:**
   - `--night-mode` (nur low-risk Issues)
   - `--eval-interval 14400` (4 Stunden)
   - Für: nächtlicher Betrieb, minimale Störung

2. **Patch-Modus:**
   - Kein `--night-mode` (alle Issues)
   - `--eval-interval 300` (5 Minuten, konfigurierbar)
   - Für: schnelle Iterationen, Bug-Sprints

---

### Best Practice

> [!TIP]
> **Beide Services parallel:**
> ```bash
> sudo python3 agent_start.py --project ~/proj --install-service night
> sudo python3 agent_start.py --project ~/proj --install-service patch
> 
> # Night: 23:00-07:00 (via systemd-Timer)
> # Patch: 09:00-18:00 (via systemd-Timer)
> ```

> [!TIP]
> **Log-Rotation:**
> ```bash
> # journald config: /etc/systemd/journald.conf
> sudo nano /etc/systemd/journald.conf
>
> [Journal]
> SystemMaxUse=500M
> MaxRetentionSec=1week
> 
> sudo systemctl restart systemd-journald
> ```

> [!TIP]
> **Service-Override für spezielle Konfiguration:**
> ```bash
> sudo systemctl edit gitea-agent-night
> 
> # Datei öffnet sich:
> [Service]
> Environment="PYTHONUNBUFFERED=1"
> Environment="LOG_LEVEL=DEBUG"
> 
> sudo systemctl daemon-reload
> sudo systemctl restart gitea-agent-night
> ```

---

### Warnung

> [!WARNING]
> **User-Permissions:**
> ```
> User=root  ← NICHT EMPFOHLEN
> ```
> → Agent läuft mit vollen Root-Rechten
> → Nutze dedizierten User: `gitea-agent`

> [!WARNING]
> **Working-Directory muss existieren:**
> ```ini
> WorkingDirectory=/home/user/nicht-existiert
> ```
> → Service startet nicht
> → `sudo systemctl status gitea-agent-night` zeigt Fehler

> [!WARNING]
> **Credentials in Environment-Variablen:**
> ```ini
> [Service]
> Environment="GITEA_TOKEN=xyz123"
> ```
> → Sichtbar in `systemctl show gitea-agent-night`
> → Besser: .env-Datei im WorkingDirectory

---

### Nächste Schritte

✅ Systemd-Service läuft  
→ [16 — Night vs Patch Modus](16-night-vs-patch.md)  
→ [14 — Watch-Modus mit tmux](14-watch-mode-tmux.md)  
→ [36 — Watch-Modus Crashes](36-watch-mode-crashes.md)
