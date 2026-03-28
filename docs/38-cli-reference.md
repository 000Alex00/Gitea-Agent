## CLI-Referenz (Alle Flags)

Vollständige Kommandozeilen-Übersicht.

---

### Voraussetzungen

> [!IMPORTANT]
> - Agent installiert ([Rezept 01](01-installation.md))

---

### Problem

Du willst alle verfügbaren CLI-Flags kennen.

---

### Lösung

```bash
cd ~/Gitea-Agent
python3 agent_start.py --help
```

---

### CLI-Flags

#### **Projekt-Steuerung**

| Flag | Argument | Beschreibung |
|------|----------|--------------|
| `--project` | `<path>` | Projekt-Pfad (absolut oder relativ) |
| `--self` | - | Dual-Repo-Modus: Agent + Projekt getrennt ([Rezept 07](07-multiple-repos.md)) |

#### **Issue/PR-Workflow**

| Flag | Argument | Beschreibung |
|------|----------|--------------|
| `--issue` | `<number>` | Issue-Nummer bearbeiten |
| `--branch` | `<name>` | Branch-Name für PR |
| `--pr` | `<number>` | PR erstellen (mit --branch) — 10 Hard-Gates vorher ([Rezept 46](46-technical-enforcement.md)) |
| `--review` | `<pr_nr>` | LLM analysiert PR-Diff, postet Findings als Kommentar (erfordert LLM) |
| `--summary` | `<text>` | PR-/Commit-Summary |
| `--fixup` | - | Bugfix-Workflow: Git-Commit → Issue-Comment ([Rezept 06](06-bugfix-on-branch.md)) |
| `--list` | - | Zeige alle offenen Issues |

#### **Watch-Modus**

| Flag | Argument | Beschreibung |
|------|----------|--------------|
| `--watch` | - | Endlos-Loop: Scanne Issues alle X Sekunden |
| `--eval-interval` | `<seconds>` | Intervall zwischen Eval-Läufen (Standard: 3600) |
| `--watch-interval` | `<seconds>` | Intervall zwischen Issue-Scans (Standard: 300) |
| ~~`--night-mode`~~ | - | Nicht als CLI-Flag vorhanden — Night-Modus läuft via systemd (`gitea-agent-night.service`, [Rezept 16](16-night-vs-patch.md)) |

#### **Eval/Testing**

| Flag | Argument | Beschreibung |
|------|----------|--------------|
| `--eval` | - | Nur Eval-Lauf (keine Issue-Bearbeitung) |
| `--update-baseline` | - | Baseline auf aktuellen Score setzen ([Rezept 11](11-baseline-management.md)) |
| `--generate-tests` | `<nr>` | LLM generiert Tests für Issue ([Rezept 13](13-test-generation.md)) |
| `--heal` | `[test_name]` | Self-Healing Loop: fehlgeschlagene Tests autonom fixen ([Rezept 44](44-self-healing.md)) |

#### **Code-Analyse**

| Flag | Argument | Beschreibung |
|------|----------|--------------|
| `--build-skeleton` | - | AST-Skeleton generieren ([Rezept 20](20-ast-skeleton.md)) |
| `--get-slice` | `<file>:<symbol>` | Code-Segment extrahieren ([Rezept 21](21-codesegment-strategy.md)) |
| `--get-llm-cmd` | `<task>` | cli_cmd für Task aus routing.json ausgeben (für context_export.sh --llm) |
| `--apply-patch` | `<file>` | Patch-Datei anwenden ([Rezept 23](23-search-replace-patches.md)) |

#### **Systemd/Service**

| Flag | Argument | Beschreibung |
|------|----------|--------------|
| `--install-service` | `night\|patch` | Systemd-Service installieren ([Rezept 15](15-watch-mode-systemd.md)) |

#### **Einrichtung & Konfiguration**

| Flag | Argument | Beschreibung |
|------|----------|--------------|
| `--setup` | - | Interaktiver Einrichtungs-Wizard (9 Schritte): Gitea-Verbindung, Repo, Labels, Eval, .env, Projekttyp, LLM, Prompts |
| `--llm` | - | LLM-Konfiguration verwalten: Provider/Modell wechseln, per-Task Routing, Fallback-Kette, Konnektivitätstest |
| `--doctor` | - | Health-Check: 7 Checks inkl. LLM-Config-Guard ([Rezept 04](04-health-check.md)) |

#### **Konfiguration**

| Flag | Argument | Beschreibung |
|------|----------|--------------|
| `--env-file` | `<path>` | Custom .env-Datei (Standard: `.env`) |
| `--config` | `<path>` | Custom agent_eval.json |
| `--label-config` | `<path>` | Custom labels.json ([Rezept 28](28-labels-and-workflow.md)) |
| `--exclude-config` | `<path>` | Custom excludes.json ([Rezept 29](29-context-excludes.md)) |
| `--use-gitignore` | - | .gitignore für Excludes nutzen |

#### **Dashboard**

| Flag | Argument | Beschreibung |
|------|----------|--------------|
| `--dashboard-enabled` | - | HTML-Dashboard generieren ([Rezept 30](30-dashboard-customization.md)) |

#### **Debugging**

| Flag | Argument | Beschreibung |
|------|----------|--------------|
| `--verbose` | - | Detaillierte Logs |
| `--debug` | - | Noch mehr Logs (HTTP-Bodies) |
| `--dry-run` | - | Simulation ohne Änderungen |

#### **LLM-Config-Guard**

| Befehl | Beschreibung |
|--------|--------------|
| `python3 plugins/llm_config_guard.py` | Prüft alle IDE-Config-Dateien |
| `python3 plugins/llm_config_guard.py --repair` | Repariert veraltete IDE-Configs |
| `python3 plugins/llm_config_guard.py --create` | Erstellt fehlende IDE-Config-Dateien |
| `python3 plugins/llm_config_guard.py --verbose` | Detaillierte Ausgabe |

---

### Beispiele

```bash
# ══════════════════════════════════════════════════════════
# Basis-Workflow
# ══════════════════════════════════════════════════════════
python3 agent_start.py --project ~/proj --issue 42 --branch fix/typo

# ══════════════════════════════════════════════════════════
# Watch-Modus (Night)
# ══════════════════════════════════════════════════════════
python3 agent_start.py --project ~/proj --install-service night
# → installiert gitea-agent-night.service (NIGHT_MODE=true, nur risk≤2)
systemctl --user start gitea-agent-night

# ══════════════════════════════════════════════════════════
# Eval-Only
# ══════════════════════════════════════════════════════════
python3 agent_start.py --project ~/proj --eval

# ══════════════════════════════════════════════════════════
# Dual-Repo
# ══════════════════════════════════════════════════════════
python3 agent_start.py --self --issue 77

# ══════════════════════════════════════════════════════════
# Skeleton + Slice
# ══════════════════════════════════════════════════════════
python3 agent_start.py --project ~/proj --build-skeleton
python3 agent_start.py --project ~/proj --get-slice src/api.py:ChatAPI

# ══════════════════════════════════════════════════════════
# Systemd-Service
# ══════════════════════════════════════════════════════════
sudo python3 agent_start.py --project ~/proj --install-service night

# ══════════════════════════════════════════════════════════
# Health-Check
# ══════════════════════════════════════════════════════════
python3 agent_start.py --project ~/proj --doctor

# ══════════════════════════════════════════════════════════
# Einrichtung & LLM-Konfiguration
# ══════════════════════════════════════════════════════════
python3 agent_start.py --setup          # Ersteinrichtung (9 Schritte)
python3 agent_start.py --llm            # LLM nachträglich konfigurieren
python3 agent_start.py --doctor         # Health-Check

# ══════════════════════════════════════════════════════════
# PR-Review (erfordert LLM)
# ══════════════════════════════════════════════════════════
python3 agent_start.py --review 7       # PR #7 analysieren, Findings als Kommentar posten

# ══════════════════════════════════════════════════════════
# Self-Healing (erfordert LLM)
# ══════════════════════════════════════════════════════════
python3 agent_start.py --heal           # Alle fehlgeschlagenen Tests fixen
python3 agent_start.py --heal test_chat # Nur Test "test_chat" fixen
```

---

### Nächste Schritte

✅ CLI-Flags kennen  
→ [39 — API-Functions](39-api-functions.md)  
→ [40 — Best Practices](40-best-practices.md)
