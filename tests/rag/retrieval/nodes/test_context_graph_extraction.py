"""
Unit tests for the Context Graph extraction node (Phase 11, plan 11-06 Task
1, D-10).

Mirrors the mocked-LLM-call testing shape of
`tests/rag/retrieval/nodes/test_function_type_routing.py`: patches
`openai.OpenAI` so no live OpenRouter call is made. Covers:
- Gated: only extracts (and only calls the LLM) for mode=="graph-compliance".
- Triple extraction + entity-type validation for graph-compliance mode.
- Graceful no-op (never raises) on LLM error, missing API key, or malformed
  JSON — degrades to an empty triple list.
- Per-query-text caching (D-14): identical scenario text is extracted once.
"""

from unittest.mock import MagicMock, patch

import pytest

from rag.retrieval.nodes.context_graph_extraction import (
    _extraction_cache,
    extract_context_graph,
)


@pytest.fixture(autouse=True)
def _clear_extraction_cache():
    _extraction_cache.clear()
    yield
    _extraction_cache.clear()


def _settings(**overrides):
    settings = MagicMock()
    settings.openrouter_api_key = "test-key"
    settings.openrouter_base_url = "https://openrouter.ai/api/v1"
    settings.ontology_discovery_model = "openai/gpt-4o-mini"
    for key, value in overrides.items():
        setattr(settings, key, value)
    return settings


def _mock_openai_response(content: str):
    resp = MagicMock()
    resp.choices = [MagicMock(message=MagicMock(content=content))]
    return resp


_TRIPLES_JSON = (
    '[{"subject": "Hospital administration system", "subject_type": "system", '
    '"predicate": "shares network with", "object": "enterprise network", '
    '"object_type": "system"}]'
)


class TestExtractContextGraphGating:
    """Node only extracts (and only calls the LLM) for graph-compliance mode."""

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_non_graph_compliance_mode_is_a_no_op(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        with patch("openai.OpenAI") as mock_openai_cls:
            state = extract_context_graph({"query": "Is X in scope?", "mode": "hybrid"})

        mock_openai_cls.assert_not_called()
        assert state["context_graph_triples"] == []

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_graphrag_ontology_mode_is_also_a_no_op(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        with patch("openai.OpenAI") as mock_openai_cls:
            state = extract_context_graph({"query": "Is X in scope?", "mode": "graphrag-ontology"})

        mock_openai_cls.assert_not_called()
        assert state["context_graph_triples"] == []

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_missing_mode_key_defaults_to_no_op(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        with patch("openai.OpenAI") as mock_openai_cls:
            state = extract_context_graph({"query": "q"})

        mock_openai_cls.assert_not_called()
        assert state["context_graph_triples"] == []

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_graph_compliance_mode_invokes_extraction(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(_TRIPLES_JSON)

        with patch("openai.OpenAI", return_value=mock_client) as mock_openai_cls:
            state = extract_context_graph(
                {"query": "Does the hospital admin system fall in scope?", "mode": "graph-compliance"}
            )

        mock_openai_cls.assert_called_once()
        assert len(state["context_graph_triples"]) == 1
        triple = state["context_graph_triples"][0]
        assert triple["subject"] == "Hospital administration system"
        assert triple["subject_type"] == "system"
        assert triple["object_type"] == "system"


class TestExtractContextGraphParsing:
    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_triples_missing_required_keys_are_dropped(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '[{"subject": "X"}]'
        )

        with patch("openai.OpenAI", return_value=mock_client):
            state = extract_context_graph({"query": "q", "mode": "graph-compliance"})

        assert state["context_graph_triples"] == []

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_invalid_entity_type_is_dropped(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '[{"subject": "X", "subject_type": "widget", "predicate": "p", '
            '"object": "Y", "object_type": "system"}]'
        )

        with patch("openai.OpenAI", return_value=mock_client):
            state = extract_context_graph({"query": "q", "mode": "graph-compliance"})

        assert state["context_graph_triples"] == []

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_non_array_json_degrades_to_empty(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '{"subject": "X"}'
        )

        with patch("openai.OpenAI", return_value=mock_client):
            state = extract_context_graph({"query": "q", "mode": "graph-compliance"})

        assert state["context_graph_triples"] == []

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_empty_llm_output_degrades_to_empty(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response("[]")

        with patch("openai.OpenAI", return_value=mock_client):
            state = extract_context_graph({"query": "q", "mode": "graph-compliance"})

        assert state["context_graph_triples"] == []


class TestExtractContextGraphGracefulDegradation:
    """Never fails the whole request — mirrors HyDE's try/except-log-return pattern."""

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_llm_error_degrades_to_empty_triples(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("OpenRouter timeout")

        with patch("openai.OpenAI", return_value=mock_client):
            state = extract_context_graph({"query": "q", "mode": "graph-compliance"})

        assert state["context_graph_triples"] == []
        assert "error" not in state

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_missing_api_key_degrades_to_empty_triples(self, mock_get_settings):
        mock_get_settings.return_value = _settings(openrouter_api_key=None)

        with patch("openai.OpenAI") as mock_openai_cls:
            state = extract_context_graph({"query": "q", "mode": "graph-compliance"})

        mock_openai_cls.assert_not_called()
        assert state["context_graph_triples"] == []

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_malformed_json_degrades_to_empty_triples(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            "not json at all {{"
        )

        with patch("openai.OpenAI", return_value=mock_client):
            state = extract_context_graph({"query": "q", "mode": "graph-compliance"})

        assert state["context_graph_triples"] == []


class TestExtractContextGraphCaching:
    """Per-query-text caching (D-14): identical scenario text extracted once."""

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_repeated_identical_query_hits_cache(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(_TRIPLES_JSON)

        with patch("openai.OpenAI", return_value=mock_client) as mock_openai_cls:
            extract_context_graph({"query": "same scenario", "mode": "graph-compliance"})
            extract_context_graph({"query": "same scenario", "mode": "graph-compliance"})

        mock_openai_cls.assert_called_once()

    @patch("rag.retrieval.nodes.context_graph_extraction.get_settings")
    def test_different_queries_each_call_the_llm(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(_TRIPLES_JSON)

        with patch("openai.OpenAI", return_value=mock_client) as mock_openai_cls:
            extract_context_graph({"query": "scenario A", "mode": "graph-compliance"})
            extract_context_graph({"query": "scenario B", "mode": "graph-compliance"})

        assert mock_openai_cls.call_count == 2


class TestExtractContextGraphStateShape:
    def test_original_query_and_mode_untouched(self):
        with patch(
            "rag.retrieval.nodes.context_graph_extraction.get_settings",
            return_value=_settings(openrouter_api_key=None),
        ):
            state = extract_context_graph(
                {"query": "Is X in scope?", "mode": "graph-compliance"}
            )

        assert state["query"] == "Is X in scope?"
        assert state["mode"] == "graph-compliance"
        assert "context_graph_triples" in state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
