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
# Issue #16 — _build_metadata() — Token-Schätzung + aufklappbarer Block
Status: 🔧 READY — Implementierung starten
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-16-_build_metadata-—-token-sch-tzung-+

## Ziel
## Problem

`_build_metadata()` gibt aktuell eine einzeilige Inline-Zusammenfassung zurück.
Kein aufklappbarer Block, keine Token-Schätzung, keine Dateianzahl.

---

## Änderung

**1. Aufklappbarer Bl...

## Dateien
- keine erkannt
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin chore/issue-16-_build_metadata-—-token-sch-tzung-+

## Commit-Template
<typ>: <beschreibung> (closes #16)

## PR-Befehl
python3 agent_start.py --pr 16 --branch chore/issue-16-_build_metadata-—-token-sch-tzung-+ --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/16
