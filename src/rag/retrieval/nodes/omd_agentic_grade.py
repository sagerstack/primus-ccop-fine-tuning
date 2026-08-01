"""Aggregate Correctness Grader for graphont-agentic retrieval (CRAG Slice 1).

Decides if Round-1 retrieval is Correct / Incorrect / Ambiguous / Empty based
on the per-clause RetrievalEvaluator scores, and recommends a corrective
action. Observational only in Slice 1 — the result is written to
``state.trace["agentic_assessment"]`` but does NOT alter graphont-agentic
behavior (no branching, no Round-2 trigger).
"""
from typing import List


def aggregate_correctness_grade(candidates: list) -> dict:
    """Aggregate per-clause eval_scores into Correct/Incorrect/Ambiguous + action.

    Inputs:
        candidates: list of candidate dicts, each expected to carry an
            ``eval_score`` field (None | 0 | 1 | 2). The grader is tolerant of
            candidates missing the field (treated as None / eval failure).

    Returns:
        dict with keys: grade, action, essential_count, related_count,
        irrelevant_count, failed_count, reasoning.
    """
    scores = [c.get("eval_score") for c in candidates]
    essential = sum(1 for s in scores if s == 2)
    related = sum(1 for s in scores if s == 1)
    irrelevant = sum(1 for s in scores if s == 0)
    failed = sum(1 for s in scores if s is None)

    if not candidates:
        return {
            "grade": "empty",
            "action": "none",
            "essential_count": 0,
            "related_count": 0,
            "irrelevant_count": 0,
            "failed_count": 0,
            "reasoning": "No retrieval candidates",
        }

    if essential > 0:
        return {
            "grade": "correct",
            "action": "refine",
            "essential_count": essential,
            "related_count": related,
            "irrelevant_count": irrelevant,
            "failed_count": failed,
            "reasoning": f"{essential} essential clause(s) retrieved",
        }

    # Conservative "incorrect" verdict: claim "incorrect" only when EVERY
    # score is 0 (no Nones, no related, no essential). Any None (eval
    # failure) means we lack full signal — fall through to "ambiguous"
    # rather than claim a strong verdict from incomplete data. None scores
    # do NOT count as 0 (per the failed_scores_treated_conservatively test).
    if scores and all(s == 0 for s in scores):
        return {
            "grade": "incorrect",
            "action": "replace",
            "essential_count": 0,
            "related_count": 0,
            "irrelevant_count": irrelevant,
            "failed_count": failed,
            "reasoning": "All scored clauses irrelevant",
        }

    # Otherwise: mixed related / failed / irrelevant, or all failed.
    return {
        "grade": "ambiguous",
        "action": "supplement",
        "essential_count": 0,
        "related_count": related,
        "irrelevant_count": irrelevant,
        "failed_count": failed,
        "reasoning": (
            f"Mixed: {related} related, {irrelevant} irrelevant, "
            f"{failed} eval failures"
        ),
    }


__all__ = ["aggregate_correctness_grade"]
