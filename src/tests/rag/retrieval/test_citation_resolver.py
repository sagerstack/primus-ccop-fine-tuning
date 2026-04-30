"""
Tests for citation parsing, resolution, and formatting.

Covers the single `**Sources:**` markdown citation footer the model is
instructed to emit, including kind tagging (always "primary"), dedup,
format permissiveness, and the formatter's pass-through behavior.

History note: the resolver previously parsed three blocks
(**Sources:** / **Cross-references:** / **Other Sources:**). That design
was reverted because it produced citations-only degenerate responses.
The single-block format is the current contract.
"""

from langchain_core.documents import Document

from rag.citations.formatter import (
    format_model_only_response,
    format_response_with_citations,
)
from rag.citations.resolver import (
    KIND_PRIMARY,
    Citation,
    build_citations_from_state,
    extract_citation_ids,
    parse_citations,
    resolve_citations,
)


class TestParseCitations:
    """parse_citations: kind-tagged extraction from the **Sources:** footer."""

    def test_basic_sources_block(self):
        generation = """Body prose...

**Sources:**
CCoP 2.0: 5.3.1
Cybersecurity Act 2018: Section 11(7)
NIST CSF: PR.AC-1"""

        citations = parse_citations(generation)
        assert len(citations) == 3
        assert citations[0]["kind"] == KIND_PRIMARY
        assert citations[0]["document"] == "CCoP 2.0"
        assert citations[0]["clause"] == "5.3.1"
        assert citations[1]["document"] == "Cybersecurity Act 2018"
        assert citations[1]["clause"] == "Section 11(7)"
        assert citations[2]["document"] == "NIST CSF"
        assert citations[2]["clause"] == "PR.AC-1"

    def test_all_citations_tagged_primary(self):
        # Single-block design: kind is always "primary". Document attribution
        # happens via document name in the entry, not via block placement.
        generation = """**Sources:**
CCoP 2.0: 5.15.1
Cybersecurity Act 2018: Section 11(7)
ISO 27001: A.5.15"""
        citations = parse_citations(generation)
        assert all(c["kind"] == KIND_PRIMARY for c in citations)

    def test_no_footer_returns_empty(self):
        assert parse_citations("Just prose without any footer.") == []

    def test_empty_input_returns_empty(self):
        assert parse_citations("") == []

    def test_dedup_within_block(self):
        generation = """**Sources:**
CCoP 2.0: 5.3.1
CCoP 2.0: 5.3.1
CCoP 2.0: 5.3.2"""
        citations = parse_citations(generation)
        assert len(citations) == 2
        assert citations[0]["citation_id"] == "CCoP 2.0::5.3.1"
        assert citations[1]["citation_id"] == "CCoP 2.0::5.3.2"

    def test_marker_case_insensitive(self):
        generation = "body\n**SOURCES**\nCCoP 2.0: 1.1"
        citations = parse_citations(generation)
        assert len(citations) == 1
        assert citations[0]["citation_id"] == "CCoP 2.0::1.1"

    def test_marker_bare_sources(self):
        # Permissive marker: also accepts plain "Sources:" without bold
        generation = "body\nSources:\nCCoP 2.0: 1.1"
        citations = parse_citations(generation)
        assert len(citations) == 1

    def test_skip_lines_without_colon(self):
        generation = """**Sources:**
CCoP 2.0: 5.3.1
not a colon line
: missing doc
CCoP 2.0:
"""
        citations = parse_citations(generation)
        assert len(citations) == 1
        assert citations[0]["citation_id"] == "CCoP 2.0::5.3.1"


class TestExtractCitationIds:
    """extract_citation_ids: backward-compat flat ID list."""

    def test_basic(self):
        generation = "body...\n**Sources:**\nCCoP 2.0: 5.3.1"
        assert extract_citation_ids(generation) == ["CCoP 2.0::5.3.1"]

    def test_multiple_entries(self):
        generation = """**Sources:**
CCoP 2.0: 5.3.1
NIST CSF: PR.AC-1"""
        assert extract_citation_ids(generation) == [
            "CCoP 2.0::5.3.1",
            "NIST CSF::PR.AC-1",
        ]

    def test_no_footer(self):
        assert extract_citation_ids("Just prose, no footer.") == []

    def test_empty(self):
        assert extract_citation_ids("") == []

    def test_dedup(self):
        generation = """**Sources:**
CCoP 2.0: 5.3.1
CCoP 2.0: 5.3.1
CCoP 2.0: 5.3.2"""
        assert extract_citation_ids(generation) == [
            "CCoP 2.0::5.3.1",
            "CCoP 2.0::5.3.2",
        ]


class TestResolveCitations:
    """resolve_citations: legacy entrypoint — all declarations emitted,
    enriched when matched in retrieved set, parsed-only when unmatched."""

    def _doc(self, cid: str, doc: str = "CCoP 2.0", clause: str = "5.1",
             section: str = "5", document_type: str = "standard") -> Document:
        return Document(
            page_content="content",
            metadata={
                "citation_id": cid,
                "document_source": doc,
                "section": section,
                "clause": clause,
                "document_type": document_type,
            },
        )

    def test_matched_citation_enriched(self):
        retrieved = [self._doc("CCoP 2.0::5.1")]
        resolved = resolve_citations(["CCoP 2.0::5.1"], retrieved)
        assert len(resolved) == 1
        assert resolved[0]["section"] == "5"
        assert resolved[0]["clause"] == "5.1"
        assert resolved[0]["document_type"] == "standard"

    def test_unmatched_citation_still_emitted(self):
        # Pure-parser semantics: unmatched citations still appear with empty
        # enrichment fields.
        retrieved = [self._doc("CCoP 2.0::5.1")]
        resolved = resolve_citations(["CCoP 2.0::99.99.99"], retrieved)
        assert len(resolved) == 1
        assert resolved[0]["citation_id"] == "CCoP 2.0::99.99.99"
        assert resolved[0]["document"] == "CCoP 2.0"
        assert resolved[0]["clause"] == "99.99.99"
        assert resolved[0]["section"] == ""
        assert resolved[0]["document_type"] == ""

    def test_empty_documents_returns_parsed_only(self):
        resolved = resolve_citations(["CCoP 2.0::5.1"], [])
        assert len(resolved) == 1
        assert resolved[0]["citation_id"] == "CCoP 2.0::5.1"
        assert resolved[0]["section"] == ""

    def test_empty_citation_ids(self):
        retrieved = [self._doc("CCoP 2.0::5.1")]
        assert resolve_citations([], retrieved) == []

    def test_dedup(self):
        retrieved = [self._doc("CCoP 2.0::5.1")]
        resolved = resolve_citations(
            ["CCoP 2.0::5.1", "CCoP 2.0::5.1", "CCoP 2.0::5.2"], retrieved,
        )
        assert len(resolved) == 2

    def test_kind_always_primary(self):
        retrieved = [self._doc("CCoP 2.0::5.1")]
        resolved = resolve_citations(
            ["CCoP 2.0::5.1", "External::1.0"], retrieved,
        )
        for c in resolved:
            assert c["kind"] == KIND_PRIMARY


class TestBuildCitationsFromState:
    """build_citations_from_state: graph-state convenience wrapper using
    parse_citations under the hood."""

    def test_extracts_block_from_state(self):
        state = {
            "generation": """body

**Sources:**
CCoP 2.0: 1.1
NIST CSF: PR.AC-1"""
        }
        citations = build_citations_from_state(state)
        assert len(citations) == 2
        assert all(c["kind"] == KIND_PRIMARY for c in citations)

    def test_empty_state_returns_empty(self):
        assert build_citations_from_state({}) == []
        assert build_citations_from_state({"generation": ""}) == []


class TestFormatResponseWithCitations:
    """Pass-through formatter: model's **Sources:** block preserved verbatim."""

    def test_passes_through_unchanged(self):
        generation = """Answer body.

**Sources:**
CCoP 2.0: 5.3.1"""
        # Citations argument is accepted but unused for rendering — the model
        # owns its own footer now.
        formatted = format_response_with_citations(generation, [])
        assert formatted == generation.strip()

    def test_no_anchors_stripped(self):
        # Old `<c>...</c>` anchor stripping behavior is gone.
        generation = "First point and second point."
        formatted = format_response_with_citations(generation, [])
        assert formatted == generation.strip()

    def test_no_auto_built_references_block(self):
        # Old auto-built `References:` footer is gone.
        generation = "Plain response."
        citations: list[Citation] = [
            {
                "citation_id": "CCoP 2.0::5.1",
                "document": "CCoP 2.0",
                "section": "5",
                "clause": "5.1",
                "document_type": "standard",
                "kind": KIND_PRIMARY,
            }
        ]
        formatted = format_response_with_citations(generation, citations)
        assert "References:" not in formatted
        assert "[1]" not in formatted

    def test_empty_generation(self):
        assert format_response_with_citations("", []) == ""

    def test_strips_trailing_whitespace(self):
        generation = "Body text.   \n\n  "
        formatted = format_response_with_citations(generation, [])
        assert formatted == "Body text."


class TestFormatModelOnlyResponse:
    """Notice prepended to llm-only-mode responses (no retrieval grounding)."""

    def test_prepends_notice(self):
        formatted = format_model_only_response("Model output.")
        assert "[Note: This response is based on model knowledge only" in formatted
        assert "Model output." in formatted

    def test_no_references_section(self):
        formatted = format_model_only_response("Output.")
        assert "References:" not in formatted

    def test_empty_generation(self):
        assert format_model_only_response("") == ""
