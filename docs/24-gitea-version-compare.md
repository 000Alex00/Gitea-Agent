## Gitea-Version-Compare (AST-Diff)

Eval-Regression → Auto-Issue mit Code-Diff.

---

### Voraussetzungen

> [!IMPORTANT]
> - Watch-Modus aktiv ([Rezept 14](14-watch-mode-tmux.md))
> - Server-Code in Gitea-Repo
> - Gitea-API-Token ([Rezept 02](02-first-setup.md))

---

### Problem

Eval bestand gestern, heute FAIL. Was hat sich geändert? Du willst automatischen Code-Diff zwischen Commits.

---

### Lösung

```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "version_compare": true,
  "server_gitea_repo": "user/mein-server",
  "tests": [
    {
      "name": "RAG-Query",
      "message": "Was steht in Kapitel 1?",
      "expected_keywords": ["Kapitel"],
      "weight": 2,
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
  --eval-interval 3600

# ──────────────────────────────────────────────────────────
# Timeline:
# ──────────────────────────────────────────────────────────
# 10:00 — Eval-Run #1: PASS (Score: 2.0 / 2.0)
#         → Baseline: 2.0
#         → Server-Commit: abc123
# 
# 11:00 — Server-Update:
#         → Commit def456: "Refactor RAG module"
#         → Server neu gestartet
# 
# 12:00 — Eval-Run #2: FAIL (Score: 0.0 / 2.0)
#         → Test "RAG-Query" failt
#         → Agent vergleicht: abc123 vs def456
#         → Issue #100 erstellt

# ──────────────────────────────────────────────────────────
# Issue #100: [REGRESSION] RAG-Query seit def456
# ──────────────────────────────────────────────────────────
# Test "RAG-Query" schlug fehl seit Commit def456.
# 
# **Letzter erfolgreicher Commit:** abc123
# **Aktueller Commit:** def456
# 
# ## Code-Änderungen (AST-Diff):
# 
# ### src/rag/retriever.py
# 
# ```diff
# - def query(self, text, top_k=5):
# + def query(self, text, top_k=3):  # ← top_k geändert
#       results = self.vector_db.search(text, limit=top_k)
#       return results
# ```
# 
# ```diff
# - embedding = self.model.encode(text)
# + embedding = self.model_v2.encode(text)  # ← model_v2?
# ```
# 
# ### src/rag/vector_db.py
# 
# ```diff
# + # Neues Feld hinzugefügt
# + self.cache_ttl = 600
# ```
# 
# **Potenzielle Root-Cause:**
# - `top_k` von 5 → 3 reduziert (weniger Kontext)
# - `model_v2` evtl. nicht initialisiert
# 
# **Nächste Schritte:**
# 1. `model_v2` prüfen (Typo?)
# 2. `top_k=3` auf 5 zurücksetzen
# 3. Tests für new `cache_ttl` schreiben
```

---

### Erklärung

**Version-Compare-Flow:**

```python
# agent_start.py (vereinfacht)
class VersionCompare:
    def on_eval_fail(self, current_score, baseline):
        # 1. Letzten erfolgreichen Commit finden
        last_success = self.score_history.last_pass_commit()
        # → abc123
        
        # 2. Aktuellen Commit vom Server abfragen
        current_commit = gitea_api.get_latest_commit(repo)
        # → def456
        
        # 3. Gitea-API: Diff abrufen
        diff = gitea_api.compare_commits(last_success, current_commit)
        
        # 4. AST-Diff generieren (nur relevante Änderungen)
        ast_diff = self.ast_compare(diff)
        
        # 5. Issue erstellen mit Diff
        create_issue(
            title=f"[REGRESSION] Test seit {current_commit[:7]}",
            body=self.format_diff(ast_diff)
        )
```

**AST-Diff vs. Text-Diff:**

### Text-Diff (git diff):
```diff
--- a/src/api.py
+++ b/src/api.py
@@ -10,6 +10,8 @@
 import logging
+import time  # neu importiert
 
 class API:
+    # neuer Kommentar
     def process(self):
```

### AST-Diff (semantisch):
```diff
+ Import hinzugefügt: time
  (Kommentare ignoriert)
```

**Score-History (tracking):**

```json
{
  "history": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "score": 2.0,
      "baseline": 2.0,
      "status": "PASS",
      "commit": "abc123"
    },
    {
      "timestamp": "2024-01-15T12:00:00Z",
      "score": 0.0,
      "baseline": 2.0,
      "status": "FAIL",
      "commit": "def456"
    }
  ]
}
```

---

### Best Practice

> [!TIP]
> **Gitea-Webhook für sofortigen Check:**
> ```bash
> # Gitea Repo-Settings → Webhooks
> URL: http://agent-host:5000/webhook
> Events: Push
> 
> # Agent startet Eval sofort nach Push
> → Kein Warten auf nächstes Intervall
> ```

> [!TIP]
> **Granulare Commits:**
> ```
> ✗ "Refactor RAG and fix auth"
> ✓ "Refactor RAG module"
> ✓ "Fix auth token validation"
> ```
> → AST-Diff zeigt präzise was Regression verursacht

> [!TIP]
> **Bisect-Integration:**
> ```bash
> # Bei Regression: Automatisches git-bisect
> cd ~/mein-server
> git bisect start def456 abc123
> git bisect run ~/Gitea-Agent/evaluation.py --project ~/mein-projekt
> 
> # → Findet exakten Commit der Test broke
> ```

---

### Warnung

> [!WARNING]
> **Gitea-API-Rate-Limits:**
> ```
> Version-Compare bei jedem Eval → viele API-Calls
> Gitea Default: 100 req/hour
> ```
> → Caching implementieren

> [!WARNING]
> **Commits ohne Server-Restart:**
> ```
> Commit def456 deployed
> Server läuft noch mit abc123
> → Version-Compare zeigt Diff, aber Test failt aus anderem Grund
> ```
> → Staleness-Check kombinieren ([Rezept 19](19-staleness-check.md))

> [!WARNING]
> **Große Diffs unlesbar:**
> ```
> 500 Dateien geändert → AST-Diff 50 KB
> → Issue-Body zu groß
> ```
> → Nur Diff für Dateien im Test-Tag (z.B. `tag: "rag"` → nur `src/rag/**`)

---

### Nächste Schritte

✅ Gitea-Version-Compare konfiguriert  
→ [19 — Staleness-Check](19-staleness-check.md)  
→ [25 — Log-Analyzer](25-log-analyzer.md)  
→ [18 — Tag-Aggregation](18-tag-aggregation.md)
