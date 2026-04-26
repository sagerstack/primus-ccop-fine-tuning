"""
Retrieval Node

Queries vector store index with configurable top-k.
Retrieves relevant CCoP clauses with metadata and similarity scores.
"""

import logging

from infrastructure.config.container import get_container
from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def retrieve_documents(state: GraphState) -> GraphState:
    """
    Retrieve documents from vector store with similarity scores.

    Uses IVectorStore from DI container to retrieve documents.
    Captures similarity scores in document metadata for downstream filtering.

    Args:
        state: Current graph state with 'rewritten_query' field

    Returns:
        Updated state with 'documents' (including similarity_score in metadata)
        and incremented 'retrieval_attempts'
    """
    settings = get_settings()
    query = state.get("rewritten_query", state.get("query", ""))
    retrieval_attempts = state.get("retrieval_attempts", 0)
    top_k = settings.rag_retrieval_top_k
    retrieval_mode = getattr(settings, "rag_retrieval_mode", "hybrid")

    logger.info(
        f"Retrieving documents (attempt {retrieval_attempts + 1}, k={top_k}, "
        f"mode={retrieval_mode}): {query[:80]}..."
    )

    try:
        # Get vector store from container
        container = get_container()
        vector_store = container.vector_store()

        # If a contextualized collection is configured, use it
        if (
            getattr(settings, "rag_collection_name_contextual", None)
            and getattr(settings, "rag_contextualization_enabled", False)
        ):
            target_collection = settings.rag_collection_name_contextual
            if vector_store is not None and getattr(vector_store, "collection_name", None) != target_collection:
                logger.info(f"Switching collection to: {target_collection}")
                vector_store.collection_name = target_collection

        if vector_store is None:
            logger.error("No vector store configured. Set CCOP_QDRANT_URL or CCOP_DATABRICKS_HOST in .env.local")
            state["documents"] = []
            state["retrieval_attempts"] = retrieval_attempts + 1
            state["error"] = "No vector store configured"
            return state

        # Retrieval mode: hybrid (RRF), dense-only, or sparse-only
        if retrieval_mode == "dense":
            # Bypass adapter's hybrid RRF; use dense vectors directly (per Exp #11)
            from langchain_core.documents import Document
            embed = vector_store.embedding_service
            client = vector_store.client
            collection = vector_store.collection_name
            dv = embed.embed_query(query)
            qres = client.query_points(
                collection_name=collection, query=dv, using="dense", limit=top_k,
                with_payload=True, with_vectors=False,
            )
            results = []
            for p in qres.points:
                payload = p.payload or {}
                doc = Document(page_content=payload.get("text", ""), metadata={**payload, "similarity_score": float(p.score)})
                results.append((doc, float(p.score)))
        else:
            # Hybrid (RRF) — uses adapter
            results = vector_store.similarity_search_with_scores(query=query, k=top_k)

        # Attach similarity score AND dense rank to each document's metadata
        documents = []
        dense_ranks = []
        for rank, (doc, score) in enumerate(results, 1):
            doc.metadata["similarity_score"] = score
            doc.metadata["dense_rank"] = rank
            documents.append(doc)
            dense_ranks.append(rank)
        state["dense_ranks"] = dense_ranks

        state["documents"] = documents
        state["retrieval_attempts"] = retrieval_attempts + 1

        # Log retrieval results
        score_summary = ""
        if documents:
            scores = [d.metadata["similarity_score"] for d in documents]
            score_summary = (
                f" Scores: min={min(scores):.3f}, max={max(scores):.3f}, "
                f"avg={sum(scores)/len(scores):.3f}"
            )

        logger.info(
            f"Retrieved {len(documents)} documents.{score_summary}"
        )

        # Log each retrieved document
        for i, doc in enumerate(documents, 1):
            sim = doc.metadata.get("similarity_score", 0.0)
            cid = doc.metadata.get("citation_id", "unknown")
            src = doc.metadata.get("document_source", "unknown")
            sec = doc.metadata.get("section", "")
            snippet = doc.page_content[:120].replace("\n", " ")
            logger.info(
                f"  [{i}] score={sim:.3f} | {src} | {sec} | {cid} | {snippet}..."
            )

    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        state["documents"] = []
        state["retrieval_attempts"] = retrieval_attempts + 1
        state["error"] = f"Retrieval error: {str(e)}"

    return state
