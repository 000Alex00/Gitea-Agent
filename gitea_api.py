#!/usr/bin/env python3
"""
gitea_api.py — Gitea REST API Helper für den Agent-Workflow.

Kapselt alle Gitea-API-Calls. Wird von agent_start.py genutzt.

Konfiguration (via .env im selben Verzeichnis oder Umgebungsvariablen):
    GITEA_URL       = http://your-gitea-host:3000
    GITEA_USER      = your-username
    GITEA_TOKEN     = your-api-token
    GITEA_REPO      = owner/repo-name
    GITEA_BOT_USER  = bot-username        (optional, für Kommentare)
    GITEA_BOT_TOKEN = bot-api-token       (optional)

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

_ENV_FILE = Path(__file__).parent / ".env"


def _load_env() -> dict:
    """
    Liest alle relevanten Variablen aus .env und Umgebungsvariablen.

    Reihenfolge: Umgebungsvariable → .env Datei → Standardwert.

    Returns:
        Dict mit GITEA_URL, GITEA_USER, GITEA_TOKEN, GITEA_REPO,
        GITEA_BOT_USER, GITEA_BOT_TOKEN.
    """
    env = {
        "GITEA_URL":       os.getenv("GITEA_URL", "http://localhost:3000"),
        "GITEA_USER":      os.getenv("GITEA_USER", ""),
        "GITEA_TOKEN":     os.getenv("GITEA_TOKEN", ""),
        "GITEA_REPO":      os.getenv("GITEA_REPO", ""),
        "GITEA_BOT_USER":  os.getenv("GITEA_BOT_USER", ""),
        "GITEA_BOT_TOKEN": os.getenv("GITEA_BOT_TOKEN", ""),
    }
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text().splitlines():
            line = line.strip()
            for key in env:
                if line.startswith(f"{key}="):
                    env[key] = line.split("=", 1)[1].strip()
    return env


def _make_auth(user: str, token: str, prompt_fallback: bool = False) -> str:
    """
    Erstellt Base64-Basic-Auth-Header aus user+token.

    Args:
        user:            Gitea-Username
        token:           API-Token oder Passwort
        prompt_fallback: Bei leerem Token interaktiv nachfragen

    Returns:
        Base64-kodierter Basic-Auth-String.
    """
    if not token and prompt_fallback:
        import getpass
        token = getpass.getpass(f"Gitea Passwort/Token für {user}: ")
    return base64.b64encode(f"{user}:{token}".encode()).decode()


# Einmalig beim Import laden
_ENV      = _load_env()
GITEA_URL = _ENV["GITEA_URL"]
REPO      = _ENV["GITEA_REPO"]

_AUTH     = _make_auth(_ENV["GITEA_USER"], _ENV["GITEA_TOKEN"], prompt_fallback=True)
_BOT_AUTH = (
    _make_auth(_ENV["GITEA_BOT_USER"], _ENV["GITEA_BOT_TOKEN"])
    if _ENV["GITEA_BOT_TOKEN"]
    else _AUTH  # Fallback: gleicher User wenn kein Bot konfiguriert
)


def _request(method: str, path: str, data: dict | None = None, auth: str | None = None) -> dict | list | None:
    """
    Führt einen Gitea-API-Request aus.

    Args:
        method: HTTP-Methode (GET, POST, PATCH, DELETE)
        path:   API-Pfad ohne Basis-URL, z.B. "/repos/owner/repo/issues"
        data:   Optionaler Request-Body als dict (wird zu JSON serialisiert)
        auth:   Auth-Header (Standard: _AUTH / Admin-User)

    Returns:
        Geparste JSON-Antwort (dict oder list), oder None bei DELETE.

    Raises:
        urllib.error.HTTPError: Bei 4xx/5xx-Antworten.
    """
    url     = f"{GITEA_URL}/api/v1{path}"
    payload = json.dumps(data).encode() if data else None
    headers = {
        "Authorization": f"Basic {auth or _AUTH}",
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
        label: Optionaler Label-Filter, z.B. "ready-for-agent"
        state: "open", "closed" oder "all"

    Returns:
        Liste von Issue-dicts.
    """
    params = f"?type=issues&state={state}&limit=50"
    if label:
        params += f"&labels={urllib.parse.quote(label)}"
    issues = _request("GET", f"/repos/{REPO}/issues{params}")
    if label:
        issues = [i for i in issues if any(l["name"] == label for l in i.get("labels", []))]
    return issues


def update_issue(number: int, *, state: str | None = None, body: str | None = None) -> dict:
    """
    Aktualisiert Status oder Body eines Issues.

    Args:
        number: Issue-Nummer
        state:  "open" oder "closed"
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
    return _request("GET", f"/repos/{REPO}/issues/{number}/comments")


def post_comment(number: int, body: str) -> dict:
    """
    Schreibt einen Kommentar als Bot-User (oder Admin-Fallback).

    Args:
        number: Issue-Nummer
        body:   Kommentar-Text (Markdown unterstützt)

    Returns:
        Erstellter Kommentar als dict.
    """
    return _request("POST", f"/repos/{REPO}/issues/{number}/comments", {"body": body}, auth=_BOT_AUTH)


def check_approval(number: int) -> bool:
    """
    Prüft ob ein Issue-Kommentar eine Freigabe enthält.

    Sucht nach "ok", "yes", "ja", "approved", "freigabe" (case-insensitive)
    in Kommentaren die NACH dem letzten Agent-Kommentar erstellt wurden.

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
        dict: name → id Mapping, z.B. {"bug": 1, "enhancement": 3}
    """
    labels = _request("GET", f"/repos/{REPO}/labels")
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
        print(f"[Warnung] Label '{label_name}' existiert nicht in Gitea.")
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
        base:   Ziel-Branch, Standard: "main"

    Returns:
        Erstellter PR als dict mit key: html_url
    """
    return _request("POST", f"/repos/{REPO}/pulls", {
        "title": title,
        "body":  body,
        "head":  branch,
        "base":  base,
    })
