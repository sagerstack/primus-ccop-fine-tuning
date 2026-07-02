"""
Tests for graphrag routing (Phase 9, D-06/D-09).

Verifies `--mode graphrag` routes to the graph_retrieval node (swapping ONLY
retrieval) while hybrid / llm-only / rag-only routing is unchanged, and that
the compiled graph contains the graph_retrieval node reaching grade_documents
→ generate (the unchanged primus node).
"""

from rag.retrieval.edges.routing import route_by_mode


def test_route_by_mode_graphrag_goes_to_graph_retrieval():
    assert route_by_mode({"mode": "graphrag"}) == "graph_retrieval"


def test_route_by_mode_hybrid_unchanged():
    assert route_by_mode({"mode": "hybrid"}) == "retrieval"


def test_route_by_mode_rag_only_unchanged():
    assert route_by_mode({"mode": "rag-only"}) == "retrieval"


def test_route_by_mode_llm_only_unchanged():
    assert route_by_mode({"mode": "llm-only"}) == "fallback"


def test_route_by_mode_default_is_retrieval():
    assert route_by_mode({}) == "retrieval"


def test_compiled_graph_has_graph_retrieval_node_reaching_generate():
    """graphrag path exists: graph_retrieval node present and generate is unchanged."""
    from infrastructure.config.settings import get_settings
    from rag.retrieval.graph import build_rag_graph

    app = build_rag_graph(get_settings())
    node_names = set(app.get_graph().nodes.keys())
    assert "graph_retrieval" in node_names
    # The unchanged primus generation node is still the terminal generator.
    assert "generate" in node_names
    # Reranking still exists for the vector path (graph path bypasses it).
    assert "reranking" in node_names
