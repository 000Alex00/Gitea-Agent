## Dein erstes Issue automatisieren

Von "ready-for-agent" bis zum PR in 3 Befehlen — ohne LLM-Session.

---

### Voraussetzungen

> [!IMPORTANT]
> - Projekt eingerichtet ([Rezept 02](02-first-setup.md))
> - Tests konfiguriert ([Rezept 09](09-first-test.md))
> - Gitea-Issue vorhanden mit Label `ready-for-agent`

---

### Problem

Du willst schnell ausprobieren ob der Agent funktioniert. Ohne komplexe LLM-Session, nur die Basics: Plan → Freigabe → PR.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Vorbereitung: Issue in Gitea erstellen
# ──────────────────────────────────────────────────────────
# Web-UI: Neue Issue
# Titel: "README.md: Typo in Zeile 5 korrigieren"
# Body: "Bitte 'funktionirt' → 'funktioniert' in `README.md` ändern"
# Label: ready-for-agent

# ──────────────────────────────────────────────────────────
# Schritt 1: Plan generieren
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py --issue 1

# → [→] Plan-Kommentar wird gepostet...
# → [✓] Label: ready-for-agent → agent-proposed

# ──────────────────────────────────────────────────────────
# Schritt 2: Freigabe geben (in Gitea)
# ──────────────────────────────────────────────────────────
# Gehe zu Issue #1 in Gitea Web-UI
# Kommentiere: "ok"

# ──────────────────────────────────────────────────────────
# Schritt 3: Branch + Kontext erstellen
# ──────────────────────────────────────────────────────────
python3 agent_start.py --implement 1

# → [✓] Branch erstellt: docs/issue-1-readme-typo
# → [✓] Kontext generiert: workspace/open/1-enhancement/
# → [✓] Label: agent-proposed → in-progress

# ──────────────────────────────────────────────────────────
# Schritt 4: Datei manuell ändern (ohne LLM)
# ──────────────────────────────────────────────────────────
cd ~/mein-projekt
nano README.md
# Zeile 5: funktionirt → funktioniert

git add README.md
git commit -m "docs: typo in README.md korrigiert"

# ──────────────────────────────────────────────────────────
# Schritt 5: PR erstellen
# ──────────────────────────────────────────────────────────
cd ~/Gitea-Agent
python3 agent_start.py --pr 1 \
  --branch docs/issue-1-readme-typo \
  --summary "Typo in README.md korrigiert"

# → [Eval] PASS — Score: 3.0 / 3.0
# → [✓] PR #1 erstellt
# → [✓] Label: in-progress → needs-review
```

---

### Erklärung

**Was macht `--issue`?**
- Liest Issue-Body aus Gitea
- Findet relevante Dateien (Backticks + AST + Keywords)
- Bestimmt Risikostufe (1-4) basierend auf Labels + Titel
- Generiert Plan-Kommentar mit Metadaten-Block
- Wechselt Label zu `agent-proposed`

**Was macht `--implement`?**
- Prüft Freigabe (Kommentar mit "ok" nach letztem Agent-Kommentar)
- Erstellt Feature-Branch (Format: `prefix/issue-N-slug`)
- Generiert `starter.md` + `files.md` in `workspace/open/N-type/`
- Wechselt Label zu `in-progress`

**Was macht `--pr`?**
- Prüft 8 Vorbedingungen (Branch, Plan, Eval, etc.)
- Führt `evaluation.run()` aus (alle Tests)
- Erstellt PR in Gitea (nur bei PASS)
- Postet Abschluss-Kommentar mit Score
- Wechselt Label zu `needs-review`

**Branch-Naming:**
```
docs/issue-1-readme-typo      # Label: documentation
fix/issue-2-server-crash      # Label: bug
feat/issue-3-new-api          # Label: Feature request
chore/issue-4-cleanup         # kein spezielles Label
```

---

### Best Practice

> [!TIP]
> **Auto-Scan statt --issue:**
> ```bash
> python3 agent_start.py
> # → Scannt alle Issues, führt jeweils passenden Schritt aus
> # → ready-for-agent: Plan posten
> # → agent-proposed + Freigabe: --implement ausführen
> ```

> [!TIP]
> **Issue-Body mit Backticks:**
> ```
> ✅ "Bitte `README.md` und `docs/setup.md` anpassen"
> ❌ "Bitte README und Setup-Docs anpassen"
> ```
> → Agent findet Dateien automatisch

> [!TIP]
> **Plan prüfen vor Freigabe:**
> ```
> Risikostufe: 1/4 (niedrig)
> Betroffene Dateien:
> - README.md (Zeilen 1-50)
> 
> OK zum Implementieren?
> ```
> → Prüfe dass Dateien + Zeilen stimmen

---

### Warnung

> [!WARNING]
> **Freigabe am falschen Ort:**
> ```
> [!] Keine Freigabe gefunden nach letztem Agent-Kommentar
> ```
> → Freigabe MUSS nach dem `🤖 Agent-Metadaten`-Block sein

> [!WARNING]
> **Branch existiert bereits:**
> ```bash
> git branch -D docs/issue-1-readme-typo
> python3 agent_start.py --implement 1
> ```

> [!WARNING]
> **Eval blockiert PR:**
> ```
> [Eval] FAIL — Score: 5.0, Baseline: 7.0
> [!] PR nicht erstellt (Eval FAIL)
> ```
> → Erst Tests fixen, dann erneut `--pr` aufrufen

---

### Nächste Schritte

✅ Ersten PR erstellt  
→ [05 — Standard-Workflow verstehen](05-issue-to-pr.md)  
→ [09 — Tests einrichten](09-first-test.md)
