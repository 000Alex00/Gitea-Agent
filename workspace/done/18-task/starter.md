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
# Issue #18 — [Audit FAIL] Risiko 1 — Eval wird nicht übersprungen (kein Risk-Gate)
Status: 🔧 READY — Implementierung starten
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-18-[audit-fail]-risiko-1-—-eval-wird-n

## Ziel
**Quelle:** Workflow-Audit Issue #14, Audit 2

## Problem
`cmd_pr()` führt Eval immer aus, unabhängig von der Risikostufe des Issues.
Ein Risk-Gate vor Zeile 981 fehlt.

**Erwartet:** Risikostufe 1 → ...

## Dateien
- agent_start.py
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin chore/issue-18-[audit-fail]-risiko-1-—-eval-wird-n

## Commit-Template
<typ>: <beschreibung> (closes #18)

## PR-Befehl
python3 agent_start.py --pr 18 --branch chore/issue-18-[audit-fail]-risiko-1-—-eval-wird-n --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/18
