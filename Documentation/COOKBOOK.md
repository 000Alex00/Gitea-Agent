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
11. [log_analyzer integrieren](#11-log_analyzer-integrieren)
12. [LLM-Workflow — Welches LLM, welcher Befehl](#12-llm-workflow--welches-llm-welcher-befehl)
13. [Zwei Repos — Ein Agent](#13-zwei-repos--ein-agent)
14. [PR mit veraltetem Server (Staleness-Check)](#14-pr-mit-veraltetem-server-staleness-check)
15. [Migration auf zentrale Agent-Instanz](#15-migration-auf-zentrale-agent-instanz)
16. [LLM-gestützte Test-Generierung (--generate-tests)](#16-llm-gestützte-test-generierung---generate-tests)
17. [Systematische Fehler-Erkennung (Tag-Aggregation)](#17-systematische-fehler-erkennung-tag-aggregation)
18. [Patch-Modus & Live-Dashboard](#18-patch-modus--live-dashboard)
19. [Consecutive-Pass Gate für Auto-Issues](#19-consecutive-pass-gate-für-auto-issues)
20. [Betriebsmodi — Night / Patch / Idle](#20-betriebsmodi--night--patch--idle)
21. [Setup-Wizard (Issue #77)](#21-setup-wizard-issue-77)
22. [Plugin-Architektur: patch + changelog (Issue #79)](#22-plugin-architektur-patch--changelog-issue-79)
23. [AST-Repository-Skelett (#68)](#23-ast-repository-skelett-68)
24. [Diff-Validierung (#57)](#24-diff-validierung-57)
25. [SEARCH/REPLACE Protokoll (#58)](#25-searchreplace-protokoll-58)
26. [Flächendeckende Codesegment-Strategie (#72)](#26-flächendeckende-codesegment-strategie-72)
27. [Gitea-Versionsvergleich (#59)](#27-gitea-versionsvergleich-59)
28. [Vollständige Funktionsreferenz](#28-vollständige-funktionsreferenz)
29. [Best Practices](#29-best-practices)
30. [Troubleshooting](#30-troubleshooting)
31. [Erweiterungsmöglichkeiten](#31-erweiterungsmöglichkeiten)
32. [Sicherheitshinweise](#32-sicherheitshinweise)

---

## 1. Agent auf neues Projekt portieren

**Architektur:** gitea-agent wird **einmalig installiert** und bleibt dauerhaft bestehen. Für jedes neue Projekt reicht es, die `.env` umzustellen und `--setup` im neuen Projekt auszuführen — der Agent-Code selbst wird nicht kopiert oder neu installiert.

```
gitea-agent/   ← einmalig, bleibt immer bestehen
    .env       ← hier GITEA_REPO + PROJECT_ROOT auf das aktive Projekt zeigen

projekt-a/     ← nur agent/config/ + agent/data/ nötig (via --setup angelegt)
projekt-b/     ← dasselbe, einfach .env wechseln
```

**Kontext:** Du willst den gitea-agent für ein neues Projekt nutzen.

### Empfohlen: Setup-Wizard

```bash
# 1. gitea-agent klonen
git clone https://github.com/Alexander-Benesch/Gitea-Agent
cd Gitea-Agent

# 2. Wizard starten — führt durch alle Schritte interaktiv
python3 agent_start.py --setup
```

Der Wizard erledigt alles in 6 Schritten:
1. Gitea-Verbindung testen (URL + Token)
2. Repository prüfen
3. Projektverzeichnis setzen (`PROJECT_ROOT`)
4. Fehlende Labels automatisch anlegen
5. `agent_eval.json` erstellen (Server-URL, Log-Pfad, Start-Script)
6. `.env` schreiben — endet mit `--doctor` zur Verifikation

Details: [Kapitel 19 — Setup-Wizard](#19-setup-wizard-issue-77)

---

### Manuell (Fallback)

```bash
# 1. gitea-agent klonen
git clone https://github.com/Alexander-Benesch/Gitea-Agent
cd Gitea-Agent

# 2. .env befüllen
cp .env.example .env
# → GITEA_URL, GITEA_TOKEN, GITEA_REPO, PROJECT_ROOT anpassen

# 3. agent_eval.json erstellen
cp agent_eval.template.json /pfad/zum/projekt/tests/agent_eval.json
# → log_path, restart_script, server_url anpassen
# → Jeder Test braucht ein tag-Feld (Pflicht für Fehleranalyse)

# 4. Labels anlegen
# Gitea → Repo → Issues → Labels → manuell erstellen
# oder: python3 agent_start.py --setup (nur Label-Schritt)

# 5. Verifikation
python3 agent_start.py --doctor
python3 agent_start.py --list
```

**Pitfalls:**
- `PROJECT_ROOT` muss absoluter Pfad zum Zielprojekt sein
- Token-Scopes: `issue` (read+write) + `repository` (read+write)
- Labels müssen exakt wie in `settings.py` heißen
- `tag`-Felder in Tests sind Pflicht für systematische Fehleranalyse

---

## 2. Standard-Workflow: Issue → PR

**Kontext:** Normaler Entwicklungszyklus für ein neues Feature oder einen Bug.

**Dateien:** `agent_start.py`, Gitea Issue

**Schritte:**

```bash
# Optional: Projektspezifische Excludes konfigurieren
# agent/config/agent_eval.json → context_loader.exclude_dirs:
# { "context_loader": { "exclude_dirs": ["Backup", "Documentation"] } }

# Schritt 1: Issue schreiben
# In Gitea: Neue Issue → Body mit betroffenen Dateien in Backticks:
# "Bitte Timeout in `myproject/plugins/web_search.py` auf 8s setzen."
# Der Agent ergänzt automatisch via Import-Analyse (AST) + Keyword-Suche (grep).
# Label: ready-for-agent

# Schritt 2: Plan generieren
python3 agent_start.py --issue 61

# → Postet Plan-Kommentar ins Issue
# → Label: ready-for-agent → agent-proposed
# → Bei Risikostufe 2/3: zusätzlicher Analyse-Kommentar mit Rückfragen

# Schritt 3: Freigabe geben
# Im Issue kommentieren: "ok", "ja" oder "✅"

# Schritt 4: Implementieren
python3 agent_start.py --implement 61

# → Prüft Freigabe
# → Erstellt Branch: git checkout -b fix/issue-61-timeout-web-search
# → Label: agent-proposed → in-progress
# → Generiert Kontext: contexts/61-enhancement/starter.md + files.md

# Schritt 5: Code ändern
# LLM liest starter.md + files.md, ändert Code, committet nach jeder Datei

# Schritt 6: PR erstellen
python3 agent_start.py --pr 61 --branch fix/issue-61-timeout-web-search --summary "Timeout von 5s auf 8s erhöht"

# → Prüft Vorbedingungen (Plan vorhanden, Eval gelaufen, etc.)
# → Führt Eval aus (blockiert bei FAIL)
# → Erstellt PR auf Gitea
# → Label: in-progress → needs-review
# → Postet Abschluss-Kommentar mit Score + Verlauf
```

**Pitfalls:**
- Ohne `--summary` gibt es Warnung im Abschluss-Kommentar.
- Eval blockiert PR bei Score < Baseline — Baseline vorher prüfen.
- `--restart-before-eval` wenn Server-Code geändert wurde.

---

## 3. Bugfix auf in-progress Issue (--fixup)

**Kontext:** Während der Implementierung (Label: `in-progress`) wird ein Bug entdeckt und gefixt.

**Dateien:** `agent_start.py`, git commit

**Schritte:**

```bash
# 1. Bug entdecken, fixen, committen
git add myproject/plugins/web_search.py
git commit -m "fix: web_search timeout exception handling"

# 2. Fixup-Kommentar posten
python3 agent_start.py --fixup 61

# → Liest letzte Commit-Message via git log
# → Postet Bugfix-Kommentar ins Issue
# → Label: in-progress → needs-review
```

**Pitfalls:**
- Funktioniert nur wenn Issue `in-progress` Label hat.
- Commit muss auf Feature-Branch sein (nicht main).

---

## 4. Ersten Test schreiben (agent_eval.json)

**Kontext:** Du willst sicherstellen dass dein Projekt noch funktioniert — vor jedem PR.

**Dateien:** `agent_eval.template.json`, `agent/config/agent_eval.json`

**Schritte:**

```bash
# 1. Vorlage kopieren
cp agent_eval.template.json /pfad/zu/deinem/projekt/agent/config/agent_eval.json

# 2. Minimal-Konfiguration anpassen
```

**Minimales `agent_eval.json`:**

```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "watch_interval_minutes": 60,
  "log_path": "/home/user/myproject/gitea-agent.log",
  "restart_script": "/home/user/start_llm.sh",
  "tests": [
    {
      "name": "Routing einfach",
      "weight": 1,
      "worker_required": false,
      "message": "Was ist 2 plus 2?",
      "expected_keywords": ["4"],
      "tag": "math_basic"
    },
    {
      "name": "Kontext-Persistenz",
      "weight": 2,
      "worker_required": false,
      "message": "Mein Name ist Max. Wie heiße ich?",
      "expected_keywords": ["Max"],
      "tag": "context_persistence"
    }
  ]
}
```

**Test-Felder:**

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `name` | ja | Anzeigename |
| `weight` | ja | Gewichtung im Score |
| `message` | ja* | Nachricht an server.py (`*` außer bei `steps`) |
| `expected_keywords` | nein | Alle Keywords müssen in Antwort vorkommen (case-insensitive) |
| `worker_required` | nein | Worker offline → Test überspringen statt FAIL |
| `tag` | **ja** | Tag für systematische Fehlererkennung (Issue #50) |

**Pitfalls:**
- `tag` ist Pflicht — ohne Tag gibt `agent_self_check.py` Warnung.
- `worker_required: true` ohne `worker_url` → Test wird immer übersprungen.
- Keywords case-insensitive — `["Max"]` matcht auch `"max"`.

---

## 5. Mehrstufigen Test schreiben (steps)

**Kontext:** Test der mehrere Nachrichten sequenziell braucht (z.B. Fakt schreiben → abfragen).

**Dateien:** `agent/config/agent_eval.json`

**Schritte:**

```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "worker_url": "http://192.168.1.x:1235",
  "watch_interval_minutes": 60,
  "log_path": "/home/user/myproject/gitea-agent.log",
  "tests": [
    {
      "name": "Routing einfach",
      "weight": 1,
      "worker_required": false,
      "message": "Was ist 2 plus 2?",
      "expected_keywords": ["4"],
      "tag": "math_basic"
    },
    {
      "name": "Stilles Failure",
      "weight": 2,
      "worker_required": true,
      "steps": [
        {
          "message": "Mein Lieblingstier ist ein Pinguin",
          "expect_stored": true
        },
        {
          "message": "Was ist mein Lieblingstier?",
          "expected_keywords": ["Pinguin"]
        }
      ],
      "tag": "context_persistence"
    },
    {
      "name": "Mehrschrittige Abfrage",
      "weight": 3,
      "worker_required": true,
      "steps": [
        {
          "message": "Ich heiße Anna",
          "expect_stored": true
        },
        {
          "message": "Ich wohne in Berlin",
          "expect_stored": true
        },
        {
          "message": "Wie heiße ich und wo wohne ich?",
          "expected_keywords": ["Anna", "Berlin"]
        }
      ],
      "tag": "multi_step"
    },
    {
      "name": "Performance-Check",
      "weight": 1,
      "worker_required": false,
      "message": "Was ist die Hauptstadt von Deutschland?",
      "expected_keywords": ["Berlin"],
      "max_response_ms": 2000,
      "tag": "performance"
    }
  ]
}
```

**Step-Typen:**

1. **`expect_stored: true`** — Nachricht senden, nur Antwort (kein Fehler) erwartet. Für Fakten-Schreiben.
2. **`expected_keywords: [...]`** — Antwort wird auf Keywords geprüft. Für Fakten-Abfragen.

**Performance-Monitoring:**
- `max_response_ms`: Maximal erlaubte Antwortzeit in Millisekunden.
- Überschreitung → `[Auto-Perf]`-Issue im Watch-Modus.

**Pitfalls:**
- Steps werden sequenziell ausgeführt — 2s Cooldown zwischen Steps.
- `expect_stored` Steps haben keine Keyword-Prüfung — nur Antwort-Existenz.
- Performance-Tests ohne `max_response_ms` werden nicht überwacht.

---

## 6. Eval-Baseline neu setzen

**Kontext:** Nach Kalibrierung oder wenn Baseline zu hoch/zu niedrig ist.

**Dateien:** `evaluation.py`, `tests/baseline.json`

**Schritte:**

```bash
# 1. Standalone Eval mit --update-baseline
python3 evaluation.py --project /pfad/zu/deinem/projekt --update-baseline

# → Führt alle Tests aus
# → Speichert aktuellen Score als neue Baseline
# → Gibt "✓ Baseline angelegt (erster Lauf)." oder "✓ Baseline aktualisiert: X → Y"
```

**Automatisches Baseline-Management:**
- **Erster Lauf:** Immer PASS, Baseline wird angelegt.
- **Folgeläufe:** Score >= Baseline → PASS, Score < Baseline → FAIL.
- **Verbesserung:** Score > Baseline → Baseline wird automatisch hochgesetzt (nie runter).

**Baseline-Datei:** `agent/data/baseline.json` (neu) oder `tests/baseline.json` (Legacy)

```json
{"score": 8.0}
```

**Pitfalls:**
- `baseline.json` gehört in `.gitignore` — laufzeitgeneriert.
- Manuelles Editieren möglich, aber `--update-baseline` empfohlen.
- Baseline wird nie automatisch gesenkt — nur bei Verbesserung erhöht.

---

## 7. Watch-Modus einrichten (tmux + Dauerbetrieb)

**Kontext:** Du willst dass der Agent 24/7 läuft und bei Regressionen Auto-Issues erstellt.

**Dateien:** `agent_start.py`, tmux

**Schritte:**

```bash
# 1. Tmux-Session starten
tmux new -s agent-watch

# 2. Watch-Modus starten (Standard-Interval: 60 Minuten)
python3 agent_start.py --watch

# 3. Detachen: Ctrl+B, dann D
# 4. Wieder verbinden: tmux attach -t agent-watch
```

**Watch-Intervall konfigurieren:**

```json
// agent/config/agent_eval.json
{
  "watch_interval_minutes": 30,
  "log_path": "/home/user/myproject/gitea-agent.log",
  "restart_script": "/home/user/start_llm.sh",
  "inactivity_minutes": 5
}
```

**Watch-Ablauf (pro Zyklus):**
1. `evaluation.run(PROJECT, trigger="watch")` — alle Tests ausführen
2. Dashboard aktualisieren (`dashboard.html`)
3. `_close_resolved_auto_issues()` — geheilte Auto-Issues schließen
4. Für jeden failed_test:
   - Duplikat-Check (`_auto_issue_exists()`)
   - `_build_auto_issue_body()` → `gitea.create_issue()`
5. Skelett inkrementell aktualisieren (`_update_skeleton_incremental()`)
6. Systematische Tag-Fehler prüfen (`_check_systematic_tag_failures()`)
7. Log-Analyzer ausführen (falls konfiguriert)
8. Szenario 2: Automatischer Neustart bei Chat-Inaktivität + neuen Commits

**S