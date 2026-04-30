"""
Tests for OpenRouterClient.

Mocked unit tests — no real API calls. Validates:
- Client construction + auth guards
- Per-model mitigations applied correctly (JSON format, max_tokens, English prefix)
- Retry logic invokes and surfaces errors cleanly
- Response parsing handles empty / malformed cases
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from openai import APIError, APITimeoutError, RateLimitError

from infrastructure.external.openrouter_client import (
    JudgeAPIError,
    OpenRouterClient,
)


def _mk_fake_response(content: str = '{"ok": true}') -> MagicMock:
    """Build a MagicMock shaped like openai.types.chat.ChatCompletion."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


class TestOpenRouterClientConstruction:
    def test_raises_on_missing_api_key(self):
        with pytest.raises(ValueError, match="OpenRouter API key is required"):
            OpenRouterClient(api_key="")

    def test_raises_on_none_api_key(self):
        with pytest.raises(ValueError, match="OpenRouter API key is required"):
            OpenRouterClient(api_key=None)  # type: ignore[arg-type]

    def test_constructs_with_defaults(self):
        client = OpenRouterClient(api_key="sk-or-v1-test")
        assert client._max_retries == 3

    def test_constructs_with_custom_retries(self):
        client = OpenRouterClient(api_key="sk-or-v1-test", max_retries=5)
        assert client._max_retries == 5


class TestOpenRouterClientCall:
    def _mk_client(self) -> OpenRouterClient:
        return OpenRouterClient(api_key="sk-or-v1-test", max_retries=2)

    def test_returns_content_on_success(self):
        client = self._mk_client()
        fake = _mk_fake_response(content='{"score": 2}')
        with patch.object(client._client.chat.completions, "create", return_value=fake):
            result = client.call("test prompt", model="qwen/qwen3-235b-a22b-07-25")
        assert result == '{"score": 2}'

    def test_passes_temperature(self):
        client = self._mk_client()
        fake = _mk_fake_response()
        with patch.object(
            client._client.chat.completions, "create", return_value=fake
        ) as mock_create:
            client.call("p", model="openai/gpt-4o-mini-2024-07-18", temperature=0.5)
        assert mock_create.call_args.kwargs["temperature"] == 0.5

    def test_passes_seed_when_set(self):
        client = self._mk_client()
        fake = _mk_fake_response()
        with patch.object(
            client._client.chat.completions, "create", return_value=fake
        ) as mock_create:
            client.call("p", model="qwen/qwen3-235b-a22b-07-25", seed=42)
        assert mock_create.call_args.kwargs["seed"] == 42

    def test_omits_seed_when_none(self):
        client = self._mk_client()
        fake = _mk_fake_response()
        with patch.object(
            client._client.chat.completions, "create", return_value=fake
        ) as mock_create:
            client.call("p", model="qwen/qwen3-235b-a22b-07-25", seed=None)
        assert "seed" not in mock_create.call_args.kwargs


class TestPerModelMitigations:
    def _mk_client(self) -> OpenRouterClient:
        return OpenRouterClient(api_key="sk-or-v1-test", max_retries=2)

    def test_qwen_gets_json_response_format(self):
        """Qwen MoE model must force JSON output to defeat routing-induced format drift."""
        client = self._mk_client()
        fake = _mk_fake_response()
        with patch.object(
            client._client.chat.completions, "create", return_value=fake
        ) as mock_create:
            client.call("p", model="qwen/qwen3-235b-a22b-07-25")
        assert mock_create.call_args.kwargs["response_format"] == {"type": "json_object"}

    def test_qwen_2507_alias_gets_json_format(self):
        client = self._mk_client()
        fake = _mk_fake_response()
        with patch.object(
            client._client.chat.completions, "create", return_value=fake
        ) as mock_create:
            client.call("p", model="qwen/qwen3-235b-a22b-2507")
        assert mock_create.call_args.kwargs["response_format"] == {"type": "json_object"}

    def test_gpt4o_mini_gets_default_max_tokens(self):
        """GPT-4o-mini needs max_tokens cap to prevent CoT truncation."""
        client = self._mk_client()
        fake = _mk_fake_response()
        with patch.object(
            client._client.chat.completions, "create", return_value=fake
        ) as mock_create:
            client.call("p", model="openai/gpt-4o-mini-2024-07-18")
        assert mock_create.call_args.kwargs["max_tokens"] == 1200

    def test_explicit_max_tokens_overrides_default(self):
        client = self._mk_client()
        fake = _mk_fake_response()
        with patch.object(
            client._client.chat.completions, "create", return_value=fake
        ) as mock_create:
            client.call(
                "p",
                model="openai/gpt-4o-mini-2024-07-18",
                max_tokens=500,
            )
        assert mock_create.call_args.kwargs["max_tokens"] == 500

    def test_qwen_does_not_get_json_if_not_in_list(self):
        """Other models do not get response_format forced."""
        client = self._mk_client()
        fake = _mk_fake_response()
        with patch.object(
            client._client.chat.completions, "create", return_value=fake
        ) as mock_create:
            client.call("p", model="openai/gpt-4o-mini-2024-07-18")
        assert "response_format" not in mock_create.call_args.kwargs

    def test_deepseek_gets_english_prefix(self):
        """DeepSeek occasionally emits Chinese — prefix suppresses this."""
        client = self._mk_client()
        fake = _mk_fake_response()
        with patch.object(
            client._client.chat.completions, "create", return_value=fake
        ) as mock_create:
            client.call("my prompt text", model="deepseek/deepseek-v3.2-20251201")
        content = mock_create.call_args.kwargs["messages"][0]["content"]
        assert content.startswith("Respond in English only.")
        assert "my prompt text" in content

    def test_qwen_does_not_get_english_prefix(self):
        """Prefix is DeepSeek-specific; Qwen handles English fine."""
        client = self._mk_client()
        fake = _mk_fake_response()
        with patch.object(
            client._client.chat.completions, "create", return_value=fake
        ) as mock_create:
            client.call("my prompt text", model="qwen/qwen3-235b-a22b-07-25")
        content = mock_create.call_args.kwargs["messages"][0]["content"]
        assert content == "my prompt text"


class TestErrorHandling:
    def _mk_client(self, max_retries: int = 2) -> OpenRouterClient:
        return OpenRouterClient(api_key="sk-or-v1-test", max_retries=max_retries)

    def test_raises_judge_api_error_on_persistent_timeout(self):
        client = self._mk_client(max_retries=2)
        with patch.object(
            client._client.chat.completions,
            "create",
            side_effect=APITimeoutError(request=MagicMock()),
        ):
            with pytest.raises(JudgeAPIError, match="APITimeoutError"):
                client.call("p", model="qwen/qwen3-235b-a22b-07-25")

    def test_raises_judge_api_error_on_rate_limit(self):
        client = self._mk_client(max_retries=2)
        mock_response = MagicMock()
        mock_response.request = MagicMock()
        with patch.object(
            client._client.chat.completions,
            "create",
            side_effect=RateLimitError(
                "rate limited", response=mock_response, body=None
            ),
        ):
            with pytest.raises(JudgeAPIError, match="RateLimitError"):
                client.call("p", model="qwen/qwen3-235b-a22b-07-25")

    def test_retries_then_succeeds(self):
        """Transient failure then success — tenacity should retry."""
        client = self._mk_client(max_retries=3)
        fake = _mk_fake_response(content="success")
        side_effects = [APITimeoutError(request=MagicMock()), fake]
        with patch.object(
            client._client.chat.completions, "create", side_effect=side_effects
        ) as mock_create:
            result = client.call("p", model="qwen/qwen3-235b-a22b-07-25")
        assert result == "success"
        assert mock_create.call_count == 2

    def test_raises_on_empty_choices(self):
        client = self._mk_client(max_retries=1)
        empty_resp = MagicMock()
        empty_resp.choices = []
        with patch.object(
            client._client.chat.completions, "create", return_value=empty_resp
        ):
            with pytest.raises(JudgeAPIError, match="no choices"):
                client.call("p", model="qwen/qwen3-235b-a22b-07-25")

    def test_raises_on_empty_content(self):
        client = self._mk_client(max_retries=1)
        resp_with_empty_content = _mk_fake_response(content="")
        with patch.object(
            client._client.chat.completions, "create", return_value=resp_with_empty_content
        ):
            with pytest.raises(JudgeAPIError, match="empty content"):
                client.call("p", model="qwen/qwen3-235b-a22b-07-25")

    def test_non_retryable_error_propagates(self):
        """ValueError (not in retry-types) should propagate immediately without retries."""
        client = self._mk_client(max_retries=3)
        with patch.object(
            client._client.chat.completions,
            "create",
            side_effect=ValueError("bad request"),
        ) as mock_create:
            with pytest.raises(ValueError, match="bad request"):
                client.call("p", model="qwen/qwen3-235b-a22b-07-25")
        assert mock_create.call_count == 1
