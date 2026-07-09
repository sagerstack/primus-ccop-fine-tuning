"""
Unit tests for the function-type routing node (Phase 10, plan 10-09, D-12).

Mirrors the mocked-LLM-call testing shape query_analysis.py's HyDE node would
use: patches `openai.OpenAI` so no live OpenRouter call is made. Covers:
- Correct classification for scope/control/definition fixtures.
- Graceful no-op (never raises) on LLM error or missing API key.
- Gated: only classifies (and only calls the LLM) for mode=="graphrag-ontology".
- Defensive validation: an unrecognized LLM label degrades to "" (no boost),
  never passed through un-validated to the Cypher-bound parameter (T-10-09-01).
"""

from unittest.mock import MagicMock, patch

import pytest

from rag.retrieval.nodes.function_type_routing import (
    VALID_FUNCTION_TYPES,
    classify_function_type,
)


def _settings(**overrides):
    settings = MagicMock()
    settings.openrouter_api_key = "test-key"
    settings.openrouter_base_url = "https://openrouter.ai/api/v1"
    settings.ontology_discovery_model = "openai/gpt-4o-mini"
    for key, value in overrides.items():
        setattr(settings, key, value)
    return settings


def _mock_openai_response(label: str):
    resp = MagicMock()
    resp.choices = [MagicMock(message=MagicMock(content=label))]
    return resp


class TestClassifyFunctionTypeGating:
    """Node only classifies (and only calls the LLM) for graphrag-ontology mode."""

    @patch("rag.retrieval.nodes.function_type_routing.get_settings")
    def test_non_ontology_mode_is_a_no_op(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        with patch("openai.OpenAI") as mock_openai_cls:
            state = classify_function_type({"query": "Is X in scope?", "mode": "hybrid"})

        mock_openai_cls.assert_not_called()
        assert state["function_type"] == ""

    @patch("rag.retrieval.nodes.function_type_routing.get_settings")
    def test_graphrag_mode_phase9_is_also_a_no_op(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        with patch("openai.OpenAI") as mock_openai_cls:
            state = classify_function_type({"query": "Is X in scope?", "mode": "graphrag"})

        mock_openai_cls.assert_not_called()
        assert state["function_type"] == ""

    @patch("rag.retrieval.nodes.function_type_routing.get_settings")
    def test_missing_mode_key_defaults_to_no_op(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        with patch("openai.OpenAI") as mock_openai_cls:
            state = classify_function_type({"query": "q"})

        mock_openai_cls.assert_not_called()
        assert state["function_type"] == ""

    @patch("rag.retrieval.nodes.function_type_routing.get_settings")
    def test_graphrag_ontology_mode_invokes_the_classifier(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response("ScopeClause")

        with patch("openai.OpenAI", return_value=mock_client) as mock_openai_cls:
            state = classify_function_type(
                {"query": "Is X in scope?", "mode": "graphrag-ontology"}
            )

        mock_openai_cls.assert_called_once()
        assert state["function_type"] == "ScopeClause"


class TestClassifyFunctionTypeFixtures:
    """Correct classification for scope/control/definition question fixtures."""

    @pytest.mark.parametrize(
        "question,label",
        [
            ("Is a system connected-but-not-designated in mandatory scope?", "ScopeClause"),
            ("What must be implemented for privileged access control?", "ControlClause"),
            ("What does 'essential service' mean under the CCoP?", "DefinitionClause"),
        ],
    )
    @patch("rag.retrieval.nodes.function_type_routing.get_settings")
    def test_classifies_expected_function_type(self, mock_get_settings, question, label):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(label)

        with patch("openai.OpenAI", return_value=mock_client):
            state = classify_function_type({"query": question, "mode": "graphrag-ontology"})

        assert state["function_type"] == label
        assert state["function_type"] in VALID_FUNCTION_TYPES

    @patch("rag.retrieval.nodes.function_type_routing.get_settings")
    def test_classifier_output_is_stripped_of_quotes_and_whitespace(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '  "ControlClause".  \n'
        )

        with patch("openai.OpenAI", return_value=mock_client):
            state = classify_function_type({"query": "q", "mode": "graphrag-ontology"})

        assert state["function_type"] == "ControlClause"


class TestClassifyFunctionTypeGracefulDegradation:
    """Never fails the whole request — mirrors HyDE's try/except-log-return pattern."""

    @patch("rag.retrieval.nodes.function_type_routing.get_settings")
    def test_llm_error_degrades_to_empty_function_type(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("OpenRouter timeout")

        with patch("openai.OpenAI", return_value=mock_client):
            state = classify_function_type({"query": "q", "mode": "graphrag-ontology"})

        assert state["function_type"] == ""

    @patch("rag.retrieval.nodes.function_type_routing.get_settings")
    def test_missing_api_key_degrades_to_empty_function_type(self, mock_get_settings):
        mock_get_settings.return_value = _settings(openrouter_api_key=None)

        with patch("openai.OpenAI") as mock_openai_cls:
            state = classify_function_type({"query": "q", "mode": "graphrag-ontology"})

        mock_openai_cls.assert_not_called()
        assert state["function_type"] == ""

    @patch("rag.retrieval.nodes.function_type_routing.get_settings")
    def test_unrecognized_label_degrades_to_empty_function_type(self, mock_get_settings):
        """T-10-09-01: classifier output constrained to the 3-value enum before binding."""
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            "SomeHallucinatedLabel"
        )

        with patch("openai.OpenAI", return_value=mock_client):
            state = classify_function_type({"query": "q", "mode": "graphrag-ontology"})

        assert state["function_type"] == ""


class TestClassifyFunctionTypeStateShape:
    def test_original_query_and_mode_untouched(self):
        with patch(
            "rag.retrieval.nodes.function_type_routing.get_settings",
            return_value=_settings(openrouter_api_key=None),
        ):
            state = classify_function_type(
                {"query": "Is X in scope?", "mode": "graphrag-ontology"}
            )

        assert state["query"] == "Is X in scope?"
        assert state["mode"] == "graphrag-ontology"
        assert "function_type" in state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
