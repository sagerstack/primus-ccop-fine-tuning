"""Focused tests for retrieval pool and primary-context top-k controls."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from rag.retrieval.nodes.omd_pack import cap_primary_candidates


def _candidate(cid: str, kind: str = "clause") -> dict:
    return {
        "citation_id": cid,
        "kind": kind,
        "text": cid,
        "definition": cid if kind == "definition" else None,
        "ch1": 1.0,
        "bm25": 1.0,
        "dense": 1.0,
        "rrf": 1.0,
    }


def test_cap_primary_candidates_preserves_definitions_and_order():
    candidates = [
        _candidate("c1"),
        _candidate("d1", "definition"),
        _candidate("c2"),
        _candidate("d2", "definition"),
        _candidate("c3"),
    ]

    selected = cap_primary_candidates(candidates, top_k=2)

    assert [c["citation_id"] for c in selected] == ["c1", "d1", "c2", "d2"]


def test_cap_primary_candidates_larger_cap_returns_all():
    candidates = [_candidate("c1"), _candidate("d1", "definition"), _candidate("c2")]

    assert cap_primary_candidates(candidates, top_k=5) == candidates


def test_cap_primary_candidates_top_one_keeps_all_definitions():
    candidates = [
        _candidate("d1", "definition"),
        _candidate("c1"),
        _candidate("c2"),
        _candidate("d2", "definition"),
    ]

    selected = cap_primary_candidates(candidates, top_k=1)

    assert [c["citation_id"] for c in selected] == ["d1", "c1", "d2"]


def test_plain_omd_uses_pool_depth_and_caps_only_primary(monkeypatch):
    import rag.retrieval.nodes.omd_retrieve as node

    candidate_pool = [_candidate("c1"), _candidate("d1", "definition"), _candidate("c2")]
    retrieve = MagicMock(return_value={
        "results": candidate_pool,
        "definitions": [],
        "ce_confidence": 0.5,
        "ranked_by": "test",
        "d_cand": 3,
        "query_concepts": ["CII"],
    })
    monkeypatch.setattr(node, "get_settings", lambda: SimpleNamespace(graphont_pool_k=3, graphont_top_k=1))
    monkeypatch.setattr(node.omd_retrieval, "retrieve", retrieve)
    state = {"query": "question"}

    node.omd_retrieve(state)

    retrieve.assert_called_once_with("question", k=3, dense_query=None)
    trace = state["retrieval_trace"]
    assert trace["candidate_pool"] == candidate_pool
    assert [c["citation_id"] for c in trace["candidates"]] == ["c1", "d1"]
    assert trace["pool_k"] == 3
    assert trace["top_k"] == 1
    assert trace["n_retrieved"] == 3
    assert trace["n_primary_selected"] == 1
    assert trace["n_auxiliary_selected"] == 1
    assert trace["per_channel"]["rrf"] == [1.0, 1.0, 1.0]


def test_agentic_evaluates_full_pool_then_caps_survivors(monkeypatch):
    import rag.retrieval.nodes.omd_agentic_context_assembly as node

    candidate_pool = [
        _candidate("c1"),
        _candidate("d1", "definition"),
        _candidate("c2"),
        _candidate("c3"),
    ]
    monkeypatch.setattr(node, "get_settings", lambda: SimpleNamespace(
        graphont_agentic_pool_k=4,
        graphont_agentic_top_k=1,
        graphont_agentic_filter_min_score=1,
    ))
    retrieve = MagicMock(return_value={"results": candidate_pool, "definitions": []})
    monkeypatch.setattr(node.omd_retrieval, "retrieve", retrieve)
    evaluator = MagicMock()
    evaluator.evaluate_pool.return_value = [
        {"score": 2, "reason": "keep"},
        {"score": 2, "reason": "keep"},
        {"score": 1, "reason": "keep"},
        {"score": 0, "reason": "drop"},
    ]
    monkeypatch.setattr(node, "RetrievalEvaluator", lambda settings: evaluator)
    pack = MagicMock(side_effect=lambda state: state)
    monkeypatch.setattr(node, "omd_pack", pack)
    state = {"query": "question", "mode": "graphont-agentic"}

    node.omd_agentic_context_assembly(state)

    retrieve.assert_called_once_with("question", k=4, dense_query=None)
    evaluator.evaluate_pool.assert_called_once_with("question", candidate_pool)
    trace = state["retrieval_trace"]
    assert trace["n_retrieved"] == 4
    assert trace["n_survived"] == 3
    assert [c["citation_id"] for c in trace["candidates"]] == ["c1", "d1"]
    assert trace["top_k"] == 1
    assert trace["n_context_selected"] == 2
    assert trace["n_primary_selected"] == 1
    assert trace["n_auxiliary_selected"] == 1
    pack.assert_called_once_with(state)


def test_agentic_does_not_backfill_filtered_candidates(monkeypatch):
    import rag.retrieval.nodes.omd_agentic_context_assembly as node

    candidate_pool = [_candidate("c1"), _candidate("c2"), _candidate("c3")]
    monkeypatch.setattr(node, "get_settings", lambda: SimpleNamespace(
        graphont_agentic_pool_k=3,
        graphont_agentic_top_k=2,
        graphont_agentic_filter_min_score=1,
    ))
    monkeypatch.setattr(node.omd_retrieval, "retrieve", MagicMock(return_value={
        "results": candidate_pool,
        "definitions": [],
    }))
    evaluator = MagicMock()
    evaluator.evaluate_pool.return_value = [
        {"score": 2, "reason": "keep"},
        {"score": 0, "reason": "drop"},
        {"score": 0, "reason": "drop"},
    ]
    monkeypatch.setattr(node, "RetrievalEvaluator", lambda settings: evaluator)
    monkeypatch.setattr(node, "omd_pack", MagicMock(side_effect=lambda state: state))
    state = {"query": "question", "mode": "graphont-agentic"}

    node.omd_agentic_context_assembly(state)

    trace = state["retrieval_trace"]
    assert trace["n_survived"] == 1
    assert trace["n_primary_selected"] == 1
    assert [c["citation_id"] for c in trace["candidates"]] == ["c1"]


def test_query_cli_help_has_pool_and_top_aliases():
    from rag.presentation.cli.query import query_app

    result = CliRunner().invoke(query_app, ["--help"])

    assert result.exit_code == 0
    assert "--poolk" in result.stdout
    assert "--pool-k" in result.stdout
    assert "--topk" in result.stdout
    assert "--top-k" in result.stdout


def test_query_cli_rejects_topk_greater_than_poolk_before_pipeline():
    from rag.presentation.cli.query import query_app

    result = CliRunner().invoke(
        query_app,
        ["question", "--poolk", "5", "--topk", "8"],
    )

    assert result.exit_code == 1
    assert "--topk cannot exceed --poolk" in result.stdout


def test_evaluate_cli_help_has_pool_and_top_aliases():
    from presentation.cli.commands.evaluate import evaluate_app

    result = CliRunner().invoke(evaluate_app, ["run", "--help"])

    assert result.exit_code == 0
    assert "--poolk" in result.stdout
    assert "--pool-k" in result.stdout
    assert "--topk" in result.stdout
    assert "--top-k" in result.stdout


def test_evaluate_cli_rejects_topk_greater_than_poolk_before_context_use():
    from presentation.cli.commands.evaluate import evaluate_app

    result = CliRunner().invoke(
        evaluate_app,
        ["run", "--model", "primus-reasoning", "--poolk", "5", "--topk", "8"],
    )

    assert result.exit_code == 1
    assert "--topk cannot exceed --poolk" in result.stdout
