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
# Issue #60 — [09] Killer-Feature: Autonomous Self-Healing Loop (TDD-Synthesis)
Status: ⏳ Wartet auf Freigabe
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-60-09-killer-feature-autonomous-self

## Ziel
Erst implemntieren, wenn issue 55-59 implementiert ist.

Ziel
Der Agent soll Fehler autonom durch einen geschlossenen Kreislauf aus Log-Analyse, Test-Generierung und validiertem Patching beheben, o...

## Dateien
- keine erkannt

## Checkliste
- [ ] Quellcode lesen
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei committen
- [ ] git push origin chore/issue-60-09-killer-feature-autonomous-self

## Commit-Template
<typ>: <beschreibung> (closes #60)

## PR-Befehl
python3 agent_start.py --pr 60 --branch chore/issue-60-09-killer-feature-autonomous-self --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/60
