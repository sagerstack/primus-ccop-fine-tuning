"""
Tests for LLMJudgeService OpenRouter integration path.

Mocked unit tests for the refactored judge service:
- __init__ accepts DI'd OpenRouterClient
- __init__ reads primary/secondary/temperature from settings by default
- _call_judge routes primary vs secondary to correct model IDs
- _call_both_judges invokes both
- Missing API key raises ValueError
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from domain.services.llm_judge_service import LLMJudgeService


class _FakeClient:
    """In-memory fake OpenRouter client capturing calls."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.responses: dict[str, str] = {}

    def call(self, prompt, *, model, temperature, seed=None, max_tokens=None):
        self.calls.append({
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "seed": seed,
            "max_tokens": max_tokens,
        })
        return self.responses.get(model, f"fake-response-from-{model}")


class TestJudgeServiceConstruction:
    def test_uses_injected_client(self):
        fake = _FakeClient()
        svc = LLMJudgeService(
            model_name="test/primary",
            rubric_path="/tmp/nonexistent.md",
            openrouter_client=fake,
            secondary_model="test/secondary",
            temperature=0.2,
        )
        assert svc._judge_client is fake
        assert svc._model == "test/primary"
        assert svc._secondary_model == "test/secondary"
        assert svc._temperature == 0.2

    def test_defaults_from_settings_when_not_overridden(self, monkeypatch):
        # Clear settings singleton so get_settings reloads
        import infrastructure.config.settings as settings_module
        monkeypatch.setattr(settings_module, "_settings", None)
        monkeypatch.setenv("CCOP_OPENROUTER_API_KEY", "sk-or-v1-fake")
        monkeypatch.setenv(
            "CCOP_JUDGE_PRIMARY_MODEL", "defaulted/primary"
        )
        monkeypatch.setenv(
            "CCOP_JUDGE_SECONDARY_MODEL", "defaulted/secondary"
        )
        monkeypatch.setenv("CCOP_JUDGE_TEMPERATURE", "0.1")

        fake = _FakeClient()
        svc = LLMJudgeService(
            rubric_path="/tmp/nonexistent.md",
            openrouter_client=fake,
        )
        assert svc._model == "defaulted/primary"
        assert svc._secondary_model == "defaulted/secondary"
        assert svc._temperature == 0.1
        # Reset for other tests
        monkeypatch.setattr(settings_module, "_settings", None)

    def test_missing_api_key_raises_when_no_client_provided(self, monkeypatch):
        import infrastructure.config.settings as settings_module
        monkeypatch.setattr(settings_module, "_settings", None)
        monkeypatch.delenv("CCOP_OPENROUTER_API_KEY", raising=False)
        # Pydantic reads from .env files too; override with empty string
        monkeypatch.setenv("CCOP_OPENROUTER_API_KEY", "")

        with pytest.raises(ValueError, match="OpenRouter API key missing"):
            LLMJudgeService(
                rubric_path="/tmp/nonexistent.md",
                model_name="test/primary",
            )
        monkeypatch.setattr(settings_module, "_settings", None)


class TestCallJudgeRouting:
    def _mk_svc(self) -> tuple[LLMJudgeService, _FakeClient]:
        fake = _FakeClient()
        svc = LLMJudgeService(
            model_name="primary/model-id",
            rubric_path="/tmp/nonexistent.md",
            openrouter_client=fake,
            secondary_model="secondary/model-id",
            temperature=0.2,
        )
        return svc, fake

    def test_call_judge_primary_routes_to_primary_model(self):
        svc, fake = self._mk_svc()
        svc._call_judge("some prompt", role="primary")
        assert len(fake.calls) == 1
        assert fake.calls[0]["model"] == "primary/model-id"
        assert fake.calls[0]["prompt"] == "some prompt"
        assert fake.calls[0]["temperature"] == 0.2

    def test_call_judge_secondary_routes_to_secondary_model(self):
        svc, fake = self._mk_svc()
        svc._call_judge("some prompt", role="secondary")
        assert len(fake.calls) == 1
        assert fake.calls[0]["model"] == "secondary/model-id"

    def test_call_judge_defaults_to_primary(self):
        svc, fake = self._mk_svc()
        svc._call_judge("p")
        assert fake.calls[0]["model"] == "primary/model-id"

    def test_call_judge_invalid_role_raises(self):
        svc, _ = self._mk_svc()
        with pytest.raises(ValueError, match="Unknown judge role"):
            svc._call_judge("p", role="tertiary")

    def test_call_judge_forwards_seed(self):
        svc, fake = self._mk_svc()
        svc._call_judge("p", role="primary", seed=42)
        assert fake.calls[0]["seed"] == 42

    def test_call_judge_returns_client_response(self):
        svc, fake = self._mk_svc()
        fake.responses["primary/model-id"] = "custom response text"
        result = svc._call_judge("p")
        assert result == "custom response text"


class TestCallBothJudges:
    def _mk_svc(self) -> tuple[LLMJudgeService, _FakeClient]:
        fake = _FakeClient()
        svc = LLMJudgeService(
            model_name="primary/model-id",
            rubric_path="/tmp/nonexistent.md",
            openrouter_client=fake,
            secondary_model="secondary/model-id",
            temperature=0.2,
        )
        return svc, fake

    def test_call_both_judges_invokes_both(self):
        svc, fake = self._mk_svc()
        primary, secondary = svc._call_both_judges("prompt text")
        assert len(fake.calls) == 2
        assert fake.calls[0]["model"] == "primary/model-id"
        assert fake.calls[1]["model"] == "secondary/model-id"
        assert primary == "fake-response-from-primary/model-id"
        assert secondary == "fake-response-from-secondary/model-id"

    def test_call_both_judges_forwards_seed_to_both(self):
        svc, fake = self._mk_svc()
        svc._call_both_judges("p", seed=99)
        assert fake.calls[0]["seed"] == 99
        assert fake.calls[1]["seed"] == 99

    def test_call_both_judges_same_prompt_and_temperature(self):
        svc, fake = self._mk_svc()
        svc._call_both_judges("same prompt")
        assert fake.calls[0]["prompt"] == "same prompt"
        assert fake.calls[1]["prompt"] == "same prompt"
        assert fake.calls[0]["temperature"] == 0.2
        assert fake.calls[1]["temperature"] == 0.2
