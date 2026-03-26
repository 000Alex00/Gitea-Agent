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

---
# Issue #30 — pr soll vor Eval prüfen ob Server-Code aktuell ist
Status: 🔧 READY — Implementierung starten
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-30-pr-soll-vor-eval-pr-fen-ob-server-c

## Ziel
--pr soll vor Eval prüfen ob Server-Code aktuell ist
Problem
--pr führt Eval gegen den laufenden Server aus — ohne zu prüfen, ob der Server den aktuellen Code hat.
Szenario:

Code geändert + comm...

## Dateien
- keine erkannt
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin chore/issue-30-pr-soll-vor-eval-pr-fen-ob-server-c

## Commit-Template
<typ>: <beschreibung> (closes #30)

## PR-Befehl
python3 agent_start.py --pr 30 --branch chore/issue-30-pr-soll-vor-eval-pr-fen-ob-server-c --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/30
