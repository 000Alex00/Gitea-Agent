## Search-Replace-Patches (--apply-patch)

5-Stufen-Sicherheit bei Code-Änderungen.

---

### Voraussetzungen

> [!IMPORTANT]
> - Git-Repo mit sauberem Working-Tree
> - Backup-Branch empfohlen

---

### Problem

LLM generiert Patches die nicht exakt matchen → git-apply schlägt fehl → manuelle Nacharbeit. Du willst robustes Patching mit Fuzzy-Match.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Szenario: Agent generiert Patch
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --issue 99 \
  --branch fix/validation

# Issue #99: "Add input validation to process_message"
# 
# Agent generiert Patch:
# ──────────────────────────────────────────────────────────
# File: src/api.py
# 
# OLD:
# def process_message(self, msg):
#     return self.model.predict(msg)
# 
# NEW:
# def process_message(self, msg):
#     if not isinstance(msg, str):
#         raise ValueError("Message must be string")
#     if not msg.strip():
#         raise ValueError("Message cannot be empty")
#     return self.model.predict(msg)

# ──────────────────────────────────────────────────────────
# Patch-Anwendung (5 Stufen):
# ──────────────────────────────────────────────────────────
# [1/5] EXACT MATCH
#       → Suche "def process_message(self, msg):\n    return self.model.predict(msg)"
#       → ✓ Gefunden: Line 145-146
#       → Ersetze durch NEW-Code
# 
# [✓] Patch erfolgreich angewendet
# [✓] Syntax-Check: OK (Python-Parser validiert)
# [✓] Commit: "feat: Add input validation to process_message (Issue #99)"

# ──────────────────────────────────────────────────────────
# Fallback-Stufen (falls Exact Match fehlschlägt):
# ──────────────────────────────────────────────────────────
# [1] EXACT MATCH
#     → String-Vergleich 1:1
# 
# [2] WHITESPACE-NORMALIZATION
#     → Tabs → Spaces, trailing spaces entfernen
# 
# [3] FUZZY MATCH (90% Ähnlichkeit)
#     → difflib.SequenceMatcher
# 
# [4] AST-BASED MATCH
#     → Code semantisch vergleichen (Kommentare egal)
# 
# [5] INTERACTIVE MODE
#     → Patch als Kommentar posten → Manuelles Review
```

---

### Erklärung

**Patch-Format (intern):**

```json
{
  "file": "src/api.py",
  "search": "def process_message(self, msg):\n    return self.model.predict(msg)",
  "replace": "def process_message(self, msg):\n    if not isinstance(msg, str):\n        raise ValueError(\"Message must be string\")\n    if not msg.strip():\n        raise ValueError(\"Message cannot be empty\")\n    return self.model.predict(msg)",
  "confidence": 0.95
}
```

**5-Stufen-Strategie:**

### 1. Exact Match
```python
if search_string in file_content:
    file_content = file_content.replace(search_string, replace_string, 1)
```

### 2. Whitespace-Normalization
```python
def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()

if normalize(search_string) in normalize(file_content):
    # ... replace ...
```

### 3. Fuzzy Match
```python
from difflib import SequenceMatcher

for chunk in sliding_window(file_content, len(search_string)):
    ratio = SequenceMatcher(None, search_string, chunk).ratio()
    if ratio > 0.90:
        # ... replace ...
```

### 4. AST-Based Match
```python
import ast

search_ast = ast.parse(search_string)
for node in ast.walk(file_ast):
    if ast.dump(node) == ast.dump(search_ast):
        # ... replace ...
```

### 5. Interactive Mode
```python
post_issue_comment(
    f"Patch konnte nicht automatisch angewendet werden.\n"
    f"Bitte manuell prüfen:\n```diff\n{diff}\n```"
)
```

---

### Best Practice

> [!TIP]
> **Context-Lines im Patch:**
> ```python
> # 3 Zeilen vor/nach der Änderung
> search = """
>     def __init__(self, model):
>         self.model = model
>     
>     def process_message(self, msg):
>         return self.model.predict(msg)
>     
>     def close(self):
> """
> ```
> → Höhere Exact-Match-Rate

> [!TIP]
> **Dry-Run Mode:**
> ```bash
> python3 agent_start.py \
>   --project ~/proj \
>   --issue 99 \
>   --dry-run
> 
> # Zeigt Patches ohne Apply
> [DRY-RUN] Würde anwenden:
> src/api.py:145-146 (Exact Match)
> ```

> [!TIP]
> **Patch-Log für Debugging:**
> ```bash
> cat ~/mein-projekt/agent/data/patch.log
> 
> 2024-01-15 10:30 | Issue #99 | src/api.py
> Strategy: EXACT_MATCH | Success: True | Lines: 145-146
> ```

---

### Warnung

> [!WARNING]
> **Mehrere Matches:**
> ```python
> # Datei hat 3× den gleichen Code-Block
> def process_message(self, msg):
>     return self.model.predict(msg)
> 
> # ... 100 Zeilen später ...
> 
> def process_message(self, msg):  # ← welcher?
>     return self.model.predict(msg)
> ```
> → Agent ändert **ersten** Match
> → Lösung: Context-Lines erweitern

> [!WARNING]
> **AST-Match bei Non-Python:**
> ```
> File: config.json
> → AST-Strategy schlägt fehl
> → Fallback auf Fuzzy-Match
> ```

> [!WARNING]
> **Fuzzy-Match bei ähnlichem Code:**
> ```python
> # Zwei fast identische Funktionen
> def process_user_message(self, msg): ...
> def process_system_message(self, msg): ...
> 
> → Fuzzy-Match (90%) matched beide
> → Falscher Block wird geändert
> ```
> → Interactive Mode zeigt Diff zur Review

---

### Nächste Schritte

✅ Search-Replace-Patches verstanden  
→ [24 — Gitea-Version-Compare](24-gitea-version-compare.md)  
→ [37 — Search-Replace debuggen](37-search-replace-no-match.md)
