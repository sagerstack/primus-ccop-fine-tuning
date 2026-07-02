"""
Graph Retrieval Node (Phase 9 — `--mode graphrag`)

LangGraph node that swaps the vector `retrieval` node for entity-anchored
Neo4j graph retrieval (D-06: retriever only). It fetches contexts from the
`IGraphRetrievalProvider` (selected in the DI container, D-11) and populates
`documents` + `filtered_documents` in hybrid's Document shape (D-11) so the
downstream grading and the UNCHANGED primus `generate` node run exactly as in
hybrid mode. This node bypasses the cross-encoder reranker (graph retrieval
already returns a bounded, entity-anchored neighborhood), going straight to
`grade_documents` → `generate`.
"""

import logging

from infrastructure.config.container import get_container
from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def graph_retrieve_documents(state: GraphState) -> GraphState:
    """
    Retrieve entity-anchored graph contexts for `--mode graphrag`.

    Uses the graph_retrieval_provider from the DI container (Neo4j adapter when
    `neo4j_uri` is set). Populates `documents` and `filtered_documents` directly
    (the reranking node is bypassed for the graph path), attaches
    `similarity_score`/`dense_rank` for downstream parity, and sets
    `retrieval_succeeded` based on whether any contexts came back.

    Args:
        state: Current graph state (uses 'rewritten_query' or 'query').

    Returns:
        Updated state with graph-retrieved documents + incremented
        'retrieval_attempts'.
    """
    settings = get_settings()
    query = state.get("rewritten_query", "") or state.get("query", "")
    retrieval_attempts = state.get("retrieval_attempts", 0)
    top_k = settings.rag_retrieval_top_k

    logger.info(
        f"Graph retrieval (attempt {retrieval_attempts + 1}, k={top_k}): {query[:80]}..."
    )

    try:
        container = get_container()
        provider = container.graph_retrieval_provider()

        if provider is None:
            logger.error(
                "No graph retrieval provider configured. Set CCOP_NEO4J_URI in .env.local "
                "and build the graph with `ccop-eval graph build`."
            )
            state["documents"] = []
            state["filtered_documents"] = []
            state["retrieval_succeeded"] = False
            state["retrieval_attempts"] = retrieval_attempts + 1
            state["error"] = "No graph retrieval provider configured"
            return state

        documents = provider.retrieve(query=query, top_k=top_k)

        # Attach rank + ensure a similarity_score exists for downstream parity
        # with the vector path (retrieval.py sets similarity_score + dense_rank).
        for rank, doc in enumerate(documents, 1):
            doc.metadata.setdefault("similarity_score", doc.metadata.get("similarity_score", 0.0))
            doc.metadata["dense_rank"] = rank

        # Graph path bypasses reranking, so populate BOTH documents and
        # filtered_documents (the generate node reads filtered_documents).
        state["documents"] = documents
        state["filtered_documents"] = documents
        state["retrieval_succeeded"] = bool(documents)
        state["retrieval_attempts"] = retrieval_attempts + 1

        if documents:
            scores = [d.metadata.get("similarity_score", 0.0) for d in documents]
            logger.info(
                f"Graph retrieval returned {len(documents)} documents. "
                f"Scores: min={min(scores):.3f}, max={max(scores):.3f}, "
                f"avg={sum(scores)/len(scores):.3f}"
            )
            for i, doc in enumerate(documents, 1):
                cid = doc.metadata.get("citation_id", "unknown")
                src = doc.metadata.get("document_source", "unknown")
                snippet = doc.page_content[:120].replace("\n", " ")
                logger.info(f"  [{i}] {src} | {cid} | {snippet}...")
        else:
            logger.warning("Graph retrieval returned no documents")

    except Exception as e:
        logger.error(f"Graph retrieval failed: {e}")
        state["documents"] = []
        state["filtered_documents"] = []
        state["retrieval_succeeded"] = False
        state["retrieval_attempts"] = retrieval_attempts + 1
        state["error"] = f"Graph retrieval error: {str(e)}"

    return state


__all__: list[str] = ["graph_retrieve_documents"]
