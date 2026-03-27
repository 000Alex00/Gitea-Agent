## Night-Modus vs. Patch-Modus

Wann welchen Workflow nutzen?

---

### Voraussetzungen

> [!IMPORTANT]
> - Watch-Modus verstanden ([Rezept 14](14-watch-mode-tmux.md) oder [15](15-watch-mode-systemd.md))

> [!NOTE]
> **Beide Modi laufen als Eval-Loop** — sie implementieren keine Issues selbstständig.
> Sie erkennen Regressions, erstellen automatisch Issues dafür und bauen den Kontext vor.
> Die eigentliche Implementierung erfolgt manuell (Mensch + `context_export.sh`) oder mit `--heal` (LLM-API nötig).

---

### Problem

Du willst nachts nur sichere Fehler-Issues erstellen, tagsüber auch riskante. Unklar welche Flags wann sinnvoll sind.

---

### Lösung

```bash
# ══════════════════════════════════════════════════════════
# NIGHT-MODUS — Konservativer Eval-Loop über Nacht
# Flag: --watch --night
# systemd: gitea-agent-night.service
# ══════════════════════════════════════════════════════════
python3 agent_start.py --project ~/mein-projekt --install-service night
systemctl --user start gitea-agent-night

# Verhalten:
# ✓ Eval-Loop läuft periodisch
# ✓ Auto-Issues nur für Regressions mit Risiko ≤ NIGHT_MAX_RISK (Standard: 1)
#   → Score-Verlust (Risiko 3): wird NICHT als Issue erstellt
#   → Performance-Regression (Risiko 2): nur wenn NIGHT_MAX_RISK ≥ 2
# ✓ Auto-Context-Build: starter.md + files.md werden sofort gebaut
# ✓ Auto-Issues + Tag-Aggregation aktiv
# ✗ Kein Server-Neustart bei Inaktivität

# Risikostufen anpassen (default: 1 = nur Docs/Cleanup):
# NIGHT_MAX_RISK=2  → auch Performance-Regressions als Issue erstellen

# ══════════════════════════════════════════════════════════
# PATCH-MODUS — Aktiver Eval-Loop bei laufender Arbeit
# Flag: --watch --patch
# systemd: gitea-agent-patch.service
# ══════════════════════════════════════════════════════════
python3 agent_start.py --project ~/mein-projekt --install-service patch

# Verhalten:
# ✓ Eval-Loop läuft periodisch
# ✓ Server-Neustart wenn Chat inaktiv + neue Commits vorhanden
# ✗ Keine Auto-Issues (du bist am Rechner, siehst Eval direkt)
# ✗ Keine Tag-Aggregation

# ══════════════════════════════════════════════════════════
# HYBRID — Beide Services parallel (systemd)
# ══════════════════════════════════════════════════════════
python3 agent_start.py --project ~/mein-projekt --install-service night
python3 agent_start.py --project ~/mein-projekt --install-service patch

# Zeitsteuerung via systemd-Timer (23:00-07:00 night, 09:00-18:00 patch):
systemctl --user edit --full gitea-agent-night.timer
```

---

### Erklärung

**Was macht der Watch-Loop wirklich?**

```
Watch-Loop (alle N Minuten):
  1. Eval ausführen
  2. Bei Fehler:
     Night-Modus: Auto-Issue erstellen (wenn Risiko ≤ NIGHT_MAX_RISK)
     Patch-Modus: Kein Auto-Issue (du siehst es direkt im Terminal)
  3. Dashboard aktualisieren
  4. Skeleton inkrementell aktualisieren
  5. Log-Analyzer ausführen (falls konfiguriert)
  6. Self-Healing (falls healing=true in project.json + LLM-API)
```

**Night-Modus Details:**

| Setting | Wert | Grund |
|---------|------|-------|
| Flag | `--watch --night` | Risiko-gefilterter Eval-Loop |
| Auto-Issues | Nur Risiko ≤ `NIGHT_MAX_RISK` | Keine Breaking-Change-Issues über Nacht |
| `NIGHT_MAX_RISK` | 1 (Standard) | Nur Docs/Cleanup-Regressions |
| Auto-Context-Build | ✅ Aktiv | Morgens ist Kontext fertig |
| Server-Neustart | ❌ Nicht aktiv | Niemand da zum Überwachen |
| Tag-Aggregation | ✅ Aktiv | Systematische Fehler erkenne |

**Patch-Modus Details:**

| Setting | Wert | Grund |
|---------|------|-------|
| Flag | `--watch --patch` | Aktiver Eval-Loop |
| Auto-Issues | ❌ Deaktiviert | Entwickler sieht Eval direkt |
| Server-Neustart | ✅ Bei Inaktivität + Commits | Schnelle Iteration |
| Tag-Aggregation | ❌ Deaktiviert | Kein Rauschen im Terminal |

**Wann was nutzen:**

```
┌─────────────────────────────────────────────────────────┐
│ NIGHT-MODUS  (--watch --night)                         │
├─────────────────────────────────────────────────────────┤
│ ✓ Du schläfst / nicht am Rechner                      │
│ ✓ Morgens: Auto-Issues mit fertigem Kontext warten    │
│ ✓ Nur sichere Regressions werden als Issue erstellt   │
│ ✓ Keine manuelle Überwachung nötig                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ PATCH-MODUS  (--watch --patch)                         │
├─────────────────────────────────────────────────────────┤
│ ✓ Du arbeitest aktiv am Projekt                       │
│ ✓ Server wird automatisch neugestartet bei Commits    │
│ ✓ Kein Issue-Spam — du siehst Fehler direkt           │
│ ✓ Schnelle Feedback-Schleife                          │
└─────────────────────────────────────────────────────────┘
```

---

### Best Practice

> [!TIP]
> **NIGHT_MAX_RISK konfigurieren:**
> ```bash
> # .env
> NIGHT_MAX_RISK=1   # nur Docs/Cleanup (Standard)
> NIGHT_MAX_RISK=2   # auch Performance-Regressions
> # Score-Verlust (Risiko 3) wird nie im Night-Modus als Issue erstellt
> ```

> [!TIP]
> **Zeitfenster in systemd:**
> ```ini
> # ~/.config/systemd/user/gitea-agent-night.timer
> [Timer]
> OnCalendar=23:00
> Persistent=true
> ```

---

### Warnung

> [!WARNING]
> **Watch-Loop implementiert keine Issues selbstständig.**
> Er erkennt Regressions und erstellt Issues — die Implementierung bleibt Aufgabe des Menschen
> oder von `--heal` (erfordert LLM-API + `healing=true` in `config/project.json`).

> [!WARNING]
> **Parallele Services konkurrieren beim Eval:**
> ```
> Night: Eval läuft gerade
> Patch: Eval startet gleichzeitig
> → Konflikte in score_history.json
> ```
> → Services über systemd-Timer zeitlich trennen.

> [!WARNING]
> **Zu kurze Eval-Intervalle:**
> ```
> --interval 1  (1 Minute)
> → Server hat keine Zeit für Cooldown
> → False-Positives bei Last-Tests
> ```
> → Minimum: 5 Minuten

---

### Nächste Schritte

✅ Modi verstanden
→ [17 — Consecutive-Pass-Gate](17-consecutive-pass-gate.md)
→ [26 — .env Konfiguration (NIGHT_MAX_RISK)](26-env-configuration.md)
→ [40 — Best Practices](40-best-practices.md)
