"""Unit tests for the Aggregate Correctness Grader (CRAG Slice 1)."""

from rag.retrieval.nodes.omd_agentic_grade import aggregate_correctness_grade


def _cand(eval_score):
    return {"citation_id": "x", "eval_score": eval_score}


def test_correct_when_any_essential():
    candidates = [_cand(0), _cand(1), _cand(2), _cand(0)]
    result = aggregate_correctness_grade(candidates)
    assert result["grade"] == "correct"
    assert result["action"] == "refine"
    assert result["essential_count"] == 1
    assert result["related_count"] == 1
    assert result["irrelevant_count"] == 2
    assert result["failed_count"] == 0
    assert "1 essential" in result["reasoning"]


def test_incorrect_when_all_irrelevant():
    candidates = [_cand(0), _cand(0), _cand(0)]
    result = aggregate_correctness_grade(candidates)
    assert result["grade"] == "incorrect"
    assert result["action"] == "replace"
    assert result["essential_count"] == 0
    assert result["related_count"] == 0
    assert result["irrelevant_count"] == 3
    assert result["failed_count"] == 0
    assert "All scored clauses irrelevant" in result["reasoning"]


def test_ambiguous_when_mixed():
    candidates = [_cand(1), _cand(0), _cand(1)]
    result = aggregate_correctness_grade(candidates)
    assert result["grade"] == "ambiguous"
    assert result["action"] == "supplement"
    assert result["essential_count"] == 0
    assert result["related_count"] == 2
    assert result["irrelevant_count"] == 1
    assert result["failed_count"] == 0
    assert "Mixed" in result["reasoning"]


def test_empty_when_no_candidates():
    result = aggregate_correctness_grade([])
    assert result["grade"] == "empty"
    assert result["action"] == "none"
    assert result["essential_count"] == 0
    assert result["related_count"] == 0
    assert result["irrelevant_count"] == 0
    assert result["failed_count"] == 0
    assert "No retrieval candidates" in result["reasoning"]


def test_failed_scores_treated_conservatively():
    """None scores must NOT count as 0 (otherwise [None] would be Incorrect).

    With only None scores (no scored clauses), the grader should fall through
    to the ambiguous branch (no essential, no scored-zero), NOT incorrect.
    """
    candidates = [_cand(None), _cand(None)]
    result = aggregate_correctness_grade(candidates)
    assert result["grade"] == "ambiguous"
    assert result["action"] == "supplement"
    assert result["essential_count"] == 0
    assert result["related_count"] == 0
    assert result["irrelevant_count"] == 0
    assert result["failed_count"] == 2

    # Mixed: one None + one 0 -> still ambiguous, NOT incorrect (the None
    # prevents the "all scored are zero" check from firing).
    candidates_mixed = [_cand(None), _cand(0)]
    result_mixed = aggregate_correctness_grade(candidates_mixed)
    assert result_mixed["grade"] == "ambiguous"
    assert result_mixed["action"] == "supplement"
    assert result_mixed["failed_count"] == 1
    assert result_mixed["irrelevant_count"] == 1
