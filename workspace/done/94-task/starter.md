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
# Issue #94 — [08] Analyse: Technische Schranken für Datei-Lesezugriffe — Schlupflöcher schließen
Status: ⏳ Wartet auf Freigabe
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-94-08-analyse-technische-schranken-fu

## Ziel
## Problem

Die Skeleton + `--get-slice` Strategie ist eine **Verhaltens-Schranke**, keine technische. Der LLM-Agent kann sie jederzeit umgehen:

- `grep -n "..." datei.py` → liest gesamte Datei im Hi...

## Dateien
- agent_self_check.py
- agent_status.sh
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
- context_export.sh
- plugins/patch.py
- plugins/changelog.py
- scripts/agent_status.sh
- scripts/start_patch.sh
- scripts/push_github.sh
- scripts/context_export.sh
- data/doctor_last.json
- tests/test_patch.py
- tests/test_skeleton.py
- tests/test_slice_gate.py
- tests/test_changelog.py
- log.py

## Checkliste
- [ ] Quellcode lesen
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei committen
- [ ] git push origin chore/issue-94-08-analyse-technische-schranken-fu

## Commit-Template
<typ>: <beschreibung> (closes #94)

## PR-Befehl
python3 agent_start.py --pr 94 --branch chore/issue-94-08-analyse-technische-schranken-fu --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/94
