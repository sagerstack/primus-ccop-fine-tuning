"""
Generation Node

RAG-augmented response generation with Llama-Primus-Reasoning.
Embeds citation anchors in response for later resolution.
"""

import logging
import re
from time import perf_counter

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
    """Strip Llama chain-of-thought tokens from model output.

    Catches both the wrapped CoT block (python_tag ... reserved_special_token_1)
    and any standalone special token markers. The character class includes
    digits to handle numbered variants like `<|reserved_special_token_0|>`,
    `<|reserved_special_token_2|>`, etc. — without digits, those numbered
    tokens leaked into the user-facing response.
    """
    cleaned = _THINKING_TOKEN_PATTERN.sub("", text)
    cleaned = re.sub(r"<\|[a-z_0-9]+\|>", "", cleaned)
    return cleaned.strip()


def generate_response(state: GraphState) -> GraphState:
    """
    Generate RAG-augmented response using filtered documents.

    Uses Llama-Primus-Reasoning via ChatOllama with the retrieved passages.
    Constructs the prompt with plain-language source headers per passage.

    The model is instructed to end its response with a `**Sources:**`
    markdown footer listing the clauses it relied on. The resolver parses
    that footer into structured citation metadata after generation.

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

    # Generation prompt: persona + glossary + source-material framing in system
    # message; question + relevant passages in user message. Revised 2026-04-27
    # to remove the "Retrieved Context" framing that the model was parroting at
    # the start of every response. Strategy: strip the seed phrases rather than
    # add forbidden-phrase rules.
    generation_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a regulatory compliance advisor specializing in Singapore's Cybersecurity Code of Practice for Critical Information Infrastructure, Second Edition (CCoP 2.0).

WHAT CCoP 2.0 IS:
CCoP 2.0 is the legally mandated cybersecurity code issued by the Cyber Security Agency of Singapore (CSA) under the Singapore Cybersecurity Act 2018. It applies exclusively to designated Critical Information Infrastructure Owners (CIIOs) operating in Singapore.

GLOSSARY (apply these meanings throughout):
- CCoP / CCoP 2.0: Cybersecurity Code of Practice (Second Edition), Singapore
- CSA: Cyber Security Agency of Singapore (the regulator)
- CIIO: Critical Information Infrastructure Owner (the regulated entity)
- CII: Critical Information Infrastructure (the protected system)
- CIRT: Cyber Incident Response Team
- IT/OT: Information Technology / Operational Technology

SOURCE MATERIAL:
You answer questions using the Singapore regulatory corpus, which consists of seven documents organized into two tiers:

PRIMARY (the main code):
  1. CCoP 2.0

SUPPORTING (related Singapore regulatory documents):
  2. CCoP Response to Feedback
  3. Cybersecurity Act 2018
  4. Guidelines for Auditing Critical Information Infrastructure
  5. Guide to Cyber Threat Modelling
  6. Guide to Conducting Cybersecurity Risk Assessment for CII
  7. Security By Design Framework

Verbatim passages from this corpus are appended to each user message. Prioritize answers grounded in those passages.

GROUNDING DISCIPLINE: Answer strictly from the passages. Never introduce specific values (lengths, character rules, frequencies, thresholds) unless a passage states them. If the code does not specify something, say so plainly and stop — the absence of a requirement is a complete answer. Report deferrals to external standards (NIST/ISO) as deferrals only; do not quote those standards' specifics. Distinguish mandatory requirements from recommendations.

RESPONSE STRUCTURE:
1. LEAD WITH THE ANSWER — Begin your response with the substantive answer. Do not preface with what you're about to do or where the information comes from.
2. CONDITIONAL ANALYSIS — use "if-then" reasoning only where a passage supports it.
3. ACTIONABLE STEPS — when applicable, provide concrete implementation steps grounded in the cited clauses.
4. SOURCES FOOTER — End your response with a `**Sources:**` block listing every source you used, one per line in the format `<document name>: <clause reference>`. Example:

   **Sources:**
   CCoP 2.0: 5.3.1
   Cybersecurity Act 2018: Section 11(7)

   Each clause reference must appear verbatim in the passages above — do not invent sub-letters like (c), (d) that aren't shown.""",
            ),
            (
                "human",
                """Question: {query}

Relevant passages from the regulatory corpus:

{context}""",
            ),
        ]
    )

    # Initialize LLM
    llm_kwargs = {
        "model": settings.model_name,
        "temperature": settings.default_temperature,
        "base_url": settings.ollama_host,
    }
    if settings.generation_seed is not None:
        llm_kwargs["seed"] = settings.generation_seed
    llm = ChatOllama(**llm_kwargs)

    # Build retrieved_contexts_detailed from filtered documents (before LLM call)
    state["retrieved_contexts_detailed"] = [
        {
            "text": doc.page_content,
            "citation_id": doc.metadata.get("citation_id"),
            "section": doc.metadata.get("section"),
            "clause": doc.metadata.get("clause"),
            "document": doc.metadata.get("document_source"),
            "score": doc.metadata.get("similarity_score"),
            "metadata": dict(doc.metadata),
        }
        for doc in filtered_docs
    ]

    _start = perf_counter()
    try:
        # Log complete LLM input
        formatted_messages = generation_prompt.format_messages(context=context, query=query)
        logger.info("=" * 60)
        logger.info("LLM INPUT (generation)")
        logger.info("=" * 60)
        for msg in formatted_messages:
            logger.info(f"[{msg.type}]\n{msg.content}")
        logger.info("=" * 60)

        # Capture system_prompt and user_prompt before invoking the chain
        _system_msg = next((m for m in formatted_messages if m.type == "system"), None)
        _human_msg = next((m for m in formatted_messages if m.type == "human"), None)
        state["system_prompt"] = _system_msg.content if _system_msg else ""
        state["user_prompt"] = _human_msg.content if _human_msg else ""

        # Generate response
        chain = generation_prompt | llm
        response = chain.invoke({"context": context, "query": query})

        state["latency_ms"] = int((perf_counter() - _start) * 1000)

        # Extract token counts from Ollama response metadata
        response_metadata = getattr(response, "response_metadata", {}) or {}
        usage_metadata = getattr(response, "usage_metadata", {}) or {}
        prompt_tokens = response_metadata.get(
            "prompt_eval_count", usage_metadata.get("input_tokens", 0)
        )
        completion_tokens = response_metadata.get(
            "eval_count", usage_metadata.get("output_tokens", 0)
        )
        total_tokens = usage_metadata.get("total_tokens") or (prompt_tokens + completion_tokens)
        state["prompt_tokens"] = prompt_tokens
        state["completion_tokens"] = completion_tokens
        state["total_tokens"] = total_tokens

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

        # Parse the model's <Sources> block into structured citation metadata.
        # Citations referencing clauses not in the retrieved set are dropped
        # (logged warning) so audit metadata reflects only grounded declarations.
        resolved_citations = build_citations_from_state(temp_state)

        # Pass-through formatter: keeps the model's <Sources> block visible in
        # the response body. No auto-built References footer, no fallback
        # synthesizer — structured citations live in state["citations"] only.
        formatted_generation = format_response_with_citations(
            raw_generation, resolved_citations
        )

        state["generation"] = formatted_generation
        state["is_rag_augmented"] = True
        state["citations"] = resolved_citations

        logger.info(
            f"Generated response: {len(formatted_generation)} chars, "
            f"{len(resolved_citations)} citations resolved, "
            f"tokens={total_tokens}, latency={state['latency_ms']}ms"
        )

    except Exception as e:
        state["latency_ms"] = int((perf_counter() - _start) * 1000)
        state["prompt_tokens"] = 0
        state["completion_tokens"] = 0
        state["total_tokens"] = 0
        logger.error(f"Generation failed: {e}")
        state["generation"] = (
            f"Error generating response: {str(e)}. Query: {query}"
        )
        state["is_rag_augmented"] = False
        state["citations"] = []
        state["error"] = f"Generation error: {str(e)}"

    return state
