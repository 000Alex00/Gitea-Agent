"""
plugins/setup_wizard.py — Interaktiver Setup-Wizard (--setup).

Ausgelagert aus agent_start.py zur Reduktion der Dateigröße.
Aufruf: python3 agent_start.py --setup
"""
from __future__ import annotations

import json
from pathlib import Path

import settings

def cmd_setup(_post_doctor=None, _post_dashboard=None) -> None:
    """--setup: Interaktiver Einrichtungs-Wizard für neue Projekte (Issue #77)."""
    import base64
    import datetime

    _STATE_FILE = Path(__file__).parent / ".setup_state.json"
    _LOG_DIR    = Path(__file__).parent / "data"
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    _ts         = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    _LOG_FILE   = _LOG_DIR / f"setup_{_ts}.log"
    _SECRET_KEYS = {"token", "password", "secret", "key", "pass"}

    def _mask(val: str) -> str:
        if len(val) <= 8:
            return "***"
        return val[:4] + "***" + val[-2:]

    def _log(step: str, status: str, detail: str = "") -> None:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{status}] {step}"
        if detail:
            line += f" — {detail}"
        with _LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _load_state() -> dict:
        if _STATE_FILE.exists():
            try:
                return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_state(state: dict) -> None:
        _STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    def _ask(prompt: str, default: str = "") -> str:
        disp = f" [{default}]" if default else ""
        val = input(f"  {prompt}{disp}: ").strip()
        return val or default

    def _sanitize_repo(val: str) -> str:
        return val.strip().strip("`'\"").strip()

    def _retry(msg: str) -> bool:
        return input(f"  {msg} Erneut versuchen? [J/n]: ").strip().lower() in ("", "j", "y")

    _log("SETUP START", "INFO", f"Log: {_LOG_FILE}")

    def _api_get_raw(url, user, token, path):
        import urllib.request, urllib.error
        req = urllib.request.Request(
            f"{url.rstrip('/')}/api/v1{path}",
            headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())

    def _api_post_raw(url, user, token, path, data: dict):
        import urllib.request
        payload = json.dumps(data).encode()
        req = urllib.request.Request(
            f"{url.rstrip('/')}/api/v1{path}",
            data=payload,
            headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())

    W = 66  # Box-Breite gesamt

    _H = '═'
    _TL = '╔'; _TR = '╗'; _BL = '╚'; _BR = '╝'
    _V  = '║'; _ML = '╠'; _MR = '╣'

    def _box(title: str, lines: list) -> None:
        inner = W - 4
        hr = _H * (W - 2)
        print(f"\n{_TL}{hr}{_TR}")
        print(f"{_V}  {title:<{inner}}{_V}")
        print(f"{_ML}{hr}{_MR}")
        for line in lines:
            print(f"{_V}  {line:<{inner}}{_V}")
        print(f"{_BL}{hr}{_BR}\n")

    def _step_done(n: int, title: str, detail: str = "") -> None:
        inner = W - 4
        hr    = _H * (W - 2)
        label = f"Schritt {n}/9 — {title}"
        info  = f"✅ (Resume: {detail})" if detail else "✅ (aus Resume)"
        print(f"\n{_TL}{hr}{_TR}")
        print(f"{_V}  {label:<{inner}}{_V}")
        print(f"{_V}  {info:<{inner}}{_V}")
        print(f"{_BL}{hr}{_BR}\n")

    try:
        # Begrüßung
        hr = _H * (W - 2)
        print(f"\n{_TL}{hr}{_TR}")
        print(f"{_V}{'  gitea-agent Setup-Wizard — 9 Schritte':^{W - 2}}{_V}")
        print(f"{_BL}{hr}{_BR}\n")
        print("  Dieser Wizard richtet den Agenten f\u00fcr dein Projekt ein.")
        print("  Jeder Schritt erkl\u00e4rt zuerst was ben\u00f6tigt wird,")
        print("  danach werden die Eingaben abgefragt.\n")
        print("  Du kannst den Wizard jederzeit mit Strg+C abbrechen.")
        print("  Beim n\u00e4chsten Start wird dort weitergemacht.\n")

        # \u2500\u2500 Resume pr\u00fcfen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        state = _load_state()
        if state:
            completed = [k for k in ("gitea_url", "gitea_repo", "project_root") if k in state]
            print(f"  \u26a1 Vorheriger Fortschritt gefunden: {', '.join(completed)}")
            if input("  Dort weitermachen? [J/n]: ").strip().lower() in ("", "j", "y"):
                _log("RESUME", "INFO", f"Fortgesetzt ab: {', '.join(completed)}")
                print()
            else:
                _log("RESUME", "INFO", "Abgelehnt \u2014 Neustart von Schritt 1")
                state = {}
                _STATE_FILE.unlink(missing_ok=True)
                print()

        # \u2500\u2500 Schritt 1: Gitea-Verbindung \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        if "gitea_url" not in state:
            _box("Schritt 1/9 \u2014 Gitea-Verbindung", [
                "In diesem Schritt verbinden wir den Agenten mit Gitea.",
                "Du ben\u00f6tigst:",
                "",
                "  [1] Gitea URL \u2014 Adresse deiner Gitea-Installation",
                "      Beispiel: http://192.168.1.60:3001",
                "      Nur Root-URL eingeben, KEIN /user oder /repo am Ende!",
                "",
                "  [2] Gitea Benutzername \u2014 dein Login-Name in Gitea",
                "",
                "  [3] API-Token \u2014 einmalig in Gitea erstellen:",
                "      Gitea \u2192 Einstellungen \u2192 Anwendungen \u2192 Token generieren",
                "      Empfohlener Name: gitea-agent",
                "      Rechte: issue R+W  \u00b7  repository R+W  \u00b7  user R",
                "      Token kopieren \u2014 danach NICHT mehr sichtbar!",
                "",
                "  [4] Bot-User (optional) \u2014 separater Gitea-Account",
                "      Vorteil: Kommentare/PRs erscheinen unter Bot-Name",
                "      Anlegen: Admin-Panel \u2192 Benutzer \u2192 Neuen User",
                "      Repo \u2192 Einstellungen \u2192 Collaborators \u2192 Write",
                "      \u2192 Leer lassen wenn du keinen Bot-Account hast",
            ])
            gitea_url = gitea_user = gitea_token = ""
            while True:
                print("  Bitte gib folgendes ein:\n")
                gitea_url   = _ask("[1] Gitea URL (z.B. http://192.168.1.x:3001)", gitea_url)
                gitea_user  = _ask("[2] Gitea Benutzername", gitea_user)
                gitea_token = _ask("[3] Gitea API-Token", gitea_token)
                try:
                    _api_get_raw(gitea_url, gitea_user, gitea_token, "/user")
                    print("  \u2705 Verbindung erfolgreich\n")
                    _log("Schritt 1 Verbindung", "OK", f"URL={gitea_url} User={gitea_user}")
                    break
                except Exception as exc:
                    print(f"  \u274c Verbindungsfehler: {exc}")
                    _log("Schritt 1 Verbindung", "FEHLER", str(exc))
                    if not _retry(""):
                        print("  \u26a0\ufe0f  Fortfahren trotz Fehler\n")
                        break
            bot_user  = _ask("[4] Bot-User (leer = kein Bot)", "")
            bot_token = _ask("    Bot-Token", "") if bot_user else ""
            _log("Schritt 1 Bot", "INFO", f"Bot-User={bot_user or '(keiner)'}")
            state.update(gitea_url=gitea_url, gitea_user=gitea_user, gitea_token=gitea_token,
                         bot_user=bot_user, bot_token=bot_token)
            _save_state(state)
        else:
            gitea_url   = state["gitea_url"]
            gitea_user  = state["gitea_user"]
            gitea_token = state["gitea_token"]
            bot_user    = state["bot_user"]
            bot_token   = state["bot_token"]
            _log("Schritt 1", "RESUME", f"URL={gitea_url} User={gitea_user}")
            _step_done(1, "Gitea-Verbindung", f"{gitea_url}  \u00b7  {gitea_user}")

        # \u2500\u2500 Schritt 2: Repository \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        if "gitea_repo" not in state:
            _box("Schritt 2/9 \u2014 Repository", [
                "Hier legst du fest, welches Gitea-Repository der Agent",
                "\u00fcberwachen und bearbeiten soll.",
                "",
                "  Format:  besitzer/reponame  (nur der Pfad, keine URL!)",
                "  Beispiel: mein-user/mein-projekt",
                "",
                "  Das Repository muss bereits in Gitea existieren.",
                "  Falls ein Bot-User konfiguriert wurde: er muss als",
                "  Collaborator im Repository eingetragen sein.",
            ])
            try:
                repos_data = _api_get_raw(gitea_url, gitea_user, gitea_token,
                                          "/repos/search?limit=50&sort=updated")
                repos = [r["full_name"] for r in repos_data.get("data", [])]
                if repos:
                    print("  Deine verf\u00fcgbaren Repositories:\n")
                    for r in repos[:15]:
                        print(f"    \u2022 {r}")
                    print()
            except Exception:
                pass
            while True:
                raw = _ask("  Repository (besitzer/name)")
                gitea_repo = _sanitize_repo(raw)
                if gitea_repo != raw:
                    print(f"  \u2139\ufe0f  Eingabe bereinigt: '{gitea_repo}'")
                    _log("Schritt 2 Sanitize", "INFO", f"'{raw}' \u2192 '{gitea_repo}'")
                try:
                    _api_get_raw(gitea_url, gitea_user, gitea_token, f"/repos/{gitea_repo}")
                    print("  \u2705 Repository gefunden\n")
                    _log("Schritt 2 Repository", "OK", gitea_repo)
                    break
                except Exception as exc:
                    print(f"  \u274c Repo nicht gefunden: {exc}")
                    _log("Schritt 2 Repository", "FEHLER", f"Eingabe='{gitea_repo}' {exc}")
                    if not _retry(""):
                        print("  \u26a0\ufe0f  Fortfahren trotz Fehler\n")
                        break
            state["gitea_repo"] = gitea_repo
            _save_state(state)
        else:
            gitea_repo = state["gitea_repo"]
            _log("Schritt 2", "RESUME", gitea_repo)
            _step_done(2, "Repository", gitea_repo)

        # \u2500\u2500 Schritt 3: Projektverzeichnis \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        if "project_root" not in state:
            _box("Schritt 3/9 \u2014 Projektverzeichnis", [
                "Der Agent ben\u00f6tigt den lokalen Pfad zu deinem Projekt.",
                "Dort wird er Code lesen, \u00c4nderungen schreiben und",
                "Konfigurationsdateien anlegen.",
                "",
                "  Gib den vollst\u00e4ndigen Pfad zum Projektordner an.",
                "  Beispiel: /home/ki02/jetson-llm-chat",
                "",
                "  Das Verzeichnis muss existieren und idealerweise",
                "  ein git-Repository sein (enth\u00e4lt einen .git Ordner).",
            ])
            while True:
                project_root = _ask("  Lokaler Pfad zum Projekt")
                if Path(project_root).is_dir():
                    if (Path(project_root) / ".git").exists():
                        print("  \u2705 git-Repo gefunden\n")
                        _log("Schritt 3 Verzeichnis", "OK", project_root)
                    else:
                        print("  \u26a0\ufe0f  Kein .git Ordner gefunden.")
                        _log("Schritt 3 Verzeichnis", "WARNUNG", f"Kein .git in {project_root}")
                        if input("  Trotzdem verwenden? [J/n]: ").strip().lower() in ("", "j", "y"):
                            print()
                        else:
                            continue
                    break
                else:
                    print(f"  \u274c Verzeichnis nicht gefunden: {project_root}")
                    _log("Schritt 3 Verzeichnis", "FEHLER", f"Nicht gefunden: {project_root}")
                    if not _retry(""):
                        print("  \u26a0\ufe0f  Fortfahren trotz Fehler\n")
                        break
            state["project_root"] = project_root
            _save_state(state)
        else:
            project_root = state["project_root"]
            _log("Schritt 3", "RESUME", project_root)
            _step_done(3, "Projektverzeichnis", project_root)

        # \u2500\u2500 Schritt 4: Labels \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        _box("Schritt 4/9 \u2014 Gitea Labels", [
            "Der Agent kommuniziert \u00fcber Labels in Gitea-Issues.",
            "Diese Labels werden jetzt automatisch im Repository angelegt",
            "sofern sie noch nicht vorhanden sind.",
            "",
            "  Labels die erstellt werden:",
            f"  \u2022 {settings.LABEL_READY:<22} \u2014 Issue bereit f\u00fcr Agent",
            f"  \u2022 {settings.LABEL_PROPOSED:<22} \u2014 Agent hat Plan vorgeschlagen",
            f"  \u2022 {settings.LABEL_PROGRESS:<22} \u2014 Agent arbeitet daran",
            f"  \u2022 {settings.LABEL_REVIEW:<22} \u2014 Bereit f\u00fcr Code-Review",
            f"  \u2022 {settings.LABEL_HELP:<22} \u2014 Manuelle Hilfe ben\u00f6tigt",
        ])
        required_labels = [
            (settings.LABEL_READY,    "0075ca", "Bereit f\u00fcr Agent-Bearbeitung"),
            (settings.LABEL_PROPOSED, "e4e669", "Agent hat Plan vorgeschlagen"),
            (settings.LABEL_PROGRESS, "d93f0b", "Agent arbeitet daran"),
            (settings.LABEL_REVIEW,   "0e8a16", "Bereit f\u00fcr Code-Review"),
            (settings.LABEL_HELP,     "ee0701", "Manuelle Hilfe ben\u00f6tigt"),
        ]
        while True:
            try:
                existing_resp = _api_get_raw(gitea_url, gitea_user, gitea_token,
                                             f"/repos/{gitea_repo}/labels")
                existing_names = {lbl["name"] for lbl in existing_resp}
                missing = [(n, c, d) for n, c, d in required_labels if n not in existing_names]
                if not missing:
                    print(f"  \u2705 Alle {len(required_labels)} Labels bereits vorhanden\n")
                    _log("Schritt 4 Labels", "OK", "Alle vorhanden")
                else:
                    print(f"  Fehlende Labels: {', '.join(n for n,_,_ in missing)}")
                    if input("  Jetzt anlegen? [J/n]: ").strip().lower() in ("", "j", "y"):
                        for name, color, desc in missing:
                            _api_post_raw(gitea_url, gitea_user, gitea_token,
                                          f"/repos/{gitea_repo}/labels",
                                          {"name": name, "color": f"#{color}", "description": desc})
                            print(f"  \u2705 Label '{name}' angelegt")
                            _log("Schritt 4 Label", "OK", f"Angelegt: {name}")
                    print()
                break
            except Exception as exc:
                print(f"  \u274c Label-Pr\u00fcfung fehlgeschlagen: {exc}")
                _log("Schritt 4 Labels", "FEHLER", str(exc))
                if not _retry(""):
                    print("  \u26a0\ufe0f  Labels \u00fcbersprungen\n")
                    break

        # \u2500\u2500 Schritt 5: agent_eval.json \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        _box("Schritt 5/9 \u2014 Evaluierung (agent_eval.json)", [
            "Der Agent kann deinen Server automatisch testen und bewerten.",
            "Daf\u00fcr braucht er die Adresse deines Servers und den Pfad",
            "zur Log-Datei deiner Anwendung.",
            "",
            "  [1] Server-URL \u2014 Adresse deines laufenden Servers",
            "      Protokoll (http:// oder https://) muss angegeben werden.",
            "      Beispiele: http://localhost:8080",
            "                 http://192.168.1.x:8080",
            "                 http://192.168.1.x  (ohne Port wenn Standard)",
            "",
            "  [2] Log-Pfad \u2014 vollst\u00e4ndiger Pfad zur Log-Datei",
            "      Mehrere Pfade kommagetrennt m\u00f6glich.",
            "      Beispiel: /home/user/projekt/logs/app.log",
            "                /home/user/projekt/logs/app.log,/var/log/syslog",
            "",
            "  [3] Start-Script \u2014 Script zum Starten des Servers (optional)",
            "      Beispiel: /home/user/mein-projekt/start.sh",
            "      \u26a0\ufe0f  Ohne Start-Script kann der Agent den Server nicht",
            "          automatisch neu starten (Eval, Restart-Workflow).",
        ])
        eval_file = _HERE / "config" / "agent_eval.json"
        write_eval = True
        if eval_file.exists():
            write_eval = input("  agent_eval.json existiert bereits \u2014 \u00fcberschreiben? [j/N]: ").strip().lower() in ("j", "y")
        if write_eval:
            server_url   = _ask("  [1] Server-URL")
            log_path_raw = _ask("  [2] Log-Pfad (kommagetrennt f\u00fcr mehrere)")
            log_paths    = [p.strip() for p in log_path_raw.split(",") if p.strip()]
            log_path     = log_paths[0] if log_paths else ""
            start_script = _ask("  [3] Start-Script (leer = keins)", "")
            if not start_script:
                print("  \u26a0\ufe0f  Kein Start-Script \u2014 automatischer Neustart nicht m\u00f6glich.\n")
                _log("Schritt 5 Start-Script", "WARNUNG", "Kein Start-Script angegeben")
            eval_data = {"server_url": server_url, "log_path": log_path,
                         "log_paths": log_paths,
                         "start_script": start_script, "watch_interval_minutes": 60}
            eval_file.parent.mkdir(parents=True, exist_ok=True)
            eval_file.write_text(json.dumps(eval_data, indent=2), encoding="utf-8")
            print("  \u2705 agent_eval.json geschrieben\n")
            _log("Schritt 5 agent_eval.json", "OK", str(eval_file))
        else:
            _log("Schritt 5 agent_eval.json", "INFO", "\u00dcbersprungen")
            print("  \u00dcbersprungen\n")

        # \u2500\u2500 Schritt 6: .env \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        _box("Schritt 6/9 \u2014 Konfigurationsdatei (.env)", [
            "Alle eingegebenen Werte werden jetzt in einer .env Datei",
            "im Agenten-Verzeichnis gespeichert.",
            "",
            "  \u26a0\ufe0f  Die .env Datei enth\u00e4lt Tokens und Passw\u00f6rter.",
            "      Sie darf NICHT in git eingecheckt werden!",
            "      Sie ist bereits in .gitignore eingetragen.",
            "",
            "  Gespeichert werden:",
            "  \u2022 GITEA_URL, GITEA_USER, GITEA_TOKEN",
            "  \u2022 GITEA_REPO, GITEA_BOT_USER, GITEA_BOT_TOKEN",
            "  \u2022 PROJECT_ROOT",
        ])
        env_file = _HERE / ".env"
        write_env = True
        if env_file.exists():
            write_env = input("  .env existiert bereits \u2014 \u00fcberschreiben? [j/N]: ").strip().lower() in ("j", "y")
        if write_env:
            env_lines = [
                f"GITEA_URL={gitea_url}", f"GITEA_USER={gitea_user}",
                f"GITEA_TOKEN={gitea_token}", f"GITEA_REPO={gitea_repo}",
                f"GITEA_BOT_USER={bot_user}", f"GITEA_BOT_TOKEN={bot_token}",
                f"PROJECT_ROOT={project_root}",
            ]
            env_file.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
            print(f"  \u2705 .env geschrieben: {env_file}")
            print("  \u26a0\ufe0f  Nicht in Git commiten!\n")
            _log("Schritt 6 .env", "OK", f"{env_file} (Secrets maskiert)")
        else:
            _log("Schritt 6 .env", "INFO", "\u00dcbersprungen")
            print("  \u00dcbersprungen\n")

        # \u2500\u2500 Schritt 7: Projekttyp \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        _box("Schritt 7/9 \u2014 Projekttyp & Features", [
            "W\u00e4hle den Typ deines Projekts. Der Agent aktiviert dann",
            "automatisch die passenden Features.",
            "",
            "  1) web_api         \u2014 REST-API / Web-Server",
            "  2) llm_chat        \u2014 LLM-Chat mit Eval-Tests",
            "  3) voice_assistant \u2014 Voice-Pipeline (STT/TTS/LLM)",
            "  4) iot             \u2014 IoT / Embedded / Edge (z.B. Jetson)",
            "  5) cli_tool        \u2014 Kommandozeilen-Programm",
            "  6) library         \u2014 Python-Bibliothek",
            "  7) custom          \u2014 Alle Features manuell w\u00e4hlen",
        ])
        type_map = {
            "1": "web_api", "2": "llm_chat", "3": "voice_assistant",
            "4": "iot", "5": "cli_tool", "6": "library", "7": "custom",
        }
        type_choice = _ask("  Projekttyp (1-7)", "2")
        proj_type = type_map.get(type_choice, "custom")
        feature_defaults = {
            "web_api":         {"eval": True,  "health_checks": True,  "auto_issues": True,  "changelog": True, "watch": True,  "pr_workflow": True},
            "llm_chat":        {"eval": True,  "health_checks": True,  "auto_issues": True,  "changelog": True, "watch": True,  "pr_workflow": True},
            "voice_assistant": {"eval": True,  "health_checks": True,  "auto_issues": True,  "changelog": True, "watch": True,  "pr_workflow": True},
            "iot":             {"eval": False, "health_checks": False, "auto_issues": True,  "changelog": True, "watch": False, "pr_workflow": True},
            "cli_tool":        {"eval": False, "health_checks": False, "auto_issues": True,  "changelog": True, "watch": False, "pr_workflow": True},
            "library":         {"eval": False, "health_checks": False, "auto_issues": True,  "changelog": True, "watch": False, "pr_workflow": True},
            "custom":          {"eval": False, "health_checks": False, "auto_issues": False, "changelog": True, "watch": False, "pr_workflow": False},
        }
        feature_desc = {
            "eval":          "Bewertet Server-Antworten automatisch  [ben\u00f6tigt: server_url]",
            "health_checks": "Pr\u00fcft ob Server erreichbar ist         [ben\u00f6tigt: server_url]",
            "auto_issues":   "Erstellt Issues bei Testfehlern        [ben\u00f6tigt: eval]",
            "changelog":     "Generiert CHANGELOG.md aus Commits",
            "watch":         "\u00dcberwacht Gitea auf neue Issues",
            "pr_workflow":   "Erstellt PRs nach Implementierung automatisch",
        }
        features = dict(feature_defaults.get(proj_type, feature_defaults["custom"]))
        print(f"\n  Voreinstellungen f\u00fcr '{proj_type}':\n")
        for k, v in features.items():
            chk = '\u2705' if v else '\u274c'
            print(f"    {chk}  {k:<14}  {feature_desc.get(k, '')}")
        print()
        if _ask("  Einzelne Features anpassen? [j/N]", "n").lower() in ("j", "y"):
            print()
            for k in list(features):
                cur = "j" if features[k] else "n"
                ans = _ask(f"  {k:<14} aktivieren? [j/n]", cur)
                features[k] = ans.lower() in ("j", "y")
            print()
        agent_config = Path(project_root) / "config"
        agent_config.mkdir(parents=True, exist_ok=True)
        proj_file = agent_config / "project.json"
        if proj_file.exists():
            if _ask("  project.json existiert. \u00dcberschreiben? [ja/nein]", "nein").lower() not in ("ja", "j", "yes", "y"):
                proj_file = None
        if proj_file:
            proj_file.write_text(json.dumps({"type": proj_type, "features": features}, indent=4, ensure_ascii=False), encoding="utf-8")
            print("  \u2705 project.json geschrieben\n")
            _log("Schritt 7 project.json", "OK", f"type={proj_type}")

        # \u2500\u2500 Schritt 8: LLM-Routing \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        _box("Schritt 8/9 \u2014 LLM-Routing", [
            "Der Agent verwendet ein KI-Modell f\u00fcr seine Aufgaben.",
            "W\u00e4hle Standard-Provider und Modell.",
            "",
            "  \u2022 claude   \u2014 Anthropic Claude  (ANTHROPIC_API_KEY)",
            "  \u2022 openai   \u2014 OpenAI GPT        (OPENAI_API_KEY)",
            "  \u2022 gemini   \u2014 Google Gemini     (GEMINI_API_KEY)",
            "  \u2022 deepseek \u2014 DeepSeek          (DEEPSEEK_API_KEY)",
            "  \u2022 local    \u2014 Ollama, kein Key n\u00f6tig",
            "",
            "  Warum eigener Key? Gezielt widerrufbar ohne dein",
            "  pers\u00f6nliches Konto zu sperren.",
            "",
            "  Per-Task Routing & Fallback: --llm",
        ])
        routing_file = _HERE / "config" / "llm" / "routing.json"
        write_routing = True
        if routing_file.exists():
            write_routing = input("  routing.json existiert bereits \u2014 \u00fcberschreiben? [j/N]: ").strip().lower() in ("j", "y")
        if write_routing:
            _s8_providers = {
                "claude":   ("claude-sonnet-4-6",  "ANTHROPIC_API_KEY",
                             ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"]),
                "openai":   ("gpt-4o-mini",        "OPENAI_API_KEY",
                             ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]),
                "gemini":   ("gemini-1.5-flash",   "GEMINI_API_KEY",
                             ["gemini-1.5-pro", "gemini-1.5-flash"]),
                "deepseek": ("deepseek-chat",      "DEEPSEEK_API_KEY",
                             ["deepseek-chat", "deepseek-coder"]),
            }
            default_provider = _ask("  Standard-Anbieter", "claude")
            _pm = _s8_providers.get(default_provider, ("llama3", "", ["llama3", "mistral", "phi3"]))
            model_default, api_key_hint, model_list = _pm
            if model_list:
                print("  Bekannte Modelle:")
                for _m in model_list:
                    print(f"    \u2022 {_m}")
                print()
            while True:
                default_model = _ask("  Standard-Modell", model_default)
                if default_model.strip():
                    break
                print("  \u274c Modell darf nicht leer sein.")
            if api_key_hint:
                print(f"\n  \u26a0\ufe0f  Nicht vergessen: {api_key_hint}=... in .env eintragen\n")
            routing_data: dict = {
                "_comment": "LLM-Routing \u2014 generiert vom Setup-Wizard. Erweitern: --llm",
                "default": {"provider": default_provider, "model": default_model,
                            "max_tokens": 1024, "timeout": 60},
            }
            routing_file.parent.mkdir(parents=True, exist_ok=True)
            routing_file.write_text(json.dumps(routing_data, indent=4, ensure_ascii=False), encoding="utf-8")
            print("  \u2705 routing.json geschrieben\n")
            print("  \U0001f4a1 Per-Task Routing & Fallback: python3 agent_start.py --llm\n")
            _log("Schritt 8 LLM-Routing", "OK", f"provider={default_provider} model={default_model}")
        else:
            _log("Schritt 8 LLM-Routing", "INFO", "\u00dcbersprungen")
            print("  \u00dcbersprungen\n")

        # \u2500\u2500 Schritt 9: System-Prompts \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        _box("Schritt 9/9 \u2014 System-Prompts", [
            "Der Agent verwendet Rollen-Prompts die sein Verhalten",
            "bei verschiedenen Aufgaben steuern.",
            "",
            "  Prompts werden aus dem Agenten-Verzeichnis in dein",
            "  Projekt unter config/llm/prompts/ kopiert.",
            "",
            "  Du kannst sie danach anpassen \u2014 die Originale bleiben",
            "  im Agenten-Verzeichnis erhalten.",
        ])
        prompts_src = Path(__file__).parent / "config" / "llm" / "prompts"
        prompts_dst = Path(project_root) / "config" / "llm" / "prompts"
        if prompts_src.exists() and prompts_src.resolve() != prompts_dst.resolve():
            if input("  Prompts jetzt ins Projekt kopieren? [J/n]: ").strip().lower() in ("", "j", "y"):
                prompts_dst.mkdir(parents=True, exist_ok=True)
                copied = sum(
                    1 for src_file in prompts_src.glob("*.md")
                    if not (prompts_dst / src_file.name).exists()
                    and (prompts_dst / src_file.name).write_text(src_file.read_text(encoding="utf-8"), encoding="utf-8") is None
                )
                if copied:
                    print(f"  \u2705 {copied} Prompt-Dateien kopiert nach:\n     {prompts_dst}")
                    _log("Schritt 9 Prompts", "OK", f"{copied} Dateien nach {prompts_dst}")
                else:
                    print("  \u2139\ufe0f  Alle Prompts bereits vorhanden")
                    _log("Schritt 9 Prompts", "OK", "Bereits vorhanden")
                print()
            else:
                _log("Schritt 9 Prompts", "INFO", "\u00dcbersprungen")
                print("  \u00dcbersprungen \u2014 Prompts k\u00f6nnen sp\u00e4ter manuell kopiert werden\n")
        else:
            _log("Schritt 9 Prompts", "OK", f"Bereits unter {prompts_dst}")
            print(f"  \u2705 Prompts bereits vorhanden\n")

        # \u2500\u2500 Abschluss \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        _log("SETUP ABGESCHLOSSEN", "OK", f"Install-Log: {_LOG_FILE}")
        _STATE_FILE.unlink(missing_ok=True)
        inner = W - 4
        hr = _H * (W - 2)
        print(f"{_TL}{hr}{_TR}")
        print(f"{_V}{'  SETUP ABGESCHLOSSEN':^{W - 2}}{_V}")
        print(f"{_ML}{hr}{_MR}")
        _log_label = "Install-Log: " + str(_LOG_FILE)
        if len(_log_label) > inner:
            _log_label = "Log: ..." + str(_LOG_FILE)[-(inner - 5):]
        print(f"{_V}  {_log_label:<{inner}}{_V}")
        print(f"{_BL}{hr}{_BR}\n")
        print("  Starte Health-Check...\n")
        cmd_doctor()
        print("\n  Generiere initiales Dashboard...\n")
        cmd_dashboard()
    except KeyboardInterrupt:
        _log("SETUP ABBRUCH", "WARNUNG", "Durch Benutzer abgebrochen (Strg+C) — Resume möglich")
        print("\n\n  Setup abgebrochen. Beim nächsten Start wird dort weitergemacht.\n")
        print(f"  Install-Log: {_LOG_FILE}\n")
        raise
