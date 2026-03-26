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
# Issue #78 — Unit-Tests für kritische reine Funktionen (pytest)
Status: 🔧 READY — Implementierung starten
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-78-unit-tests-fuer-kritische-reine-fun

## Ziel
## Ziel
pytest Unit-Tests für alle reinen Hilfsfunktionen in agent_start.py — kein Server, kein Gitea, keine Seiteneffekte nötig.

## Hintergrund
Der Agent hat keine Unit-Tests. Kritische Funktionen w...

## Diskussion
**Alexmistrator:** ok

## Dateien
- agent_self_check.py
- agent_status.sh
- start_patch.sh
- agent_start.py
- gitea_api.py
- agent_eval.template.json
- _create_issue_github.py
- dashboard.py
- settings.py
- evaluation.py
- repo_skeleton.json
- context_export.sh
- log.py
- tests/score_history.json
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin chore/issue-78-unit-tests-fuer-kritische-reine-fun

## Commit-Template
<typ>: <beschreibung> (closes #78)

## PR-Befehl
python3 agent_start.py --pr 78 --branch chore/issue-78-unit-tests-fuer-kritische-reine-fun --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/78
