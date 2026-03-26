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
# Issue #42 — [06] LLM-gestützte Log-Analyse + Custom Health Checks (Teil 2)
Status: ⏳ Wartet auf Freigabe
Risiko: 2/4 — MITTEL — Enhancement (Plan vor Implementierung)
Branch: chore/issue-42-06-llm-gestuetzte-log-analyse-cust

## Ziel
## Ziel
Log-Analyzer mit LLM-Unterstützung für Root-Cause-Hypothesen.

## Hintergrund
- log_analyzer.py existiert (regelbasiert)
- Erkennt nur bekannte Muster
- LLM könnte unbekannte Muster erkennen

...

## Dateien
- keine erkannt

## Checkliste
- [ ] Quellcode lesen
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei committen
- [ ] git push origin chore/issue-42-06-llm-gestuetzte-log-analyse-cust

## Commit-Template
<typ>: <beschreibung> (closes #42)

## PR-Befehl
python3 agent_start.py --pr 42 --branch chore/issue-42-06-llm-gestuetzte-log-analyse-cust --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/42
