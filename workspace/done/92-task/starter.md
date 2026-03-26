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
# Issue #92 — [02] Projektstruktur: saubere Trennung Code / Laufzeit / Config / Scripts
Status: 🔧 READY — Implementierung starten
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-92-02-projektstruktur-saubere-trennun

## Ziel
## Problem

Der Root des gitea-agent ist ein Durcheinander — Laufzeit-Dateien, Code, Docs und Shell-Scripts liegen auf einer Ebene. Das erschwert Navigation, gitignore-Verwaltung und den Einsatz auf n...

## Diskussion
**Alexmistrator:** ok


## Dateien
- start_night.sh
- stop_agent.sh
- context_56.md
- _create_issue_github.py
- settings.py
- agent_self_check.py
- agent_status.sh
- start_patch.sh
- push_github.sh
- agent_start.py
- doctor_last.json
- gitea_api.py
- agent_eval.template.json
- dashboard.py
- evaluation.py
- repo_skeleton.json
- context_export.sh
- log.py
- plugins/patch.py
- plugins/changelog.py
- tests/test_issue.py
- tests/test_patch.py
- tests/test_skeleton.py
- tests/test_changelog.py
- tests/test_settings.py
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin chore/issue-92-02-projektstruktur-saubere-trennun

## Commit-Template
<typ>: <beschreibung> (closes #92)

## PR-Befehl
python3 agent_start.py --pr 92 --branch chore/issue-92-02-projektstruktur-saubere-trennun --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/92
