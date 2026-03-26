"""
tests/test_llm.py — Tests für plugins/llm.py (Issues #54 + #95)
"""
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.llm import (
    ClaudeClient,
    GeminiClient,
    LocalClient,
    LLMResponse,
    OpenAIClient,
    _build_client,
    _load_routing,
    _resolve_task_config,
    complete,
    get_client,
)


class TestLLMResponse(unittest.TestCase):
    def test_ok_with_text(self):
        r = LLMResponse(text="hello", provider="claude", model="sonnet")
        self.assertTrue(r.ok)

    def test_not_ok_empty(self):
        r = LLMResponse(text="", provider="claude", model="sonnet")
        self.assertFalse(r.ok)

    def test_not_ok_with_error(self):
        r = LLMResponse(text="hello", provider="claude", model="sonnet", error="oops")
        self.assertFalse(r.ok)


class TestLoadRouting(unittest.TestCase):
    def test_no_config(self):
        result = _load_routing(Path("/nonexistent/llm_routing.json"))
        self.assertEqual(result, {})

    def test_valid_config(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            cfg_file = Path(td) / "llm_routing.json"
            cfg_file.write_text(json.dumps({
                "default": {"provider": "claude", "model": "sonnet"},
                "tasks": {"log_analysis": {"provider": "local", "model": "llama3"}},
            }), encoding="utf-8")
            result = _load_routing(cfg_file)
        self.assertEqual(result["default"]["provider"], "claude")
        self.assertIn("log_analysis", result["tasks"])

    def test_invalid_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            cfg_file = Path(td) / "llm_routing.json"
            cfg_file.write_text("{ invalid json", encoding="utf-8")
            result = _load_routing(cfg_file)
        self.assertEqual(result, {})


class TestResolveTaskConfig(unittest.TestCase):
    def setUp(self):
        self.routing = {
            "default": {"provider": "claude", "model": "sonnet"},
            "tasks": {
                "log_analysis": {"provider": "local", "model": "llama3"},
                "implementation": {"provider": "claude", "model": "opus"},
            },
        }

    def test_known_task(self):
        cfg = _resolve_task_config("log_analysis", self.routing)
        self.assertEqual(cfg["provider"], "local")

    def test_unknown_task_falls_back_to_default(self):
        cfg = _resolve_task_config("unknown_task", self.routing)
        self.assertEqual(cfg["provider"], "claude")
        self.assertEqual(cfg["model"], "sonnet")

    def test_default_as_string(self):
        routing = {"default": "claude-sonnet-4-6", "tasks": {}}
        cfg = _resolve_task_config("anything", routing)
        self.assertEqual(cfg["provider"], "claude")
        self.assertEqual(cfg["model"], "claude-sonnet-4-6")

    def test_empty_routing(self):
        cfg = _resolve_task_config("log_analysis", {})
        self.assertEqual(cfg, {})


class TestBuildClient(unittest.TestCase):
    def test_claude(self):
        client = _build_client({"provider": "claude", "model": "haiku"})
        self.assertIsInstance(client, ClaudeClient)
        self.assertEqual(client.model, "haiku")

    def test_openai(self):
        client = _build_client({"provider": "openai", "model": "gpt-4o-mini"})
        self.assertIsInstance(client, OpenAIClient)

    def test_gemini(self):
        client = _build_client({"provider": "gemini", "model": "gemini-1.5-flash"})
        self.assertIsInstance(client, GeminiClient)

    def test_local(self):
        client = _build_client({"provider": "local", "model": "llama3",
                                 "base_url": "http://localhost:11434"})
        self.assertIsInstance(client, LocalClient)
        self.assertEqual(client.model, "llama3")

    def test_ollama_alias(self):
        client = _build_client({"provider": "ollama", "model": "mistral"})
        self.assertIsInstance(client, LocalClient)

    def test_unknown_provider_falls_back_to_local(self):
        client = _build_client({"provider": "unknown_xyz", "model": "test"})
        self.assertIsInstance(client, LocalClient)


class TestClaudeClient(unittest.TestCase):
    def _mock_response(self, text: str, input_tokens: int = 10, output_tokens: int = 20):
        mock = MagicMock()
        mock.read.return_value = json.dumps({
            "content": [{"text": text}],
            "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        }).encode()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        return mock

    def test_success(self):
        client = ClaudeClient(model="haiku", api_key="test-key")
        with patch("urllib.request.urlopen", return_value=self._mock_response("Hallo!")):
            resp = client.complete("Sag Hallo")
        self.assertTrue(resp.ok)
        self.assertEqual(resp.text, "Hallo!")
        self.assertEqual(resp.provider, "claude")
        self.assertEqual(resp.tokens_used, 30)

    def test_api_error(self):
        client = ClaudeClient(model="haiku", api_key="bad-key")
        err = urllib.error.HTTPError("", 401, "Unauthorized", {}, None)
        with patch("urllib.request.urlopen", side_effect=err):
            resp = client.complete("test")
        self.assertFalse(resp.ok)
        self.assertNotEqual(resp.error, "")

    def test_connection_error(self):
        client = ClaudeClient(model="haiku", api_key="key")
        with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError):
            resp = client.complete("test")
        self.assertFalse(resp.ok)


class TestOpenAIClient(unittest.TestCase):
    def test_success(self):
        client = OpenAIClient(model="gpt-4o-mini", api_key="test")
        mock = MagicMock()
        mock.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Antwort"}}],
            "usage": {"total_tokens": 50},
        }).encode()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock):
            resp = client.complete("Frage")
        self.assertTrue(resp.ok)
        self.assertEqual(resp.text, "Antwort")
        self.assertEqual(resp.tokens_used, 50)

    def test_connection_error(self):
        client = OpenAIClient(model="gpt-4o-mini", api_key="key")
        with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError):
            resp = client.complete("test")
        self.assertFalse(resp.ok)


class TestGeminiClient(unittest.TestCase):
    def test_success(self):
        client = GeminiClient(model="gemini-1.5-flash", api_key="test")
        mock = MagicMock()
        mock.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "Gemini sagt hallo"}]}}],
            "usageMetadata": {"totalTokenCount": 42},
        }).encode()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock):
            resp = client.complete("Hallo")
        self.assertTrue(resp.ok)
        self.assertEqual(resp.text, "Gemini sagt hallo")
        self.assertEqual(resp.tokens_used, 42)


class TestLocalClient(unittest.TestCase):
    def test_success(self):
        client = LocalClient(model="llama3")
        mock = MagicMock()
        mock.read.return_value = json.dumps({"response": "Lokale Antwort"}).encode()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock):
            resp = client.complete("Frage")
        self.assertTrue(resp.ok)
        self.assertEqual(resp.text, "Lokale Antwort")
        self.assertEqual(resp.provider, "local")

    def test_connection_error(self):
        client = LocalClient(model="llama3")
        with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError):
            resp = client.complete("test")
        self.assertFalse(resp.ok)


class TestGetClient(unittest.TestCase):
    def test_no_routing_falls_back_to_env(self):
        with patch("plugins.llm._load_routing", return_value={}):
            with patch("plugins.llm._client_from_env",
                       return_value=LocalClient("llama3")) as mock_env:
                client = get_client("log_analysis")
        mock_env.assert_called_once()
        self.assertIsInstance(client, LocalClient)

    def test_routing_selects_correct_provider(self):
        routing = {
            "default": {"provider": "claude", "model": "sonnet"},
            "tasks": {"log_analysis": {"provider": "local", "model": "llama3"}},
        }
        with patch("plugins.llm._load_routing", return_value=routing):
            client = get_client("log_analysis")
        self.assertIsInstance(client, LocalClient)

    def test_default_used_for_unknown_task(self):
        routing = {
            "default": {"provider": "openai", "model": "gpt-4o-mini"},
            "tasks": {},
        }
        with patch("plugins.llm._load_routing", return_value=routing):
            with patch("plugins.llm._build_client",
                       return_value=OpenAIClient("gpt-4o-mini", "key")) as mock_build:
                get_client("nonexistent_task")
        mock_build.assert_called_once()


class TestCompleteConvenience(unittest.TestCase):
    def test_delegates_to_client(self):
        mock_client = MagicMock()
        mock_client.complete.return_value = LLMResponse(
            text="result", provider="claude", model="sonnet"
        )
        with patch("plugins.llm.get_client", return_value=mock_client):
            resp = complete("mein prompt", task="implementation")
        mock_client.complete.assert_called_once_with("mein prompt")
        self.assertEqual(resp.text, "result")


if __name__ == "__main__":
    unittest.main()
