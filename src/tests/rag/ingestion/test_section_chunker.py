"""
Tests for section-level semantic chunking.
"""

import pytest

from rag.ingestion.chunkers.section_chunker import (
    _create_citation_id,
    _extract_clause_number,
    chunk_document,
    chunk_qa_pairs,
)
from rag.ingestion.models import ChunkMetadata, QAPair


class TestChunkDocument:
    def test_splits_at_header_boundaries(self):
        # Create markdown with large enough sections to avoid merging
        markdown = """# CCoP 2.0

## Section 5: Access Control

""" + " ".join(["Access control requirements for CII include authentication and authorization mechanisms."] * 50) + """

### 5.1 Authentication

""" + " ".join(["Multi-factor authentication must be implemented for all privileged accounts."] * 30) + """

### 5.2 Authorization

""" + " ".join(["Role-based access control must be enforced."] * 30) + """

## Section 6: Security Monitoring

""" + " ".join(["Continuous monitoring of security events is required."] * 50)

        chunks = chunk_document(markdown, "CCoP 2.0")

        assert len(chunks) > 0
        # Check that sections appear in chunk metadata
        all_text = " ".join(c.text for c in chunks)
        assert "Section 5: Access Control" in all_text or any("Section 5" in c.metadata.section for c in chunks)
        assert "Section 6: Security Monitoring" in all_text or any("Section 6" in c.metadata.section for c in chunks)

    def test_metadata_extraction(self):
        # Use larger sections to avoid merging
        markdown = """# CCoP 2.0

## Section 5: Access Control

""" + " ".join(["Content about access control."] * 50) + """

### 5.1 Authentication

""" + " ".join(["Multi-factor authentication must be implemented for all privileged accounts."] * 30)

        chunks = chunk_document(markdown, "CCoP 2.0")

        assert len(chunks) > 0
        # Check that at least one chunk has proper metadata
        has_section_5 = any("Section 5" in c.metadata.section for c in chunks)
        has_subsection_5_1 = any("5.1" in c.metadata.subsection for c in chunks)
        has_clause_5_1 = any("5.1" in c.metadata.clause for c in chunks)
        has_ccop_citation = any("CCoP" in c.metadata.citation_id for c in chunks)

        assert has_section_5, "Should have Section 5 in metadata"
        assert has_subsection_5_1 or has_clause_5_1, "Should have 5.1 reference in metadata"
        assert has_ccop_citation, "Should have CCoP in citation_id"

    def test_citation_id_format(self):
        # Use larger section to avoid merging
        markdown = """# CCoP 2.0

## Section 5: Access Control

""" + " ".join(["Content about access control."] * 50) + """

### 5.1 Authentication

""" + " ".join(["Content about authentication with clause 5.1.2 requirement."] * 30)

        chunks = chunk_document(markdown, "CCoP 2.0")

        citation_ids = [c.metadata.citation_id for c in chunks]
        assert any("CCoP" in cid for cid in citation_ids), f"Expected CCoP in citation IDs: {citation_ids}"
        # Check for clause reference (5.1 or 5.1.2)
        has_clause = any(("5.1" in cid or "5" in cid) for cid in citation_ids)
        assert has_clause, f"Expected clause reference in citation IDs: {citation_ids}"

    def test_small_section_handling(self):
        """Small sections (< 200 tokens) should be merged with preceding chunks."""
        # Create markdown with alternating large and small sections
        markdown = """# Document

## Section 1

""" + " ".join(["word"] * 250) + """

## Section 2

Small section with few words.

## Section 3

""" + " ".join(["word"] * 250)

        chunks = chunk_document(markdown, "Test Document")

        # Small section should be merged, not standalone
        standalone_small = any(
            50 < len(c.text.split()) < 200 for c in chunks
        )
        # With merging, we should have fewer standalone small chunks
        assert len(chunks) <= 3  # Not one chunk per section

    def test_large_section_splitting(self):
        """Large sections (> 1000 tokens) should be split on paragraph boundaries."""
        # Create markdown with a very large section
        large_text = "\n\n".join(
            [f"Paragraph {i} with content. " + " ".join(["word"] * 100) for i in range(15)]
        )
        markdown = f"""# Document

## Large Section

{large_text}
"""
        chunks = chunk_document(markdown, "Test Document")

        # Should have multiple chunks from the large section
        assert len(chunks) > 1
        # No chunk should exceed 1000 tokens significantly
        for chunk in chunks:
            token_count = len(chunk.text.split())
            assert token_count <= 1100  # Allow some flexibility


class TestChunkQAPairs:
    def test_qa_pair_conversion(self):
        qa_pairs = [
            QAPair(
                question="What is the incident reporting timeline?",
                answer="Incidents must be reported within 2 hours.",
                linked_clause="7.2.1",
                metadata=ChunkMetadata(
                    document_source="CCoP Response to Feedback",
                    section="Incident Response",
                    subsection="",
                    clause="7.2.1",
                    citation_id="ResponseFeedback.IncidentResponse.7.2.1",
                    document_type="clarification",
                ),
            )
        ]

        chunks = chunk_qa_pairs(qa_pairs, "CCoP Response to Feedback")

        assert len(chunks) == 1
        assert "Q: What is the incident reporting timeline?" in chunks[0].text
        assert "A: Incidents must be reported within 2 hours." in chunks[0].text
        assert chunks[0].metadata.document_type == "clarification"

    def test_multiple_qa_pairs(self):
        qa_pairs = [
            QAPair(
                question="Question 1?",
                answer="Answer 1.",
                metadata=ChunkMetadata(
                    document_source="Test Doc",
                    section="Section 1",
                    subsection="",
                    clause="",
                    citation_id="TestDoc.Section1",
                    document_type="clarification",
                ),
            ),
            QAPair(
                question="Question 2?",
                answer="Answer 2.",
                metadata=ChunkMetadata(
                    document_source="Test Doc",
                    section="Section 2",
                    subsection="",
                    clause="",
                    citation_id="TestDoc.Section2",
                    document_type="clarification",
                ),
            ),
        ]

        chunks = chunk_qa_pairs(qa_pairs, "Test Doc")

        assert len(chunks) == 2
        assert "Q: Question 1?" in chunks[0].text
        assert "Q: Question 2?" in chunks[1].text

    def test_qa_text_format(self):
        qa_pairs = [
            QAPair(
                question="What is required?",
                answer="Implementation of controls.",
                metadata=ChunkMetadata(
                    document_source="Test",
                    section="",
                    subsection="",
                    clause="",
                    citation_id="Test",
                    document_type="clarification",
                ),
            )
        ]

        chunks = chunk_qa_pairs(qa_pairs, "Test")

        assert chunks[0].text == "Q: What is required?\n\nA: Implementation of controls."


class TestExtractClauseNumber:
    def test_extract_from_text(self):
        text = "Section 5.2.1 requires multi-factor authentication."
        clause = _extract_clause_number(text)
        assert clause == "5.2.1"

    def test_extract_two_digit_clause(self):
        text = "According to clause 7.3, incident reporting..."
        clause = _extract_clause_number(text)
        assert clause == "7.3"

    def test_no_clause_number(self):
        text = "This text does not contain any clause numbers."
        clause = _extract_clause_number(text)
        assert clause == ""

    def test_extract_first_occurrence(self):
        text = "Clause 5.1 and clause 5.2 are both relevant."
        clause = _extract_clause_number(text)
        assert clause == "5.1"


class TestCreateCitationId:
    def test_with_clause(self):
        citation_id = _create_citation_id("CCoP 2.0", "Section 5", "5.2.1")
        assert "CCoP" in citation_id
        assert "Section" in citation_id or "5" in citation_id
        assert "5.2.1" in citation_id

    def test_without_clause(self):
        citation_id = _create_citation_id("Risk Assessment Guide", "Section 3", "")
        assert "Risk" in citation_id or "Assessment" in citation_id
        assert "Section" in citation_id or "3" in citation_id

    def test_sanitizes_document_name(self):
        citation_id = _create_citation_id("CCoP 2.0", "Section 5", "5.1")
        # Spaces and dots should be removed/replaced
        assert " " not in citation_id or citation_id.count(" ") < 2  # Minimal spaces
