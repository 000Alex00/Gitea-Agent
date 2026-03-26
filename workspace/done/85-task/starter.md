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
# Issue #85 — [07] Token-Budget-Tracker — Slice-Token zählen + warnen bei Limit-Annäherung
Status: ⏳ Wartet auf Freigabe
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-85-07-token-budget-tracker-slice-toke

## Ziel
## Hintergrund

Aus der Analyse von Issue #82 (Token Verdichtung) folgt dieser konkrete, architekturkonforme Vorschlag.

## Problem

`cmd_get_slice` liefert Zeilenbereiche on-demand, aber es gibt kein...

## Dateien
- agent_start.py
- settings.py
- context_export.sh
- agent_self_check.py
- agent_status.sh
- stop_agent.sh
- start_patch.sh
- project.template.json
- push_github.sh
- gitea_api.py
- agent_eval.template.json
- dashboard.py
- evaluation.py
- repo_skeleton.json
- start_night.sh
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
- tests/test_skeleton.py
- tests/test_token_budget.py
- tests/test_changelog.py
- tests/test_settings.py

## Checkliste
- [ ] Quellcode lesen
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei committen
- [ ] git push origin chore/issue-85-07-token-budget-tracker-slice-toke

## Commit-Template
<typ>: <beschreibung> (closes #85)

## PR-Befehl
python3 agent_start.py --pr 85 --branch chore/issue-85-07-token-budget-tracker-slice-toke --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/85
