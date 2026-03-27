"""
plugins/llm_wizard.py — Interaktiver LLM-Konfigurations-Wizard (#129).

Verwaltet config/llm/routing.json nachträglich ohne Setup-Neustart.
Aufruf: python3 agent_start.py --llm

Zukunft: Dashboard kann cmd_llm() und die Menü-Funktionen direkt
aufrufen ohne CLI — gleiche Logik, anderes Frontend.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).parent.parent  # gitea-agent/
_ROUTING_FILE = _HERE / "config" / "llm" / "routing.json"

W = 66
_H = '═'; _TL = '╔'; _TR = '╗'; _BL = '╚'; _BR = '╝'
_V = '║'; _ML = '╠'; _MR = '╣'


def _box(title: str, lines: list) -> None:
    inner = W - 4
    hr = _H * (W - 2)
    print(f"\n{_TL}{hr}{_TR}")
    print(f"{_V}  {title:<{inner}}{_V}")
    print(f"{_ML}{hr}{_MR}")
    for line in lines:
        print(f"{_V}  {line:<{inner}}{_V}")
    print(f"{_BL}{hr}{_BR}\n")


def _ask(prompt: str, default: str = "") -> str:
    disp = f" [{default}]" if default else ""
    val = input(f"  {prompt}{disp}: ").strip()
    return val or default


def _load_routing() -> dict:
    if _ROUTING_FILE.exists():
        try:
            return json.loads(_ROUTING_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_routing(data: dict) -> None:
    _ROUTING_FILE.parent.mkdir(parents=True, exist_ok=True)
    _ROUTING_FILE.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")


_PROVIDER_MODELS: dict = {
    "claude":   ("claude-sonnet-4-6",  "ANTHROPIC_API_KEY",
                 ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"]),
    "openai":   ("gpt-4o-mini",        "OPENAI_API_KEY",
                 ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]),
    "gemini":   ("gemini-1.5-flash",   "GEMINI_API_KEY",
                 ["gemini-1.5-pro", "gemini-1.5-flash"]),
    "deepseek": ("deepseek-chat",      "DEEPSEEK_API_KEY",
                 ["deepseek-chat", "deepseek-coder"]),
    "local":    ("llama3",             "",
                 ["llama3", "mistral", "phi3", "codellama"]),
}

_TASKS = [
    ("issue_analysis",  "Issue-Analyse",    "claude-haiku-4-5-20251001", "config/llm/prompts/analyst.md"),
    ("implementation",  "Implementierung",  "claude-sonnet-4-6",         "config/llm/prompts/senior_python.md"),
    ("pr_review",       "PR-Review",        "claude-sonnet-4-6",         "config/llm/prompts/reviewer.md"),
    ("test_generation", "Test-Generierung", "claude-sonnet-4-6",         "config/llm/prompts/senior_python.md"),
    ("log_analysis",    "Log-Analyse",      "claude-haiku-4-5-20251001", "config/llm/prompts/log_analyst.md"),
    ("healing",         "Self-Healing",     "claude-sonnet-4-6",         "config/llm/prompts/healer.md"),
]


def _show_current(routing: dict) -> None:
    default = routing.get("default", {})
    fallback = routing.get("fallback_chain", [])
    tasks = {k: v for k, v in routing.get("tasks", {}).items() if not k.startswith("_")}
    if default:
        print(f"  Standard:  {default.get('provider', '—')} / {default.get('model', '—')}")
    else:
        print("  Standard:  (nicht konfiguriert)")
    _arr = ' \u2192 '
    if fallback:
        print(f"  Fallback:  {_arr.join(fallback)}")
    if tasks:
        print("  Tasks:")
        for k, v in tasks.items():
            if isinstance(v, dict):
                print(f"    {k:<18} {v.get('provider', '—')} / {v.get('model', '—')}")
    print()


def _menu_default(routing: dict) -> None:
    """Standard-Provider und Modell ändern."""
    default = routing.get("default", {})
    cur_provider = default.get("provider", "claude")
    cur_model = default.get("model", "claude-sonnet-4-6")
    print(f"\n  Aktuell: {cur_provider} / {cur_model}\n")

    provider = _ask("  Standard-Anbieter (claude/openai/gemini/deepseek/local)", cur_provider)
    pm = _PROVIDER_MODELS.get(provider, ("", "", []))
    model_default, key_hint, model_list = pm
    if model_list:
        print("  Bekannte Modelle:")
        for m in model_list:
            print(f"    \u2022 {m}")
        print()
    while True:
        model = _ask("  Standard-Modell", cur_model if cur_model else model_default)
        if model.strip():
            break
        print("  \u274c Modell darf nicht leer sein.")

    routing.setdefault("default", {})
    routing["default"].update({"provider": provider, "model": model})
    routing["default"].setdefault("max_tokens", 1024)
    routing["default"].setdefault("timeout", 60)

    if key_hint:
        print(f"\n  \u26a0\ufe0f  Nicht vergessen: {key_hint}=... in .env eintragen\n")

    _save_routing(routing)
    print("  \u2705 Standard-Konfiguration gespeichert.\n")


def _menu_tasks(routing: dict) -> None:
    """Per-Task Routing konfigurieren."""
    default_provider = routing.get("default", {}).get("provider", "claude")
    tasks = routing.setdefault("tasks", {})
    print("\n  Für jeden Task kannst du Provider und Modell festlegen.")
    print("  Enter = Standardwert übernehmen.\n")
    for task_key, task_label, suggested_model, default_prompt in _TASKS:
        cur = tasks.get(task_key, {}) if isinstance(tasks.get(task_key), dict) else {}
        cur_p = cur.get("provider", default_provider)
        cur_m = cur.get("model", suggested_model)
        print(f"  \u2500\u2500 {task_label}")
        tp = _ask(f"    Anbieter", cur_p)
        tm = _ask(f"    Modell", cur_m)
        tc: dict = {"provider": tp, "model": tm, "system_prompt": default_prompt}
        if tp in ("local", "lmstudio"):
            tc["base_url"] = _ask(f"    Base-URL", cur.get("base_url", "http://localhost:11434"))
        tasks[task_key] = tc
        print()
    _save_routing(routing)
    print("  \u2705 Task-Routing gespeichert.\n")


def _menu_fallback(routing: dict) -> None:
    """Fallback-Kette konfigurieren."""
    _arr = ' \u2192 '
    cur = routing.get("fallback_chain", [])
    _cur_str = _arr.join(cur) if cur else "(keine)"
    print(f"\n  Aktuelle Fallback-Kette: {_cur_str}")
    print("  Wenn der primäre Provider nicht erreichbar ist, wird")
    print("  der nächste in der Kette versucht.")
    print("  Eingabe: Anbieter leerzeichen-getrennt, z.B.: claude openai local")
    print("  (Leer lassen um Fallback zu deaktivieren)\n")
    raw = _ask("  Fallback-Kette", " ".join(cur))
    chain = [x.strip() for x in raw.split() if x.strip()]
    if chain:
        routing["fallback_chain"] = chain
    elif "fallback_chain" in routing:
        del routing["fallback_chain"]
    _save_routing(routing)
    _chain_str = _arr.join(chain) if chain else "deaktiviert"
    print(f"  \u2705 Fallback: {_chain_str}\n")


def _menu_test(routing: dict) -> None:
    """Konnektivität testen."""
    print()
    try:
        from plugins.llm import get_client
    except ImportError:
        from llm import get_client  # type: ignore

    provider = routing.get("default", {}).get("provider", "claude")
    model = routing.get("default", {}).get("model", "")
    print(f"  Teste {provider} / {model} ...")
    try:
        client = get_client("default")
        resp = client.complete("Antworte nur mit dem Wort: OK")
        if resp.ok:
            print(f"  \u2705 Verbindung OK \u2014 Antwort: {resp.text[:80].strip()}\n")
        else:
            print(f"  \u274c Fehler: {resp.error}\n")
    except Exception as exc:
        print(f"  \u274c Verbindungsfehler: {exc}\n")


def cmd_llm() -> None:
    """Interaktiver LLM-Konfigurations-Wizard — nachträgliche Verwaltung."""
    _box("LLM-Konfiguration — gitea-agent", [
        "Verwalte Provider, Modelle und Fallback-Kette.",
        f"Datei: config/llm/routing.json",
        "",
        "  \u00c4nderungen wirken sofort \u2014 kein Setup-Neustart n\u00f6tig.",
    ])

    while True:
        routing = _load_routing()
        print("  Aktuelle Konfiguration:")
        _show_current(routing)
        print("  [1] Standard-Provider / Modell \u00e4ndern")
        print("  [2] Per-Task Routing konfigurieren")
        print("  [3] Fallback-Kette konfigurieren")
        print("  [4] Konnektivit\u00e4t testen")
        print("  [5] Beenden\n")

        choice = _ask("  Auswahl", "5")
        print()
        if choice == "1":
            _menu_default(routing)
        elif choice == "2":
            _menu_tasks(routing)
        elif choice == "3":
            _menu_fallback(routing)
        elif choice == "4":
            _menu_test(routing)
        else:
            break
