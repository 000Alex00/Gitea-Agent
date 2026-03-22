# evaluation.py — Generisches Eval-System

## Warum

Vor jedem PR prüft der Agent ob das Zielprojekt noch funktioniert.
Ohne Eval könnte eine Änderung bestehende Features still brechen — der PR würde trotzdem erstellt.

## Architektur

```
cmd_pr()
  └── evaluation.run(PROJECT)
        ├── SKIP  → kein tests/agent_eval.json → Workflow unverändert
        ├── WARN  → server offline → PR trotzdem erstellt
        └── RUN   → Tests ausführen → Score vs. Baseline
              ├── PASS (score >= baseline) → PR wird erstellt
              └── FAIL (score < baseline)  → PR blockiert, Gitea-Kommentar
```

## Konfiguration im Zielprojekt

`agent/config/agent_eval.json` — liegt im Zielprojekt unter `agent/config/` (neu seit #35), Fallback: `tests/agent_eval.json`:

```json
{
  "server_url": "http://192.168.1.x:8000",
  "chat_endpoint": "/chat",
  "pi5_url": "http://192.168.1.x:1235",
  "tests": [
    {
      "name": "Routing einfach",
      "weight": 1,
      "pi5_required": false,
      "message": "Was ist 2 plus 2?",
      "expected_keywords": ["4"]
    },
    {
      "name": "Stilles Failure",
      "weight": 2,
      "pi5_required": true,
      "steps": [
        {"message": "Mein Lieblingstier ist ein Pinguin", "expect_stored": true},
        {"message": "Was ist mein Lieblingstier?", "expected_keywords": ["Pinguin"]}
      ]
    }
  ]
}
```

### Test-Felder

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `name` | ja | Anzeigename |
| `weight` | ja | Gewichtung im Score |
| `message` | ja* | Nachricht an server.py (`*` außer bei `steps`) |
| `expected_keywords` | nein | Alle Keywords müssen in Antwort vorkommen (case-insensitive) |
| `expect_stored` | nein | Nur Antwort erwarten, kein Keyword-Check (Fakt schreiben) |
| `pi5_required` | nein | Pi5 offline → Test überspringen statt FAIL |
| `steps` | nein | Mehrstufiger Test (sequenziell) — ersetzt `message` |

### steps-Format

Für Tests die mehrere Nachrichten sequenziell brauchen (z.B. Fakt schreiben → abfragen):

```json
"steps": [
  {"message": "Ich heiße Max", "expect_stored": true},
  {"message": "Wie heiße ich?", "expected_keywords": ["Max"]}
]
```

## Baseline

`agent/data/baseline.json` — wird **automatisch** beim ersten Lauf angelegt (Fallback: `tests/baseline.json`):

```json
{"score": 8.0}
```

- Erster Lauf → immer PASS, Baseline gespeichert
- Folgeläufe → Score >= Baseline → PASS, Score < Baseline → FAIL
- Manuell zurücksetzen: `python3 evaluation.py --update-baseline --project /pfad/projekt`

`baseline.json` gehört in `.gitignore` — sie ist laufzeitgeneriert.

## Erreichbarkeits-Logik

| Zustand | Verhalten |
|---|---|
| `server_url` offline | Abbruch mit Warnung — kein FAIL, PR wird erstellt |
| `pi5_url` offline | Pi5-Tests überspringen, Rest läuft durch |
| Kein `agent_eval.json` | Silent Skip — Workflow komplett unverändert |

## Score-Berechnung

Gewichtetes Binär: jeder Test ist bestanden (volles Gewicht) oder nicht (0).

```
score = sum(weight für bestandene Tests)
max   = sum(aller weights)
PASS  wenn score >= baseline_score
```

## Standalone-Aufruf

```bash
# Einmalig ausführen (z.B. nach Kalibrierung)
python3 evaluation.py --project /home/user/myproject

# Baseline neu setzen
python3 evaluation.py --project /home/user/myproject --update-baseline
```

## Kontext-Isolation

Pro Eval-Lauf wird eine einmalige `eval-<uuid>`-User-ID generiert.
Verhindert dass Tests sich gegenseitig über den Chat-Kontext (ChromaDB, History) beeinflussen.

## TestResult-Felder

| Feld | Typ | Beschreibung |
|---|---|---|
| `name` | str | Testname aus agent_eval.json |
| `weight` | int | Gewichtung |
| `passed` | bool | Ergebnis |
| `skipped` | bool | Pi5-Test übersprungen |
| `reason` | str | Fehlergrund (menschenlesbar) |
| `category` | str | Regelbasierte Fehler-Kategorie (s.u.) |
| `actual_response` | str | Tatsächliche LLM-Antwort (leer bei None) |
| `step_details` | list | Bei steps-Tests: Liste von `{msg, expected, actual, passed, stored}` |

## Fehler-Kategorien (`_categorize`)

Objektiv — kein LLM, nur regelbasiert:

| Kategorie | Bedingung |
|---|---|
| `timeout` | `response is None` |
| `server_error` | Antwort enthält HTTP-Fehlercode (500/502/503/504) |
| `empty_response` | Antwort leer nach strip() |
| `keyword_miss` | Antwort vorhanden, aber `expected_keywords` fehlen |
| `pi5_offline` | Test wegen Pi5-Offline übersprungen |

## Consecutive-Pass Gate (Auto-Issue Schließen)

Seit Issue #50: Auto-Issues werden erst geschlossen, wenn der zugehörige Test **N-mal hintereinander** bestanden hat — nicht beim ersten Pass.

### Konfiguration

`agent_eval.json` im Zielprojekt:

```json
{
  "close_after_consecutive_passes": 3
}
```

| Wert | Verhalten |
|---|---|
| `1` (Default) | Bisheriges Verhalten — sofort schließen beim ersten Pass |
| `3` | Test muss 3x hintereinander bestehen bevor Issue geschlossen wird |

### Ablauf

1. Watch-Loop erkennt: Test besteht, passendes `[Auto]`-Issue ist offen
2. Zählt aufeinanderfolgende Passes rückwärts aus `score_history.json`
3. `count < threshold` → Fortschritts-Kommentar: `"⏳ Test besteht (2/3) — warte auf Bestätigung"`
4. `count >= threshold` → Issue wird geschlossen
5. Kommentar-Dedup: gleicher Zählerstand wird nicht doppelt gepostet

### Beispiel-Timeline

```
Zyklus 1: "Stilles Failure" FAIL  → Auto-Issue #42 erstellt
Zyklus 2: "Stilles Failure" PASS  → Kommentar "⏳ Test besteht (1/3)"
Zyklus 3: "Stilles Failure" PASS  → Kommentar "⏳ Test besteht (2/3)"
Zyklus 4: "Stilles Failure" PASS  → Issue #42 geschlossen (3/3 erreicht)
```

## Änderungshistorie

- 2026-03-21 | fix: `_resolve_path()` + `_resolve_config()` — `Path()` fehlte bei str `project_root` (TypeError)
- 2026-03-21 | #35: Pfade auf `agent/config/` + `agent/data/` umgestellt via `_resolve_path()` / `_resolve_config()` (closes #35)
- 2026-03-21 | #29: `TestResult` + `category`/`actual_response`/`step_details`; `_categorize()` helper; `_run_steps()` gibt Step-Details zurück (closes #29)
- 2026-03-22 | #50: `close_after_consecutive_passes` — Auto-Issues erst nach N aufeinanderfolgenden Passes schließen (closes #50)
