"""
Tests for citation extraction, resolution, and formatting.
"""

import pytest
from langchain_core.documents import Document

from rag.citations.formatter import (
    format_model_only_response,
    format_response_with_citations,
)
from rag.citations.resolver import (
    Citation,
    extract_citation_ids,
    resolve_citations,
)


class TestExtractCitationIds:
    def test_single_anchor(self):
        generation = "Access control requirements are specified in <c>CCoP-2.0.5.5.2.1</c>."
        citation_ids = extract_citation_ids(generation)
        assert citation_ids == ["CCoP-2.0.5.5.2.1"]

    def test_multiple_anchors(self):
        generation = (
            "See <c>CCoP-2.0.5.1</c> for access control, "
            "<c>CCoP-2.0.6.2</c> for monitoring, and "
            "<c>CCoP-2.0.7.3</c> for incident response."
        )
        citation_ids = extract_citation_ids(generation)
        assert citation_ids == ["CCoP-2.0.5.1", "CCoP-2.0.6.2", "CCoP-2.0.7.3"]

    def test_no_anchors(self):
        generation = "This is plain text without any citations."
        citation_ids = extract_citation_ids(generation)
        assert citation_ids == []

    def test_duplicate_anchors(self):
        generation = (
            "As stated in <c>CCoP-2.0.5.1</c>, access control is critical. "
            "Furthermore, <c>CCoP-2.0.5.1</c> also requires authentication."
        )
        citation_ids = extract_citation_ids(generation)
        assert citation_ids == ["CCoP-2.0.5.1"]  # Deduplicated

    def test_empty_string(self):
        citation_ids = extract_citation_ids("")
        assert citation_ids == []

    def test_malformed_anchors(self):
        # Regex matches anything between <c> and </c>, so incomplete tag gets matched too
        generation = "Some text with <c>incomplete tag and <c>CCoP-2.0.5.1</c> valid one."
        citation_ids = extract_citation_ids(generation)
        # The regex will match the entire content between the first <c> and the </c>
        # This is acceptable behavior - malformed input produces malformed output
        assert len(citation_ids) >= 1
        # At least check that the valid citation ID appears in the extracted content
        assert any("CCoP-2.0.5.1" in cid for cid in citation_ids)


class TestResolveCitations:
    def test_valid_resolution(self):
        documents = [
            Document(
                page_content="Access control content",
                metadata={
                    "citation_id": "CCoP-2.0.5.1",
                    "document_source": "CCoP 2.0",
                    "section": "Section 5",
                    "clause": "5.1",
                    "document_type": "primary",
                },
            )
        ]
        citation_ids = ["CCoP-2.0.5.1"]
        citations = resolve_citations(citation_ids, documents)

        assert len(citations) == 1
        assert citations[0]["citation_id"] == "CCoP-2.0.5.1"
        assert citations[0]["document"] == "CCoP 2.0"
        assert citations[0]["section"] == "Section 5"
        assert citations[0]["clause"] == "5.1"
        assert citations[0]["document_type"] == "primary"

    def test_missing_citation(self):
        documents = [
            Document(
                page_content="Access control content",
                metadata={
                    "citation_id": "CCoP-2.0.5.1",
                    "document_source": "CCoP 2.0",
                    "section": "Section 5",
                    "clause": "5.1",
                },
            )
        ]
        citation_ids = ["CCoP-2.0.5.1", "NonExistent-ID"]
        citations = resolve_citations(citation_ids, documents)

        assert len(citations) == 1
        assert citations[0]["citation_id"] == "CCoP-2.0.5.1"

    def test_empty_documents_list(self):
        citation_ids = ["CCoP-2.0.5.1"]
        citations = resolve_citations(citation_ids, [])
        assert citations == []

    def test_empty_citation_ids(self):
        documents = [
            Document(
                page_content="Content",
                metadata={"citation_id": "CCoP-2.0.5.1"},
            )
        ]
        citations = resolve_citations([], documents)
        assert citations == []

    def test_multiple_citations_resolved(self):
        documents = [
            Document(
                page_content="Access control",
                metadata={
                    "citation_id": "CCoP-2.0.5.1",
                    "document_source": "CCoP 2.0",
                    "section": "Section 5",
                    "clause": "5.1",
                    "document_type": "primary",
                },
            ),
            Document(
                page_content="Monitoring",
                metadata={
                    "citation_id": "CCoP-2.0.6.2",
                    "document_source": "CCoP 2.0",
                    "section": "Section 6",
                    "clause": "6.2",
                    "document_type": "primary",
                },
            ),
            Document(
                page_content="Risk assessment",
                metadata={
                    "citation_id": "RiskAssessment.3",
                    "document_source": "Risk Assessment Guide",
                    "section": "Risk Analysis",
                    "clause": "",
                    "document_type": "supplementary",
                },
            ),
        ]
        citation_ids = ["CCoP-2.0.5.1", "CCoP-2.0.6.2", "RiskAssessment.3"]
        citations = resolve_citations(citation_ids, documents)

        assert len(citations) == 3
        assert citations[0]["citation_id"] == "CCoP-2.0.5.1"
        assert citations[1]["citation_id"] == "CCoP-2.0.6.2"
        assert citations[2]["citation_id"] == "RiskAssessment.3"
        assert citations[2]["document"] == "Risk Assessment Guide"


class TestFormatResponseWithCitations:
    def test_with_citations(self):
        generation = "Access control is required per <c>CCoP-2.0.5.1</c>."
        citations: list[Citation] = [
            {
                "citation_id": "CCoP-2.0.5.1",
                "document": "CCoP 2.0",
                "section": "Section 5",
                "clause": "5.1",
                "document_type": "primary",
            }
        ]

        formatted = format_response_with_citations(generation, citations)

        assert "<c>" not in formatted
        assert "</c>" not in formatted
        assert "Access control is required per ." in formatted
        assert "\n\nReferences:" in formatted
        assert "[1] CCoP 2.0 Section 5 Clause 5.1" in formatted

    def test_anchor_removal(self):
        generation = (
            "First point <c>CCoP-2.0.5.1</c> and second point <c>CCoP-2.0.6.2</c>."
        )
        citations: list[Citation] = []

        formatted = format_response_with_citations(generation, citations)

        assert "<c>" not in formatted
        assert "</c>" not in formatted
        assert "First point  and second point ." in formatted

    def test_no_citations(self):
        generation = "This is a plain response without citations."
        citations: list[Citation] = []

        formatted = format_response_with_citations(generation, citations)

        assert formatted == "This is a plain response without citations."
        assert "References:" not in formatted

    def test_multiple_citations_numbered(self):
        generation = "Text with <c>CCoP-2.0.5.1</c> and <c>CCoP-2.0.6.2</c>."
        citations: list[Citation] = [
            {
                "citation_id": "CCoP-2.0.5.1",
                "document": "CCoP 2.0",
                "section": "Section 5",
                "clause": "5.1",
                "document_type": "primary",
            },
            {
                "citation_id": "CCoP-2.0.6.2",
                "document": "CCoP 2.0",
                "section": "Section 6",
                "clause": "6.2",
                "document_type": "primary",
            },
        ]

        formatted = format_response_with_citations(generation, citations)

        assert "[1] CCoP 2.0 Section 5 Clause 5.1" in formatted
        assert "[2] CCoP 2.0 Section 6 Clause 6.2" in formatted

    def test_citation_without_clause(self):
        generation = "See <c>RiskGuide.Section2</c> for details."
        citations: list[Citation] = [
            {
                "citation_id": "RiskGuide.Section2",
                "document": "Risk Assessment Guide",
                "section": "Section 2",
                "clause": "",
                "document_type": "supplementary",
            }
        ]

        formatted = format_response_with_citations(generation, citations)

        assert "[1] Risk Assessment Guide Section 2" in formatted
        assert "Clause" not in formatted

    def test_empty_generation(self):
        formatted = format_response_with_citations("", [])
        assert formatted == ""


class TestFormatModelOnlyResponse:
    def test_prepends_notice(self):
        generation = "This is a model-only response."
        formatted = format_model_only_response(generation)

        assert "[Note: This response is based on model knowledge only" in formatted
        assert "This is a model-only response." in formatted

    def test_no_references_section(self):
        generation = "Model response."
        formatted = format_model_only_response(generation)

        assert "References:" not in formatted

    def test_empty_generation(self):
        formatted = format_model_only_response("")
        assert formatted == ""
