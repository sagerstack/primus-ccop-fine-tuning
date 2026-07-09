"""
Graph Retrieval Node (Phase 9 — `--mode graphrag`; Phase 10 — `--mode graphrag-ontology`)

LangGraph node that swaps the vector `retrieval` node for graph retrieval
(D-06: retriever only). It fetches contexts from the `IGraphRetrievalProvider`
(selected in the DI container, D-11) and populates `documents` in hybrid's
Document shape (D-11), then flows through the SAME `reranking` →
`grade_documents` → primus `generate` path as hybrid mode.

Mode-aware provider selection (Phase 10, plan 10-02, D-16 additivity): this
node is shared by BOTH `graphrag` (Phase 9 emergent-KG) and `graphrag-ontology`
(Phase 10 ontology-grounded KG). It selects
`container.graph_retrieval_provider_ontology()` when `state["mode"] ==
"graphrag-ontology"`, else `container.graph_retrieval_provider()` (Phase 9,
unchanged). This closes RESEARCH Pitfall 3 — provider selection was not
previously mode-aware.

Wave-6 retrieval parity (2026-07-02): the graph path retrieves a WIDE candidate
pool (`rag_retrieval_top_k`, same as hybrid's pre-rerank count) and routes
through the shared cross-encoder reranker, which funnels to `rerank_top_n`
(=3) — mirroring hybrid's retrieve-wide → rerank → top-3 funnel. This node
therefore does NOT pre-set `filtered_documents` (the reranker + grader own the
final top-N), and it attaches `dense_rank`/`similarity_score` so the reranker's
RRF ensemble (dense_rank ⊕ ce_rank) has the inputs it expects.
"""

import logging

from infrastructure.config.container import get_container
from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def graph_retrieve_documents(state: GraphState) -> GraphState:
    """
    Retrieve graph contexts for `--mode graphrag` or `--mode graphrag-ontology`.

    Mode-aware provider selection (Phase 10, D-16 additivity): picks
    `container.graph_retrieval_provider_ontology()` when `state["mode"] ==
    "graphrag-ontology"`, else `container.graph_retrieval_provider()` (Phase 9,
    unchanged). Populates `documents` (the WIDE candidate pool) and attaches
    `similarity_score`/`dense_rank` so the downstream shared reranker can
    funnel to `rerank_top_n`; `filtered_documents` is set later by the grader,
    NOT here (Wave-6 parity — the reranker owns the final top-N).

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
    mode = state.get("mode", "graphrag")

    logger.info(
        f"Graph retrieval (mode={mode}, attempt {retrieval_attempts + 1}, k={top_k}): {query[:80]}..."
    )

    try:
        container = get_container()
        is_ontology_mode = mode == "graphrag-ontology"
        provider = (
            container.graph_retrieval_provider_ontology()
            if is_ontology_mode
            else container.graph_retrieval_provider()
        )

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

        if is_ontology_mode:
            # D-12 (plan 10-09): thread the classified function-type intent
            # (state["function_type"], set by the function_type_routing node
            # that runs immediately before this one — see
            # rag/retrieval/graph.py) into the ontology provider's boosted
            # Cypher query. This kwarg exists ONLY on
            # Neo4jOntologyGraphRetrievalAdapter.retrieve — the Phase 9
            # branch below is untouched (D-16 additivity), and the shared
            # IGraphRetrievalProvider port's abstract signature is unchanged.
            documents = provider.retrieve(
                query=query, top_k=top_k, function_type=state.get("function_type", "")
            )
        else:
            documents = provider.retrieve(query=query, top_k=top_k)

        # Attach rank + ensure a similarity_score exists for downstream parity
        # with the vector path (retrieval.py sets similarity_score + dense_rank).
        for rank, doc in enumerate(documents, 1):
            doc.metadata.setdefault("similarity_score", doc.metadata.get("similarity_score", 0.0))
            doc.metadata["dense_rank"] = rank

        # Graph path now flows through the shared reranker → grader (Wave-6
        # parity), so populate ONLY `documents` (the wide candidate pool). The
        # reranker funnels to rerank_top_n and the grader sets filtered_documents.
        state["documents"] = documents
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
