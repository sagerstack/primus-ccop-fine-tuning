"""
LangGraph Adaptive RAG Graph

Assembles stateful graph with query analysis, retrieval, grading,
generation, and fallback nodes with conditional routing.
"""

import logging
from typing import TYPE_CHECKING, Callable

from langgraph.graph import END, StateGraph

from rag.retrieval.edges.routing import decide_after_grading, rewrite_query, route_query

if TYPE_CHECKING:
    from infrastructure.config.settings import Settings
from rag.retrieval.nodes.fallback import fallback_generation
from rag.retrieval.nodes.generation import generate_response
from rag.retrieval.nodes.grading import grade_documents
from rag.retrieval.nodes.query_analysis import analyze_query
from rag.retrieval.nodes.retrieval import retrieve_documents
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def build_rag_graph(settings: "Settings"):
    """
    Build the LangGraph adaptive RAG graph.

    Graph topology:
    ```
    query_analysis
        |
    [needs_retrieval?]
       / \
      Y   N
      |    \
    retrieval  fallback -> END
      |
    grade_documents
      |
    [relevant docs found?]
     / | \
    Y  retry  N (max attempts)
    |    |      \
  generate  rewrite_query  fallback -> END
    |         |
    END    retrieval (loop)
    ```

    Args:
        settings: Application settings (for configuration)

    Returns:
        Compiled LangGraph graph
    """
    logger.info("Building LangGraph adaptive RAG graph...")

    # Create graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("query_analysis", analyze_query)
    workflow.add_node("retrieval", retrieve_documents)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("rewrite_query", rewrite_query)  # Self-correction node
    workflow.add_node("generate", generate_response)
    workflow.add_node("fallback", fallback_generation)

    # Set entry point
    workflow.set_entry_point("query_analysis")

    # Add edges
    # After query analysis: route based on needs_retrieval
    workflow.add_conditional_edges(
        "query_analysis",
        route_query,
        {
            "retrieval": "retrieval",
            "fallback": "fallback",
        },
    )

    # After retrieval: always grade documents
    workflow.add_edge("retrieval", "grade_documents")

    # After grading: decide to generate, rewrite, or fallback
    workflow.add_conditional_edges(
        "grade_documents",
        decide_after_grading,
        {
            "generate": "generate",
            "rewrite": "rewrite_query",  # Self-correction loop
            "fallback": "fallback",
        },
    )

    # After rewrite: loop back to retrieval
    workflow.add_edge("rewrite_query", "retrieval")

    # Terminal nodes
    workflow.add_edge("generate", END)
    workflow.add_edge("fallback", END)

    # Compile graph
    app = workflow.compile()

    logger.info("LangGraph adaptive RAG graph compiled successfully")

    return app


def create_rag_pipeline(settings: "Settings") -> Callable[[str], dict]:
    """
    Create RAG pipeline callable.

    Public API for the RAG system. Returns a simple function that
    accepts a query string and returns the final state with response.

    Args:
        settings: Application settings

    Returns:
        Callable that accepts query string and returns dict with:
        - generation: Response text
        - is_rag_augmented: Whether response used RAG context
        - citations: List of source citations
        - retrieval_attempts: Number of retrieval attempts
        - error: Error message if any
    """
    graph = build_rag_graph(settings)

    def query(question: str) -> dict:
        """
        Query the RAG pipeline.

        Args:
            question: User query

        Returns:
            Final state dict with generation, citations, metadata
        """
        logger.info(f"RAG pipeline query: {question[:100]}...")

        # Initialize state
        initial_state: GraphState = {
            "query": question,
            "rewritten_query": "",
            "needs_retrieval": False,
            "documents": [],
            "filtered_documents": [],
            "grading_scores": [],
            "retrieval_succeeded": False,
            "retrieval_attempts": 0,
            "generation": "",
            "is_rag_augmented": False,
            "citations": [],
            "error": "",
        }

        # Invoke graph
        final_state = graph.invoke(initial_state)

        logger.info(
            f"RAG pipeline complete: is_rag_augmented={final_state.get('is_rag_augmented')}, "
            f"attempts={final_state.get('retrieval_attempts')}"
        )

        return final_state

    return query
