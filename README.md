# gitea-agent

LLM-agnostischer Agent-Workflow für Gitea Issues.

Verbindet einen LLM-Agenten (Claude Code, ChatGPT, lokales LLM, …) mit dem Gitea Issue-Tracker: Issue analysieren → Plan posten → Freigabe einholen → Branch + Implementierung → PR erstellen.

---

## Konzept

```
Gitea Issue (ready-for-agent)
        ↓
  agent_start.py --issue <NR>
        ↓
  LLM liest Code + Issue
        ↓
  Plan-Kommentar in Gitea posten
        ↓
  Mensch kommentiert "ok"
        ↓
  agent_start.py --implement <NR>
        ↓
  Branch erstellen + Implementieren
        ↓
  agent_start.py --pr <NR> --branch <branch>
        ↓
  PR in Gitea
```

Kein automatisches Deployment. Kein Auto-Merge. Der Mensch behält die Kontrolle über jeden Schritt.

---

## Installation

```bash
git clone http://your-gitea/gitea-agent
cd gitea-agent
cp .env.example .env
# .env befüllen (GITEA_URL, GITEA_USER, GITEA_TOKEN, GITEA_REPO)
```

Keine zusätzlichen Abhängigkeiten — nur Python 3.10+ Stdlib.

---

## Konfiguration

`.env` Datei im Projektverzeichnis (oder Umgebungsvariablen):

| Variable | Beschreibung | Beispiel |
|----------|-------------|---------|
| `GITEA_URL` | Gitea-Instanz URL | `http://192.168.1.x:3001` |
| `GITEA_USER` | Gitea-Benutzername | `admin` |
| `GITEA_TOKEN` | API-Token (Settings → Applications) | `abc123...` |
| `GITEA_REPO` | Repository (owner/name) | `admin/myproject` |
| `GITEA_BOT_USER` | Bot-User für Kommentare (optional) | `working-bot` |
| `GITEA_BOT_TOKEN` | API-Token des Bot-Users (optional) | `xyz789...` |
| `PROJECT_ROOT` | Pfad zum Projekt-Repo (optional) | `/home/user/myproject` |

**Token-Scopes:** `issue` (read+write), `repository` (read+write)

**Bot-User (optional):** Erstelle einen separaten Gitea-User (z.B. `working-bot`) damit Agent-Kommentare klar als Bot erkennbar sind. Nur API-Token nötig — kein SSH/GPG.

---

## Verwendung

```bash
# Auto-Modus (empfohlen): scannt alle Labels, arbeitet alles ab
python3 agent_start.py

# Manuell:
python3 agent_start.py --list                                    # Status-Übersicht
python3 agent_start.py --issue 16                                # Plan für Issue #16 posten
python3 agent_start.py --implement 16                            # Nach "ok": implementieren
python3 agent_start.py --pr 16 --branch fix/issue-16-xyz        # PR erstellen
python3 agent_start.py --pr 16 --branch fix/issue-16-xyz \
  --summary "- Funktion X geändert\n- Doku aktualisiert"        # PR mit Zusammenfassung
```

**Auto-Modus Ablauf:**
1. Erster Run → postet Pläne für alle `ready-for-agent` Issues
2. Du kommentierst `ok` in Gitea
3. Zweiter Run → implementiert alle freigegebenen Issues, postet PRs

---

## Labels (im Gitea-Repo anlegen)

| Label | Bedeutung |
|-------|-----------|
| `ready-for-agent` | Issue ist bereit zur Bearbeitung |
| `agent-proposed` | Plan wurde gepostet, wartet auf Freigabe |
| `in-progress` | Agent implementiert gerade |
| `needs-review` | PR erstellt, wartet auf Review |

Labels einmalig anlegen: Gitea → Repository → Issues → Labels

---

## Risiko-Klassifikation

Der Agent bewertet jedes Issue automatisch:

| Stufe | Beschreibung | Vorgehen |
|-------|-------------|---------|
| 1 | Docs, Cleanup, Kommentare | Direkte Implementierung möglich |
| 2 | Enhancements, Refactoring | Plan vor Implementierung |
| 3 | Bugs, neue Features | Plan + explizite Freigabe |
| 4 | Breaking Changes, Security | Manuell, kein Agent-Deploy |

---

## Workflow-Sicherheitsregeln

- **Commit-as-Checkpoint:** Nach jeder geänderten Datei sofort committen (verhindert Datenverlust bei LLM-Timeout)
- **Kein Auto-Merge:** PR wird erstellt, Mensch entscheidet über Merge
- **Kein Auto-Deploy:** Kein direkter Push auf `main` durch den Agenten
- **Freigabe-Pflicht:** `--implement` startet nur nach explizitem `ok`/`ja`/`✅` Kommentar

---

## Dateistruktur

```
gitea-agent/
├── agent_start.py   # Haupt-Einstiegspunkt, CLI
├── gitea_api.py     # Gitea REST API Wrapper
├── .env.example     # Konfigurationsvorlage
├── .env             # Secrets (nicht im Git!)
└── README.md
```

---

## Für andere LLMs

`agent_start.py` gibt strukturierten Text aus — dieser kann direkt als System-Prompt für andere LLMs verwendet werden:

```bash
# Output in Datei → als Kontext an anderes LLM übergeben
python3 agent_start.py --issue 16 > context.txt
```

Der Output enthält: Issue-Beschreibung, Risikostufe, erkannte Dateien, Branch-Befehl, Pflicht-Checkliste.

---

## Erweiterungsideen

- Cron-Job: einmal täglich `--list` → nächstes Issue automatisch bearbeiten
- Webhook: Gitea-Event bei neuem `ready-for-agent` Label triggert Agent
- Multi-Repo: `.env` je Projekt, `--root` für Projektwechsel
- Audit-Log: alle Agent-Aktionen in Datei schreiben
