"""
Document Grading Node

Two modes controlled by CCOP_RAG_GRADING_ENABLED:
- Disabled (default): Filter by similarity score threshold (instant)
- Enabled: LLM-as-judge batch grading (slow with local models)
"""

import json
import logging
import re

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def _parse_scores(response_text: str, num_docs: int) -> list[float]:
    """
    Parse scores from LLM batch grading response.

    Tries JSON array first, then falls back to extracting numbers.
    """
    json_match = re.search(r"\[[\d\s.,]+\]", response_text)
    if json_match:
        try:
            scores = json.loads(json_match.group())
            scores = [max(0.0, min(1.0, float(s))) for s in scores]
            if len(scores) >= num_docs:
                return scores[:num_docs]
        except (json.JSONDecodeError, ValueError):
            pass

    numbers = re.findall(r"\b(0\.\d+|1\.0|0|1)\b", response_text)
    scores = [float(n) for n in numbers if 0.0 <= float(n) <= 1.0]

    while len(scores) < num_docs:
        scores.append(0.5)

    return scores[:num_docs]


def _grade_by_similarity(state: GraphState, settings) -> GraphState:
    """
    Filter documents by similarity score from vector search.

    Uses similarity_score attached to document metadata by retrieval node.
    """
    documents = state.get("documents", [])
    threshold = settings.rag_similarity_threshold

    logger.info(f"Filtering {len(documents)} documents by similarity threshold={threshold}")

    grading_scores = []
    filtered_docs = []

    for doc in documents:
        score = doc.metadata.get("similarity_score", 0.0)
        grading_scores.append(score)

        if score >= threshold:
            filtered_docs.append(doc)
            logger.debug(
                f"Document passed (similarity={score:.3f}): "
                f"{doc.metadata.get('citation_id', 'unknown')}"
            )
        else:
            logger.debug(
                f"Document filtered (similarity={score:.3f}): "
                f"{doc.metadata.get('citation_id', 'unknown')}"
            )

    state["grading_scores"] = grading_scores
    state["filtered_documents"] = filtered_docs
    state["retrieval_succeeded"] = len(filtered_docs) > 0

    logger.info(
        f"Similarity filtering: {len(filtered_docs)}/{len(documents)} documents passed "
        f"(threshold={threshold})"
    )

    return state


def _grade_by_llm(state: GraphState, settings) -> GraphState:
    """
    Batch grade documents using LLM-as-judge in a single call.
    """
    query = state.get("rewritten_query", state.get("query", ""))
    documents = state.get("documents", [])

    doc_list = []
    for i, doc in enumerate(documents, 1):
        citation_id = doc.metadata.get("citation_id", "unknown")
        doc_list.append(f"Document {i} [{citation_id}]:\n{doc.page_content[:500]}")

    documents_text = "\n\n---\n\n".join(doc_list)

    llm = ChatOllama(
        model=settings.model_name, temperature=0.0, base_url=settings.ollama_host
    )

    grading_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are grading the relevance of retrieved CCoP clauses to a user question.

Grade each document's relevance on a 0-1 scale:
- 1.0: Directly answers the question
- 0.7-0.9: Related and provides useful context
- 0.4-0.6: Mentions relevant concepts but doesn't fully address question
- 0.1-0.3: Tangentially related
- 0.0: Irrelevant

Be generous - false positives are better than missing relevant context.

Output ONLY a JSON array of scores, one per document. Example for 3 documents:
[0.9, 0.3, 0.7]""",
            ),
            (
                "human",
                "Question: {query}\n\n{documents}\n\nOutput the JSON array of scores:",
            ),
        ]
    )

    try:
        chain = grading_prompt | llm
        response = chain.invoke({"query": query, "documents": documents_text})
        response_text = response.content if hasattr(response, "content") else str(response)

        logger.info("Batch grading response received, parsing scores...")
        grading_scores = _parse_scores(response_text, len(documents))

    except Exception as e:
        logger.warning(f"Batch grading failed: {e}. Passing all documents through.")
        grading_scores = [0.7] * len(documents)

    filtered_docs = []
    for doc, score in zip(documents, grading_scores):
        if score > 0.6:
            filtered_docs.append(doc)

    state["grading_scores"] = grading_scores
    state["filtered_documents"] = filtered_docs
    state["retrieval_succeeded"] = len(filtered_docs) > 0

    logger.info(
        f"LLM grading: {len(filtered_docs)}/{len(documents)} documents passed "
        f"(scores: min={min(grading_scores):.2f}, max={max(grading_scores):.2f}, "
        f"avg={sum(grading_scores)/len(grading_scores):.2f})"
    )

    return state


def grade_documents(state: GraphState) -> GraphState:
    """
    Grade retrieved documents for relevance to query.

    Mode controlled by CCOP_RAG_GRADING_ENABLED:
    - False (default): Fast similarity-score filtering from vector search
    - True: LLM-as-judge batch grading (single LLM call)

    Args:
        state: Current graph state with 'rewritten_query' and 'documents'

    Returns:
        Updated state with 'filtered_documents', 'grading_scores', 'retrieval_succeeded'
    """
    settings = get_settings()
    documents = state.get("documents", [])

    logger.info(f"Grading {len(documents)} retrieved documents...")

    if not documents:
        state["filtered_documents"] = []
        state["grading_scores"] = []
        state["retrieval_succeeded"] = False
        logger.warning("No documents to grade")
        return state

    if settings.rag_grading_enabled:
        logger.info("Using LLM-as-judge batch grading")
        return _grade_by_llm(state, settings)
    else:
        return _grade_by_similarity(state, settings)
