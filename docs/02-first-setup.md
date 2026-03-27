## Erstes Projekt einrichten (Setup-Wizard)

Interaktiver 9-Schritt-Wizard führt durch die komplette Einrichtung.

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
# [1] Server-URL (z.B. http://localhost:8080): http://192.168.1.x:8080
#     Protokoll (http:// oder https://) muss angegeben werden.
# [2] Log-Pfad: /home/user/mein-projekt/logs/app.log
# [3] Start-Script (leer = keins): /home/user/scripts/start_server.sh
#     ⚠️  Ohne Start-Script kein automatischer Neustart möglich.

# → Schreibt ~/Gitea-Agent/config/agent_eval.json
# → [✓] agent_eval.json erstellt

# ──────────────────────────────────────────────────────────
# Schritt 6: .env schreiben
# ──────────────────────────────────────────────────────────
# → Sammelt alle Eingaben
# → Schreibt ~/Gitea-Agent/.env
# → [✓] .env geschrieben

# ──────────────────────────────────────────────────────────
# Schritt 7: Projekttyp & Features
# ──────────────────────────────────────────────────────────
# Projekttypen:
#   1) web_api         — REST-API / Web-Server
#   2) llm_chat        — LLM-Chat mit Eval-Tests
#   3) voice_assistant — Voice-Pipeline (STT/TTS/LLM)
#   4) iot             — IoT / Embedded / Edge (z.B. Jetson)
#   5) cli_tool        — Kommandozeilen-Programm
#   6) library         — Python-Bibliothek
#   7) custom          — Alle Features manuell wählen
#
# Features mit Beschreibung:
#   ✅  eval           Bewertet Server-Antworten automatisch  [benötigt: server_url]
#   ✅  health_checks  Prüft ob Server erreichbar ist         [benötigt: server_url]
#   ✅  auto_issues    Erstellt Issues bei Testfehlern        [benötigt: eval]
#   ✅  changelog      Generiert CHANGELOG.md aus Commits
#   ✅  watch          Überwacht Gitea auf neue Issues
#   ✅  pr_workflow    Erstellt PRs nach Implementierung
#
# → Einzelne Features anpassen? [j/N]
# → [✓] config/project.json erstellt

# ──────────────────────────────────────────────────────────
# Schritt 8: LLM-Routing (Minimal-Setup)
# ──────────────────────────────────────────────────────────
# → Standard-Anbieter [claude]: claude
# → Bekannte Modelle: claude-opus-4-6, claude-sonnet-4-6, ...
# → Standard-Modell [claude-sonnet-4-6]: claude-sonnet-4-6
# → ⚠️  Nicht vergessen: ANTHROPIC_API_KEY=... in .env eintragen
# → [✓] config/llm/routing.json erstellt
# → 💡 Per-Task Routing & Fallback: python3 agent_start.py --llm

# ──────────────────────────────────────────────────────────
# Schritt 9: System-Prompts
# ──────────────────────────────────────────────────────────
# → Kopiert Templates aus config/llm/ide/ nach config/llm/prompts/
# → [✓] analyst.md, senior_python.md, reviewer.md, healer.md, log_analyst.md

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
# [✓] LLM-Config-Guard (config/llm/routing.json + System-Prompts)

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

2. **`config/agent_eval.json` im Projekt:**
```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "log_path": "/home/user/mein-projekt/server.log",
  "restart_script": "/home/user/scripts/start_server.sh",
  "tests": []
}
```

3. **`config/llm/routing.json` (LLM-Routing):**
```json
{
  "_comment": "LLM-Routing — generiert vom Setup-Wizard. Erweitern: --llm",
  "default": { "provider": "claude", "model": "claude-sonnet-4-6", "max_tokens": 1024, "timeout": 60 }
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
> **LLM-Routing nachträglich ändern:**
> ```bash
> python3 agent_start.py --llm
> # → Provider wechseln, per-Task Routing, Fallback-Kette konfigurieren
> # → Kein Setup-Neustart nötig
> ```
> → Vollständige Dokumentation: [Rezept 42 — LLM-Routing](42-llm-routing.md)

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
