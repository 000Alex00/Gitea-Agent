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
# Issue #76 — --doctor: Health-Check-Befehl für Agent-Integrität
Status: ⏳ Wartet auf Freigabe
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-76-doctor-health-check-befehl-fuer-ag

## Ziel
## Ziel
Neuer Befehl `--doctor` der den vollständigen Zustand des Agents prüft und klaren Status-Report ausgibt.

## Hintergrund
Aktuell gibt es keine Möglichkeit schnell zu prüfen ob der Agent korrek...

## Dateien
- agent_self_check.py
- agent_status.sh
- stop_agent.sh
- start_patch.sh
- push_github.sh
- agent_start.py
- doctor_last.json
- gitea_api.py
- agent_eval.template.json
- _create_issue_github.py
- dashboard.py
- settings.py
- evaluation.py
- repo_skeleton.json
- start_night.sh
- context_export.sh
- log.py
- plugins/patch.py
- plugins/changelog.py
- tests/test_issue.py
- tests/test_patch.py
- tests/score_history.json
- tests/test_skeleton.py
- tests/test_changelog.py

## Checkliste
- [ ] Quellcode lesen
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei committen
- [ ] git push origin chore/issue-76-doctor-health-check-befehl-fuer-ag

## Commit-Template
<typ>: <beschreibung> (closes #76)

## PR-Befehl
python3 agent_start.py --pr 76 --branch chore/issue-76-doctor-health-check-befehl-fuer-ag --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/76
