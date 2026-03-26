## Eval-Baseline setzen & aktualisieren

Score-Schwellwerte nach Änderungen neu kalibrieren.

---

### Voraussetzungen

> [!IMPORTANT]
> - Tests konfiguriert ([Rezept 09](09-first-test.md))
> - `baseline.json` existiert (wird beim ersten Eval angelegt)

---

### Problem

Nach Test-Änderungen oder Server-Verbesserungen ist die alte Baseline zu niedrig/hoch. Du willst den Schwellwert neu setzen.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Szenario 1: Tests hinzugefügt/entfernt
# ──────────────────────────────────────────────────────────
# agent_eval.json: 3 Tests (weight: 1+2+3 = max 6)
cat ~/mein-projekt/agent/data/baseline.json
# {"score": 6.0}

# Neuen Test hinzugefügt (weight: 2)
# → max score jetzt: 8.0

# Baseline neu setzen:
cd ~/Gitea-Agent
python3 evaluation.py --project ~/mein-projekt --update-baseline

# → [Eval] PASS — Score: 8.0 / 8.0
# → [✓] Baseline aktualisiert: 6.0 → 8.0

# ──────────────────────────────────────────────────────────
# Szenario 2: Server verbessert, Score gestiegen
# ──────────────────────────────────────────────────────────
# Alter Score: 6.0 / 8.0 (Baseline: 6.0)
# Neuer Score: 8.0 / 8.0 (alle Tests bestehen)

# Automatisches Baseline-Update:
python3 evaluation.py --project ~/mein-projekt
# → [✓] Baseline erhöht: 6.0 → 8.0 (Score > Baseline)

# Oder manuell erzwingen:
python3 evaluation.py --project ~/mein-projekt --update-baseline

# ──────────────────────────────────────────────────────────
# Szenario 3: Baseline zu hoch (Tests geändert)
# ──────────────────────────────────────────────────────────
cat ~/mein-projekt/agent/data/baseline.json
# {"score": 8.0}

# Test entfernt → max score jetzt nur 6.0
# Eval schlägt fehl:
python3 evaluation.py --project ~/mein-projekt
# → [Eval] FAIL — Score: 6.0, Baseline: 8.0

# Baseline manuell senken:
python3 evaluation.py --project ~/mein-projekt --update-baseline
# → [✓] Baseline aktualisiert: 8.0 → 6.0
```

---

### Erklärung

**Baseline-Logik:**

1. **Erster Lauf:** Keine `baseline.json` vorhanden
   - Eval → immer PASS
   - Aktueller Score wird als Baseline gespeichert

2. **Folgeläufe:** `baseline.json` existiert
   - `score >= baseline` → PASS
   - `score < baseline` → FAIL

3. **Automatische Erhöhung:** Score > Baseline
   - Baseline wird automatisch hochgesetzt
   - **Nie automatisch gesenkt**

4. **Manuelle Anpassung:** `--update-baseline`
   - Überschreibt Baseline mit aktuellem Score
   - Unabhängig davon ob höher/niedriger

**Baseline-Datei:**
```bash
cat ~/mein-projekt/agent/data/baseline.json
{"score": 7.0}
```

---

### Best Practice

> [!TIP]
> **Nach Test-Änderungen immer Baseline prüfen:**
> ```bash
> # Tests anpassen
> nano ~/mein-projekt/agent/config/agent_eval.json
> 
> # Baseline neu setzen
> python3 evaluation.py --project ~/mein-projekt --update-baseline
> 
> # Verifizieren
> cat ~/mein-projekt/agent/data/baseline.json
> ```

> [!TIP]
> **Baseline in .gitignore:**
> ```bash
> # ~/mein-projekt/.gitignore
> agent/data/baseline.json
> agent/data/score_history.json
> agent/data/*.log
> ```
> → Laufzeit-Daten nicht versionieren

> [!TIP]
> **Baseline-Check vor PR:**
> ```bash
> cat ~/mein-projekt/agent/data/baseline.json
> # {"score": 7.0}
> 
> python3 agent_start.py --pr 21 --branch fix/... --summary "..."
> # → Eval läuft automatisch
> # → PR nur bei Score >= 7.0
> ```

---

### Warnung

> [!WARNING]
> **Baseline nie automatisch gesenkt:**
> ```bash
> # Baseline: 8.0
> # Score: 6.0 (Tests failen)
> 
> python3 evaluation.py --project ~/mein-projekt
> # → [Eval] FAIL — Score: 6.0, Baseline: 8.0
> # → Baseline bleibt 8.0!
> 
> # Manuell senken erforderlich:
> python3 evaluation.py --project ~/mein-projekt --update-baseline
> ```

> [!WARNING]
> **Baseline zu niedrig = keine Qualitätssicherung:**
> ```json
> {"score": 1.0}  // nur 1 von 8 Tests muss bestehen
> ```
> → PR wird erstellt auch wenn fast alles kaputt ist

> [!WARNING]
> **Baseline zu hoch = ständige Blockaden:**
> ```json
> {"score": 8.0}  // alle Tests müssen immer bestehen
> ```
> → PR blockiert bei kleinsten Problemen

---

### Nächste Schritte

✅ Baseline-Management verstanden  
→ [12 — Performance-Tests](12-performance-tests.md)  
→ [09 — Ersten Test schreiben](09-first-test.md)
