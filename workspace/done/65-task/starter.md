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
# Issue #65 — context_export.sh — LLM-agnostischer Kontext-Export + Dual-Repo-Unterstützung
Status: ⏳ Wartet auf Freigabe
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-65-context-export-sh-llm-agnostischer

## Ziel
Titel: context_export.sh — LLM-agnostischer Kontext-Export + Dual-Repo-Unterstützung

Ziel
Ein universelles Skript das für jedes LLM funktioniert
(Claude Code, Gemini CLI, GPT, Copilot, Web-Chats)...

## Dateien
- keine erkannt

## Checkliste
- [ ] Quellcode lesen
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei committen
- [ ] git push origin chore/issue-65-context-export-sh-llm-agnostischer

## Commit-Template
<typ>: <beschreibung> (closes #65)

## PR-Befehl
python3 agent_start.py --pr 65 --branch chore/issue-65-context-export-sh-llm-agnostischer --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/65
