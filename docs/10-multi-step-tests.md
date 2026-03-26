## Mehrstufige Tests (steps)

Fakt schreiben → abfragen: Context-Persistence testen.

---

### Voraussetzungen

> [!IMPORTANT]
> - Basis-Tests konfiguriert ([Rezept 09](09-first-test.md))
> - Server mit Context-Speicherung (z.B. ChromaDB, Chat-History)

---

### Problem

Einzelne Nachrichten testen nur Routing. Du willst prüfen ob der Server sich Fakten merkt und später korrekt abruft.

---

### Lösung

```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "tests": [
    {
      "name": "Kontext-Persistenz",
      "weight": 2,
      "steps": [
        {
          "message": "Mein Lieblingstier ist ein Pinguin",
          "expect_stored": true
        },
        {
          "message": "Was ist mein Lieblingstier?",
          "expected_keywords": ["Pinguin"]
        }
      ],
      "tag": "context_persistence"
    },
    {
      "name": "Mehrschrittige Abfrage",
      "weight": 3,
      "steps": [
        {
          "message": "Ich heiße Anna",
          "expect_stored": true
        },
        {
          "message": "Ich wohne in Berlin",
          "expect_stored": true
        },
        {
          "message": "Wie heiße ich und wo wohne ich?",
          "expected_keywords": ["Anna", "Berlin"]
        }
      ],
      "tag": "multi_step"
    }
  ]
}
```

---

### Erklärung

**Step-Typen:**

1. **`expect_stored: true`**
   - Sendet Nachricht
   - Prüft nur: Antwort vorhanden (nicht leer)
   - Keine Keyword-Prüfung
   - Für: Fakten schreiben

2. **`expected_keywords: [...]`**
   - Sendet Nachricht
   - Prüft: Alle Keywords in Antwort (case-insensitive)
   - Für: Fakten abfragen

**Ausführung:**
- Steps werden **sequenziell** ausgeführt
- **2 Sekunden Pause** zwischen Steps (LLM-Inferenz-Cooldown)
- Gesamtzeit wird gemessen (für Performance-Monitoring)
- Bei Fehler in Step N: Test schlägt fehl, weitere Steps übersprungen

**User-ID:**
- Pro Eval-Lauf: `eval-<uuid>`
- Isoliert Tests voneinander (ChromaDB, History)

---

### Best Practice

> [!TIP]
> **Komplexe Szenarien:**
> ```json
> {
>   "name": "Projekt-Kontext",
>   "weight": 3,
>   "steps": [
>     {"message": "Projekt: gitea-agent, Sprache: Python", "expect_stored": true},
>     {"message": "Repository: github.com/user/gitea-agent", "expect_stored": true},
>     {"message": "Was ist die Sprache von gitea-agent?", "expected_keywords": ["Python"]},
>     {"message": "Wo liegt das Repository?", "expected_keywords": ["github"]}
>   ],
>   "tag": "project_context"
> }
> ```

> [!TIP]
> **Negative Tests:**
> ```json
> {
>   "name": "Falsche Abfrage",
>   "weight": 1,
>   "steps": [
>     {"message": "Mein Name ist Max", "expect_stored": true},
>     {"message": "Wie alt bin ich?", "expected_keywords": ["weiß nicht", "keine Information"]}
>   ],
>   "tag": "negative_test"
> }
> ```

---

### Warnung

> [!WARNING]
> **Context-Isolation beachten:**
> ```
> Eval-Lauf 1: User = eval-abc123
> Eval-Lauf 2: User = eval-def456
> ```
> → Tests beeinflussen sich nicht gegenseitig

> [!WARNING]
> **Steps vs. message:**
> ```json
> {
>   "name": "Test",
>   "message": "...",      ← FEHLER
>   "steps": [...]         ← steps ersetzt message
> }
> ```
> → Entweder `message` ODER `steps`, nicht beides

> [!WARNING]
> **Timeout bei vielen Steps:**
> ```json
> {
>   "steps": [/* 20 Steps */],
>   "max_response_ms": 60000  // 60 Sekunden
> }
> ```
> → Gesamtzeit aller Steps + Pausen

---

### Nächste Schritte

✅ Mehrstufige Tests laufen  
→ [11 — Baseline-Management](11-baseline-management.md)  
→ [12 — Performance-Tests](12-performance-tests.md)
