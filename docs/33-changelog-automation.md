## Changelog-Automation (changelog.py)

Conventional-Commits → automatisches CHANGELOG.md.

---

### Voraussetzungen

> [!IMPORTANT]
> - Git mit Conventional-Commits
> - changelog.py Plugin verfügbar

---

### Problem

PRs werden gemerged, aber CHANGELOG.md wird nie aktualisiert. Du willst automatische Changelog-Generierung.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Schritt 1: Conventional-Commits nutzen
# ──────────────────────────────────────────────────────────
cd ~/mein-projekt

# Beispiel-Commits:
git commit -m "feat: Add RAG support (Issue #42)"
git commit -m "fix: Handle empty messages (Issue #45)"
git commit -m "docs: Update README"
git commit -m "refactor: Simplify API module"
git commit -m "perf: Reduce context loading time"

# ──────────────────────────────────────────────────────────
# Schritt 2: Changelog aktivieren
# ──────────────────────────────────────────────────────────
# ~/mein-projekt/agent/config/settings.json

{
  "changelog": {
    "enabled": true,
    "file": "CHANGELOG.md",
    "format": "keep-a-changelog",
    "sections": {
      "feat": "Added",
      "fix": "Fixed",
      "docs": "Documentation",
      "refactor": "Changed",
      "perf": "Performance",
      "test": "Testing"
    },
    "link_issues": true
  }
}

# ──────────────────────────────────────────────────────────
# Schritt 3: Agent aktualisiert Changelog automatisch
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --issue 42 \
  --branch feature/rag

# Nach PR-Merge:
# → changelog.py wird ausgeführt
# → CHANGELOG.md wird aktualisiert

# ──────────────────────────────────────────────────────────
# Resultat: CHANGELOG.md
# ──────────────────────────────────────────────────────────
cat ~/mein-projekt/CHANGELOG.md

# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Add RAG support ([#42](https://gitea.example.com/user/repo/issues/42))

### Fixed
- Handle empty messages ([#45](https://gitea.example.com/user/repo/issues/45))

### Changed
- Simplify API module

### Performance
- Reduce context loading time

### Documentation
- Update README

## [1.0.0] - 2024-01-10

### Added
- Initial release
```

---

### Erklärung

**Conventional-Commits-Format:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

| Type | Beschreibung | Changelog-Section |
|------|--------------|-------------------|
| `feat` | Neue Features | Added |
| `fix` | Bugfixes | Fixed |
| `docs` | Dokumentation | Documentation |
| `refactor` | Code-Umstrukturierung | Changed |
| `perf` | Performance-Verbesserungen | Performance |
| `test` | Tests hinzugefügt/geändert | Testing |
| `chore` | Build/Tooling | (nicht in Changelog) |
| `style` | Formatierung | (nicht in Changelog) |

**Issue-Linking:**

```bash
# Commit-Message:
git commit -m "feat: Add RAG (Issue #42)"

# Changelog-Eintrag:
- Add RAG ([#42](https://gitea.example.com/user/repo/issues/42))
```

**Changelog-Workflow:**

```
┌──────────────────┐
│ PR merged        │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ changelog.py     │
├──────────────────┤
│ 1. Parse Commits │
│ 2. Group by Type │
│ 3. Update MD     │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ CHANGELOG.md     │
│ updated          │
└──────────────────┘
```

---

### Best Practice

> [!TIP]
> **Breaking-Changes markieren:**
> ```bash
> git commit -m "feat!: Change API endpoint structure

BREAKING CHANGE: /chat endpoint now requires 'message' field"
> ```
> → Changelog: "⚠️ BREAKING CHANGE: ..."

> [!TIP]
> **Scope nutzen:**
> ```bash
> git commit -m "feat(api): Add /health endpoint"
> git commit -m "fix(rag): Handle empty vectors"
> 
> # Changelog:
> ### Added
> - **api:** Add /health endpoint
> 
> ### Fixed
> - **rag:** Handle empty vectors
> ```

> [!TIP]
> **Release-Tagging:**
> ```bash
> # Version bumpen
> git tag v1.1.0
> 
> # Changelog.py erkennt Tags:
> ## [1.1.0] - 2024-01-15
> ### Added
> - ...
> ```

---

### Warnung

> [!WARNING]
> **Nicht-Conventional-Commits:**
> ```bash
> git commit -m "fixed bug"  # ← kein Type
> git commit -m "Added stuff" # ← falsches Format
> ```
> → Nicht in Changelog aufgenommen
> → Commit-Hooks nutzen (commitlint)

> [!WARNING]
> **Doppelte Einträge:**
> ```
> Agent commitet CHANGELOG.md-Update
> Dann erneuter PR-Merge
> → changelog.py läuft wieder
> → Changelog hat doppelte Entries
> ```
> → Deduplizierung in changelog.py

> [!WARNING]
> **Manual-Edits überschrieben:**
> ```markdown
> # CHANGELOG.md (manuell editiert)
> ## [Unreleased]
> - My custom entry
> 
> → changelog.py überschreibt komplett
> ```
> → "<!-- AGENT_MANAGED -->" Marker nutzen

---

### Nächste Schritte

✅ Changelog-Automation aktiv  
→ [31 — Plugin-Architektur](31-plugin-architecture.md)  
→ [32 — Custom-Plugin](32-create-custom-plugin.md)
