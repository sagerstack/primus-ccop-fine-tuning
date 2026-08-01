"""Agentic OMD-GraphRAG context assembly with LLM-based relevance filtering.

Retrieves k candidates via omd_retrieval, scores each with RetrievalEvaluator on
answer-support (0=IRRELEVANT/1=RELATED/2=ESSENTIAL), filters by min_score, then
packs survivors via omd_pack. Fail-open (keeps eval_score=None). Empty-guard (if
all filtered out, keeps highest-scoring candidate). Audit logged + persisted.
"""
import logging
from typing import List

from infrastructure.config.settings import get_settings
from rag.graph.ontology_v2 import omd_retrieval
from rag.retrieval.evaluation.retrieval_evaluator import RetrievalEvaluator
from rag.retrieval.nodes.omd_agentic_grade import aggregate_correctness_grade
from rag.retrieval.nodes.omd_pack import cap_primary_candidates, omd_pack
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def omd_agentic_context_assembly(state: GraphState) -> GraphState:
    """Retrieve, LLM-filter by answer-support, and pack OMD-GraphRAG context."""
    # CRITICAL: Create retrieval_trace FIRST (before anything that could error)
    # so downstream nodes (pack_contexts, routing) can safely assume it exists.
    trace = state.setdefault("retrieval_trace", {})
    
    settings = get_settings()
    
    # 1. Read question (same as omd_retrieve)
    question = state.get("query", "") or ""
    
    # 2. Retrieve candidates (direct call with agentic pool_k)
    pool_k = settings.graphont_agentic_pool_k
    out = omd_retrieval.retrieve(question, k=pool_k, dense_query=state.get("hyde_clause"))
    candidates = out.get("results", [])
    
    # 3. Build retrieval_trace (mirror omd_retrieve structure EXACTLY)
    trace["candidates"] = candidates
    trace["definitions"] = out.get("definitions", [])
    trace["ce_confidence"] = out.get("ce_confidence")
    trace["ranked_by"] = out.get("ranked_by")
    trace["d_cand"] = out.get("d_cand", 0)
    trace["query_concepts"] = out.get("query_concepts", [])
    trace["per_channel"] = {
        "ch1": [r.get("ch1") for r in candidates],
        "bm25": [r.get("bm25") for r in candidates],
        "dense": [r.get("dense") for r in candidates],
        "rrf": [r.get("rrf") for r in candidates],
    }
    
    # 4. Evaluate all candidates with RetrievalEvaluator
    evaluator = RetrievalEvaluator(settings)
    eval_results = evaluator.evaluate_pool(question, candidates)
    
    # Attach eval_score and eval_reason to each candidate
    evaluator_scores = []
    for candidate, eval_result in zip(candidates, eval_results):
        candidate["eval_score"] = eval_result["score"]
        candidate["eval_reason"] = eval_result["reason"]
        evaluator_scores.append({
            "citation_id": candidate.get("citation_id"),
            "eval_score": eval_result["score"],
            "eval_reason": eval_result["reason"],
        })
    
    # 5. Filter by min_score (FAIL-OPEN: keep if eval_score is None)
    min_score = settings.graphont_agentic_filter_min_score
    survivors: List = []
    for candidate in candidates:
        eval_score = candidate.get("eval_score")
        if eval_score is None:
            # FAIL-OPEN: keep if evaluator failed
            survivors.append(candidate)
        elif eval_score >= min_score:
            survivors.append(candidate)
        # else: drop (eval_score < min_score)
    
    # 6. EMPTY-GUARD: if all filtered out, keep highest-scoring one
    if not survivors and candidates:
        # Treat None as -1 for selection
        def _eval_score_or_neg1(cand):
            es = cand.get("eval_score")
            return es if es is not None else -1
        
        # Find max eval_score (treating None as -1)
        max_score = max(_eval_score_or_neg1(c) for c in candidates)
        # Keep first candidate with that score (tie-break by original order)
        for candidate in candidates:
            if _eval_score_or_neg1(candidate) == max_score:
                survivors = [candidate]
                break

    selected = cap_primary_candidates(survivors, settings.graphont_agentic_top_k)
    
    # 7. AUDIT: log and persist evaluation metadata
    n_retrieved = len(candidates)
    n_survived = len(survivors)
    n_eval_failures = sum(1 for c in candidates if c.get("eval_score") is None)
    
    if n_eval_failures > 0:
        logger.warning(
            "Retrieval evaluator failures: %d/%d candidates (fail-open: kept)",
            n_eval_failures, n_retrieved
        )
    
    trace["evaluator_scores"] = evaluator_scores
    trace["n_retrieved"] = n_retrieved
    trace["n_survived"] = n_survived
    # Persist the FULL pre-cap survivor list (passed min_score filter, before
    # cap_primary_candidates) so the corrective merge can supplement against all
    # relevant Round-1 clauses, not just the top_k-capped selection. Non-corrective
    # pack still uses trace["candidates"] (the capped selection) below.
    trace["round1_survivors"] = survivors
    trace["n_eval_failures"] = n_eval_failures
    trace["filter_min_score"] = min_score
    trace["top_k"] = settings.graphont_agentic_top_k
    trace["n_context_selected"] = len(selected)
    trace["n_primary_selected"] = sum(1 for c in selected if c.get("kind") != "definition")
    trace["n_auxiliary_selected"] = sum(1 for c in selected if c.get("kind") == "definition")
    
    logger.info(
        "Agentic filtering: retrieved=%d survived=%d (min_score=%d, eval_failures=%d)",
        n_retrieved, n_survived, min_score, n_eval_failures
    )

    # 7b. CRAG Slice 1: aggregate correctness assessment (observational only).
    # Computed from the full Round-1 retrieval pool (candidates), not the
    # filtered survivors — Round-1 = the initial retrieval result.
    agentic_assessment = aggregate_correctness_grade(candidates)
    trace["agentic_assessment"] = agentic_assessment
    logger.info(
        "Agentic assessment: grade=%s action=%s (essential=%d related=%d "
        "irrelevant=%d failed=%d)",
        agentic_assessment["grade"],
        agentic_assessment["action"],
        agentic_assessment["essential_count"],
        agentic_assessment["related_count"],
        agentic_assessment["irrelevant_count"],
        agentic_assessment["failed_count"],
    )

    # 8. Update trace with selected survivors (pack happens later in the graph).
    # For corrective mode: pack is deferred until after corrective pipeline.
    # For non-corrective mode: graph routes directly to pack node.
    trace["candidates"] = selected
    
    return state


__all__ = ["omd_agentic_context_assembly"]
