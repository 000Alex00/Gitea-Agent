## Watch-Modus mit tmux starten

Richte 24/7-Betrieb ein: Periodische Evals + Auto-Issues bei Regression.

---

### Voraussetzungen

> [!IMPORTANT]
> - Tests konfiguriert ([Rezept 09](09-first-test.md))
> - Baseline existiert (`data/baseline.json`)
> - **tmux installiert:** `sudo apt install tmux` (Linux) oder `brew install tmux` (macOS)

---

### Problem

Du willst dass der Agent kontinuierlich läuft: alle 60 Minuten Eval ausführen, bei Score-Regression automatisch Issues erstellen, bei Erholung Issues schließen. Ohne dass du dabei sein musst.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Schritt 1: Watch-Intervall konfigurieren (optional)
# ──────────────────────────────────────────────────────────
nano ~/mein-projekt/config/agent_eval.json

# Füge hinzu:
{
  "watch_interval_minutes": 30,  // Standard: 60
  "log_path": "/home/user/mein-projekt/server.log",  // für Inaktivitäts-Check
  "restart_script": "/home/user/start_server.sh",    // für Auto-Restart
  "inactivity_minutes": 5,                            // Schwellwert
  // ... tests ...
}

# ──────────────────────────────────────────────────────────
# Schritt 2: Tmux-Session starten
# ──────────────────────────────────────────────────────────
tmux new -s agent-watch

# → Neue tmux-Session namens "agent-watch"

# ──────────────────────────────────────────────────────────
# Schritt 3: Watch-Modus aktivieren
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py --watch

# → Startet Eval-Loop:
#   [Watch] Zyklus 1 — 2026-03-26 14:30:00
#   [Eval] PASS — Score: 7.0 / 7.0
#   [Dashboard] dashboard.html aktualisiert
#   [Watch] Nächster Lauf in 60 Minuten...

# ──────────────────────────────────────────────────────────
# Schritt 4: Session detachen (Terminal verlassen)
# ──────────────────────────────────────────────────────────
# Tastenkombination: Ctrl+B, dann D

# → Terminal kann geschlossen werden, Agent läuft weiter

# ──────────────────────────────────────────────────────────
# Schritt 5: Session wieder öffnen
# ──────────────────────────────────────────────────────────
tmux attach -t agent-watch

# → Zeigt laufenden Watch-Modus

# ──────────────────────────────────────────────────────────
# Schritt 6: Watch-Modus beenden
# ──────────────────────────────────────────────────────────
# In der tmux-Session: Ctrl+C
# Dann Session verlassen: exit
```

---

### Erklärung

**Was passiert in jedem Zyklus?**
1. `evaluation.run(PROJECT, trigger="watch")` — alle Tests ausführen
2. `dashboard.generate(PROJECT)` — HTML-Dashboard aktualisieren
3. `_close_resolved_auto_issues()` — geheilte `[Auto]`-Issues schließen
4. Für jeden failed_test:
   - Duplikat-Check: `[Auto] Testname` Issue existiert?
   - Falls nein: Neues Issue mit Fehlerdetails erstellen
5. `_update_skeleton_incremental()` — repo_skeleton.json aktualisieren
6. `_check_systematic_tag_failures()` — Tag-Aggregation prüfen
7. Optional: `log_analyzer.run()` (falls konfiguriert)
8. **Szenario 2:** Auto-Restart bei Inaktivität + neuen Commits

**Szenario 2 — Automatischer Neustart:**
- Bedingung 1: Chat-Log zeigt Inaktivität ≥ `inactivity_minutes`
- Bedingung 2: Neue Commits seit letztem Eval vorhanden
- Aktion: `restart_script` ausführen → sofort Eval

**Auto-Issue-Format:**
```
Titel: [Auto] Routing einfach
Body:
  Test: Routing einfach (weight: 1, tag: math_basic)
  Kategorie: keyword_miss
  Erwartet: ["4"]
  Erhalten: "Das ist die falsche Antwort"
  
  Letzte 3 Scores: 7.0 → 6.0 → 5.0
  Verlauf: 📉 Verschlechterung
```

---

### Best Practice

> [!TIP]
> **Intervall per CLI überschreiben:**
> ```bash
> python3 agent_start.py --watch --interval 15
> # → 15 Minuten Intervall (überschreibt agent_eval.json)
> ```

> [!TIP]
> **Tmux-Cheatsheet:**
> ```bash
> tmux ls                    # Alle Sessions auflisten
> tmux attach -t agent-watch # Session verbinden
> tmux kill-session -t agent-watch  # Session beenden
> 
> # In Session:
> Ctrl+B, D   # Detach
> Ctrl+B, C   # Neues Fenster
> Ctrl+B, [   # Scroll-Modus (q zum Beenden)
> ```

> [!TIP]
> **Dashboard live ansehen:**
> ```bash
> # In separatem Terminal:
> cd ~/mein-projekt
> python3 -m http.server 8080
> # → http://localhost:8080/dashboard.html
> ```

---

### Warnung

> [!WARNING]
> **Watch-Modus stürzt ab bei Netzwerk-Timeout:**
> ```python
> # evaluation.py hat try/except — sollte nicht crashen
> # Falls doch: Logs prüfen
> tail -50 ~/mein-projekt/data/gitea-agent.log
> ```

> [!WARNING]
> **Disk voll → score_history.json nicht schreibbar:**
> ```bash
> df -h  # Disk-Space prüfen
> # → score_history.json wird automatisch rotiert (max. 90 Einträge)
> ```

> [!WARNING]
> **Patch-Modus vs. Normal-Modus:**
> ```bash
> # Normal (Night): Auto-Issues + Auto-Close
> python3 agent_start.py --watch
> 
> # Patch: Nur Eval, keine Auto-Issues
> python3 agent_start.py --watch --patch
> ```
> → Siehe [Rezept 16](16-night-vs-patch.md)

---

### Nächste Schritte

✅ Watch-Modus läuft  
→ [15 — Watch als Systemd-Dienst](15-watch-mode-systemd.md)  
→ [16 — Betriebsmodi verstehen](16-night-vs-patch.md)  
→ [17 — Consecutive-Pass Gate](17-consecutive-pass-gate.md)
