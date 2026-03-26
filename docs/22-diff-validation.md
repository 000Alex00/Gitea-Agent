## Diff-Validation (Out-of-Scope Warnung)

Agent warnt bei Änderungen außerhalb Issue-Scope.

---

### Voraussetzungen

> [!IMPORTANT]
> - Issue mit klarem Scope
> - Agent im Plan-Review-Workflow ([Rezept 05](05-issue-to-pr.md))

---

### Problem

Issue: "Fix typo in README". Agent ändert auch: `src/api.py` + `tests/`. Du willst Warnung bei Scope-Creep.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Workflow mit Diff-Validation
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --issue 88 \
  --branch fix/readme-typo

# Issue #88:
# Titel: "Fix typo in README"
# Body: "Word 'occurence' → 'occurrence' in README.md"
# 
# ──────────────────────────────────────────────────────────
# Agent-Plan:
# ──────────────────────────────────────────────────────────
# [✓] Plan erstellt:
#     1. README.md ändern (Line 42: occurence → occurrence)
# 
# Du: approve
# 
# ──────────────────────────────────────────────────────────
# Agent-Implementation:
# ──────────────────────────────────────────────────────────
# [✓] Patch angewendet: README.md
# [!] Warnung: Unerwartete Änderungen:
#     - src/api.py (+15 / -3 Zeilen)
#     - tests/test_api.py (+8 Zeilen)
# 
# [?] Diff-Review erforderlich (Post in Issue #88)

# ──────────────────────────────────────────────────────────
# Agent-Kommentar in Issue #88:
# ──────────────────────────────────────────────────────────
# ⚠️ OUT-OF-SCOPE CHANGES DETECTED
# 
# Issue-Scope: README.md
# Tatsächliche Änderungen:
# 
# ✓ README.md (1 Zeile geändert)
# ⚠️ src/api.py (15 Zeilen hinzugefügt, 3 entfernt)
# ⚠️ tests/test_api.py (8 Zeilen hinzugefügt)
# 
# Diff-Preview:
# ```diff
# --- src/api.py
# +++ src/api.py
# @@ -145,3 +145,18 @@
#  def process_message(self, msg):
# +    # Neuer Logging-Code (WARUM?)
# +    logger.info("Processing: %s", msg)
# ```
# 
# Bitte bestätigen oder ablehnen:
# - approve-oos (out-of-scope akzeptieren)
# - reject-oos (nur README-Änderung committen)
```

---

### Erklärung

**Scope-Detection:**

```python
# agent_start.py (vereinfacht)
def validate_changes(issue, changed_files):
    # 1. Issue-Body parsen
    mentioned_files = extract_file_references(issue.body)
    # Beispiel: ["README.md"]
    
    # 2. Git-Diff auslesen
    changed_files = get_changed_files()
    # Beispiel: ["README.md", "src/api.py", "tests/test_api.py"]
    
    # 3. Out-of-Scope Dateien identifizieren
    oos_files = set(changed_files) - set(mentioned_files)
    
    if oos_files:
        post_warning(issue, oos_files)
        return "REVIEW_REQUIRED"
    
    return "OK"
```

**File-Reference-Patterns:**

```markdown
# Issue-Body Patterns (werden erkannt):
- "Fix typo in README.md"
- "Bug in `src/api.py`, line 145"
- "Files: README.md, docs/INSTALL.md"
- "Traceback: src/api.py:145"
```

**Validation-Modes:**

| Mode | Verhalten |
|------|-----------|
| **strict** | Jede OOS-Änderung blockiert PR |
| **warn** | Warnung posten, aber PR erstellen |
| **off** | Keine Validation |

```json
{
  "diff_validation": "warn"
}
```

---

### Best Practice

> [!TIP]
> **Issue-Template mit File-Liste:**
> ```markdown
> ## Bug Report
> 
> **Affected Files:**
> - [ ] src/api.py
> - [ ] tests/test_api.py
> 
> **Description:**
> ...
> ```
> → Agent parsed Checkboxen → klarer Scope

> [!TIP]
> **Auto-Approve für Test-Änderungen:**
> ```json
> {
>   "diff_validation": "warn",
>   "oos_whitelist": ["tests/**", "docs/**"]
> }
> ```
> → Tests/Docs automatisch erlaubt

> [!TIP]
> **Diff-Review in PR-Description:**
> ```
> PR #42: Fix README typo
> 
> ⚠️ Out-of-Scope:
> - src/api.py (Logging hinzugefügt)
> 
> Begründung:
> Logging fehlte für Debugging
> ```

---

### Warnung

> [!WARNING]
> **False-Positives bei vagen Issues:**
> ```markdown
> Issue: "Improve API"
> → Keine Files erwähnt
> → Jede Änderung gilt als OOS
> ```
> → Issue-Quality wichtig ([Rezept 40](40-best-practices.md))

> [!WARNING]
> **Strict-Mode blockiert legitime Fixes:**
> ```
> Issue: "Fix API bug"
> Agent findet: Bug ist in utils.py, nicht api.py
> → Strict-Mode blockiert utils.py-Änderung
> ```
> → `warn`-Mode flexibler

> [!WARNING]
> **OOS-Check bei Refactorings sinnlos:**
> ```
> Issue: "Refactor codebase"
> → 50 Dateien betroffen
> → OOS-Check bringt nichts
> ```
> → `diff_validation: off` für Refactoring-Issues

---

### Nächste Schritte

✅ Diff-Validation verstanden  
→ [23 — Search-Replace-Patches](23-search-replace-patches.md)  
→ [40 — Best Practices](40-best-practices.md)
