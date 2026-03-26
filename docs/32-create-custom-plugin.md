## Custom-Plugin erstellen

Eigene Plugin-Funktionalität hinzufügen.

---

### Voraussetzungen

> [!IMPORTANT]
> - Plugin-Architektur verstanden ([Rezept 31](31-plugin-architecture.md))
> - Python 3.10+ Kenntnisse

---

### Problem

Du willst Funktionalität ergänzen die Agent nicht hat (z.B. Slack-Notifikation bei Failures).

---

### Lösung

```python
# ──────────────────────────────────────────────────────────
# Schritt 1: Plugin-Datei erstellen
# ──────────────────────────────────────────────────────────
# ~/Gitea-Agent/plugins/slack_notifier.py

"""
Slack-Notification-Plugin.

Sendet Slack-Nachrichten bei Test-Failures.
"""

import json
import urllib.request
from typing import Dict, List
from datetime import datetime

class SlackNotifierPlugin:
    """Send Slack notifications for eval failures."""
    
    def __init__(self, project_path: str, webhook_url: str):
        self.project_path = project_path
        self.webhook_url = webhook_url
    
    def notify_failure(self, test_results: List[Dict], issue_url: str) -> Dict:
        """Send Slack notification for test failures.
        
        Args:
            test_results: List of failed tests
            issue_url: Gitea issue URL
        
        Returns:
            {"success": bool, "error": Optional[str]}
        """
        failed_tests = [t for t in test_results if not t["passed"]]
        
        if not failed_tests:
            return {"success": True, "message": "No failures"}
        
        # Build Slack message
        message = {
            "text": f"🚨 Eval Failed — {len(failed_tests)} tests",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 {len(failed_tests)} Test(s) Failed"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Project:*\n{self.project_path}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Failed Tests:*\n" + "\n".join(
                            f"• {t['name']}: {t.get('error', 'Unknown')}"
                            for t in failed_tests
                        )
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Issue"
                            },
                            "url": issue_url
                        }
                    ]
                }
            ]
        }
        
        # Send to Slack
        try:
            data = json.dumps(message).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    return {"success": True}
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
        
        except Exception as e:
            return {"success": False, "error": str(e)}

# ──────────────────────────────────────────────────────────
# Schritt 2: Plugin registrieren
# ──────────────────────────────────────────────────────────
# ~/Gitea-Agent/plugins/__init__.py

from plugins.patch import PatchPlugin
from plugins.changelog import ChangelogPlugin
from plugins.slack_notifier import SlackNotifierPlugin

PLUGINS = {
    "patch": PatchPlugin,
    "changelog": ChangelogPlugin,
    "slack_notifier": SlackNotifierPlugin
}

# ──────────────────────────────────────────────────────────
# Schritt 3: Konfiguration
# ──────────────────────────────────────────────────────────
# ~/mein-projekt/.env

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/XXXX

# ──────────────────────────────────────────────────────────
# Schritt 4: Im Agent nutzen
# ──────────────────────────────────────────────────────────
# agent_start.py (Erweiterung)

from plugins import load_plugin
import os

# Plugin laden
slack = SlackNotifierPlugin(
    project_path=project_path,
    webhook_url=os.getenv("SLACK_WEBHOOK_URL")
)

# Bei Eval-Failure
if eval_failed:
    result = slack.notify_failure(
        test_results=test_results,
        issue_url=f"{gitea_url}/issues/{issue_number}"
    )
    
    if result["success"]:
        print("[✓] Slack notification sent")
    else:
        print(f"[✗] Slack failed: {result['error']}")
```

---

### Erklärung

**Plugin-Template:**

```python
class MyPlugin:
    """Short description."""
    
    def __init__(self, project_path: str, **kwargs):
        """Initialize with project and config."""
        self.project_path = project_path
        # Store kwargs
    
    def main_function(self, input_data):
        """Primary plugin functionality.
        
        Args:
            input_data: Description
        
        Returns:
            {"success": bool, ...}
        """
        try:
            # Do work
            result = self._process(input_data)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _process(self, data):
        """Internal helper method."""
        pass
```

**Integration-Punkte:**

| Hook | Wann aufgerufen | Use-Case |
|------|-----------------|----------|
| `on_eval_start` | Vor Eval-Lauf | Pre-Checks, Setup |
| `on_eval_fail` | Nach Eval-Failure | Notifications, Alerts |
| `on_eval_pass` | Nach Eval-Success | Cleanup, Reports |
| `on_issue_created` | Issue eröffnet | External-Tracking |
| `on_pr_created` | PR erstellt | Code-Review-Trigger |

---

### Best Practice

> [!TIP]
> **Type-Hints:**
> ```python
> from typing import Dict, List, Optional
> 
> def notify(self, data: Dict[str, str]) -> Dict:
>     ...
> ```

> [!TIP]
> **Config-Validation:**
> ```python
> def __init__(self, project_path: str, webhook_url: str):
>     if not webhook_url.startswith("https://"):
>         raise ValueError("webhook_url must be HTTPS")
>     self.webhook_url = webhook_url
> ```

> [!TIP]
> **Unit-Tests:**
> ```python
> # tests/test_slack_notifier.py
> import unittest
> from plugins.slack_notifier import SlackNotifierPlugin
> 
> class TestSlackNotifier(unittest.TestCase):
>     def test_notify_success(self):
>         plugin = SlackNotifierPlugin(".", "https://mock")
>         result = plugin.notify_failure([], "http://issue")
>         self.assertTrue(result["success"])
> ```

---

### Warnung

> [!WARNING]
> **Blocking-Operations:**
> ```python
> def notify(self, data):
>     response = requests.post(url, json=data)  # blockiert
>     # Agent wartet bis Slack antwortet
> ```
> → Threading oder Async nutzen

> [!WARNING]
> **Secrets in Code:**
> ```python
> webhook_url = "https://hooks.slack.com/..."  # ← hardcoded
> ```
> → Aus .env laden

> [!WARNING]
> **Fehlende Error-Handling:**
> ```python
> def notify(self, data):
>     urllib.request.urlopen(url)  # kann crashen
> ```
> → try/except + return {"success": False}

---

### Nächste Schritte

✅ Custom-Plugin erstellt  
→ [33 — Changelog-Automation](33-changelog-automation.md)  
→ [31 — Plugin-Architektur](31-plugin-architecture.md)
