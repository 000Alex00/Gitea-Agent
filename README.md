# gitea-agent

**LLM-agnostischer Agent-Workflow für Gitea Issues.**

Verbindet einen LLM-Agenten (Claude Code, Gemini, lokales LLM, …) mit dem Gitea Issue-Tracker:
Issue analysieren → Plan posten → Freigabe einholen → Branch + Implementierung → PR erstellen.

Kein Cloud-Zwang. Keine Abhängigkeiten außer Python 3.10+ Stdlib. Läuft auf kleiner Hardware neben Gitea.

---

## Entstehungsgeschichte

Ich habe ursprünglich an einem privaten lokalen LLM-Chatbot gearbeitet und dabei gemerkt, dass LLMs beim Coden oft unzuverlässig sind: sie überspringen Tests, verändern falsche Dateien, ignorieren Workflows oder halluzinieren neue Pfade.

Ich wollte eigentlich nur verhindern, dass mir das wieder passiert.

Daraus ist — ohne dass ich es geplant habe — ein komplettes AI-Dev-System entstanden: ein autonomer Agent für Gitea, der Issues automatisch in getestete Pull Requests verwandelt, mit echten technischen Schranken, deterministischen Checks und einem vollständigen Eval-System.

Ich bin kein Entwickler (mehr als "Hallo Welt" bekomme ich in Python nicht hin), aber durch viele LLM-Sessions ist daraus ein System geworden, das inzwischen größer ist als ich selbst. Es läuft komplett lokal — bei mir läuft Gitea auf einem Synology NAS, der Agent selbst auf einem Jetson Orin Nano 8 GB.

---

## Was ist das und wozu?

`gitea-agent` ist ein Python-Script (`agent_start.py`), das einen strukturierten Entwicklungs-Workflow zwischen einem Gitea Issue-Tracker und einem LLM-Agenten vermittelt.

**Problem das es löst:** LLM-Agenten (Claude Code, Gemini, …) sind leistungsfähig, aber ohne Struktur fehlt die Rückkopplung zur tatsächlichen Codebasis — sie erfinden Dateipfade, überspringen Tests oder pushen direkt auf main. `gitea-agent` löst das durch **technische Schranken statt Prompt-Regeln**.

**Kernprinzip:** Das Script übernimmt die gesamte Infrastruktur-Arbeit (Issue lesen, Dateien finden, Branch erstellen, Tests laufen, PR öffnen). Der LLM-Agent schreibt nur Code — und nur nach expliziter Freigabe.

**Typischer Einsatz:**
- Selbst-hosting auf einem Raspberry Pi / Server neben dem Gitea-Service
- LLM-Session (z.B. Claude Code, Aider, Gemini CLI) läuft lokal, Script läuft auf dem Server
- Keine Cloud-Abhängigkeit — nur Python 3.10+ Stdlib + Gitea API

---

## Feature-Übersicht

---

### Auto-Modus
`agent_start.py` ohne Argumente scannt alle Gitea-Issues und führt automatisch den jeweils passenden nächsten Schritt aus — Plan posten, Branch erstellen oder Status anzeigen.

```bash
python3 agent_start.py
# → [→] Issue #21 ready-for-agent — poste Plan...
# → [✓] Kommentar gepostet
```

---

### Kontext-Loader
Vor der Implementierung sucht `save_implement_context()` automatisch alle relevanten Dateien — ohne manuelles Angeben. Drei Quellen werden kombiniert:
1. Dateinamen in Backticks im Issue-Text (`\`server.py\``)
2. AST-Import-Analyse: welche Module importieren die genannten Dateien?
3. Keyword-Grep: welche anderen Dateien enthalten die gleichen Begriffe?

Das Ergebnis landet in `starter.md` (Auftrag + Checkliste) und `files.md` (AST-Skelett der betroffenen Dateien mit `--get-slice`-Hinweisen) — fertig für den LLM-Agenten.

```
contexts/21-docs/
├── starter.md   ← Auftrag, Checkliste, Commit-Template, PR-Befehl
├── files.md     ← AST-Skelett (Klassen, Funktionen, Zeilen) + Slice-Hinweise
└── session.json ← protokolliert --get-slice Anforderungen dieser Session
```

> **Token-Einsparung:** `files.md` enthält *keinen* Volltext mehr — nur das AST-Skelett. Für `agent_start.py` (128 KB): von ~32.000 Token auf ~500 Token. Volltext wird bei Bedarf per `--get-slice` nachgeladen.

---

### AST-Repository-Skelett
`--build-skeleton` erstellt einmalig ein projektweites `repo_skeleton.json` aus allen `.py`-Dateien. Kein Größen-Limit. Der Watch-Loop aktualisiert es inkrementell nach jeder Dateiänderung.

```bash
python3 agent_start.py --build-skeleton
# → [✓] repo_skeleton.json geschrieben (7 Dateien, 3684 Zeilen, 75 Symbole)
```

**Skelett-Eintrag (Beispiel):**
```json
{
  "file": "agent_start.py",
  "symbols": [
    { "type": "function", "name": "_check_pr_preconditions", "lines": [1201, 1289], "signature": "def _check_pr_preconditions(number, branch)" },
    { "type": "function", "name": "cmd_build_skeleton",      "lines": [3620, 3650], "signature": "def cmd_build_skeleton()" }
  ]
}
```

**`files.md` im neuen Format (Ausschnitt):**
```
## agent_start.py  (3684 Zeilen)

### Funktionen
- _check_pr_preconditions  [1201–1289]  def _check_pr_preconditions(number, branch)
- cmd_build_skeleton        [3620–3650]  def cmd_build_skeleton()

Für Volltext: python3 agent_start.py --get-slice agent_start.py:1201-1289
```

---

### Codesegment-Strategie — `--get-slice`
Statt kompletter Dateien lädt der Agent exakte Zeilenbereiche nach — on demand, im Kontext, ohne Token-Verschwendung.

```bash
# LLM fordert an:
python3 agent_start.py --get-slice agent_start.py:1201-1289
# → gibt genau diese 89 Zeilen zurück

# Im Kontext-Export (context_export.sh):
> SLICE: agent_start.py:1201-1289
# → script ruft --get-slice auf und gibt Output zurück
```

Jede `--get-slice`-Anforderung wird in `contexts/{N}-*/session.json` protokolliert. Vor dem PR prüft Schritt 8, ob alle geänderten Dateien tatsächlich per Slice angefordert wurden — nicht per Volltext hineingerutscht sind.

---

### SEARCH/REPLACE Protokoll
LLM-agnostisches Patch-Format: kein Diff, keine Koordinaten — nur alten und neuen Textblock. Funktioniert in jedem Chat-LLM, in jeder IDE, in jeder Terminal-Session.

```
<<<<<<< SEARCH
def old_function():
    return "alt"
=======
def old_function():
    return "neu"
>>>>>>> REPLACE
```

```bash
# LLM postet SEARCH/REPLACE als Kommentar ins Gitea-Issue, dann:
python3 agent_start.py --apply-patch 21            # anwenden
python3 agent_start.py --apply-patch 21 --dry-run  # Vorschau ohne Änderung
```

**Sicherheitsnetz:** Jedes Patch wird durch `ast.parse()` gejagt bevor es geschrieben wird — syntaktisch kaputte Patches werden mit Fehlermeldung abgelehnt. `.bak`-Backup immer angelegt.

---

### Diff-Validierung
`--pr` prüft ob das LLM **nur Zeilen im freigegebenen AST-Bereich** geändert hat. Scope-Verletzungen erscheinen als Warnung im Terminal und als Gitea-Kommentar — kein harter Abbruch, aber sichtbar.

```bash
python3 agent_start.py --pr 21 --branch fix/issue-21-xyz --summary "..."
# [!] Diff-Warnung: agent_start.py Zeilen 850-920 außerhalb des freigegebenen Bereichs
#     Issue betraf: Zeilen 1201-1289
#     → Bitte überprüfen ob diese Änderungen zum Issue gehören
```

---

### Gitea-Versionsvergleich
Bei Score-Regression lädt der Agent die alte Dateiversion via Gitea-API und vergleicht AST-Skelette: welche Funktionen wurden hinzugefügt, entfernt oder haben sich in der Größe verändert?

```
## AST-Strukturänderung: nanoclaw/server.py

+ handle_upload  (neu)
- _cleanup_temp  (entfernt)
~ parse_request  (+45 Zeilen, war 67 jetzt 112)
```

Opt-in via `agent_eval.json`:
```json
{ "gitea_version_compare": { "enabled": true } }
```

---

### LLM-agnostischer Kontext-Export
`context_export.sh` exportiert den aufgebauten Kontext für beliebige LLM-Clients — Terminal, Gemini CLI, Web-Chat.

```bash
./context_export.sh 21 --self           # plain Text im Terminal (mit interaktivem Slice-Modus)
./context_export.sh 21 --self gemini    # Gemini CLI direkt starten
./context_export.sh 21 --self file      # context_21.md erzeugen (für Web-Chats: GPT, Claude Web, Gemini Web)
```

**Interaktiver Slice-Modus (plain):**
```
========================================
  SLICE-MODUS — Zeile eingeben:
  SLICE: datei.py:START-END   → Code laden
  READY                       → Starten
========================================
> SLICE: agent_start.py:1201-1289
[gibt Zeilen 1201-1289 aus]
> READY
```

---

### Diskussion im Kontext
Gitea-Kommentare (nur von echten Nutzern, Bot-Kommentare gefiltert) werden in `starter.md` unter `## Diskussion` eingebunden. Der LLM sieht so die vollständige Vorgeschichte des Issues.

```markdown
## Diskussion
**Alex:** Das betrifft auch analyst_worker.py, nicht nur server.py
**Robin:** ok, beide Dateien anpassen
```

---

### Risiko-Klassifikation
Jedes Issue wird anhand seiner Labels automatisch eingestuft. Die Stufe bestimmt den Workflow: Stufe 1 direkt umsetzen, Stufe 2/3 erst planen und `help wanted` setzen, Stufe 4 gar nicht automatisieren.

| Stufe | Label | Vorgehen |
|-------|-------|---------|
| 1 | `docs`, `cleanup` | Plan → Freigabe → Implementierung |
| 2 | `enhancement` | Plan + offene Fragen → `help wanted` → Freigabe |
| 3 | `bug`, `feature_request` | wie Stufe 2, mit Analyse-Kommentar |
| 4 | Breaking Change | kein Auto-Workflow |

---

### Plan-Kommentar + Agent-Metadaten
`--issue <NR>` oder Auto-Modus postet einen strukturierten Plan ins Gitea-Issue — mit Implementierungsvorschlag, betroffenen Dateien und einem `<details>`-Metadaten-Block.

```
[Agent-Analyse] Stufe 2/4 — Enhancement
Vorgeschlagene Änderung: ...
Betroffene Dateien: server.py, router.py
→ Mit 'ok' oder 'ja' kommentieren um zu starten.

<details>
<summary>🤖 Agent-Metadaten</summary>

**Modell:** claude-sonnet-4-6
**Branch:** fix/issue-21-server-crash
**Commit:** abc1234
**Zeitstempel:** 2026-03-20T14:23:00
**Token-Schätzung:** ~4200 (Kontext: files.md, starter.md)
**Gelesene Dateien:** nanoclaw/server.py, nanoclaw/router.py
</details>
```

---

### Freigabe-Pflicht
`--implement` prüft ob ein Gitea-Kommentar mit `ok`, `ja` oder `✅` vorhanden ist. Ohne explizite Freigabe startet nichts.

```bash
python3 agent_start.py --implement 21
# Ohne "ok"-Kommentar: [!] Keine Freigabe — abgebrochen.
# Mit "ok"-Kommentar:  [✓] Freigabe erkannt — Branch erstellen...
```

---

### Branch-Management
Nach Freigabe wird automatisch ein Feature-Branch erstellt, der Branch-Name aus Issue-Typ und -Titel abgeleitet. Label wechselt zu `in-progress`.

```
fix/issue-21-server-crash-bei-leerem-body
docs/issue-14-filter-strings-settings
feat/issue-6-statusmanager
```

---

### Eval-System
`evaluation.py` schickt HTTP-Requests an den laufenden Server und prüft ob die Antworten die erwarteten Keywords enthalten. Tests sind gewichtet — ein kritischer Test zählt mehr als ein Smoke-Test. Schlägt ein Test fehl, wird der PR blockiert.

```json
// agent/config/agent_eval.json
{
  "tests": [
    { "name": "Grundfunktion", "weight": 2, "message": "Was ist 2+2?", "expected_keywords": ["4"], "max_response_ms": 2000 },
    { "name": "Fakten-Speichern", "weight": 1, "steps": [
        { "message": "Mein Name ist Max", "expect_stored": true },
        { "message": "Wie heiße ich?", "expected_keywords": ["Max"] }
    ]}
  ]
}
```

---

### Baseline-Tracking
Nach dem ersten Eval-Lauf wird der Score als Referenz gespeichert (`baseline.json`). Jeder folgende PR muss mindestens diesen Score erreichen. Verbessert sich das System, steigt die Baseline automatisch mit — sinkt aber nie.

```
[Eval] Score: 7/7 (Baseline: 6)  → Baseline auf 7 erhöht
[Eval] Score: 5/7 (Baseline: 7)  → PR blockiert
```

---

### Server-Aktualitäts-Check
Vor dem Eval prüft `_check_server_staleness()` ob der laufende Server überhaupt den aktuellen Code hat — anhand Commit-Zeitstempel vs. Startup-Zeitpunkt im Log. Veraltet → Abbruch mit Anweisung.

```
[!] Server-Code veraltet
    Letzter Commit: 2026-03-20 22:45
    Server gestartet: 2026-03-20 21:20
    → Server neu starten oder --restart-before-eval verwenden.
```

---

### Prozess-Enforcement
`_check_pr_preconditions()` läuft vor jedem PR und prüft Bedingungen technisch — nicht als Prompt-Regel. Schlägt eine fehl, wird der Prozess mit Exit 1 abgebrochen.

| Schritt | Prüfung | Fehler wenn... |
|---------|---------|---------------|
| 1 | Branch ≠ main/master | PR von main verboten |
| 2 | Plan-Kommentar vorhanden | kein Plan im Issue |
| 3 | Metadaten-Block im Plan | Plan ohne `🤖 Agent-Metadaten` |
| 4 | Eval nach letztem Commit | Eval veraltet oder fehlend |
| 5 | Server-Neustart | `restart_script` gesetzt, Eval veraltet |
| 6 | Self-Consistency Check | Agent-Code geändert + Check fehlgeschlagen |
| 7 | Diff-Validierung | geänderte Zeilen außerhalb des Issue-Bereichs (Warnung) |
| 8 | Slice-Warnung | Dateien geändert ohne vorherige `--get-slice`-Anforderung (Warnung) |

---

### Consecutive-Pass Gate
Auto-Issues werden nicht beim ersten Pass geschlossen, sondern erst nach **N aufeinanderfolgenden Passes**. Verhindert Falsch-Positives bei intermittierenden Tests.

```json
// agent_eval.json
{ "close_after_consecutive_passes": 3 }
```

Bei jedem Pass vor Erreichen des Schwellwerts postet der Agent einen Fortschritts-Kommentar:
```
⏳ Test besteht (2/3) — warte auf Bestätigung
```
Standard: `1` (bisheriges Verhalten — sofort schließen).

---

### Betriebsmodi — Night / Patch / Idle
Drei systemd-basierte Modi steuern den Agent-Betrieb. Notebook kann jederzeit zugeklappt werden — keine offene Terminal-Session nötig.

| Modus | Service | Beschreibung |
|---|---|---|
| **NIGHT** | `gitea-agent-night` | Autonomer Betrieb: Watch, Eval, Auto-Issues, Log-Analyse |
| **PATCH** | `gitea-agent-patch` | Aktive Entwicklung: Watch mit `--patch` (keine Auto-Issues) |
| **IDLE** | — | Alles gestoppt |

```bash
# Ersteinrichtung (einmalig)
python3 agent_start.py --install-service

# Moduswechsel
./start_night.sh    # → Night-Modus (stoppt Patch falls aktiv)
./start_patch.sh    # → Patch-Modus (stoppt Night falls aktiv)
./stop_agent.sh     # → IDLE
./agent_status.sh   # → Modus, Laufzeit, Score, offene Issues
```

Das Dashboard wird nicht nur im Watch-Takt aktualisiert, sondern sofort nach jedem signifikanten Event (PR-Abschluss, Auto-Issue erstellt/geschlossen, Server-Neustart).

---

### Watch-Modus & Patch-Modus
`--watch` startet eine periodische Eval-Schleife — entweder via systemd (empfohlen) oder manuell in tmux. Bei Regression → automatisches Bug-Issue in Gitea. Erholt sich der Score → Issue wird nach N Passes geschlossen (siehe Consecutive-Pass Gate).

```bash
# Empfohlen: via Betriebsmodi-Skripte (systemd)
./start_night.sh    # oder ./start_patch.sh

# Alternativ: manuell
tmux new -s watch
python3 agent_start.py --watch --interval 30  # alle 30 Minuten
# Ctrl+B, D zum Detachen
```

Auto-Issues enthalten: Erwartung vs. Realität, Step-Tabelle mit ✅/❌, Fehler-Kategorie, letzte 3 Scores. Duplikate werden verhindert (gleicher Titel + offen = kein neues Issue).

Wenn du intensiv am Code entwickelst und oft kaputten Code eincheckst, kannst du den **Patch-Modus** aktivieren (`--watch --patch`).
Im Patch-Modus:
1. Werden **keine** automatischen Gitea-Issues erstellt.
2. Werden **Neustarts sofort durchgeführt** (die `inactivity_minutes` werden übersprungen).
3. Wird bei jedem Lauf ein Live-Dashboard (`dashboard.html`) für dich generiert.

---

### Systematische Fehler-Erkennung (Tag-Aggregation)
Der Watch-Modus analysiert nach jedem Lauf die `score_history.json` und erkennt Muster über mehrere Läufe hinweg.
Wenn Tests mit dem gleichen `tag` wiederholt fehlschlagen, wird automatisch ein Issue erstellt: `[Auto-Improvement] Systematische Schwäche bei Tag: <tag>`.

**Konfiguration in `agent_eval.json`:**
```json
{
  "tag_failure_threshold": 3,
  "tag_failure_window": 5,
  "affected_files": {
    "chroma_retrieval": ["agent/utils/retriever.py", "agent/config/chroma.yaml"]
  },
  "improvement_hints": {
    "chroma_retrieval": "Vector-Search Parameter prüfen oder Embeddings neu generieren."
  }
}
```
*   `tag_failure_threshold` / `tag_failure_window`: Erstellt ein Issue, wenn ein Tag in X der letzten Y Läufe mindestens einen Fehler hatte.
*   `improvement_hints`: Eigener Text, der als Lösungsvorschlag (Hebel) in das Auto-Issue eingefügt wird.
*   `affected_files`: Optionale Liste von Dateien, die bei diesem Tag als relevant markiert werden sollen.

---

### Performance-Benchmarking
Das Eval-System misst automatisch die Latenz (Antwortzeit in Millisekunden) jedes Tests.
Optional kann in der `agent_eval.json` pro Test ein `max_response_ms`-Limit gesetzt werden.
Wird dieses Limit im Watch-Modus überschritten, erstellt der Agent automatisch ein Issue mit dem Label `[Auto-Perf]`, um eine Regression der Performance zu signalisieren.
Die gemessenen Latenzen werden zudem fortlaufend in der `score_history.json` dokumentiert.

---

### Auto-Neustart (Watch)
Zusätzlich zur Eval-Schleife prüft Watch ob ein Neustart sinnvoll ist:
- Chat seit ≥ `inactivity_minutes` inaktiv (aus Log gelesen)
- Neue Commits seit letztem Eval vorhanden

Beide Bedingungen erfüllt → `restart_script` wird ausgeführt, danach sofort Eval.

```json
// agent_eval.json
{ "restart_script": "/home/user/projekt/start.sh", "inactivity_minutes": 5 }
```

---

### Label-Lifecycle
Alle Labels werden vom Script gesetzt und entfernt — kein manuelles Label-Management nötig (außer `help wanted` entfernen bei Stufe 2/3 nach Klärung).

```
ready-for-agent → agent-proposed → in-progress → needs-review
                      ↓ (Stufe 2/3)
                  help wanted (offene Fragen) → agent-proposed (nach Klärung)
```

---

### Session-Tracking
`contexts/session.json` zählt abgeschlossene Issues pro LLM-Session. Ab `SESSION_LIMIT` (Standard: 2) erscheint eine Warnung im PR-Kommentar — LLM-Kontext-Drift wird wahrscheinlicher je mehr Issues in einer Session bearbeitet wurden.

```
🟢 Session 1/2 — Kontext frisch
🟡 Session 2/2 — neue Session empfohlen
🔴 Session 3/2 — Drift-Risiko: neue LLM-Session starten
```

---

### PFLICHTREGELN in starter.md
Jede `starter.md` enthält automatisch einen unveränderlichen Regelblock am Anfang. Ziel: LLM-Agenten die per Drift anfangen `curl` statt `agent_start.py` zu benutzen oder Schritte zu überspringen, werden durch explizite Checklisten gebremst.

```markdown
⚠️ NIEMALS `curl` statt `agent_start.py` verwenden
⚠️ NIEMALS Schritte überspringen
⚠️ NIEMALS PR manuell erstellen
- [ ] Vorheriger Schritt vollständig abgeschlossen?
- [ ] agent_start.py verwendet (nicht curl)?
```

---

### Kontext-Kommentar
Nach `--implement` postet der Agent eine Zusammenfassung des aufgebauten Kontexts als Gitea-Kommentar — welche Dateien gefunden wurden, wie viele Diskussions-Kommentare einbezogen wurden, welche Keywords aus Kommentaren extrahiert wurden.

```
## 📎 Kontext-Loader
**Erkannte Dateien (5):**
- `nanoclaw/server.py`
- `nanoclaw/router.py`
**Diskussion:** 2 Kommentar(e) einbezogen
---
_Kontext bereit in starter.md + files.md_
```

---

### Score-History
Jeder Eval-Lauf (PR, Watch, manuell, nach Neustart) wird in `score_history.json` protokolliert (max. 90 Einträge). Die letzten 5 Einträge werden automatisch an den PR-Kommentar angehängt.

```
| Datum       | Score | Trigger |
|-------------|-------|---------|
| 2026-03-20  | 7/7   | pr      |
| 2026-03-19  | 6/7   | watch   |
| 2026-03-18  | 7/7   | restart |
```

---

### Docs-Check
`--pr` prüft automatisch ob Dateien unter `Documentation/` seit dem Branch-Abzweig von main geändert wurden. Falls nicht → Warnung im Terminal und Gitea-Kommentar. Kein Hard-Block — nur Hinweis.

```
[!] Warnung: Code geändert aber keine Documentation/*.md aktualisiert.
```

---

### Auto-Cleanup
Beim jedem Auto-Scan vergleicht der Agent die lokalen `contexts/open/`-Ordner mit den tatsächlich offenen Gitea-Issues. Geschlossene Issues werden automatisch nach `contexts/done/` verschoben — kein manuelles Aufräumen.

```
contexts/open/13-enhancement/  →  contexts/done/13-enhancement/
```

---

### Agent Self-Consistency Check
Vor jedem PR, der den Agenten-Code selbst betrifft, läuft ein automatischer Selbst-Check (`agent_self_check.py`). Dieser deterministische Test stellt sicher, dass die interne Logik des Agenten konsistent ist. Er prüft u.a.:
- Sind alle in `settings.py` definierten Gitea-Labels im Projekt vorhanden?
- Haben alle CLI-Flags in `agent_start.py` eine zugehörige Handler-Funktion?
- Sind alle Umgebungsvariablen in der `.env.example` dokumentiert?

Schlägt der Check fehl, wird der PR blockiert, um unvollständige Implementierungen zu verhindern.

---

### LLM-gestützte Test-Generierung
Der Befehl `--generate-tests <NR>` automatisiert die Erstellung von Testfällen. Der Agent sammelt den gesamten relevanten Kontext zu einem Issue (Code, Imports, Diskussion) und generiert einen System-Prompt. Dieser Prompt weist ein LLM an, passende `pytest`-Unit-Tests und `agent_eval.json`-Integrationstests zu schreiben.

**Besonderheit:** Der Prompt erzwingt die Verwendung von `tag`s in den `agent_eval.json`-Tests, um eine systematische Fehleranalyse zu ermöglichen.

---

### LLM-gestützte Log-Analyse
Der projektspezifische `log_analyzer.py`, der vom Watch-Modus aufgerufen wird, kann optional mit LLM-Unterstützung erweitert werden. Ist dies konfiguriert, sendet der Analyzer bei unbekannten Fehlermustern den Log-Kontext an ein LLM.

**Kontext-Anreicherung:** Der Prompt wird automatisch mit Informationen aus der `score_history.json` angereichert, um dem LLM Hinweise auf systematisch fehlschlagende Test-Tags zu geben. Dies ermöglicht gezieltere Hypothesen zur Fehlerursache.

---

### Auto-Changelog-Generator
Der Befehl `--changelog [VERSION]` generiert oder aktualisiert `CHANGELOG.md` automatisch aus der Git-History.

**Ablauf:**
1. Liest alle Commits seit dem letzten Git-Tag (`git describe --tags`)
2. Klassifiziert Commits nach [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `perf:`, `ci:`, `style:`
3. Commits ohne Präfix landen unter "Sonstiges"
4. Schreibt/prependet einen neuen Abschnitt in `CHANGELOG.md`

**Verwendung:**
```bash
python3 agent_start.py --changelog            # Version: "Unreleased"
python3 agent_start.py --changelog 1.2.0      # Versionierter Release-Eintrag
```

**PR-Integration:** `--pr` aktualisiert `CHANGELOG.md` automatisch nach dem PR-Post (als "Unreleased"). Fehler dabei sind nicht blockierend.

**Format-Beispiel:**
```markdown
## [1.2.0] — 2026-03-24

### Features
- Neue API-Route für Webhooks (`a1b2c3d4`)

### Bugfixes
- Race condition in Watch-Loop behoben (`e5f6a7b8`)
```

---

### Live-Dashboard
Für die lokale Entwicklung generiert der Agent eine `dashboard.html`. Diese Seite bietet eine Live-Übersicht über den Systemzustand und wird im `--watch`-Modus automatisch bei jedem Lauf aktualisiert. Sie kann auch manuell mit `--dashboard` erstellt werden.

**Inhalt:**
- **Score-Verlauf:** Interaktiver Chart der letzten 24 Stunden.
- **System-Status:** Live-Ping von Server und Backend-Workern.
- **Fehleranalyse:** Tabellen der letzten Fehler und systematisch fehlschlagender Test-Tags.

---

### Health-Check — `--doctor`
Vollständige Zustandsprüfung in einem Befehl: Gitea-Verbindung, Repository, Labels, `.env`, `agent_eval.json`, Skeleton-Aktualität.

```bash
python3 agent_start.py --doctor
# → [✓] Gitea-Verbindung OK
# → [✓] Repository gefunden
# → [✓] Labels vollständig (6/6)
# → [!] agent_eval.json: server_url nicht erreichbar
```

Jeder Check wird einzeln ausgewertet — fehlende Konfiguration wird mit Hinweis auf den entsprechenden Setup-Schritt ausgegeben.

---

### Setup-Wizard — `--setup`
Interaktiver 6-Schritt-Wizard für die vollständige Ersteinrichtung — ohne manuelle `.env`-Arbeit.

```bash
python3 agent_start.py --setup
```

Schritt für Schritt: Gitea-Verbindung testen → Repository prüfen → Projektverzeichnis setzen → fehlende Labels anlegen → `agent_eval.json` erstellen → `.env` schreiben. Endet automatisch mit `--doctor` zur Verifikation. Details: [COOKBOOK Kapitel 19](Documentation/COOKBOOK.md#19-setup-wizard-issue-77).

---

### Plugin-Architektur
`agent_start.py` lagert isolierte Funktionsgruppen in `plugins/` aus — sauber trennbar, einzeln testbar, erweiterbar.

```
plugins/
├── patch.py      # SEARCH/REPLACE Protokoll (cmd_apply_patch)
└── changelog.py  # Changelog-Generator (cmd_changelog)
```

Eigene Plugins folgen demselben Muster: neue Datei in `plugins/`, Import in `agent_start.py`. Details: [COOKBOOK Kapitel 20](Documentation/COOKBOOK.md#20-plugin-architektur-patch--changelog-issue-79).

---

## Schnellstart

```bash
git clone https://github.com/Alexander-Benesch/Gitea-Agent
cd Gitea-Agent
python3 agent_start.py --setup   # Interaktiver Wizard: .env + Labels + Verifikation
```

Keine zusätzlichen Abhängigkeiten — nur Python 3.10+ Stdlib.

---

## Schritt-für-Schritt Anleitung

### 1. Issue schreiben

In Gitea ein neues Issue anlegen. Im Body die betroffenen Dateien in Backticks erwähnen — der Agent erkennt sie automatisch und ergänzt zusätzlich via Import-Analyse (AST) und Keyword-Suche (grep):

```
Bitte Docstrings in `nanoclaw/fact_extractor.py` ergänzen.
```

---

### 2. Label setzen: `ready-for-agent`

Das Label signalisiert dem Agent, dass das Issue bearbeitet werden soll.

Gitea → Issue → Labels → `ready-for-agent` setzen.

---

### 3. Agent starten

Im Terminal (im `gitea-agent`-Verzeichnis):

```bash
python3 agent_start.py
```

Der Agent scannt alle Issues und verarbeitet sie der Reihe nach:

**Konsolenausgabe (Beispiel):**
```
======================================================================
  GITEA AGENT — AUTO-SCAN
======================================================================

[→] 1 Issue(s) bereit — poste Pläne:

  → #21 (Stufe 1) Docstrings in fact_extractor.py ergänzen

[✓] Kommentar gepostet: http://gitea/repo/issues/21
[→] Freigabe: mit 'ok' oder 'ja' kommentieren
```

In Gitea erscheint jetzt automatisch ein Kommentar mit dem Implementierungsplan.

---

### 4. Plan prüfen und freigeben

Gitea → Issue → Kommentar des Agents lesen → mit `ok`, `ja` oder `✅` antworten.

---

### 5. Implementierung starten

Erneut im Terminal:

```bash
python3 agent_start.py
```

Der Agent erkennt die Freigabe und gibt aus:

```
[✓] Freigabe erhalten — starte Implementierung.
[✓] Branch 'docs/issue-21-...' erstellt.
```

**In der LLM-Session** (Claude Code, Aider, Gemini CLI, …) eintippen:

```
prüf Issues / starte Agent / run agent_start.py
```

Das LLM führt das Script aus, liest den Output und startet die Implementierung — ohne weiteren manuellen Eingriff.

---

### 6. PR wird automatisch erstellt

Nach der Implementierung:

```bash
python3 agent_start.py --pr 21 --branch docs/issue-21-xyz --summary "- Docstrings ergänzt"
```

Der Agent führt vor dem PR-Erstellen automatisch das Eval-System aus — **nur bei Risiko ≥ 2** (Docs-PRs sind bewusst ausgenommen, da sie kein Verhalten ändern):

| Risiko | Eval |
|---|---|
| 1 — Docs/Cleanup | Übersprungen |
| 2 — Enhancement | ✅ läuft |
| 3 — Bug/Feature | ✅ läuft |

| Ergebnis | Verhalten |
|---|---|
| Kein `agent_eval.json` | Übersprungen — PR wird normal erstellt |
| server offline | Warnung — PR wird trotzdem erstellt |
| Eval-Fehler (Bug in evaluation.py) | Warnung ins Issue — PR wird trotzdem erstellt |
| PASS (score >= baseline) | PR wird erstellt |
| FAIL (score < baseline) | PR blockiert, Kommentar ins Issue |

Danach:
- postet einen Abschluss-Kommentar ins Issue
- setzt das Label auf `needs-review`

---

### 7. Review und Merge

PR in Gitea reviewen → mergen → Issue schließen. Fertig.

---

## Eval-System

`evaluation.py` prüft vor jedem PR ob das Zielprojekt noch korrekt funktioniert. Schlägt ein Test fehl, wird der PR blockiert.

### Voraussetzung

Im Zielprojekt muss eine `tests/agent_eval.json` existieren:

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
        {"message": "Mein Name ist Max", "expect_stored": true},
        {"message": "Wie heiße ich?", "expected_keywords": ["Max"]}
      ]
    }
  ]
}
```

### Felder

| Feld | Beschreibung |
|---|---|
| `server_url` | URL des zu testenden Servers |
| `chat_endpoint` | HTTP-POST Endpunkt — wird aus dem Zielprojekt gelesen, nicht hardcodiert |
| `pi5_url` | Optionaler Backend-Worker — wird vorab auf Erreichbarkeit geprüft |
| `watch_interval_minutes` | Interval für `--watch` in Minuten (Standard: 60) — wird von `--interval` CLI-Arg überschrieben |
| `log_path` | Pfad zur Logdatei — von `--watch` für Inaktivitätserkennung (Szenario 2) genutzt |
| `restart_script` | Pfad zum Start-Skript — Watch startet Server automatisch neu bei Inaktivität + neuen Commits |
| `inactivity_minutes` | Schwellwert für Chat-Inaktivität in Minuten, ab dem Neustart getriggert wird (Standard: 5) |
| `log_analysis_interval_minutes` | Interval für Log-Analyse in Watch-Zyklen (projektspezifisch) |
| `close_after_consecutive_passes` | Anzahl aufeinanderfolgender Passes bevor Auto-Issue geschlossen wird (Standard: 1) |
| `gitea_version_compare.enabled` | AST-Diff gegen alte Dateiversion bei Regression (opt-in, Standard: false) |
| `weight` | Gewichtung im Score (1–3) |
| `pi5_required` | Bei `true`: Test wird übersprungen wenn Pi5 offline |
| `message` | Nachricht an den Server |
| `expected_keywords` | Alle Keywords müssen in der Antwort enthalten sein (case-insensitive). Leer `[]` = nur Antwort vorhanden prüfen |
| `expect_stored` | `true` = Antwort darf `null` sein — prüft nur ob Server nicht abstürzt (z.B. beim Einschreiben von Fakten) |
| `steps` | Mehrschrittige Tests: Schritte werden sequenziell mit derselben User-ID ausgeführt, alle müssen bestehen. Zwischen Steps wird 2s gewartet (LLM-Cooldown) |

### Score-Berechnung

Gewichtetes Binär — kein LLM-Judgement:
- Test bestanden → `weight` Punkte
- Test nicht bestanden → 0 Punkte
- `max_score` = Summe aller Gewichte

### Baseline

`tests/baseline.json` enthält den Referenz-Score. Regeln:
- Erster Lauf → Baseline wird automatisch angelegt
- Score ≥ Baseline → PR erlaubt
- Score < Baseline → PR blockiert
- Score > Baseline → Baseline wird **automatisch hochgesetzt** (nie runter)
- `--update-baseline` → manuelle Neusetzung (z.B. nach bewusstem Score-Wechsel durch neuen Test)

`baseline.json` sollte in `.gitignore` stehen — maschinenspezifisch, nicht versionieren.

### Score-History

Jeder Eval-Lauf wird in `tests/score_history.json` protokolliert (max. 90 Einträge). Ältere Einträge werden automatisch verworfen. Feld `trigger` zeigt den Auslöser:

| trigger | Auslöser |
|---|---|
| `pr` | Vor einem PR (`--pr`) |
| `watch` | Watch-Modus (`--watch`) |
| `restart` | Nach Neustart (`--eval-after-restart`) |
| `manual` | Manueller Aufruf (`evaluation.py` direkt) |

Die letzten 5 Einträge werden automatisch an jeden `--pr` Gitea-Kommentar angehängt. Auto-Issues aus dem Watch-Modus enthalten die letzten 3 Einträge.

`score_history.json` sollte in `.gitignore` stehen — maschinenspezifisch, nicht versionieren.

### Verhalten bei Infrastruktur-Problemen

| Situation | Verhalten |
|---|---|
| `server_url` offline | Warnung — Eval übersprungen, PR wird trotzdem erstellt |
| `pi5_url` offline | Pi5-Tests übersprungen, Rest läuft durch |
| Score < Baseline | PR blockiert + Kommentar ins Issue |
| Kein `agent_eval.json` | Eval übersprungen |
| Fehler in `evaluation.py` | Warnung ins Issue — PR wird trotzdem erstellt |

### Baseline verwalten

```bash
# Manuell testen ohne PR
python3 evaluation.py --project /path/to/project

# Baseline neu setzen (nur nach bewusstem Score-Wechsel, z.B. neuer Test hinzugefügt)
python3 evaluation.py --project /path/to/project --update-baseline
```

---

## Workflow-Diagramm

```
Du:     Issue schreiben + Label "ready-for-agent" setzen
        ↓
Script: Plan-Kommentar ins Issue (mit 🤖 Metadaten-Block: Zeitstempel, Tokens, Dateien)
        contexts/{N}-{typ}/starter.md erstellt → Label: agent-proposed
        ↓ (Stufe 2/3 zusätzlich — wenn noch kein Plan vorhanden:)
Script: Analyse-Kommentar + Nächste Schritte ins Issue
        Label "help wanted" gesetzt, "agent-proposed" entfernt
        ↓
Du:     Fragen im Issue beantworten
        python3 agent_start.py --issue {N}  → starter.md mit Kommentarhistorie aktualisiert
        [Wiederholen bis Konzept steht]
        Label "help wanted" manuell entfernen → "ok" kommentieren
        ↓
Script: Freigabe erkannt (help wanted weg + ok) → Branch erstellen
        Label: agent-proposed → in-progress
        Nächste Schritte ins Issue gepostet
        contexts/{N}-{typ}/files.md erstellt (AST-Skelett + Slice-Hinweise)
        ↓
LLM:    Liest starter.md + files.md → fordert Slices an (--get-slice) → implementiert → committet
        ↓
Script: --pr <NR> --branch <branch> --summary "..."
        → Prüft 8 Preconditions (Branch, Plan, Eval, Diff-Scope, Slices, …)
        ↓
        PR erstellt + Abschluss-Kommentar + Label: needs-review
        contexts/{N}-{typ}/ → contexts/done/{N}-{typ}/
        ↓
Du:     PR reviewen + mergen
```

---

## Installation & Konfiguration

### Setup-Wizard (empfohlen)

```bash
python3 agent_start.py --setup
```

Interaktiver 6-Schritt-Wizard: Gitea-Verbindung → Repo → Projektverzeichnis → Labels → `agent_eval.json` → `.env`. Endet automatisch mit `--doctor` zur Verifikation. Details: [COOKBOOK Kapitel 19](Documentation/COOKBOOK.md#19-setup-wizard-issue-77).

### .env befüllen

```bash
cp .env.example .env
```

| Variable | Beschreibung | Beispiel |
|----------|-------------|---------|
| `GITEA_URL` | Gitea-Instanz URL | `http://192.168.1.x:3001` |
| `GITEA_USER` | Gitea-Benutzername | `admin` |
| `GITEA_TOKEN` | API-Token (Settings → Applications) | `abc123...` |
| `GITEA_REPO` | Repository (owner/name) | `admin/myproject` |
| `GITEA_BOT_USER` | Bot-User für Kommentare (optional) | `working-bot` |
| `GITEA_BOT_TOKEN` | API-Token des Bot-Users (optional) | `xyz789...` |
| `PROJECT_ROOT` | Pfad zum Projekt-Repo | `/home/user/myproject` |
| `LLM_API_ENABLED` | LLM-API aktivieren (Vollautomatik) | `false` |
| `ANTHROPIC_API_KEY` | API-Key (Beispiel: Claude/Anthropic) | `sk-ant-...` |

**Token-Scopes:** `issue` (read+write), `repository` (read+write)

**Bot-User (empfohlen):** Separater Gitea-User (`working-bot`) damit Agent-Kommentare klar als Bot erkennbar sind. Nur API-Token nötig — kein SSH/GPG.

### .env.agent (Dual-Repo / --self)

Für den Agent-Selbst-Betrieb (gitea-agent entwickelt gitea-agent):

```bash
# .env.agent
GITEA_URL=http://192.168.1.x:3001
GITEA_USER=youruser
GITEA_TOKEN=...
GITEA_REPO=youruser/gitea-agent
GITEA_BOT_USER=working-bot
GITEA_BOT_TOKEN=...
PROJECT_ROOT=/home/user/gitea-agent
CONTEXT_DIR=/home/user/gitea-agent/contexts
```

Alle `agent_start.py --self`-Befehle und `context_export.sh --self` lesen aus `.env.agent` statt `.env`.

### Textbausteine anpassen

Alle Texte (Plan-Platzhalter, PR-Checkliste, Freigabe-Prompt, Abschluss-Text) sind in `settings.py` zentralisiert und über `.env` überschreibbar. Details: [settings.py](settings.py) und [.env.example](.env.example).

---

## Verwendung

```bash
# Auto-Modus (empfohlen)
python3 agent_start.py

# Manuell:
python3 agent_start.py --list                              # Status-Übersicht
python3 agent_start.py --issue 16                          # Plan posten
python3 agent_start.py --implement 16                      # Nach "ok": Branch
python3 agent_start.py --fixup 16                          # Nach Bugfix: Kommentar + needs-review
python3 agent_start.py --pr 16 --branch fix/issue-16-xyz  # PR erstellen
python3 agent_start.py --pr 16 --branch fix/issue-16-xyz \
  --summary "- X geändert\n- Doku aktualisiert"           # PR mit Zusammenfassung
python3 agent_start.py --pr 16 --branch fix/... --force   # Staleness-Check überspringen
python3 agent_start.py --pr 16 --branch fix/... \
  --restart-before-eval                                    # Server neu starten, dann Eval

# Codesegment-Strategie:
python3 agent_start.py --generate-tests 16                 # Test-Prompt für Issue generieren

# Codesegment-Strategie:
python3 agent_start.py --build-skeleton                    # Projektweites repo_skeleton.json erstellen
python3 agent_start.py --get-slice agent_start.py:100-200 # Zeilenbereiche nachladen

# SEARCH/REPLACE Patches:
python3 agent_start.py --apply-patch 16                    # Patch aus Issue-Kommentar anwenden
python3 agent_start.py --apply-patch 16 --dry-run          # Vorschau ohne Schreiben

# Changelog:
python3 agent_start.py --changelog                         # CHANGELOG.md mit "Unreleased"-Block aktualisieren
python3 agent_start.py --changelog 1.2.0                   # CHANGELOG.md mit Versions-Tag erstellen

# Dual-Repo (Agent auf sich selbst):
python3 agent_start.py --self --issue 16
python3 agent_start.py --self --implement 16
python3 agent_start.py --self --pr 16 --branch fix/...
./context_export.sh 16 --self                              # Kontext für externen LLM
./context_export.sh 16 --self gemini                       # Gemini CLI starten
./context_export.sh 16 --self file                         # context_16.md für Web-Chat

# Watch-Modus (periodische Eval-Überwachung):
python3 agent_start.py --watch                             # alle 60 Minuten (Standard)
python3 agent_start.py --watch --interval 30               # alle 30 Minuten
python3 agent_start.py --eval-after-restart                # Eval nach Neustart (ohne Issue-Kommentar)
python3 agent_start.py --eval-after-restart 61             # Eval nach Neustart + Score in Issue #61

# Betriebsmodi (systemd):
python3 agent_start.py --install-service                   # Units installieren (einmalig)
./start_night.sh                                           # Night-Modus
./start_patch.sh                                           # Patch-Modus
./stop_agent.sh                                            # IDLE
./agent_status.sh                                          # Status anzeigen

# Dashboard:
python3 agent_start.py --dashboard                         # Dashboard einmalig generieren

# Health-Check:
python3 agent_start.py --doctor                            # Vollständigen Zustand prüfen

# Ersteinrichtung:
python3 agent_start.py --setup                             # Interaktiver Setup-Wizard
```

---

## Labels

| Label | Bedeutung |
|-------|-----------|
| `ready-for-agent` | Issue bereit zur Bearbeitung |
| `agent-proposed` | Plan gepostet, wartet auf Freigabe |
| `help wanted` | Stufe 2/3: offene Fragen offen — `agent-proposed` wird entfernt bis Konzept steht |
| `in-progress` | Agent implementiert |
| `needs-review` | PR erstellt, wartet auf Review |

---

## Risiko-Klassifikation

Der Agent stuft jedes Issue automatisch ein:

| Stufe | Beschreibung | Vorgehen |
|-------|-------------|---------|
| 1 | Docs, Cleanup | Plan gepostet → Freigabe → Implementierung |
| 2 | Enhancements | Plan + Analyse-Kommentar → `help wanted` → Freigabe → Implementierung |
| 3 | Bugs, Features | Plan + Analyse-Kommentar → `help wanted` → Freigabe → Implementierung |
| 4 | Breaking Changes | Nicht automatisiert — nur manuell |

**Stufe 2/3:** Der Agent postet Plan-Kommentar + Analyse-Kommentar mit offenen Fragen (Seiteneffekte, betroffene Module, Konfiguration). Label wird zu `help wanted` — `agent-proposed` wird entfernt (Plan noch nicht freigegeben). Erst nach Beantwortung, `help wanted` manuell entfernen und `ok`-Kommentar startet die Implementierung.

**Bugfix-Workflow:** Issue nach Test auf `in-progress` zurücksetzen → fix committen → `--fixup <NR>` → postet Commit-Message als Kommentar + setzt `needs-review`.

**Docs-Check:** `--pr` prüft automatisch ob `Documentation/` seit Abzweig von main geändert wurde. Warnung im Terminal + Gitea-Kommentar wenn nicht. Abschluss-Kommentar enthält immer Revert-Hinweis.

**Auto-Cleanup:** Beim Start verschiebt der Agent automatisch Kontext-Ordner geschlossener Issues nach `contexts/done/`.

---

## Prozess-Enforcement

Technische Schranken die Kontext-Drift verhindern — kein LLM kann sie umgehen:

### `_check_pr_preconditions()` — vor jedem PR

`--pr` prüft automatisch vor der PR-Erstellung:

| Schritt | Prüfung | Fehlermeldung |
|---------|---|---|
| 1 | Branch ≠ main/master | `Branch ist 'main' — PR von main verboten` |
| 2 | Plan-Kommentar vorhanden | `Kein Plan-Kommentar im Issue gefunden` |
| 3 | Agent-Metadaten-Block im Plan | `Plan-Kommentar ohne Metadata-Block` |
| 4 | Eval nach letztem Commit ausgeführt | `Eval nicht ausgeführt seit letztem Commit` |
| 5 | Server-Neustart empfohlen | `restart_script konfiguriert, Eval veraltet` (nur wenn `restart_script` in agent_eval.json gesetzt) |
| 6 | Agent Self-Consistency Check | `Self-Check fehlgeschlagen` (nur wenn Agent-Code geändert) |
| 7 | Diff-Validierung | Warnung wenn Zeilen außerhalb des Issue-AST-Bereichs geändert |
| 8 | Slice-Warnung | Warnung wenn Dateien geändert ohne vorherige `--get-slice`-Anforderung |

Bei Fehler (Schritte 1–6): `SystemExit(1)` — PR wird nicht erstellt.
Schritte 7–8: Warnung + Gitea-Kommentar — PR wird trotzdem erstellt.

### Server-Aktualitäts-Check (`_check_server_staleness()`)

`--pr` prüft zusätzlich ob der laufende Server den aktuellen Branch-Code hat:

1. Letzter Commit-Timestamp via `git log -1 --pretty=%cI`
2. Server-Start-Zeitpunkt aus `log_path` (aus `agent_eval.json`) — sucht rückwärts nach Startup-Mustern
3. Commit neuer als Server-Start → Warnung + `SystemExit(1)`

**Ausgabe bei veraltetem Server:**
```
[!] Server-Code veraltet
    Letzter Commit: 2026-03-20 22:45 (fix/issue-38-...)
    Server gestartet: 2026-03-20 21:20

    → Server neu starten, dann erneut --pr aufrufen.
      Oder: --restart-before-eval (automatisch) / --force (überspringen)
```

**Flags:**

| Flag | Verhalten |
|---|---|
| *(kein Flag)* | Warnung + Exit 1 wenn Server veraltet |
| `--force` | Staleness-Check überspringen — Eval läuft trotzdem |
| `--restart-before-eval` | `restart_script` aus `agent_eval.json` starten + warten, dann Eval |

**Voraussetzung:** `log_path` in `agent_eval.json` konfiguriert + Server schreibt Startup-Message ins Log.
Fehlt `log_path` oder ist Startup nicht parsebar → Check wird silent übersprungen (rückwärtskompatibel).

### Agent-Metadaten-Block

Jeder Plan-Kommentar und Abschluss-Kommentar enthält einen `<details>`-Block:

```
<details>
<summary>🤖 Agent-Metadaten</summary>

**Modell:** claude-sonnet-4-6
**Branch:** fix/issue-61-...
**Commit:** abc1234
**Zeitstempel:** 2026-03-20T14:23:00
**Token-Schätzung:** ~4200 (Kontext: files.md, starter.md)
**Gelesene Dateien:** nanoclaw/server.py, nanoclaw/router.py
</details>
```

### Session-Tracking

`contexts/session.json` zählt abgeschlossene Issues pro LLM-Session:

- `SESSION_LIMIT` (Standard: 2) → Warnung bei Überschreitung (Drift-Risiko)
- `SESSION_RESET_HOURS` (Standard: 4) → session.json wird nach Inaktivität zurückgesetzt
- Status (🟢/🟡/🔴) erscheint im Abschluss-Kommentar jedes PR

### PFLICHTREGELN in starter.md

Jede starter.md enthält automatisch einen PFLICHTREGELN-Block:
- NIEMALS `curl` statt `agent_start.py` verwenden
- NIEMALS Schritte überspringen
- NIEMALS PR manuell erstellen
- Selbst-Check-Checkliste vor jedem Schritt

---

## Sicherheitsregeln

- **Commit-as-Checkpoint:** Nach jeder Datei sofort committen (Schutz bei LLM-Timeout)
- **Kein Auto-Merge:** PR erstellt, Mensch entscheidet
- **Kein Auto-Push auf main:** Agent arbeitet immer auf Feature-Branch
- **Freigabe-Pflicht:** `--implement` nur nach `ok`/`ja`/`✅` in Gitea

---

## Dateistruktur

### gitea-agent (zentraler Clone)

```
gitea-agent/
├── agent_start.py        # CLI + Workflow-Logik (AST, Skelett, SEARCH/REPLACE, Diff, …)
├── evaluation.py         # Eval-System
├── gitea_api.py          # Gitea REST API Wrapper
├── settings.py           # Alle konfigurierbaren Werte (Labels, Texte, Limits, Pfade)
├── dashboard.py          # Live-Dashboard Generator
├── agent_self_check.py   # Deterministischer Self-Consistency Check
├── log.py                # Logging-Konfiguration (Console + File)
├── context_export.sh     # LLM-agnostischer Kontext-Export (plain/gemini/file)
├── repo_skeleton.json    # Projektweites AST-Skelett (einmalig via --build-skeleton)
├── start_night.sh        # Night-Modus starten (systemd)
├── start_patch.sh        # Patch-Modus starten (systemd)
├── stop_agent.sh         # Alle Services stoppen → IDLE
├── agent_status.sh       # Modus, Laufzeit, Score, Issues anzeigen
├── .env.example          # Konfigurationsvorlage
├── .env.agent            # Konfiguration für --self (Agent-Selbst-Betrieb)
└── README.md
```

### Projektstruktur (empfohlen — zentrale Instanz)

```
mein-projekt/
└── agent/
    ├── config/                ← versioniert
    │   ├── agent_eval.json    # Test-Definitionen
    │   └── log_analyzer.py    # Optionaler Log-Analyzer (Watch-Modus)
    ├── data/                  ← .gitignore
    │   ├── baseline.json      # Referenz-Score (maschinenspezifisch)
    │   ├── score_history.json # Score-Verlauf
    │   ├── session.json       # Session-Tracking
    │   ├── contexts/          # Kontext-Ordner pro Issue
    │   │   ├── open/          # Aktive Issues
    │   │   ├── done/          # Abgeschlossene Issues
    │   │   └── session.json   # Session-Zähler
    │   └── gitea-agent.log    # Log-Datei
    └── .env                   ← .gitignore (Secrets + PROJECT_ROOT)
```

Der Agent erkennt die neue Struktur automatisch wenn `PROJECT_ROOT/agent/` existiert.
Fallback: alte Submodul-Struktur (`tests/`, `tools/`, `contexts/` neben agent_start.py).

### Legacy-Struktur (Submodul / Rückwärtskompatibilität)

```
mein-projekt/
├── Helper-tools/        # gitea-agent als Submodul
│   ├── contexts/        # Kontext-Dateien (Laufzeit)
│   └── gitea-agent.log  # Log-Datei (Laufzeit)
├── tests/
│   ├── agent_eval.json
│   ├── baseline.json
│   └── score_history.json
└── tools/
    └── log_analyzer.py
```

**Typen** (aus Gitea-Label): `bug`, `feature_request`, `enhancement`, `docs`, `task`

---

## LLM-Anbindung: Manuell vs. Vollautomatisch

Der Agent produziert strukturierten Output (starter.md, files.md, Gitea-Kommentare) — welches LLM den Code dann tatsächlich schreibt, ist vollständig austauschbar. Das Script ist LLM-agnostisch: es kümmert sich um Gitea, Git und Kontext — das LLM kümmert sich nur um den Code.

### Modus 1: Halb-manuell (aktueller Stand)

Ein LLM-Agent (z.B. Claude Code, Gemini CLI, Aider, …) läuft als interaktive Session im Terminal. Der Mensch triggert den nächsten Schritt durch einen Satz im Chat:

```
# Terminal 1 — Agent (Script)
python3 agent_start.py
# → [✓] Branch erstellt. starter.md + files.md bereit.

# Terminal 2 — LLM-Session (z.B. Claude Code, Aider, Gemini CLI)
> starte agent / prüf issues / run agent_start.py
# LLM liest Output, öffnet starter.md, liest Skelett, fordert Slices an, implementiert, committet
```

**Vorteil:** Volle Kontrolle, Änderungen sind vor dem Commit sichtbar.
**Nachteil:** Mensch muss aktiv sein — kein Nacht-/Hintergrund-Betrieb.

---

### Modus 1b: Kontext-Export für beliebige LLMs

```bash
# Kontext für externen LLM aufbereiten
./context_export.sh 21 --self file
# → context_21.md erzeugen → in Claude Web / GPT / Gemini Web hochladen

# oder: Gemini CLI direkt starten
./context_export.sh 21 --self gemini

# oder: plain mit interaktivem Slice-Modus
./context_export.sh 21 --self
# → SLICE: agent_start.py:1201-1289  → nachfragen
# → READY → Implementierung starten
```

**Wann welchen LLM nutzen:**

| Aufgabe | Empfehlung |
|---------|-----------|
| > 1 Datei oder > 50 Zeilen Änderung | **Claude Code** |
| Einfache Einzeldatei-Änderung | Gemini CLI möglich |
| Ohne Terminal (Web-Chat) | `context_export.sh file` + Hochladen |

> ⚠️ **Gemini CLI** ist für komplexe Issues nicht geeignet: verlässt den Issue-Scope, ignoriert `--self` beim PR-Befehl, Infinite-Loop-Bug nach Abschluss. **Für alles Nicht-Triviale: Claude Code verwenden.**

---

### Modus 2: Vollautomatisch via LLM-API *(vorbereitet, nicht aktiv)*

Das Script hat eine eingebaute API-Anbindung. Mit `LLM_API_ENABLED=true` und einem API-Key läuft der gesamte Workflow ohne menschliche Interaktion. Aktuell ist Claude (Anthropic) als erster Anbieter vorbereitet — die Struktur ist so ausgelegt, dass weitere Anbieter (OpenAI-kompatible APIs, Gemini, lokale Modelle via Ollama) ergänzt werden können.

```bash
# .env — Beispiel mit Claude
LLM_API_ENABLED=true
ANTHROPIC_API_KEY=sk-ant-...

# alternativ: OpenAI-kompatible API (z.B. Ollama, LM Studio, Mistral)
# LLM_API_BASE=http://localhost:11434/v1
# LLM_API_KEY=...
# LLM_MODEL=llama3
```

```bash
# Dauerbetrieb (empfohlen: tmux oder systemd)
python3 agent_start.py
# → Issue erkannt → Plan gepostet → Freigabe abgewartet
# → Branch erstellt → LLM implementiert → PR erstellt
# → Alles ohne manuellen Eingriff
```

**Ablauf intern:**
1. Script liest Issue + baut Kontext (starter.md, files.md mit AST-Skelett)
2. Schickt Kontext als System-Prompt + Skelett an LLM-API
3. LLM fordert Slices an, antwortet mit SEARCH/REPLACE Blöcken
4. Script wendet `--apply-patch` an, committet, erstellt PR

**Vorteil:** Vollständig autonom — kann nachts laufen, Issues aus der Queue abarbeiten.
**Nachteil:** Kein Live-Review vor dem Commit. Freigabe-Pflicht (`ok`-Kommentar) bleibt trotzdem erhalten — der Mensch entscheidet weiterhin *ob* implementiert wird, nicht *wann*.

> **Status:** Im Code vorbereitet (API-Flag + Grundstruktur vorhanden). Vollständige Implementierung der Edit-Loop + Commit-Logik steht noch aus.

---

### Modus 3: Beliebiges LLM via CLI-Pipe

```bash
python3 agent_start.py --implement 21
cat agent/data/contexts/open/21-docs/starter.md | llm "Implementiere das Issue"
# oder: | aider --message "..."
# oder: | ollama run llama3
```

Funktioniert für Text-Antworten — kein direktes Datei-Editing. Sinnvoll für Recherche oder Plan-Kommentare, nicht für vollständige Code-Änderungen.

---

### Vergleich

| Modus | LLM-Beispiele | Autonomie | Mensch muss... | Status |
|-------|--------------|-----------|----------------|--------|
| Interaktive Session | Claude Code, Aider, Gemini CLI | Halb-manuell | Trigger-Satz tippen | ✅ aktiv |
| Kontext-Export | Claude Web, GPT, Gemini Web | Halb-manuell | Datei hochladen, PR-Befehl tippen | ✅ aktiv |
| LLM-API | Claude, GPT-4, Gemini, Ollama | Vollständig autonom | Issue schreiben + freigeben | 🔧 vorbereitet |
| CLI-Pipe | ollama, llm, aider | Text-only | Output manuell anwenden | ⚙️ möglich |

---

## Roadmap

### Abgeschlossen

- **Performance-Benchmarking** — Misst die Latenz bei jedem Eval-Test und erstellt bei Regressionen automatisch `[Auto-Perf]`-Issues (`--watch`).
- **Patch-Modus & Live-Dashboard** — Entwicklungs-Modus (`--patch`) ohne Auto-Issue-Spam, dafür mit einem Live-Dashboard (`dashboard.html`), das bei jedem Watch-Lauf aktualisiert wird.
- **LLM-gestützte Test-Generierung** — Neuer Befehl (`--generate-tests`), der Kontext sammelt und einen Prompt zur Erstellung von `pytest`- und `agent_eval.json`-Tests vorbereitet.
- **Systematische Fehler-Erkennung (Tag-Aggregation)** — Der Watch-Modus analysiert die `score_history.json`, erkennt systematisch fehlschlagende Test-`tags` und erstellt `[Auto-Improvement]`-Issues mit Lösungsvorschlägen.
- **LLM-gestützte Log-Analyse** — Der `log_analyzer.py` kann optional ein LLM nutzen, um bei unbekannten Fehlern eine Root-Cause-Analyse durchzuführen. Der Prompt wird dabei mit dem Kontext aus der `score_history.json` angereichert.
- **Agent Self-Consistency Check** — Ein deterministischer Check (`agent_self_check.py`) stellt sicher, dass Erweiterungen am Agenten selbst konsistent sind (Flags, Labels, etc.) und wird vor jedem PR auf den Agenten-Code ausgeführt.
- **Consecutive-Pass Gate** — Auto-Issues werden erst nach N aufeinanderfolgenden Passes geschlossen (`close_after_consecutive_passes`). Fortschritts-Kommentare im Issue zeigen den Zählerstand.
- **Betriebsmodi (Night / Patch / Idle)** — Drei systemd-basierte Modi mit Shell-Skripten (`start_night.sh`, `start_patch.sh`, `stop_agent.sh`, `agent_status.sh`). Dashboard-Updates nach jedem Event. Dynamische Unit-Installation via `--install-service`.
- **LLM-agnostischer Kontext-Export & Dual-Repo-Support** (#65) — `context_export.sh` exportiert den Issue-Kontext für beliebige LLMs (plain/gemini/file). `.env.agent` + `--self` Flag ermöglichen es, den Agenten auf sich selbst anzuwenden (gitea-agent entwickelt gitea-agent).
- **AST-Repository-Skelett** (#68) — Bei `--issue`/`--implement` werden ClassDef/FunctionDef mit Zeilen und Signatur extrahiert (`repo_skeleton.json` + `repo_skeleton.md`). Große Dateien erscheinen als Skelett statt Volltext in `files.md`. `--get-slice datei.py:START-END` lädt exakte Zeilenbereiche nach.
- **Diff-Validierung** (#57) — `--pr` prüft ob das LLM nur Zeilen im freigegebenen AST-Bereich geändert hat. Scope-Verletzungen erscheinen als Warnung im Terminal und als Gitea-Kommentar — kein harter Abbruch.
- **SEARCH/REPLACE Protokoll & Chirurgisches Refactoring** (#58/#47) — LLM-agnostisches Patch-Format (`<<<<<<< SEARCH / ======= / >>>>>>> REPLACE`). Parser + Whitespace-Normalisierung + `ast.parse()`-Syntax-Check + `.bak`-Backup. `--apply-patch NR [--dry-run]`.
- **Flächendeckende Codesegment-Strategie** (#72) — LLM bekommt niemals mehr Volltext. `files.md` enthält nur Skelett + Slice-Hinweise. `--build-skeleton` erstellt projektweites `repo_skeleton.json` (alle .py-Dateien, kein Größen-Limit). Watch-Loop aktualisiert inkrementell. `session.json` protokolliert Slice-Anforderungen pro Issue. Technische Schranke warnt bei ungesliceten Dateiänderungen.
- **Gitea-Versionsvergleich** (#59) — Bei Score-Regression wird die alte Dateiversion via Gitea-API geladen und AST-Skelette verglichen. Struktureller Diff (`+ neu`, `- entfernt`, `~ gewachsen`) erscheint automatisch im Auto-Issue. Opt-in via `agent_eval.json: gitea_version_compare.enabled`.
- **Unit-Tests für kritische Funktionen** (#78) — `pytest`-Suite für `patch.py`, `changelog.py`, `agent_self_check.py` und das Repository-Skelett. Deterministisch, ohne Netzwerk- oder Datei-I/O.
- **Plugin-Architektur: patch + changelog** (#79) — `plugins/patch.py` + `plugins/changelog.py` ausgelagert (~300 Zeilen aus `agent_start.py`). `settings.py`: `DOCTOR_RESULT_PATH`. `dashboard.py`: `--doctor` Sektion.
- **Setup-Wizard & Health-Check** (#77) — `--setup`: Interaktiver 6-Schritt-Wizard (Gitea-Verbindung → Repo → Projektverzeichnis → Labels → `agent_eval.json` → `.env`). `--doctor`: 6 Prüfpunkte, speichert `doctor_last.json`, zeigt strukturierten Report.

### ⚠️ Bekannte Einschränkungen

**Gemini CLI** ist aktuell **nicht geeignet** für Issues mit mehr als einer Datei oder mehr als ~50 Zeilen Änderung:
- Verlässt den Issue-Scope und refactored Dateien die nicht zum Issue gehören
- Ignoriert das `--self` Flag beim PR-Befehl
- Infinite Loop nach Abschluss (Bug in Gemini CLI)

Für alle komplexeren Issues: **Claude Code verwenden**. Gemini CLI nur für triviale Einzeldatei-Änderungen.

### Geplant / In Arbeit

- **Stufe-1 Auto-Implement** — Autonome Bearbeitung von Low-Risk Issues (Docs/Cleanup), steuerbar über die .env (`AUTO_IMPLEMENT_LEVEL1=true`).
- **LLM-API Vollimplementierung** — automatische Implementierungsschleife über konfigurierbare API (Anthropic, OpenAI-kompatibel, Ollama); Grundstruktur vorhanden, fehlt: Datei-Edit-Loop + Commit-Logik
- **Webhook-Integration** — Gitea sendet Event bei `ready-for-agent` → Agent wird direkt getriggert, kein Cron/manueller Aufruf nötig

### Ideen / Offen

- **Multi-LLM-Routing** — je nach Issue-Risikostufe unterschiedliche Modelle einsetzen (z.B. kleines Modell für Docs, starkes Modell für Bugs)
- **Multi-Repo-Support** — eine Agent-Instanz verwaltet mehrere Repos, `.env` pro Repo in `~/.gitea-agent/repos/`
- **Gitea Webhook-Server** — kleiner HTTP-Server der Gitea-Webhooks empfängt und `agent_start.py` direkt triggert
- **PR-Review-Kommentar-Loop** — Agent liest Review-Kommentare aus dem PR und reagiert automatisch auf Änderungswünsche
- **Parallelisierung** — mehrere Issues gleichzeitig auf separaten Branches bearbeiten (aktuell sequenziell)
- **Web-UI** — erweitertes Dashboard mit Issue-Queue und Aktions-Buttons (aktuell: `dashboard.html` als statisches File)
