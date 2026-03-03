"""
RAG Response Node

Returns retrieved chunks as the response without LLM generation.
Used in rag-only mode for evaluating retrieval quality.
"""

import logging

from rag.retrieval.context import assemble_llm_context
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def rag_only_response(state: GraphState) -> GraphState:
    """
    Format retrieved chunks as the response without LLM generation.

    Args:
        state: Current graph state with 'filtered_documents'

    Returns:
        Updated state with formatted retrieval results
    """
    filtered_docs = state.get("filtered_documents", [])

    logger.info(f"RAG-only response: {len(filtered_docs)} documents")

    if not filtered_docs:
        state["generation"] = "No relevant documents found."
        state["is_rag_augmented"] = False
        state["citations"] = []
        state["llm_context"] = ""
        return state

    # Format each chunk with metadata for human-readable display
    parts = []
    for i, doc in enumerate(filtered_docs, 1):
        source = doc.metadata.get("document_source", "Unknown")
        section = doc.metadata.get("section", "")
        clause = doc.metadata.get("clause", "")
        citation_id = doc.metadata.get("citation_id", "")
        score = doc.metadata.get("similarity_score", 0.0)

        header = f"**[{i}] {source}**"
        if section:
            header += f" | {section}"
        if clause:
            header += f" | Clause {clause}"
        header += f" | score={score:.3f}"

        parts.append(f"{header}\n\n{doc.page_content}")

    retrieval_output = "\n\n---\n\n".join(parts)

    # Assemble the LLM context string (what the generation node would receive)
    llm_context = assemble_llm_context(filtered_docs)
    state["llm_context"] = llm_context

    # Combine both views in the generation output
    state["generation"] = (
        f"{retrieval_output}\n\n"
        f"{'=' * 60}\n"
        f"LLM Context (as sent to generation):\n"
        f"{'=' * 60}\n\n"
        f"{llm_context}"
    )
    state["is_rag_augmented"] = True
    state["citations"] = []

    return state
