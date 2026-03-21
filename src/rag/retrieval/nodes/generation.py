"""
Generation Node

RAG-augmented response generation with Llama-Primus-Reasoning.
Embeds citation anchors in response for later resolution.
"""

import logging
import re

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from infrastructure.config.settings import get_settings
from rag.citations.formatter import format_response_with_citations
from rag.citations.resolver import build_citations_from_state
from rag.retrieval.context import assemble_llm_context
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

# Pattern to strip Llama chain-of-thought tokens
_THINKING_TOKEN_PATTERN = re.compile(
    r"<\|python_tag\|>.*?<\|reserved_special_token_1\|>\s*",
    re.DOTALL,
)


def strip_thinking_tokens(text: str) -> str:
    """Strip Llama chain-of-thought tokens from model output."""
    cleaned = _THINKING_TOKEN_PATTERN.sub("", text)
    # Also strip any remaining special tokens individually
    cleaned = re.sub(r"<\|[a-z_]+\|>", "", cleaned)
    return cleaned.strip()


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
    context = assemble_llm_context(filtered_docs)

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
                """You are a CCoP 2.0 compliance expert advising Critical Information Infrastructure Owners (CIIOs) in Singapore. Answer the question using the retrieved context below.

Question: {query}

Retrieved Context:
{context}

RESPONSE STRUCTURE:
1. CLAUSE CITATIONS: Reference specific CCoP clauses (e.g., Clause 5.2.1, Section 3.4) from the retrieved context. Use citation anchors in the format <c>Document::Clause</c> after each claim.
2. CONDITIONAL ANALYSIS: Where applicable, analyze conditions, scenarios, or trade-offs relevant to the compliance question. Use "if-then" reasoning for different situations the CIIO may face.
3. ACTIONABLE STEPS: Where applicable, provide concrete implementation steps the CIIO should take to achieve compliance.

RULES:
- Only use citation anchors that appear in the retrieved context above
- If context is insufficient for a complete answer, state this explicitly
- Not all questions require all three elements — factual questions may only need clause citations, while advisory questions benefit from all three""",
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
        raw_generation = strip_thinking_tokens(raw_generation)

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

        # Fallback: if LLM failed to cite correctly, build citations from
        # filtered documents so sources are always traceable
        if not resolved_citations and filtered_docs:
            seen = set()
            for doc in filtered_docs:
                source = doc.metadata.get("document_source", "Unknown")
                clause = doc.metadata.get("clause", "")
                section = doc.metadata.get("section", "")
                ref_key = f"{source}::{clause or section}"
                if ref_key in seen:
                    continue
                seen.add(ref_key)
                resolved_citations.append({
                    "document": source,
                    "section": section,
                    "clause": clause,
                    "citation_id": doc.metadata.get("citation_id", ""),
                    "document_type": doc.metadata.get("document_type", "standard"),
                })

            source_refs = ["\n\nSources:"]
            for citation in resolved_citations:
                ref = f"- {citation['document']}"
                if citation["clause"]:
                    ref += f", Clause {citation['clause']}"
                elif citation["section"]:
                    ref += f", Section {citation['section']}"
                source_refs.append(ref)
            formatted_generation = formatted_generation.strip() + "\n".join(source_refs)

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
