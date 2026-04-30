"""
Tests for LangGraph state schema.
"""

import pytest
from langchain_core.documents import Document

from rag.retrieval.state.graph_state import GraphState

# Phase 3.1 I/O capture fields added to GraphState
IO_CAPTURE_FIELDS = [
    "system_prompt",
    "user_prompt",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "latency_ms",
    "retrieved_contexts_detailed",
]


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


class TestGraphStateIoCaptureFields:
    """Phase 3.1 I/O capture fields added to GraphState schema."""

    def test_all_io_capture_fields_in_annotations(self):
        """All 7 new I/O capture fields must be present in GraphState.__annotations__."""
        annotations = GraphState.__annotations__
        for field in IO_CAPTURE_FIELDS:
            assert field in annotations, (
                f"Expected GraphState to have annotation '{field}', "
                f"but it was not found. Available keys: {sorted(annotations.keys())}"
            )

    def test_system_prompt_annotation_is_str(self):
        assert GraphState.__annotations__["system_prompt"] == str

    def test_user_prompt_annotation_is_str(self):
        assert GraphState.__annotations__["user_prompt"] == str

    def test_prompt_tokens_annotation_is_int(self):
        assert GraphState.__annotations__["prompt_tokens"] == int

    def test_completion_tokens_annotation_is_int(self):
        assert GraphState.__annotations__["completion_tokens"] == int

    def test_total_tokens_annotation_is_int(self):
        assert GraphState.__annotations__["total_tokens"] == int

    def test_latency_ms_annotation_is_int(self):
        assert GraphState.__annotations__["latency_ms"] == int

    def test_io_capture_fields_with_zero_defaults(self):
        """An initial state dict with zero/empty I/O capture defaults is valid."""
        state: GraphState = {
            "query": "Test",
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
            # I/O capture fields with zero/empty defaults
            "system_prompt": "",
            "user_prompt": "",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "latency_ms": 0,
            "retrieved_contexts_detailed": [],
        }

        assert state["system_prompt"] == ""
        assert state["user_prompt"] == ""
        assert state["prompt_tokens"] == 0
        assert state["completion_tokens"] == 0
        assert state["total_tokens"] == 0
        assert state["latency_ms"] == 0
        assert state["retrieved_contexts_detailed"] == []

    def test_io_capture_fields_with_real_values(self):
        """I/O capture fields accept non-zero values after inference."""
        state: GraphState = {
            "query": "What are MFA requirements?",
            "rewritten_query": "",
            "needs_retrieval": True,
            "documents": [],
            "filtered_documents": [],
            "grading_scores": [],
            "retrieval_succeeded": True,
            "retrieval_attempts": 1,
            "generation": "MFA is required for privileged access.",
            "is_rag_augmented": True,
            "citations": [],
            "error": "",
            "system_prompt": "You are a CCoP 2.0 expert.",
            "user_prompt": "Context: [chunk text]. Question: What are MFA requirements?",
            "prompt_tokens": 120,
            "completion_tokens": 45,
            "total_tokens": 165,
            "latency_ms": 1234,
            "retrieved_contexts_detailed": [
                {"citation_id": "CCoP-5.2.1", "text": "MFA required.", "score": 0.91}
            ],
        }

        assert state["system_prompt"] == "You are a CCoP 2.0 expert."
        assert state["prompt_tokens"] == 120
        assert state["completion_tokens"] == 45
        assert state["total_tokens"] == 165
        assert state["latency_ms"] == 1234
        assert len(state["retrieved_contexts_detailed"]) == 1
