## Performance-Tests (max_response_ms)

Antwortzeit überwachen → Issues bei Regression.

---

### Voraussetzungen

> [!IMPORTANT]
> - Tests konfiguriert ([Rezept 09](09-first-test.md))
> - Server läuft stabil

---

### Problem

Keyword-Tests bestehen, aber Antworten werden langsamer. Du willst Timeouts automatisch erkennen und Issues öffnen.

---

### Lösung

```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "max_response_ms": 5000,
  "tests": [
    {
      "name": "Schnelle Begrüßung",
      "message": "Hallo",
      "expected_keywords": ["Hallo", "Hi"],
      "max_response_ms": 1000,
      "weight": 1,
      "tag": "greeting"
    },
    {
      "name": "Komplexe Abfrage",
      "message": "Erkläre mir Quantenphysik",
      "expected_keywords": ["Quant", "Physik"],
      "max_response_ms": 8000,
      "weight": 2,
      "tag": "long_inference"
    },
    {
      "name": "RAG-Abfrage",
      "message": "Was steht in Kapitel 3 der Dokumentation?",
      "expected_keywords": ["Kapitel"],
      "max_response_ms": 3000,
      "weight": 2,
      "tag": "rag"
    }
  ]
}
```

**Watch-Modus Aktivierung:**
```bash
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --watch \
  --eval-interval 3600
  
# Verhalten bei Performance-Regression:
# ──────────────────────────────────────────────────────────
# Run 1: Antwortzeit 2000ms → PASS
# Run 2: Antwortzeit 6000ms → FAIL (> max_response_ms: 5000)
# → Issue: "Performance-Regression bei Test: RAG-Abfrage"
# → Label: agent:perf-regression
```

---

### Erklärung

**Timeout-Hierarchie:**

1. **Global:** `max_response_ms: 5000` (Top-Level)
   - Gilt für **alle** Tests ohne eigenes Limit
   - Standard-Timeout

2. **Test-spezifisch:** `max_response_ms: 1000` (in Test-Objekt)
   - Überschreibt Global-Limit
   - Für schnelle Tests (Greetings, Health-Checks)
   - Für langsame Tests (RAG, komplexe Inference)

**Zeitmessung:**

```python
# evaluation.py (vereinfacht)
start = time.time()
response = requests.post(url, json={"message": msg})
elapsed_ms = (time.time() - start) * 1000

if elapsed_ms > max_response_ms:
    test["status"] = "TIMEOUT"
    test["error"] = f"Response time {elapsed_ms:.0f}ms > {max_response_ms}ms"
```

**Watch-Modus Logik:**

- **Pass → Pass:** Keine Aktion
- **Pass → Fail:** Issue eröffnen (Performance-Regression)
- **Fail → Pass:** Issue schließen
- **Fail → Fail:** Kommentar hinzufügen

---

### Best Practice

> [!TIP]
> **Zeitlimits pro Test-Typ:**
> ```json
> {
>   "max_response_ms": 5000,
>   "tests": [
>     // ── Schnell: < 1 Sekunde ──
>     {"name": "Health", "max_response_ms": 500, "...": "..."},
>     {"name": "Greeting", "max_response_ms": 1000, "...": "..."},
>     
>     // ── Mittel: 1-3 Sekunden ──
>     {"name": "RAG-Query", "max_response_ms": 3000, "...": "..."},
>     {"name": "Context-Recall", "max_response_ms": 3000, "...": "..."},
>     
>     // ── Langsam: 3-10 Sekunden ──
>     {"name": "Code-Generation", "max_response_ms": 10000, "...": "..."},
>     {"name": "Long-Document", "max_response_ms": 8000, "...": "..."}
>   ]
> }
> ```

> [!TIP]
> **Performance-Baseline dokumentieren:**
> ```bash
> # Initiale Messung
> python3 evaluation.py --project ~/mein-projekt
> 
> # Zeiten in README festhalten:
> cat ~/mein-projekt/agent/README.md
> # Performance-Ziele:
> # - Health-Check: < 500ms
> # - RAG-Queries: < 3000ms
> # - Code-Gen: < 10000ms
> ```

> [!TIP]
> **Aggregierte Zeiterfassung:**
> ```json
> {
>   "name": "Multi-Step Performance",
>   "weight": 3,
>   "max_response_ms": 10000,
>   "steps": [
>     {"message": "Schritt 1", "expect_stored": true},
>     {"message": "Schritt 2", "expect_stored": true},
>     {"message": "Schritt 3", "expected_keywords": ["..."]}
>   ]
> }
> ```
> → Gesamtzeit aller Steps inkl. Pausen (2s × 2 = 4s extra)

---

### Warnung

> [!WARNING]
> **Netzwerk-Latenz beachten:**
> ```json
> {
>   "server_url": "http://remote-server:8000",
>   "max_response_ms": 1000  // ← zu niedrig bei Netzwerk-Overhead
> }
> ```
> → +100-500ms für HTTP-Roundtrip addieren

> [!WARNING]
> **Cold-Start bei ersten Tests:**
> ```
> Test 1: 8000ms (Model wird geladen)
> Test 2: 2000ms (Model warm)
> ```
> → Warmup-Requests vor Eval-Lauf senden

> [!WARNING]
> **Shared-Server Varianz:**
> ```
> Run 1: 2500ms (Server leer)
> Run 2: 6000ms (Server unter Last)
> ```
> → max_response_ms mit Puffer (z.B. 2× normale Zeit)

---

### Nächste Schritte

✅ Performance-Tests konfiguriert  
→ [13 — Test-Generierung](13-test-generation.md)  
→ [18 — Tag-Aggregation](18-tag-aggregation.md)  
→ [36 — Watch-Modus Crashes debuggen](36-watch-mode-crashes.md)
