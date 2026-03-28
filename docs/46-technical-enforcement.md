## Technische Schranken — 9-Stufen-Precondition-Check

Codebasierte Schranken blockieren fehlerhafte oder unsichere Aktionen **hart** —
unabhängig vom LLM-Kontext, Prompt-Inhalt oder Context-Drift.

---

### Voraussetzungen

> [!IMPORTANT]
> - gitea-agent eingerichtet ([Rezept 02](02-first-setup.md))
> - System-Prompts verstanden ([Rezept 43](43-system-prompts.md))

---

### Problem

System-Prompts sind die erste Verteidigungslinie — aber LLMs können durch
Context-Drift, Jailbreaks oder manipulierte Issue-Inhalte beeinflusst werden.
Ohne codebasierte Schranken sind Prompt-Regeln kein verlässlicher Schutz.

---

### Lösung: Zwei-Schichten-Modell

```
┌──────────────────────────────────────────────────────────┐
│  Schicht 1: System-Prompts (config/llm/prompts/)         │
│  → Rollen, Schranken-Sektion, Pflicht-Format             │
│  → Weich — durch Context-Drift theoretisch umgehbar      │
├──────────────────────────────────────────────────────────┤
│  Schicht 2: Code-Enforcement (agent_start.py)            │
│  → _check_pr_preconditions() — 9 Hard-Gates vor --pr     │
│  → SystemExit(1) bei Verstoß — keine Ausnahmen           │
│  → Unabhängig von LLM-Ausgabe                            │
├──────────────────────────────────────────────────────────┤
│  Schicht 3: llm_config_guard.py (pre-commit)             │
│  → Prüft IDE-Konfigurationsdateien auf Pflichtinhalte    │
│  → Blockiert Commits bei fehlenden Schranken             │
└──────────────────────────────────────────────────────────┘
```

---

### Die 9 Hard-Gates (`_check_pr_preconditions`)

Jeder `--pr`-Aufruf durchläuft automatisch alle 9 Prüfungen. Schlägt eine fehl,
wird der PR **abgebrochen** — kein Merge möglich.

#### Gate 1 — Branch ≠ main/master

```
❌ Branch ist 'main'/'master' — PR von main verboten
```

Direkt-Push auf `main` ist strukturell ausgeschlossen. Nie per Prompt konfigurierbar.

#### Gate 2 — Plan-Kommentar vorhanden

```
❌ Kein Plan-Kommentar im Issue gefunden (cmd_plan ausgeführt?)
```

Das Issue muss einen Agent-Plan mit `Implementierungsplan` oder `Agent-Analyse` enthalten.
Ohne vorherige Analyse kein PR.

#### Gate 3 — Metadata-Block im Plan

```
❌ Plan-Kommentar ohne Metadata-Block (cmd_plan neu ausführen)
```

Der Plan-Kommentar muss `Agent-Metadaten` enthalten (Token-Count, Modell, Dateien).
Stellt sicher dass der Plan mit dem aktuellen Agenten-Stand erstellt wurde.

#### Gate 4 — Eval nach letztem Commit

```
❌ Eval nicht nach letztem Commit ausgeführt
   (letzter Eval: 2026-03-28T10:00, letzter Commit: 2026-03-28T11:30)
```

Timestamps werden verglichen: `score_history.json` vs. `git log -1 --pretty=%cI`.
Veraltete Testergebnisse blockieren den PR.

#### Gate 5 — Server-Neustart vor PR

```
❌ Server-Neustart empfohlen vor PR
   → Lösung: --restart-before-eval beim PR-Aufruf verwenden
   ⚠️ Manuelle Neustarts erforderlich: payment-service
```

Wenn `services` oder `restart_script` in `agent_eval.json` konfiguriert sind,
wird geprüft ob ein Neustart seit dem letzten Commit erfolgte.

#### Gate 6 — Self-Consistency-Check

```
❌ Agent Self-Consistency Check fehlgeschlagen (siehe Logs)
```

Wenn `agent_start.py`, `settings.py` oder `gitea_api.py` im Branch geändert wurden,
läuft automatisch `agent_self_check.py`. Schlägt er fehl, kein PR.

#### Gate 7 — Diff-Validierung (Out-of-Scope-Warnung)

```
⚠️ Geänderte Dateien außerhalb des Issue-Scope (repo_skeleton.json)
```

Geänderte Zeilen werden gegen `repo_skeleton.json` geprüft.
Änderungen außerhalb des Issue-Themas erzeugen eine Warnung (kein Hard-Block, aber sichtbar).

#### Gate 8 — Slice-Gate

```
❌ Slice-Gate aktiv: 200+ Zeilen-Dateien ohne --get-slice geändert
```

Wenn `SLICE_GATE_ENABLED=true` in `.env`: Dateien über `SLICE_GATE_MIN_LINES` Zeilen,
die ohne vorherigen `--get-slice`-Abruf geändert wurden, blockieren den PR.
**Verhindert halluzinierte Patches** auf nicht gelesenen Dateien.

#### Gate 9 — Branch auf Remote vorhanden

```
❌ Branch 'feat/issue-42' nicht auf Remote — erst pushen:
   git push origin feat/issue-42
```

Verhindert PRs auf nicht gepushte Branches (Merge würde fehlschlagen).

#### Gate 10 — Agent Policies

```
❌ Policy-Verstoß: 450 geänderte Zeilen > max_diff_lines (300)
❌ Policy-Verstoß: forbidden_path 'config/secrets' betroffen: config/secrets/prod.yaml
❌ Policy-Verstoß: Dateien außerhalb allowed_paths geändert: legacy/old_api.py
```

Konfigurierbare Regeln in `agent_eval.json` → `"policies"` Block:

```json
{
  "policies": {
    "max_diff_lines": 300,
    "allowed_paths": ["src/", "tests/"],
    "forbidden_paths": ["config/secrets", ".env", "credentials"]
  }
}
```

| Policy | Typ | Beschreibung |
|--------|-----|--------------|
| `max_diff_lines` | Integer | Maximale geänderte Zeilen im Branch-Diff |
| `allowed_paths` | Liste | Nur Änderungen in diesen Pfaden erlaubt |
| `forbidden_paths` | Liste | Diese Pfade dürfen nie geändert werden |

Policies sind optional — kein `"policies"`-Block = kein Check.

---

### Zusammenfassung aller Gates

| # | Prüfung | Auswirkung |
|---|---------|------------|
| 1 | Branch ≠ main/master | Hard-Block |
| 2 | Plan-Kommentar vorhanden | Hard-Block |
| 3 | Metadata im Plan | Hard-Block |
| 4 | Eval nach letztem Commit | Hard-Block |
| 5 | Server-Neustart (wenn Services konfiguriert) | Hard-Block |
| 6 | Self-Consistency bei Agent-Code-Änderung | Hard-Block |
| 7 | Diff-Scope vs. Issue | Warnung |
| 8 | Slice-Gate (wenn `SLICE_GATE_ENABLED=true`) | Hard-Block |
| 9 | Branch auf Remote | Hard-Block |
| 10 | Agent Policies (wenn `policies` in agent_eval.json) | Hard-Block |

---

### Schicht 3 — `llm_config_guard.py` (pre-commit)

```bash
# Manuell prüfen
python3 agent_start.py --guard

# Kaputte IDE-Config reparieren
python3 agent_start.py --guard --repair
```

Geprüfte Dateien:

| Datei | Tool |
|-------|------|
| `CLAUDE.md` | Claude Code |
| `.cursorrules` | Cursor |
| `.clinerules` | Cline |
| `copilot-instructions.md` | GitHub Copilot |
| `windsurfrules` | Windsurf |
| `GEMINI.md` | Gemini CLI |
| `AGENTS.md` | OpenAI Agents |

Pre-commit-Integration: `plugins/llm_config_guard.py` läuft automatisch bei jedem Commit
und blockiert wenn Pflichtinhalte (Unveränderliche Schranken, CLAUDE.md-Struktur) fehlen.

---

### Best Practice

> [!TIP]
> **Gates sind nicht deaktivierbar per Prompt:**
> ```
> # Kein LLM-Output kann --pr ohne bestandene Gates erzwingen
> # SystemExit(1) kommt vor jedem API-Call
> ```
> → Schranken gelten auch für autonome `--watch`/`--heal`-Loops

> [!TIP]
> **Slice-Gate gezielt aktivieren:**
> ```bash
> # .env
> SLICE_GATE_ENABLED=true
> SLICE_GATE_MIN_LINES=150
> ```
> → Empfohlen für große Repos mit vielen langen Dateien

> [!TIP]
> **Gate 7 (Diff-Scope) beobachten:**
> ```
> ⚠️ 3 Dateien außerhalb des Issue-Scope geändert
> ```
> → Kein Hard-Block, aber Signal für schleichenden Feature-Creep

---

### Warnung

> [!WARNING]
> **Gate 4 erfordert aktuelle `score_history.json`:**
> Wenn `agent_eval.json` existiert aber noch nie Eval gelaufen ist, blockiert Gate 4
> jeden PR bis `python3 agent_start.py --eval` einmal erfolgreich war.

> [!WARNING]
> **Slice-Gate schützt nicht vor absichtlichen Umgehungen:**
> Ein Mensch kann Dateien manuell editieren ohne `--get-slice`. Gate 8 ist für
> autonome LLM-Workflows gedacht, nicht für menschliche Entwickler.

---

### Nächste Schritte

✅ Technische Schranken verstanden
→ [43 — System-Prompts](43-system-prompts.md) — Erste Schranken-Schicht: Rollen-Prompts
→ [26 — .env-Konfiguration](26-env-configuration.md#slice-gate) — Slice-Gate konfigurieren
→ [41 — Security-Guide](41-security-guide.md) — Vollständige Sicherheitsübersicht
→ [44 — Self-Healing](44-self-healing.md) — Gates gelten auch im Healing-Loop
