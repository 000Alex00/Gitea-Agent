# gitea-agent

LLM-agnostischer Agent-Workflow für Gitea Issues.

Verbindet einen LLM-Agenten (Claude Code, Gemini, lokales LLM, …) mit dem Gitea Issue-Tracker:
Issue analysieren → Plan posten → Freigabe einholen → Branch + Implementierung → PR erstellen.

---

## Schnellstart

```bash
git clone http://your-gitea/gitea-agent
cd gitea-agent
cp .env.example .env
# .env befüllen (GITEA_URL, GITEA_USER, GITEA_TOKEN, GITEA_REPO)
python3 agent_start.py
```

Keine zusätzlichen Abhängigkeiten — nur Python 3.10+ Stdlib.

---

## Schritt-für-Schritt Anleitung

### 1. Issue schreiben

In Gitea ein neues Issue anlegen. Im Body die betroffenen Dateien in Backticks erwähnen — der Agent erkennt sie automatisch:

```
Bitte Docstrings in `nanoclaw/fact_extractor.py` ergänzen.
```

---

### 2. Label setzen: `ready-for-agent`

Das Label signalisiert dem Agent, dass das Issue bearbeitet werden soll.

Gitea → Issue → Labels → `ready-for-agent` setzen.

---

### 3. Agent starten

Im Terminal (im `gitea-agent`-Verzeichnis):

```bash
python3 agent_start.py
```

Der Agent scannt alle Issues und verarbeitet sie der Reihe nach:

**Konsolenausgabe (Beispiel):**
```
======================================================================
  GITEA AGENT — AUTO-SCAN
======================================================================

[→] 1 Issue(s) bereit — poste Pläne:

  → #21 (Stufe 1) Docstrings in fact_extractor.py ergänzen

[✓] Kommentar gepostet: http://gitea/repo/issues/21
[→] Freigabe: mit 'ok' oder 'ja' kommentieren
```

In Gitea erscheint jetzt automatisch ein Kommentar mit dem Implementierungsplan.

---

### 4. Plan prüfen und freigeben

Gitea → Issue → Kommentar des Agents lesen → mit `ok`, `ja` oder `✅` antworten.

---

### 5. Implementierung starten

Erneut im Terminal:

```bash
python3 agent_start.py
```

Der Agent erkennt die Freigabe und gibt aus:

```
[✓] Freigabe erhalten — starte Implementierung.
[✓] Branch 'docs/issue-21-...' erstellt.
```

**In der Claude Code Chat-Session** (oder beliebigem LLM) eintippen:

```
prüf Issues / starte Agent / run agent_start.py
```

Claude führt das Script über sein Bash-Tool aus, liest den Output und startet die Implementierung — ohne weiteren manuellen Eingriff.

---

### 6. PR wird automatisch erstellt

Nach der Implementierung:

```bash
python3 agent_start.py --pr 21 --branch docs/issue-21-xyz --summary "- Docstrings ergänzt"
```

Der Agent:
- erstellt den PR in Gitea
- postet einen Abschluss-Kommentar ins Issue
- setzt das Label auf `needs-review`

---

### 7. Review und Merge

PR in Gitea reviewen → mergen → Issue schließen. Fertig.

---

## Workflow-Diagramm

```
Du:     Issue schreiben + Label "ready-for-agent" setzen
        ↓
Script: Plan-Kommentar ins Issue (mit 🤖 Metadaten-Block: Zeitstempel, Tokens, Dateien)
        contexts/{N}-{typ}/starter.md erstellt → Label: agent-proposed
        ↓ (Stufe 2/3 zusätzlich — wenn noch kein Plan vorhanden:)
Script: Analyse-Kommentar + Nächste Schritte ins Issue
        Label "help wanted" gesetzt, "agent-proposed" entfernt
        ↓
Du:     Fragen im Issue beantworten
        python3 agent_start.py --issue {N}  → starter.md mit Kommentarhistorie aktualisiert
        [Wiederholen bis Konzept steht]
        Label "help wanted" manuell entfernen → "ok" kommentieren
        ↓
Script: Freigabe erkannt (help wanted weg + ok) → Branch erstellen
        Label: agent-proposed → in-progress
        Nächste Schritte ins Issue gepostet
        contexts/{N}-{typ}/files.md erstellt
        ↓
LLM:    Liest starter.md + files.md → implementiert → committet
        ↓
Script: --pr <NR> --branch <branch> --summary "..."
        ↓
        PR erstellt + Abschluss-Kommentar + Label: needs-review
        contexts/{N}-{typ}/ → contexts/done/{N}-{typ}/
        ↓
Du:     PR reviewen + mergen
```

---

## Installation & Konfiguration

### .env befüllen

```bash
cp .env.example .env
```

| Variable | Beschreibung | Beispiel |
|----------|-------------|---------|
| `GITEA_URL` | Gitea-Instanz URL | `http://192.168.1.x:3001` |
| `GITEA_USER` | Gitea-Benutzername | `admin` |
| `GITEA_TOKEN` | API-Token (Settings → Applications) | `abc123...` |
| `GITEA_REPO` | Repository (owner/name) | `admin/myproject` |
| `GITEA_BOT_USER` | Bot-User für Kommentare (optional) | `working-bot` |
| `GITEA_BOT_TOKEN` | API-Token des Bot-Users (optional) | `xyz789...` |
| `PROJECT_ROOT` | Pfad zum Projekt-Repo | `/home/user/myproject` |
| `CLAUDE_API_ENABLED` | Claude API aktivieren | `false` |
| `ANTHROPIC_API_KEY` | Claude API-Key | `sk-ant-...` |

**Token-Scopes:** `issue` (read+write), `repository` (read+write)

**Bot-User (empfohlen):** Separater Gitea-User (`working-bot`) damit Agent-Kommentare klar als Bot erkennbar sind. Nur API-Token nötig — kein SSH/GPG.

### Textbausteine anpassen

Alle Texte (Plan-Platzhalter, PR-Checkliste, Freigabe-Prompt, Abschluss-Text) sind in `settings.py` zentralisiert und über `.env` überschreibbar. Details: [settings.py](settings.py) und [.env.example](.env.example).

---

## Verwendung

```bash
# Auto-Modus (empfohlen)
python3 agent_start.py

# Manuell:
python3 agent_start.py --list                              # Status-Übersicht
python3 agent_start.py --issue 16                          # Plan posten
python3 agent_start.py --implement 16                      # Nach "ok": Branch
python3 agent_start.py --fixup 16                          # Nach Bugfix: Kommentar + needs-review
python3 agent_start.py --pr 16 --branch fix/issue-16-xyz  # PR erstellen
python3 agent_start.py --pr 16 --branch fix/issue-16-xyz \
  --summary "- X geändert\n- Doku aktualisiert"           # PR mit Zusammenfassung
```

---

## Labels

| Label | Bedeutung |
|-------|-----------|
| `ready-for-agent` | Issue bereit zur Bearbeitung |
| `agent-proposed` | Plan gepostet, wartet auf Freigabe |
| `help wanted` | Stufe 2/3: offene Fragen offen — `agent-proposed` wird entfernt bis Konzept steht |
| `in-progress` | Agent implementiert |
| `needs-review` | PR erstellt, wartet auf Review |

---

## Risiko-Klassifikation

Der Agent stuft jedes Issue automatisch ein:

| Stufe | Beschreibung | Vorgehen |
|-------|-------------|---------|
| 1 | Docs, Cleanup | Plan gepostet → Freigabe → Implementierung |
| 2 | Enhancements | Plan + Analyse-Kommentar → `help wanted` → Freigabe → Implementierung |
| 3 | Bugs, Features | Plan + Analyse-Kommentar → `help wanted` → Freigabe → Implementierung |
| 4 | Breaking Changes | Nicht automatisiert — nur manuell |

**Stufe 2/3:** Der Agent postet Plan-Kommentar + Analyse-Kommentar mit offenen Fragen (Seiteneffekte, betroffene Module, Konfiguration). Label wird zu `help wanted` — `agent-proposed` wird entfernt (Plan noch nicht freigegeben). Erst nach Beantwortung, `help wanted` manuell entfernen und `ok`-Kommentar startet die Implementierung.

**Bugfix-Workflow:** Issue nach Test auf `in-progress` zurücksetzen → fix committen → `--fixup <NR>` → postet Commit-Message als Kommentar + setzt `needs-review`.

**Docs-Check:** `--pr` prüft automatisch ob `Documentation/` seit Abzweig von main geändert wurde. Warnung im Terminal + Gitea-Kommentar wenn nicht. Abschluss-Kommentar enthält immer Revert-Hinweis.

**Auto-Cleanup:** Beim Start verschiebt der Agent automatisch Kontext-Ordner geschlossener Issues nach `contexts/done/`.

---

## Sicherheitsregeln

- **Commit-as-Checkpoint:** Nach jeder Datei sofort committen (Schutz bei LLM-Timeout)
- **Kein Auto-Merge:** PR erstellt, Mensch entscheidet
- **Kein Auto-Push auf main:** Agent arbeitet immer auf Feature-Branch
- **Freigabe-Pflicht:** `--implement` nur nach `ok`/`ja`/`✅` in Gitea

---

## Dateistruktur

```
gitea-agent/
├── agent_start.py      # CLI + Workflow-Logik
├── gitea_api.py        # Gitea REST API Wrapper
├── settings.py         # Alle konfigurierbaren Werte (Labels, Texte, Limits)
├── log.py              # Logging-Konfiguration (Console + File)
├── .env.example        # Konfigurationsvorlage
├── .env                # Secrets (nicht im Git!)
├── contexts/           # Kontext-Dateien pro Issue (auto-erstellt)
│   ├── 21-docs/        # Ein Unterordner pro Issue: {num}-{typ}
│   │   ├── starter.md  # Metadaten, Plan, Checkliste, Kommentarhistorie
│   │   ├── files.md    # Quellcode (max MAX_FILE_LINES pro Datei)
│   │   └── plan.md     # Plan-Draft (Stufe 2/3, lokal befüllen)
│   └── done/           # Nach PR: ganzer Ordner wird hierher verschoben
│       └── 21-docs/
└── README.md
```

**Typen** (aus Gitea-Label): `bug`, `feature_request`, `enhancement`, `docs`, `task`

---

## Optimierungsansätze / Roadmap

### LLM-Anbindung

Der Agent gibt strukturierten Output aus — wer ihn verarbeitet ist austauschbar:

| Ansatz | Autonomie | Voraussetzung |
|--------|-----------|---------------|
| **Claude Code Session** | Halb-manuell (Trigger-Satz im Chat) | Aktive Session |
| **Claude API** | Vollständig autonom | `ANTHROPIC_API_KEY` in `.env` |
| **`\| llm` CLI** | Text-only (kein Datei-Edit) | `pip install llm` + API-Key |

Claude API ist im Script vorbereitet (`CLAUDE_API_ENABLED=true`) — sobald ein Key vorhanden ist, läuft alles vollständig autonom.

### Weitere Ideen

- **Webhook-Integration:** Gitea Event bei `ready-for-agent` → Agent direkt triggern (kein manueller Aufruf)
- **Multi-Repo:** Eine Agent-Instanz für mehrere Repos (`.env` per Repo)
- **Google Gemini:** `GEMINI_API_KEY` analog zu Claude API einbauen
- **Stufe-1 Auto-Implement:** Docs/Cleanup ohne Freigabe direkt implementieren (opt-in via `.env`)
