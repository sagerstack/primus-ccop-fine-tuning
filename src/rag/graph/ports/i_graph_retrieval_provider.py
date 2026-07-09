"""
Graph Retrieval Provider Port (Interface)

Abstract interface for graph-backed retrieval (D-11: pluggable graph
*retrieval* provider). The Neo4j graph — and, in Phase 10, an
ontology-grounded graph — sits behind this abstraction, selected by the
DI container based on `--mode`.

D-06 (model roles, MUST hold): a graph retrieval provider returns retrieved
CONTEXTS (a graph neighborhood), NEVER a finished answer. The existing
primus `generate` node (src/rag/retrieval/nodes/generation.py) consumes the
returned Documents exactly as it consumes the vector-store retriever's
output — this port's job is solely to make that swap safe.
"""

from abc import ABC, abstractmethod

from langchain_core.documents import Document


class IGraphRetrievalProvider(ABC):
    """
    Port for graph-backed retrieval operations.

    This abstraction enables swappable graph-retrieval implementations
    (Neo4j emergent-KG in Phase 9; Neo4j ontology-grounded KG in Phase 10)
    without changing the LangGraph node or the downstream generation node.
    """

    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> list[Document]:
        """
        Retrieve graph-neighborhood contexts relevant to a query.

        Returns retrieved CONTEXTS, NOT an answer (D-06) — the caller
        (graph_retrieve_documents node) feeds these Documents into the
        unchanged primus generation node, exactly like the vector-store
        retriever's output in hybrid mode.

        Args:
            query: User query text (embedded internally; never string-
                formatted into Cypher — see Neo4jGraphRetrievalAdapter).
            top_k: Number of neighborhood contexts to return.

        Returns:
            List of langchain Documents whose metadata carries, at minimum:
            citation_id, section, document_source, similarity_score,
            original_text — the exact shape hybrid's vector-store retriever
            produces, so the judge + RAGAs harness runs unchanged.

        Raises:
            Exception: Implementations should let underlying errors
                propagate; the calling node is responsible for catching
                and recording retrieval failures in graph state.
        """
        ...
