## .env-Konfiguration (Field-Referenz)

Alle Umgebungsvariablen erklärt.

---

### Voraussetzungen

> [!IMPORTANT]
> - Basis-Setup durchgeführt ([Rezept 02](02-first-setup.md))

---

### Problem

Du willst wissen: welche .env-Felder gibt es? Was ist optional?

---

### Lösung

```bash
# ──────────────────────────────────────────────────────────
# ~/Gitea-Agent/.env
# ──────────────────────────────────────────────────────────

# ══════════════════════════════════════════════════════════
# PFLICHTFELDER
# ══════════════════════════════════════════════════════════

# Gitea-Server-URL (ohne trailing slash)
GITEA_URL=https://gitea.example.com

# Gitea-API-Token (Scopes: repo, write:issue, write:pull_request)
GITEA_TOKEN=abc123def456...

# Claude API aktivieren (Pflicht für LLM-Routing)
CLAUDE_API_ENABLED=true

# Lokaler LLM-Endpunkt (z.B. Ollama, optional)
LLM_LOCAL_URL=http://localhost:11434

# ══════════════════════════════════════════════════════════
# REPOSITORY-KONFIGURATION
# ══════════════════════════════════════════════════════════

# Gitea-Repo (Format: owner/repo)
GITEA_REPO=myuser/my-project

# Lokaler Repo-Pfad (absolut)
PROJECT_PATH=/home/user/my-project

# ══════════════════════════════════════════════════════════
# LLM-ROUTING (Neu)
# ══════════════════════════════════════════════════════════

# Routing-Konfiguration (Provider + Modell pro Task)
# → config/llm/routing.json ist der zentrale Konfig-Punkt
# → Unterstützte Provider: claude, openai, gemini, local (Ollama)
LLM_ROUTING_CONFIG=config/llm/routing.json

# Legacy-Felder (nur für direkten Modus ohne routing.json):
# LLM_API_URL=http://localhost:8000/v1/chat/completions
# LLM_MODEL=gpt-4

# ══════════════════════════════════════════════════════════
# WATCH-MODUS
# ══════════════════════════════════════════════════════════

# Eval-Intervall (Sekunden)
EVAL_INTERVAL=3600

# Night-Modus aktivieren (nur low-risk Issues)
NIGHT_MODE=false

# Consecutive-Pass-Gate (Issue-Schließ-Schwelle)
CONSECUTIVE_PASSES=2

# ══════════════════════════════════════════════════════════
# LLM-PARAMETER (global, Fallback wenn kein Routing)
# ══════════════════════════════════════════════════════════

# Temperature (0.0-2.0, höher = kreativer)
LLM_TEMPERATURE=0.7

# Max-Tokens (Response-Länge)
LLM_MAX_TOKENS=2048

# Context-Window (Input-Limit)
LLM_CONTEXT_WINDOW=8192

# ══════════════════════════════════════════════════════════
# LABELS & WORKFLOW
# ══════════════════════════════════════════════════════════

# Label-Präfix für Agent-Issues
LABEL_PREFIX=agent

# Auto-Merge aktivieren (VORSICHT!)
AUTO_MERGE=false

# Branch-Präfix für Agent-Branches
BRANCH_PREFIX=agent

# ══════════════════════════════════════════════════════════
# EVAL-KONFIGURATION
# ══════════════════════════════════════════════════════════

# Pfad zu agent_eval.json (relativ zu PROJECT_PATH)
EVAL_CONFIG=config/agent_eval.json

# Baseline-Datei (relativ zu PROJECT_PATH)
BASELINE_FILE=data/baseline.json

# Score-History (relativ zu PROJECT_PATH)
SCORE_HISTORY=data/score_history.json

# ══════════════════════════════════════════════════════════
# ERWEITERTE FEATURES
# ══════════════════════════════════════════════════════════

# AST-Skeleton aktivieren
USE_SKELETON=true

# Skeleton-Datei (relativ zu PROJECT_PATH)
SKELETON_FILE=data/repo_skeleton.json

# Diff-Validation (strict / warn / off)
DIFF_VALIDATION=warn

# Tag-Aggregation aktivieren
TAG_AGGREGATION=true

# Tag-Threshold (AnzahlFailedTests für Meta-Issue)
TAG_THRESHOLD=3

# Version-Compare aktivieren
VERSION_COMPARE=true

# Staleness-Check aktivieren
STALENESS_CHECK=true

# Staleness-Intervall (Sekunden)
STALENESS_INTERVAL=7200

# ══════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════

# Log-Level (DEBUG / INFO / WARNING / ERROR)
LOG_LEVEL=INFO

# Log-Datei (relativ zu PROJECT_PATH)
# Täglich rotiert: data/gitea-agent.log.YYYY-MM-DD
LOG_FILE=data/gitea-agent.log

# Log-Backup-Count (täglich rotiert, 10 Backups)
LOG_BACKUP_COUNT=10

# ══════════════════════════════════════════════════════════
# NETZWERK
# ══════════════════════════════════════════════════════════

# HTTP-Timeout (Sekunden)
HTTP_TIMEOUT=30

# Retry-Count (bei Netzwerkfehlern)
HTTP_RETRIES=3

# Retry-Delay (Sekunden)
HTTP_RETRY_DELAY=5
```

---

### Erklärung

**Feld-Kategorien:**

### Pflichtfelder
- `GITEA_URL`, `GITEA_TOKEN`, `CLAUDE_API_ENABLED`, `LLM_LOCAL_URL`
- Agent startet nicht ohne `GITEA_URL` und `GITEA_TOKEN`

### LLM-Routing (Neu)
- `LLM_ROUTING_CONFIG`: Zeigt auf `config/llm/routing.json`
- Routing-Datei definiert Provider + Modell pro Task (issue_analysis, implementation, etc.)
- Legacy: `LLM_API_URL` + `LLM_MODEL` nur für direkten Modus ohne Routing

### Watch-Modus
- `EVAL_INTERVAL`: Wie oft Eval läuft
- `NIGHT_MODE`: Filter auf low-risk Issues
- `CONSECUTIVE_PASSES`: Stabilität vor Issue-Close

### LLM-Parameter
- `LLM_TEMPERATURE`: Kreativität (0.0 = deterministisch, 2.0 = chaotisch)
- `LLM_MAX_TOKENS`: Längere Responses = mehr Tokens/Kosten
- `LLM_CONTEXT_WINDOW`: Model-abhängig (GPT-4: 8k/32k, Llama-2: 4k)

### Logging
- `LOG_FILE`: Basis-Dateiname, täglich rotiert (`data/gitea-agent.log.YYYY-MM-DD`)
- `LOG_BACKUP_COUNT`: Anzahl täglicher Backups (Standard: 10)
- `LOG_MAX_SIZE` ist nicht mehr genutzt — Rotation erfolgt zeitbasiert

### Features
- `USE_SKELETON`: Token-Reduktion ([Rezept 20](20-ast-skeleton.md))
- `TAG_AGGREGATION`: Mehrere Failures → 1 Issue ([Rezept 18](18-tag-aggregation.md))
- `VERSION_COMPARE`: Code-Diff bei Regression ([Rezept 24](24-gitea-version-compare.md))

---

### Best Practice

> [!TIP]
> **.env.template versionieren:**
> ```bash
> # ~/Gitea-Agent/.env.template
> GITEA_URL=https://gitea.example.com
> GITEA_TOKEN=<your_token>
> CLAUDE_API_ENABLED=true
> 
> # .gitignore
> .env
> ```

> [!TIP]
> **Multi-Environment Setup:**
> ```bash
> .env.dev
> .env.staging
> .env.prod
> 
> # Laden:
> python3 agent_start.py --env-file .env.staging
> ```

> [!TIP]
> **Validierung mit --doctor:**
> ```bash
> python3 agent_start.py --project ~/proj --doctor
> # [✓] .env vorhanden
> # [✓] GITEA_TOKEN gültig
> # [✓] CLAUDE_API_ENABLED gesetzt
> # [✗] PROJECT_PATH existiert nicht
> ```

---

### Warnung

> [!WARNING]
> **.env in .gitignore:**
> ```
> ✗ .env committed → Tokens öffentlich
> ✓ .env.template committed → Struktur dokumentiert
> ```

> [!WARNING]
> **AUTO_MERGE=true:**
> ```
> Agent merged PRs ohne Review
> → Breaking Changes in main
> → NUR für Repos ohne Prod-Traffic
> ```

> [!WARNING]
> **LLM_CONTEXT_WINDOW zu klein:**
> ```
> LLM_CONTEXT_WINDOW=2048
> Agent sendet 4096 Tokens
> → API-Error: Context length exceeded
> ```

---

### Nächste Schritte

✅ .env-Felder verstanden  
→ [27 — agent_eval.json-Referenz](27-eval-json-reference.md)  
→ [28 — Labels und Workflow](28-labels-and-workflow.md)  
→ [04 — Health-Check](04-health-check.md)
