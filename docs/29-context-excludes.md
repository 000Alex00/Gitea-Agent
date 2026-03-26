## Context-Excludes (exclude_dirs)

Irrelevante Ordner aus LLM-Context filtern.

---

### Voraussetzungen

> [!IMPORTANT]
> - Projekt mit vielen Ordnern (venv, node_modules, etc.)

---

### Problem

Agent lädt 50.000 Dateien aus `node_modules`, `venv`, `.git` → Token-Overflow. Du willst nur relevante Dateien.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Schritt 1: Exclude-Config erstellen
# ──────────────────────────────────────────────────────────
# ~/mein-projekt/agent/config/excludes.json

{
  "exclude_dirs": [
    "venv",
    "node_modules",
    ".git",
    ".vscode",
    ".idea",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    "*.egg-info",
    "logs",
    "tmp"
  ],
  "exclude_files": [
    "*.pyc",
    "*.pyo",
    "*.log",
    "*.tmp",
    ".DS_Store",
    "Thumbs.db",
    "package-lock.json",
    "yarn.lock"
  ],
  "include_patterns": [
    "src/**/*.py",
    "tests/**/*.py",
    "README.md",
    "pyproject.toml",
    "requirements.txt"
  ]
}

# ──────────────────────────────────────────────────────────
# Schritt 2: Agent mit Excludes starten
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --exclude-config agent/config/excludes.json \
  --build-skeleton

# Output:
# [Scanning] ~/mein-projekt
# [Exclude] venv/ (12.345 Dateien)
# [Exclude] node_modules/ (45.678 Dateien)
# [✓] 147 Dateien analysiert (vorher: 58.170)

# ──────────────────────────────────────────────────────────
# Schritt 3: .gitignore automatisch nutzen
# ──────────────────────────────────────────────────────────
python3 agent_start.py \
  --project ~/mein-projekt \
  --use-gitignore \
  --build-skeleton

# Agent liest: ~/mein-projekt/.gitignore
# Wendet alle Patterns automatisch an
```

---

### Erklärung

**Exclude-Strategien:**

### 1. Manuelle Exclude-Liste:
```json
{
  "exclude_dirs": ["venv", "node_modules"]
}
```

### 2. .gitignore-Integration:
```bash
--use-gitignore
```
→ Agent liest `.gitignore`, wandelt Patterns um

### 3. Include-Whitelist (strikt):
```json
{
  "include_patterns": ["src/**", "tests/**"],
  "mode": "whitelist"
}
```
→ **Nur** diese Patterns werden geladen (alles andere ignoriert)

**Pattern-Syntax:**

| Pattern | Bedeutung |
|---------|-----------|
| `venv` | Ordner `venv` auf jeder Ebene |
| `./venv` | Nur Top-Level `venv` |
| `*.pyc` | Alle `.pyc`-Dateien |
| `src/**/*.py` | Alle `.py`-Dateien in `src` (rekursiv) |
| `!important.log` | Negation (inkludiere trotz Exclude) |

**Token-Reduktion:**

```
Vorher (ohne Excludes):
- 58.170 Dateien
- 2.3 GB Code
- ~500k Tokens

Nachher (mit Excludes):
- 147 Dateien
- 12 MB Code
- ~3k Tokens

Ersparnis: 99.4%
```

---

### Best Practice

> [!TIP]
> **Standard-Excludes für Python:**
> ```json
> {
>   "exclude_dirs": [
>     "venv", ".venv", "env", ".env",
>     "__pycache__", ".pytest_cache", ".mypy_cache",
>     "dist", "build", "*.egg-info",
>     ".git", ".hg", ".svn"
>   ],
>   "exclude_files": [
>     "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll"
>   ]
> }
> ```

> [!TIP]
> **Standard-Excludes für JavaScript:**
> ```json
> {
>   "exclude_dirs": [
>     "node_modules", "bower_components",
>     "dist", "build", ".cache",
>     ".next", ".nuxt"
>   ],
>   "exclude_files": [
>     "package-lock.json", "yarn.lock", "pnpm-lock.yaml"
>   ]
> }
> ```

> [!TIP]
> **Conditional Excludes:**
> ```json
> {
>   "exclude_dirs": {
>     "development": ["tests", "docs"],
>     "production": ["tests", "docs", "examples"]
>   }
> }
> ```

---

### Warnung

> [!WARNING]
> **Wichtige Dateien excluded:**
> ```json
> {
>   "exclude_dirs": ["src"]  // ← FEHLER
> }
> ```
> → Agent hat keinen Source-Code mehr
> → Validierung mit `--dry-run`

> [!WARNING]
> **Negation-Reihenfolge:**
> ```json
> {
>   "exclude_files": ["*.log"],
>   "include_patterns": ["important.log"]
> }
> ```
> → `exclude` wird ZUERST angewendet
> → `important.log` wird trotzdem excluded
> → Lösung: `!important.log` in `exclude_files`

> [!WARNING]
> **.gitignore-Fallstricke:**
> ```
> # .gitignore
> *.log
> !debug.log
> ```
> → Agent muss Negation-Syntax unterstützen
> → Ggf. manuell excludes.json pflegen

---

### Nächste Schritte

✅ Context-Excludes konfiguriert  
→ [20 — AST-Skeleton](20-ast-skeleton.md)  
→ [21 — Codesegment-Strategie](21-codesegment-strategy.md)  
→ [40 — Best Practices](40-best-practices.md)
