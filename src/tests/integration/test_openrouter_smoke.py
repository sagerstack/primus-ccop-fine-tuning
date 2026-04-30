"""
OpenRouter smoke test.

Real API call against OpenRouter for both primary (Qwen3-235B) and secondary
(GPT-4o-mini) models. Validates:
  - Auth works
  - Model IDs resolve
  - Responses parse cleanly
  - Per-model mitigations don't break the call (Qwen JSON mode, GPT max_tokens)

Cost: ~$0.002 per full run (2 real calls against OpenRouter).

Marked @pytest.mark.integration — skipped by default. Run explicitly with:
    poetry run pytest tests/integration/test_openrouter_smoke.py -m integration -v

Skipped when CCOP_OPENROUTER_API_KEY is not set.
"""

from __future__ import annotations

import json
import os

import pytest

from infrastructure.config.settings import get_settings
from infrastructure.external.openrouter_client import OpenRouterClient


pytestmark = pytest.mark.integration


# Minimal prompt — we don't care about actual evaluation quality here,
# only that the round-trip works and parsing succeeds.
_SMOKE_PROMPT = (
    'Respond with exactly this JSON: {"ok": true, "echo": "smoke"}. '
    "Do not add any other text."
)


def _skip_if_no_key():
    settings = get_settings()
    if not settings.openrouter_api_key:
        pytest.skip(
            "CCOP_OPENROUTER_API_KEY not set — skipping OpenRouter smoke test"
        )
    return settings


def test_openrouter_primary_judge_responds():
    """Qwen3 primary judge: auth + JSON mode mitigation + parse."""
    settings = _skip_if_no_key()
    client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=settings.judge_timeout,
        max_retries=1,
    )

    raw = client.call(
        _SMOKE_PROMPT,
        model=settings.judge_primary_model,
        temperature=0.0,
        seed=42,
    )

    assert isinstance(raw, str)
    assert len(raw) > 0
    # Since Qwen gets response_format=json_object forced, output should parse as JSON
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)


def test_openrouter_secondary_judge_responds():
    """GPT-4o-mini secondary: auth + max_tokens cap + parse."""
    settings = _skip_if_no_key()
    client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=settings.judge_timeout,
        max_retries=1,
    )

    raw = client.call(
        _SMOKE_PROMPT,
        model=settings.judge_secondary_model,
        temperature=0.0,
        seed=42,
    )

    assert isinstance(raw, str)
    assert len(raw) > 0
    # GPT-4o-mini without forced JSON mode — should still return parseable JSON
    # for this prompt. Extract between first { and last } defensively.
    start = raw.find("{")
    end = raw.rfind("}")
    assert start >= 0 and end > start, f"no JSON object in response: {raw!r}"
    parsed = json.loads(raw[start : end + 1])
    assert isinstance(parsed, dict)
