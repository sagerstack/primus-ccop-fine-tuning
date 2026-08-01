"""Minimal unit tests for CRAG corrective nodes (Slice 3)."""

from rag.retrieval.nodes.corrective_merge import corrective_merge
from rag.retrieval.nodes.corrective_select import corrective_select


def _cand(cid: str, eval_score: int) -> dict:
    return {"citation_id": cid, "eval_score": eval_score, "text": f"text for {cid}"}


def test_corrective_merge_incorrect_replaces():
    """Incorrect action (replace) discards all Round-1, keeps only Round-2."""
    state = {
        "retrieval_trace": {
            "agentic_assessment": {"action": "replace"},
            "candidates": [_cand("r1-1", 1), _cand("r1-2", 2)],  # Round-1 (2 clauses)
            "corrective_round2_pool": {
                "candidates": [_cand("r2-1", 2), _cand("r2-2", 1), _cand("r2-3", 0)]  # Round-2 (3 clauses)
            },
        }
    }
    result = corrective_merge(state)
    merged = result["retrieval_trace"]["corrective_merged_pool"]
    
    assert len(merged) == 3  # Only Round-2
    assert {c["citation_id"] for c in merged} == {"r2-1", "r2-2", "r2-3"}


def test_corrective_merge_ambiguous_supplements():
    """Ambiguous action (supplement) retains Round-1 score>=1, merges with Round-2, deduplicates."""
    state = {
        "retrieval_trace": {
            "agentic_assessment": {"action": "supplement"},
            "candidates": [_cand("c1", 2), _cand("c2", 1), _cand("c3", 0)],  # Round-1 (keep c1, c2; drop c3)
            "corrective_round2_pool": {
                "candidates": [_cand("c1", 1), _cand("c4", 2)]  # Round-2 (c1 collision, c4 new)
            },
        }
    }
    result = corrective_merge(state)
    merged = result["retrieval_trace"]["corrective_merged_pool"]
    
    # Expect: c1 (from R1, score=2 > R2 score=1), c2 (from R1), c4 (from R2)
    assert len(merged) == 3
    ids = {c["citation_id"] for c in merged}
    assert ids == {"c1", "c2", "c4"}
    # c1 should be from Round-1 (score=2), not Round-2 (score=1)
    c1 = next(c for c in merged if c["citation_id"] == "c1")
    assert c1["eval_score"] == 2


def test_corrective_merge_correct_keeps_round1():
    """Correct action (refine) keeps Round-1 only, no Round-2."""
    state = {
        "retrieval_trace": {
            "agentic_assessment": {"action": "refine"},
            "candidates": [_cand("r1-1", 2), _cand("r1-2", 1)],
            "corrective_round2_pool": {
                "candidates": [_cand("r2-1", 2)]
            },
        }
    }
    result = corrective_merge(state)
    merged = result["retrieval_trace"]["corrective_merged_pool"]
    
    assert len(merged) == 2  # Only Round-1
    assert {c["citation_id"] for c in merged} == {"r1-1", "r1-2"}


def test_corrective_select_essential_first():
    """Essential-first selection: takes all score==2, then score==1 to fill top_k."""
    # Mock settings with top_k=3
    from unittest.mock import patch
    mock_settings = type("Settings", (), {"graphont_agentic_top_k": 3})()
    
    state = {
        "retrieval_trace": {
            "corrective_merged_pool": [
                _cand("e1", 2),  # essential
                _cand("r1", 1),  # related
                _cand("r2", 1),  # related
                _cand("e2", 2),  # essential
                _cand("r3", 1),  # related
            ]
        },
        "corrective_retry_count": 0,
    }
    
    with patch("rag.retrieval.nodes.corrective_select.get_settings", return_value=mock_settings):
        result = corrective_select(state)
    
    selected = result["retrieval_trace"]["corrective_selected"]
    # Expect: 2 essential + 1 related (to fill top_k=3)
    assert len(selected) == 3
    essential_count = sum(1 for c in selected if c["eval_score"] == 2)
    assert essential_count == 2
    # Also check trace["candidates"] is updated
    assert result["retrieval_trace"]["candidates"] == selected
    # And retry count incremented
    assert result["corrective_retry_count"] == 1
