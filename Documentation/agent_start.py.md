# agent_start.py — Workflow-Steuerung

## Übersicht

Zentrales CLI für den gitea-agent. Koordiniert Issue-Scan, PR-Erstellung, Eval und Watch-Modus.

## Befehle

| Befehl | Beschreibung |
|---|---|
| (ohne Argumente) | Auto-Scan — scannt Gitea nach `ready-for-agent` Issues |
| `--pr NR` | PR erstellen (nach Eval) |
| `--eval [NR]` | Eval ausführen + ggf. Kommentar posten |
| `--watch` | Periodischer Eval-Loop mit Auto-Issues |
| `--interval MIN` | Watch-Interval in Minuten (Default: aus agent_eval.json) |
| `--force` | PR auch bei Staleness-Warnung erzwingen |
| `--restart-before-eval` | Server vor Eval neustarten |

## Watch-Modus

```
cmd_watch()
  └── loop alle N Minuten:
        ├── evaluation.run(PROJECT, trigger="watch")
        ├── _close_resolved_auto_issues() — schließt geheilte Issues
        └── für jeden failed_test:
              ├── Duplikat-Check (_auto_issue_exists)
              └── _build_auto_issue_body() → gitea.create_issue()
```

### Auto-Issue Body (`_build_auto_issue_body`)

Erzeugt strukturierten Markdown mit:

1. **Einfache Tests** — Tabelle `Erwartet | Ergebnis`
2. **Steps-Tests** — Step-Tabelle mit ✅/❌ für jeden Schritt + fehlgeschlagener Step-Index
3. **Kategorie** — regelbasiert aus `evaluation._categorize()` (kein LLM)
4. **Letzte 3 Scores** — aus `tests/score_history.json`

Beispiel-Output für einen Steps-Test:

```markdown
## [Auto] Kontext-Persistenz fehlgeschlagen

**Test:** Kontext-Persistenz (Gewicht 2)
**Score:** 5/7 (Baseline: 7)
**Letzter Commit:** `abc1234 fix: ...`

**Step 2/2 fehlgeschlagen**

| Schritt | Nachricht | Erwartet | Ergebnis |
|---------|-----------|----------|----------|
| 1 | `Mein Name ist Max` | (gespeichert) | ✅ OK |
| 2 | `Wie heiße ich?` | `Max` | ❌ `Ich weiß es nicht` |

**Kategorie:** `keyword_miss`

**Letzte 3 Scores:**
```
2026-03-21 14:30 | 5/7 | watch  | ✗
2026-03-21 12:00 | 7/7 | pr     | ✓
2026-03-20 22:15 | 7/7 | watch  | ✓
```
```

### Deduplication

Pro fehlgeschlagenem Test wird nur **ein** offenes `[Auto]`-Issue gehalten.
`_auto_issue_exists()` prüft via Gitea API ob bereits ein offenes Issue mit gleichem Titel existiert.

Bei Erholung (Test besteht wieder) schließt `_close_resolved_auto_issues()` das Issue automatisch.

## Änderungshistorie

- 2026-03-21 | #29: `_build_auto_issue_body()` — strukturierter Auto-Issue Body mit Tabelle, Step-Tracking, Kategorie, 3 Scores (closes #29)
