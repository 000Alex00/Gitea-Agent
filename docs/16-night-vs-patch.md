## Night-Modus vs. Patch-Modus

Wann welchen Workflow nutzen?

---

### Voraussetzungen

> [!IMPORTANT]
> - Watch-Modus verstanden ([Rezept 14](14-watch-mode-tmux.md) oder [15](15-watch-mode-systemd.md))
> - Issues haben Risk-Level Labels

> [!WARNING]
> **Night-Modus und Patch-Modus erfordern ein LLM-API-Backend.**
> Der Agent läuft ohne menschliche Interaktion — er muss Issues selbstständig analysieren und implementieren.
> Ohne konfiguriertes LLM-Backend (`CLAUDE_API_ENABLED=true` oder `config/llm/routing.json`) startet der Watch-Loop zwar, kann aber keine Issues bearbeiten.
>
> **Manueller Workflow ohne API:** `--issue` + `context_export.sh` → Kontext manuell in Web-Chat einfügen → Agent postet PR via `--pr`. Kein API-Backend nötig.

---

### Problem

Du willst nachts nur sichere Änderungen, tagsüber aggressive Bugfixes. Unklar welche Flags/Modi wann sinnvoll sind.

---

### Lösung

```bash
# ══════════════════════════════════════════════════════════
# NIGHT-MODUS — Sichere, nächtliche Automatisierung
# (läuft als systemd-Service, nicht als CLI-Flag)
# ══════════════════════════════════════════════════════════
python3 agent_start.py --project ~/mein-projekt --install-service night
systemctl --user start gitea-agent-night

# Verhalten:
# ✓ Nur Issues mit Label: agent:low-risk
# ✓ Eval-Lauf alle 4 Stunden
# ✓ PR erstellt ohne Merge (Review nächsten Morgen)
# ✓ Consecutive-Pass-Gate: 3 Durchläufe (konservativ)
# ✓ Erfordert LLM-API (CLAUDE_API_ENABLED=true oder routing.json)

# ══════════════════════════════════════════════════════════
# PATCH-MODUS — Schnelle, aggressive Bugfixes
# ══════════════════════════════════════════════════════════
python3 agent_start.py \
  --project ~/mein-projekt \
  --watch \
  --eval-interval 300
  
# Verhalten:
# ✓ Alle Issues (low/medium/high-risk)
# ✓ Eval-Lauf alle 5 Minuten
# ✓ Consecutive-Pass-Gate: 2 Durchläufe (Standard)
# ✓ Du bist am Rechner → sofortiges Feedback

# ══════════════════════════════════════════════════════════
# HYBRID — Beide Modi parallel (systemd)
# ══════════════════════════════════════════════════════════
# Night: 23:00-07:00
sudo python3 agent_start.py \
  --project ~/mein-projekt \
  --install-service night

# Patch: 09:00-18:00
sudo python3 agent_start.py \
  --project ~/mein-projekt \
  --install-service patch \
  --watch-interval 600

# Zeitsteuerung via systemd-Timer:
sudo systemctl edit --full gitea-agent-night.timer
```

---

### Erklärung

**Night-Modus Details:**

| Setting | Wert | Grund |
|---------|------|-------|
| Issue-Filter | `agent:low-risk` | Keine Breaking Changes |
| Eval-Interval | 4 Stunden | Niedrige Last, lange Inferenz-Zeit OK |
| Consecutive-Passes | 3 | Extra-Sicherheit vor Auto-Close |
| Auto-Merge | ❌ Disabled | Manuelle Review am Morgen |
| Labels | `agent:night-run` | Nachvollziehbarkeit |
| **Auto-Context-Build** | ✅ Aktiv | Nach Auto-Issue: `workspace/open/{N}-*/starter.md` sofort erstellt |

> [!TIP]
> **Auto-Context-Build:** Nach jeder automatischen Issue-Erstellung (Score-Regression, Performance) baut der Agent sofort `workspace/open/{N}-*/starter.md` und `files.md`. Morgens ist der Kontext fertig — der LLM kann direkt loslegen.

**Patch-Modus Details:**

| Setting | Wert | Grund |
|---------|------|-------|
| Issue-Filter | Alle (oder `agent:patch`) | Auch riskante Fixes |
| Eval-Interval | 5-10 Minuten | Schnelles Feedback |
| Consecutive-Passes | 2 | Standard-Gate |
| Auto-Merge | Optional | Mit `--auto-merge` möglich |
| Labels | `agent:patch-run` | Differenzierung zu Night |

**Wann was nutzen:**

```
┌─────────────────────────────────────────────────────────┐
│ NIGHT-MODUS                                            │
├─────────────────────────────────────────────────────────┤
│ ✓ Du schläfst / nicht am Rechner                      │
│ ✓ Repo ist produktiv / kritisch                       │
│ ✓ Issues: Refactorings, Doku, Tests                   │
│ ✓ Ziel: Morgens 3-5 PRs zur Review                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ PATCH-MODUS                                            │
├─────────────────────────────────────────────────────────┤
│ ✓ Du arbeitest aktiv am Projekt                       │
│ ✓ Repo ist Entwicklungs-Branch                        │
│ ✓ Issues: Bugfixes, Features, Breaking Changes        │
│ ✓ Ziel: Sofortiges Feedback, schnelle Iteration       │
└─────────────────────────────────────────────────────────┘
```

---

### Best Practice

> [!TIP]
> **Labels für Modi:**
> ```
> agent:low-risk → Night-Modus
> agent:high-risk → Patch-Modus (mit manueller Überwachung)
> agent:manual → Nie automatisch
> ```

> [!TIP]
> **Zeitfenster in systemd:**
> ```ini
> # /etc/systemd/system/gitea-agent-night.timer
> [Unit]
> Description=Gitea Agent Night Timer
> 
> [Timer]
> OnCalendar=23:00
> Persistent=true
> 
> [Install]
> WantedBy=timers.target
> ```

> [!TIP]
> **Hybrid-Konfiguration:**
> ```bash
> # .env
> NIGHT_MODE_START=23:00
> NIGHT_MODE_END=07:00
> PATCH_MODE_INTERVAL=300
> NIGHT_MODE_INTERVAL=14400
> ```

---

### Warnung

> [!WARNING]
> **Night-Modus ohne low-risk Labels:**
> ```
> Alle Issues haben default-Label
> → --night-mode filtert nichts
> → Agent arbeitet wie Patch-Modus
> ```
> → Labels konsequent vergeben

> [!WARNING]
> **Parallele Modi konkurrieren:**
> ```
> Night-Service: Issue #42 wird bearbeitet
> Patch-Service: Issue #42 wird AUCH bearbeitet
> → Konflikte im Branch
> ```
> → Nutze Issue-Locks oder verschiedene Labels

> [!WARNING]
> **Zu kurze Eval-Intervalle:**
> ```
> --eval-interval 60  (1 Minute)
> → Server hat keine Zeit für Cooldown
> → False-Positives bei Load-Tests
> ```
> → Minimum: 5 Minuten

---

### Nächste Schritte

✅ Modi verstanden  
→ [17 — Consecutive-Pass-Gate](17-consecutive-pass-gate.md)  
→ [28 — Labels und Workflow](28-labels-and-workflow.md)  
→ [40 — Best Practices](40-best-practices.md)
