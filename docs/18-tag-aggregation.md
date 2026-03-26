## Tag-Aggregation (systematische Failures)

Mehrere Tests mit gleichem Tag failen → Meta-Issue.

---

### Voraussetzungen

> [!IMPORTANT]
> - Watch-Modus läuft ([Rezept 14](14-watch-mode-tmux.md))
> - Tests haben `tag`-Felder

---

### Problem

5 RAG-Tests failen einzeln → 5 separate Issues. Du willst: **1 Issue** für "RAG-System defekt".

---

### Lösung

```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "tag_aggregation": true,
  "tag_threshold": 3,
  "tests": [
    {
      "name": "RAG-Query-1",
      "message": "Was steht in Kapitel 1?",
      "expected_keywords": ["Kapitel"],
      "weight": 1,
      "tag": "rag"
    },
    {
      "name": "RAG-Query-2",
      "message": "Was steht in Kapitel 2?",
      "expected_keywords": ["Kapitel"],
      "weight": 1,
      "tag": "rag"
    },
    {
      "name": "RAG-Query-3",
      "message": "Was steht in Kapitel 3?",
      "expected_keywords": ["Kapitel"],
      "weight": 1,
      "tag": "rag"
    },
    {
      "name": "RAG-Query-4",
      "message": "Was steht in Kapitel 4?",
      "expected_keywords": ["Kapitel"],
      "weight": 1,
      "tag": "rag"
    }
  ]
}
```

**Watch-Modus Verhalten:**

```bash
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --watch \
  --eval-interval 1800

# ──────────────────────────────────────────────────────────
# Szenario: RAG-System down
# ──────────────────────────────────────────────────────────
# Run 1: 4 RAG-Tests failen
# 
# ✗ Ohne tag_aggregation:
#   Issue #101: RAG-Query-1 fehlschlägt
#   Issue #102: RAG-Query-2 fehlschlägt
#   Issue #103: RAG-Query-3 fehlschlägt
#   Issue #104: RAG-Query-4 fehlschlägt
# 
# ✓ Mit tag_aggregation (tag_threshold=3):
#   Issue #100: [RAG] Systematischer Fehler (4 Tests failen)
#   
#   Body:
#   Die folgenden Tests mit Tag "rag" schlagen fehl:
#   - RAG-Query-1
#   - RAG-Query-2
#   - RAG-Query-3
#   - RAG-Query-4
#   
#   Mögliche Ursachen:
#   - Vector-DB offline (ChromaDB, Pinecone)
#   - Embedding-Model nicht geladen
#   - Index korrupt/leer
```

---

### Erklärung

**Tag-Aggregation Logik:**

```python
# evaluation.py (vereinfacht)
failed_by_tag = {}

for test in tests:
    if not test["passed"]:
        tag = test.get("tag", "untagged")
        failed_by_tag.setdefault(tag, []).append(test["name"])

for tag, failed_tests in failed_by_tag.items():
    if len(failed_tests) >= tag_threshold:
        create_aggregated_issue(
            title=f"[{tag.upper()}] Systematischer Fehler",
            body=f"{len(failed_tests)} Tests mit Tag '{tag}' failen:\n" +
                 "\n".join(f"- {name}" for name in failed_tests)
        )
```

**Threshold-Logik:**

| Threshold | Bedeutung |
|-----------|-----------|
| `2` | ≥2 Tests mit gleichem Tag failen → Meta-Issue |
| `3` | ≥3 Tests (Standard, verhindert False-Positives) |
| `5+` | Erst bei massiver Failure-Welle aggregieren |

**Tags Beispiele:**

```json
{
  "tests": [
    {"tag": "rag", "...": "..."},        // RAG-System
    {"tag": "auth", "...": "..."},       // Authentifizierung
    {"tag": "network", "...": "..."},    // Externe APIs
    {"tag": "context", "...": "..."},    // Context-Persistenz
    {"tag": "performance", "...": "..."} // Timeouts
  ]
}
```

---

### Best Practice

> [!TIP]
> **Hierarchische Tags:**
> ```json
> {
>   "tests": [
>     {"tag": "rag:vector", "...": "..."},
>     {"tag": "rag:embedding", "...": "..."},
>     {"tag": "rag:retrieval", "...": "..."}
>   ]
> }
> ```
> → Agent kann Sub-Tags erkennen (z.B. "rag:*")

> [!TIP]
> **Threshold nach Kategorie:**
> ```json
> {
>   "tag_aggregation": true,
>   "tag_thresholds": {
>     "rag": 3,
>     "auth": 2,
>     "performance": 5
>   }
> }
> ```

> [!TIP]
> **Issue-Labels für aggregierte Issues:**
> ```
> Issue #100: [RAG] Systematischer Fehler
> Labels: agent:aggregated, agent:rag, agent:high-priority
> ```

---

### Warnung

> [!WARNING]
> **Threshold zu niedrig:**
> ```json
> {"tag_threshold": 1}
> ```
> → Jeder einzelne Fehler wird aggregiert
> → Kein Unterschied zu normalen Issues

> [!WARNING]
> **Fehlende Tags:**
> ```json
> {
>   "tests": [
>     {"name": "Test1", "...": "..."},  // kein tag
>     {"name": "Test2", "...": "..."}   // kein tag
>   ],
>   "tag_aggregation": true
> }
> ```
> → Alle fallen in "untagged" → sinnlose Aggregation

> [!WARNING]
> **Aggregation verschleiert Root-Cause:**
> ```
> Issue #100: [RAG] Systematischer Fehler (4 Tests)
> → Tatsächlich: Nur 1 Test hat echten Bug
> → Die anderen 3 sind Follow-up-Failures
> ```
> → Details in Issue-Body prüfen, nicht blind fixen

---

### Nächste Schritte

✅ Tag-Aggregation konfiguriert  
→ [19 — Staleness-Check](19-staleness-check.md)  
→ [12 — Performance-Tests](12-performance-tests.md)  
→ [28 — Labels und Workflow](28-labels-and-workflow.md)
