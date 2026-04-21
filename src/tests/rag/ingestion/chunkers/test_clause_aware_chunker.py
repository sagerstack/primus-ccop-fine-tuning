"""
Regression tests for clause_aware_chunker.py.

Guards two Phase 3.2 bug fixes:
  - Bug #9: <30-word merge rule caused cross-clause bleed (short clauses
    absorbed into next clause's chunk with wrong citation_id).
  - Bug #10: CLAUSE_PATTERN missed ## markdown heading prefix, so sections
    5.3/5.4 were never indexed as discrete chunks.

Uses inline markdown fixtures only — no Docling dependency.
"""

import pytest

from rag.ingestion.chunkers.clause_aware_chunker import (
    CLAUSE_PATTERN,
    chunk_by_clauses,
)


# ---------------------------------------------------------------------------
# CLAUSE_PATTERN regex tests
# ---------------------------------------------------------------------------


class TestClausePatternRegex:
    """Unit tests for the CLAUSE_PATTERN regex itself."""

    def test_bare_digit_clause_matched(self):
        """Existing bare-digit format still works after regex extension."""
        m = CLAUSE_PATTERN.search("5.2.2 The CIIO shall perform a review")
        assert m is not None
        assert m.group(1) == "5.2.2"
        assert "The CIIO shall perform a review" in m.group(2)

    def test_hashed_section_heading_matched(self):
        """## X.Y section headings (51 in CCoP 2.0) are now captured."""
        m = CLAUSE_PATTERN.search("## 5.3 Privileged Access Management")
        assert m is not None
        assert m.group(1) == "5.3"
        assert m.group(2) == "Privileged Access Management"

    def test_hashed_clause_heading_matched(self):
        """## X.Y.Z clause headings are now captured."""
        m = CLAUSE_PATTERN.search(
            "## 5.3.1 With respect to privileged accounts, the CIIO shall:"
        )
        assert m is not None
        assert m.group(1) == "5.3.1"

    def test_item_letter_boundary_recognized(self):
        """Item-letter notation X.Y.Z(c) is captured when present as a heading."""
        m = CLAUSE_PATTERN.search(
            "5.3.1(c) Implement multi-factor authentication"
        )
        assert m is not None
        assert m.group(1) == "5.3.1(c)"
        assert "multi-factor" in m.group(2)

    def test_plain_text_not_matched(self):
        """Non-clause lines are not matched."""
        assert CLAUSE_PATTERN.search("Privileged accounts are prime targets") is None
        assert CLAUSE_PATTERN.search("- (a) Ensure that privileged access") is None
        assert CLAUSE_PATTERN.search("This is a paragraph.") is None


# ---------------------------------------------------------------------------
# chunk_by_clauses behavioural tests
# ---------------------------------------------------------------------------


class TestItemLetterBoundary:
    """item-letter notation produces a chunk when used as a heading."""

    def test_item_letter_boundary_recognized(self):
        markdown = (
            "5.3.1(c) Implement multi-factor authentication\n\n"
            "body text about MFA requirements"
        )
        chunks = chunk_by_clauses(markdown, "TestDoc")
        assert len(chunks) >= 1
        mfa_chunks = [c for c in chunks if c.metadata.clause.startswith("5.3.1")]
        assert len(mfa_chunks) >= 1
        assert "multi-factor" in mfa_chunks[0].text


class TestNoCrossClauseBleed:
    """
    Bug #9 regression: 5.2.2 chunk must not contain text from 5.3.

    Before the fix the <30-word merge rule accumulated short clauses into
    a merge_buffer. When a subsequent clause exceeded 30 words the buffer
    was flushed *then* the new clause was appended — but the buffer still
    held text from a different clause number. This produced chunks whose
    citation_id pointed to one clause while their body contained text from
    the next clause.
    """

    MARKDOWN = (
        "5.2.2 Account Review\n\n"
        "Short body.\n\n"
        "## 5.3 Privileged Access Management\n\n"
        "Longer body here with enough words to demonstrate the bleed "
        "that previously occurred when the merge buffer was flushed."
    )

    def test_two_distinct_chunks_emitted(self):
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        clauses = [c.metadata.clause for c in chunks]
        assert "5.2.2" in clauses, "5.2.2 chunk missing"
        assert "5.3" in clauses, "5.3 chunk missing"

    def test_5_2_2_chunk_does_not_contain_privileged_access_management(self):
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        chunk_522 = next(c for c in chunks if c.metadata.clause == "5.2.2")
        assert "Privileged Access Management" not in chunk_522.text, (
            "5.2.2 chunk contains 5.3 text — cross-clause bleed detected"
        )

    def test_5_3_chunk_contains_its_own_body(self):
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        chunk_53 = next(c for c in chunks if c.metadata.clause == "5.3")
        assert "Privileged Access Management" in chunk_53.text


class TestShortClauseNotDropped:
    """
    Bug #9 regression: short clause bodies (<30 words) must not be dropped.

    Before the fix, the <30-word merge rule buffered such clauses indefinitely
    or appended them to the wrong citation chunk.
    """

    MARKDOWN = (
        "5.2.1 Short body\n\n"
        "Ten words total here so this is small."
    )

    def test_short_clause_emits_chunk(self):
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        clauses = [c.metadata.clause for c in chunks]
        assert "5.2.1" in clauses, (
            "Short clause (< 30 words) was dropped — merge rule still active"
        )

    def test_short_clause_text_preserved(self):
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        chunk = next(c for c in chunks if c.metadata.clause == "5.2.1")
        assert "Ten words total here" in chunk.text


class TestSection53ProducesDiscreteChunks:
    """
    Bug #10 regression: Docling ## headings now produce distinct chunks.

    This fixture mirrors the exact structure found in CCoP---Second-Edition_
    Revision-One.pdf as emitted by Docling's Classic pipeline.
    """

    MARKDOWN = (
        "5.2.2 Account Review\n\n"
        "The CIIO shall perform a review of all accounts that have access to the CII. "
        "The purpose of this review is to ensure that privileges are up-to-date.\n\n"
        "## 5.3 Privileged Access Management\n\n"
        "Privileged accounts are prime targets for malicious exploitation.\n\n"
        "## 5.3.1 With respect to privileged accounts, the CIIO shall:\n\n"
        "- (a) Ensure that privileged access is granted only to selected accounts;\n"
        "- (b) Maintain an updated inventory of privileged accounts;\n"
        "- (c) Implement multi-factor authentication where privileged accounts are used;\n"
    )

    def test_5_3_chunk_exists(self):
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        clauses = [c.metadata.clause for c in chunks]
        assert "5.3" in clauses, "5.3 chunk not emitted — ## heading still missed"

    def test_5_3_1_chunk_exists(self):
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        clauses = [c.metadata.clause for c in chunks]
        assert "5.3.1" in clauses, "5.3.1 chunk not emitted — ## heading still missed"

    def test_5_3_1_body_contains_item_letters(self):
        """Item-letter sub-items remain embedded in parent clause body per CONTEXT.md."""
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        chunk_531 = next(c for c in chunks if c.metadata.clause == "5.3.1")
        assert "(a)" in chunk_531.text
        assert "(b)" in chunk_531.text
        assert "(c)" in chunk_531.text

    def test_5_3_1_contains_mfa_text(self):
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        chunk_531 = next(c for c in chunks if c.metadata.clause == "5.3.1")
        assert "multi-factor authentication" in chunk_531.text

    def test_5_2_2_does_not_bleed_into_5_3(self):
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        chunk_522 = next(c for c in chunks if c.metadata.clause == "5.2.2")
        assert "Privileged Access Management" not in chunk_522.text
        assert "5.3.1" not in chunk_522.text
