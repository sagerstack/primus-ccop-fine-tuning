"""
Tests for LangGraph state schema.
"""

import pytest
from langchain_core.documents import Document

from rag.retrieval.state.graph_state import GraphState


class TestGraphState:
    def test_initialization_with_required_fields(self):
        state: GraphState = {
            "query": "What are access control requirements?",
            "rewritten_query": "",
            "needs_retrieval": True,
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

        assert state["query"] == "What are access control requirements?"
        assert state["needs_retrieval"] is True
        assert state["documents"] == []
        assert state["retrieval_attempts"] == 0

    def test_state_holds_document_objects(self):
        doc1 = Document(
            page_content="Access control content",
            metadata={"citation_id": "CCoP-2.0.5.1"},
        )
        doc2 = Document(
            page_content="Monitoring content",
            metadata={"citation_id": "CCoP-2.0.6.2"},
        )

        state: GraphState = {
            "query": "Test query",
            "rewritten_query": "",
            "needs_retrieval": True,
            "documents": [doc1, doc2],
            "filtered_documents": [doc1],
            "grading_scores": [0.85, 0.45],
            "retrieval_succeeded": True,
            "retrieval_attempts": 1,
            "generation": "Generated response",
            "is_rag_augmented": True,
            "citations": [{"citation_id": "CCoP-2.0.5.1"}],
            "error": "",
        }

        assert len(state["documents"]) == 2
        assert len(state["filtered_documents"]) == 1
        assert state["documents"][0].page_content == "Access control content"
        assert state["filtered_documents"][0].metadata["citation_id"] == "CCoP-2.0.5.1"

    def test_state_with_error(self):
        state: GraphState = {
            "query": "Test query",
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
            "error": "Databricks connection failed",
        }

        assert state["error"] == "Databricks connection failed"

    def test_state_after_self_correction(self):
        state: GraphState = {
            "query": "Original query",
            "rewritten_query": "Reformulated query with more context",
            "needs_retrieval": True,
            "documents": [],
            "filtered_documents": [],
            "grading_scores": [],
            "retrieval_succeeded": False,
            "retrieval_attempts": 2,
            "generation": "",
            "is_rag_augmented": False,
            "citations": [],
            "error": "",
        }

        assert state["rewritten_query"] == "Reformulated query with more context"
        assert state["retrieval_attempts"] == 2
