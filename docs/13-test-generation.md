## LLM-generierte Tests (--generate-tests)

Agent schreibt Tests für deinen Server.

---

### Voraussetzungen

> [!IMPORTANT]
> - Eval-Server läuft (mit Dokumentation/API-Specs)
> - LLM-Session aktiv ([Rezept 05](05-issue-to-pr.md))

---

### Problem

Du hast einen neuen Endpunkt implementiert, aber keine Tests geschrieben. Der Agent soll anhand der Doku/API Tests generieren.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Schritt 1: Test-Generierung
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --issue 42 \
  --generate-tests

# ──────────────────────────────────────────────────────────
# Ablauf (LLM-gesteuert):
# ──────────────────────────────────────────────────────────
# [1] Agent liest: ~/mein-projekt/config/agent_eval.json
# [2] Agent scannt: API-Dokumentation, Swagger, README
# [3] LLM generiert neue Tests:
#     {
#       "name": "Auth-Token-Validation",
#       "message": "Login mit Token xyz",
#       "expected_keywords": ["token", "valid"],
#       "weight": 2,
#       "tag": "auth"
#     }
# [4] Neue Tests werden zu agent_eval.json hinzugefügt
# [5] Agent postet JSON-Diff als Kommentar in Issue #42
# [6] Du approve → Tests werden committed

# ──────────────────────────────────────────────────────────
# Schritt 2: Neue Tests validieren
# ──────────────────────────────────────────────────────────
python3 evaluation.py --project ~/mein-projekt

# Output:
# [1/5] Auth-Token-Validation — PASS (2500ms)
# [2/5] Invalid-Token-Check — PASS (1200ms)
# [✓] Score: 10.0 / 10.0 (alle neuen Tests bestehen)

# ──────────────────────────────────────────────────────────
# Schritt 3: Baseline anpassen
# ──────────────────────────────────────────────────────────
python3 evaluation.py --project ~/mein-projekt --update-baseline
# → Baseline: 6.0 → 10.0
```

---

### Erklärung

**Was der Agent analysiert:**

1. **API-Dokumentation:**
   - `~/mein-projekt/README.md` (Endpunkt-Beschreibungen)
   - `~/mein-projekt/docs/API.md`
   - Swagger/OpenAPI-Specs

2. **Bestehende Tests:**
   - `agent_eval.json` (Muster verstehen)
   - Coverage-Lücken identifizieren

3. **Source-Code:**
   - Endpunkt-Signaturen (`@app.route("/chat")`)
   - Error-Handling (welche Fehler testen?)

**LLM-Prompt (vereinfacht):**
```
Analysiere die API und generiere Tests für agent_eval.json.

Fokus:
- Neue Endpunkte ohne Tests
- Edge-Cases (leere Eingabe, ungültige Token)
- Error-Handling (404, 500)

Format:
{
  "name": "...",
  "message": "...",
  "expected_keywords": [...],
  "weight": 1-3,
  "tag": "..."
}
```

**Generierte Test-Kategorien:**

| Kategorie | Beispiel |
|-----------|----------|
| Happy-Path | `"message": "Hallo", "expected_keywords": ["Hi"]` |
| Edge-Cases | `"message": "", "expected_keywords": ["error", "empty"]` |
| Auth | `"message": "Login ohne Token", "expected_keywords": ["401", "unauthorized"]` |
| Performance | `"max_response_ms": 1000` für schnelle Endpunkte |

---

### Best Practice

> [!TIP]
> **Iterative Test-Generierung:**
> ```bash
> # Runde 1: Basis-Tests
> python3 agent_start.py --project ~/proj --issue 10 --generate-tests
> # → 5 Tests generiert
> 
> # Validieren
> python3 evaluation.py --project ~/proj
> 
> # Runde 2: Edge-Cases nachgenerieren
> # (LLM sieht vorherige Tests und ergänzt)
> python3 agent_start.py --project ~/proj --issue 10 --generate-tests
> # → 3 zusätzliche Tests
> ```

> [!TIP]
> **Test-Generierung im Issue-Template:**
> ```markdown
> # Issue #42: Neuer /search Endpunkt
> 
> ## Acceptance-Criteria
> - [ ] Endpunkt implementiert
> - [ ] Tests generiert (--generate-tests)
> - [ ] Alle Tests bestehen
> ```

> [!TIP]
> **Manuelle Nachbearbeitung:**
> ```bash
> nano ~/mein-projekt/config/agent_eval.json
> # Anpassen:
> # - Keywords verfeinern
> # - Weights justieren
> # - Tags vereinheitlichen
> ```

---

### Warnung

> [!WARNING]
> **LLM halluziniert Tests:**
> ```json
> {
>   "name": "Nicht-existenter-Endpunkt",
>   "message": "/fantasy-api",
>   "expected_keywords": ["magic"]
> }
> ```
> → Immer manuell prüfen bevor approve

> [!WARNING]
> **Zu viele Tests generiert:**
> ```
> Agent generiert 50 Tests für kleine API
> → Baseline wird unrealistisch hoch
> → Eval-Laufzeit explodiert
> ```
> → Selektiv mergen, nicht blind übernehmen

> [!WARNING]
> **Sensible Daten in Tests:**
> ```json
> {
>   "message": "Login: user@example.com, password: secret123"
> }
> ```
> → Tests werden committed → keine Produktions-Credentials

---

### Nächste Schritte

✅ Tests automatisch generiert  
→ [09 — Ersten Test schreiben](09-first-test.md)  
→ [11 — Baseline-Management](11-baseline-management.md)  
→ [40 — Best Practices](40-best-practices.md)
