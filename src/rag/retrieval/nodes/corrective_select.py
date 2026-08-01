"""CRAG essential-first selection node (graphont-agentic corrective mode).

Selects the final corrective context from the merged pool using essential-first
ordering:
  1. Take ALL score==2 (essential) candidates
  2. Fill remaining slots to topk with score==1 (related) candidates
  3. Apply diversity preference: avoid duplicate section-siblings (clauses from
     the same parent section, e.g., 1.2.1 and 1.2.2) when possible

Writes selected candidates to state.trace["corrective_selected"] for the final
pack/generation step.
"""
import logging
from typing import List

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def _extract_section_prefix(citation_id: str) -> str:
    """Extract section prefix for diversity check (e.g., '1.2' from '1.2.1')."""
    if not citation_id:
        return ""
    # Format: "Doc::1.2.1" or "Doc::AnnexC" or "Doc::1.2.1(a)"
    parts = citation_id.split("::")
    if len(parts) < 2:
        return ""
    clause = parts[-1]
    # Strip parenthetical suffix like (a)
    clause = clause.split("(")[0]
    # Take first two levels: 1.2.1 -> 1.2
    levels = clause.split(".")
    return ".".join(levels[:2]) if len(levels) >= 2 else clause


def corrective_select(state: GraphState) -> GraphState:
    """Essential-first selection from the merged corrective pool.
    
    Expects state.trace["corrective_merged_pool"] from corrective_merge.
    
    Writes selected candidates to state.trace["corrective_selected"] (these
    will be packed into the final context by the pack node).
    """
    settings = get_settings()
    trace = state.setdefault("retrieval_trace", {})
    
    merged_pool = trace.get("corrective_merged_pool", [])
    top_k = settings.graphont_agentic_top_k
    
    if not merged_pool:
        trace["corrective_selected"] = []
        logger.warning("corrective_select: merged pool is empty, no selection")
        return state
    
    # Partition by eval_score
    essential = [c for c in merged_pool if c.get("eval_score") == 2]
    related = [c for c in merged_pool if c.get("eval_score") == 1]
    
    # Essential-first: take ALL essential (score==2) candidates
    selected: List[dict] = list(essential)
    
    # Fill remaining slots with related (score==1) candidates
    remaining_slots = top_k - len(selected)
    if remaining_slots > 0 and related:
        # Apply diversity preference: avoid duplicate section-siblings
        selected_sections = {_extract_section_prefix(c.get("citation_id", "")) for c in selected}
        
        # First pass: prefer related candidates from NEW sections
        diverse = []
        for candidate in related:
            section = _extract_section_prefix(candidate.get("citation_id", ""))
            if section not in selected_sections:
                diverse.append(candidate)
                selected_sections.add(section)
                if len(diverse) >= remaining_slots:
                    break
        
        # Second pass: if not enough diverse candidates, take remaining related
        if len(diverse) < remaining_slots:
            for candidate in related:
                if candidate not in diverse:
                    diverse.append(candidate)
                    if len(diverse) >= remaining_slots:
                        break
        
        selected.extend(diverse[:remaining_slots])
    
    trace["corrective_selected"] = selected
    trace["corrective_select_n_essential"] = len(essential)
    trace["corrective_select_n_related_available"] = len(related)
    trace["corrective_select_n_selected"] = len(selected)
    trace["corrective_select_top_k"] = top_k
    
    # Update trace["candidates"] with the corrective-selected pool so pack_contexts
    # packs the corrective results (not the original Round-1 survivors)
    trace["candidates"] = selected
    
    # Increment retry count so the next corrective check knows we've done one Round-2
    state["corrective_retry_count"] = state.get("corrective_retry_count", 0) + 1
    
    logger.info(
        "corrective_select: essential=%d related_available=%d selected=%d (top_k=%d, retry_count=%d)",
        len(essential), len(related), len(selected), top_k, state["corrective_retry_count"]
    )
    
    return state


__all__ = ["corrective_select"]
