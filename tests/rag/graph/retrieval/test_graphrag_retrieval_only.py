"""
Tests for the graphrag CLI mode surface (Phase 9 Plan 05, D-10).

Covers:
- `evaluate run` exposes ONLY `graphrag` (scored) — no retrieval-only mode
  (unscoreable, deliberately excluded).
- `query ask` exposes both `graphrag` (scored: graph -> primus) and
  `graphrag-retrieval` (inspection-only: graph -> rag_response, no generation),
  mirroring the existing hybrid/rag-only split.
- Routing: `graphrag-retrieval` mirrors `rag-only` (always -> rag_response,
  no LLM call, token counts stay 0); `graphrag` still routes to `generate`
  when retrieval succeeds (unchanged primus generation, D-06).
- `LangGraphRagAdapter.is_available` treats both graphrag modes as available
  only when the graph provider (Neo4j) is configured.
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from rag.graph.retrieval.graph_retrieval_node import graph_retrieve_documents
from rag.retrieval.edges.routing import decide_after_grading, route_by_mode
from rag.retrieval.nodes.rag_response import rag_only_response


class TestEvaluateModeSurface:
    """`evaluate run` gains ONLY `graphrag` — no retrieval-only mode (D-10)."""

    def test_graphrag_is_a_valid_evaluate_mode(self):
        from presentation.cli.commands.evaluate import VALID_EVAL_MODES

        assert "graphrag" in VALID_EVAL_MODES
        # Phase 10 (plan 10-02) adds "graphrag-ontology" to this allowlist.
        assert VALID_EVAL_MODES == ["hybrid", "llm-only", "graphrag", "graphrag-ontology"]

    def test_no_retrieval_only_mode_on_evaluate(self):
        from presentation.cli.commands.evaluate import VALID_EVAL_MODES

        assert "rag-only" not in VALID_EVAL_MODES
        assert "graphrag-retrieval" not in VALID_EVAL_MODES


class TestQueryModeSurface:
    """`query ask` gains `graphrag` AND the graph-retrieval-only inspection mode."""

    def test_graphrag_modes_are_valid_query_modes(self):
        from rag.presentation.cli.query import VALID_MODES

        assert "graphrag" in VALID_MODES
        assert "graphrag-retrieval" in VALID_MODES
        # Phase 10 (plan 10-02) adds "graphrag-ontology" to this allowlist.
        assert VALID_MODES == [
            "hybrid",
            "llm-only",
            "rag-only",
            "graphrag",
            "graphrag-retrieval",
            "graphrag-ontology",
        ]


class TestGraphragRouting:
    """route_by_mode / decide_after_grading for both graphrag mode variants."""

    def test_route_by_mode_graphrag_goes_to_graph_retrieval(self):
        assert route_by_mode({"mode": "graphrag"}) == "graph_retrieval"

    def test_route_by_mode_graphrag_retrieval_goes_to_graph_retrieval(self):
        assert route_by_mode({"mode": "graphrag-retrieval"}) == "graph_retrieval"

    def test_decide_after_grading_graphrag_retrieval_always_rag_response(self):
        # Mirrors rag-only: no LLM call regardless of retrieval_succeeded.
        assert (
            decide_after_grading({"mode": "graphrag-retrieval", "retrieval_succeeded": True})
            == "rag_response"
        )
        assert (
            decide_after_grading({"mode": "graphrag-retrieval", "retrieval_succeeded": False})
            == "rag_response"
        )

    def test_decide_after_grading_graphrag_generates_when_retrieval_succeeded(self):
        assert (
            decide_after_grading({"mode": "graphrag", "retrieval_succeeded": True}) == "generate"
        )

    def test_decide_after_grading_graphrag_falls_back_when_no_docs(self):
        assert (
            decide_after_grading({"mode": "graphrag", "retrieval_succeeded": False}) == "fallback"
        )

    def test_decide_after_grading_rag_only_unchanged(self):
        assert decide_after_grading({"mode": "rag-only", "retrieval_succeeded": True}) == "rag_response"


class TestGraphragRetrievalOnlyNoGeneration:
    """End-to-end (mocked provider): graphrag-retrieval performs no LLM call."""

    def _docs(self):
        return [
            Document(
                page_content="clause text A",
                metadata={
                    "citation_id": "c1",
                    "section": None,
                    "document_source": "doc.pdf",
                    "similarity_score": 0.9,
                    "original_text": "clause text A",
                },
            )
        ]

    def test_graph_retrieval_then_rag_response_has_zero_token_counts(self):
        import rag.graph.retrieval.graph_retrieval_node as node_mod

        provider = MagicMock()
        provider.retrieve.return_value = self._docs()
        container = MagicMock()
        container.graph_retrieval_provider.return_value = provider
        settings = MagicMock()
        settings.rag_retrieval_top_k = 3

        with patch.object(node_mod, "get_settings", return_value=settings), patch.object(
            node_mod, "get_container", return_value=container
        ):
            state = graph_retrieve_documents(
                {"mode": "graphrag-retrieval", "query": "access control?", "retrieval_attempts": 0}
            )

        assert route_by_mode(state) == "graph_retrieval"
        assert decide_after_grading(state) == "rag_response"

        final_state = rag_only_response(state)

        assert final_state["prompt_tokens"] == 0
        assert final_state["completion_tokens"] == 0
        assert final_state["total_tokens"] == 0
        assert final_state["system_prompt"] == ""
        assert final_state["user_prompt"] == ""
        assert final_state["generation"] != ""  # formatted retrieval, not empty


class TestLangGraphRagAdapterGraphragAvailability:
    """is_available() treats graphrag modes as available only with a graph provider."""

    def _adapter(self, neo4j_uri, ollama_host="http://localhost:11434"):
        from rag.infrastructure.adapters.langgraph_rag_adapter import LangGraphRagAdapter

        settings = MagicMock()
        settings.ollama_host = ollama_host
        settings.neo4j_uri = neo4j_uri
        logger = MagicMock()
        return LangGraphRagAdapter(settings=settings, logger=logger)

    @pytest.mark.asyncio
    async def test_graphrag_available_when_neo4j_configured(self):
        adapter = self._adapter(neo4j_uri="bolt://localhost:7687")
        assert await adapter.is_available("graphrag") is True

    @pytest.mark.asyncio
    async def test_graphrag_retrieval_available_when_neo4j_configured(self):
        adapter = self._adapter(neo4j_uri="bolt://localhost:7687")
        assert await adapter.is_available("graphrag-retrieval") is True

    @pytest.mark.asyncio
    async def test_graphrag_unavailable_when_neo4j_not_configured(self):
        adapter = self._adapter(neo4j_uri="")
        assert await adapter.is_available("graphrag") is False

    @pytest.mark.asyncio
    async def test_graphrag_unavailable_when_ollama_not_configured(self):
        adapter = self._adapter(neo4j_uri="bolt://localhost:7687", ollama_host="")
        assert await adapter.is_available("graphrag") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
