## Labels und Workflow

Alle Built-in-Labels, ihre Bedeutung und der `help wanted`-Flow.

---

### Voraussetzungen

> [!IMPORTANT]
> - Basis-Setup durchgeführt ([Rezept 02](02-first-setup.md))
> - Labels in Gitea angelegt (`--setup-labels`)

---

### Problem

Welche Labels setzt der Agent wann? Was bedeutet `help wanted` und wie kommt ein Issue wieder in den normalen Flow?

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Labels anlegen (einmalig, Teil von --setup)
# ──────────────────────────────────────────────────────────
python3 agent_start.py --project ~/mein-projekt --setup
# Schritt 4/9 im Wizard legt alle 5 Labels automatisch an

# ──────────────────────────────────────────────────────────
# Standard-Workflow (Risikostufe 1)
# ──────────────────────────────────────────────────────────

# 1. Issue erstellen + Label setzen
#    Gitea: Neues Issue → Label "ready-for-agent" setzen

# 2. Plan posten
python3 agent_start.py --project ~/proj --issue 42
# → Label: agent-proposed  (ready-for-agent wird entfernt)
# → Gitea: Plan-Kommentar mit "OK zum Implementieren?"

# 3. Freigabe geben
#    Gitea: Kommentar "ok" oder "ja" oder "✅"

# 4. Implementierung starten
python3 agent_start.py --project ~/proj --implement 42
# → Label: in-progress  (agent-proposed wird entfernt)
# → Branch erstellt

# 5. PR erstellen
python3 agent_start.py --project ~/proj --pr 42
# → Label: needs-review  (in-progress wird entfernt)
# → PR in Gitea erstellt

# ──────────────────────────────────────────────────────────
# help wanted-Workflow (Risikostufe ≥ 2: Bug / Feature)
# ──────────────────────────────────────────────────────────

# 1. Issue mit Label "ready-for-agent"
#    (enthält Bug-Label oder Feature-Label)

# 2. Plan + Analyse-Kommentar
python3 agent_start.py --project ~/proj --issue 42
# → Labels: agent-proposed + help wanted  (beide gesetzt)
# → Gitea: Plan-Kommentar + Analyse mit offenen Fragen

# 3. User klärt Fragen (Kommentare in Gitea)

# 4. User gibt manuell frei:
#    a) Label "help wanted" in Gitea manuell ENTFERNEN
#    b) Kommentar "ok" schreiben

# 5. Implementierung (manuell oder auto-scan)
python3 agent_start.py --project ~/proj --implement 42
# → Prüft: help wanted nicht mehr vorhanden + ok-Kommentar
# → Label: in-progress
```

---

### Erklärung

**Die 5 Built-in-Labels:**

| Label | Variable | Standard-Name | Bedeutung |
|-------|----------|---------------|-----------|
| LABEL_READY | `LABEL_READY` | `ready-for-agent` | User-Signal: Issue bearbeiten |
| LABEL_PROPOSED | `LABEL_PROPOSED` | `agent-proposed` | Plan gepostet, wartet auf Freigabe |
| LABEL_PROGRESS | `LABEL_PROGRESS` | `in-progress` | Agent implementiert gerade |
| LABEL_REVIEW | `LABEL_REVIEW` | `needs-review` | PR erstellt, wartet auf Review |
| LABEL_HELP | `LABEL_HELP` | `help wanted` | Hohe Risikostufe — Mensch muss entscheiden |

Alle Namen per `.env` änderbar:
```bash
LABEL_READY=ready-for-agent
LABEL_PROPOSED=agent-proposed
LABEL_PROGRESS=in-progress
LABEL_REVIEW=needs-review
LABEL_HELP=help wanted
```

---

**Label-Lifecycle (Standard):**

```
Issue erstellt
     │
     ↓  User setzt Label
 ready-for-agent
     │
     ↓  --issue N  (cmd_plan)
 agent-proposed         ← wartet auf "ok"-Kommentar
     │
     ↓  --implement N  (cmd_implement)
 in-progress
     │
     ↓  --pr N  (cmd_pr)
 needs-review
     │
     ↓  Merge + Issue schließen (manuell)
 [geschlossen]
```

---

**help wanted-Lifecycle (Risikostufe ≥ 2):**

```
 ready-for-agent
     │
     ↓  --issue N  (Bug oder Feature erkannt)
 agent-proposed
 + help wanted          ← BEIDE Labels gleichzeitig!
     │                    Gitea: Analyse-Kommentar mit Fragen
     │
     ↓  User: Fragen beantworten + "help wanted" MANUELL entfernen
 agent-proposed          ← nur noch agent-proposed
     │
     ↓  User: "ok" kommentieren
     │
     ↓  --implement N (oder auto-scan)
 in-progress
```

> **Wichtig:** `agent-proposed` bleibt während `help wanted` aktiv.
> So findet der Auto-Scan das Issue weiterhin und prüft nach der manuellen
> Label-Entfernung automatisch auf Freigabe.

---

**Risikostufen:**

| Stufe | Auslöser | Verhalten |
|-------|----------|-----------|
| 1 | Enhancement mit safe Keywords (docs, cleanup, import) | Direkt `agent-proposed`, kein `help wanted` |
| 2 | Enhancement ohne safe Keywords | `agent-proposed` + `help wanted` |
| 3 | Bug-Label oder Feature-Label | `agent-proposed` + `help wanted` |
| 4 | Manuell gesetzt (kritische Issues) | Kein Auto-Implement möglich |

---

**Auto-Freigabe-Prüfung (`check_approval`):**

```
check_approval(#42, blocked_label="help wanted")
    │
    ├─ "help wanted" noch am Issue?
    │      → Nein weiter
    │      → Ja: return False (blockiert)
    │
    └─ Kommentar nach letztem Agent-Kommentar?
           enthält "ok" / "ja" / "✅" / "approved"?
               → Ja: return True
               → Nein: return False
```

---

### Best Practice

> [!TIP]
> **Labels via `--setup` anlegen:**
> ```bash
> python3 agent_start.py --project ~/proj --setup
> # Schritt 4/9: Labels anlegen (interaktiv, prüft vorhandene)
> # Alternativ: Gitea → Repo → Settings → Labels → manuell anlegen
> ```

> [!TIP]
> **Approval-Keywords anpassen:**
> ```bash
> # .env
> APPROVAL_KEYWORDS=ok,yes,ja,approved,freigabe,👍,✅,lgtm
> ```

> [!TIP]
> **help wanted-Issues in Gitea erkennen:**
> ```
> Gitea → Issues → Filter: Label = "help wanted"
> → Zeigt alle Issues die menschliche Entscheidung brauchen
> ```

---

### Warnung

> [!WARNING]
> **"help wanted" entfernen ohne "ok" zu kommentieren:**
> ```
> Label entfernt, aber kein Freigabe-Kommentar
> → check_approval gibt False zurück
> → --implement schlägt fehl
> ```
> → Erst Label entfernen, dann "ok" kommentieren

> [!WARNING]
> **"ok" kommentieren ohne "help wanted" zu entfernen:**
> ```
> Kommentar "ok" vorhanden, aber Label noch aktiv
> → check_approval gibt False zurück (Label blockiert)
> ```
> → `help wanted` Label muss manuell entfernt werden

> [!WARNING]
> **Night-Modus und help wanted:**
> ```
> Night-Modus implementiert KEINE Issues autonom.
> help wanted-Issues werden nur als Auto-Issues erstellt (nicht implementiert).
> ```

---

### Nächste Schritte

✅ Labels und Workflow verstanden
→ [05 — Standard-Workflow](05-issue-to-pr.md)
→ [16 — Night vs Patch Modus](16-night-vs-patch.md)
→ [26 — .env-Konfiguration](26-env-configuration.md)
