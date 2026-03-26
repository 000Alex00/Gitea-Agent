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
# Issue #11 — Docs: README + COOKBOOK aktualisieren — #6/#8 Details + log_analyzer Rezept
Status: 🔧 READY — Implementierung starten
Risiko: 1/4 — NIEDRIG — Dokumentation/Cleanup
Branch: docs/issue-11-docs-readme-+-cookbook-aktualisiere

## Ziel
## Kontext

Nach Issue #6 (Prozess-Enforcement) und #8 (Output-Validierung) sind README und COOKBOOK unvollständig. Neue Funktionen sind zu vage oder gar nicht dokumentiert.

## Änderungen

### README...

## Dateien
- README.md
- Documentation/COOKBOOK.md
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin docs/issue-11-docs-readme-+-cookbook-aktualisiere

## Commit-Template
<typ>: <beschreibung> (closes #11)

## PR-Befehl
python3 agent_start.py --pr 11 --branch docs/issue-11-docs-readme-+-cookbook-aktualisiere --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/11
