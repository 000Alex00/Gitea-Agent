# Dateien — Issue #11

## README.md
```
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
  "server_url": "http://192.168.1.179:8000",
  "chat_endpoint": "/chat",
  "pi5_url": "http://192.168.1.148:1235",
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
| `log_path` | Optionaler Pfad zur Logdatei für `--watch` Inaktivitätserkennung |
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
  "watch_interval_minutes": 60
}
```

Priorität: `--interval` CLI-Arg > `watch_interval_minutes` in `agent_eval.json` > Fallback 60 min.

Verhalten:
- Score ≥ Baseline → kein Issue, nur Log
- Score < Baseline → Gitea Issue mit Label `bug` wird erstellt (Titel: `[Auto] <test-name>`)
- Deduplication: kein Duplikat wenn Issue mit gleichem Titel bereits offen
- Test besteht wieder → Issue wird automatisch geschlossen
- Jedes Auto-Issue enthält die letzten 5 History-Einträge im Body

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

[... gekürzt — 148 Zeilen weggelassen ...]
```

## Documentation/COOKBOOK.md
```
# gitea-agent COOKBOOK

Schritt-für-Schritt-Rezepte für häufige Aufgaben.
Referenzprojekt: Skynet (LLM WhatsApp-Bot, Jetson Nano + Raspberry Pi 5).

---

## Inhaltsverzeichnis

1. [Agent auf neues Projekt portieren](#1-agent-auf-neues-projekt-portieren)
2. [Standard-Workflow: Issue → PR](#2-standard-workflow-issue--pr)
3. [Bugfix auf in-progress Issue (--fixup)](#3-bugfix-auf-in-progress-issue---fixup)
4. [Ersten Test schreiben (agent_eval.json)](#4-ersten-test-schreiben-agent_evaljson)
5. [Mehrstufigen Test schreiben (steps)](#5-mehrstufigen-test-schreiben-steps)
6. [Eval-Baseline neu setzen](#6-eval-baseline-neu-setzen)
7. [Watch-Modus einrichten (tmux + Dauerbetrieb)](#7-watch-modus-einrichten-tmux--dauerbetrieb)
8. [Systemd-Timer: Eval nach Nachtsync](#8-systemd-timer-eval-nach-nachtsync)
9. [Eval nach Neustart (--eval-after-restart)](#9-eval-nach-neustart---eval-after-restart)
10. [Auto-Issue manuell schließen](#10-auto-issue-manuell-schließen)

---

## 1. Agent auf neues Projekt portieren

**Kontext:** Du willst den gitea-agent für ein neues Projekt nutzen.

**Dateien:** `.env`, `tests/agent_eval.json` (im Zielprojekt)

**Schritte:**

```bash
# 1. gitea-agent klonen (oder bestehende Kopie verwenden)
git clone http://192.168.1.60:3001/Alexmistrator/gitea-agent
cd gitea-agent

# 2. .env befüllen
cp .env.example .env
```

```ini
# .env — Werte anpassen (NICHT committen)
GITEA_URL=http://192.168.1.60:3001
GITEA_USER=dein-username
GITEA_TOKEN=abc123xxxxxxxxxxxxx   # Gitea → Settings → Applications → Token
GITEA_REPO=username/mein-projekt
PROJECT_ROOT=/home/user/mein-projekt
```

```bash
# 3. Labels in Gitea anlegen
# Gitea → Repo → Issues → Labels → folgende erstellen:
#   ready-for-agent   (grün)
#   agent-proposed    (blau)
#   in-progress       (gelb)
#   needs-review      (orange)

# 4. Ersten Testlauf
python3 agent_start.py --list
```

**Pitfalls:**
- `PROJECT_ROOT` muss absoluter Pfad zum Zielprojekt sein — nicht zum gitea-agent-Verzeichnis
- Token braucht Scopes: `issue` (read+write) + `repository` (read+write)
- Labels müssen exakt so heißen wie in `settings.py → LABEL_*`

---

## 2. Standard-Workflow: Issue → PR

**Kontext:** Normaler Entwicklungszyklus für ein neues Feature oder einen Bug.

**Dateien:** `agent_start.py`, Gitea Issue

**Schritte:**

```bash
# Schritt 1: Issue schreiben
# In Gitea: Neue Issue → Body mit betroffenen Dateien in Backticks:
# "Bitte Timeout in `nanoclaw/plugins/web_search.py` auf 8s setzen."
# Label: ready-for-agent

# Schritt 2: Plan generieren
python3 agent_start.py --issue 61

# → Postet Plan-Kommentar ins Issue
# → Label: ready-for-agent → agent-proposed
# → Gibt contexts/open/61-bug/starter.md aus

# Schritt 3: Plan freigeben
# In Gitea: Issue → Kommentar: "ok"

# Schritt 4: Implementierung starten
python3 agent_start.py --implement 61

# → Erstellt Branch: fix/issue-61-...
# → Label: agent-proposed → in-progress
# [LLM implementiert Code, committed]

# Schritt 5: PR erstellen (nach Implementierung)
python3 agent_start.py --pr 61 --branch fix/issue-61-web-search-timeout \
  --summary "DDGS.text() blockierte asyncio — run_in_executor + wait_for(8s)"

# → Eval läuft automatisch (Risiko ≥ 2)
# → Bei PASS: PR erstellt, Abschluss-Kommentar, Label: needs-review
# → Bei FAIL: PR blockiert, Kommentar ins Issue
```

**Pitfalls:**
- `--branch` muss exakt dem Branch-Namen entsprechen (`git branch` zeigt aktuellen)
- `--summary` weglassen → Warnung im Kommentar (nicht blockierend)

---

## 3. Bugfix auf in-progress Issue (--fixup)

**Kontext:** Du hast einen Commit auf einem in-progress Branch gemacht und willst den Reviewer benachrichtigen.

**Dateien:** `agent_start.py`

**Schritte:**

```bash
# Commit gemacht, jetzt Kommentar ins Issue:
git add nanoclaw/plugins/web_search.py
git commit -m "fix: DDGS run_in_executor + wait_for(8s) (closes #61)"

python3 agent_start.py --fixup 61

# → Liest letzten Commit automatisch aus git log
# → Postet Bugfix-Kommentar mit Commit-SHA ins Issue
# → Label: in-progress → needs-review
```

**Pitfalls:**
- `--fixup` liest `git log -1` — immer erst committen, dann aufrufen
- Label-Wechsel passiert automatisch, kein manueller Schritt nötig

---

## 4. Ersten Test schreiben (agent_eval.json)

**Kontext:** Du willst das Verhalten deines Servers absichern.

**Dateien:** `tests/agent_eval.json` (im Zielprojekt)

**Schritte:**

```bash
mkdir -p /home/user/mein-projekt/tests
```

```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "watch_interval_minutes": 60,
  "tests": [
    {
      "name": "Einfache Antwort",
      "weight": 1,
      "pi5_required": false,
      "message": "Was ist 2 plus 2?",
      "expected_keywords": ["4"]
    },
    {
      "name": "Server antwortet",
      "weight": 1,
      "pi5_required": false,
      "message": "Hallo",
      "expected_keywords": []
    }
  ]
}
```

```bash
# Ersten Lauf — Baseline wird automatisch angelegt
python3 evaluation.py --project /home/user/mein-projekt
# → Schreibt tests/baseline.json mit aktuellem Score
```

**Pitfalls:**
- `expected_keywords: []` = nur prüfen ob Server antwortet (kein Keyword-Check)
- `weight` beeinflusst wie stark ein FAIL die Baseline unterschreitet
- Baseline-Datei nicht versionieren (maschinenspezifisch)

---

## 5. Mehrstufigen Test schreiben (steps)

**Kontext:** Du willst Kontext-Persistenz testen — z.B. ob etwas gespeichert und später abrufbar ist.

**Referenz:** Skynet-Projekt, ChromaDB-Kontext-Test

**Dateien:** `tests/agent_eval.json`

```json
{
  "server_url": "http://192.168.1.179:8000",
  "chat_endpoint": "/chat",
  "pi5_url": "http://192.168.1.148:1235",
  "watch_interval_minutes": 60,
  "log_path": "/home/user/mein-projekt/logs/system.log",
  "tests": [
    {
      "name": "Routing einfach",
      "weight": 1,
      "pi5_required": false,
      "message": "Was ist 2 plus 2?",
      "expected_keywords": ["4"]
    },
    {
      "name": "Kontext-Persistenz",
      "weight": 2,
      "pi5_required": true,
      "steps": [
        {
          "message": "Mein Name ist TestUser",
          "expect_stored": true
        },
        {
          "message": "Wie heiße ich?",
          "expected_keywords": ["TestUser"]
        }
      ]
    },
    {
      "name": "Stilles Failure",
      "weight": 2,
      "pi5_required": true,
      "steps": [
        {
          "message": "Mein Lieblingstier ist ein Pinguin",
          "expect_stored": true
        },
        {
          "message": "Was ist mein Lieblingstier?",
          "expected_keywords": ["Pinguin"]
        }
      ]
    },
    {
      "name": "Web Search",
      "weight": 1,
      "pi5_required": true,
      "message": "Was gibt es aktuell Neues?",
      "expected_keywords": []
    }
  ]
}
```

**Erklärung:**
- `steps`: sequenzielle Schritte mit derselben User-ID (verhindert Kontext-Bleeding zwischen Tests)
- `expect_stored: true`: Antwort darf leer sein — prüft nur ob der Server nicht abstürzt (Schreib-Schritt)
- `pi5_required: true`: Test wird übersprungen wenn Backend-Worker offline (kein FAIL)
- Zwischen Steps: 2s Wartezeit (LLM-Cooldown)

**Pitfalls:**
- Jeder Lauf bekommt eine neue `eval-XXXXXXXX` User-ID → kein Bleeding zwischen Läufen
- `pi5_url` fehlt → `pi5_required: true` Tests laufen trotzdem (werden nicht als offline erkannt)

---

## 6. Eval-Baseline neu setzen

**Kontext:** Du hast bewusst einen neuen Test hinzugefügt oder ein Feature entfernt — die alte Baseline passt nicht mehr.

**Dateien:** `tests/baseline.json`, `evaluation.py`

**Schritte:**

```bash
# Aktuellen Score anzeigen (ohne Baseline zu ändern)
python3 evaluation.py --project /home/user/mein-projekt

# Neue Baseline setzen (nur wenn du weißt was du tust)
python3 evaluation.py --project /home/user/mein-projekt --update-baseline

# Prüfen was gesetzt wurde
cat /home/user/mein-projekt/tests/baseline.json
# → {"score": 7.0}
```

**Wann neu setzen:**
- Neuer Test hinzugefügt → Score steigt → Baseline automatisch erhöht (kein manueller Schritt nötig)
- Test entfernt → Score sinkt → manuell neu setzen
- Hardware-Umbau → neue Infrastruktur hat anderen Basis-Score

**Pitfalls:**
- Baseline auto-erhöht sich bei `score > baseline` — nie runter (außer manuell)
- `--update-baseline` schreibt sofort — kein Bestätigungsprompt

---

## 7. Watch-Modus einrichten (tmux + Dauerbetrieb)

**Kontext:** Kontinuierliche Überwachung im Hintergrund, Auto-Issues bei Score-Verlust.

**Dateien:** `agent_start.py`, `tests/agent_eval.json`

[... gekürzt — 179 Zeilen weggelassen ...]
```
