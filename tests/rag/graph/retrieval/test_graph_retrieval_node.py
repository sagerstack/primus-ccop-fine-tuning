"""
Tests for the graph_retrieve_documents LangGraph node (Phase 9, D-06/D-11).

Mocked — no live Neo4j. Verifies the node pulls contexts from the DI
graph_retrieval_provider, populates `documents` (the wide candidate pool) in
hybrid's Document shape WITHOUT pre-setting filtered_documents (Wave-6 parity:
the shared reranker + grader own the final top-N), sets retrieval_succeeded,
and degrades cleanly when no provider is configured.
"""

from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

import rag.graph.retrieval.graph_retrieval_node as node_mod
from rag.graph.retrieval.graph_retrieval_node import graph_retrieve_documents


def _settings(top_k=3):
    s = MagicMock()
    s.rag_retrieval_top_k = top_k
    return s


def _docs():
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
        ),
        Document(
            page_content="clause text B",
            metadata={
                "citation_id": "c2",
                "section": None,
                "document_source": "doc.pdf",
                "similarity_score": 0.7,
                "original_text": "clause text B",
            },
        ),
    ]


def test_node_populates_documents_and_defers_filtering_to_reranker():
    provider = MagicMock()
    provider.retrieve.return_value = _docs()
    container = MagicMock()
    container.graph_retrieval_provider.return_value = provider

    with patch.object(node_mod, "get_settings", return_value=_settings(top_k=5)), patch.object(
        node_mod, "get_container", return_value=container
    ):
        out = graph_retrieve_documents({"query": "access control?", "retrieval_attempts": 0})

    # Retrieves the WIDE candidate pool (rag_retrieval_top_k), not the final top-N.
    provider.retrieve.assert_called_once_with(query="access control?", top_k=5)
    assert len(out["documents"]) == 2
    # Wave-6 parity: the node must NOT pre-set filtered_documents — the shared
    # reranker → grader own the final top-N (else the reranker is a no-op).
    assert "filtered_documents" not in out
    assert out["retrieval_succeeded"] is True
    assert out["retrieval_attempts"] == 1
    # dense_rank attached so the reranker's RRF ensemble (dense_rank ⊕ ce_rank) works.
    assert out["documents"][0].metadata["dense_rank"] == 1
    assert out["documents"][1].metadata["dense_rank"] == 2


def test_node_prefers_rewritten_query():
    provider = MagicMock()
    provider.retrieve.return_value = _docs()
    container = MagicMock()
    container.graph_retrieval_provider.return_value = provider

    with patch.object(node_mod, "get_settings", return_value=_settings()), patch.object(
        node_mod, "get_container", return_value=container
    ):
        graph_retrieve_documents(
            {"query": "orig", "rewritten_query": "rewritten q", "retrieval_attempts": 1}
        )

    provider.retrieve.assert_called_once_with(query="rewritten q", top_k=3)


def test_node_handles_no_provider():
    container = MagicMock()
    container.graph_retrieval_provider.return_value = None

    with patch.object(node_mod, "get_settings", return_value=_settings()), patch.object(
        node_mod, "get_container", return_value=container
    ):
        out = graph_retrieve_documents({"query": "q", "retrieval_attempts": 0})

    assert out["documents"] == []
    assert out["filtered_documents"] == []
    assert out["retrieval_succeeded"] is False
    assert out["retrieval_attempts"] == 1
    assert "provider" in out["error"].lower()


def test_node_handles_provider_exception():
    provider = MagicMock()
    provider.retrieve.side_effect = RuntimeError("bolt down")
    container = MagicMock()
    container.graph_retrieval_provider.return_value = provider

    with patch.object(node_mod, "get_settings", return_value=_settings()), patch.object(
        node_mod, "get_container", return_value=container
    ):
        out = graph_retrieve_documents({"query": "q", "retrieval_attempts": 0})

    assert out["documents"] == []
    assert out["retrieval_succeeded"] is False
    assert "bolt down" in out["error"]
