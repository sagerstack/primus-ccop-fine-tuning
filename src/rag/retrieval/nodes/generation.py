"""
Generation Node

RAG-augmented response generation with Llama-Primus-Reasoning.
Embeds citation anchors in response for later resolution.
"""

import logging

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from infrastructure.config.settings import get_settings
from rag.citations.formatter import format_response_with_citations
from rag.citations.resolver import build_citations_from_state
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def generate_response(state: GraphState) -> GraphState:
    """
    Generate RAG-augmented response using filtered documents.

    Uses Llama-Primus-Reasoning via ChatOllama with retrieved context.
    Constructs prompt with citation anchors for each source document.

    Response contains raw citation anchors <c>citation_id</c> that will
    be resolved and formatted by Plan 01-04 citation resolution module.

    Args:
        state: Current graph state with 'query' and 'filtered_documents'

    Returns:
        Updated state with 'generation', 'is_rag_augmented', and 'citations'
    """
    settings = get_settings()
    query = state.get("query", "")
    filtered_docs = state.get("filtered_documents", [])

    logger.info(
        f"Generating RAG-augmented response with {len(filtered_docs)} documents..."
    )

    # Format retrieved context with citation anchors
    context_parts = []
    for doc in filtered_docs:
        citation_id = doc.metadata.get("citation_id", "unknown")
        document_source = doc.metadata.get("document_source", "unknown")
        section = doc.metadata.get("section", "")

        # Format: [Source: <c>citation_id</c>] document_text
        context_parts.append(
            f"[Source: {document_source}, {section} <c>{citation_id}</c>]\n{doc.page_content}\n"
        )

    context = "\n---\n".join(context_parts)

    # Log the assembled context being sent to the model
    logger.info(f"Context assembled for generation ({len(context)} chars, {len(filtered_docs)} sources):")
    for i, doc in enumerate(filtered_docs, 1):
        cid = doc.metadata.get("citation_id", "unknown")
        src = doc.metadata.get("document_source", "unknown")
        sec = doc.metadata.get("section", "")
        sim = doc.metadata.get("similarity_score", 0.0)
        logger.info(f"  [{i}] {src} | {sec} | {cid} | similarity={sim:.3f} | {len(doc.page_content)} chars")

    # Generation prompt with citation instructions
    generation_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a CCoP 2.0 compliance expert. Answer using the retrieved context below.

IMPORTANT CITATION RULES:
- The context contains citation anchors like <c>CCoP-2.0.5.5.2.1</c>
- When you reference information from a source, include its citation anchor in your response
- Place citation anchors after the relevant sentence or claim
- DO NOT make up citations - only use anchors provided in the context
- If context is insufficient, say so explicitly

Retrieved Context:
{context}""",
            ),
            ("human", "{query}"),
        ]
    )

    # Initialize LLM
    llm = ChatOllama(
        model=settings.model_name,
        temperature=settings.default_temperature,
        base_url=settings.ollama_host,
    )

    try:
        # Log complete LLM input
        formatted_messages = generation_prompt.format_messages(context=context, query=query)
        logger.info("=" * 60)
        logger.info("LLM INPUT (generation)")
        logger.info("=" * 60)
        for msg in formatted_messages:
            logger.info(f"[{msg.type}]\n{msg.content}")
        logger.info("=" * 60)

        # Generate response
        chain = generation_prompt | llm
        response = chain.invoke({"context": context, "query": query})

        raw_generation = (
            response.content if hasattr(response, "content") else str(response)
        )

        # Post-process: resolve citation anchors to metadata
        # Store raw generation for debugging
        state["raw_generation"] = raw_generation

        # Build temporary state for citation resolution
        temp_state = {
            "generation": raw_generation,
            "filtered_documents": filtered_docs,
        }

        # Resolve raw <c>citation_id</c> anchors to citation metadata
        resolved_citations = build_citations_from_state(temp_state)

        # Format final response with end-of-response references
        formatted_generation = format_response_with_citations(
            raw_generation, resolved_citations
        )

        # Update state with formatted output
        state["generation"] = formatted_generation
        state["is_rag_augmented"] = True
        state["citations"] = resolved_citations

        logger.info(
            f"Generated response: {len(formatted_generation)} chars, "
            f"{len(resolved_citations)} citations resolved"
        )

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        state["generation"] = (
            f"Error generating response: {str(e)}. Query: {query}"
        )
        state["is_rag_augmented"] = False
        state["citations"] = []
        state["error"] = f"Generation error: {str(e)}"

    return state
