"""
Regression tests for clause_aware_chunker.py (Phase 11, D-19/D-25.1).

Guards:
  - The 5.2 -> 5.3 section boundary (bug 2026-04-21 / Phase 3.2 fix) —
    sections 5.3/5.4 (and their .1 leaves) must each emit as their own
    discrete chunk, never glued onto a neighbor's tail.
  - Lettered sub-items ("- (a) ...", "- (b) ...", "- (c) ...") emitting as
    their OWN discrete, additive chunk (Phase 11 new requirement) — the
    parent clause chunk keeps its full body (including the lettered items)
    unchanged, exactly mirroring the existing table-chunk additive pattern.
  - No regression on the previously-documented list-item absorption cases
    (6.1.1, 8.2.5) or the no-merge emission discipline (bug #9: the <30-word
    merge rule that caused cross-clause bleed must never come back).

Uses inline markdown fixtures mirroring the exact structure Docling's
Classic pipeline emits for CCoP 2.0 (confirmed against the live re-ingested
corpus) — no live Docling/network dependency, so this suite runs in <1s.
"""

import re

from rag.ingestion.chunkers.clause_aware_chunker import (
    CLAUSE_PATTERN,
    ITEM_LETTER_PATTERN,
    chunk_by_clauses,
)


# ---------------------------------------------------------------------------
# CLAUSE_PATTERN / ITEM_LETTER_PATTERN regex unit tests
# ---------------------------------------------------------------------------


class TestClausePatternRegex:
    def test_bare_digit_clause_matched(self):
        m = CLAUSE_PATTERN.search("5.2.2 The CIIO shall perform a review")
        assert m is not None
        assert m.group(1) == "5.2.2"

    def test_hashed_section_heading_matched(self):
        m = CLAUSE_PATTERN.search("## 5.3 Privileged Access Management")
        assert m is not None
        assert m.group(1) == "5.3"
        assert m.group(2) == "Privileged Access Management"

    def test_hashed_clause_heading_matched(self):
        m = CLAUSE_PATTERN.search(
            "## 5.3.1 With respect to privileged accounts, the CIIO shall:"
        )
        assert m is not None
        assert m.group(1) == "5.3.1"

    def test_list_item_boundary_still_recognized_6_1_1(self):
        """Documented list-item absorption case (6.1.1) — no regression."""
        m = CLAUSE_PATTERN.search(
            "- 6.1.1 The CIIO shall generate, collect and store logs"
        )
        assert m is not None
        assert m.group(1) == "6.1.1"

    def test_list_item_boundary_still_recognized_8_2_5(self):
        """Documented list-item absorption case (8.2.5) — no regression."""
        m = CLAUSE_PATTERN.search("- 8.2.5 The CIIO shall conduct a review")
        assert m is not None
        assert m.group(1) == "8.2.5"

    def test_plain_text_not_matched(self):
        assert CLAUSE_PATTERN.search("Privileged accounts are prime targets") is None
        assert CLAUSE_PATTERN.search("This is a paragraph.") is None


class TestItemLetterPatternRegex:
    """Unit tests for the new ITEM_LETTER_PATTERN (Phase 11)."""

    def test_lettered_list_line_matched(self):
        m = ITEM_LETTER_PATTERN.match(
            "- (a) Ensure that privileged access is granted only to selected accounts;"
        )
        assert m is not None
        assert m.group(1) == "a"
        assert "Ensure that privileged access" in m.group(2)

    def test_non_lettered_list_line_not_matched(self):
        assert ITEM_LETTER_PATTERN.match("- Some other bullet without a letter") is None

    def test_plain_prose_not_matched(self):
        assert ITEM_LETTER_PATTERN.match("Privileged accounts are prime targets") is None


# ---------------------------------------------------------------------------
# chunk_by_clauses: 5.2 -> 5.3 section boundary + lettered sub-items
# ---------------------------------------------------------------------------


# Mirrors the exact structure Docling's Classic pipeline emits for CCoP 2.0
# section 5.2 -> 5.3 -> 5.3.1 -> 5.4 -> 5.4.1 (confirmed against the live
# re-ingested corpus).
CCOP_5_2_TO_5_4_MARKDOWN = (
    "5.2.2 Account Review\n\n"
    "The CIIO shall perform a review of all accounts that have access to the CII. "
    "The purpose of this review is to ensure that privileges are up-to-date.\n\n"
    "## 5.3 Privileged Access Management\n\n"
    "Privileged accounts are prime targets for malicious exploitation.\n\n"
    "## 5.3.1 With respect to privileged accounts, the CIIO shall:\n\n"
    "- (a) Ensure that privileged access is granted only to selected accounts "
    "authorised to have such access;\n"
    "- (b) Maintain an updated inventory of privileged accounts including "
    "details of the permissions and privileges assigned to each account;\n"
    "- (c) Implement multi-factor authentication where privileged accounts "
    "are used to access the CII; and\n"
    "- (d) Ensure that privileged access is initiated from a cybersecurity "
    "hardened environment.\n\n"
    "## 5.4 Trust Relationship Management\n\n"
    "Trust relationships between systems must be managed and reviewed.\n\n"
    "## 5.4.1 The CIIO shall review all trust relationships:\n\n"
    "- (a) Identify all trust relationships between the CII and other systems;\n"
    "- (b) Review trust relationships on a periodic basis.\n"
)


class TestSection52To54BoundaryProducesDiscreteChunks:
    """
    Bug 2026-04-21 regression: the 5.2 -> 5.3 section boundary (and its
    5.3.1/5.4/5.4.1 descendants) must each produce a discrete, independently
    retrievable chunk — never absorbed into a neighboring clause's tail.
    """

    def test_all_expected_clauses_present(self):
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        clauses = {c.metadata.clause for c in chunks}
        for expected in ("5.2.2", "5.3", "5.3.1", "5.4", "5.4.1"):
            assert expected in clauses, f"{expected} chunk not emitted"

    def test_5_2_2_does_not_bleed_into_5_3(self):
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        chunk_522 = next(c for c in chunks if c.metadata.clause == "5.2.2")
        assert "Privileged Access Management" not in chunk_522.text
        assert "Trust Relationship Management" not in chunk_522.text

    def test_5_3_chunk_contains_its_own_body(self):
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        chunk_53 = next(c for c in chunks if c.metadata.clause == "5.3")
        assert "Privileged Access Management" in chunk_53.text

    def test_5_4_chunk_contains_its_own_body(self):
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        chunk_54 = next(c for c in chunks if c.metadata.clause == "5.4")
        assert "Trust Relationship Management" in chunk_54.text

    def test_5_3_does_not_bleed_into_5_4(self):
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        chunk_531 = next(c for c in chunks if c.metadata.clause == "5.3.1")
        assert "Trust Relationship Management" not in chunk_531.text
        assert "5.4.1" not in chunk_531.text


class TestLetteredSubItemsEmitDiscreteChunks:
    """
    Phase 11 new requirement (D-19/D-25.1): lettered sub-items each emit as
    their own chunk carrying their own clause_id, additively (parent keeps
    its full body too).
    """

    def test_5_3_1_lettered_items_each_have_own_chunk(self):
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        clauses = {c.metadata.clause for c in chunks}
        for letter_id in ("5.3.1(a)", "5.3.1(b)", "5.3.1(c)", "5.3.1(d)"):
            assert letter_id in clauses, f"{letter_id} chunk not emitted"

    def test_5_4_1_lettered_items_each_have_own_chunk(self):
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        clauses = {c.metadata.clause for c in chunks}
        for letter_id in ("5.4.1(a)", "5.4.1(b)"):
            assert letter_id in clauses, f"{letter_id} chunk not emitted"

    def test_item_letter_chunk_carries_its_own_verbatim_text(self):
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        chunk_c = next(c for c in chunks if c.metadata.clause == "5.3.1(c)")
        assert "multi-factor authentication" in chunk_c.text

    def test_item_letter_chunk_does_not_contain_sibling_items(self):
        """Each item chunk must carry ONLY its own text, not a neighbor's."""
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        chunk_a = next(c for c in chunks if c.metadata.clause == "5.3.1(a)")
        assert "multi-factor authentication" not in chunk_a.text
        assert "Maintain an updated inventory" not in chunk_a.text

    def test_item_letter_chunk_parent_clause_field(self):
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        chunk_c = next(c for c in chunks if c.metadata.clause == "5.3.1(c)")
        assert chunk_c.metadata.parent_clause == "5.3.1"
        assert chunk_c.metadata.type == "clause"

    def test_item_letter_chunk_citation_id_format(self):
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        chunk_c = next(c for c in chunks if c.metadata.clause == "5.3.1(c)")
        assert chunk_c.metadata.citation_id == "CCoP 2.0::5.3.1(c)"

    def test_parent_clause_chunk_still_contains_all_lettered_items(self):
        """Additive, not a replacement — parent keeps its full body (backward compat)."""
        chunks = chunk_by_clauses(CCOP_5_2_TO_5_4_MARKDOWN, "CCoP 2.0")
        chunk_531 = next(
            c
            for c in chunks
            if c.metadata.clause == "5.3.1" and c.metadata.type == "clause"
            and not c.metadata.parent_clause
        )
        assert "(a) Ensure that privileged access" in chunk_531.text
        assert "(d) Ensure that privileged access is initiated" in chunk_531.text


# ---------------------------------------------------------------------------
# No-merge emission discipline (bug #9 guard — must never regress)
# ---------------------------------------------------------------------------


class TestNoMergeRuleReintroduced:
    def test_short_clause_still_emits_its_own_chunk(self):
        """Bug #9 regression: short clause bodies (<30 words) must not be
        dropped or merged into a neighbor via a word-count buffer."""
        markdown = "5.2.1 Short body\n\nTen words total here so this is small.\n\n5.2.2 Next Clause\n\nMore text."
        chunks = chunk_by_clauses(markdown, "TestDoc")
        clauses = {c.metadata.clause for c in chunks}
        assert "5.2.1" in clauses
        assert "5.2.2" in clauses

    def test_no_merge_buffer_symbol_in_source(self):
        """
        Static guard: the merge-rule branch (a live `merge_buffer` variable /
        word-count conditional) must never be reintroduced. Matches only
        active code shapes, not historical-bug references in comments/
        docstrings (which legitimately document why the rule was removed).
        """
        import inspect

        import rag.ingestion.chunkers.clause_aware_chunker as chunker_module

        source = inspect.getsource(chunker_module)
        assert "merge_buffer" not in source
        assert not re.search(r"if\s+\w+\s*<\s*30", source)


# ---------------------------------------------------------------------------
# Table chunks unaffected by the item-letter extraction (co-existence check)
# ---------------------------------------------------------------------------


class TestItemLetterExtractionDoesNotBreakTableChunks:
    MARKDOWN = (
        "## 5.3.1 Enumeration Matrix\n\n"
        "The following matrix lists privileged account types:\n\n"
        "| Account Type | Scope | MFA Required |\n"
        "| --- | --- | --- |\n"
        "| Domain Admin | Enterprise | Yes |\n"
        "| Service Account | Application | Yes |\n\n"
        "- (a) Ensure the matrix is reviewed annually;\n"
        "- (b) Update the matrix when new account types are introduced.\n"
    )

    def test_table_chunk_and_item_letter_chunks_coexist(self):
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        table_chunks = [c for c in chunks if c.metadata.type == "table"]
        item_chunks = [
            c for c in chunks if c.metadata.clause in ("5.3.1(a)", "5.3.1(b)")
        ]
        assert len(table_chunks) >= 1
        assert len(item_chunks) == 2

    def test_table_text_not_absorbed_into_item_chunks(self):
        chunks = chunk_by_clauses(self.MARKDOWN, "TestDoc")
        chunk_a = next(c for c in chunks if c.metadata.clause == "5.3.1(a)")
        assert "Domain Admin" not in chunk_a.text
