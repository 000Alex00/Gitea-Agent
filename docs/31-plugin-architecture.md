## Plugin-Architektur verstehen

Wie patch.py und changelog.py funktionieren.

---

### Voraussetzungen

> [!IMPORTANT]
> - Python 3.10+ Kenntnisse
> - Agent-Codebase geklont

---

### Problem

Du willst verstehen wie Plugins strukturiert sind, um eigene zu schreiben.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Plugin-Struktur
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
tree plugins/

plugins/
├── __init__.py
├── patch.py           # Search-Replace-Patches
├── changelog.py       # CHANGELOG.md-Generator
├── llm.py             # LLM-Routing (lädt config/llm/routing.json)
├── llm_config_guard.py # IDE-Config-Guard (CLAUDE.md, .cursorrules, etc.)
└── log_analyzer.py    # (Optional, User-created)

# ──────────────────────────────────────────────────────────
# Plugin-Template (patch.py vereinfacht)
# ──────────────────────────────────────────────────────────
# plugins/patch.py

"""
Search-Replace-Patch-Plugin.

Wendet LLM-generierte Code-Änderungen an.
"""

from typing import Dict, List, Optional
from pathlib import Path
import difflib

class PatchPlugin:
    """Handles code patching with 5-stage fallback."""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
    
    def apply_patches(self, patches: List[Dict]) -> List[Dict]:
        """Apply list of patches.
        
        Args:
            patches: List of {file, search, replace} dicts
        
        Returns:
            List of results with status
        """
        results = []
        
        for patch in patches:
            result = self._apply_single_patch(patch)
            results.append(result)
        
        return results
    
    def _apply_single_patch(self, patch: Dict) -> Dict:
        """Apply single patch with fallback strategies."""
        file_path = self.project_path / patch["file"]
        
        # Read file
        with open(file_path, "r") as f:
            content = f.read()
        
        # Try strategies
        strategies = [
            self._exact_match,
            self._whitespace_normalized,
            self._fuzzy_match,
            self._ast_based,
            self._interactive
        ]
        
        for strategy in strategies:
            result = strategy(content, patch)
            if result["success"]:
                self._write_file(file_path, result["new_content"])
                return result
        
        return {"success": False, "error": "All strategies failed"}
    
    def _exact_match(self, content: str, patch: Dict) -> Dict:
        """Strategy 1: Exact string match."""
        if patch["search"] in content:
            new_content = content.replace(
                patch["search"],
                patch["replace"],
                1  # nur erstes Vorkommen
            )
            return {
                "success": True,
                "strategy": "EXACT_MATCH",
                "new_content": new_content
            }
        return {"success": False}
    
    # ... weitere Strategies ...

# ──────────────────────────────────────────────────────────
# Plugin registrieren
# ──────────────────────────────────────────────────────────
# plugins/__init__.py

from plugins.patch import PatchPlugin
from plugins.changelog import ChangelogPlugin

PLUGINS = {
    "patch": PatchPlugin,
    "changelog": ChangelogPlugin
}

def load_plugin(name: str, project_path: str):
    """Load plugin by name."""
    if name not in PLUGINS:
        raise ValueError(f"Unknown plugin: {name}")
    
    return PLUGINS[name](project_path)

# ──────────────────────────────────────────────────────────
# Plugin im Agent nutzen
# ──────────────────────────────────────────────────────────
# agent_start.py (vereinfacht)

from plugins import load_plugin

# Plugin laden
patch_plugin = load_plugin("patch", project_path)

# Plugin ausführen
patches = [
    {
        "file": "src/api.py",
        "search": "def process(msg):\n    return msg",
        "replace": "def process(msg):\n    if not msg:\n        raise ValueError()\n    return msg"
    }
]

results = patch_plugin.apply_patches(patches)

for result in results:
    if result["success"]:
        print(f"✓ Patch applied: {result['strategy']}")
    else:
        print(f"✗ Patch failed: {result['error']}")
```

---

### Erklärung

**Plugin-Interface:**

Jedes Plugin muss implementieren:

```python
class MyPlugin:
    def __init__(self, project_path: str):
        """Initialisierung mit Projekt-Pfad."""
        pass
    
    def execute(self, **kwargs):
        """Haupt-Funktionalität."""
        pass
```

**Plugin-Lifecycle:**

```
┌─────────────────────────────────────────────┐
│ Agent-Start                                 │
├─────────────────────────────────────────────┤
│ 1. Scanne plugins/ Ordner                  │
│ 2. Importiere alle .py-Dateien             │
│ 3. Registriere in PLUGINS-Dict             │
└─────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────┐
│ Issue-Verarbeitung                          │
├─────────────────────────────────────────────┤
│ 1. LLM generiert Patches                   │
│ 2. load_plugin("patch")                    │
│ 3. plugin.apply_patches(patches)           │
│ 4. Return success/failure                  │
└─────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────┐
│ Post-Commit                                 │
├─────────────────────────────────────────────┤
│ 1. load_plugin("changelog")                │
│ 2. plugin.update_changelog(commit)         │
└─────────────────────────────────────────────┘
```

**Builtin-Plugins:**

### patch.py:
- **Input:** List[{file, search, replace}]
- **Output:** List[{success, strategy, error}]
- **Use-Case:** Code-Änderungen anwenden

### changelog.py:
- **Input:** commit_message, commit_hash
- **Output:** Updated CHANGELOG.md
- **Use-Case:** Conventional-Commits → Changelog

### llm.py:
- **Input:** task-Name (z.B. "implementation")
- **Output:** LLM-Client-Instanz
- **Use-Case:** `get_client(task="implementation").complete(prompt)` → LLMResponse
- Liest `config/llm/routing.json` → Provider + Modell pro Task
- Lädt System-Prompts aus `config/llm/prompts/` automatisch

### llm_config_guard.py:
- **Use-Case:** Prüft IDE-Config-Dateien auf Aktualität
- Prüft: `CLAUDE.md`, `.cursorrules`, `.clinerules`, `copilot-instructions.md`, `windsurfrules`, `GEMINI.md`, `AGENTS.md`
- Modi: `--repair` (repariert), `--create` (erstellt fehlende), `--verbose`
- Templates in `config/llm/ide/`
- Läuft als pre-commit Hook

---

### Best Practice

> [!TIP]
> **Plugin-Konfiguration:**
> ```python
> class MyPlugin:
>     def __init__(self, project_path: str, config: dict):
>         self.config = config
>         # ...
> 
> # Laden mit Config:
> plugin = MyPlugin(path, {"timeout": 30, "verbose": True})
> ```

> [!TIP]
> **Error-Handling:**
> ```python
> def execute(self, **kwargs):
>     try:
>         result = self._do_work(kwargs)
>         return {"success": True, "result": result}
>     except Exception as e:
>         return {"success": False, "error": str(e)}
> ```

> [!TIP]
> **Logging:**
> ```python
> import logging
> 
> class MyPlugin:
>     def __init__(self, project_path: str):
>         self.logger = logging.getLogger(__name__)
>     
>     def execute(self):
>         self.logger.info("Plugin started")
>         # ...
> ```

---

### Warnung

> [!WARNING]
> **Plugin-Name-Konflikt:**
> ```python
> # plugins/patch.py (builtin)
> # plugins/patch.py (user-created)
> → User-Plugin überschreibt builtin
> ```
> → Namespace: `plugins/custom/my_patch.py`

> [!WARNING]
> **Fehlende Dependencies:**
> ```python
> # Plugin nutzt externe Library
> import specialized_lib  # nicht in stdlib
> 
> → Agent-Crash wenn nicht installiert
> ```
> → Dependencies in Plugin-Docstring dokumentieren

> [!WARNING]
> **Plugin-Performance:**
> ```python
> def execute(self):
>     time.sleep(60)  # ← blockiert Agent
> ```
> → Langläufige Tasks in Background-Thread

---

### Nächste Schritte

✅ Plugin-Architektur verstanden  
→ [32 — Custom-Plugin erstellen](32-create-custom-plugin.md)  
→ [33 — Changelog-Automation](33-changelog-automation.md)  
→ [25 — Log-Analyzer](25-log-analyzer.md)
