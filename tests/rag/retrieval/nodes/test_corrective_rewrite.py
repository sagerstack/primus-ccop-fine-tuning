"""Unit tests for the corrective query rewrite node (CRAG Slice 2)."""

from unittest.mock import MagicMock, patch

import pytest

from rag.retrieval.nodes.corrective_rewrite import corrective_rewrite


def _state(question: str) -> dict:
    return {"query": question}


def test_rewrite_success_with_valid_neutral_output(monkeypatch):
    """LLM returns valid neutral JSON → rewrite succeeds, written to trace."""
    mock_client = MagicMock()
    mock_client.call.return_value = '{"keyphrases": ["digital boundary", "CII"], "search_query": "digital boundary; CII"}'
    
    with patch("rag.retrieval.nodes.corrective_rewrite.OpenRouterClient", return_value=mock_client):
        state = _state("Does CCoP apply to the admin network?")
        result = corrective_rewrite(state)
    
    trace = result["retrieval_trace"]["corrective_rewrite"]
    assert trace["rewritten_query"] == "digital boundary; CII"
    assert trace["keyphrases"] == ["digital boundary", "CII"]
    assert trace["source"] in ("llm", "cache")  # Accept both (cache from prior runs)
    assert "error" not in trace


def test_rewrite_strips_markdown_fences(monkeypatch):
    """LLM returns JSON wrapped in ```json fences → fences stripped, parse succeeds."""
    mock_client = MagicMock()
    mock_client.call.return_value = '```json\n{"keyphrases": ["test"], "search_query": "test"}\n```'
    
    with patch("rag.retrieval.nodes.corrective_rewrite.OpenRouterClient", return_value=mock_client):
        state = _state("test question")
        result = corrective_rewrite(state)
    
    trace = result["retrieval_trace"]["corrective_rewrite"]
    assert trace["rewritten_query"] == "test"
    assert "error" not in trace


def test_neutrality_violation_rejects_output(monkeypatch):
    """LLM output contains verdict token ("must comply") → rejected, fallback to None."""
    mock_client = MagicMock()
    mock_client.call.return_value = '{"keyphrases": ["must comply"], "search_query": "must comply with CCoP"}'
    
    with patch("rag.retrieval.nodes.corrective_rewrite.OpenRouterClient", return_value=mock_client):
        state = _state("question for neutrality violation test unique")
        result = corrective_rewrite(state)
    
    trace = result["retrieval_trace"]["corrective_rewrite"]
    assert trace["rewritten_query"] is None
    assert "neutrality_violation" in trace
    assert trace["neutrality_violation"] == "must comply"


def test_neutrality_check_case_insensitive(monkeypatch):
    """Neutrality check is case-insensitive ("MUST COMPLY" also rejected)."""
    mock_client = MagicMock()
    mock_client.call.return_value = '{"keyphrases": ["System"], "search_query": "System MUST COMPLY"}'
    
    with patch("rag.retrieval.nodes.corrective_rewrite.OpenRouterClient", return_value=mock_client):
        state = _state("question for case insensitive test unique")
        result = corrective_rewrite(state)
    
    trace = result["retrieval_trace"]["corrective_rewrite"]
    assert trace["rewritten_query"] is None
    assert "neutrality_violation" in trace


def test_llm_call_failure_fallback(monkeypatch):
    """LLM call raises exception → fallback to None, error logged in trace."""
    mock_client = MagicMock()
    mock_client.call.side_effect = Exception("API timeout")
    
    with patch("rag.retrieval.nodes.corrective_rewrite.OpenRouterClient", return_value=mock_client):
        state = _state("question for llm failure test unique")
        result = corrective_rewrite(state)
    
    trace = result["retrieval_trace"]["corrective_rewrite"]
    assert trace["rewritten_query"] is None
    assert "error" in trace
    assert "API timeout" in trace["error"]


def test_json_parse_failure_fallback(monkeypatch):
    """LLM returns malformed JSON → parse fails, fallback to None."""
    mock_client = MagicMock()
    mock_client.call.return_value = "not valid JSON at all"
    
    with patch("rag.retrieval.nodes.corrective_rewrite.OpenRouterClient", return_value=mock_client):
        state = _state("question for parse failure test unique")
        result = corrective_rewrite(state)
    
    trace = result["retrieval_trace"]["corrective_rewrite"]
    assert trace["rewritten_query"] is None
    assert "error" in trace
    assert "Parse failed" in trace["error"]


def test_empty_question_no_op(monkeypatch):
    """Empty question → no LLM call, no trace entry (no-op)."""
    state = {"query": ""}
    result = corrective_rewrite(state)
    # Should not have created a trace entry
    assert "retrieval_trace" not in result or "corrective_rewrite" not in result.get("retrieval_trace", {})


def test_missing_question_no_op(monkeypatch):
    """Missing 'query' key → no LLM call, no trace entry (no-op)."""
    state = {}
    result = corrective_rewrite(state)
    assert "retrieval_trace" not in result or "corrective_rewrite" not in result.get("retrieval_trace", {})
