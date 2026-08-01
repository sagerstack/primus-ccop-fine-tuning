"""CRAG corrective merge node (graphont-agentic corrective mode).

Merges Round-1 and Round-2 candidate pools based on the agentic_assessment
action:
  - Incorrect (action="replace"): discard all Round-1, keep only Round-2
  - Ambiguous (action="supplement"): retain Round-1 score≥1 clauses, merge with
    Round-2, deduplicate by citation_id (keep highest eval_score on collision)
  - Correct (action="refine"): keep Round-1 only (no Round-2 needed — refine
    means the initial retrieval was good enough)

Writes the merged pool to state.trace["corrective_merged_pool"] for the
essential-first select node.
"""
import logging
from typing import List

from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def corrective_merge(state: GraphState) -> GraphState:
    """Merge Round-1 and Round-2 pools per the agentic_assessment action.
    
    Expects:
      - state.trace["agentic_assessment"]["action"] (replace/supplement/refine)
      - state.trace["round1_survivors"] (full pre-cap Round-1 survivors after filter)
      - state.trace["corrective_round2_pool"]["candidates"] (Round-2 pool with eval scores)
    
    Writes merged pool to state.trace["corrective_merged_pool"] with full
    candidate dicts (including eval_score, eval_reason, citation_id, text, etc.).
    """
    trace = state.setdefault("retrieval_trace", {})
    
    # Read the action from agentic_assessment
    action = trace.get("agentic_assessment", {}).get("action", "none")
    
    # Round-1 relevant survivors: the FULL pre-cap set that passed the min_score
    # filter (omd_agentic_context_assembly persists this as "round1_survivors").
    # Supplement (Ambiguous) merges against all relevant Round-1 clauses, not the
    # top_k-capped selection. Fall back to the capped "candidates" for resilience
    # if an older/other path did not persist round1_survivors.
    round1_pool = trace.get("round1_survivors", trace.get("candidates", []))
    
    # Round-2 pool (with eval scores attached by corrective_round2_eval)
    round2_pool = trace.get("corrective_round2_pool", {}).get("candidates", [])
    
    merged: List[dict] = []
    
    if action == "replace":
        # INCORRECT: discard all Round-1, keep only Round-2
        merged = round2_pool
        logger.info(
            "corrective_merge: action=replace (Incorrect) → discarded %d Round-1, kept %d Round-2",
            len(round1_pool), len(round2_pool)
        )
    
    elif action == "supplement":
        # AMBIGUOUS: retain Round-1 score≥1, merge with Round-2, deduplicate
        round1_keep = [c for c in round1_pool if (c.get("eval_score") or 0) >= 1]
        
        # Merge: start with Round-1 kept clauses, then add Round-2 clauses not
        # already present (deduplicate by citation_id, keep highest eval_score)
        merged = list(round1_keep)
        seen_ids = {c.get("citation_id") for c in merged}
        
        for r2_candidate in round2_pool:
            cid = r2_candidate.get("citation_id")
            if cid not in seen_ids:
                merged.append(r2_candidate)
                seen_ids.add(cid)
            else:
                # Collision: keep the one with higher eval_score
                existing = next((c for c in merged if c.get("citation_id") == cid), None)
                if existing and (r2_candidate.get("eval_score") or 0) > (existing.get("eval_score") or 0):
                    merged.remove(existing)
                    merged.append(r2_candidate)
        
        logger.info(
            "corrective_merge: action=supplement (Ambiguous) → retained %d Round-1 (score≥1), added %d unique Round-2 (of %d), merged=%d",
            len(round1_keep), len(merged) - len(round1_keep), len(round2_pool), len(merged)
        )
    
    elif action == "refine":
        # CORRECT: keep Round-1 only (no Round-2 needed)
        merged = round1_pool
        logger.info(
            "corrective_merge: action=refine (Correct) → kept %d Round-1, no Round-2",
            len(round1_pool)
        )
    
    else:
        # Unknown action or "none" (e.g., empty pool) → fallback to Round-1 only
        merged = round1_pool
        logger.warning(
            "corrective_merge: action=%s (unknown/none) → fallback to Round-1 only",
            action
        )
    
    trace["corrective_merged_pool"] = merged
    trace["corrective_merge_action"] = action
    trace["corrective_merge_n_round1"] = len(round1_pool)
    trace["corrective_merge_n_round2"] = len(round2_pool)
    trace["corrective_merge_n_merged"] = len(merged)
    
    return state


__all__ = ["corrective_merge"]
