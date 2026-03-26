## Eval-Failure debuggen

Baseline-Issues, Server-Offline, Token-Probleme.

---

### Voraussetzungen

> [!IMPORTANT]
> - Eval konfiguriert ([Rezept 09](09-first-test.md))
> - Tests laufen manchmal

---

### Problem

Eval schlägt fehl aber warum? Fehler ist unklar.

---

### Lösung

```bash
# ══════════════════════════════════════════════════════════
# Problem 1: Server offline
# ══════════════════════════════════════════════════════════
cd ~/Gitea-Agent
python3 evaluation.py --project ~/mein-projekt

# Output:
# [✗] Connection Error: http://localhost:8000/chat
# [✗] ConnectionRefusedError: [Errno 111]

# Debugging:
curl http://localhost:8000/health
# curl: (7) Failed to connect

# Lösung:
sudo systemctl status mein-server
# → inactive (dead)

sudo systemctl start mein-server

# ══════════════════════════════════════════════════════════
# Problem 2: Baseline zu hoch
# ══════════════════════════════════════════════════════════
python3 evaluation.py --project ~/mein-projekt

# Output:
# [Eval] FAIL — Score: 6.0, Baseline: 8.0
# Test "RAG-Query" PASS (2.0)
# Test "Context" PASS (2.0)
# Test "Validation" PASS (2.0)
# Test "Removed" NOT FOUND (0.0)  ← Ursache

# Debugging:
cat ~/mein-projekt/data/baseline.json
# {"score": 8.0}

cat ~/mein-projekt/config/agent_eval.json | grep weight
# → Summe: 6.0 (Test "Removed" wurde gelöscht)

# Lösung:
python3 evaluation.py --project ~/mein-projekt --update-baseline
# → Baseline: 8.0 → 6.0

# ══════════════════════════════════════════════════════════
# Problem 3: Keywords nicht gefunden
# ══════════════════════════════════════════════════════════
python3 evaluation.py --project ~/mein-projekt --verbose

# Output:
# Test "RAG-Query" FAIL
# Expected: ["Kapitel", "Inhalt"]
# Got: "Das Kapital handelt von..."
#      ^^^^^^^^
# → "Kapitel" gefunden, aber "Inhalt" fehlt

# Debugging:
# Server-Antwort prüfen:
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Was steht in Kapitel 1?"}'

# Response:
# {"response": "Das Kapitel handelt von Python-Grundlagen"}

# Lösung:
nano ~/mein-projekt/config/agent_eval.json
# Ändere:
# "expected_keywords": ["Kapitel", "Inhalt"]
# → "expected_keywords": ["Kapitel"]

# ══════════════════════════════════════════════════════════
# Problem 4: Timeout
# ══════════════════════════════════════════════════════════
python3 evaluation.py --project ~/mein-projekt --verbose

# Output:
# Test "Long-Query" FAIL
# Timeout: 8500ms > 5000ms

# Debugging:
# Test einzeln ausführen:
time curl -X POST http://localhost:8000/chat \
  -d '{"message": "Erkläre Quantenphysik"}'

# → 8.5 Sekunden

# Lösung A: Timeout erhöhen
nano ~/mein-projekt/config/agent_eval.json
# "max_response_ms": 10000  (global)
# oder:
# {"name": "Long-Query", "max_response_ms": 10000}

# Lösung B: Server optimieren
# → Model kleiner, Batch-Size reduzieren

# ══════════════════════════════════════════════════════════
# Problem 5: Token-Fehler (Gitea)
# ══════════════════════════════════════════════════════════
python3 agent_start.py --project ~/mein-projekt --issue 42

# Output:
# [✗] Gitea API Error: 401 Unauthorized

# Debugging:
curl -H "Authorization: token $GITEA_TOKEN" \
  https://gitea.example.com/api/v1/user

# → {"message": "token is expired"}

# Lösung:
# Gitea → Settings → Applications → Regenerate Token
nano ~/mein-projekt/.env
# GITEA_TOKEN=<neuer_token>

# ══════════════════════════════════════════════════════════
# Problem 6: Score-History korrupt
# ══════════════════════════════════════════════════════════
python3 evaluation.py --project ~/mein-projekt

# Output:
# [✗] JSONDecodeError: score_history.json

# Debugging:
cat ~/mein-projekt/data/score_history.json
# {"history": [{"score": 8.0, ...},
# → Datei abgeschnitten / korrupt

# Lösung:
rm ~/mein-projekt/data/score_history.json
python3 evaluation.py --project ~/mein-projekt
# → Neue History wird angelegt
```

---

### Erklärung

**Debugging-Tools:**

| Tool | Use-Case |
|------|----------|
| `--verbose` | Detaillierte Logs |
| `--debug` | Noch mehr Details (HTTP-Bodies) |
| `--dry-run` | Simulation ohne Änderungen |
| `curl` | Server-Endpunkte manuell testen |
| `tail -f *.log` | Live-Logs beobachten |

**Häufige Fehlerquellen:**

1. **Server offline/crashed**
2. **Baseline veraltet** (Tests geändert)
3. **Keywords zu strikt** (LLM paraphrasiert)
4. **Timeout zu niedrig** (Server langsam)
5. **Token expired** (Gitea/LLM)
6. **JSON korrupt** (Disk-Full, Crash während Write)

---

### Best Practice

> [!TIP]
> **Health-Check vor Eval:**
> ```bash
> python3 agent_start.py --project ~/proj --doctor
> # [✓] Server erreichbar
> # [✓] Gitea-Token gültig
> # [✓] Config valid
> ```

> [!TIP]
> **Backup vor Baseline-Update:**
> ```bash
> cp ~/proj/data/baseline.json ~/proj/data/baseline.json.backup
> python3 evaluation.py --project ~/proj --update-baseline
> ```

> [!TIP]
> **Logging aktivieren:**
> ```bash
> # .env
> LOG_LEVEL=DEBUG
> LOG_FILE=data/debug.log
> 
> tail -f ~/proj/data/debug.log
> ```

---

### Warnung

> [!WARNING]
> **Baseline löschen:**
> ```bash
> rm ~/proj/data/baseline.json
> → Nächster Eval: Score wird neue Baseline (egal wie niedrig)
> ```

> [!WARNING]
> **--update-baseline bei Failures:**
> ```bash
> Eval FAIL (Score: 2.0, Baseline: 8.0)
> python3 evaluation.py --update-baseline
> → Baseline wird auf 2.0 gesenkt (FALSCH!)
> ```
> → Nur bei absichtlichen Test-Änderungen

> [!WARNING]
> **Verbose-Mode in Production:**
> ```bash
> --verbose → Logs enthalten Server-Responses
> → Sensitive Daten in Logs
> ```

---

### Nächste Schritte

✅ Eval-Debugging verstanden  
→ [35 — Empty-Agent-Comments](35-empty-agent-comments.md)  
→ [36 — Watch-Modus Crashes](36-watch-mode-crashes.md)  
→ [09 — Ersten Test](09-first-test.md)
