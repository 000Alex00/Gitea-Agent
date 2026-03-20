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
git clone http://192.168.1.x:3001/youruser/gitea-agent
cd gitea-agent

# 2. .env befüllen
cp .env.example .env
```

```ini
# .env — Werte anpassen (NICHT committen)
GITEA_URL=http://192.168.1.x:3001
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
3. Score < Baseline → `[Auto] <test-name> fehlgeschlagen` Issue erstellt (Label: `bug`)
4. Deduplication: gleiches Issue schon offen → kein Duplikat
5. Test erholt sich → Auto-Issue wird automatisch geschlossen

**Pitfalls:**
- tmux-Session überlebt SSH-Disconnect — wichtig bei Remote-Betrieb
- `--interval 0` würde Endlosschleife ohne Pause erzeugen — nicht nutzen
- Log landet in `gitea-agent.log` (konfigurierbar via `LOG_FILE` in `.env`)

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
