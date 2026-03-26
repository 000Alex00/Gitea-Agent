## API-Functions-Referenz

evaluation.py, gitea_api.py wichtige Funktionen.

---

### Voraussetzungen

> [!IMPORTANT]
> - Python-Kenntnisse
> - Agent-Codebase geklont

---

### Problem

Du willst Agent-Code erweitern oder verstehen welche Funktionen verfügbar sind.

---

### Lösung

**evaluation.py**

```python
from evaluation import run_evaluation, update_baseline

# ──────────────────────────────────────────────────────────
# Eval-Lauf durchführen
# ──────────────────────────────────────────────────────────
result = run_evaluation(
    project_path="/home/user/my-project",
    config_path="config/agent_eval.json"
)

# Returns:
# {
#   "score": 8.0,
#   "baseline": 8.0,
#   "status": "PASS",
#   "tests": [
#     {"name": "Test1", "passed": True, "response_time_ms": 1234},
#     ...
#   ]
# }

# ──────────────────────────────────────────────────────────
# Baseline aktualisieren
# ──────────────────────────────────────────────────────────
update_baseline(
    project_path="/home/user/my-project",
    new_score=8.0
)

# ──────────────────────────────────────────────────────────
# Einzelnen Test ausführen
# ──────────────────────────────────────────────────────────
from evaluation import run_single_test

test_result = run_single_test(
    server_url="http://localhost:8000",
    endpoint="/chat",
    test_config={
        "name": "RAG-Query",
        "message": "Was steht in Kapitel 1?",
        "expected_keywords": ["Kapitel"],
        "weight": 2
    }
)

# Returns:
# {
#   "name": "RAG-Query",
#   "passed": True,
#   "response_time_ms": 2345,
#   "response": "Das Kapitel 1 handelt von...",
#   "error": None
# }
```

**gitea_api.py**

```python
from gitea_api import GiteaAPI

# ──────────────────────────────────────────────────────────
# API-Client initialisieren
# ──────────────────────────────────────────────────────────
api = GiteaAPI(
    base_url="https://gitea.example.com",
    token="abc123...",
    repo="user/project"
)

# ──────────────────────────────────────────────────────────
# Issues
# ──────────────────────────────────────────────────────────
# Alle Issues abrufen
issues = api.get_issues(state="open", labels=["agent:todo"])

# Issue erstellen
issue = api.create_issue(
    title="Test failure: RAG-Query",
    body="Test failed at...",
    labels=["agent:regression"]
)

# Issue-Kommentar posten
api.create_comment(
    issue_number=42,
    body="Plan created:\n- Step 1\n- Step 2"
)

# Label hinzufügen
api.add_label(issue_number=42, label="agent:in-progress")

# Issue schließen
api.close_issue(issue_number=42)

# ──────────────────────────────────────────────────────────
# Pull-Requests
# ──────────────────────────────────────────────────────────
# PR erstellen
pr = api.create_pull_request(
    title="Fix: Handle empty messages",
    head="fix/empty-messages",
    base="main",
    body="Closes #45"
)

# PR-Review-Kommentar
api.create_pr_review(
    pr_number=21,
    body="LGTM",
    event="APPROVE"
)

# PR mergen
api.merge_pull_request(
    pr_number=21,
    merge_method="squash"
)

# ──────────────────────────────────────────────────────────
# Repository
# ──────────────────────────────────────────────────────────
# Branches abrufen
branches = api.get_branches()

# Branch erstellen
api.create_branch(
    branch_name="feature/new-api",
    from_branch="main"
)

# Commit-Info
commit = api.get_commit("abc123def")

# Commits vergleichen (Diff)
diff = api.compare_commits(base="abc123", head="def456")

# ──────────────────────────────────────────────────────────
# Files
# ──────────────────────────────────────────────────────────
# Datei-Content abrufen
content = api.get_file_content(
    file_path="src/api.py",
    ref="main"
)

# Datei erstellen/updaten
api.update_file(
    file_path="README.md",
    content="New content",
    message="docs: Update README",
    branch="main",
    sha=None  # None = create, <sha> = update
)
```

**plugins/llm.py**

```python
from plugins.llm import get_client, LLMResponse

# ──────────────────────────────────────────────────────────
# LLM-Client per Task-Name laden (via routing.json)
# ──────────────────────────────────────────────────────────
client = get_client(task="implementation")

# LLM-Request ausführen
response: LLMResponse = client.complete(
    prompt="Implementiere eine Validierungsfunktion für leere Strings."
)

# LLMResponse Dataclass:
# response.text      — generierter Text
# response.tokens    — genutzte Tokens
# response.model     — genutztes Modell
# response.provider  — genutzter Provider (claude, openai, gemini, local)

# ──────────────────────────────────────────────────────────
# Verfügbare Tasks (aus config/llm/routing.json):
# ──────────────────────────────────────────────────────────
# "issue_analysis"   — schnelles Modell für Plan-Generierung
# "implementation"   — leistungsfähiges Modell für Code-Änderungen
# "review"           — Reviewer-Rolle
# "heal"             — Healer/Fixer-Rolle
# "log_analysis"     — Log-Analyse-Rolle

# Fallback auf "default" wenn Task nicht konfiguriert:
client = get_client(task="custom_task")
# → nutzt routing.json["default"]
```

**agent_self_check.py**

```python
from agent_self_check import validate_setup

# ──────────────────────────────────────────────────────────
# Setup validieren
# ──────────────────────────────────────────────────────────
result = validate_setup(project_path="/home/user/my-project")

# Returns:
# {
#   "valid": True,
#   "checks": [
#     {"name": "Project-Path exists", "passed": True},
#     {"name": ".env present", "passed": True},
#     {"name": "Gitea-Token valid", "passed": True},
#     {"name": "LLM-Server reachable", "passed": True},
#     {"name": "agent_eval.json valid", "passed": True}
#   ]
# }
```

---

### Häufig genutzte Patterns

**Pattern 1: Issue-Workflow**

```python
from gitea_api import GiteaAPI

api = GiteaAPI(base_url, token, repo)

# 1. Issue finden
issues = api.get_issues(state="open", labels=["agent:todo"])

for issue in issues:
    # 2. Label setzen
    api.add_label(issue["number"], "agent:in-progress")
    
    # 3. Branch erstellen
    branch_name = f"agent/{issue['number']}"
    api.create_branch(branch_name, from_branch="main")
    
    # 4. Code ändern (lokal)
    # ... git operations ...
    
    # 5. PR erstellen
    pr = api.create_pull_request(
        title=f"Fix: {issue['title']}",
        head=branch_name,
        base="main",
        body=f"Closes #{issue['number']}"
    )
    
    # 6. Label updaten
    api.remove_label(issue["number"], "agent:in-progress")
    api.add_label(issue["number"], "agent:review")
```

**Pattern 2: Eval + Issue bei Failure**

```python
from evaluation import run_evaluation
from gitea_api import GiteaAPI

result = run_evaluation(project_path)

if result["status"] == "FAIL":
    failed_tests = [t for t in result["tests"] if not t["passed"]]
    
    api = GiteaAPI(...)
    
    for test in failed_tests:
        issue = api.create_issue(
            title=f"[Eval] {test['name']} failed",
            body=f"Error: {test['error']}",
            labels=["agent:regression"]
        )
```

---

### Nächste Schritte

✅ API-Functions kennen  
→ [38 — CLI-Referenz](38-cli-reference.md)  
→ [40 — Best Practices](40-best-practices.md)
