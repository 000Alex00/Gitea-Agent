## Labels und Workflow-Anpassung

Custom Labels für Agent-Steuerung.

---

### Voraussetzungen

> [!IMPORTANT]
> - Gitea-Repo mit Issues
> - Agent läuft ([Rezept 03](03-first-issue.md))

---

### Problem

Standard-Labels passen nicht zu deinem Workflow. Du willst eigene Labels und Regeln.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Schritt 1: Custom Labels in Gitea erstellen
# ──────────────────────────────────────────────────────────
# Gitea-Repo → Settings → Labels → New Label

agent:todo          # 🔵 Blau     → Agent soll bearbeiten
agent:in-progress   # 🟡 Gelb     → Agent arbeitet gerade
agent:review        # 🟠 Orange   → Code-Review erforderlich
agent:blocked       # 🔴 Rot      → Agent kann nicht weitermachen
agent:done          # 🟢 Grün     → Abgeschlossen

agent:low-risk      # 🟦 Hellblau → Night-Modus OK
agent:high-risk     # 🟥 Dunkelrot→ Nur manuell / Patch-Modus

agent:regression    # 🟣 Lila     → Eval-Failure
agent:perf          # 🟤 Braun    → Performance-Problem

agent:skip          # ⚫ Schwarz  → Agent soll ignorieren

# ──────────────────────────────────────────────────────────
# Schritt 2: Label-Konfiguration im Agent
# ──────────────────────────────────────────────────────────
# ~/mein-projekt/config/labels.json

{
  "workflow": {
    "todo": "agent:todo",
    "in_progress": "agent:in-progress",
    "review": "agent:review",
    "blocked": "agent:blocked",
    "done": "agent:done",
    "skip": "agent:skip"
  },
  "risk_levels": {
    "low": "agent:low-risk",
    "high": "agent:high-risk"
  },
  "issue_types": {
    "regression": "agent:regression",
    "performance": "agent:perf"
  },
  "rules": {
    "night_mode": {
      "allowed_labels": ["agent:low-risk"],
      "forbidden_labels": ["agent:high-risk", "agent:skip"]
    },
    "auto_close": {
      "required_labels": ["agent:done"],
      "forbidden_labels": ["agent:blocked"]
    }
  }
}

# ──────────────────────────────────────────────────────────
# Schritt 3: Agent mit Custom-Labels starten
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py \
  --project ~/mein-projekt \
  --label-config config/labels.json \
  --watch

# Verhalten:
# ──────────────────────────────────────────────────────────
# Issue #42: "Fix typo"
# Labels: agent:todo, agent:low-risk
# 
# Agent-Workflow:
# 1. Findet Issue (hat agent:todo)
# 2. Setzt Label: agent:in-progress
# 3. Erstellt Branch, implementiert Fix
# 4. Setzt Label: agent:review
# 5. Erstellt PR
# 6. Nach Eval-Pass: Setzt Label: agent:done
# 7. Entfernt Label: agent:in-progress
```

---

### Erklärung

**Label-Lifecycle:**

```
┌─────────────────┐
│  Issue created  │
│  (no labels)    │
└────────┬────────┘
         │
         ↓ User adds: agent:todo
┌─────────────────┐
│   agent:todo    │ ← Agent scannt Issues
└────────┬────────┘
         │
         ↓ Agent startet Arbeit
┌─────────────────┐
│ agent:in-progress│
└────────┬────────┘
         │
         ↓ Code fertig
┌─────────────────┐
│  agent:review   │ ← PR erstellt
└────────┬────────┘
         │
         ↓ Eval PASS + Review approved
┌─────────────────┐
│   agent:done    │ ← Issue geschlossen
└─────────────────┘
```

**Risk-Level-Logik:**

```python
# agent_start.py (vereinfacht)
def scan_issues():
    issues = gitea.get_issues(repo)
    
    for issue in issues:
        labels = [l["name"] for l in issue["labels"]]
        
        # Skip-Check
        if "agent:skip" in labels:
            continue
        
        # Night-Mode-Check
        if night_mode_active():
            if "agent:high-risk" in labels:
                continue  # Überspringe high-risk
            if "agent:low-risk" not in labels:
                continue  # Nur explizit low-risk
        
        # Workflow-Check
        if "agent:todo" in labels:
            process_issue(issue)
```

**Custom-Workflow-Regeln:**

### Auto-Review-Merge:
```json
{
  "rules": {
    "auto_merge": {
      "required_labels": ["agent:low-risk", "agent:done"],
      "forbidden_labels": ["agent:blocked", "breaking-change"]
    }
  }
}
```

### Priority-Queue:
```json
{
  "rules": {
    "priority": {
      "high": ["agent:urgent", "agent:security"],
      "medium": ["agent:todo"],
      "low": ["agent:nice-to-have"]
    }
  }
}
```

---

### Best Practice

> [!TIP]
> **Label-Template in Issue-Templates:**
> ```markdown
> ---
> name: Bug Report
> labels: agent:todo, agent:high-risk
> ---
> 
> ## Bug Description
> ...
> ```

> [!TIP]
> **Color-Coding konsequent:**
> ```
> 🔵 Blau    → To-Do / Neu
> 🟡 Gelb    → In Arbeit
> 🟢 Grün    → Fertig / OK
> 🔴 Rot     → Fehler / Blockiert
> 🟣 Lila    → Automatisch erstellt (Agent)
> ```

> [!TIP]
> **Label-Sync mit CI/CD:**
> ```yaml
> # .github/workflows/label-sync.yml
> on:
>   issues:
>     types: [labeled]
> 
> jobs:
>   sync:
>     if: contains(github.event.label.name, 'agent:')
>     runs-on: ubuntu-latest
>     steps:
>       - name: Trigger Agent
>         run: curl -X POST http://agent-server:5000/webhook
> ```

---

### Warnung

> [!WARNING]
> **Label-Typo:**
> ```
> Issue hat: agent:todo
> Agent sucht: agent:to-do
> → Issue wird nicht gefunden
> ```
> → labels.json als Single-Source-of-Truth

> [!WARNING]
> **Zu viele Labels:**
> ```
> Issue hat: agent:todo, agent:bug, agent:frontend, agent:urgent, agent:low-risk
> → Unübersichtlich
> ```
> → Max. 3-4 Labels pro Issue

> [!WARNING]
> **Forbidden-Labels überschreibbar:**
> ```json
> {
>   "auto_merge": {
>     "forbidden_labels": ["agent:blocked"]
>   }
> }
> ```
> → User kann `agent:blocked` entfernen → Auto-Merge aktiv
> → Nur als Sicherheitsnetz, nicht als Hard-Lock

---

### Nächste Schritte

✅ Labels konfiguriert  
→ [16 — Night vs Patch Modus](16-night-vs-patch.md)  
→ [40 — Best Practices](40-best-practices.md)
