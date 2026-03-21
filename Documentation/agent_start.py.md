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

## Kontext-Loader (`cmd_implement`)

`cmd_implement()` kombiniert drei Quellen um `files.md` möglichst vollständig zu befüllen:

| Quelle | Funktion | Beschreibung |
|---|---|---|
| Backtick-Erwähnungen | `relevant_files()` | Dateipfade direkt im Issue-Text |
| Import-Analyse | `_find_imports()` | AST-Walk über Python-Dateien → `from x import y` → Kandidaten |
| Keyword-Suche | `_search_keywords()` | grep über Backtick-Wörter (≥4 Zeichen) im Repo |

**`_find_imports(files, depth=1)`** — stdlib, nur `.py`:
- Parsed jede Datei mit `ast.parse()`
- Sucht `ImportFrom`-Nodes → löst Pfad relativ zu `PROJECT` auf
- `depth=1` — nur direkte Imports, keine transitive Kette
- Gibt nur existierende Dateien zurück die nicht bereits in `files` sind

**`_search_keywords(issue_text, repo_path)`** — stdlib (`re` + `Path.read_text`):
- Extrahiert Wörter aus Backtick-Spans (≥4 Zeichen, alphanumerisch)
- Durchsucht alle `_KEYWORD_SEARCH_EXTENSIONS`-Dateien (`.py .js .ts .sh .yaml .yml .json`)
- Ignoriert Verzeichnisse via `_get_exclude_dirs(repo_path)`: Default aus `_EXCLUDE_DIRS_DEFAULT` + projektspezifische Einträge aus `agent/config/agent_eval.json → context_loader.exclude_dirs`
- Ignoriert Dateien in `_EXCLUDE_FILES`: `package-lock.json`, `yarn.lock`, `output.json`, Lock-Dateien, `*.min.js`, `*.map`

**Größen-Cap in `save_implement_context()`:**
- Dateien > `_MAX_FILE_SIZE_KB` (50KB) werden auf 500 Zeilen gekürzt mit `[GEKÜRZT: N Zeilen, XKB]`-Hinweis
- Dateien > `MAX_FILE_LINES` (300) werden zeilenbasiert gekürzt

**files.md Header** signalisiert dem LLM Vollständigkeit:
```
> Automatisch erkannt via Backtick-Erwähnungen, Import-Analyse (AST) und Keyword-Suche (grep).
> Zusätzliche Suche im Repo ist nicht nötig — der Kontext ist vollständig.
```

**starter.md** enthält zusätzlich einen `## Kontext`-Block mit der Anweisung, nicht selbst im Repo zu suchen.

## Änderungshistorie

- 2026-03-21 | feat: `_get_exclude_dirs(project)` — konfigurierbare Excludes aus `agent_eval.json → context_loader.exclude_dirs`; `_EXCLUDE_DIRS` → `_EXCLUDE_DIRS_DEFAULT`
- 2026-03-21 | feat: `_issue_dir()` → `contexts/open/`; `_find_issue_dir()` mit Fallback auf alte Struktur
- 2026-03-21 | fix: `_EXCLUDE_FILES` Blacklist + `_MAX_FILE_SIZE_KB` 50KB-Cap in `save_implement_context()`
- 2026-03-21 | fix: `_EXCLUDE_DIRS` erweitert (Backup, vendor, Documentation, contexts, .claude)
- 2026-03-21 | fix: `_find_imports()` depth=1 — keine transitive Import-Kette mehr
- 2026-03-21 | fix: `_KEYWORD_SEARCH_EXTENSIONS` statt `CODE_EXTENSIONS` — .md-Dateien aus Keyword-Suche raus
- 2026-03-21 | fix: `branch_name()` — Sonderzeichen robust filtern via `re.sub(r'[^a-z0-9-]', '-', slug)`
- 2026-03-21 | fix: `import time` fehlte — Watch-Modus crashed mit NameError
- 2026-03-21 | #33: `_find_imports()` + `_search_keywords()` — Kontext-Loader für files.md (closes #33)
- 2026-03-21 | #29: `_build_auto_issue_body()` — strukturierter Auto-Issue Body mit Tabelle, Step-Tracking, Kategorie, 3 Scores (closes #29)
