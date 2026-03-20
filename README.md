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

Der Agent führt vor dem PR-Erstellen automatisch das Eval-System aus — **nur bei Risiko ≥ 2** (Docs-PRs sind bewusst ausgenommen, da sie kein Verhalten ändern):

| Risiko | Eval |
|---|---|
| 1 — Docs/Cleanup | Übersprungen |
| 2 — Enhancement | ✅ läuft |
| 3 — Bug/Feature | ✅ läuft |

| Ergebnis | Verhalten |
|---|---|
| Kein `agent_eval.json` | Übersprungen — PR wird normal erstellt |
| server offline | Warnung — PR wird trotzdem erstellt |
| Eval-Fehler (Bug in evaluation.py) | Warnung ins Issue — PR wird trotzdem erstellt |
| PASS (score >= baseline) | PR wird erstellt |
| FAIL (score < baseline) | PR blockiert, Kommentar ins Issue |

Danach:
- postet einen Abschluss-Kommentar ins Issue
- setzt das Label auf `needs-review`

---

### 7. Review und Merge

PR in Gitea reviewen → mergen → Issue schließen. Fertig.

---

## Eval-System

`evaluation.py` prüft vor jedem PR ob das Zielprojekt noch korrekt funktioniert. Schlägt ein Test fehl, wird der PR blockiert.

### Voraussetzung

Im Zielprojekt muss eine `tests/agent_eval.json` existieren:

```json
{
  "server_url": "http://192.168.1.x:8000",
  "chat_endpoint": "/chat",
  "pi5_url": "http://192.168.1.x:1235",
  "tests": [
    {
      "name": "Routing einfach",
      "weight": 1,
      "pi5_required": false,
      "message": "Was ist 2 plus 2?",
      "expected_keywords": ["4"]
    },
    {
      "name": "Stilles Failure",
      "weight": 2,
      "pi5_required": true,
      "steps": [
        {"message": "Mein Name ist Max", "expect_stored": true},
        {"message": "Wie heiße ich?", "expected_keywords": ["Max"]}
      ]
    }
  ]
}
```

### Felder

| Feld | Beschreibung |
|---|---|
| `server_url` | URL des zu testenden Servers |
| `chat_endpoint` | HTTP-POST Endpunkt — wird aus dem Zielprojekt gelesen, nicht hardcodiert |
| `pi5_url` | Optionaler Backend-Worker — wird vorab auf Erreichbarkeit geprüft |
| `watch_interval_minutes` | Interval für `--watch` in Minuten (Standard: 60) — wird von `--interval` CLI-Arg überschrieben |
| `log_path` | Pfad zur Logdatei — von `--watch` für Inaktivitätserkennung (Szenario 2) genutzt |
| `restart_script` | Pfad zum Start-Skript — Watch startet Server automatisch neu bei Inaktivität + neuen Commits |
| `inactivity_minutes` | Schwellwert für Chat-Inaktivität in Minuten, ab dem Neustart getriggert wird (Standard: 5) |
| `log_analysis_interval_minutes` | Interval für Log-Analyse in Watch-Zyklen (projektspezifisch) |
| `weight` | Gewichtung im Score (1–3) |
| `pi5_required` | Bei `true`: Test wird übersprungen wenn Pi5 offline |
| `message` | Nachricht an den Server |
| `expected_keywords` | Alle Keywords müssen in der Antwort enthalten sein (case-insensitive). Leer `[]` = nur Antwort vorhanden prüfen |
| `expect_stored` | `true` = Antwort darf `null` sein — prüft nur ob Server nicht abstürzt (z.B. beim Einschreiben von Fakten) |
| `steps` | Mehrschrittige Tests: Schritte werden sequenziell mit derselben User-ID ausgeführt, alle müssen bestehen. Zwischen Steps wird 2s gewartet (LLM-Cooldown) |

### Score-Berechnung

Gewichtetes Binär — kein LLM-Judgement:
- Test bestanden → `weight` Punkte
- Test nicht bestanden → 0 Punkte
- `max_score` = Summe aller Gewichte

### Baseline

`tests/baseline.json` enthält den Referenz-Score. Regeln:
- Erster Lauf → Baseline wird automatisch angelegt
- Score ≥ Baseline → PR erlaubt
- Score < Baseline → PR blockiert
- Score > Baseline → Baseline wird **automatisch hochgesetzt** (nie runter)
- `--update-baseline` → manuelle Neusetzung (z.B. nach bewusstem Score-Wechsel durch neuen Test)

`baseline.json` sollte in `.gitignore` stehen — maschinenspezifisch, nicht versionieren.

### Score-History

Jeder Eval-Lauf wird in `tests/score_history.json` protokolliert (max. 90 Einträge). Ältere Einträge werden automatisch verworfen. Feld `trigger` zeigt den Auslöser:

| trigger | Auslöser |
|---|---|
| `pr` | Vor einem PR (`--pr`) |
| `watch` | Watch-Modus (`--watch`) |
| `restart` | Nach Neustart (`--eval-after-restart`) |
| `manual` | Manueller Aufruf (`evaluation.py` direkt) |

Die letzten 5 Einträge werden automatisch an jeden `--pr` Gitea-Kommentar und an jeden Auto-Issue aus dem Watch-Modus angehängt.

`score_history.json` sollte in `.gitignore` stehen — maschinenspezifisch, nicht versionieren.

### Verhalten bei Infrastruktur-Problemen

| Situation | Verhalten |
|---|---|
| `server_url` offline | Warnung — Eval übersprungen, PR wird trotzdem erstellt |
| `pi5_url` offline | Pi5-Tests übersprungen, Rest läuft durch |
| Score < Baseline | PR blockiert + Kommentar ins Issue |
| Kein `agent_eval.json` | Eval übersprungen |
| Fehler in `evaluation.py` | Warnung ins Issue — PR wird trotzdem erstellt |

### Baseline verwalten

```bash
# Manuell testen ohne PR
python3 evaluation.py --project /path/to/project

# Baseline neu setzen (nur nach bewusstem Score-Wechsel, z.B. neuer Test hinzugefügt)
python3 evaluation.py --project /path/to/project --update-baseline
```

### Watch-Modus

`--watch` startet eine periodische Eval-Schleife:

```bash
python3 agent_start.py --watch               # Interval aus agent_eval.json oder 60 min
python3 agent_start.py --watch --interval 30 # explizit 30 Minuten (überschreibt Config)
```

**Empfohlen:** Interval in `agent_eval.json` konfigurieren:
```json
{
  "watch_interval_minutes": 60,
  "log_path": "/home/user/mein-projekt/logs/system.log",
  "restart_script": "/home/user/mein-projekt/start_assistant.sh",
  "inactivity_minutes": 5
}
```

Priorität: `--interval` CLI-Arg > `watch_interval_minutes` in `agent_eval.json` > Fallback 60 min.

**Was passiert pro Zyklus:**
- Score ≥ Baseline → kein Issue, nur Log
- Score < Baseline → Gitea Issue mit Label `bug` wird erstellt (Titel: `[Auto] <test-name>`)
- Deduplication: kein Duplikat wenn Issue mit gleichem Titel bereits offen
- Test besteht wieder → Issue wird automatisch geschlossen
- Jedes Auto-Issue enthält die letzten 5 History-Einträge im Body
- Wenn `tools/log_analyzer.py` im Zielprojekt vorhanden → wird automatisch ausgeführt + Ausgabe ins Terminal

**Szenario 2 — automatischer Neustart:**

Pro Zyklus wird zusätzlich geprüft ob ein Neustart notwendig ist:
1. Chat inaktiv seit ≥ `inactivity_minutes` (aus `log_path` gelesen)
2. Neue Commits seit letztem Eval (git log vs. score_history.json)

→ Wenn beide Bedingungen: `restart_script` starten + sofort Eval

Konfiguration in `agent_eval.json`:
```json
{
  "restart_script": "/home/user/mein-projekt/start_assistant.sh",
  "inactivity_minutes": 5
}
```

**tmux empfohlen** für Dauerbetrieb:
```bash
tmux new -s watch
python3 agent_start.py --watch
# Ctrl+B, D zum Detachen
```

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
python3 agent_start.py --pr 16 --branch fix/... --force   # Staleness-Check überspringen
python3 agent_start.py --pr 16 --branch fix/... \
  --restart-before-eval                                    # Server neu starten, dann Eval

# Watch-Modus (periodische Eval-Überwachung):
python3 agent_start.py --watch                             # alle 60 Minuten (Standard)
python3 agent_start.py --watch --interval 30               # alle 30 Minuten
python3 agent_start.py --eval-after-restart                # Eval nach Neustart (ohne Issue-Kommentar)
python3 agent_start.py --eval-after-restart 61             # Eval nach Neustart + Score in Issue #61
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

## Prozess-Enforcement

Technische Schranken die Kontext-Drift verhindern — kein LLM kann sie umgehen:

### `_check_pr_preconditions()` — vor jedem PR

`--pr` prüft automatisch vor der PR-Erstellung:

| Prüfung | Fehlermeldung |
|---|---|
| Branch ≠ main/master | `Branch ist 'main' — PR von main verboten` |
| Plan-Kommentar vorhanden | `Kein Plan-Kommentar im Issue gefunden` |
| Agent-Metadaten-Block im Plan | `Plan-Kommentar ohne Metadata-Block` |
| Eval nach letztem Commit ausgeführt | `Eval nicht ausgeführt seit letztem Commit` |

Bei Fehler: `SystemExit(1)` — PR wird nicht erstellt.

### Server-Aktualitäts-Check (`_check_server_staleness()`)

`--pr` prüft zusätzlich ob der laufende Server den aktuellen Branch-Code hat:

1. Letzter Commit-Timestamp via `git log -1 --pretty=%cI`
2. Server-Start-Zeitpunkt aus `log_path` (aus `agent_eval.json`) — sucht rückwärts nach Startup-Mustern
3. Commit neuer als Server-Start → Warnung + `SystemExit(1)`

**Ausgabe bei veraltetem Server:**
```
[!] Server-Code veraltet
    Letzter Commit: 2026-03-20 22:45 (fix/issue-38-...)
    Server gestartet: 2026-03-20 21:20

    → Server neu starten, dann erneut --pr aufrufen.
      Oder: --restart-before-eval (automatisch) / --force (überspringen)
```

**Flags:**

| Flag | Verhalten |
|---|---|
| *(kein Flag)* | Warnung + Exit 1 wenn Server veraltet |
| `--force` | Staleness-Check überspringen — Eval läuft trotzdem |
| `--restart-before-eval` | `restart_script` aus `agent_eval.json` starten + warten, dann Eval |

**Voraussetzung:** `log_path` in `agent_eval.json` konfiguriert + Server schreibt Startup-Message ins Log.
Fehlt `log_path` oder ist Startup nicht parsebar → Check wird silent übersprungen (rückwärtskompatibel).

### Agent-Metadaten-Block

Jeder Plan-Kommentar und Abschluss-Kommentar enthält einen `<details>`-Block:

```
<details>
<summary>🤖 Agent-Metadaten</summary>

**Modell:** claude-sonnet-4-6
**Branch:** fix/issue-61-...
**Commit:** abc1234
**Zeitstempel:** 2026-03-20T14:23:00
**Token-Schätzung:** ~4200 (Kontext: files.md, starter.md)
**Gelesene Dateien:** nanoclaw/server.py, nanoclaw/router.py
</details>
```

### Session-Tracking

`contexts/session.json` zählt abgeschlossene Issues pro Claude-Session:

- `SESSION_LIMIT` (Standard: 2) → Warnung bei Überschreitung (Drift-Risiko)
- `SESSION_RESET_HOURS` (Standard: 4) → session.json wird nach Inaktivität zurückgesetzt
- Status (🟢/🟡/🔴) erscheint im Abschluss-Kommentar jedes PR

### PFLICHTREGELN in starter.md

Jede starter.md enthält automatisch einen PFLICHTREGELN-Block:
- NIEMALS `curl` statt `agent_start.py` verwenden
- NIEMALS Schritte überspringen
- NIEMALS PR manuell erstellen
- Selbst-Check-Checkliste vor jedem Schritt

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
├── evaluation.py       # Eval-System: liest tests/agent_eval.json, HTTP-Tests gegen server
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
