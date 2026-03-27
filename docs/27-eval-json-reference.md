## agent_eval.json-Referenz (Alle Felder)

Vollständige Test-Konfiguration.

---

### Voraussetzungen

> [!IMPORTANT]
> - Basis-Tests verstanden ([Rezept 09](09-first-test.md))

---

### Problem

Du willst alle möglichen Felder in `agent_eval.json` kennen mit Beispielen.

---

### Lösung

```json
{
  "server_url": "http://localhost:8000",
  "chat_endpoint": "/chat",
  "max_response_ms": 5000,
  "baseline_file": "data/baseline.json",
  "score_history_file": "data/score_history.json",
  "close_after_consecutive_passes": 2,
  "tag_aggregation": true,
  "tag_threshold": 3,
  "version_compare": true,
  "server_gitea_repo": "user/server-repo",
  "staleness_check": true,
  "staleness_check_interval": 7200,
  "server_repo_path": "/home/user/server",
  "diff_validation": "warn",
  "oos_whitelist": ["tests/**", "docs/**"],
  "log_analyzer": {
    "enabled": true,
    "module": "plugins.log_analyzer",
    "function": "analyze_logs",
    "log_dir": "/var/log/server"
  },
  "services": [
    {
      "name": "api-worker",
      "cmd": "./scripts/restart_worker.sh",
      "auto_restart": true,
      "wait_seconds": 2
    },
    {
      "name": "main-server",
      "cmd": "./scripts/restart_server.sh",
      "auto_restart": false,
      "on_regression": "issue"
    },
    {
      "name": "cache",
      "cmd": "systemctl restart redis",
      "auto_restart": true
    }
  ],
  "tests": [
    {
      "name": "Health-Check",
      "message": "/health",
      "expected_keywords": ["ok", "status"],
      "weight": 1,
      "tag": "health",
      "max_response_ms": 500,
      "required": true
    },
    {
      "name": "RAG-Context-Persistence",
      "weight": 3,
      "tag": "rag",
      "steps": [
        {
          "message": "Mein Name ist Anna",
          "expect_stored": true
        },
        {
          "message": "Wie heiße ich?",
          "expected_keywords": ["Anna"]
        }
      ]
    },
    {
      "name": "Error-Handling",
      "message": "",
      "expected_keywords": ["error", "empty"],
      "weight": 2,
      "tag": "validation",
      "expect_error": true,
      "error_code": 400
    }
  ]
}
```

---

### Erklärung

**Top-Level-Felder:**

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| `server_url` | string | ✓ | Basis-URL des Servers |
| `chat_endpoint` | string | ✓ | Endpunkt für Chat-Requests (z.B. `/chat`) |
| `max_response_ms` | int | ✗ | Global Timeout (Standard: 5000) |
| `baseline_file` | string | ✗ | Pfad zu baseline.json (relativ) |
| `score_history_file` | string | ✗ | Pfad zu score_history.json |
| `close_after_consecutive_passes` | int | ✗ | Consecutive-Pass-Gate (Standard: 1) |
| `tag_aggregation` | bool | ✗ | Tag-basierte Issue-Aggregation ([Rezept 18](18-tag-aggregation.md)) |
| `tag_threshold` | int | ✗ | Min. Failures für Aggregation (Standard: 3) |
| `version_compare` | bool | ✗ | Code-Diff bei Regression ([Rezept 24](24-gitea-version-compare.md)) |
| `server_gitea_repo` | string | ✗ | Gitea-Repo des Servers (für Version-Compare) |
| `staleness_check` | bool | ✗ | Server-Code-Freshness ([Rezept 19](19-staleness-check.md)) |
| `staleness_check_interval` | int | ✗ | Check-Intervall in Sekunden (Standard: 7200) |
| `server_repo_path` | string | ✗ | Lokaler Pfad zu Server-Repo |
| `diff_validation` | string | ✗ | `strict` / `warn` / `off` ([Rezept 22](22-diff-validation.md)) |
| `oos_whitelist` | array | ✗ | Erlaubte Out-of-Scope Patterns |
| `log_analyzer` | object | ✗ | Log-Analyzer-Config ([Rezept 25](25-log-analyzer.md)) |
| `services` | array | ✗ | Service-Neustart-Matrix (granularer als `restart_script`) |
| `restart_script` | string | ✗ | Legacy: einzelnes Restart-Script (wird durch `services` ersetzt) |

**Services-Felder (in `services`):**

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| `name` | string | ✓ | Dienst-Name (für Logs und Issues) |
| `cmd` | string | ✓ | Shell-Befehl oder Script-Pfad |
| `auto_restart` | bool | ✗ | `true` = automatisch neustarten; `false` = nur Issue, kein Neustart (Standard: true) |
| `wait_seconds` | int | ✗ | Wartezeit nach Neustart in Sekunden (Standard: 0) |
| `on_regression` | string | ✗ | Aktion bei `auto_restart: false` — aktuell nur `"issue"` unterstützt |

**Test-Felder:**

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| `name` | string | ✓ | Test-Name (unique) |
| `message` | string | * | Nachricht an Server (entweder `message` oder `steps`) |
| `steps` | array | * | Mehrstufiger Test ([Rezept 10](10-multi-step-tests.md)) |
| `expected_keywords` | array | ✗ | Keywords in Response (case-insensitive) |
| `expect_stored` | bool | ✗ | Prüft nur: Response nicht leer (für Steps) |
| `weight` | int | ✓ | Gewicht für Score-Berechnung (1-10) |
| `tag` | string | ✗ | Kategorie-Tag für Aggregation |
| `max_response_ms` | int | ✗ | Test-spezifisches Timeout |
| `required` | bool | ✗ | Test muss bestehen (Score = 0 wenn FAIL) |
| `expect_error` | bool | ✗ | Erwartet Fehler-Response |
| `error_code` | int | ✗ | Erwarteter HTTP-Status-Code (bei expect_error) |

**Step-Felder (in `steps`):**

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| `message` | string | ✓ | Nachricht für diesen Step |
| `expected_keywords` | array | ✗ | Keywords in Response |
| `expect_stored` | bool | ✗ | Prüft nur: Response vorhanden |

---

### Best Practice

> [!TIP]
> **Required-Tests für Critical-Paths:**
> ```json
> {
>   "name": "Auth-System",
>   "required": true,
>   "weight": 10,
>   "...": "..."
> }
> ```
> → Wenn Auth failt: Score = 0 (unabhängig von anderen Tests)

> [!TIP]
> **Granulare Timeouts:**
> ```json
> {
>   "max_response_ms": 5000,
>   "tests": [
>     {"name": "Fast", "max_response_ms": 500, "...": "..."},
>     {"name": "Slow", "max_response_ms": 10000, "...": "..."}
>   ]
> }
> ```

> [!TIP]
> **Hierarchische Tags:**
> ```json
> {
>   "tests": [
>     {"tag": "rag:vector", "...": "..."},
>     {"tag": "rag:embedding", "...": "..."},
>     {"tag": "auth:token", "...": "..."},
>     {"tag": "auth:session", "...": "..."}
>   ]
> }
> ```
> → Ermöglicht Sub-Kategorie-Aggregation

> [!TIP]
> **Service-Matrix für gemischte Dienste:**
> ```json
> {
>   "services": [
>     {"name": "worker",      "cmd": "systemctl restart worker",  "auto_restart": true,  "wait_seconds": 3},
>     {"name": "main-server", "cmd": "systemctl restart server",  "auto_restart": false},
>     {"name": "cache",       "cmd": "systemctl restart redis",   "auto_restart": true}
>   ]
> }
> ```
> → Worker und Cache werden automatisch neugestartet
> → `main-server`: Gitea-Issue wird erstellt, kein automatischer Neustart
> → Alle Warnungen landen im Issue (nicht nur im Terminal)

> [!TIP]
> **Legacy restart_script weiterhin nutzbar:**
> ```json
> {"restart_script": "./scripts/restart.sh"}
> ```
> → Wird automatisch als `{"name": "server", "cmd": "...", "auto_restart": true}` behandelt

---

### Warnung

> [!WARNING]
> **Weight-Summe beachten:**
> ```json
> {
>   "tests": [
>     {"weight": 1},
>     {"weight": 2},
>     {"weight": 3}
>   ]
> }
> ```
> → Max-Score = 6 → Baseline entsprechend setzen

> [!WARNING]
> **expect_error ohne error_code:**
> ```json
> {"expect_error": true}  // kein error_code
> ```
> → Jeder HTTP-Fehler (400/404/500) gilt als PASS
> → Besser: `"error_code": 400` spezifizieren

> [!WARNING]
> **message + steps gleichzeitig:**
> ```json
> {
>   "message": "Hallo",
>   "steps": [...]
> }
> ```
> → `steps` überschreibt `message`

> [!WARNING]
> **auto_restart: false ohne Monitoring:**
> ```json
> {"name": "main-server", "auto_restart": false}
> ```
> → Issue wird erstellt aber niemand sieht es wenn kein Gitea-Monitoring aktiv
> → Eval bleibt FAIL bis manueller Neustart + neuer Eval-Lauf

> [!WARNING]
> **services + restart_script gleichzeitig:**
> ```json
> {"restart_script": "...", "services": [...]}
> ```
> → `services` hat Vorrang — `restart_script` wird ignoriert

---

### Nächste Schritte

✅ agent_eval.json vollständig verstanden  
→ [26 — .env-Konfiguration](26-env-configuration.md)  
→ [09 — Ersten Test schreiben](09-first-test.md)  
→ [40 — Best Practices](40-best-practices.md)
