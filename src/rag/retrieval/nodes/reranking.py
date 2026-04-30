"""
Reranking Node

Cross-encoder reranking for retrieved documents (Phase 1.3).
Re-scores bi-encoder results and selects top-N for LLM context.
"""

import logging
import threading
from typing import Optional

import numpy as np

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

# Lazy singleton for cross-encoder model (same pattern as EmbeddingService)
_cross_encoder: Optional[object] = None
_cross_encoder_lock = threading.Lock()


def _get_cross_encoder(model_name: str):
    """
    Get or create cross-encoder model (thread-safe lazy initialization).

    Args:
        model_name: HuggingFace model ID (e.g., cross-encoder/ms-marco-MiniLM-L12-v2)

    Returns:
        CrossEncoder model instance
    """
    global _cross_encoder
    if _cross_encoder is None:
        with _cross_encoder_lock:
            if _cross_encoder is None:
                logger.info(f"Loading cross-encoder model: {model_name}")
                from sentence_transformers import CrossEncoder
                _cross_encoder = CrossEncoder(model_name)
                logger.info("Cross-encoder model loaded successfully")
    return _cross_encoder


def rerank_documents(state: GraphState) -> GraphState:
    """
    Rerank retrieved documents using cross-encoder.

    Scores query-document pairs and keeps top-N based on rerank_top_n setting.
    Cross-encoder scores are logits (unbounded, NOT 0-1 normalized).

    Args:
        state: Current graph state with 'documents' and 'rewritten_query'

    Returns:
        Updated state with reranked 'documents' and 'reranker_scores'
    """
    settings = get_settings()
    documents = state.get("documents", [])
    # CE query: prefer HyDE-expanded form if available (per 2026-04-27 diagnostic).
    # bge-reranker-large can't bridge "MFA" → "multi-factor authentication" via attention;
    # the HyDE rewrite already expands acronyms and gives the CE token-level overlap.
    # Fall back to original user query if HyDE not produced.
    rerank_query = state.get("rewritten_query") or state.get("query", "")
    if not rerank_query:
        rerank_query = state.get("query", "")

    logger.info(f"Reranking {len(documents)} documents with cross-encoder...")
    logger.debug(f"CE query (first 120 chars): {rerank_query[:120]}")

    if not documents:
        state["reranker_scores"] = []
        logger.warning("No documents to rerank")
        return state

    # Load cross-encoder model (lazy, thread-safe)
    model = _get_cross_encoder(settings.cross_encoder_model)

    # Build query-document pairs for scoring.
    # Per 2026-04-27 diagnostic: pass AUGMENTED chunk text (page_content) — it provides
    # domain anchors (CCoP 2.0, section refs, related concepts) that give CE attention
    # something to lock onto. Lab Exp #15's "use original_text" finding was based on the
    # v1 contextualization (which had hallucinations); v3 acronyms-only contexts produce
    # cleaner augmented text that materially improves CE discrimination on short queries.
    pairs = [
        (rerank_query, doc.page_content)
        for doc in documents
    ]

    # Score pairs (returns numpy array of logits)
    scores = model.predict(pairs)

    # Convert to Python floats for JSON serialization
    scores_list = [float(s) for s in scores]

    # Attach scores AND ce_rank to document metadata
    for doc, score in zip(documents, scores_list):
        doc.metadata["reranker_score"] = score

    # CE-rank by sorted index
    ce_sorted_idx = sorted(range(len(scores_list)), key=lambda i: -scores_list[i])
    for rank, idx in enumerate(ce_sorted_idx, 1):
        documents[idx].metadata["ce_rank"] = rank

    # Per Exp #28: RRF ensemble of dense rank + cross-encoder rank
    # rrf_score = w_d / (K + r_d) + w_c / (K + r_c)
    K_RRF = 60
    rrf_w_d = float(getattr(settings, "rag_rrf_dense_weight", 1.0))
    rrf_w_c = float(getattr(settings, "rag_rrf_ce_weight", 1.5))
    rrf_scores = []
    for doc in documents:
        r_d = doc.metadata.get("dense_rank", 1)
        r_c = doc.metadata.get("ce_rank", 1)
        rrf = rrf_w_d / (K_RRF + r_d) + rrf_w_c / (K_RRF + r_c)
        doc.metadata["rrf_score"] = rrf
        rrf_scores.append(rrf)
    state["rrf_scores"] = rrf_scores

    # Sort by RRF score (not raw CE score) — combines complementary signals
    scored_docs = sorted(zip(documents, rrf_scores), key=lambda x: -x[1])

    # DEBUG: log top-10 by RRF with components, to verify ranking decisions
    logger.info("RRF ensemble top-10 (citation_id | dense_rank | ce_rank | ce_score | rrf_score):")
    for i, (doc, rrf) in enumerate(scored_docs[:10], 1):
        cid = doc.metadata.get("citation_id", "?")
        dr = doc.metadata.get("dense_rank", "?")
        cr = doc.metadata.get("ce_rank", "?")
        cs = doc.metadata.get("reranker_score", "?")
        cs_s = f"{cs:.4f}" if isinstance(cs, (int, float)) else str(cs)
        logger.info(f"  [{i:2d}] {cid:55s} | dense={dr:3} | ce={cr:3} | ce_score={cs_s} | rrf={rrf:.5f}")

    # Per Exp #16/#33: parent-child auto-merge sibling clauses in top-window
    if getattr(settings, "rag_merge_parent_enabled", False):
        merge_window = int(getattr(settings, "rag_merge_window", 40))
        merge_min = int(getattr(settings, "rag_merge_min_siblings", 2))
        merge_min_score_ratio = float(getattr(settings, "rag_merge_min_score_ratio", 0.5))
        merge_max_members = int(getattr(settings, "rag_merge_max_members", 4))

        def parent_path_of(doc):
            cid = doc.metadata.get("citation_id", "")
            # Strip "CCoP 2.0::" or similar prefix
            for pfx in ("CCoP 2.0::", "Cybersecurity Act 2018::", "CCoP Response to Feedback::",
                        "Auditing Guidelines::", "Risk Assessment Guide::",
                        "Threat Modelling Guide::", "Security By Design::"):
                if cid.startswith(pfx):
                    cid = cid[len(pfx):]
                    break
            # Strip parenthetical sub-letter (e.g. "1.6.1(c)" → "1.6.1")
            if "(" in cid:
                cid = cid.rsplit("(", 1)[0]
            # Drop last dotted segment ("1.6.1" → "1.6")
            parts = cid.split(".")
            if len(parts) > 1:
                return ".".join(parts[:-1])
            return cid

        head = scored_docs[:merge_window]
        tail = scored_docs[merge_window:]

        # Group by parent_path (preserve insertion order)
        parent_groups = {}
        for doc_score in head:
            doc, _ = doc_score
            pk = parent_path_of(doc)
            parent_groups.setdefault(pk, []).append(doc_score)

        merged_docs = []
        seen_parents = set()
        n_merges_fired = 0
        n_members_filtered_low_score = 0
        n_members_filtered_max_cap = 0
        for doc, sc in head:
            pk = parent_path_of(doc)
            if pk in seen_parents:
                continue
            seen_parents.add(pk)
            all_siblings = parent_groups[pk]

            # Relevance gate: only include sibling members whose CE score is at
            # least (anchor_ce_score × ratio). Stops weak siblings being bundled
            # into a slot just because they share a parent. Anchor is the highest-
            # RRF member (siblings[0]).
            anchor_doc_for_gate = all_siblings[0][0]
            anchor_ce_score = float(anchor_doc_for_gate.metadata.get("reranker_score", 0.0))
            score_threshold = anchor_ce_score * merge_min_score_ratio if anchor_ce_score > 0 else 0.0

            gated_siblings = []
            for sib_doc, sib_score in all_siblings:
                sib_ce = float(sib_doc.metadata.get("reranker_score", 0.0))
                # Anchor is always included; gate only applies to non-anchor siblings
                if sib_doc is anchor_doc_for_gate or sib_ce >= score_threshold:
                    gated_siblings.append((sib_doc, sib_score))
                else:
                    n_members_filtered_low_score += 1

            # Hard cap on group size — keep top-N by CE score (highest-relevance members)
            if len(gated_siblings) > merge_max_members:
                gated_siblings.sort(
                    key=lambda ds: -float(ds[0].metadata.get("reranker_score", 0.0))
                )
                n_members_filtered_max_cap += len(gated_siblings) - merge_max_members
                gated_siblings = gated_siblings[:merge_max_members]
                # Re-sort by RRF score so anchor is first (preserve display order)
                gated_siblings.sort(key=lambda ds: -ds[1])

            if len(gated_siblings) >= merge_min:
                # Merge: take first (best-rank) doc as anchor; aggregate metadata
                anchor_doc, anchor_score = gated_siblings[0]
                member_cids = [d.metadata.get("citation_id", "") for d, _ in gated_siblings]
                merged_content_parts = [d.page_content for d, _ in gated_siblings]
                anchor_doc.page_content = "\n\n---\n\n".join(merged_content_parts)
                anchor_doc.metadata["merged_member_citation_ids"] = member_cids
                anchor_doc.metadata["merged_member_count"] = len(gated_siblings)
                merged_docs.append(anchor_doc)
                n_merges_fired += 1
            else:
                merged_docs.append(doc)
        merged_docs.extend(d for d, _ in tail)
        # The state["merged_groups"] field can capture this for downstream LLM/citation logic.
        # Built from the final post-gate groups (not the raw parent_groups) so it reflects
        # what was actually merged.
        state["merged_groups"] = []
        for d in merged_docs:
            members = d.metadata.get("merged_member_citation_ids")
            if members and len(members) > 1:
                pk = parent_path_of(d)
                state["merged_groups"].append({"parent": pk, "members": members})
        scored_for_topn = merged_docs

        # Diagnostic: log parent-child merge activity. Critical for understanding when
        # cardinality-fair retrieval is firing (Exp #16/#33 mechanism).
        if n_merges_fired > 0:
            gate_note = ""
            if n_members_filtered_low_score or n_members_filtered_max_cap:
                gate_parts = []
                if n_members_filtered_low_score:
                    gate_parts.append(f"{n_members_filtered_low_score} below score-ratio {merge_min_score_ratio:.2f}")
                if n_members_filtered_max_cap:
                    gate_parts.append(f"{n_members_filtered_max_cap} over max-members {merge_max_members}")
                gate_note = f"; gate dropped {', '.join(gate_parts)}"
            logger.info(
                f"Parent-child merge: {n_merges_fired} group(s) merged "
                f"(window={merge_window}, min_siblings={merge_min}{gate_note})"
            )
            for grp in state["merged_groups"]:
                members_str = ", ".join(grp["members"])
                logger.info(f"  → parent='{grp['parent']}' members=[{members_str}] (n={len(grp['members'])})")
        else:
            # Also useful to know when merging found nothing — suggests siblings missed top-window
            n_singleton_parents = sum(1 for sibs in parent_groups.values() if len(sibs) == 1)
            n_potential_pairs = sum(1 for sibs in parent_groups.values() if len(sibs) >= 2)
            if n_potential_pairs == 0:
                logger.info(
                    f"Parent-child merge: 0 groups merged ({len(parent_groups)} unique parents in top-{merge_window}, "
                    f"none had ≥{merge_min} siblings — likely embedder/reranker missed sibling candidates)"
                )
            else:
                logger.info(
                    f"Parent-child merge: 0 groups merged but {n_potential_pairs} parent(s) had ≥{merge_min} siblings — investigate"
                )
    else:
        scored_for_topn = [d for d, _ in scored_docs]

    # Keep top-N
    top_n = settings.rerank_top_n
    top_docs = scored_for_topn[:top_n]

    # Log reranking results
    if scores_list:
        score_min = min(scores_list)
        score_max = max(scores_list)
        score_mean = np.mean(scores_list)
        logger.info(
            f"Reranking complete: {len(documents)} -> {len(top_docs)} docs "
            f"(score range: [{score_min:.3f}, {score_max:.3f}], mean={score_mean:.3f})"
        )

        # Log which citation_ids made it to top-N
        top_citation_ids = [doc.metadata.get("citation_id", "unknown") for doc in top_docs]
        logger.info(f"Top-{top_n} citation_ids: {top_citation_ids}")
    else:
        logger.warning("No scores generated during reranking")

    # Update state
    state["documents"] = top_docs  # Reranked top-N documents
    state["reranker_scores"] = scores_list  # ALL scores for logging

    return state
