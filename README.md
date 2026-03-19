# gitea-agent

LLM-agnostischer Agent-Workflow für Gitea Issues.

Verbindet einen LLM-Agenten (Claude Code, Gemini, lokales LLM, …) mit dem Gitea Issue-Tracker: Issue analysieren → Plan posten → Freigabe einholen → Branch + Implementierung → PR erstellen.

---

## Kernproblem & Lösungsansätze

### Das Problem: Wie triggert der Agent?

Ein LLM kann nicht eigenständig auf ein laufendes Terminal reagieren. Das Script `agent_start.py` gibt strukturierten Output aus — aber *wer liest ihn?*

Drei Ansätze, Stand 2026:

| Ansatz | Autonomie | Voraussetzung | Status |
|--------|-----------|---------------|--------|
| **A — Claude API** | ✅ Vollständig | `ANTHROPIC_API_KEY` in `.env` | Im Script vorbereitet, deaktiviert |
| **B — `\| llm` CLI** | ✅ Vollständig | `pip install llm` + API-Key | Extern, kein Script-Eingriff nötig |
| **C — Zed/Chat-Session** | ⚠️ Halb-manuell | Aktive Claude Code Session | Aktueller Standard |

### Ansatz A — Claude API (vorbereitet, noch deaktiviert)

```bash
# .env:
CLAUDE_API_ENABLED=true
ANTHROPIC_API_KEY=sk-ant-...

# Dann läuft alles autonom:
python3 agent_start.py
```

Das Script ruft intern `anthropic.Anthropic().messages.create()` auf — analysiert Code, generiert Plan, implementiert.

### Ansatz B — LLM CLI Pipe

```bash
python3 agent_start.py | llm "führe die ==CLAUDE-ACTION== aus"
```

Funktioniert mit beliebigem LLM CLI (`llm` von Simon Willison, `ollama`, etc.). Das LLM erhält den strukturierten Output als Kontext. Aber: Das LLM kann *nur Text antworten* — keine Datei-Edits, keine Git-Commits. Daher für reine Plananalyse geeignet, nicht für Implementierung.

### Ansatz C — Zed/Claude Code Session (aktueller Standard)

```
Du:    "prüf Issues" / "starte Agent" / "run agent_start.py"
Claude: führt python3 agent_start.py via Bash-Tool aus
Claude: liest Output → erkennt ==CLAUDE-ACTION== → implementiert direkt
```

**Warum kein Auto-Trigger?**
Es gibt keine Möglichkeit vom Terminal direkt in eine Chat-Session zu schreiben. Kein Socket, kein Webhook, kein Pipe führt in den Chat. Die Session ist eine geschlossene UI — von außen nicht beschreibbar.

**Minimaler Trigger-Aufwand:**
```bash
# Terminal:
python3 agent_start.py
# → sieht ==CLAUDE-ACTION: IMPLEMENT== im Output
# → kopiert den Block in den Chat
# Claude: startet sofort ohne weitere Eingabe
```

---

## Workflow-Diagramm

```
Du:     Issue auf "ready-for-agent" setzen
        ↓
Script: Scannt Gitea → analysiert Code per AST
        ↓
        ┌─ Stufe 1 (Docs/Cleanup) ──────────────────────────────────┐
        │  Plan wird automatisch generiert + sofort gepostet        │
        └───────────────────────────────────────────────────────────┘
        ┌─ Stufe 2+ (Bug/Feature) ──────────────────────────────────┐
        │  Plan-Draft erstellt → LLM befüllt → --post-plan <NR>    │
        └───────────────────────────────────────────────────────────┘
        ↓
Du:     "ok" in Gitea kommentieren
        ↓
Script: Erkennt Freigabe → Branch erstellen → Label: in-progress
        ↓
Script: Postet in Issue: "🤖 Agent aktiv — Implementierung gestartet"
        ↓
Script: Gibt ==CLAUDE-ACTION: IMPLEMENT== aus (maschinenlesbar)
        ↓
LLM:    Liest Output → implementiert → committet nach jeder Datei
        ↓
Script: --pr <NR> --branch <branch> --summary "..."
        ↓
        ┌─ PR erstellt ─────────────────────────────────────────────┐
        │  Abschluss-Kommentar ins Issue + Label: needs-review      │
        └───────────────────────────────────────────────────────────┘
        ↓
Du:     PR reviewen + mergen
```

---

## Installation

```bash
git clone http://your-gitea/gitea-agent
cd gitea-agent
cp .env.example .env
# .env befüllen (GITEA_URL, GITEA_USER, GITEA_TOKEN, GITEA_REPO)
```

Keine zusätzlichen Abhängigkeiten — nur Python 3.10+ Stdlib.
Optional für Ansatz A: `pip install anthropic`

---

## Konfiguration

`.env` Datei im Projektverzeichnis:

| Variable | Beschreibung | Beispiel |
|----------|-------------|---------|
| `GITEA_URL` | Gitea-Instanz URL | `http://192.168.1.x:3001` |
| `GITEA_USER` | Gitea-Benutzername | `admin` |
| `GITEA_TOKEN` | API-Token (Settings → Applications) | `abc123...` |
| `GITEA_REPO` | Repository (owner/name) | `admin/myproject` |
| `GITEA_BOT_USER` | Bot-User für Kommentare (optional) | `working-bot` |
| `GITEA_BOT_TOKEN` | API-Token des Bot-Users (optional) | `xyz789...` |
| `PROJECT_ROOT` | Pfad zum Projekt-Repo | `/home/user/myproject` |
| `MODEL` | LLM-Modellname (für Metadaten) | `claude-sonnet-4-6` |
| `CLAUDE_API_ENABLED` | Claude API aktivieren | `false` |
| `ANTHROPIC_API_KEY` | Claude API-Key | `sk-ant-...` |

**Token-Scopes:** `issue` (read+write), `repository` (read+write)

**Bot-User (empfohlen):** Separater Gitea-User (`working-bot`) damit Agent-Kommentare klar als Bot erkennbar sind. Nur API-Token nötig — kein SSH/GPG.

---

## Verwendung

```bash
# Auto-Modus (empfohlen)
python3 agent_start.py

# Manuell:
python3 agent_start.py --list                              # Status-Übersicht
python3 agent_start.py --issue 16                          # Analysieren + Draft
python3 agent_start.py --post-plan 16                      # Befüllten Plan posten
python3 agent_start.py --implement 16                      # Nach "ok": Branch
python3 agent_start.py --pr 16 --branch fix/issue-16-xyz  # PR erstellen
python3 agent_start.py --pr 16 --branch fix/issue-16-xyz \
  --summary "- X geändert\n- Doku aktualisiert"           # PR mit Zusammenfassung
```

---

## ==CLAUDE-ACTION== Block

Der Script gibt maschinenlesbaren Output aus wenn ein LLM aktiv sein soll:

```
==CLAUDE-ACTION: IMPLEMENT==
ISSUE=21
BRANCH=docs/issue-21-...
FILES=/home/user/project/nanoclaw/fact_extractor.py
PR_CMD=python3 agent_start.py --pr 21 --branch ... --summary "..."
==END-CLAUDE-ACTION==
```

```
==CLAUDE-ACTION: NONE==
==END-CLAUDE-ACTION==
```

LLMs/Scripts können diesen Block parsen und entsprechend reagieren — unabhängig vom Rest des Outputs.

---

## Labels

| Label | Bedeutung |
|-------|-----------|
| `ready-for-agent` | Issue bereit zur Bearbeitung |
| `agent-proposed` | Plan gepostet, wartet auf Freigabe |
| `in-progress` | Agent implementiert |
| `needs-review` | PR erstellt, wartet auf Review |

---

## Risiko-Klassifikation

| Stufe | Beschreibung | Plan-Generierung | Vorgehen |
|-------|-------------|-----------------|---------|
| 1 | Docs, Cleanup | Automatisch per AST | Sofort posten |
| 2 | Enhancements | Draft → LLM befüllt | Manuell posten |
| 3 | Bugs, Features | Draft → LLM befüllt | Freigabe + Plan |
| 4 | Breaking Changes | Nicht automatisiert | Nur manuell |

---

## Sicherheitsregeln

- **Commit-as-Checkpoint:** Nach jeder Datei sofort committen (LLM-Timeout-Schutz)
- **Kein Auto-Merge:** PR erstellt, Mensch entscheidet
- **Kein Auto-Push auf main:** Agent arbeitet immer auf Feature-Branch
- **Freigabe-Pflicht:** `--implement` nur nach `ok`/`ja`/`✅` in Gitea

---

## Dateistruktur

```
gitea-agent/
├── agent_start.py   # CLI + Workflow-Logik + Claude API Stub
├── gitea_api.py     # Gitea REST API Wrapper
├── .env.example     # Konfigurationsvorlage
├── .env             # Secrets (nicht im Git!)
└── README.md
```

---

## Offene Fragen / Roadmap

- **Claude API aktivieren** wenn API-Key vorhanden → vollständige Autonomie
- **Webhook-Integration:** Gitea Event bei `ready-for-agent` → direkt Agent triggern
- **Multi-Repo:** eine Agent-Instanz für mehrere Repos (`.env` per Repo)
- **Google Gemini:** `GEMINI_API_KEY` analog zu Claude API einbauen
