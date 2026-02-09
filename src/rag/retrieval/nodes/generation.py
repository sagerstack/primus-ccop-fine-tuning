"""
Generation Node

RAG-augmented response generation with Llama-Primus-Reasoning.
Embeds citation anchors in response for later resolution.
"""

import logging

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from infrastructure.config.settings import get_settings
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
        # Generate response
        chain = generation_prompt | llm
        response = chain.invoke({"context": context, "query": query})

        generation_text = (
            response.content if hasattr(response, "content") else str(response)
        )

        state["generation"] = generation_text
        state["is_rag_augmented"] = True

        # Extract initial citations from document metadata
        citations = []
        for doc in filtered_docs:
            citations.append(
                {
                    "citation_id": doc.metadata.get("citation_id", ""),
                    "document_source": doc.metadata.get("document_source", ""),
                    "section": doc.metadata.get("section", ""),
                    "clause": doc.metadata.get("clause", ""),
                    "page": doc.metadata.get("page"),
                }
            )

        state["citations"] = citations

        logger.info(
            f"Generated response: {len(generation_text)} chars, "
            f"{len(citations)} source documents"
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
