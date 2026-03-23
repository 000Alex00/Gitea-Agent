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
12. [PR mit veraltetem Server (Staleness-Check)](#12-pr-mit-veraltetem-server-staleness-check)
13. [Migration auf zentrale Agent-Instanz](#13-migration-auf-zentrale-agent-instanz)
14. [LLM-gestützte Test-Generierung (--generate-tests)](#14-llm-gestützte-test-generierung---generate-tests)
15. [Systematische Fehler-Erkennung (Tag-Aggregation)](#15-systematische-fehler-erkennung-tag-aggregation)
16. [Patch-Modus & Live-Dashboard](#16-patch-modus--live-dashboard)
17. [Consecutive-Pass Gate für Auto-Issues](#17-consecutive-pass-gate-für-auto-issues)
18. [Betriebsmodi — Night / Patch / Idle](#18-betriebsmodi--night--patch--idle)

---

## 1. Agent auf neues Projekt portieren

**Kontext:** Du willst den gitea-agent für ein neues Projekt nutzen.

**Dateien:** `.env`, `agent_eval.template.json`

**Schritte:**

```bash
# 1. gitea-agent klonen (oder bestehende Kopie verwenden)
git clone http://192.168.1.x:3001/youruser/gitea-agent
cd gitea-agent

# 2. .env befüllen
cp .env.example .env
# → Werte anpassen (GITEA_URL, GITEA_TOKEN, etc.)

# 3. agent_eval.json aus Vorlage erstellen
cp agent_eval.template.json /pfad/zu/deinem/projekt/agent/config/agent_eval.json
# → Pfade in der neuen Datei anpassen (log_path, restart_script)
```

**Wichtiger Hinweis zu `agent_eval.json`:**
- **`tag` ist Pflicht:** Jeder Test in `agent_eval.json` muss ein `tag`-Feld haben. Dieses Feld ist entscheidend für die systematische Fehlererkennung und das Performance-Monitoring. Der `agent_self_check.py` gibt eine Warnung aus, wenn Tags fehlen.

```bash
# 4. Labels in Gitea anlegen
# Gitea → Repo → Issues → Labels → folgende erstellen:
#   ready-for-agent   (grün)
#   agent-proposed    (blau)
#   in-progress       (gelb)
#   needs-review      (orange)

# 5. Ersten Testlauf
python3 agent_start.py --list
```

**Pitfalls:**
- `PROJECT_ROOT` in `.env` muss der absolute Pfad zum Zielprojekt sein.
- `tag`-Felder in den Tests sind essenziell für die Fehleranalyse. Nicht vergessen!
- Token braucht Scopes: `issue` (read+write) + `repository` (read+write).
- Labels müssen exakt so heißen wie in `settings.py` definiert.

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
# "Bitte Timeout in `nanoclaw/plugins/web_search.py` auf 8s setzen."
# Der Agent ergänzt automatisch via Import-Analyse (AST) + Keyword-Suche (grep).
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
- Wenn Eval auf altem Server-Code lief: `--restart-before-eval` oder manueller Neustart + `--pr` wiederholen

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
  "log_path": "/home/user/mein-projekt/logs/system.log",
  "restart_script": "/home/user/mein-projekt/start_assistant.sh",
  "inactivity_minutes": 5,
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

**Neue Felder:**
| Feld | Beschreibung |
|---|---|
| `log_path` | Pfad zur Logdatei — für Watch Inaktivitätserkennung (Szenario 2) |
| `restart_script` | Pfad zum Start-Skript — Watch startet Server automatisch neu |
| `inactivity_minutes` | Schwellwert Chat-Inaktivität in Minuten (Standard: 5) |

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
  "server_url": "http://192.168.1.x:8000",
  "chat_endpoint": "/chat",
  "pi5_url": "http://192.168.1.x:1235",
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

**Schritte:**

```bash
# Interval in agent_eval.json konfigurieren (einmalig)
# "watch_interval_minutes": 60   ← Standard

# tmux-Session starten
tmux new -s watch

# Watch starten (liest Interval aus agent_eval.json)
cd /home/user/gitea-agent
python3 agent_start.py --watch

# Oder mit explizitem Interval (überschreibt agent_eval.json)
python3 agent_start.py --watch --interval 30

# tmux detachen (läuft weiter im Hintergrund)
# Ctrl+B, dann D

# Session wiederfinden
tmux attach -t watch

# Beenden
tmux kill-session -t watch
```

**Was passiert pro Zyklus:**
1. Eval läuft gegen `server_url`
2. Score ≥ Baseline → nur Log, kein Issue
3. Score < Baseline → strukturiertes `[Auto]`-Issue erstellt (Label: `bug`) mit:
   - Tabelle Erwartung vs. Realität (einfache Tests) oder Step-Tabelle mit ✅/❌ (steps-Tests)
   - Regelbasierte Fehler-Kategorie (`timeout` / `keyword_miss` / `empty_response` / `server_error` / `pi5_offline`)
   - Letzte 3 Scores aus `score_history.json`
4. Deduplication: gleiches Issue schon offen → kein Duplikat
5. Test erholt sich → Auto-Issue wird automatisch geschlossen
6. `tools/log_analyzer.py` vorhanden → wird ausgeführt, Ausgabe ins Terminal
7. Szenario 2 Prüfung (wenn `restart_script` + `log_path` konfiguriert, siehe unten)

**Szenario 2 — automatischer Neustart:**

Pro Zyklus wird zusätzlich geprüft:
- Chat inaktiv seit ≥ `inactivity_minutes` (aus `log_path` ermittelt)
- Neue Commits seit letztem Eval-Eintrag in `score_history.json`

→ Wenn beide Bedingungen erfüllt: `restart_script` starten + sofort Eval ausführen

```json
{
  "log_path": "/home/user/myproject/logs/system.log",
  "restart_script": "/home/user/myproject/start_assistant.sh",
  "inactivity_minutes": 5
}
```

**Pitfalls:**
- tmux-Session überlebt SSH-Disconnect — wichtig bei Remote-Betrieb
- `--interval 0` würde Endlosschleife ohne Pause erzeugen — nicht nutzen
- Log landet in `gitea-agent.log` (konfigurierbar via `LOG_FILE` in `.env`)
- Szenario 2 greift nicht wenn `log_path` oder `restart_script` fehlen

---

## 8. Systemd-Timer: Eval nach Nachtsync

**Kontext:** Skynet synchronisiert jede Nacht Pi5-Code via `sync_pi.sh`. Danach soll Eval automatisch prüfen ob die Pipeline noch funktioniert.

**Dateien:** `nanoclaw/sync_pi.sh`, `systemd/skynet-sync.service`, `systemd/skynet-sync.timer`

**Timer-Setup:**

```ini
# systemd/skynet-sync.timer
[Unit]
Description=Nachtlicher Sync + Eval (täglich 03:30)

[Timer]
OnCalendar=*-*-* 03:30:00
OnBootSec=15min   # Auch nach Stromausfall nachholen

[Install]
WantedBy=timers.target
```

```ini
# systemd/skynet-sync.service
[Unit]
Description=Skynet Sync Jetson → Pi 5
After=network.target

[Service]
Type=oneshot
User=ki02
ExecStart=/bin/bash /home/user/myproject/nanoclaw/sync_pi.sh
```

```bash
# sync_pi.sh — am Ende des Skripts (nach erfolgreichem Sync):
if [ -f "$PROJECT_DIR/Helper-tools/agent_start.py" ] && \
   [ -f "$PROJECT_DIR/.venv/bin/python3" ]; then
    "$PROJECT_DIR/.venv/bin/python3" \
        "$PROJECT_DIR/Helper-tools/agent_start.py" \
        --eval-after-restart >> "$LOG_FILE" 2>&1 &
    log_msg "INFO" "Eval nach Sync gestartet (PID $!, background)."
fi
```

```bash
# Timer aktivieren
sudo cp systemd/skynet-sync.service /etc/systemd/system/
sudo cp systemd/skynet-sync.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable skynet-sync.timer
sudo systemctl start skynet-sync.timer

# Status prüfen
systemctl status skynet-sync.timer
systemctl list-timers skynet-sync.timer
```

**Pitfalls:**
- `&` am Ende → Eval läuft im Hintergrund, blockiert Sync nicht
- `OnBootSec=15min` verhindert dass ein verpasster Timer-Slot verloren geht
- server.py muss laufen wenn Eval startet — `--eval-after-restart` wartet automatisch (max 5 min)

---

## 9. Eval nach Neustart (--eval-after-restart)

**Kontext:** Du hast `start_assistant.sh` ausgeführt und willst danach automatisch Eval + Score ins Issue schreiben.

**Drei Szenarien:**

| Szenario | Auslöser | Issue-Kommentar |
|---|---|---|
| Manuell | `--eval-after-restart <NR>` | ✅ ja |
| Watch-Loop | Inaktiv >5 min + neue Commits | ❌ nur score_history |
| Nachtsync | sync_pi.sh Ende | ❌ nur score_history |

**Szenario 1 — Manuell:**

```bash
# Server starten
./start_assistant.sh

# Eval starten (wartet automatisch bis server.py bereit)
python3 Helper-tools/agent_start.py --eval-after-restart 61
# → Pollt http://localhost:8000 alle 10s (max 5 min)
# → Eval läuft sobald Server antwortet
# → Score-Kommentar in Issue #61
# → score_history.json aktualisiert (trigger: "restart")
```

**Szenario 2 — Watch-Loop automatisch:**
```bash
# Watch läuft bereits in tmux
# Bedingung: letzte Nutzernachricht >5 min + neue Commits seit letztem Eval
# → Watch ruft start_assistant.sh + eval-after-restart selbst auf
# Kein manueller Eingriff nötig
```

**Konfiguration (`.env` oder Umgebungsvariable):**

| Variable | Standard | Bedeutung |
|---|---|---|
| `SERVER_URL` | `http://localhost:8000` | Ziel-URL für Polling |
| `SERVER_WAIT_TIMEOUT` | `300` | Max. Wartezeit in Sekunden |
| `SERVER_WAIT_INTERVAL` | `10` | Polling-Intervall in Sekunden |

**Pitfalls:**
- Timeout 5 min: wenn server.py nach 5 min immer noch nicht antwortet → exit 1
- Ohne `<NR>`: nur score_history, kein Gitea-Kommentar
- `trigger: "restart"` erscheint in score_history und im History-Block der nächsten PR-Kommentare

---

## 10. Auto-Issue manuell schließen

**Kontext:** Watch-Modus hat ein `[Auto]`-Issue erstellt, aber der FAIL hat einen externen Grund (Hardware offline, Wartung) — kein echter Bug.

**Schritte:**

```bash
# Option A: In Gitea
# Issue → Close issue (Watch schließt es automatisch wenn Test wieder PASS)

# Option B: Via API
TOKEN=abc123xxxxxxxxxxxxx
curl -X PATCH \
  -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"state":"closed"}' \
  "http://192.168.1.x:3001/api/v1/repos/username/mein-projekt/issues/99"

# Option C: Watch erholt sich selbst
# Wenn der Test beim nächsten Zyklus wieder PASS → Issue wird automatisch geschlossen
```

**Pitfalls:**
- Manuell geschlossenes Issue wird nicht neu erstellt wenn FAIL anhält (Deduplication by title)
- Wenn echter Bug: Issue offen lassen → Watch-Modus tracked den Verlauf in score_history

---

## 11. log_analyzer integrieren

**Kontext:** Du willst dass der Watch-Modus pro Zyklus auch Logdateien analysiert und Anomalien meldet — z.B. häufige Fehler, hohe Latenz, Verbindungsabbrüche.

**Referenz:** Skynet-Projekt, `tools/log_analyzer.py`

**Dateien:** `tools/log_analyzer.py` (im Zielprojekt), `agent_start.py`

**Voraussetzung:**

Watch-Modus sucht automatisch nach `{PROJECT_ROOT}/tools/log_analyzer.py`. Wenn vorhanden, wird es pro Zyklus ausgeführt. Das Modul muss zwei Funktionen exportieren:

```python
def run() -> object:
    """Analysiert Logs und gibt ein Ergebnis-Objekt zurück."""
    ...

def format_terminal(result: object) -> str:
    """Gibt eine kompakte Zusammenfassung für Terminal aus."""
    ...
```

**Minimales Beispiel:**



### LLM-gestützte Log-Analyse (Root-Cause Analyse)

Der Log-Analyzer kann bei unbekannten oder wiederkehrenden Fehlern optional eine KI-gestützte Root-Cause-Analyse durchführen. Das System generiert dabei Hypothesen zur Fehlerursache, schlägt Fixes vor und weist auf bekannte Muster hin. 

**Voraussetzung:**
Du benötigst in der `agent_eval.json` einen Block `llm_log_analysis`, der die Anbindung konfiguriert (entweder an eine OpenAI-kompatible API wie `llama.cpp` oder Anthropic Claude).

**Beispiel für llama.cpp (lokal):**
```json
{
  "llm_log_analysis": {
    "enabled": true,
    "provider": "openai",
    "url": "http://localhost:8080/v1/chat/completions",
    "model": "mistral-instruct",
    "api_key": ""
  }
}
```

**Beispiel für Claude (Anthropic API):**
```json
{
  "llm_log_analysis": {
    "enabled": true,
    "provider": "anthropic",
    "url": "https://api.anthropic.com/v1/messages",
    "model": "claude-3-sonnet-20240229",
    "api_key": "sk-ant-..."
  }
}
```

**Ablauf:**
1. Der Watch-Modus führt den `log_analyzer.py` aus.
2. Wenn ein systematischer Fehler erkannt wird (Muster `error`), wird geprüft, ob `llm_log_analysis` aktiv ist.
3. Falls ja, sendet das Skript die Fehlermeldungen und Beispiel-Logs als Kontext an das Modell.
4. Das LLM antwortet mit einer Root-Cause-Hypothese und Lösungsvorschlägen, welche automatisch an das generierte Gitea-Issue angehängt werden.
5. **Tag-Kontext:** Zusätzlich wird die `score_history.json` analysiert, um dem LLM mitzuteilen, welche Test-Tags in letzter Zeit häufig fehlgeschlagen sind. Dadurch kann das LLM gezieltere Hypothesen aufstellen, die bekannte Schwachstellen berücksichtigen.
6. **Fallback:** Ist das LLM nicht erreichbar oder deaktiviert, greift der Log-Analyzer stillschweigend auf die klassische regelbasierte Analyse zurück.

```python
# tools/log_analyzer.py
from dataclasses import dataclass, field
from pathlib import Path

LOG_PATH = Path("/home/user/myproject/logs/system.log")
TAIL_LINES = 200

@dataclass
class AnalyzerResult:
    errors: list[str] = field(default_factory=list)
    warnings: int = 0

def run() -> AnalyzerResult:
    result = AnalyzerResult()
    if not LOG_PATH.exists():
        return result
    lines = LOG_PATH.read_text(errors="replace").splitlines()[-TAIL_LINES:]
    for line in lines:
        if "ERROR" in line or "Exception" in line:
            result.errors.append(line.strip())
        elif "WARNING" in line:
            result.warnings += 1
    return result

def format_terminal(r: AnalyzerResult) -> str:
    if not r.errors and r.warnings == 0:
        return "[LogAnalyzer] OK — keine Fehler"
    parts = [f"[LogAnalyzer] {len(r.errors)} Fehler, {r.warnings} Warnungen"]
    for e in r.errors[-3:]:  # max 3 anzeigen
        parts.append(f"  ✗ {e[:120]}")
    return "\n".join(parts)
```

**Integration:**

Keine Konfiguration nötig — Watch-Modus erkennt `tools/log_analyzer.py` automatisch:

```
[Watch] Zyklus 1 (2026-03-20 14:00)
[Eval] Score: 7/7 (Baseline: 7) ✓ PASS
[LogAnalyzer] 2 Fehler, 5 Warnungen
  ✗ 2026-03-20 13:58:01 ERROR analyst_worker — DuckDuckGo Timeout nach 23s
  ✗ 2026-03-20 13:59:44 ERROR router — Pi5 nicht erreichbar
    Nächster Lauf in 60 Minute(n)...
```

**Pitfalls:**
- Exceptions in `log_analyzer.py` werden abgefangen — Watch läuft trotzdem weiter (nur Warnung im Log)
- Kein Interface-Vertrag — `run()` kann beliebiges Objekt zurückgeben solange `format_terminal()` es verarbeitet
- Log-Analyzer schreibt keine Gitea-Issues — nur Terminal-Output (Eval bleibt zuständig für Auto-Issues)

---

## 12. PR mit veraltetem Server (Staleness-Check)

**Kontext:** Du hast Code committed und rufst `--pr` auf — aber der Server läuft noch mit dem alten Code.
Der Eval würde die alte Version testen, nicht den neuen Code.

**Dateien:** `agent_start.py`, `tests/agent_eval.json`

**Voraussetzung:** `log_path` in `agent_eval.json` konfiguriert, Server schreibt Startup-Message ins Log:

```json
{
  "log_path": "/home/user/myproject/logs/system.log"
}
```

**Was passiert automatisch:**

```
python3 agent_start.py --pr 61 --branch fix/issue-61-...
→ [!] Server-Code veraltet
      Letzter Commit: 2026-03-20 22:45 (fix/issue-61-...)
      Server gestartet: 2026-03-20 21:20

      → Server neu starten, dann erneut --pr aufrufen.
        Oder: --restart-before-eval (automatisch) / --force (überspringen)
```

**Option A — Manueller Neustart:**

```bash
# Server neu starten (projektspezifisch)
./start_assistant.sh

# Dann PR erneut aufrufen
python3 agent_start.py --pr 61 --branch fix/issue-61-... --summary "..."
```

**Option B — Automatischer Neustart:**

```bash
python3 agent_start.py --pr 61 --branch fix/issue-61-... \
  --restart-before-eval \
  --summary "..."
# → Führt restart_script aus agent_eval.json aus
# → Wartet bis Server antwortet (max SERVER_WAIT_TIMEOUT Sekunden)
# → Eval + PR
```

Voraussetzung: `restart_script` in `agent_eval.json`:
```json
{
  "restart_script": "/home/user/myproject/start_assistant.sh"
}
```

**Option C — Check überspringen:**

```bash
python3 agent_start.py --pr 61 --branch fix/issue-61-... --force --summary "..."
# → Warnung wird ausgegeben, aber Eval läuft trotzdem
# → Sinnvoll wenn: Änderung betrifft nur Docs/Config (kein Neustart nötig)
```

**Pitfalls:**
- Check wird silent übersprungen wenn `log_path` fehlt oder Startup-Muster nicht gefunden — kein Fehler
- Startup-Muster die erkannt werden: `application startup complete`, `uvicorn running`, `server started`, u.a.
- Zeitzone: Commit-Timestamp und Log-Timestamp werden auf naive datetime normalisiert für Vergleich

---

## 13. Migration auf zentrale Agent-Instanz

**Kontext:** Du willst Laufzeitdaten (contexts/, Log, Session) aus dem Submodul-Verzeichnis herauslösen und einen zentralen gitea-agent für mehrere Projekte nutzen.

**Voraussetzung:** gitea-agent als eigenständiger Clone (nicht als Submodul).

**Schritte:**

```bash
# 1. Projektstruktur anlegen
mkdir -p /home/user/mein-projekt/agent/config
mkdir -p /home/user/mein-projekt/agent/data

# 2. agent_eval.json verschieben (war: tests/agent_eval.json)
mv /home/user/mein-projekt/tests/agent_eval.json \
   /home/user/mein-projekt/agent/config/agent_eval.json

# 3. log_analyzer.py verschieben (war: tools/log_analyzer.py)
mv /home/user/mein-projekt/tools/log_analyzer.py \
   /home/user/mein-projekt/agent/config/log_analyzer.py

# 4. .env anlegen (agent/.env — Symlink oder Kopie)
cp /home/user/gitea-agent/.env.example /home/user/mein-projekt/agent/.env
# PROJECT_ROOT=/home/user/mein-projekt eintragen
```

```ini
# agent/.env
GITEA_URL=http://192.168.1.x:3001
GITEA_USER=dein-username
GITEA_TOKEN=abc123xxxxxxxxxxxxx
GITEA_REPO=username/mein-projekt
PROJECT_ROOT=/home/user/mein-projekt
```

```bash
# 5. .gitignore im Projekt anpassen
echo "agent/data/" >> /home/user/mein-projekt/.gitignore
echo "agent/.env"  >> /home/user/mein-projekt/.gitignore

# 6. Agent mit project-spezifischer .env starten
cd /home/user/gitea-agent
env $(cat /home/user/mein-projekt/agent/.env | grep -v '^#' | xargs) python3 agent_start.py

# Oder: .env direkt im gitea-agent-Verzeichnis auf das Projekt zeigen lassen
ln -sf /home/user/mein-projekt/agent/.env /home/user/gitea-agent/.env
python3 agent_start.py
```

**Was passiert automatisch:**
- Agent erkennt `PROJECT_ROOT/agent/` → nutzt neue Pfade
- `agent/data/contexts/`, `agent/data/gitea-agent.log`, `agent/data/session.json` werden auto-erstellt
- `agent/config/agent_eval.json` wird für Eval genutzt
- Fallback: wenn `agent/` nicht existiert → alte Pfade (keine Breaking Changes)

**Für Skynet (jetson-llm-chat) konkret:**

```bash
mkdir -p /home/user/myproject/agent/config
mkdir -p /home/user/myproject/agent/data

# Configs verschieben
mv /home/user/myproject/tests/agent_eval.json \
   /home/user/myproject/agent/config/
mv /home/user/myproject/tools/log_analyzer.py \
   /home/user/myproject/agent/config/

# .env anlegen
echo "PROJECT_ROOT=/home/user/myproject" >> /home/user/myproject/agent/.env
# + alle anderen Gitea-Credentials ergänzen

# .gitignore
echo "agent/data/" >> /home/user/myproject/.gitignore
echo "agent/.env"  >> /home/user/myproject/.gitignore
```

**Pitfalls:**
- `agent_eval.json` Pfad in `log_path`/`restart_script` anpassen (absolute Pfade eintragen)
- `baseline.json` + `score_history.json` neu erzeugen lassen (erster Lauf nach Migration → neue Baseline)
- Submodul `Helper-tools/` kann danach entfernt werden wenn nicht mehr benötigt

## Agent Self-Consistency Check

Der Gitea Agent enthält einen integrierten deterministischen Check, um sicherzustellen, dass Erweiterungen am Agenten selbst vollständig und korrekt implementiert wurden (z.B. neue Flags ohne fehlende Handlers).

### Was wird geprüft?
1. **Labels:** Alle in `settings.py` definierten Labels existieren im Gitea-Projekt.
2. **Flags:** Alle CLI-Flags in `agent_start.py` (`argparse`) haben ein zugehöriges `cmd_*()` Handle.
3. **Pflichtfelder:** Alle in `COMMENT_REQUIRED_FIELDS` (`settings.py`) definierten Felder werden bei der Erstellung von Gitea-Kommentaren in `agent_start.py` eingebunden.
4. **Environment Variables:** Alle mit `_env()` abgerufenen Konfigurationen in `settings.py` sind in der Vorlage `.env.example` dokumentiert.

### Wann wird der Check ausgeführt?
Der Check läuft automatisch innerhalb von `_check_pr_preconditions()` bevor ein PR (`--pr`) erstellt wird. Er greift nur, wenn Änderungen an `agent_start.py`, `settings.py` oder `gitea_api.py` detektiert wurden.

### Fehlerbehebung
Schlägt der Check fehl, wird der PR-Befehl blockiert und die Fehler werden im Terminal ausgegeben. Behebe die angezeigten Fehler (z.B. durch Hinzufügen der fehlenden Funktion oder des Labels) und starte den Befehl erneut. Du kannst den Check zur Validierung auch manuell ausführen:
```bash
python3 agent_self_check.py
```

## 14. LLM-gestützte Test-Generierung (--generate-tests)

Der Agent kann dir dabei helfen, Unit-Tests (`pytest`), Integrationstests und Evaluierungs-Einträge (`agent_eval.json`) für ein Issue automatisch via LLM generieren zu lassen. Dies spart Zeit beim manuellen Erstellen von Regressionstests.

### Ablauf

**1. Generierung anstoßen**
Rufe den Agenten mit der Issue-Nummer auf, für die Tests generiert werden sollen:
```bash
python3 agent_start.py --generate-tests 44
```

**2. Was passiert im Hintergrund?**
Der Agent lädt das Issue, sucht alle relevanten Dateien (Code und Imports) zusammen und erstellt einen spezifischen Prompt in einem neuen Kontext-Ordner (z. B. `contexts/44-task-tests/tests_prompt.md`). In diesem Prompt ist festgelegt:
*   Es sollen `pytest` Unit-Tests generiert werden.
*   Es sollen `agent_eval.json` Einträge hinzugefügt werden.
*   **Wichtig:** Jeder Test in `agent_eval.json` muss zwingend ein `tag`-Feld (z. B. `"tag": "chroma_retrieval"`) besitzen, um den Bereich zu kennzeichnen.

**3. Tests mit Claude ausführen**
Anschließend gibt der Agent den genauen Befehl aus, den du ausführen musst, um Claude Code aufzurufen.
```bash
claude -p contexts/44-task-tests/tests_prompt.md
```

Nachdem Claude die Tests erstellt hat, solltest du diese kurz manuell verifizieren (`pytest`, `python3 evaluation.py`) und kannst sie danach in deinen Branch übernehmen.

## 15. Systematische Fehler-Erkennung (Tag-Aggregation)

Der Watch-Modus kann wiederkehrende Fehlermuster bei Test-Tags identifizieren und automatisch "Verbesserungs-Issues" erstellen. 

### Ablauf

**1. Tags in Tests definieren**
Stelle sicher, dass Tests in der `agent_eval.json` ein `tag` Feld haben (z. B. `"tag": "routing"`).

**2. Schwellenwerte und Hints setzen**
Konfiguriere in der `agent_eval.json`, ab wann ein Tag als "systematisch kaputt" gilt und hinterlege Lösungsansätze:
```json
{
  "tag_failure_threshold": 3,
  "tag_failure_window": 5,
  "affected_files": {
    "routing": ["agent/router.py", "agent/config/prompts.yaml"]
  },
  "improvement_hints": {
    "routing": "Prüfe den Router-Prompt auf Halluzinationen. Evtl. Temperatur senken.",
    "chroma_retrieval": "Embeddings neu aufbauen oder Top-K erhöhen."
  }
}
```

**3. Watch-Modus Analyse**
Der Agent prüft nach jedem Durchlauf die `score_history.json`.
Tritt ein Fehler bei einem Tag in 3 von 5 aufeinanderfolgenden Läufen auf, wird automatisch ein Issue mit dem Titel `[Auto-Improvement] Systematische Schwäche bei Tag: <tag>` erstellt und dein konfigurierter Hinweis (`improvement_hints`) als Lösungsansatz vorgeschlagen.

## 16. Patch-Modus & Live-Dashboard

Wenn du lokal stark am Code arbeitest (oft speicherst, Code oft inkonsistent ist), stören die automatischen Gitea-Issues und blockierten Neustarts des Watch-Modus.

### Patch-Modus aktivieren
Starte den Watch-Modus mit dem Flag `--patch`:
```bash
python3 agent_start.py --watch --patch
```
**Was passiert im Patch-Modus?**
*   **Keine Auto-Issues:** Es werden keine neuen Issues für Fehler oder Performance-Regressionen in Gitea angelegt.
*   **Neustarts erlaubt:** Der Server wird bei neuen Commits sofort neu gestartet, der Inaktivitäts-Check (z.B. 5 Minuten warten) entfällt.

### Live-Dashboard
Anstatt Fehler in Gitea zu verfolgen, kannst du das Live-Dashboard nutzen. Bei jedem Eval-Lauf im Watch-Modus generiert der Agent automatisch eine `dashboard.html` im Projekt-Root.
Öffne diese Datei einfach im Browser:
```bash
open dashboard.html
# oder im Browser: file:///home/.../dashboard.html
```
Das Dashboard zeigt:
*   Deinen Score-Verlauf (Chart.js) der letzten 24 Stunden.
*   Live-Status des Servers und Pi5.
*   Die letzten Fehler, Evaluations-Läufe und fehlschlagende Tags.

Um das Dashboard ohne Watch-Modus einmalig manuell zu generieren:
```bash
python3 agent_start.py --dashboard
```

---

## 17. Consecutive-Pass Gate für Auto-Issues

**Kontext:** Ein intermittierender Test (z.B. ChromaDB-Kontext) besteht manchmal zufällig. Das Auto-Issue wird sofort geschlossen, obwohl der Fix nicht verifiziert ist.

**Lösung:** `close_after_consecutive_passes` in `agent_eval.json` — Auto-Issues werden erst nach N aufeinanderfolgenden Passes geschlossen.

### Konfiguration

In `agent/config/agent_eval.json` des Zielprojekts:

```json
{
  "close_after_consecutive_passes": 3
}
```

| Wert | Verhalten |
|---|---|
| `1` (Default) | Sofort schließen beim ersten Pass (bisheriges Verhalten) |
| `3` | Test muss 3x hintereinander in der Watch-Loop bestehen |

### Was passiert

1. Test besteht → Watch-Loop zählt aufeinanderfolgende Passes aus `score_history.json`
2. Zähler < Schwellwert → Fortschritts-Kommentar im Issue: `"⏳ Test besteht (2/3) — warte auf Bestätigung"`
3. Zähler >= Schwellwert → Issue wird geschlossen
4. Test schlägt zwischendurch fehl → Zähler wird zurückgesetzt (break bei erstem FAIL)

### Beispiel-Timeline

```
Zyklus 1: "Stilles Failure" FAIL  → Auto-Issue #42 erstellt
Zyklus 2: "Stilles Failure" PASS  → Kommentar "⏳ Test besteht (1/3)"
Zyklus 3: "Stilles Failure" FAIL  → Kette unterbrochen, Zähler zurück auf 0
Zyklus 4: "Stilles Failure" PASS  → Kommentar "⏳ Test besteht (1/3)"
Zyklus 5: "Stilles Failure" PASS  → Kommentar "⏳ Test besteht (2/3)"
Zyklus 6: "Stilles Failure" PASS  → Issue #42 geschlossen (3/3 erreicht)
```

### Pitfalls

- Kommentar-Dedup: gleicher Zählerstand wird nicht doppelt gepostet
- Ohne das Feld: Standard `1` — kein Breaking Change
- Perf-Issues (`[Auto-Perf]`) folgen der gleichen Logik

---

## 18. Betriebsmodi — Night / Patch / Idle

**Kontext:** Der Agent soll ohne offene Terminal-Session laufen. Drei Modi decken alle Szenarien ab: autonomer Nachtbetrieb, aktive Entwicklung, und Pause.

### Übersicht

| Modus | Service | Beschreibung |
|---|---|---|
| **NIGHT** | `gitea-agent-night` | Autonomer Betrieb: Watch, Eval, Auto-Issues, Log-Analyse |
| **PATCH** | `gitea-agent-patch` | Aktive Entwicklung: Watch mit `--patch` (keine Auto-Issues) |
| **IDLE** | — | Alles gestoppt |

### Ersteinrichtung

```bash
# 1. Systemd-Units installieren (einmalig)
python3 agent_start.py --install-service

# 2. Skripte sind sofort nutzbar:
./start_night.sh    # → Night-Modus
./start_patch.sh    # → Patch-Modus
./stop_agent.sh     # → IDLE
./agent_status.sh   # → Status anzeigen
```

### Wechsel zwischen Modi

```bash
# Night → Patch (Patch stoppt Night automatisch)
./start_patch.sh

# Patch → Night (Night stoppt Patch automatisch)
./start_night.sh

# Alles stoppen
./stop_agent.sh
```

Immer nur ein Modus aktiv — jedes Start-Skript stoppt den anderen zuerst.

### start_patch.sh — Was passiert

1. Stoppt Night-Service (falls aktiv)
2. Server-Neustart via `restart_script` (falls konfiguriert)
3. Eval durchführen + Dashboard aktualisieren
4. `gitea-agent-patch.service` starten

### start_night.sh — Was passiert

1. Stoppt Patch-Service (falls aktiv)
2. `gitea-agent-night.service` starten
3. Watch-Loop läuft: Eval, Tag-Aggregation, Log-Analyse, Auto-Issues

### agent_status.sh — Ausgabe

```
=== Agent-Status ===
Modus:    NIGHT
Seit:     Sat 2026-03-22 20:00:00 CET
Laufzeit: 8h 30m

Letzter Eval: 7/7 ✅ PASS (2026-03-23T04:00)

Offene Issues: 3 (1 Auto, 2 manuell)
  # 42 [Auto] Stilles Failure fehlgeschlagen [ready-for-agent]
  # 50 Consecutive-Pass Gate
  # 52 Betriebsmodi
```

### Dashboard-Event-Updates

Das Dashboard wird nicht nur im Watch-Takt aktualisiert, sondern sofort nach:
- PR-Abschluss (`cmd_pr`)
- Auto-Issue erstellt/geschlossen
- Server-Neustart + Eval
- Manuelles `--dashboard`

### Pflicht-Kette vor PR

`_check_pr_preconditions()` erzwingt:
1. Branch ≠ main
2. Plan-Kommentar vorhanden
3. Eval nach letztem Commit
4. Server-Neustart empfohlen (wenn `restart_script` konfiguriert und Eval veraltet)

### Pitfalls

- `--install-service` braucht `sudo` für `/etc/systemd/system/`
- Pfade werden dynamisch aus der aktuellen Umgebung abgeleitet — kein Hardcoding
- Logs: `journalctl -u gitea-agent-night -f` bzw. `-u gitea-agent-patch`

---

## 12. LLM-Workflow — Welches LLM, welcher Befehl

> Implementiert in Issue #65 — `context_export.sh` + `--self` Flag + Dual-Repo-Support. Siehe auch Kapitel 13.

### Claude Code (Standard)

```bash
python3 agent_start.py --implement NR
```

Claude Code liest `starter.md` selbst und arbeitet direkt im Dateisystem.

### Gemini CLI

> ⚠️ **Eingeschränkt nutzbar** — nur für einfache Issues (eine Datei, < 50 Zeilen). Bei komplexen Issues: Scope-Drift, ignoriert `--self` beim PR-Befehl, Infinite Loop nach Abschluss. Für alles andere: Claude Code verwenden.

```bash
# Kontext laden + Gemini direkt starten
./context_export.sh NR gemini

# gitea-agent Eigenentwicklung
./context_export.sh NR --self gemini
```

Gemini bekommt `starter.md` + `files.md` als `@`-Referenzen übergeben.

### Web-Chat (GPT, Claude Web, Gemini Web, Copilot)

```bash
# Kontext-Datei erzeugen
./context_export.sh NR file

# → context_NR.md in Web-Chat hochladen
# → Anweisung: "Lies die Datei und arbeite das Issue ab"
# → Nach Session: PR-Befehl manuell ausführen (wird in der Datei angezeigt)
```

### Plain-Text (Copy/Paste)

```bash
./context_export.sh NR
# → Kontext im Terminal ausgeben, manuell kopieren
```

### PR-Befehl nach jeder Session

```bash
# Standard (jetson-llm-chat)
python3 ~/gitea-agent/agent_start.py --pr NR --branch BRANCH --summary "..."

# gitea-agent Eigenentwicklung
GITEA_REPO=youruser/gitea-agent \
python3 ~/gitea-agent/agent_start.py --self --pr NR --branch BRANCH --summary "..." --force
```

---

## 13. Zwei Repos — Ein Agent

Der Agent kann zwei verschiedene Repos verwalten:

| | jetson-llm-chat | gitea-agent |
|---|---|---|
| Env-Datei | `.env` | `.env.agent` |
| Eval | läuft (agent_eval.json vorhanden) | übersprungen |
| Flag | (Standard) | `--self` |

### Setup

`.env.agent` liegt in `~/gitea-agent/` und enthält:

```
GITEA_REPO=youruser/gitea-agent
PROJECT_ROOT=/home/user/gitea-agent
# Kein agent_eval.json → Eval wird übersprungen
```

### Befehle mit --self

```bash
# Issue planen
python3 agent_start.py --self --issue NR

# Implementieren (Kontext generieren)
python3 agent_start.py --self --implement NR

# PR erstellen
GITEA_REPO=youruser/gitea-agent \
python3 agent_start.py --self --pr NR --branch BRANCH --summary "..." --force

# Patch-Modus für gitea-agent
./start_patch.sh --self

# Kontext für Gemini / Web-Chat
./context_export.sh NR --self gemini
./context_export.sh NR --self file
```

### Eval-Verhalten

- `agent_eval.json` in `PROJECT_ROOT/agent/config/` oder `PROJECT_ROOT/tests/` → Eval läuft
- Datei fehlt → Eval wird automatisch übersprungen
- `gitea-agent` hat kein `agent_eval.json` → `--force` beim `--pr` nötig

---

## 14. AST-Repository-Skelett (#68)

Bei `--issue` und `--implement` wird für alle relevanten Python-Dateien automatisch ein AST-Skelett erzeugt.

### Was wird generiert

| Datei | Inhalt |
|---|---|
| `contexts/NR-*/repo_skeleton.json` | Maschinenlesbar — Pfad, Zeilen, Symbole |
| `contexts/NR-*/repo_skeleton.md` | LLM-Prompt — oben in `files.md` eingebettet |

### Format repo_skeleton.json

```json
[
  {
    "path": "agent_start.py",
    "truncated": false,
    "lines": 3174,
    "size_kb": 120,
    "symbols": [
      {"type": "function", "name": "cmd_plan", "lines": "1250-1340", "signature": "def cmd_plan(number: int) -> None:"},
      {"type": "class",    "name": "Foo",      "lines": "45-90",     "signature": "class Foo:"}
    ]
  }
]
```

Dateien > `_MAX_SKELETON_FILE_SIZE_KB` (Standard: 20 KB) werden als `truncated: true` markiert — kein Volltext, nur Metadaten.

### Zeilenbereich nachladen — --get-slice

Wenn das Skelett zeigt dass eine Funktion relevant ist, kann der exakte Bereich nachgeladen werden:

```bash
python3 agent_start.py --get-slice agent_start.py:1250-1340

# Mit --self (gitea-agent Eigenentwicklung)
python3 agent_start.py --self --get-slice agent_start.py:45-90
```

Ausgabe: nummerierte Zeilen direkt im Terminal — ideal zum Kopieren in den LLM-Kontext.

### Konfiguration

```bash
# .env oder .env.agent
MAX_FILE_LINES=300       # Ab dieser Zeilenzahl: Datei wird in files.md gekürzt
```

`_MAX_SKELETON_FILE_SIZE_KB` (20 KB) ist aktuell nur als Code-Konstante konfigurierbar.

---

## 15. Diff-Validierung (#57)

Bei `--pr` prüft `_check_pr_preconditions()` automatisch ob das LLM nur Zeilen innerhalb des freigegebenen AST-Bereichs geändert hat.

### Verhalten

- **Nicht-blockierend** — kein harter Abbruch, Entwickler entscheidet
- Warnung im Terminal + Kommentar im Gitea-Issue bei Scope-Verletzung
- Nur `.py`-Dateien werden geprüft (andere Dateien: kein Check)

### Wann schlägt es an

| Situation | Reaktion |
|---|---|
| Datei war nicht im Skelett-Kontext | Warnung: "nicht im Skelett" |
| Geänderte Zeile liegt außerhalb aller AST-Symbole | Warnung mit Zeilennummern |
| Alle Änderungen im Scope | Stille — kein Kommentar |

### Beispiel-Ausgabe

```
[!] Diff-Validierung: 2 Scope-Warnung(en):
    - agent_start.py: 3 Zeile(n) außerhalb AST-Bereich: [42, 43, 44]
    - settings.py: nicht im Skelett — 5 Zeile(n) geändert
```

Zusätzlich wird ein Kommentar ins Gitea-Issue gepostet, damit der Review sieht was außerhalb des Plans geändert wurde.

---

## Sitzungs-Protokoll 2026-03-23

### Durchgeführte Änderungen
- `context_export.sh` — LLM-agnostischer Kontext-Export (plain/gemini/file)
- `.env.agent` — Dual-Repo-Unterstützung für gitea-agent Eigenentwicklung
- `--self` Flag in `agent_start.py` — schaltet zwischen jetson-llm-chat und gitea-agent
- `start_patch.sh` — `--self` Flag ergänzt
- `evaluation.py` — Commit-Hash in score_history.json
- `context_export.sh` — CONTEXT_DIR aus .env.agent lesen (Fix)
- `agent_eval.json` — Tags für alle Tests gesetzt (chroma_retrieval, routing, web_search)
- `score_history.json` — Tags nachträglich migriert
- `dashboard.py` — failed vs failed_tests Feldname-Fix
- `dashboard.html` — Tag-Aggregation funktioniert jetzt

### ⚠️ Gemini CLI — NICHT FUNKTIONAL für Agent-Workflow

Gemini CLI ist aktuell NICHT geeignet für komplexe Issues:
- Verlässt den Issue-Scope unkontrolliert
- Refactored Dateien die nicht zum Issue gehören
- Ignoriert --self Flag beim PR-Befehl
- Infinite Loop nach Abschluss (Bug in Gemini CLI)

Gemini CLI NUR für einfache Issues verwenden (< 50 Zeilen, eine Datei).
Für alle anderen Issues: Claude Code verwenden.

### Offene Issues
- #68  AST-Skelett (neu erstellt — mit Claude Code abarbeiten)
- context_export.sh: files.md wird nicht zuverlässig eingebettet
- Gemini Scope-Drift: strikterer Prompt nötig in context_export.sh
