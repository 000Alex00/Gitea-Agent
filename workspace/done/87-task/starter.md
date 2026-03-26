## PFLICHTREGELN (bei Kontext-Drift: neue Session starten)
> ⚠️ **Technische Schranken haben Vorrang vor Prompt-Regeln.**
> `cmd_pr()` prüft Vorbedingungen automatisch — kein manueller Bypass möglich.

- NIEMALS `curl` statt `agent_start.py` verwenden
- NIEMALS Schritte überspringen
- NIEMALS PR manuell erstellen

⚠️ **Sessions-Limit:** Nach 2 Issues neue Claude-Session empfohlen.
Kontext-Drift Symptome: curl statt agent_start.py, fehlende Metadata, übersprungene Schritte.

## SELBST-CHECK vor jedem Schritt
- [ ] Vorheriger Schritt vollständig abgeschlossen?
- [ ] `agent_start.py` verwendet (nicht curl)?
- [ ] Metadata-Block vorhanden?
- [ ] Eval gelaufen?

Wenn Checkbox offen → **STOPP**. Schritt nachholen oder neue Session.

## Kontext

Die relevanten Dateien wurden automatisch erkannt:
- Backtick-Erwähnungen im Issue-Text
- Import-Analyse (AST)
- Keyword-Suche (grep)

⚠️ **NICHT selbst im Repo suchen** — der Kontext ist vollständig.
Falls etwas fehlt: im Issue nachfragen, nicht raten.

---
# Issue #87 — [05] Health-Check: /health-Endpoint-Strategie (Zwei-Wege-System Teil 1)
Status: 🔧 READY — Implementierung starten
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-87-05-health-check-health-endpoint-st

## Ziel
## Ziel

Universelle HTTP-basierte Health-Check-Strategie implementieren. Anwendungen die einen `/health`-Endpoint mitbringen werden automatisch überwacht — ohne DB-Credentials, ohne projektspezifisch...

## Diskussion
**Alexmistrator:** ok

## Dateien
- agent_self_check.py
- agent_status.sh
- stop_agent.sh
- start_patch.sh
- project.template.json
- push_github.sh
- agent_start.py
- gitea_api.py
- agent_eval.template.json
- dashboard.py
- settings.py
- evaluation.py
- repo_skeleton.json
- start_night.sh
- context_export.sh
- log.py
- plugins/patch.py
- plugins/changelog.py
- scripts/agent_status.sh
- scripts/stop_agent.sh
- scripts/start_patch.sh
- scripts/push_github.sh
- scripts/start_night.sh
- scripts/context_export.sh
- data/doctor_last.json
- tests/test_issue.py
- tests/test_patch.py
- tests/score_history.json
- tests/test_skeleton.py
- tests/test_changelog.py
- tests/test_settings.py
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin chore/issue-87-05-health-check-health-endpoint-st

## Commit-Template
<typ>: <beschreibung> (closes #87)

## PR-Befehl
python3 agent_start.py --pr 87 --branch chore/issue-87-05-health-check-health-endpoint-st --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/87
