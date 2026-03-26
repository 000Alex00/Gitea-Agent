# gitea-agent COOKBOOK

**LLM-agnostischer Agent-Workflow für Gitea Issues**

Strukturiertes Issue-Management mit KI-Agenten: Issue analysieren → Plan posten → Freigabe einholen → Branch + Implementierung → PR erstellen. Kein Cloud-Zwang. Python 3.10+ Stdlib only.

---

## 📚 Inhaltsverzeichnis

### 🚀 Getting Started

| Rezept | Thema | Beschreibung |
|--------|-------|--------------|
| [01](01-installation.md) | **Installation & Systemvoraussetzungen** | gitea-agent lokal einrichten — einmalig, für alle Projekte |
| [02](02-first-setup.md) | **Erstes Projekt einrichten (Setup-Wizard)** | Interaktiver 6-Schritt-Wizard für neues Projekt |
| [03](03-first-issue.md) | **Dein erstes Issue automatisieren** | Von "ready-for-agent" bis zum PR in 3 Befehlen |
| [04](04-health-check.md) | **System-Zustand prüfen (--doctor)** | Alle Verbindungen und Konfigurationen auf einen Blick |

### 🔄 Core Workflow

| Rezept | Thema | Beschreibung |
|--------|-------|--------------|
| [05](05-issue-to-pr.md) | **Standard-Workflow: Issue → PR** | Plan → Freigabe → Branch → Code → PR (vollständiger Durchlauf) |
| [06](06-bugfix-on-branch.md) | **Bugfix während Implementierung (--fixup)** | Schneller Commit-Kommentar für in-progress Issues |
| [07](07-multiple-repos.md) | **Zwei Repos — Ein Agent (--self)** | Agent auf sich selbst anwenden + normales Projekt parallel |
| [08](08-manual-workflow.md) | **Manueller Workflow ohne Auto-Scan** | Volle Kontrolle: --issue, --implement, --pr einzeln |

### ✅ Testing & Evaluation

| Rezept | Thema | Beschreibung |
|--------|-------|--------------|
| [09](09-first-test.md) | **Ersten Eval-Test schreiben** | Minimal-Konfiguration agent_eval.json für Smoke-Tests |
| [10](10-multi-step-tests.md) | **Mehrstufige Tests (steps)** | Fakt schreiben → abfragen: Context-Persistence testen |
| [11](11-baseline-management.md) | **Eval-Baseline setzen & aktualisieren** | Score-Schwellwerte nach Änderungen neu kalibrieren |
| [12](12-performance-tests.md) | **Latenz-Tests mit max_response_ms** | Performance-Regression automatisch erkennen |
| [13](13-test-generation.md) | **Tests LLM-generieren lassen (--generate-tests)** | Automatisch pytest + agent_eval-Tests aus Issues |

### 🤖 Watch-Modus & Automation

| Rezept | Thema | Beschreibung |
|--------|-------|--------------|
| [14](14-watch-mode-tmux.md) | **Watch-Modus mit tmux starten** | Dauerbetrieb: Eval-Loop + Auto-Issues bei Regression |
| [15](15-watch-mode-systemd.md) | **Watch als Systemd-Dienst** | Automatischer Start beim Boot mit systemd |
| [16](16-night-vs-patch.md) | **Betriebsmodi: Night / Patch / Idle** | Wann Auto-Issues, wann nur Monitoring |
| [17](17-consecutive-pass-gate.md) | **Auto-Issues erst nach N× PASS schließen** | Falsch-Positives vermeiden: 3 Zyklen bestehen statt 1 |
| [18](18-tag-aggregation.md) | **Systematische Fehler erkennen (Tags)** | Wiederkehrende Fehlertypen automatisch melden |
| [19](19-staleness-check.md) | **PR mit veraltetem Server verhindern** | Server-Code-Check vor PR-Erstellung |

### 🛠️ Advanced Features

| Rezept | Thema | Beschreibung |
|--------|-------|--------------|
| [20](20-ast-skeleton.md) | **AST-Repository-Skelett erstellen** | Token-Einsparung: 98% weniger Context via Slices |
| [21](21-codesegment-strategy.md) | **Volltext durch Slices ersetzen** | LLM sieht nur Struktur, lädt Zeilen on-demand |
| [22](22-diff-validation.md) | **Änderungen auf Issue-Scope prüfen** | Warnung bei Out-of-Scope-Edits vor PR |
| [23](23-search-replace-patches.md) | **SEARCH/REPLACE-Patches anwenden** | LLM-agnostisches Patch-Format mit 5-Schritt-Sicherheitsnetz |
| [24](24-gitea-version-compare.md) | **AST-Diff bei Regression zeigen** | Was hat sich strukturell geändert seit Score-Einbruch |
| [25](25-log-analyzer.md) | **Projekt-eigene Log-Analyse** | Eigene log_analyzer.py in Watch-Zyklus integrieren |

### 🔧 Configuration & Customization

| Rezept | Thema | Beschreibung |
|--------|-------|--------------|
| [26](26-env-configuration.md) | **.env vs .env.agent verstehen** | Umgebungsvariablen für Dual-Repo-Setup |
| [27](27-eval-json-reference.md) | **agent_eval.json Referenz** | Alle Konfigurations-Felder mit Beispielen |
| [28](28-labels-and-workflow.md) | **Label-System anpassen** | Risikostufen, Branch-Präfixe, Freigabe-Keywords |
| [29](29-context-excludes.md) | **Dateien vom Context ausschließen** | exclude_dirs für große/irrelevante Ordner |
| [30](30-dashboard-customization.md) | **Dashboard anpassen & deployen** | HTML-Dashboard für Team-Visibility |

### 🧩 Plugins & Extensions

| Rezept | Thema | Beschreibung |
|--------|-------|--------------|
| [31](31-plugin-architecture.md) | **Plugin-System verstehen** | Wie patch.py und changelog.py funktionieren |
| [32](32-create-custom-plugin.md) | **Eigenes Plugin schreiben** | Template für neue plugins/my_feature.py Module |
| [33](33-changelog-automation.md) | **CHANGELOG.md automatisch generieren** | Conventional Commits → Markdown-Changelog |

### 🐛 Troubleshooting

| Rezept | Thema | Beschreibung |
|--------|-------|--------------|
| [34](34-debug-eval-fail.md) | **Eval gibt FAIL obwohl alles läuft** | Baseline zu hoch? Server offline? Debug-Schritte |
| [35](35-empty-agent-comments.md) | **Agent-Kommentare sind leer** | Bot-Token-Problem: Scopes & Auth prüfen |
| [36](36-watch-mode-crashes.md) | **Watch-Modus stürzt ab** | Typische Fehler: Netzwerk, Disk voll, Import-Fehler |
| [37](37-search-replace-no-match.md) | **SEARCH/REPLACE matcht nicht** | Whitespace, CRLF, Datei-Änderungen debuggen |

### 📚 Reference

| Rezept | Thema | Beschreibung |
|--------|-------|--------------|
| [38](38-cli-reference.md) | **Vollständige CLI-Befehlsreferenz** | Alle --flags mit Beispielen in einer Tabelle |
| [39](39-api-functions.md) | **Funktions-Referenz (evaluation, gitea_api)** | Alle öffentlichen Funktionen dokumentiert |
| [40](40-best-practices.md) | **Best Practices & Patterns** | Issue-Qualität, Test-Design, Sicherheit |
| [41](41-security-guide.md) | **Sicherheitshinweise** | Token-Management, keine Auto-Merges, Netzwerk-Isolation |

---

## 🎯 Schnelleinstieg

**Neu hier?** Starte mit:
1. [Installation](01-installation.md) — Python 3.10+, git, Gitea-Zugang
2. [Erstes Projekt](02-first-setup.md) — Setup-Wizard durchlaufen
3. [Erstes Issue](03-first-issue.md) — Von Label bis PR in 3 Befehlen

**Produktiv-Einsatz?** Direkt zu:
- [Standard-Workflow](05-issue-to-pr.md) — täglicher Ablauf
- [Ersten Test schreiben](09-first-test.md) — Qualitätssicherung aktivieren
- [Watch-Modus](14-watch-mode-tmux.md) — 24/7-Betrieb einrichten

---

## 🔗 Weitere Ressourcen

- **Haupt-README**: `../README.md` (Projekt-Übersicht)
- **API-Dokumentation**: `../docs/` (Tiefe technische Details)
- **GitHub**: [Alexander-Benesch/Gitea-Agent](https://github.com/Alexander-Benesch/Gitea-Agent)
