"""
Live-Neo4j integration test for Neo4jGraphRetrievalAdapter (Phase 9 Plan 04).

READ-ONLY against the existing live CCoP knowledge graph. Does NOT seed,
build, or drop anything — the corpus KG (625 nodes / 1,232 relationships /
179 chunks / 7 docs, built via `ccop-eval graph build` in Plan 02) is
expensive to rebuild and is required by downstream Wave 6 evaluation.

Marked `@pytest.mark.integration` so `poetry run pytest -m "not integration"`
stays green without a live Neo4j service (mirrors
tests/rag/test_qdrant_vector_store_adapter.py's precedent).
"""

import pytest

from infrastructure.config.settings import get_settings
from rag.graph.retrieval.neo4j_graph_retrieval_adapter import (
    Neo4jGraphRetrievalAdapter,
)


@pytest.mark.integration
class TestNeo4jGraphRetrievalAdapterIntegration:
    """Read-only retrieval against the live, existing CCoP graph."""

    def test_retrieve_returns_nonempty_documents_with_required_metadata(self):
        settings = get_settings()

        adapter = Neo4jGraphRetrievalAdapter(settings=settings)

        try:
            docs = adapter.retrieve(
                "What are the access control requirements for CII?", top_k=3
            )

            assert len(docs) > 0, "Expected non-empty retrieval from the live CCoP graph"

            for doc in docs:
                assert hasattr(doc, "page_content")
                assert doc.page_content  # non-empty context text
                for key in (
                    "citation_id",
                    "section",
                    "document_source",
                    "similarity_score",
                    "original_text",
                ):
                    assert key in doc.metadata
        finally:
            # Read-only test: no writes were made, nothing to tear down.
            # Explicitly close the driver this test opened to avoid leaking
            # a bolt connection across test runs.
            adapter._driver.close()
