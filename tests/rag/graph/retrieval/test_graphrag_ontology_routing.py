"""
Tests for graphrag-ontology routing (Phase 10, plan 10-02).

Closes RESEARCH Pitfall 3 (provider selection was not mode-aware) and the
multi-allowlist mode-wiring gap (the studio-ssdlc Phase-9 near-miss: a new
`--mode` value added to one allowlist but missed in a second — see
~/.claude/rules/e2e-testing.md). Verifies:

- `route_by_mode({"mode": "graphrag-ontology"})` returns a DISTINCT route key
  from `graphrag` (both target the same physical `graph_retrieval` node,
  which is itself mode-aware — see graph_retrieval_node.py).
- RunId accepts "graphrag-ontology"; rejects a bogus mode.
- The compiled `build_rag_graph` still contains the `graph_retrieval` node and
  the new route key resolves to it (no KeyError at graph-build time).
- `graph_retrieve_documents` (the mode-aware node) selects
  `graph_retrieval_provider_ontology()` for `graphrag-ontology` and
  `graph_retrieval_provider()` for `graphrag`.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

import rag.graph.retrieval.graph_retrieval_node as node_mod
from domain.value_objects.run_id import RunId
from rag.graph.retrieval.graph_retrieval_node import graph_retrieve_documents
from rag.retrieval.edges.routing import route_by_mode


def _settings(top_k=3):
    s = MagicMock()
    s.rag_retrieval_top_k = top_k
    return s


def _docs(provider_marker=None):
    metadata = {
        "citation_id": "c1",
        "section": None,
        "document_source": "doc.pdf",
        "similarity_score": 0.9,
        "original_text": "clause text A",
    }
    if provider_marker:
        metadata["provider"] = provider_marker
    return [Document(page_content="clause text A", metadata=metadata)]


class TestRouteByModeGraphragOntology:
    def test_route_by_mode_graphrag_ontology_is_distinct_from_graphrag(self):
        ontology_route = route_by_mode({"mode": "graphrag-ontology"})
        graphrag_route = route_by_mode({"mode": "graphrag"})

        assert ontology_route == "graph_retrieval_ontology"
        assert graphrag_route == "graph_retrieval"
        assert ontology_route != graphrag_route

    def test_route_by_mode_hybrid_unchanged(self):
        assert route_by_mode({"mode": "hybrid"}) == "retrieval"

    def test_route_by_mode_llm_only_unchanged(self):
        assert route_by_mode({"mode": "llm-only"}) == "fallback"


class TestRunIdAcceptsGraphragOntology:
    def test_run_id_accepts_graphrag_ontology_mode(self):
        run_id = RunId(
            mode="graphrag-ontology", scope="B1", timestamp=datetime(2026, 7, 2, 12, 0, tzinfo=timezone.utc)
        )
        assert run_id.mode == "graphrag-ontology"

    def test_run_id_rejects_bogus_mode(self):
        with pytest.raises(ValueError):
            RunId(
                mode="not-a-real-mode", scope="B1", timestamp=datetime(2026, 7, 2, 12, 0, tzinfo=timezone.utc)
            )


class TestCompiledGraphHandlesOntologyRoute:
    def test_compiled_graph_has_graph_retrieval_node(self):
        from infrastructure.config.settings import get_settings
        from rag.retrieval.graph import build_rag_graph

        app = build_rag_graph(get_settings())
        node_names = set(app.get_graph().nodes.keys())
        assert "graph_retrieval" in node_names
        assert "generate" in node_names

    def test_graphrag_ontology_state_invokes_graph_retrieval_node(self):
        """
        The new route key must resolve at graph-build time (no KeyError) and
        actually reach the graph_retrieval node when invoked with
        mode=graphrag-ontology, proving the conditional-edge map wiring
        (rag/retrieval/graph.py) is correct for the new route.
        """
        container = MagicMock()
        provider = MagicMock()
        provider.retrieve.return_value = []
        container.graph_retrieval_provider_ontology.return_value = provider

        with patch.object(node_mod, "get_settings", return_value=_settings()), patch.object(
            node_mod, "get_container", return_value=container
        ):
            out = graph_retrieve_documents(
                {"query": "q", "mode": "graphrag-ontology", "retrieval_attempts": 0}
            )

        container.graph_retrieval_provider_ontology.assert_called_once()
        container.graph_retrieval_provider.assert_not_called()
        assert out["retrieval_attempts"] == 1


class TestModeAwareNodeProviderSelection:
    """graph_retrieve_documents picks the provider based on state['mode']."""

    def test_graphrag_ontology_mode_selects_ontology_provider(self):
        provider = MagicMock()
        provider.retrieve.return_value = _docs(provider_marker="graphrag-ontology")
        container = MagicMock()
        container.graph_retrieval_provider_ontology.return_value = provider

        with patch.object(node_mod, "get_settings", return_value=_settings()), patch.object(
            node_mod, "get_container", return_value=container
        ):
            out = graph_retrieve_documents(
                {"query": "q", "mode": "graphrag-ontology", "retrieval_attempts": 0}
            )

        container.graph_retrieval_provider_ontology.assert_called_once()
        container.graph_retrieval_provider.assert_not_called()
        assert out["documents"][0].metadata["provider"] == "graphrag-ontology"

    def test_graphrag_mode_selects_phase9_provider(self):
        provider = MagicMock()
        provider.retrieve.return_value = _docs()  # no "provider" key — Phase 9 shape
        container = MagicMock()
        container.graph_retrieval_provider.return_value = provider

        with patch.object(node_mod, "get_settings", return_value=_settings()), patch.object(
            node_mod, "get_container", return_value=container
        ):
            out = graph_retrieve_documents(
                {"query": "q", "mode": "graphrag", "retrieval_attempts": 0}
            )

        container.graph_retrieval_provider.assert_called_once()
        container.graph_retrieval_provider_ontology.assert_not_called()
        assert "provider" not in out["documents"][0].metadata

    def test_default_mode_falls_back_to_phase9_provider(self):
        """No 'mode' key in state (older callers) must not accidentally hit the ontology provider."""
        provider = MagicMock()
        provider.retrieve.return_value = _docs()
        container = MagicMock()
        container.graph_retrieval_provider.return_value = provider

        with patch.object(node_mod, "get_settings", return_value=_settings()), patch.object(
            node_mod, "get_container", return_value=container
        ):
            graph_retrieve_documents({"query": "q", "retrieval_attempts": 0})

        container.graph_retrieval_provider.assert_called_once()
        container.graph_retrieval_provider_ontology.assert_not_called()
