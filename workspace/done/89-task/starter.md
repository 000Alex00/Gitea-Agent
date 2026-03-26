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
# Issue #89 — [03] Refactor: evaluation.py von jetson-llm-chat entkoppeln
Status: 🔧 READY — Implementierung starten
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-89-03-refactor-evaluation-py-von-jets

## Ziel
## Problem

`evaluation.py` enthält hartcodierte Annahmen die nur für jetson-llm-chat gelten:
- Pi5-Erreichbarkeit (`pi5_url`, `pi5_offline`-Kategorie)
- `server.py` als einziger Test-Endpunkt
- Chrom...

## Diskussion
— keine —

## Dateien
- evaluation.py
- agent_self_check.py
- agent_status.sh
- start_patch.sh
- agent_start.py
- gitea_api.py
- agent_eval.template.json
- dashboard.py
- settings.py
- repo_skeleton.json
- scripts/agent_status.sh
- scripts/start_patch.sh
- data/doctor_last.json
- log.py
- plugins/patch.py
- plugins/changelog.py
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin chore/issue-89-03-refactor-evaluation-py-von-jets

## Commit-Template
<typ>: <beschreibung> (closes #89)

## PR-Befehl
python3 agent_start.py --pr 89 --branch chore/issue-89-03-refactor-evaluation-py-von-jets --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/89
