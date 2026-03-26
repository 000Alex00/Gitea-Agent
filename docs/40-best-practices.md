## Best Practices

Issue-Quality, Test-Design, Sicherheit.

---

### Voraussetzungen

> [!IMPORTANT]
> - Basis-Workflows verstanden

---

### Problem

Agent läuft, aber Ergebnisse suboptimal. Was sind Best-Practices?

---

### Lösung

## Issue-Quality

**✓ Gute Issues:**

```markdown
## Issue #42: Fix empty message handling

**Problem:**
API crashes when sending empty message to `/chat` endpoint.

**Affected Files:**
- `src/api.py` (Line 145, function `process_message`)

**Expected Behavior:**
Return `{"error": "Message cannot be empty"}` with HTTP 400

**Steps to Reproduce:**
1. POST to `/chat` with `{"message": ""}`
2. Observe crash

**Error Message:**
```
IndexError: list index out of range
```

**Risk-Level:** low (edge-case, no data-loss)
```

**✗ Schlechte Issues:**

```markdown
## Issue: Fix API

The API is broken. Please fix.
```

→ Agent hat keine Informationen: Welche API? Welcher Fehler? Wo?

---

## Test-Design

**✓ Gute Tests:**

```json
{
  "name": "RAG-Context-Retrieval",
  "weight": 3,
  "tag": "rag",
  "max_response_ms": 3000,
  "steps": [
    {
      "message": "Store: Python ist eine Programmiersprache",
      "expect_stored": true
    },
    {
      "message": "Was ist Python?",
      "expected_keywords": ["Programmiersprache"]
    }
  ]
}
```

→ Spezifisch, messbar, reproduzierbar

**✗ Schlechte Tests:**

```json
{
  "name": "Test",
  "message": "Hallo",
  "expected_keywords": ["irgendwas"]
}
```

→ Vage, kein klares Ziel

---

## Sicherheit

**✓ Token-Management:**

```bash
# .env (nicht committen!)
GITEA_TOKEN=xyz123

# .gitignore
.env
.env.*
```

**✗ Tokens in Code:**

```python
token = "abc123"  # ← im Git-Repo
```

---

**✓ Auto-Merge mit Vorsicht:**

```json
{
  "auto_merge": {
    "enabled": true,
    "only_if_labels": ["agent:low-risk"],
    "never_if_labels": ["breaking-change"]
  }
}
```

**✗ Blind Auto-Merge:**

```bash
--auto-merge  # ← alles wird gemerged
```

---

**✓ Issue-Body-Sanierung:**

```python
def sanitize_issue_body(body):
    # Remove tokens
    body = re.sub(r'token[=:]?\s*[a-f0-9]{40}', '[REDACTED]', body)
    # Remove passwords
    body = re.sub(r'password[=:]?\s*\S+', '[REDACTED]', body)
    return body
```

---

## Performance

**✓ AST-Skeleton nutzen:**

```bash
python3 agent_start.py --project ~/proj --build-skeleton
# Token-Reduktion: 95%
```

**✗ Full-Context bei jedem Request:**

```
Agent sendet 100.000 Zeilen Code an LLM
→ Token-Limit exceeded
```

---

**✓ Excludes konfigurieren:**

```json
{
  "exclude_dirs": ["venv", "node_modules", ".git"]
}
```

**✗ Alle Dateien laden:**

```
Agent lädt .git/ (5 GB)
→ Out-of-Memory
```

---

## Reliability

**✓ Consecutive-Pass-Gate:**

```json
{
  "close_after_consecutive_passes": 3
}
```

→ Issue erst nach 3 stabilen Runs schließen

**✗ Sofort schließen:**

```json
{
  "close_after_consecutive_passes": 1
}
```

→ Flaky-Tests öffnen/schließen Issues ständig

---

**✓ Health-Checks vor Eval:**

```python
if not check_server_health():
    log.warning("Server down, skipping eval")
    return
```

**✗ Blind Eval-Run:**

```
Server offline → Alle Tests failen → 50 Issues erstellt
```

---

## Monitoring

**✓ Dashboard + Alerts:**

```bash
python3 agent_start.py --dashboard-enabled

# Slack-Webhook bei Failures
```

**✗ Keine Überwachung:**

```
Agent crashed vor 3 Tagen → niemand weiß es
```

---

## Dokumentation

**✓ README mit Setup-Guide:**

```markdown
# Agent-Setup

1. Installation: [docs/01-installation.md](...)
2. Setup: [docs/02-first-setup.md](...)
3. Erster Issue: [docs/03-first-issue.md](...)
```

**✗ Keine Doku:**

```
# README.md
This is a project.
```

→ Neue Team-Mitglieder wissen nicht wie Agent funktioniert

---

## Checkliste

```
✓ Issues haben klare Descriptions + Affected-Files
✓ Tests haben expected_keywords + weights
✓ .env nicht committed
✓ Auto-Merge nur für low-risk
✓ AST-Skeleton generiert
✓ Excludes konfiguriert (venv, node_modules)
✓ Consecutive-Pass-Gate = 2-3
✓ Health-Checks vor Eval
✓ Dashboard + Monitoring
✓ README mit Links zu Cookbook
```

---

### Nächste Schritte

✅ Best-Practices kennen  
→ [41 — Security-Guide](41-security-guide.md)  
→ [README](README.md) — Zurück zur Übersicht
