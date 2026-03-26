## System-Zustand prüfen (--doctor)

Health-Check: alle Verbindungen und Konfigurationen auf einen Blick.

---

### Voraussetzungen

> [!IMPORTANT]
> - gitea-agent installiert ([Rezept 01](01-installation.md))
> - `.env` vorhanden (manuell oder via [Setup-Wizard](02-first-setup.md))

---

### Problem

Du bist unsicher ob deine Konfiguration stimmt: Gitea erreichbar? Token korrekt? Labels vorhanden? Projektpfad valide?

---

### Lösung

```bash
cd ~/Gitea-Agent
python3 agent_start.py --doctor

# ──────────────────────────────────────────────────────────
# Ausgabe:
# ──────────────────────────────────────────────────────────
[✓] Gitea-Verbindung — http://localhost:3000 (admin)
[✓] Repository — admin/mein-projekt erreichbar
[✓] Projektverzeichnis — /home/user/mein-projekt existiert
[✓] repo_skeleton.json — 15 Dateien, 234 Symbole
[✓] agent_eval.json — 3 Tests konfiguriert
[✓] Labels — 4/4 vorhanden
    - ready-for-agent (grün)
    - agent-proposed (gelb)
    - in-progress (blau)
    - needs-review (orange)
[✓] .env — alle Pflichtfelder gesetzt

────────────────────────────────────────────────────────────
Health-Check: OK (7/7)
```

---

### Erklärung

**7 geprüfte Bereiche:**

1. **Gitea-Verbindung:** GET `/api/v1/user` mit Token
2. **Repository:** GET `/api/v1/repos/{repo}` erreichbar
3. **Projektverzeichnis + Skeleton-Staleness:** `PROJECT_ROOT` existiert + `.git` vorhanden + mtime-Vergleich `repo_skeleton.md` vs. `.py`-Dateien
4. **repo_skeleton.json:** Falls vorhanden → Statistik
5. **agent_eval.json:** Falls vorhanden → Anzahl Tests
6. **Labels:** Alle 4 Workflow-Labels in Gitea vorhanden
7. **LLM-Config-Guard:** Prüft `CLAUDE.md`, `.cursorrules`, `.clinerules`, `copilot-instructions.md`, `windsurfrules`, `GEMINI.md`, `AGENTS.md` auf Aktualität und Konsistenz

**Fehlerfälle:**
```bash
[!] Gitea-Verbindung — Timeout nach 10s
[!] Labels — 2/4 fehlen:
    ✗ in-progress
    ✗ needs-review
[⚠] repo_skeleton.json — nicht gefunden (optional)
```

**Ergebnis:**
```
Health-Check: WARN (5/7) — 2 Fehler
```

---

### Best Practice

> [!TIP]
> **Nach Setup immer --doctor:**
> ```bash
> python3 agent_start.py --setup
> # → Wizard endet automatisch mit --doctor
> ```

> [!TIP]
> **Ergebnis speichern:**
> ```bash
> python3 agent_start.py --doctor > doctor_last.txt
> # → Für Troubleshooting
> ```

> [!TIP]
> **Dashboard zeigt letzten Check:**
> ```bash
> python3 agent_start.py --dashboard
> # → HTML enthält Health-Check-Sektion (falls doctor_last.json vorhanden)
> ```

---

### Warnung

> [!WARNING]
> **Token-Scopes prüfen:**
> ```
> [!] Gitea-Verbindung — 403 Forbidden
> → Token-Scopes: issue (read+write) + repository (read+write)
> ```

> [!WARNING]
> **Falsche URL/Repo:**
> ```
> [!] Repository — 404 Not Found
> → Prüfe GITEA_REPO in .env (Format: user/name)
> ```

> [!WARNING]
> **PROJECT_ROOT falsch:**
> ```
> [!] Projektverzeichnis — kein .git gefunden
> → Muss auf git-Repository zeigen
> ```

---

### Nächste Schritte

✅ System geprüft  
→ [03 — Erstes Issue](03-first-issue.md)  
→ [05 — Standard-Workflow](05-issue-to-pr.md)
