## Codesegment-Strategie (--get-slice)

98% Token-Reduktion: Nur betroffene Funktionen laden.

---

### Voraussetzungen

> [!IMPORTANT]
> - AST-Skeleton vorhanden ([Rezept 20](20-ast-skeleton.md))
> - Python-Projekt mit großen Dateien

---

### Problem

File hat 2000 Zeilen, Bug ist in 1 Funktion (30 Zeilen). Voller File → Token-Waste. Du willst: nur relevante Funktion laden.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Schritt 1: Skeleton bauen (falls noch nicht vorhanden)
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --build-skeleton

# ──────────────────────────────────────────────────────────
# Schritt 2: Code-Slice für spezifische Funktion abrufen
# ──────────────────────────────────────────────────────────
python3 agent_start.py \
  --project ~/mein-projekt \
  --get-slice src/api.py:ChatAPI.process_message

# Output:
# ──────────────────────────────────────────────────────────
# File: src/api.py
# Location: Line 145-178 (34 lines)
# 
# class ChatAPI:
#     def process_message(self, msg: str) -> dict:
#         """Process incoming chat message.
#         
#         Args:
#             msg: User message
#         
#         Returns:
#             Response dictionary
#         """
#         if not msg:
#             return {"error": "Empty message"}
#         
#         # ... 20 Zeilen Implementation ...
#         
#         return response

# ──────────────────────────────────────────────────────────
# Schritt 3: Agent nutzt Slices automatisch
# ──────────────────────────────────────────────────────────
python3 agent_start.py \
  --project ~/mein-projekt \
  --issue 77 \
  --branch bugfix/empty-message

# Issue #77:
# Titel: "process_message crashes on empty input"
# Body: "src/api.py:ChatAPI.process_message → IndexError"
# 
# Agent-Verhalten:
# 1. Liest Skeleton → findet ChatAPI.process_message
# 2. Lädt nur Lines 145-178 (nicht ganze 2000 Zeilen)
# 3. LLM bekommt:
#    - Function-Context (34 Zeilen)
#    - Dependencies (Imports, andere genutzte Methods)
# 4. Generiert Fix
# 5. Patch wird auf Lines 145-178 angewendet
```

---

### Erklärung

**Slice-Syntax:**

```
--get-slice <file>:<class>.<method>
--get-slice <file>:<function>
--get-slice <file>:lines:<start>-<end>
```

**Beispiele:**

| Slice | Bedeutung |
|-------|-----------|
| `src/api.py:ChatAPI` | Ganze Klasse ChatAPI |
| `src/api.py:ChatAPI.process_message` | Nur Methode process_message |
| `src/api.py:handle_request` | Top-Level-Funktion handle_request |
| `src/api.py:lines:100-150` | Zeilen 100-150 (manuell) |

**Auto-Slicing im Agent:**

```python
# agent_start.py (vereinfacht)
def parse_issue_body(body):
    # Erkennt Patterns:
    # - "File: src/api.py, Line: 145"
    # - "Traceback: src/api.py:145 in process_message"
    # - "Bug in ChatAPI.process_message"
    
    matches = re.findall(r'(\w+\.py):(\d+)', body)
    for file, lineno in matches:
        # Skeleton konsultieren
        function = skeleton.find_function_at_line(file, int(lineno))
        
        # Slice laden
        code_slice = get_slice(file, function)
        
        # LLM-Context hinzufügen
        context.append(code_slice)
```

**Token-Vergleich:**

```
Full-File-Strategy:
src/api.py: 2000 Zeilen × 4 Tokens/Zeile = 8000 Tokens

Slice-Strategy:
src/api.py:ChatAPI.process_message: 34 Zeilen × 4 = 136 Tokens
Savings: 98.3%
```

---

### Best Practice

> [!TIP]
> **Issue-Templates mit Slice-Hints:**
> ```markdown
> ## Bug Report
> 
> **File:** src/api.py
> **Function:** ChatAPI.process_message
> **Line:** 145
> 
> **Error:**
> IndexError bei leerem Input
> ```
> → Agent parsed automatisch → lädt nur relevanten Slice

> [!TIP]
> **Dependency-Expansion:**
> ```python
> def process_message(self, msg):
>     result = self._validate(msg)  # ruft andere Methode
>     return result
> ```
> → Agent lädt automatisch auch `_validate()` (Dependency-Graph)

> [!TIP]
> **Slice-Cache:**
> ```bash
> # ~/mein-projekt/data/slice_cache/
> ls
> api_ChatAPI_process_message.txt
> utils_format_response.txt
> ```
> → Wiederverwendung bei mehreren Issues

---

### Warnung

> [!WARNING]
> **Context-Loss bei engen Slices:**
> ```python
> # api.py (Line 145-178)
> def process_message(self, msg):
>     return self.model.predict(msg)  # model ist wo definiert?
> ```
> → Agent weiß nicht: `self.model` ist LLM-Wrapper
> → Lösung: Skeleton + Docstrings

> [!WARNING]
> **Cross-File-Dependencies:**
> ```python
> # api.py
> from utils import format_response
> 
> def process_message(self, msg):
>     return format_response(msg)  # in anderem File
> ```
> → Agent muss auch `utils.py:format_response` laden
> → Automatisch via Dependency-Analyse

> [!WARNING]
> **Slice bei Multi-File-Bugs:**
> ```
> Issue: "API und DB nicht synchron"
> → Slice-Strategy ungeeignet
> → Full-Context erforderlich
> ```

---

### Nächste Schritte

✅ Codesegment-Strategie verstanden  
→ [22 — Diff-Validation](22-diff-validation.md)  
→ [20 — AST-Skeleton](20-ast-skeleton.md)  
→ [40 — Best Practices](40-best-practices.md)
