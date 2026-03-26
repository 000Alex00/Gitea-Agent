## Manueller Workflow ohne Auto-Scan

Volle Kontrolle: --issue, --implement, --pr einzeln steuern.

---

### Voraussetzungen

> [!IMPORTANT]
> - Projekt eingerichtet ([Rezept 02](02-first-setup.md))
> - Gitea-Issue vorhanden (Label egal)

---

### Problem

Du willst nicht dass der Agent automatisch Issues scannt. Du willst jeden Schritt explizit kontrollieren.

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# Manueller Ablauf: jeder Schritt explizit
# ──────────────────────────────────────────────────────────

# Schritt 1: Alle ready-for-agent Issues auflisten
python3 agent_start.py --list
# → Issue #21: "Timeout erhöhen" (ready-for-agent)
# → Issue #22: "Bug in Login" (ready-for-agent)

# Schritt 2: Spezifisches Issue bearbeiten
python3 agent_start.py --issue 21
# → Nur Issue #21, nicht #22

# Schritt 3: In Gitea Freigabe geben
# (manuell im Browser: Kommentar "ok")

# Schritt 4: Branch erstellen
python3 agent_start.py --implement 21

# Schritt 5: Code ändern (manuell oder LLM)
cd ~/mein-projekt
# ... Änderungen ...
git commit -m "fix: timeout erhöht"

# Schritt 6: PR erstellen
python3 agent_start.py --pr 21 --branch fix/issue-21-timeout --summary "Timeout auf 8s"
```

**Versus Auto-Scan:**
```bash
# Auto-Scan (alles automatisch):
python3 agent_start.py
# → Plant alle ready-for-agent Issues
# → Implementiert alle agent-proposed Issues mit Freigabe
# → Zeigt Status aller in-progress Issues

# Manuell (selektiv):
python3 agent_start.py --issue 21  # nur dieses Issue
```

---

### Erklärung

**Warum manuell?**
- Kontrolle über Reihenfolge
- Parallele Bearbeitung mehrerer Issues verhindern
- Gezieltes Testen einzelner Workflows
- Debugging bei Problemen

**Auto-Scan vs. Manuell:**

| Befehl | Auto-Scan | Manuell |
|--------|-----------|---------|
| `python3 agent_start.py` | Alle Issues | — |
| `python3 agent_start.py --issue 21` | — | Nur #21 |
| `python3 agent_start.py --list` | — | Anzeige |

---

### Best Practice

> [!TIP]
> **Liste vor Aktion:**
> ```bash
> python3 agent_start.py --list
> # → Übersicht aller ready-for-agent Issues
> # → Wähle aus, welches zuerst
> ```

> [!TIP]
> **Status-Check ohne Aktion:**
> ```bash
> python3 agent_start.py --list
> # → Zeigt nur an, ändert nichts
> ```

> [!TIP]
> **Kombination mit --self:**
> ```bash
> python3 agent_start.py --self --list
> python3 agent_start.py --self --issue 42
> # → Manueller Workflow für Agent-Eigenentwicklung
> ```

---

### Warnung

> [!WARNING]
> **Auto-Scan kann unerwartete Aktionen ausführen:**
> ```bash
> python3 agent_start.py
> # → Plant ALLE ready-for-agent Issues auf einmal
> # → Implementiert ALLE freigegebenen Issues
> ```

> [!WARNING]
> **--implement ohne Freigabe:**
> ```
> [!] Keine Freigabe gefunden
> → Erst Freigabe geben, dann --implement
> ```

---

### Nächste Schritte

✅ Manueller Workflow verstanden  
→ [05 — Standard-Workflow](05-issue-to-pr.md)  
→ [06 — Bugfix-Workflow](06-bugfix-on-branch.md)
