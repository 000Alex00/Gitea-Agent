# gitea-agent

**Autonomes CI/CD-System für LLM-Agenten — Issue-Tracking, Eval-Framework, Token-Optimierung, technische Schranken. Selbstgehostet, LLM-agnostisch.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Status: Beta](https://img.shields.io/badge/Status-Beta-orange.svg)]()

Ein vollständiges Infrastruktur-System für KI-gestützte Code-Entwicklung: Issue-Tracking mit Gitea, automatisches Testing & Eval-Framework, hohe Token-Reduktion via AST-Skeleton, 8-stufige technische Schranken statt Prompt-Engineering. Läuft komplett lokal (z.b. Raspberry Pi, Jetson Nano, Synology NAS). Python 3.10+ Stdlib only — keine Cloud, keine Dependencies.

---

> [!WARNING]
> **🚧 Beta-Software — Aktive Entwicklung**
> 
> Dieses Projekt funktioniert in meinem Setup (Jetson Orin Nano + Gitea auf Synology NAS) sehr gut und ist täglich im Einsatz. **Jedoch:**
> 
> - **Keine Version 1.0:** Einige Features können noch robuster gestaltet werden
> - **Code-Refactoring ausstehend:** Der Code ist gewachsen, braucht Generalisierung & Optimierung
> - **Gitea-spezifisch:** GitHub-Integration ist in Arbeit, aber noch nicht vollständig
> - **Keine Garantien:** Nutze es auf eigenes Risiko — Backups empfohlen!
> 
> **Roadmap zu v1.0:**
> - ✅ Gitea-Integration (funktioniert)
> - 🔄 GitHub-Integration (in Arbeit)
> - 🔄 Code-Refactoring & Generalisierung
> - 🔄 Erweiterte Fehlerbehandlung
> - 🔄 Umfassende Test-Coverage
> 
> **Feedback willkommen!** Issues & Pull Requests helfen, das System produktionsreif zu machen. → [GitHub Issues](https://github.com/Alexander-Benesch/Gitea-Agent/issues)

---

## 🎯 Was ist das?

`gitea-agent` ist eine Infrastruktur-Automatisierung für LLM-basierte Code-Agenten. Das Problem: LLMs halluzinieren Dateipfade, überspringen Tests oder pushen auf `main`. Dieser Agent löst das durch **technische Schranken statt Prompt-Regeln**.

**Kernprinzip:** Der Agent übernimmt die gesamte Repo-Verwaltung (Issue lesen, Dateien finden, Branch erstellen, Tests laufen, PR öffnen). Ein beliebig nutzbarer LLM-Agent schreibt nur Code — und nur nach expliziter Freigabe.

### Entstehungsgeschichte

> **Von einem kaputten Chatbot zum autonomen AI-Dev-System.**
>
> Ich bin kein Entwickler, gerade der "Hallo Welt"-Phase entsprungen. Ich wollte eigentlich nur meinen lokalen LLM-Chatbot debuggen und um Features erweitern. Leider stieß ich bei jedem LLM auf die selben Probleme: Feature-Verlust, überschriebene Dateien, halluzinierte Pfade, Neuerfindung bereits vorhandener Funktionen. Mein Tokenlimit war durch das Einlesen ganzer Code-Dateien ständig erreicht. Dazu kam viel manueller Aufwand: Änderungen im lokalen Gitea-Repository pflegen, den Überblick behalten, Code-Chaos vermeiden.
> 
> Also dachte ich: "Ich schreibe ein kleines Script, das den LLM daran hindert, Chaos anzurichten — automatisches Branching, Tests vor jedem Merge, keine direkten Pushes auf `main`." Dann kam die nächste Idee: "Er soll Tests laufen lassen, bevor er einen PR öffnet." Und dann: "Er soll nur die Dateien laden, die er wirklich braucht, nicht das gesamte Repository."
>
> **Einen Monat später hatte ich versehentlich ein komplettes CI/CD-System gebaut:**
> - Ein Eval-Framework, das Tests automatisch läuft und bei Regression Issues öffnet
> - Ein AST-basiertes Token-Optimierungs-System (massive Token-Reduktion: 128 KB → 500 Tokens)
> - 8-stufige technische Schranken (kein Prompt-Engineering mehr nötig)
> - Gitea-Version-Compare, das zeigt, welche Funktionen sich zwischen Commits geändert haben
> - Ein Live-Dashboard mit Score-History und Performance-Tracking
> - LLM-gestützte Log-Analyse bei Fehlern
> - Automatische Changelog-Generierung aus Commit-Nachrichten
>
> Das System ist inzwischen größer und komplexer, als ich es je verstehen werde. Es läuft komplett lokal — bei mir auf einem **Jetson Orin Nano 8 GB** (Agent) neben **Gitea auf einem Synology NAS**.
>
> **Und das Verrückte:** Es funktioniert. Der Agent hat sich selbst weiterentwickelt, seine eigenen Tests geschrieben, seine eigene Dokumentation gepflegt. Ich bin nur noch der Typ, der ideen einsteuert und "ok" in Issues kommentiert — verrückte Welt! :-)

---

## ✨ Features im Überblick

### 🤖 **Autonomer Betrieb**
- **Auto-Modus:** Scannt alle Issues, führt automatisch den nächsten Schritt aus (Plan, Branch, PR)
- **Watch-Modus:** 24/7-Betrieb mit Auto-Restart bei Regression
- **Night/Patch-Modi:** Systemd-basiert — Notebook zuklappen, Agent läuft weiter

### 🧠 **Massive Token-Optimierung**
- **AST-Skeleton:** Nur Funktions-Signaturen statt Volltext (128 KB → 500 Tokens)
- **`--get-slice`:** On-Demand-Laden exakter Zeilenbereiche
- **Kontext-Loader:** Automatisches Finden relevanter Dateien via Imports + Grep

### 🔒 **Prozess-Enforcement**
- **Freigabe-Pflicht:** Kein Code ohne "ok"-Kommentar im Issue
- **Eval-System:** Tests müssen bestehen, sonst PR blockiert
- **Baseline-Tracking:** Score darf nie unter Referenzwert fallen
- **Self-Consistency-Check:** Agent prüft sich selbst vor PRs

### �️ **Sicherheitsnetz**
- **SEARCH/REPLACE-Patches:** LLM-agnostisch, kein Diff-Koordinaten-Chaos
- **AST-Syntax-Check:** Kaputte Patches werden abgelehnt
- **Diff-Validation:** Warnung bei Out-of-Scope-Änderungen
- **Branch-Protection:** Nie direkt auf `main` pushen
- **8-Stufen-Precondition-Check:** Technische Schranken vor jedem PR (nicht per Prompt!)

### 🔬 **Extreme Technical Enforcement**
- **Gitea-Version-Compare:** AST-Diff zeigt Code-Änderungen bei Score-Regression
- **Server-Staleness-Check:** Blockiert PR wenn Server veraltet ist
- **Slice-Tracking:** Warnt wenn Dateien ohne `--get-slice` geändert wurden
- **Docs-Check:** Automatische Warnung wenn Code geändert aber Doku nicht
- **Metadaten in jedem Plan:** Token-Schätzung, Modell, Zeitstempel, gelesene Dateien

### 📊 **Monitoring & Debugging**
- **Live-Dashboard:** HTML-Übersicht mit Score-Charts, System-Status
- **Tag-Aggregation:** Systematische Fehler automatisch erkennen
- **Performance-Benchmarking:** Latenz-Regression → Auto-Issue
- **Log-Analyzer:** LLM-gestützte Fehleranalyse
- **Score-History:** Letzte 90 Eval-Runs protokolliert (5 im PR-Kommentar)
- **Token-Usage-Tracking:** Jeder LLM-Call mit Token-Count in Metadaten

### 🗣️ **Diskussion & Context**
- **Kommentar-Integration:** Nachträglich hinzugefügte Nutzer-Kommentare landen automatisch in `starter.md`
- **Keyword-Extraction:** Wichtige Begriffe aus Diskussion → Context-Loader
- **User-Only-Filter:** Bot-Kommentare werden herausgefiltert
- **Kontext-Kommentar:** Agent postet Zusammenfassung der gefundenen Dateien + Keywords

### 🔄 **Lifecycle-Management**
- **Auto-Changelog:** Generiert `CHANGELOG.md` aus Conventional Commits
- **Auto-Cleanup:** Verschiebt geschlossene Issues nach `contexts/done/`
- **Session-Tracking:** Warnt bei Context-Drift nach N Issues
- **Label-Automation:** Kompletter Label-Lifecycle automatisiert
- **Risk-Classification:** 4-Stufen-System (Docs → Enhancement → Bug → Breaking Change)
- **Auto-Neustart:** Watch-Modus startet Server bei Inaktivität + neuen Commits

### 🎯 **LLM-Agnostisch & Flexibel**
- **Context-Export-Script:** Unterstützt plain Terminal, Gemini CLI, File-Export für Web-Chats
- **Interaktiver Slice-Modus:** `SLICE: file:100-200` live im Terminal eingeben
- **SEARCH/REPLACE-Format:** Funktioniert in jedem Chat (GPT, Claude, Gemini Web)
- **Test-Generierung:** LLM schreibt pytest + agent_eval.json Tests aus Issue-Kontext

---

## 🚀 Quick Start

```bash
# 1. Installation (einmalig, für alle Projekte)
git clone https://github.com/Alexander-Benesch/Gitea-Agent.git ~/Gitea-Agent
cd ~/Gitea-Agent

# 2. Projekt einrichten (interaktiver Wizard)
python3 agent_start.py --setup

# 3. Erstes Issue automatisieren
# → Gitea: Issue mit Label "ready-for-agent" versehen
python3 agent_start.py  # Auto-Modus: Plan wird gepostet
# → Gitea: "ok" kommentieren
python3 agent_start.py  # Implementierung + PR
```

> [!TIP]
> **Detaillierte Anleitungen im Cookbook:** Installation, Setup-Wizard, Health-Check → [cookbook/01-installation.md](cookbook/01-installation.md)

---

## 📚 Cookbook — Vollständige Dokumentation

Das **Cookbook** ist die zentrale Anlaufstelle für alle technischen Details, Workflows und Troubleshooting. Jedes Rezept folgt dem **Atomic Recipe Principle**: Voraussetzungen, Problem, Lösung, Erklärung, Best Practices, Warnungen.

### 🚀 Getting Started

| Rezept | Thema |
|--------|-------|
| [01](cookbook/01-installation.md) | Installation & Systemvoraussetzungen |
| [02](cookbook/02-first-setup.md) | Erstes Projekt einrichten (Setup-Wizard) |
| [03](cookbook/03-first-issue.md) | Dein erstes Issue automatisieren |
| [04](cookbook/04-health-check.md) | System-Zustand prüfen (`--doctor`) |

### 🔄 Core Workflow

| Rezept | Thema |
|--------|-------|
| [05](cookbook/05-issue-to-pr.md) | Standard-Workflow: Issue → PR |
| [06](cookbook/06-bugfix-on-branch.md) | Bugfix während Implementierung (`--fixup`) |
| [07](cookbook/07-multiple-repos.md) | Zwei Repos — Ein Agent (`--self`) |
| [08](cookbook/08-manual-workflow.md) | Manueller Workflow ohne Auto-Scan |

### ✅ Testing & Evaluation

| Rezept | Thema |
|--------|-------|
| [09](cookbook/09-first-test.md) | Ersten Eval-Test schreiben |
| [10](cookbook/10-multi-step-tests.md) | Mehrstufige Tests (Context-Persistence) |
| [11](cookbook/11-baseline-management.md) | Eval-Baseline setzen & aktualisieren |
| [12](cookbook/12-performance-tests.md) | Latenz-Tests mit `max_response_ms` |
| [13](cookbook/13-test-generation.md) | Tests LLM-generieren lassen (`--generate-tests`) |

### 🤖 Watch-Modus & Automation

| Rezept | Thema |
|--------|-------|
| [14](cookbook/14-watch-mode-tmux.md) | Watch-Modus mit tmux starten |
| [15](cookbook/15-watch-mode-systemd.md) | Watch als Systemd-Dienst |
| [16](cookbook/16-night-vs-patch.md) | Betriebsmodi: Night / Patch / Idle |
| [17](cookbook/17-consecutive-pass-gate.md) | Auto-Issues erst nach N× PASS schließen |
| [18](cookbook/18-tag-aggregation.md) | Systematische Fehler erkennen (Tags) |
| [19](cookbook/19-staleness-check.md) | PR mit veraltetem Server verhindern |

### 🛠️ Advanced Features

| Rezept | Thema |
|--------|-------|
| [20](cookbook/20-ast-skeleton.md) | AST-Repository-Skelett erstellen |
| [21](cookbook/21-codesegment-strategy.md) | Volltext durch Slices ersetzen (`--get-slice`) |
| [22](cookbook/22-diff-validation.md) | Änderungen auf Issue-Scope prüfen |
| [23](cookbook/23-search-replace-patches.md) | SEARCH/REPLACE-Patches anwenden |
| [24](cookbook/24-gitea-version-compare.md) | AST-Diff bei Regression zeigen |
| [25](cookbook/25-log-analyzer.md) | Projekt-eigene Log-Analyse integrieren |

### 🔧 Configuration & Customization

| Rezept | Thema |
|--------|-------|
| [26](cookbook/26-env-configuration.md) | `.env`-Konfiguration (Field-Referenz) |
| [27](cookbook/27-eval-json-reference.md) | `agent_eval.json`-Referenz |
| [28](cookbook/28-labels-and-workflow.md) | Label-System anpassen |
| [29](cookbook/29-context-excludes.md) | Dateien vom Context ausschließen |
| [30](cookbook/30-dashboard-customization.md) | Dashboard anpassen & deployen |

### 🧩 Plugins & Extensions

| Rezept | Thema |
|--------|-------|
| [31](cookbook/31-plugin-architecture.md) | Plugin-System verstehen |
| [32](cookbook/32-create-custom-plugin.md) | Eigenes Plugin schreiben |
| [33](cookbook/33-changelog-automation.md) | CHANGELOG.md automatisch generieren |

### 🐛 Troubleshooting

| Rezept | Thema |
|--------|-------|
| [34](cookbook/34-debug-eval-fail.md) | Eval gibt FAIL obwohl alles läuft |
| [35](cookbook/35-empty-agent-comments.md) | Agent-Kommentare sind leer |
| [36](cookbook/36-watch-mode-crashes.md) | Watch-Modus stürzt ab |
| [37](cookbook/37-search-replace-no-match.md) | SEARCH/REPLACE matcht nicht |

### 📚 Reference

| Rezept | Thema |
|--------|-------|
| [38](cookbook/38-cli-reference.md) | Vollständige CLI-Befehlsreferenz |
| [39](cookbook/39-api-functions.md) | Funktions-Referenz (evaluation, gitea_api) |
| [40](cookbook/40-best-practices.md) | Best Practices & Patterns |
| [41](cookbook/41-security-guide.md) | Sicherheitshinweise |

> [!IMPORTANT]
> **Alle Features erklärt im Cookbook:** Jedes Rezept enthält Copy-Paste-ready Code, Erklärungen, Tipps und Warnungen. → [cookbook/README.md](cookbook/README.md)

---

## 🏗️ Architektur-Übersicht

```
┌─────────────────────────────────────────────────────┐
│                   Gitea Issue                       │
│  Label: ready-for-agent → agent-proposed → ...     │
│  + Diskussion: Nutzer-Kommentare (nachträglich)    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│              agent_start.py (Orchestrator)          │
├─────────────────────────────────────────────────────┤
│ • Issue scannen & Risk-Classification (4 Stufen)   │
│ • Kontext-Loader (Imports, Grep, AST-Skeleton)     │
│   → Inkl. Keywords aus Diskussion                  │
│ • Plan generieren → Gitea-Kommentar                │
│   → Mit Metadaten: Token-Count, Modell, Files      │
│ • Freigabe prüfen → Branch erstellen               │
│ • Context-Export (starter.md, files.md)            │
│   → Diskussion automatisch in starter.md           │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│              LLM-Agent (User-Controlled)            │
│  Claude Code / Gemini / Aider / Custom              │
│  → Liest starter.md + files.md (AST-Skeleton)      │
│  → Fordert Slices an: --get-slice file:100-200     │
│  → Postet SEARCH/REPLACE-Patches als Kommentar     │
│  → Alle Slice-Requests werden in session.json      │
│     protokolliert (für Stufe 8 Check)              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│            agent_start.py (Finalization)            │
├─────────────────────────────────────────────────────┤
│ • --apply-patch: AST-Syntax-Check + Backup          │
│ • evaluation.py: Tests laufen lassen               │
│   → Token-Usage wird gemessen & geloggt            │
│ • Baseline-Check (Score ≥ Referenz?)               │
│ • Server-Staleness-Check (Code aktuell?)           │
│ • Diff-Validation (Out-of-Scope? Stufe 7)          │
│ • Slice-Check (Alle Dateien angefordert? Stufe 8)  │
│ • Self-Consistency (Agent-Code? Stufe 6)           │
│ • Docs-Check (Documentation/*.md aktualisiert?)    │
│ • --pr: Pull-Request erstellen                     │
│   → Metadaten + Score-History (letzte 5 Runs)     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│               Gitea Pull Request                    │
│  Label: needs-review → Merge → Done                │
│  + Score-History-Tabelle (letzte 5 Eval-Runs)      │
│  + Token-Usage-Zusammenfassung                     │
│  + Gitea-Version-Compare (bei Regression)          │
└─────────────────────────────────────────────────────┘
```

### Token-Optimierung: files.md-Format

**Vorher (Volltext):**
```
## server.py (3684 Zeilen)
[kompletter Code...]
→ ~32.000 Tokens
```

**Nachher (AST-Skeleton):**
```
## server.py (3684 Zeilen)

### Funktionen
- handle_request     [145-289]   def handle_request(msg)
- process_upload     [312-450]   def process_upload(file)

Volltext: python3 agent_start.py --get-slice server.py:145-289
→ ~500 Tokens (98% Reduktion)
```

### User-Journey: Vom Issue zum PR

```
User:   Issue schreiben + Label "ready-for-agent" setzen
        ↓
Agent:  Plan-Kommentar ins Issue (mit 🤖 Metadaten-Block: Zeitstempel, Tokens, Dateien)
        contexts/{N}-{typ}/starter.md erstellt → Label: agent-proposed
        ↓ (Stufe 2/3 zusätzlich — wenn noch kein Plan vorhanden:)
Agent:  Analyse-Kommentar + Nächste Schritte ins Issue
        Label "help wanted" gesetzt, "agent-proposed" entfernt
        ↓
User:   Fragen im Issue beantworten
        python3 agent_start.py --issue {N}  → starter.md mit Kommentarhistorie aktualisiert
        [Wiederholen bis Konzept steht]
        Label "help wanted" manuell entfernen → "ok" kommentieren
        ↓
Agent:  Freigabe erkannt (help wanted weg + ok) → Branch erstellen
        Label: agent-proposed → in-progress
        Nächste Schritte ins Issue gepostet
        contexts/{N}-{typ}/files.md erstellt (AST-Skelett + Slice-Hinweise)
        ↓
LLM:    Liest starter.md + files.md → fordert Slices an (--get-slice) → implementiert → committet
        ↓
Agent:  --pr <NR> --branch <branch> --summary "..."
        → Prüft 8 Preconditions (Branch, Plan, Eval, Diff-Scope, Slices, …)
        ↓
        PR erstellt + Abschluss-Kommentar + Label: needs-review
        contexts/{N}-{typ}/ → contexts/done/{N}-{typ}/
        ↓
User:   PR reviewen + mergen
```

> [!NOTE]
> **"help wanted" Workflow:** Bei komplexen Issues (Stufe 2/3) startet der Agent einen Dialog — User beantwortet Fragen im Issue, Agent aktualisiert `starter.md` mit der Kommentarhistorie. Erst nach "ok" geht's weiter zur Implementierung.

---

## 🔐 Technische Schranken (8-Stufen-Check)

Vor jedem PR läuft `_check_pr_preconditions()` — **technische Enforcement, nicht Prompt-basiert**. Bei Fehler: Exit 1, PR wird blockiert.

| Stufe | Prüfung | Blockiert wenn... |
|-------|---------|-------------------|
| **1** | Branch ≠ main/master | Versuch auf main zu pushen |
| **2** | Plan-Kommentar vorhanden | Kein Plan im Issue gepostet |
| **3** | Metadaten-Block im Plan | Plan ohne `🤖 Agent-Metadaten` (Token-Count, Modell, Zeitstempel) |
| **4** | Eval nach letztem Commit | Eval veraltet oder nicht gelaufen |
| **5** | Server-Neustart (falls konfiguriert) | `restart_script` gesetzt, aber Server veraltet |
| **6** | Self-Consistency Check | Agent-Code geändert + Logik-Fehler (Labels fehlen, CLI-Flags ohne Handler) |
| **7** | Diff-Validierung (Warnung) | Zeilen außerhalb Issue-Scope geändert |
| **8** | Slice-Warnung (Warnung) | Dateien geändert ohne vorherige `--get-slice`-Anforderung |

**Beispiel: Stufe 3 (Metadaten-Block)**

```markdown
<details>
<summary>🤖 Agent-Metadaten</summary>

**Modell:** claude-sonnet-4-6
**Token-Schätzung:** ~4200 (Context: files.md 2.1k, starter.md 1.8k, Diskussion 0.3k)
**Gelesene Dateien:** myproject/server.py, myproject/router.py
**Branch:** fix/issue-21-server-crash
**Commit:** abc1234
**Zeitstempel:** 2026-03-20T14:23:00
</details>
```

> [!TIP]
> **Alle Checks erklärt:** [cookbook/05-issue-to-pr.md](cookbook/05-issue-to-pr.md) — Abschnitt "Prozess-Enforcement"

---

## 🔍 Gitea-Version-Compare bei Regression

Bei Score-Einbruch im Watch-Modus: Agent lädt alte Dateiversion via Gitea-API, vergleicht AST-Skelette und zeigt strukturelle Änderungen.

**Beispiel-Output im Auto-Issue:**

```markdown
## [Auto-Issue] Score-Regression seit Commit def456

**Letzter erfolgreicher Score:** 7/7 (Commit abc123)  
**Aktueller Score:** 5/7 (Commit def456)

### AST-Strukturänderung: myproject/server.py

+ handle_upload  (neu, 45 Zeilen)
- _cleanup_temp  (entfernt)
~ parse_request  (+45 Zeilen, war 67 → jetzt 112)

**Potenzielle Root-Cause:**
- `_cleanup_temp` wurde entfernt → möglicherweise Memory-Leak
- `parse_request` stark gewachsen → Komplexitätszunahme
```

**Aktivierung:**
```json
// agent_eval.json
{
  "gitea_version_compare": { "enabled": true }
}
```

> [!TIP]
> **Details:** [cookbook/24-gitea-version-compare.md](cookbook/24-gitea-version-compare.md)

---

## 💬 Diskussion & nachträglich hinzugefügte Kommentare

Der Agent bezieht **alle Nutzer-Kommentare** automatisch in den Kontext ein — auch die, die nach dem Plan-Post hinzugefügt wurden.

**Workflow:**

```bash
# 1. Agent postet Plan
python3 agent_start.py --issue 42
# → Plan-Kommentar in Gitea

# 2. User kommentiert: "Das betrifft auch worker.py, nicht nur server.py"
# → Agent liest diesen Kommentar bei nächstem Schritt

# 3. Implementierung startet
python3 agent_start.py --implement 42
# → starter.md enthält:

## Diskussion
**User:** Das betrifft auch worker.py, nicht nur server.py
**Colleague:** ok, beide Dateien anpassen

# → Context-Loader findet jetzt BEIDE Dateien (worker.py + server.py)
```

**Features:**

- **User-Only-Filter:** Bot-Kommentare (vom Agent selbst) werden herausgefiltert
- **Keyword-Extraction:** Wichtige Begriffe aus Diskussion → Context-Loader
- **Kontext-Kommentar:** Agent postet Zusammenfassung nach `--implement`:

```markdown
## 📎 Kontext-Loader
**Erkannte Dateien (3):**
- `myproject/server.py` (aus Issue-Body)
- `myproject/worker.py` (aus Diskussion)
- `myproject/router.py` (via Import-Analyse)

**Diskussion:** 2 Kommentar(e) einbezogen
**Keywords aus Diskussion:** worker.py, beide Dateien, anpassen
```

> [!TIP]
> **Details:** [cookbook/05-issue-to-pr.md](cookbook/05-issue-to-pr.md) — Abschnitt "Diskussion im Kontext"

---

## ⚙️ Systemvoraussetzungen

- **Python:** 3.10+ (Stdlib only — keine externen Dependencies)
- **Git:** Für Branch-Management
- **Gitea:** Self-hosted oder Cloud (API v1)
- **LLM-Zugang:** Claude Code, Gemini, Aider, lokales LLM (optional)

### Hardware-Tested

✅ Raspberry Pi 4 (4 GB RAM)  
✅ Jetson Orin Nano (8 GB RAM)  
✅ Synology NAS (Docker-Container)  
✅ Standard-Linux-Server

---

## 🔧 Typische Workflows

### Workflow 1: Issue → PR (Standard)

```bash
# 1. Issue in Gitea mit Label "ready-for-agent"
python3 agent_start.py              # → Plan wird gepostet

# 2. "ok" in Gitea kommentieren
python3 agent_start.py              # → Branch + Context generiert

# 3. LLM-Agent-Session starten
./context_export.sh 42 --self       # → starter.md + files.md laden
# LLM fordert Slices an via --get-slice, postet SEARCH/REPLACE

# 4. Patches anwenden
python3 agent_start.py --apply-patch 42

# 5. PR erstellen (inkl. Eval)
python3 agent_start.py --pr 42 --branch fix/issue-42 --summary "Fix typo"
```

> [!TIP]
> **Detailliert erklärt:** [cookbook/05-issue-to-pr.md](cookbook/05-issue-to-pr.md)

### Workflow 2: Watch-Modus (24/7-Betrieb)

```bash
# Ersteinrichtung (einmalig)
python3 agent_start.py --install-service

# Betriebsmodi aktivieren
./start_night.sh    # → Autonomer Betrieb (Auto-Issues bei Regression)
./start_patch.sh    # → Entwicklungs-Modus (kein Auto-Issue)
./stop_agent.sh     # → Idle

# Status prüfen
./agent_status.sh   # → Modus, Laufzeit, Score, offene Issues
```

> [!TIP]
> **Systemd-Integration:** [cookbook/15-watch-mode-systemd.md](cookbook/15-watch-mode-systemd.md)

### Workflow 3: Dual-Repo (Agent auf sich selbst anwenden)

```bash
# Agent-Code ändern
python3 agent_start.py --self --issue 77

# Self-Consistency-Check läuft automatisch vor PR
# → Prüft: Labels existieren, CLI-Flags haben Handler, etc.
```

> [!TIP]
> **Details:** [cookbook/07-multiple-repos.md](cookbook/07-multiple-repos.md)

---

## 📊 Dashboard-Beispiel

Das Live-Dashboard (`dashboard.html`) zeigt:

- **Score-Verlauf:** Chart der letzten 24 Stunden
- **System-Status:** Server/Worker-Pings
- **Fehleranalyse:** Systematisch fehlschlagende Test-Tags
- **Performance:** Latenz-Trends

![Dashboard Preview](Documentation/img/dashboard-preview.svg)

> [!TIP]
> **Dashboard aktivieren:** `python3 agent_start.py --watch --dashboard` → [cookbook/30-dashboard-customization.md](cookbook/30-dashboard-customization.md)

---

## 🛡️ Sicherheit & Best Practices

### Token-Management

```bash
# .env-Datei (nie committen!)
GITEA_TOKEN=abc123...
LLM_API_KEY=sk-...

# .gitignore
.env
.env.*
*.key
```

> [!WARNING]
> **Auto-Merge-Risiko:** Nur für Entwicklungs-Repos aktivieren. Produktions-Repos → manuelles Review erforderlich.

### Prozess-Enforcement

- ✅ **Freigabe-Pflicht:** Kein Code ohne "ok"-Kommentar
- ✅ **Eval-Gate:** Tests müssen bestehen (Baseline-Check)
- ✅ **Branch-Protection:** Nie direkt auf `main` pushen
- ✅ **Diff-Validation:** Warnung bei Out-of-Scope-Änderungen

> [!IMPORTANT]
> **Security-Guide:** Token-Rotation, Input-Validation, Audit-Logging → [cookbook/41-security-guide.md](cookbook/41-security-guide.md)

---

## 🤝 Community & Support

- **GitHub Issues:** [github.com/Alexander-Benesch/Gitea-Agent/issues](https://github.com/Alexander-Benesch/Gitea-Agent/issues)
- **Cookbook:** [cookbook/README.md](cookbook/README.md) — 41 Rezepte mit Troubleshooting
- **API-Dokumentation:** [Documentation/](Documentation/) — Tiefe technische Details

### Beitragen

Pull Requests sind willkommen! Bitte:
1. Issue öffnen zur Diskussion
2. Branch erstellen: `fix/issue-NR` oder `feat/issue-NR`
3. Tests schreiben (`agent_eval.json`)
4. PR mit Conventional-Commit-Message

---

## 📄 Lizenz

MIT License — siehe [LICENSE](LICENSE)

---

## 🙏 Credits

Entwickelt von einem Nicht-Entwickler mit viel LLM-Hilfe. Läuft produktiv auf:
- Gitea (Synology NAS)
- Agent (Jetson Orin Nano 8 GB)
- LLM (Claude Code, Gemini)

**Danke an:** Die Open-Source-Community für Gitea, Python, und alle die dieses Projekt inspiriert haben.

---

> **"Kein Cloud-Zwang. Keine externen Dependencies. Läuft auf kleiner Hardware."**
> 
> → [Quick Start](#-quick-start) | [Cookbook](cookbook/README.md) | [GitHub](https://github.com/Alexander-Benesch/Gitea-Agent)
