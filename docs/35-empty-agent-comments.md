## Empty-Agent-Comments debuggen

Bot postet leere Kommentare in Issues.

---

### Voraussetzungen

> [!IMPORTANT]
> - Agent läuft, erstellt Issues
> - Kommentare sind leer

---

### Problem

Agent erstellt Issue-Kommentare, aber Body ist leer. Warum?

---

### Lösung

```bash
# ══════════════════════════════════════════════════════════
# Problem 1: Token-Scopes unzureichend
# ══════════════════════════════════════════════════════════
# Issue-Kommentar leer:
# → Agent erstellt Comment, aber ohne Inhalt

# Debugging:
curl -H "Authorization: token $GITEA_TOKEN" \
  https://gitea.example.com/api/v1/user/tokens

# Response:
# {"scopes": ["read:issue"]}  ← nur read!

# Lösung:
# Gitea → Settings → Applications
# Token erstellen mit Scopes:
# ✓ read:issue
# ✓ write:issue
# ✓ write:repository

nano ~/mein-projekt/.env
# GITEA_TOKEN=<neuer_token_mit_allen_scopes>

# ══════════════════════════════════════════════════════════
# Problem 2: LLM-Response leer
# ══════════════════════════════════════════════════════════
# Agent plant Fix, aber Plan-Text ist leer

# Debugging:
python3 agent_start.py \
  --project ~/mein-projekt \
  --issue 42 \
  --debug

# Logs:
# [LLM] Request: "Create plan for Issue #42..."
# [LLM] Response: ""  ← leer!
# [LLM] Tokens used: 0

# Ursache: LLM-Server antwortet mit leerem Body

curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Response:
# {"error": "Model not loaded"}

# Lösung:
sudo systemctl restart llm-server
# oder Model neu laden

# ══════════════════════════════════════════════════════════
# Problem 3: Markdown-Encoding-Fehler
# ══════════════════════════════════════════════════════════
# Agent generiert Text, aber Gitea zeigt leer

# Debugging:
python3 agent_start.py --project ~/proj --issue 42 --debug

# Logs:
# [Agent] Plan created (348 bytes)
# [Gitea] POST /issues/42/comments → 201 Created
# [Gitea] Response: {"id": 123, "body": ""}  ← leer trotz 201!

# Ursache: Encoding-Problem (UTF-8 vs Latin-1)

# Test:
python3 -c "
import requests
response = requests.post(
    'https://gitea.example.com/api/v1/repos/user/repo/issues/42/comments',
    headers={'Authorization': 'token XXX'},
    json={'body': 'Test with Ümläüt'}
)
print(response.json())
"

# → body kommt leer an bei Umlauten

# Lösung:
# gitea_api.py anpassen:
headers = {
    "Authorization": f"token {token}",
    "Content-Type": "application/json; charset=utf-8"
}

# ══════════════════════════════════════════════════════════
# Problem 4: Rate-Limit exceeded
# ══════════════════════════════════════════════════════════
# Erste Kommentare OK, dann plötzlich leer

# Debugging:
curl -I -H "Authorization: token $GITEA_TOKEN" \
  https://gitea.example.com/api/v1/user

# Response-Headers:
# X-RateLimit-Remaining: 0
# X-RateLimit-Reset: 1610000000

# Lösung:
# Warten bis Reset-Timestamp
# Oder: Admin erhöht Limit in Gitea-Config

# ══════════════════════════════════════════════════════════
# Problem 5: Comment-Body zu lang
# ══════════════════════════════════════════════════════════
# Agent generiert 50KB-Plan, Gitea kürzt auf 0

# Debugging:
python3 agent_start.py --issue 42 --debug

# Logs:
# [Agent] Plan: 52.384 Zeichen
# [Gitea] POST /comments → 413 Payload Too Large

# Lösung A: Plan kürzen (LLM-Prompt anpassen)
# Lösung B: Split in mehrere Comments
def post_long_comment(issue, text, max_len=10000):
    chunks = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    for i, chunk in enumerate(chunks):
        gitea.create_comment(issue, f"**Part {i+1}/{len(chunks)}**\n{chunk}")
```

---

### Erklärung

**Gitea-Token-Scopes:**

| Scope | Erforderlich für |
|-------|------------------|
| `read:issue` | Issues lesen |
| `write:issue` | Issues/Comments erstellen |
| `write:repository` | PRs erstellen, Branches pushen |
| `read:user` | User-Info (optional) |

**Comment-API:**

```python
# Korrekt:
response = requests.post(
    f"{gitea_url}/api/v1/repos/{owner}/{repo}/issues/{issue_id}/comments",
    headers={"Authorization": f"token {token}"},
    json={"body": "My comment"}
)

# Falsch:
json={"text": "..."}   # ← Feld heißt "body", nicht "text"
json={"comment": "..."} # ← auch falsch
```

**Rate-Limits:**

```
Gitea Default: 100 req/hour
GitHub: 5000 req/hour (authenticated)

Bei Watch-Modus mit eval_interval=300:
- 1 Eval/5min = 12 Eval/Stunde
- Pro Eval: 5-10 API-Calls
- Total: 60-120 req/Stunde → über Limit!
```

---

### Best Practice

> [!TIP]
> **Token-Validation on Startup:**
> ```python
> def validate_token(gitea_url, token):
>     response = requests.get(
>         f"{gitea_url}/api/v1/user",
>         headers={"Authorization": f"token {token}"}
>     )
>     
>     if response.status_code != 200:
>         raise ValueError("Invalid token")
>     
>     scopes = response.headers.get("X-OAuth-Scopes", "")
>     required = ["write:issue", "write:repository"]
>     
>     for scope in required:
>         if scope not in scopes:
>             raise ValueError(f"Missing scope: {scope}")
> ```

> [!TIP]
> **Comment-Preview:**
> ```python
> if len(comment_body) > 10000:
>     print(f"[!] Warning: Comment sehr lang ({len(comment_body)} chars)")
>     print(f"[!] Preview: {comment_body[:200]}...")
> ```

> [!TIP]
> **Rate-Limit-Monitoring:**
> ```python
> response = requests.get(...)
> remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
> 
> if remaining < 10:
>     print(f"[!] Rate-Limit fast erreicht: {remaining} remaining")
> ```

---

### Warnung

> [!WARNING]
> **Token-Rotation während Laufzeit:**
> ```
> Agent startet mit Token A
> User regeneriert Token → Token A invalid
> → Alle API-Calls failen plötzlich
> ```
> → Token in .env nicht ändern während Agent läuft

> [!WARNING]
> **Gitea-Version-Unterschiede:**
> ```
> Gitea 1.18: write:issue reicht
> Gitea 1.19: write:issue + write:repository erforderlich
> ```
> → Alle Scopes geben (defensiv)

> [!WARNING]
> **HTML in Comments:**
> ```python
> comment = "<script>alert('XSS')</script>"
> → Gitea escaped HTML, aber besser vermeiden
> ```
> → Nur Markdown nutzen

---

### Nächste Schritte

✅ Empty-Comments debugged  
→ [34 — Eval-Failure debuggen](34-debug-eval-fail.md)  
→ [36 — Watch-Modus Crashes](36-watch-mode-crashes.md)
