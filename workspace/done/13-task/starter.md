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
# Issue #13 — Abschluss-Kommentar — Eval-Ergebnis + Metadata + Session-Status
Status: 🔧 READY — Implementierung starten
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-13-abschluss-kommentar-—-eval-ergebnis

## Ziel
Titel: Abschluss-Kommentar — Eval-Ergebnis + Metadata + Session-Status

Problem:
Im Abschluss-Kommentar nach PR-Erstellung fehlen drei wichtige Informationen:
1. Eval-Ergebnis ist nur indirekt aus...

## Dateien
- keine erkannt
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin chore/issue-13-abschluss-kommentar-—-eval-ergebnis

## Commit-Template
<typ>: <beschreibung> (closes #13)

## PR-Befehl
python3 agent_start.py --pr 13 --branch chore/issue-13-abschluss-kommentar-—-eval-ergebnis --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/13
