"""
Document Grading Node

LLM-as-judge pattern for relevance scoring.
Filters documents with score > 0.6 threshold.
"""

import logging

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


class GradeResult(BaseModel):
    """
    Document relevance grading result.

    Score 0-1 with reasoning explanation.
    """

    score: float = Field(
        description="Relevance score 0-1 (0=irrelevant, 1=highly relevant)", ge=0.0, le=1.0
    )
    reasoning: str = Field(description="Explanation of relevance score")


def grade_documents(state: GraphState) -> GraphState:
    """
    Grade each retrieved document for relevance to query.

    Uses LLM-as-judge pattern with Llama-Primus-Reasoning.
    Filters documents: keep only those with score > 0.6.

    This catches silent failures where vector search returns
    irrelevant results but system appears to work (Pitfall 1).

    Args:
        state: Current graph state with 'rewritten_query' and 'documents'

    Returns:
        Updated state with 'filtered_documents', 'grading_scores', 'retrieval_succeeded'
    """
    settings = get_settings()
    query = state.get("rewritten_query", state.get("query", ""))
    documents = state.get("documents", [])

    logger.info(f"Grading {len(documents)} retrieved documents...")

    if not documents:
        state["filtered_documents"] = []
        state["grading_scores"] = []
        state["retrieval_succeeded"] = False
        logger.warning("No documents to grade")
        return state

    # Initialize LLM for grading
    llm = ChatOllama(
        model=settings.model_name, temperature=0.0, base_url=settings.ollama_host
    )

    # Grading prompt
    grading_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are grading the relevance of a retrieved CCoP clause to a user question.

Grade relevance on a 0-1 scale:
- 1.0: Clause directly answers the question or contains required information
- 0.7-0.9: Clause is related and provides useful context
- 0.4-0.6: Clause mentions relevant concepts but doesn't fully address question
- 0.1-0.3: Clause is tangentially related
- 0.0: Clause is irrelevant

If the clause contains keywords or semantic meaning related to the question,
grade it as relevant (>0.6). Be generous - false positives are better than
missing relevant context.""",
            ),
            (
                "human",
                "Question: {query}\n\nCCoP Clause:\n{document}\n\nGrade the relevance.",
            ),
        ]
    )

    grader = grading_prompt | llm.with_structured_output(GradeResult)

    grading_scores = []
    filtered_docs = []

    for doc in documents:
        try:
            # Grade document
            grade = grader.invoke({"query": query, "document": doc.page_content})

            grading_scores.append(grade.score)

            # Filter: keep if score > 0.6
            if grade.score > 0.6:
                filtered_docs.append(doc)
                logger.debug(
                    f"Document passed grading (score={grade.score:.2f}): "
                    f"{doc.metadata.get('citation_id', 'unknown')}"
                )
            else:
                logger.debug(
                    f"Document filtered out (score={grade.score:.2f}): "
                    f"{doc.metadata.get('citation_id', 'unknown')}"
                )

        except Exception as e:
            logger.warning(f"Grading failed for document: {e}. Assigning score=0.0")
            grading_scores.append(0.0)

    state["grading_scores"] = grading_scores
    state["filtered_documents"] = filtered_docs
    state["retrieval_succeeded"] = len(filtered_docs) > 0

    logger.info(
        f"Grading complete: {len(filtered_docs)}/{len(documents)} documents passed "
        f"(scores: min={min(grading_scores):.2f}, max={max(grading_scores):.2f}, "
        f"avg={sum(grading_scores)/len(grading_scores):.2f})"
    )

    return state
