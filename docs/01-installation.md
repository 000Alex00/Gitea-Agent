## Installation & Systemvoraussetzungen

Richte gitea-agent **einmalig** ein — gilt dann für alle deine Projekte.

---

### Voraussetzungen

> [!IMPORTANT]
> - **Python 3.10+** (check: `python3 --version`)
> - **git** installiert (check: `git --version`)
> - **Gitea-Instanz** mit API-Zugang (URL + API-Token)
> - **Mindestens 4 GB RAM** empfohlen (für LLM + Agent parallel)

---

### Problem

Du willst gitea-agent nutzen, aber weißt nicht wie du anfängst. Die Installation soll sauber sein — kein Projekt-Verzeichnis vollmüllen, keine globalen System-Änderungen.

---

### Lösung

```bash
# 1. Repository klonen (einmalig, zentrale Installation)
cd ~  # oder anderes Verzeichnis deiner Wahl
git clone https://github.com/Alexander-Benesch/Gitea-Agent
cd Gitea-Agent

# 2. Python-Version prüfen
python3 --version
# → muss >= 3.10 sein

# 3. Keine Abhängigkeiten installieren — nur Stdlib!
# (keine requirements.txt, keine pip install nötig)

# 4. Ausführbarkeit testen
python3 agent_start.py --help
# → zeigt CLI-Hilfe
```

**Das war's!** Der Agent ist jetzt installiert und kann für beliebig viele Projekte genutzt werden.

---

### Erklärung

**Warum zentrale Installation?**
- gitea-agent ist **projekt-agnostisch** — ein Agent, viele Projekte.
- Konfiguration liegt in den Zielprojekten (via `agent/config/`), nicht im Agent selbst.
- Updates ziehst du mit `git pull` im Agent-Verzeichnis.

**Warum keine Dependencies?**
- Absichtliches Design: nur Python Stdlib (`urllib`, `json`, `pathlib`, `ast`).
- Läuft auf kleiner Hardware (Raspberry Pi, Jetson Nano) ohne pip-Probleme.
- Keine Versions-Konflikte mit Projekt-Dependencies.

**Architektur:**
```
~/Gitea-Agent/          ← Agent-Code (einmalig)
    agent_start.py
    evaluation.py
    gitea_api.py
    .env                ← zeigt auf aktives Projekt

~/mein-projekt/         ← dein Zielprojekt
    agent/
        config/         ← versioniert (Tests, Excludes)
        data/           ← .gitignore (Scores, Logs)

~/anderes-projekt/      ← weiteres Projekt
    agent/config/       ← eigene Konfiguration
    agent/data/         ← eigene Laufzeit-Daten
```

---

### Best Practice

> [!TIP]
> **Agent-Updates:**
> ```bash
> cd ~/Gitea-Agent
> git pull
> # → sofort für alle Projekte aktiv
> ```

> [!TIP]
> **PATH-Variable (optional):**
> ```bash
> # In ~/.bashrc oder ~/.zshrc:
> export PATH="$HOME/Gitea-Agent:$PATH"
> alias agent="python3 $HOME/Gitea-Agent/agent_start.py"
> 
> # Dann von überall:
> agent --list
> ```

---

### Warnung

> [!WARNING]
> **Nicht ins Projekt-Verzeichnis klonen!**
> ❌ `~/mein-projekt/Gitea-Agent/` (vermischt Agent + Projekt)
> ✅ `~/Gitea-Agent/` (zentral, sauber getrennt)

> [!WARNING]
> **Python < 3.10:**
> - `match/case`-Statements werden nicht funktionieren.
> - `pathlib`-Methoden könnten fehlen.
> - Upgrade auf Python 3.10+ erforderlich.

---

### Nächste Schritte

✅ Installation abgeschlossen  
→ [02 — Erstes Projekt einrichten](02-first-setup.md)
