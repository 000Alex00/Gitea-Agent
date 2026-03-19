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

`tests/agent_eval.json` — liegt im Zielprojekt, nicht im gitea-agent:

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

`tests/baseline.json` — wird **automatisch** beim ersten Lauf angelegt:

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
