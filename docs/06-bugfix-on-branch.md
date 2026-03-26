## Bugfix während Implementierung (--fixup)

Schneller Commit-Kommentar für Bugfixes auf in-progress Issues.

---

### Voraussetzungen

> [!IMPORTANT]
> - Issue mit Label `in-progress` vorhanden
> - Auf Feature-Branch (nicht main)
> - Bugfix bereits committed

---

### Problem

Während der Implementierung entdeckst du einen Bug und fixst ihn. Du willst das schnell ins Issue dokumentieren, ohne den kompletten PR-Workflow.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Szenario: Issue #21 ist in-progress, du fixst einen Bug
# ──────────────────────────────────────────────────────────
cd ~/mein-projekt
git checkout fix/issue-21-timeout-handling

# Bug fixen
nano myproject/server.py
# → Exception-Handling verbessert

# Committen
git add myproject/server.py
git commit -m "fix: timeout exception handling in server.py"

# ──────────────────────────────────────────────────────────
# Fixup-Kommentar ins Issue posten
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py --fixup 21

# → [→] Lese letzte Commit-Message...
# → [→] Poste Kommentar ins Issue #21...
# → [✓] Kommentar gepostet
# → [✓] Label: in-progress → needs-review
```

**Generierter Kommentar:**
```markdown
🔧 Bugfix committed

**Commit:** fix: timeout exception handling in server.py
**Datei:** myproject/server.py
**Zeitpunkt:** 2026-03-26 14:30:00

Bitte Review des Fixes vor Merge.
```

---

### Erklärung

**Was macht --fixup?**
1. Liest letzte Commit-Message via `git log -1 --pretty=%s`
2. Prüft ob Issue Label `in-progress` hat
3. Postet strukturierten Bugfix-Kommentar
4. Wechselt Label zu `needs-review`

**Wann verwenden?**
- Bug während Implementierung entdeckt
- Schnelle Dokumentation ohne PR
- Mehrere Bugfixes vor finalem PR

**Unterschied zu --pr:**
- `--fixup`: Nur Kommentar, kein Eval, kein PR
- `--pr`: Vollständiger Abschluss mit Tests + PR-Erstellung

---

### Best Practice

> [!TIP]
> **Mehrere Bugfixes:**
> ```bash
> git commit -m "fix: bug 1"
> python3 agent_start.py --fixup 21
> 
> git commit -m "fix: bug 2"
> python3 agent_start.py --fixup 21
> 
> # Finaler PR:
> python3 agent_start.py --pr 21 --branch fix/... --summary "..."
> ```

> [!TIP]
> **Commit-Message-Konvention:**
> ```bash
> git commit -m "fix: kurze beschreibung"  # Bugfix
> git commit -m "refactor: code cleanup"   # Refactoring
> git commit -m "docs: update readme"      # Dokumentation
> ```
> → Wird automatisch im Kommentar übernommen

---

### Warnung

> [!WARNING]
> **Falsches Label:**
> ```
> [!] Issue #21 hat nicht Label 'in-progress'
> → --fixup nur für aktive Implementierungen
> ```

> [!WARNING]
> **Auf main-Branch:**
> ```bash
> git branch
> # * main  ← Falsch!
> 
> # Muss Feature-Branch sein:
> git checkout fix/issue-21-...
> ```

> [!WARNING]
> **Keine Commits vorhanden:**
> ```
> [!] Keine Commits gefunden
> → Erst committen, dann --fixup
> ```

---

### Nächste Schritte

✅ Bugfix dokumentiert  
→ [05 — Standard-Workflow fortsetzen](05-issue-to-pr.md)  
→ [08 — Manueller Workflow](08-manual-workflow.md)
