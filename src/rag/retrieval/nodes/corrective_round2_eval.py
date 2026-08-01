"""CRAG Round-2 evaluator node (graphont-agentic corrective mode).

Re-runs the RetrievalEvaluator on Round-2 candidates, scoring them against the
ORIGINAL question (not the rewritten query). This ensures answer-support is
judged by the user's real intent, not the retrieval rewrite.

Writes eval scores to state.trace["corrective_round2_eval_scores"] and attaches
eval_score + eval_reason to each Round-2 candidate for merge/select.
"""
import logging

from infrastructure.config.settings import get_settings
from rag.retrieval.evaluation.retrieval_evaluator import RetrievalEvaluator
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def corrective_round2_eval(state: GraphState) -> GraphState:
    """Evaluate Round-2 candidates for answer-support against the ORIGINAL question.
    
    Expects state.trace["corrective_round2_pool"]["candidates"] from the
    corrective_round2_retrieve node. Scores each candidate 0/1/2 (irrelevant/
    related/essential) for the ORIGINAL question.
    
    Attaches eval_score + eval_reason to each Round-2 candidate and writes
    the full scores list to state.trace["corrective_round2_eval_scores"].
    """
    settings = get_settings()
    trace = state.setdefault("retrieval_trace", {})
    
    # Read Round-2 candidates
    round2_pool = trace.get("corrective_round2_pool", {})
    candidates = round2_pool.get("candidates", [])
    
    if not candidates:
        logger.warning("corrective_round2_eval: no Round-2 candidates to evaluate")
        trace["corrective_round2_eval_scores"] = []
        return state
    
    # IMPORTANT: evaluate against the ORIGINAL question, not the rewritten query
    original_question = (
        trace.get("corrective_rewrite", {}).get("original_question")
        or state.get("query", "")
    )
    
    # Run the evaluator on all Round-2 candidates
    evaluator = RetrievalEvaluator(settings)
    eval_results = evaluator.evaluate_pool(original_question, candidates)
    
    # Attach eval_score and eval_reason to each candidate (same pattern as Round-1)
    evaluator_scores = []
    for candidate, eval_result in zip(candidates, eval_results):
        candidate["eval_score"] = eval_result["score"]
        candidate["eval_reason"] = eval_result["reason"]
        evaluator_scores.append({
            "citation_id": candidate.get("citation_id"),
            "eval_score": eval_result["score"],
            "eval_reason": eval_result["reason"],
        })
    
    trace["corrective_round2_eval_scores"] = evaluator_scores
    trace["corrective_round2_n_eval_failures"] = sum(
        1 for c in candidates if c.get("eval_score") is None
    )
    
    logger.info(
        "corrective_round2_eval: evaluated %d candidates against ORIGINAL question (failures=%d)",
        len(candidates), trace["corrective_round2_n_eval_failures"]
    )
    
    return state


__all__ = ["corrective_round2_eval"]
