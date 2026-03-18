#!/usr/bin/env python3
"""
gitea_api.py — Gitea REST API Helper für den Agent-Workflow.

Kapselt alle Gitea-API-Calls. Wird von agent_start.py genutzt.

Konfiguration (via .env im selben Verzeichnis oder Umgebungsvariablen):
    GITEA_URL   = http://your-gitea-host:3000
    GITEA_USER  = your-username
    GITEA_TOKEN = your-api-token
    GITEA_REPO  = owner/repo-name

Auth:
    Liest GITEA_TOKEN aus .env oder Umgebungsvariablen.
    Fallback: interaktiver Passwort-Prompt.

Verwendete Endpunkte:
    GET    /repos/{repo}/issues                   → Issues lesen
    GET    /repos/{repo}/issues/{nr}              → Einzelnes Issue
    GET    /repos/{repo}/issues/{nr}/comments     → Kommentare lesen
    POST   /repos/{repo}/issues/{nr}/comments     → Kommentar schreiben
    POST   /repos/{repo}/issues/{nr}/labels       → Label hinzufügen
    DELETE /repos/{repo}/issues/{nr}/labels/{id}  → Label entfernen
    PATCH  /repos/{repo}/issues/{nr}              → Issue updaten
    POST   /repos/{repo}/pulls                    → PR erstellen
    GET    /repos/{repo}/labels                   → Alle Labels abrufen
"""

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Konfiguration — aus .env laden
# ---------------------------------------------------------------------------

def _find_env_file() -> Path | None:
    """
    Sucht .env-Datei: zuerst im gleichen Verzeichnis wie dieses Script,
    dann im aktuellen Arbeitsverzeichnis.

    Returns:
        Path zur .env-Datei oder None wenn nicht gefunden.
    """
    candidates = [
        Path(__file__).parent / ".env",
        Path.cwd() / ".env",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _load_config() -> dict:
    """
    Lädt Konfiguration aus .env-Datei und Umgebungsvariablen.

    Priorität: Umgebungsvariablen > .env-Datei > Defaults/Prompt.

    Returns:
        dict mit keys: url, user, token, repo
    """
    cfg = {
        "url":  os.getenv("GITEA_URL", ""),
        "user": os.getenv("GITEA_USER", ""),
        "token": os.getenv("GITEA_TOKEN", ""),
        "repo": os.getenv("GITEA_REPO", ""),
    }

    env_file = _find_env_file()
    if env_file:
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            if key == "GITEA_URL"   and not cfg["url"]:   cfg["url"]   = val
            if key == "GITEA_USER"  and not cfg["user"]:  cfg["user"]  = val
            if key == "GITEA_TOKEN" and not cfg["token"]: cfg["token"] = val
            if key == "GITEA_REPO"  and not cfg["repo"]:  cfg["repo"]  = val

    if not cfg["url"]:
        cfg["url"] = input("Gitea URL (z.B. http://192.168.1.x:3001): ").strip()
    if not cfg["repo"]:
        cfg["repo"] = input("Repository (owner/name): ").strip()
    if not cfg["token"]:
        import getpass
        cfg["token"] = getpass.getpass(f"Gitea Token/Passwort für {cfg['user']}: ")

    return cfg


_CFG  = _load_config()
GITEA_URL = _CFG["url"].rstrip("/")
REPO      = _CFG["repo"]
_AUTH     = base64.b64encode(f"{_CFG['user']}:{_CFG['token']}".encode()).decode()


# ---------------------------------------------------------------------------
# Interner HTTP-Client
# ---------------------------------------------------------------------------

def _request(method: str, path: str, data: dict | None = None) -> dict | list | None:
    """
    Führt einen Gitea-API-Request aus.

    Aufgerufen von:
        Alle öffentlichen Funktionen dieses Moduls.

    Args:
        method: HTTP-Methode (GET, POST, PATCH, DELETE)
        path:   API-Pfad ohne Basis-URL, z.B. \"/repos/owner/repo/issues\"
        data:   Optionaler Request-Body als dict (wird zu JSON serialisiert)

    Returns:
        Geparste JSON-Antwort (dict oder list), oder None bei DELETE.

    Raises:
        urllib.error.HTTPError: Bei 4xx/5xx-Antworten.
    """
    url     = f"{GITEA_URL}/api/v1{path}"
    payload = json.dumps(data).encode() if data else None
    headers = {
        "Authorization": f"Basic {_AUTH}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        print(f"[Gitea API Fehler] {method} {path} → {e.code}: {e.read().decode()}")
        raise


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

def get_issue(number: int) -> dict:
    """
    Liest ein einzelnes Issue.

    Args:
        number: Issue-Nummer

    Returns:
        Issue-dict mit keys: number, title, body, labels, state
    """
    return _request("GET", f"/repos/{REPO}/issues/{number}")


def get_issues(label: str | None = None, state: str = "open") -> list:
    """
    Liest Issues, optional gefiltert nach Label.

    Args:
        label: Optionaler Label-Filter, z.B. \"ready-for-agent\"
        state: \"open\", \"closed\" oder \"all\"

    Returns:
        Liste von Issue-dicts.
    """
    params = f"?type=issues&state={state}&limit=50"
    if label:
        params += f"&labels={urllib.parse.quote(label)}"
    issues = _request("GET", f"/repos/{REPO}/issues{params}")
    if label:
        issues = [i for i in issues if any(l["name"] == label for l in i.get("labels", []))]
    return issues or []


def update_issue(number: int, *, state: str | None = None, body: str | None = None) -> dict:
    """
    Aktualisiert Status oder Body eines Issues.

    Args:
        number: Issue-Nummer
        state:  \"open\" oder \"closed\"
        body:   Neuer Issue-Body

    Returns:
        Aktualisiertes Issue-dict.
    """
    data = {}
    if state: data["state"] = state
    if body:  data["body"]  = body
    return _request("PATCH", f"/repos/{REPO}/issues/{number}", data)


# ---------------------------------------------------------------------------
# Kommentare
# ---------------------------------------------------------------------------

def get_comments(number: int) -> list:
    """
    Liest alle Kommentare eines Issues.

    Args:
        number: Issue-Nummer

    Returns:
        Liste von Kommentar-dicts mit keys: id, body, user.login, created_at
    """
    return _request("GET", f"/repos/{REPO}/issues/{number}/comments") or []


def post_comment(number: int, body: str) -> dict:
    """
    Schreibt einen Kommentar auf ein Issue.

    Args:
        number: Issue-Nummer
        body:   Kommentar-Text (Markdown unterstützt)

    Returns:
        Erstellter Kommentar als dict.
    """
    return _request("POST", f"/repos/{REPO}/issues/{number}/comments", {"body": body})


def check_approval(number: int) -> bool:
    """
    Prüft ob ein Issue-Kommentar eine Freigabe enthält.

    Sucht nach Freigabe-Keywords in Kommentaren die NACH dem letzten
    Agent-Kommentar (erkennbar an \"OK zum Implementieren?\") erstellt wurden.

    Args:
        number: Issue-Nummer

    Returns:
        True wenn Freigabe-Kommentar gefunden.
    """
    APPROVAL_KEYWORDS = {"ok", "yes", "ja", "approved", "freigabe", "👍", "✅"}
    comments = get_comments(number)

    last_agent_idx = -1
    for i, c in enumerate(comments):
        if "OK zum Implementieren?" in c.get("body", ""):
            last_agent_idx = i

    review_comments = comments[last_agent_idx + 1:] if last_agent_idx >= 0 else comments
    for c in review_comments:
        body_lower = c.get("body", "").lower().strip()
        if any(kw in body_lower for kw in APPROVAL_KEYWORDS):
            return True
    return False


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

def get_all_labels() -> dict:
    """
    Liest alle verfügbaren Labels des Repos.

    Returns:
        dict: name → id Mapping, z.B. {\"bug\": 1, \"enhancement\": 3}
    """
    labels = _request("GET", f"/repos/{REPO}/labels") or []
    return {l["name"]: l["id"] for l in labels}


def add_label(number: int, label_name: str) -> None:
    """
    Fügt einem Issue ein Label hinzu.

    Args:
        number:     Issue-Nummer
        label_name: Label-Name, muss im Repo existieren
    """
    labels = get_all_labels()
    if label_name not in labels:
        print(f"[Warnung] Label '{label_name}' existiert nicht.")
        return
    _request("POST", f"/repos/{REPO}/issues/{number}/labels", {"labels": [labels[label_name]]})


def remove_label(number: int, label_name: str) -> None:
    """
    Entfernt ein Label von einem Issue.

    Args:
        number:     Issue-Nummer
        label_name: Label-Name
    """
    labels = get_all_labels()
    if label_name not in labels:
        return
    _request("DELETE", f"/repos/{REPO}/issues/{number}/labels/{labels[label_name]}")


def swap_label(number: int, remove: str, add: str) -> None:
    """
    Tauscht ein Label gegen ein anderes (atomarer Status-Wechsel).

    Args:
        number: Issue-Nummer
        remove: Label das entfernt wird
        add:    Label das gesetzt wird
    """
    remove_label(number, remove)
    add_label(number, add)


# ---------------------------------------------------------------------------
# Pull Requests
# ---------------------------------------------------------------------------

def create_pr(branch: str, title: str, body: str, base: str = "main") -> dict:
    """
    Erstellt einen Pull Request.

    Args:
        branch: Feature-Branch (head)
        title:  PR-Titel
        body:   PR-Beschreibung (Markdown)
        base:   Ziel-Branch, Standard: \"main\"

    Returns:
        Erstellter PR als dict mit key: html_url
    """
    return _request("POST", f"/repos/{REPO}/pulls", {
        "title": title,
        "body":  body,
        "head":  branch,
        "base":  base,
    })
