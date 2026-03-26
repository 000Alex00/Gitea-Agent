## AST-Skeleton (--build-skeleton)

Token-Reduktion: Code-Struktur statt voller Files.

---

### Voraussetzungen

> [!IMPORTANT]
> - Python 3.10+ mit `ast` module (stdlib)
> - Projekt mit vielen großen Python-Dateien

---

### Problem

LLM-Context: 20 Dateien × 500 Zeilen = 10.000 Zeilen → Token-Limit. Du willst: nur Funktions-/Klassen-Signaturen → 95% Token-Ersparnis.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Skeleton erstellen
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --build-skeleton

# Output:
# [✓] Scanning ~/mein-projekt
# [✓] Analyzing 47 Python files...
# [✓] Skeleton saved: ~/mein-projekt/data/repo_skeleton.json

# ──────────────────────────────────────────────────────────
# Skeleton-Datei Struktur
# ──────────────────────────────────────────────────────────
cat ~/mein-projekt/data/repo_skeleton.json

{
  "files": {
    "src/main.py": {
      "functions": [
        {
          "name": "main",
          "args": [],
          "lineno": 15,
          "docstring": "Application entry point"
        }
      ],
      "classes": [
        {
          "name": "App",
          "lineno": 20,
          "methods": [
            {"name": "__init__", "args": ["self", "config"], "lineno": 21},
            {"name": "run", "args": ["self"], "lineno": 35}
          ],
          "docstring": "Main application class"
        }
      ],
      "imports": ["flask", "logging"],
      "size_kb": 12.3
    },
    "src/api.py": { "...": "..." }
  },
  "summary": {
    "total_files": 47,
    "total_functions": 203,
    "total_classes": 18,
    "total_size_kb": 587.2
  }
}

# ──────────────────────────────────────────────────────────
# Agent nutzt Skeleton automatisch
# ──────────────────────────────────────────────────────────
python3 agent_start.py \
  --project ~/mein-projekt \
  --issue 42 \
  --branch feature/new-api

# LLM-Prompt (simplified):
# ──────────────────────────────────────────────────────────
# REPOSITORY STRUCTURE (from skeleton):
# 
# src/main.py:
#   - main() [line 15]
#   - class App [line 20]
#     - __init__(self, config) [line 21]
#     - run(self) [line 35]
# 
# src/api.py:
#   - class API [line 10]
#     - route_chat(self, message) [line 45]
# 
# TASK: Implement /health endpoint in src/api.py
```

---

### Erklärung

**AST (Abstract Syntax Tree):**

```python
# Original Code (500 Zeilen):
class ChatAPI:
    """Handles chat requests."""
    
    def __init__(self, model):
        self.model = model
        self.cache = {}
        # ... 100 Zeilen init-Code ...
    
    def process_message(self, msg):
        """Process incoming message."""
        # ... 200 Zeilen Logik ...
    
    # ... weitere Methoden ...

# ──────────────────────────────────────────────────────────
# AST-Skeleton (20 Zeilen):
{
  "name": "ChatAPI",
  "lineno": 10,
  "docstring": "Handles chat requests.",
  "methods": [
    {
      "name": "__init__",
      "args": ["self", "model"],
      "lineno": 13
    },
    {
      "name": "process_message",
      "args": ["self", "msg"],
      "lineno": 25,
      "docstring": "Process incoming message."
    }
  ]
}
```

**Token-Reduktion:**

| Szenario | Voller Code | Skeleton | Ersparnis |
|----------|-------------|----------|-----------|
| Klein (10 Dateien) | 5.000 Zeilen | 250 Zeilen | 95% |
| Mittel (50 Dateien) | 25.000 Zeilen | 1.200 Zeilen | 95% |
| Groß (200 Dateien) | 100.000 Zeilen | 5.000 Zeilen | 95% |

**Wann Skeleton nutzen:**

1. **Planning-Phase:** Übersicht verschaffen
2. **Neue Features:** Wo gehört Code hin?
3. **Refactoring:** Struktur-Änderungen planen
4. **Cross-File-Changes:** Welche Files betroffen?

**Wann NICHT nutzen:**

- **Implementation:** Voller Code nötig für Patches
- **Bug-Hunting:** Logik-Details erforderlich

---

### Best Practice

> [!TIP]
> **Skeleton regelmäßig aktualisieren:**
> ```bash
> # Git-Hook: post-commit
> #!/bin/bash
> python3 ~/Gitea-Agent/agent_start.py \
>   --project ~/mein-projekt \
>   --build-skeleton
> ```

> [!TIP]
> **Exclude-Patterns:**
> ```json
> {
>   "exclude_dirs": ["tests/", "docs/", "venv/"],
>   "exclude_files": ["setup.py", "conftest.py"]
> }
> ```
> → In `config/settings.json`

> [!TIP]
> **Skeleton in README verlinken:**
> ```markdown
> # Project Structure
> 
> Siehe: `data/repo_skeleton.json`
> 
> Aktualisieren mit:
> ```bash
> python3 ~/Gitea-Agent/agent_start.py --project . --build-skeleton
> ```
> ```

---

### Warnung

> [!WARNING]
> **Skeleton veraltet:**
> ```
> Letztes Build: gestern
> Heute: 5 neue Dateien hinzugefügt
> → Agent kennt neue Files nicht
> ```
> → Auto-Update via Git-Hook

> [!WARNING]
> **Nicht für alle Sprachen:**
> ```
> Python: ✓ (ast module)
> JavaScript: ✗ (benötigt esprima/babel)
> TypeScript: ✗ (benötigt ts-morph)
> ```
> → Nur Python vollständig supported

> [!WARNING]
> **Docstrings fehlen:**
> ```python
> def process_message(msg):  # kein docstring
>     ...
> ```
> → Skeleton hat weniger Kontext
> → LLM muss raten was Funktion tut

---

### Nächste Schritte

✅ AST-Skeleton generiert  
→ [21 — Codesegment-Strategie](21-codesegment-strategy.md)  
→ [29 — Context-Excludes](29-context-excludes.md)  
→ [40 — Best Practices](40-best-practices.md)
