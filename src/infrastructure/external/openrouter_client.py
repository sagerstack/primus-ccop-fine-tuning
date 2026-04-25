"""
OpenRouter Judge Client

Thin wrapper around the OpenAI Python SDK pointed at OpenRouter's
OpenAI-compatible endpoint. Handles per-model mitigations, retry with
exponential backoff, and raises a domain-specific error on persistent failure.

References:
  - OpenRouter docs: https://openrouter.ai/docs/quickstart
  - Path B recommendation: research/llm-judge-cybersec/followup-openrouter-judge/30-recommendation.md
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class JudgeAPIError(RuntimeError):
    """Raised when OpenRouter judge call fails after all retries exhausted."""


# Models that require strict JSON output format to defeat MoE-routing drift
_JSON_FORMAT_MODELS = frozenset(
    [
        # Qwen MoE family
        "qwen/qwen3-235b-a22b-07-25",
        "qwen/qwen3-235b-a22b-2507",
    ]
)

# Models where we need to bound output length to prevent CoT truncation mid-thought
_DEFAULT_MAX_TOKENS = {
    "openai/gpt-4o-mini-2024-07-18": 1200,
    "openai/gpt-4o-mini": 1200,
}

# Models where provider tends to emit non-English tokens on unfamiliar English content
_ENGLISH_ONLY_PREFIX_MODELS = frozenset(
    [
        # DeepSeek (not used in Path B but documented for future use)
        "deepseek/deepseek-v3.2-20251201",
        "deepseek/deepseek-v3.2",
    ]
)


class OpenRouterClient:
    """OpenRouter client for LLM-as-Judge calls."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: int = 60,
        max_retries: int = 3,
    ) -> None:
        if not api_key:
            raise ValueError(
                "OpenRouter API key is required. Set CCOP_OPENROUTER_API_KEY in .env.local."
            )
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        self._max_retries = max_retries

    def call(
        self,
        prompt: str,
        *,
        model: str,
        temperature: float = 0.2,
        seed: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Call a judge model and return the assistant's text response.

        Args:
            prompt: User prompt (full judge rubric prompt including ground truth).
            model: OpenRouter model ID (e.g., "qwen/qwen3-235b-a22b-07-25").
            temperature: Sampling temperature. Default 0.2 per A1 variance-reduction plan.
            seed: Optional seed for byte-level reproducibility on supporting models.
            max_tokens: Optional cap. Falls back to per-model default for known models.

        Returns:
            Assistant's text content.

        Raises:
            JudgeAPIError: When the call fails after all retries.
        """
        return self._retry_call(
            prompt=prompt,
            model=model,
            temperature=temperature,
            seed=seed,
            max_tokens=max_tokens,
        )

    def _retry_call(
        self,
        prompt: str,
        model: str,
        temperature: float,
        seed: Optional[int],
        max_tokens: Optional[int],
    ) -> str:
        # tenacity inner function so instance-level max_retries binds at call time
        decorator = retry(
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception_type(
                (APITimeoutError, RateLimitError, APIError)
            ),
            reraise=True,
        )

        @decorator
        def _do_call() -> str:
            return self._single_call(prompt, model, temperature, seed, max_tokens)

        try:
            return _do_call()
        except (APITimeoutError, RateLimitError, APIError) as e:
            logger.error(
                "OpenRouter call failed after %d retries: model=%s err=%s",
                self._max_retries, model, str(e),
            )
            raise JudgeAPIError(
                f"OpenRouter call failed after {self._max_retries} retries "
                f"for model={model}: {type(e).__name__}: {e}"
            ) from e

    def _single_call(
        self,
        prompt: str,
        model: str,
        temperature: float,
        seed: Optional[int],
        max_tokens: Optional[int],
    ) -> str:
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": self._apply_prefix(model, prompt)}],
            "temperature": temperature,
        }

        if seed is not None:
            kwargs["seed"] = seed

        resolved_max_tokens = max_tokens or _DEFAULT_MAX_TOKENS.get(model)
        if resolved_max_tokens is not None:
            kwargs["max_tokens"] = resolved_max_tokens

        if model in _JSON_FORMAT_MODELS:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)

        if not response.choices:
            raise JudgeAPIError(
                f"OpenRouter returned no choices for model={model}"
            )
        content = response.choices[0].message.content
        if not content:
            raise JudgeAPIError(
                f"OpenRouter returned empty content for model={model}"
            )
        return content

    @staticmethod
    def _apply_prefix(model: str, prompt: str) -> str:
        """Prepend per-model instruction prefix when needed."""
        if model in _ENGLISH_ONLY_PREFIX_MODELS:
            return (
                "Respond in English only. Output only valid JSON per the rubric schema.\n\n"
                + prompt
            )
        return prompt
