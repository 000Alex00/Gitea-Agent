# Issue #6 — Prozess-Enforcement — Kontext-Drift verhindern
Status: 🔧 READY — Implementierung starten
Risiko: 2/4 — MITTEL — Enhancement (Plan vor Implementierung)
Branch: chore/issue-6-prozess-enforcement-—-kontext-drift

## Ziel
## Problem
Nach langen Sessions überspringt das LLM definierte Prozessschritte:
- `curl` statt `agent_start.py --pr`
- Kein Metadata-Block
- Eval nicht gelaufen
- Label-Wechsel vergessen
- Context-Ord...

## Dateien
- keine erkannt
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin chore/issue-6-prozess-enforcement-—-kontext-drift

## Commit-Template
<typ>: <beschreibung> (closes #6)

## PR-Befehl
python3 agent_start.py --pr 6 --branch chore/issue-6-prozess-enforcement-—-kontext-drift --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/6
