"""
plugins/llm.py — LLM-agnostischer Orchestrator + Multi-LLM-Routing (Issues #54 + #95).

Bietet eine einheitliche Schnittstelle für verschiedene LLM-Anbieter:
    - claude   : Anthropic API (HTTP, kein SDK-Zwang)
    - openai   : OpenAI-kompatible API (OpenAI, Together, Groq, LM Studio ...)
    - gemini   : Google Gemini API
    - local    : Ollama-Format (llama.cpp, Ollama, LM Studio)

Aufgaben-Routing via agent/config/llm_routing.json (optional):
    Ohne Konfiguration → Fallback auf CLAUDE_API_ENABLED / lokale LLM aus .env

System-Prompts (Issue #111):
    Jeder Task kann einen system_prompt Pfad in llm_routing.json referenzieren.
    Die Datei (z.B. config/llm/prompts/senior_python.md) wird als Rollen-Instruktion geladen.

Aufgerufen von:
    plugins/healing.py, log_analyzer.template.py, agent_start.py
    Direkt: get_client(task="implementation").complete(prompt)
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Routing-Konfiguration laden
# ---------------------------------------------------------------------------

_ROUTING_PATHS = [
    Path(__file__).parent.parent / "config" / "llm" / "routing.json",
]


def _load_routing(extra_path: Optional[Path] = None) -> dict:
    """Lädt llm_routing.json — gibt leeres Dict zurück wenn nicht vorhanden."""
    if extra_path is not None:
        if extra_path.exists():
            try:
                return json.loads(extra_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}
    for p in _ROUTING_PATHS:
        if p and p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {}


def _resolve_task_config(task: str, routing: dict) -> dict:
    """Löst Task-Name zu Provider/Model-Config auf. Fallback: default → env."""
    tasks = routing.get("tasks", {})
    if task in tasks:
        return tasks[task]
    default = routing.get("default")
    if isinstance(default, dict):
        return default
    if isinstance(default, str):
        # "claude-sonnet-4-6" → {provider: "claude", model: "claude-sonnet-4-6"}
        return {"provider": "claude", "model": default}
    return {}


def _load_system_prompt(cfg: dict) -> str:
    """
    Lädt System-Prompt aus Datei wenn 'system_prompt' in cfg gesetzt.
    Sucht relativ zum Projekt-Root (zwei Ebenen über plugins/).
    """
    sp = cfg.get("system_prompt", "")
    if not sp:
        return ""
    base = Path(__file__).parent.parent  # gitea-agent/
    candidate = base / sp
    if candidate.exists():
        try:
            return candidate.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return ""


# ---------------------------------------------------------------------------
# Antwort-Datenklasse
# ---------------------------------------------------------------------------

@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    tokens_used: int = 0
    error: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.text) and not self.error


# ---------------------------------------------------------------------------
# Provider-Implementierungen (reine stdlib)
# ---------------------------------------------------------------------------

def _http_post(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


class ClaudeClient:
    """Anthropic Messages API — direkte HTTP-Implementierung."""

    BASE_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def __init__(self, model: str, api_key: str, max_tokens: int = 1024, timeout: int = 60,
                 system_prompt: str = ""):
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.system_prompt = system_prompt

    def complete(self, prompt: str) -> LLMResponse:
        try:
            payload: dict = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if self.system_prompt:
                payload["system"] = self.system_prompt
            result = _http_post(
                self.BASE_URL,
                payload,
                {
                    "x-api-key": self.api_key,
                    "anthropic-version": self.API_VERSION,
                    "content-type": "application/json",
                },
                self.timeout,
            )
            text = result["content"][0]["text"].strip()
            usage = result.get("usage", {})
            tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            return LLMResponse(text=text, provider="claude", model=self.model, tokens_used=tokens)
        except Exception as exc:
            return LLMResponse(text="", provider="claude", model=self.model, error=str(exc))


class OpenAIClient:
    """OpenAI-kompatible Chat-Completions API."""

    _PROVIDER = "openai"

    def __init__(self, model: str, api_key: str, base_url: str = "https://api.openai.com/v1",
                 max_tokens: int = 1024, timeout: int = 60, system_prompt: str = ""):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.system_prompt = system_prompt

    def complete(self, prompt: str) -> LLMResponse:
        try:
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            messages.append({"role": "user", "content": prompt})
            result = _http_post(
                f"{self.base_url}/chat/completions",
                {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "messages": messages,
                    "temperature": 0.2,
                },
                {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                self.timeout,
            )
            text = result["choices"][0]["message"]["content"].strip()
            tokens = result.get("usage", {}).get("total_tokens", 0)
            return LLMResponse(text=text, provider=self._PROVIDER, model=self.model, tokens_used=tokens)
        except Exception as exc:
            return LLMResponse(text="", provider=self._PROVIDER, model=self.model, error=str(exc))


class DeepseekClient(OpenAIClient):
    """Deepseek API — OpenAI-kompatibel, eigene Base-URL."""

    _PROVIDER = "deepseek"
    _BASE_URL  = "https://api.deepseek.com/v1"

    def __init__(self, model: str, api_key: str, max_tokens: int = 1024, timeout: int = 60):
        super().__init__(model=model, api_key=api_key,
                         base_url=self._BASE_URL,
                         max_tokens=max_tokens, timeout=timeout)


class LMStudioClient(OpenAIClient):
    """LM Studio lokale API — OpenAI-kompatibel, Standard-Port 1234."""

    _PROVIDER = "lmstudio"
    _BASE_URL  = "http://localhost:1234/v1"

    def __init__(self, model: str, api_key: str = "lm-studio",
                 base_url: str = _BASE_URL, max_tokens: int = 1024, timeout: int = 60):
        super().__init__(model=model, api_key=api_key,
                         base_url=base_url,
                         max_tokens=max_tokens, timeout=timeout)


class GeminiClient:
    """Google Gemini generateContent API."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, model: str, api_key: str, max_tokens: int = 1024, timeout: int = 60,
                 system_prompt: str = ""):
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.system_prompt = system_prompt

    def complete(self, prompt: str) -> LLMResponse:
        try:
            url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"
            payload: dict = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": self.max_tokens, "temperature": 0.2},
            }
            if self.system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": self.system_prompt}]}
            result = _http_post(
                url,
                payload,
                {"Content-Type": "application/json"},
                self.timeout,
            )
            text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            usage = result.get("usageMetadata", {})
            tokens = usage.get("totalTokenCount", 0)
            return LLMResponse(text=text, provider="gemini", model=self.model, tokens_used=tokens)
        except Exception as exc:
            return LLMResponse(text="", provider="gemini", model=self.model, error=str(exc))


class LocalClient:
    """Ollama/llama.cpp-kompatible HTTP-API (generate-Endpunkt)."""

    def __init__(self, model: str, base_url: str = "http://localhost:11434",
                 max_tokens: int = 1024, timeout: int = 60, system_prompt: str = ""):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.system_prompt = system_prompt

    def complete(self, prompt: str) -> LLMResponse:
        try:
            payload: dict = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": self.max_tokens},
            }
            if self.system_prompt:
                payload["system"] = self.system_prompt
            result = _http_post(
                f"{self.base_url}/api/generate",
                payload,
                {"Content-Type": "application/json"},
                self.timeout,
            )
            text = result.get("response", "").strip()
            return LLMResponse(text=text, provider="local", model=self.model)
        except Exception as exc:
            return LLMResponse(text="", provider="local", model=self.model, error=str(exc))


# ---------------------------------------------------------------------------
# Env-Fallback
# ---------------------------------------------------------------------------

def _client_from_env() -> Optional["ClaudeClient | LocalClient"]:
    """
    Erzeugt Client aus Umgebungsvariablen (.env / os.environ).
    Reihenfolge: CLAUDE_API_ENABLED → ANTHROPIC_API_KEY → lokale LLM.
    """
    import os
    # .env einlesen wenn vorhanden
    env_file = Path(__file__).parent.parent / ".env"
    env: dict[str, str] = {}
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()

    def _get(key: str, default: str = "") -> str:
        return os.environ.get(key, env.get(key, default))

    deepseek_enabled = _get("DEEPSEEK_API_ENABLED", "false").lower() in ("true", "1", "yes")
    deepseek_key = _get("DEEPSEEK_API_KEY", "")
    if deepseek_enabled and deepseek_key:
        model = _get("DEEPSEEK_MODEL", "deepseek-chat")
        return DeepseekClient(model=model, api_key=deepseek_key)

    claude_enabled = _get("CLAUDE_API_ENABLED", "false").lower() in ("true", "1", "yes")
    api_key = _get("ANTHROPIC_API_KEY", "")
    if claude_enabled and api_key:
        model = _get("CLAUDE_MODEL", "claude-sonnet-4-6")
        return ClaudeClient(model=model, api_key=api_key)

    lmstudio_enabled = _get("LMSTUDIO_ENABLED", "false").lower() in ("true", "1", "yes")
    if lmstudio_enabled:
        model = _get("LMSTUDIO_MODEL", "local-model")
        base_url = _get("LMSTUDIO_URL", LMStudioClient._BASE_URL)
        return LMStudioClient(model=model, base_url=base_url)

    local_url = _get("LLM_LOCAL_URL", "http://localhost:11434")
    local_model = _get("LLM_LOCAL_MODEL", "llama3")
    return LocalClient(model=local_model, base_url=local_url)


def _build_client(cfg: dict) -> "ClaudeClient | OpenAIClient | GeminiClient | LocalClient":
    """Baut Client-Objekt aus Routing-Config-Dict (inkl. system_prompt)."""

    def _get_key(env_var: str) -> str:
        import os as _os
        val = _os.environ.get(env_var, "")
        if not val:
            env_file = Path(__file__).parent.parent / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith(f"{env_var}="):
                        val = line.split("=", 1)[1].strip()
                        break
        return val

    provider = cfg.get("provider", "claude").lower()
    model = cfg.get("model", "")
    max_tokens = int(cfg.get("max_tokens", 1024))
    timeout = int(cfg.get("timeout", 60))
    system_prompt = _load_system_prompt(cfg)

    if provider == "claude":
        api_key = _get_key("ANTHROPIC_API_KEY")
        return ClaudeClient(model=model or "claude-sonnet-4-6",
                            api_key=api_key, max_tokens=max_tokens, timeout=timeout,
                            system_prompt=system_prompt)
    elif provider == "openai":
        api_key = _get_key("OPENAI_API_KEY")
        base_url = cfg.get("base_url", "https://api.openai.com/v1")
        return OpenAIClient(model=model or "gpt-4o-mini",
                            api_key=api_key, base_url=base_url,
                            max_tokens=max_tokens, timeout=timeout,
                            system_prompt=system_prompt)
    elif provider == "gemini":
        api_key = _get_key("GEMINI_API_KEY")
        return GeminiClient(model=model or "gemini-1.5-flash",
                            api_key=api_key, max_tokens=max_tokens, timeout=timeout,
                            system_prompt=system_prompt)
    elif provider == "deepseek":
        api_key = _get_key("DEEPSEEK_API_KEY")
        return DeepseekClient(model=model or "deepseek-chat",
                              api_key=api_key, max_tokens=max_tokens, timeout=timeout)
    elif provider == "lmstudio":
        base_url = cfg.get("base_url", LMStudioClient._BASE_URL)
        return LMStudioClient(model=model or "local-model",
                              base_url=base_url, max_tokens=max_tokens, timeout=timeout)
    elif provider in ("local", "ollama"):
        base_url = cfg.get("base_url", "http://localhost:11434")
        return LocalClient(model=model or "llama3",
                           base_url=base_url, max_tokens=max_tokens, timeout=timeout,
                           system_prompt=system_prompt)
    else:
        # Unbekannter Provider → lokaler Fallback
        return LocalClient(model=model or "llama3", system_prompt=system_prompt)


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------

def get_client(
    task: str = "default",
    routing_path: Optional[Path] = None,
) -> "ClaudeClient | OpenAIClient | GeminiClient | LocalClient":
    """
    Gibt den konfigurierten LLM-Client für eine bestimmte Aufgabe zurück.

    Args:
        task:          Aufgaben-Typ (z.B. "implementation", "log_analysis", "healing")
        routing_path:  Optionaler Pfad zu llm_routing.json (überschreibt Standard)

    Returns:
        Konfigurierten LLM-Client mit .complete(prompt) → LLMResponse

    Beispiel:
        client = get_client("log_analysis")
        resp = client.complete("Analysiere diesen Log: ...")
        if resp.ok:
            print(resp.text)
    """
    routing = _load_routing(routing_path)
    if not routing:
        # Kein Routing-Config → Env-Fallback
        return _client_from_env()

    task_cfg = _resolve_task_config(task, routing)
    if not task_cfg:
        return _client_from_env()

    return _build_client(task_cfg)


def complete(
    prompt: str,
    task: str = "default",
    routing_path: Optional[Path] = None,
) -> LLMResponse:
    """
    Convenience-Wrapper: Routing-Client wählen + Prompt direkt ausführen.

    Beispiel:
        resp = complete("Schreibe einen Fix für...", task="implementation")
    """
    client = get_client(task=task, routing_path=routing_path)
    return client.complete(prompt)
