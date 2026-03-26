## Ersten Eval-Test schreiben

Richte Qualitätssicherung ein: Tests laufen automatisch vor jedem PR.

---

### Voraussetzungen

> [!IMPORTANT]
> - Projekt eingerichtet ([Rezept 02](02-first-setup.md))
> - Server/Anwendung läuft lokal (z.B. `http://localhost:8000`)
> - HTTP-Endpunkt verfügbar (z.B. `/chat` oder `/api/test`)

---

### Problem

Du willst sicherstellen dass dein Projekt nach jeder Änderung noch funktioniert. Manuelle Tests sind mühsam — du brauchst automatisierte Smoke-Tests die vor jedem PR laufen.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Schritt 1: agent_eval.json erstellen
# ──────────────────────────────────────────────────────────
mkdir -p ~/mein-projekt/config
nano ~/mein-projekt/config/agent_eval.json

# ──────────────────────────────────────────────────────────
# Minimal-Konfiguration (Copy-Paste-ready):
# ──────────────────────────────────────────────────────────
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "tests": [
    {
      "name": "Routing einfach",
      "weight": 1,
      "message": "Was ist 2 plus 2?",
      "expected_keywords": ["4"],
      "tag": "math_basic"
    },
    {
      "name": "Kontext-Persistenz",
      "weight": 2,
      "message": "Mein Name ist Max. Wie heiße ich?",
      "expected_keywords": ["Max"],
      "tag": "context_persistence"
    }
  ]
}

# ──────────────────────────────────────────────────────────
# Schritt 2: Ersten Test-Lauf (manuell)
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 evaluation.py --project ~/mein-projekt

# → Führt alle Tests aus
# → Erstellt baseline.json (erster Lauf = immer PASS)
# → Ausgabe:
#   [Eval] PASS — Score: 3.0 / 3.0 (Baseline: 3.0)
#   [✓] Baseline angelegt (erster Lauf)

# ──────────────────────────────────────────────────────────
# Schritt 3: Tests sind jetzt aktiv bei --pr
# ──────────────────────────────────────────────────────────
python3 agent_start.py --pr 61 --branch fix/... --summary "..."

# → evaluation.run() läuft automatisch
# → Score < Baseline: PR blockiert
# → Score >= Baseline: PR wird erstellt
```

---

### Erklärung

**Was ist ein Test?**
- HTTP-POST an `server_url + chat_endpoint`
- Body: `{"prompt": "...", "user": "eval-<uuid>"}`
- Antwort wird auf `expected_keywords` geprüft (case-insensitive)

**Warum `tag`-Feld Pflicht?**
- Ermöglicht [Tag-Aggregation](18-tag-aggregation.md): Systematische Fehler erkennen
- Beispiel: Tag `database` failt 3× in 5 Läufen → Auto-Issue
- Ohne Tag: `agent_self_check.py` gibt Warnung

**Score-Berechnung:**
```
score = sum(weight für bestandene Tests)
max   = sum(aller weights)
PASS  wenn score >= baseline_score
```

**Baseline-Logik:**
- **Erster Lauf:** Immer PASS, Baseline wird angelegt
- **Folgeläufe:** Score >= Baseline → PASS, Score < Baseline → FAIL
- **Verbesserung:** Score > Baseline → Baseline automatisch erhöht (nie gesenkt)

---

### Best Practice

> [!TIP]
> **Gewichtung sinnvoll verteilen:**
> ```json
> {
>   "name": "Server startet",
>   "weight": 1,  // Smoke-Test
>   "tag": "startup"
> },
> {
>   "name": "Datenbank-Migration",
>   "weight": 3,  // Kritischer Test
>   "tag": "database"
> }
> ```

> [!TIP]
> **Keywords leer = nur Antwort prüfen:**
> ```json
> {
>   "name": "Server antwortet",
>   "message": "Hallo",
>   "expected_keywords": [],  // Jede Antwort OK
>   "tag": "health_check"
> }
> ```

> [!TIP]
> **Deterministische User-IDs:**
> - Pro Eval-Lauf: `eval-<uuid>` (einmalig generiert)
> - Verhindert dass Tests sich gegenseitig beeinflussen (z.B. ChromaDB, Chat-History)

---

### Warnung

> [!WARNING]
> **Server offline → Eval übersprungen:**
> ```
> [Eval] WARN — Server http://localhost:8000 offline
> → Eval übersprungen, PR wird trotzdem erstellt
> ```
> → Kein FAIL, nur Warnung (Workflow blockiert nicht)

> [!WARNING]
> **Baseline zu hoch gesetzt:**
> ```bash
> # Baseline manuell zurücksetzen:
> python3 evaluation.py --project ~/mein-projekt --update-baseline
> ```
> → Führt Tests aus und schreibt aktuellen Score als neue Baseline

> [!WARNING]
> **agent_eval.json Syntax-Fehler:**
> ```
> [!] JSON Syntax Error in agent_eval.json
> → Eval silent skip (kein Crash)
> ```
> → Validate JSON: `python3 -m json.tool < agent_eval.json`

---

### Nächste Schritte

✅ Erste Tests laufen  
→ [10 — Mehrstufige Tests (steps)](10-multi-step-tests.md)  
→ [11 — Baseline-Management](11-baseline-management.md)  
→ [12 — Performance-Tests](12-performance-tests.md)
