## Standard-Workflow: Issue → PR

Der vollständige Durchlauf: von einem Gitea-Issue bis zum fertigen Pull Request.

---

### Voraussetzungen

> [!IMPORTANT]
> - gitea-agent installiert ([Rezept 01](01-installation.md))
> - Projekt eingerichtet ([Rezept 02](02-first-setup.md))
> - Gitea-Issue mit Label `ready-for-agent`
> - LLM-Session bereit (z.B. Claude Code, Aider, Gemini CLI)

---

### Problem

Du hast ein Issue in Gitea, das der Agent bearbeiten soll. Du brauchst einen klaren Ablauf: Plan erstellen → Freigabe → Implementierung → Tests → PR.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Schritt 1: Issue in Gitea vorbereiten
# ──────────────────────────────────────────────────────────
# Web-UI: Neue Issue erstellen
# Titel: "Timeout in web_search.py auf 8s erhöhen"
# Body: "Bitte Timeout in `myproject/plugins/web_search.py` auf 8s setzen."
# Label: ready-for-agent
# → Dateien in Backticks erwähnen für Auto-Context!

# ──────────────────────────────────────────────────────────
# Schritt 2: Plan generieren
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py --issue 61

# → Agent postet Plan-Kommentar ins Issue
# → Label wechselt: ready-for-agent → agent-proposed
# → Bei Risikostufe 2/3: zusätzliche Rückfragen

# ──────────────────────────────────────────────────────────
# Schritt 3: Freigabe geben (in Gitea Web-UI)
# ──────────────────────────────────────────────────────────
# Kommentar schreiben: "ok" oder "ja" oder "✅"
# → Freigabe-Keywords aus settings.py: ok, yes, ja, approved, 👍, ✅

# ──────────────────────────────────────────────────────────
# Schritt 4: Branch + Kontext erstellen
# ──────────────────────────────────────────────────────────
python3 agent_start.py --implement 61

# → Prüft Freigabe (muss NACH letztem Agent-Kommentar sein)
# → Erstellt Branch: git checkout -b fix/issue-61-timeout-web-search
# → Label: agent-proposed → in-progress
# → Generiert Kontext-Dateien:
#    - contexts/61-enhancement/starter.md  (Auftrag + Regeln)
#    - contexts/61-enhancement/files.md    (relevante Dateien)

# ──────────────────────────────────────────────────────────
# Schritt 5: Code ändern (LLM-Session)
# ──────────────────────────────────────────────────────────
# In deiner LLM-Session (z.B. Claude Code):
# 1. Lade starter.md + files.md
# 2. LLM ändert Code
# 3. LLM committet nach jeder Datei

# Beispiel mit Claude Code:
# $ claude
# > Bitte lade contexts/61-enhancement/starter.md
# > [LLM ändert myproject/plugins/web_search.py]
# > git add myproject/plugins/web_search.py
# > git commit -m "fix: timeout auf 8s erhöht"

# ──────────────────────────────────────────────────────────
# Schritt 6: PR erstellen (mit Eval)
# ──────────────────────────────────────────────────────────
python3 agent_start.py --pr 61 \
  --branch fix/issue-61-timeout-web-search \
  --summary "Timeout von 5s auf 8s erhöht (web_search.py)"

# → Prüft 8 Vorbedingungen (Plan, Eval, Diff, etc.)
# → Führt evaluation.run() aus (alle Tests)
# → Bei FAIL: PR blockiert, Fehler-Kommentar ins Issue
# → Bei PASS: PR auf Gitea erstellt
# → Label: in-progress → needs-review
# → Abschluss-Kommentar mit Score + Verlauf + Emoji-Status
```

---

### Erklärung

**Warum Freigabe-Pflicht?**
- Verhindert dass Agent ohne Review Code ändert.
- Bei Risikostufe 2/3 (bugs, features) stellt Agent Rückfragen.
- Mensch bleibt immer in Kontrolle.

**Was ist `starter.md`?**
- Strukturierter Auftrag für das LLM.
- Enthält: Issue-Text, betroffene Dateien, Pflicht-Regeln, Checkliste.
- LLM-agnostisch: funktioniert mit Claude, Gemini, Aider, etc.

**Was macht `files.md`?**
- Listet relevante Dateien auf (via Backticks + AST-Import-Analyse + Keyword-Suche).
- Kann Volltext oder nur Skelett enthalten (abhängig von [Codesegment-Strategie](21-codesegment-strategy.md)).

**8 Vorbedingungen bei `--pr`:**
1. Branch ≠ main/master
2. Plan-Kommentar vorhanden
3. Agent-Metadaten-Block im Plan
4. Eval nach letztem Commit
5. Server-Neustart empfohlen (Staleness-Check)
6. Agent Self-Consistency Check
7. Diff-Validierung (Warnung bei Out-of-Scope)
8. Slice-Warnung (ungelesene Dateien)

---

### Best Practice

> [!TIP]
> **Backticks in Issue-Body:**
> ```
> ✅ "Bitte `myproject/server.py` und `myproject/config.yaml` anpassen"
> ❌ "Bitte Server und Config anpassen"
> ```
> → Agent findet Dateien automatisch via Backtick-Parsing

> [!TIP]
> **--summary immer mitgeben:**
> ```bash
> python3 agent_start.py --pr 61 --branch fix/... \
>   --summary "Kurze Beschreibung der Änderung"
> ```
> → Erscheint prominent im PR-Kommentar

> [!TIP]
> **Eval-Baseline vorher prüfen:**
> ```bash
> cat ~/mein-projekt/agent/data/baseline.json
> # {"score": 7.0}
> ```
> → Wenn Score < Baseline: PR wird blockiert

---

### Warnung

> [!WARNING]
> **Ohne Freigabe geht `--implement` nicht:**
> ```
> [!] Keine Freigabe gefunden nach letztem Agent-Kommentar
> → Bitte "ok" kommentieren in Issue #61
> ```
> → Freigabe MUSS nach letztem `🤖 Agent-Metadaten`-Block sein

> [!WARNING]
> **Server-Code geändert?**
> ```bash
> # Staleness-Check kann PR blockieren
> python3 agent_start.py --pr 61 --branch fix/... --restart-before-eval
> # → Startet Server vor Eval automatisch neu
> ```

> [!WARNING]
> **Eval FAIL blockiert PR:**
> ```
> [Eval] FAIL — Score: 5.0, Baseline: 7.0
> → PR nicht erstellt
> ```
> → Erst Fehler fixen, dann erneut `--pr` aufrufen

---

### Nächste Schritte

✅ Ersten PR erstellt  
→ [06 — Bugfix während Implementierung](06-bugfix-on-branch.md)  
→ [09 — Ersten Eval-Test schreiben](09-first-test.md)  
→ [14 — Watch-Modus aktivieren](14-watch-mode-tmux.md)
