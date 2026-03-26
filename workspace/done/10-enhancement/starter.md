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
# Issue #10 — Fix: --eval-after-restart Diskrepanz — COOKBOOK vs agent_start.py
Status: 🔧 READY — Implementierung starten
Risiko: 2/4 — MITTEL — Enhancement (Plan vor Implementierung)
Branch: chore/issue-10-fix-eval-after-restart-diskrepanz-—

## Ziel
## Problem

`Documentation/COOKBOOK.md` Rezept #9 beschreibt `--eval-after-restart <NR>` als CLI-Flag:

```bash
python3 agent_start.py --eval-after-restart 42
```

Aber `agent_start.py` hat dieses Fla...

## Dateien
- Documentation/COOKBOOK.md
- agent_start.py
- evaluation.py
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin chore/issue-10-fix-eval-after-restart-diskrepanz-—

## Commit-Template
<typ>: <beschreibung> (closes #10)

## PR-Befehl
python3 agent_start.py --pr 10 --branch chore/issue-10-fix-eval-after-restart-diskrepanz-— --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/10
