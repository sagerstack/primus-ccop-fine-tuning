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
    # ORIGINAL user query for reranker scoring (NOT the HyDE rewrite, per Exp #15)
    rerank_query = state.get("query", "")
    if not rerank_query:
        rerank_query = state.get("rewritten_query", "")

    logger.info(f"Reranking {len(documents)} documents with cross-encoder...")

    if not documents:
        state["reranker_scores"] = []
        logger.warning("No documents to rerank")
        return state

    # Load cross-encoder model (lazy, thread-safe)
    model = _get_cross_encoder(settings.cross_encoder_model)

    # Build query-document pairs for scoring.
    # Per Exp #15: score against ORIGINAL clause text (preserved in metadata.original_text),
    # NOT the augmented page_content. bge-reranker is distracted by breadcrumb prefixes.
    pairs = [
        (
            rerank_query,
            doc.metadata.get("original_text") or doc.page_content,
        )
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

    # Per Exp #16/#33: parent-child auto-merge sibling clauses in top-window
    if getattr(settings, "rag_merge_parent_enabled", False):
        merge_window = int(getattr(settings, "rag_merge_window", 40))
        merge_min = int(getattr(settings, "rag_merge_min_siblings", 2))

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
        for doc, sc in head:
            pk = parent_path_of(doc)
            if pk in seen_parents:
                continue
            seen_parents.add(pk)
            siblings = parent_groups[pk]
            if len(siblings) >= merge_min:
                # Merge: take first (best-rank) doc as anchor; aggregate metadata
                anchor_doc, anchor_score = siblings[0]
                member_cids = [d.metadata.get("citation_id", "") for d, _ in siblings]
                # Combine page contents (separator)
                merged_content_parts = [d.page_content for d, _ in siblings]
                anchor_doc.page_content = "\n\n---\n\n".join(merged_content_parts)
                anchor_doc.metadata["merged_member_citation_ids"] = member_cids
                anchor_doc.metadata["merged_member_count"] = len(siblings)
                merged_docs.append(anchor_doc)
            else:
                merged_docs.append(doc)
        merged_docs.extend(d for d, _ in tail)
        # The state["merged_groups"] field can capture this for downstream LLM/citation logic
        state["merged_groups"] = [
            {"parent": pk, "members": [d.metadata.get("citation_id", "") for d, _ in g]}
            for pk, g in parent_groups.items() if len(g) >= merge_min
        ]
        scored_for_topn = merged_docs
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
