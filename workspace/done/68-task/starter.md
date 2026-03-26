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
# Issue #68 — Titel: AST-Repository-Skelett — repo_skeleton.json bei --issue generieren
Status: 🔧 READY — Implementierung starten
Risiko: 2/4 — MITTEL — (Plan vor Implementierung)
Branch: chore/issue-68-titel-ast-repository-skelett-repo-s

## Ziel
Titel: AST-Repository-Skelett — repo_skeleton.json bei --issue generieren

Ziel
Große Dateien nicht mehr komplett laden — nur Inhaltsverzeichnis
mit Zeilennummern als Planungsgrundlage.

Hinterg...

## Diskussion
— keine —

## Dateien
- keine erkannt
(Quellcode: files.md)

## Checkliste
- [ ] Quellcode lesen (files.md)
- [ ] Änderung vornehmen
- [ ] Nach jeder Datei: git add <datei> && git commit -m "..."
- [ ] git push origin chore/issue-68-titel-ast-repository-skelett-repo-s

## Commit-Template
<typ>: <beschreibung> (closes #68)

## PR-Befehl
python3 agent_start.py --pr 68 --branch chore/issue-68-titel-ast-repository-skelett-repo-s --summary "..."

## Gitea
http://192.168.1.60:3001/Alexmistrator/gitea-agent/issues/68
