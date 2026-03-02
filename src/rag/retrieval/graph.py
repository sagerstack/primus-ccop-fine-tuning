"""
LangGraph RAG Graph

Assembles stateful graph with mode-based routing:
hybrid (retrieval + LLM), llm-only, or rag-only.
"""

import logging
from typing import TYPE_CHECKING, Callable

from langgraph.graph import END, StateGraph

from rag.retrieval.edges.routing import decide_after_grading, route_by_mode

if TYPE_CHECKING:
    from infrastructure.config.settings import Settings
from rag.retrieval.nodes.fallback import fallback_generation
from rag.retrieval.nodes.generation import generate_response
from rag.retrieval.nodes.grading import grade_documents
from rag.retrieval.nodes.query_analysis import analyze_query
from rag.retrieval.nodes.rag_response import rag_only_response
from rag.retrieval.nodes.reranking import rerank_documents
from rag.retrieval.nodes.retrieval import retrieve_documents
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def build_rag_graph(settings: "Settings"):
    """
    Build the LangGraph RAG graph.

    Graph topology:
    ```
    query_analysis
        |
    [mode?]
        |
    ┌───┼───────────┐
    │   │           │
    │  hybrid    llm-only
    │  rag-only     │
    │   │        fallback
    │   │           │
    │ retrieval    END
    │   │
    │ reranking
    │   │
    │ grading
    │   │
    │ [mode + docs?]
    │   │
    ├───┼───────┬──────────┐
    │   │       │          │
    │ hybrid  hybrid    rag-only
    │ +docs   -docs       │
    │   │       │      rag_response
    │ generate fallback   │
    │   │       │        END
    │  END     END
    ```

    Args:
        settings: Application settings (for configuration)

    Returns:
        Compiled LangGraph graph
    """
    logger.info("Building LangGraph RAG graph...")

    workflow = StateGraph(GraphState)

    # Nodes
    workflow.add_node("query_analysis", analyze_query)
    workflow.add_node("retrieval", retrieve_documents)
    workflow.add_node("reranking", rerank_documents)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate_response)
    workflow.add_node("fallback", fallback_generation)
    workflow.add_node("rag_response", rag_only_response)

    # Entry point
    workflow.set_entry_point("query_analysis")

    # Mode routing: after query_analysis, route by mode
    workflow.add_conditional_edges(
        "query_analysis",
        route_by_mode,
        {
            "retrieval": "retrieval",
            "fallback": "fallback",
        },
    )

    # Retrieval → reranking → grading (always)
    workflow.add_edge("retrieval", "reranking")
    workflow.add_edge("reranking", "grade_documents")

    # After grading: route by mode + retrieval success
    workflow.add_conditional_edges(
        "grade_documents",
        decide_after_grading,
        {
            "generate": "generate",
            "fallback": "fallback",
            "rag_response": "rag_response",
        },
    )

    # Terminal nodes
    workflow.add_edge("generate", END)
    workflow.add_edge("fallback", END)
    workflow.add_edge("rag_response", END)

    app = workflow.compile()

    logger.info("LangGraph RAG graph compiled successfully")

    return app


def create_rag_pipeline(settings: "Settings") -> Callable[[str, str], dict]:
    """
    Create RAG pipeline callable.

    Args:
        settings: Application settings

    Returns:
        Callable that accepts (query, mode) and returns final state dict
    """
    graph = build_rag_graph(settings)

    def query(question: str, mode: str = "hybrid") -> dict:
        """
        Query the RAG pipeline.

        Args:
            question: User query
            mode: Pipeline mode — "hybrid", "llm-only", "rag-only"

        Returns:
            Final state dict with generation, citations, metadata
        """
        logger.info(f"RAG pipeline query (mode={mode}): {question[:100]}...")

        initial_state: GraphState = {
            "mode": mode,
            "query": question,
            "rewritten_query": "",
            "needs_retrieval": False,
            "documents": [],
            "filtered_documents": [],
            "grading_scores": [],
            "retrieval_succeeded": False,
            "retrieval_attempts": 0,
            "reranker_scores": [],
            "generation": "",
            "is_rag_augmented": False,
            "citations": [],
            "error": "",
        }

        final_state = graph.invoke(initial_state)

        logger.info(
            f"RAG pipeline complete: mode={mode}, "
            f"is_rag_augmented={final_state.get('is_rag_augmented')}, "
            f"attempts={final_state.get('retrieval_attempts')}"
        )

        return final_state

    return query
