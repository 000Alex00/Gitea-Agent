## Erstes Projekt einrichten (Setup-Wizard)

Interaktiver 6-Schritt-Wizard führt durch die komplette Einrichtung.

---

### Voraussetzungen

> [!IMPORTANT]
> - gitea-agent installiert ([Rezept 01](01-installation.md))
> - Gitea-Instanz erreichbar (URL + API-Token bereit)
> - Projekt-Repository in Gitea existiert
> - Lokales git-Repository geklont

---

### Problem

Du hast gitea-agent installiert und ein Projekt in Gitea. Jetzt brauchst du: `.env`-Datei, Labels in Gitea, `agent_eval.json` im Projekt. Manuell ist das fehleranfällig.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Setup-Wizard starten
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py --setup

# ──────────────────────────────────────────────────────────
# Schritt 1: Gitea-Verbindung
# ──────────────────────────────────────────────────────────
# Wizard fragt:
# Gitea URL (z.B. http://192.168.1.10:3001): http://localhost:3000
# Gitea User: admin
# Gitea API Token: 1234567890abcdef...
# Gitea Bot User (optional, Enter für gleichen): gitea-bot
# Gitea Bot Token (optional, Enter für gleichen): 

# → Prüft Verbindung via GET /api/v1/user
# → [✓] Verbindung erfolgreich

# ──────────────────────────────────────────────────────────
# Schritt 2: Repository
# ──────────────────────────────────────────────────────────
# Wizard fragt:
# Repository (user/name): admin/mein-projekt

# → Prüft via GET /api/v1/repos/admin/mein-projekt
# → [✓] Repository gefunden

# ──────────────────────────────────────────────────────────
# Schritt 3: Projektverzeichnis
# ──────────────────────────────────────────────────────────
# Wizard fragt:
# Absoluter Pfad zum Projekt: /home/user/mein-projekt

# → Prüft ob .git existiert
# → [✓] Git-Repository gefunden

# ──────────────────────────────────────────────────────────
# Schritt 4: Labels anlegen
# ──────────────────────────────────────────────────────────
# → Vergleicht settings.py Labels mit Gitea
# → [→] Erstelle Label: ready-for-agent (grün)
# → [→] Erstelle Label: agent-proposed (gelb)
# → [→] Erstelle Label: in-progress (blau)
# → [→] Erstelle Label: needs-review (orange)
# → [✓] 4 Labels angelegt

# ──────────────────────────────────────────────────────────
# Schritt 5: agent_eval.json
# ──────────────────────────────────────────────────────────
# Wizard fragt:
# Server URL (z.B. http://localhost:8000): http://localhost:8000
# Chat Endpoint (Enter für /chat): /chat
# Log-Pfad (optional): /home/user/mein-projekt/server.log
# Restart-Script (optional): /home/user/start_server.sh

# → Schreibt /home/user/mein-projekt/agent/config/agent_eval.json
# → [✓] agent_eval.json erstellt

# ──────────────────────────────────────────────────────────
# Schritt 6: .env schreiben
# ──────────────────────────────────────────────────────────
# → Sammelt alle Eingaben
# → Schreibt ~/Gitea-Agent/.env
# → [✓] .env geschrieben

# ──────────────────────────────────────────────────────────
# Abschluss: Health-Check
# ──────────────────────────────────────────────────────────
# Führt automatisch --doctor aus:
# [✓] Gitea-Verbindung
# [✓] Repository erreichbar
# [✓] Projektverzeichnis existiert
# [✓] Labels vorhanden
# [✓] agent_eval.json vorhanden
# [✓] .env korrekt

# → [✓] Setup abgeschlossen
```

---

### Erklärung

**Was wird erstellt?**

1. **`.env` im Agent-Verzeichnis:**
```bash
GITEA_URL=http://localhost:3000
GITEA_USER=admin
GITEA_TOKEN=1234567890abcdef...
GITEA_REPO=admin/mein-projekt
PROJECT_ROOT=/home/user/mein-projekt
```

2. **`agent/config/agent_eval.json` im Projekt:**
```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "log_path": "/home/user/mein-projekt/server.log",
  "restart_script": "/home/user/start_server.sh",
  "tests": []
}
```

3. **Labels in Gitea:**
- `ready-for-agent` (grün)
- `agent-proposed` (gelb)
- `in-progress` (blau)
- `needs-review` (orange)

**Warum interaktiv?**
- Keine Tippfehler in Pfaden/URLs
- Sofortige API-Validierung
- Überspringt bereits vorhandene Labels

---

### Best Practice

> [!TIP]
> **Bestehende Konfiguration überschreiben:**
> ```
> Datei .env existiert bereits. Überschreiben? (y/N): y
> ```
> → Wizard fragt bei jedem bestehenden File nach

> [!TIP]
> **Bot-Token optional:**
> ```
> Gitea Bot User (optional, Enter für gleichen): [Enter]
> ```
> → Verwendet Admin-Token auch für Kommentare (Ein-User-Setup)

> [!TIP]
> **Mehrere Projekte:**
> ```bash
# Projekt 1
python3 agent_start.py --setup
# → .env zeigt auf Projekt 1

# Projekt 2
python3 agent_start.py --setup
# → .env zeigt auf Projekt 2 (überschrieben)

# Zwischen Projekten wechseln:
cp .env.projekt1 .env  # oder .env manuell editieren
```

---

### Warnung

> [!WARNING]
> **API-Token-Scopes prüfen:**
> ```
> [!] Token-Scopes unzureichend
> → Benötigt: issue (read+write) + repository (read+write)
> ```
> → In Gitea: Settings → Applications → Token Scopes

> [!WARNING]
> **Pfad muss absolut sein:**
> ```
> [!] Pfad muss absolut sein (startet mit /)
> → Eingabe: /home/user/mein-projekt
> ```
> → Nicht: `~/mein-projekt` oder `./mein-projekt`

> [!WARNING]
> **Wizard schlägt fehl bei Schritt 1/2:**
> ```
> [!] Gitea nicht erreichbar. Fortfahren? (y/N):
> ```
> → Bei `y`: Wizard läuft weiter, aber Konfiguration unvollständig

---

### Nächste Schritte

✅ Projekt eingerichtet  
→ [03 — Dein erstes Issue](03-first-issue.md)  
→ [04 — Health-Check](04-health-check.md)
