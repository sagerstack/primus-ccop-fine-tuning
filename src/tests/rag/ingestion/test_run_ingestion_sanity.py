"""
Ingestion sanity tests — TOC coverage gate (SC #5).

Guards against silent section loss at ingestion time (bug #10 regression):
the _verify_toc_coverage helper must raise RuntimeError before the upload step
if any of the 12 expected CCoP 2.0 section-level chunks are absent.

Uses inline chunk fixtures only — no Docling, no Qdrant dependency.
"""

import pytest

from rag.ingestion.models import ChunkMetadata, CcopChunk
from rag.ingestion.run_ingestion import EXPECTED_CCOP_2_SECTIONS, _verify_toc_coverage


def _make_clause_chunk(section: str, clause: str, doc: str = "CCoP 2.0") -> CcopChunk:
    """Helper: build a minimal clause CcopChunk for testing."""
    metadata = ChunkMetadata(
        document_source=doc,
        section=section,
        clause=clause,
        citation_id=f"{doc}::{clause}",
        parent_path=f"Chapter 5 > Section {section} > {clause}",
        chapter="5",
        type="clause",
        parent_clause="",
    )
    return CcopChunk(id=f"{doc}::{clause}", text=f"Body of clause {clause}.", metadata=metadata)


def _make_all_sections_chunks() -> list:
    """Build one representative clause chunk per expected section."""
    chunks = []
    for section in EXPECTED_CCOP_2_SECTIONS:
        clause = f"{section}.1"
        chunks.append(_make_clause_chunk(section, clause))
    return chunks


class TestTocCoveragePassesWhenAllSectionsPresent:
    """Gate passes silently when all 12 sections have at least one clause chunk."""

    def test_passes_with_exactly_one_chunk_per_section(self):
        chunks = _make_all_sections_chunks()
        # Should not raise
        _verify_toc_coverage(chunks)

    def test_passes_with_multiple_chunks_per_section(self):
        """Multiple clauses per section (realistic) still passes."""
        chunks = []
        for section in EXPECTED_CCOP_2_SECTIONS:
            chunks.append(_make_clause_chunk(section, f"{section}.1"))
            chunks.append(_make_clause_chunk(section, f"{section}.2"))
        _verify_toc_coverage(chunks)

    def test_table_chunks_do_not_satisfy_gate(self):
        """Table chunks alone (no clause chunks) must NOT satisfy the gate."""
        # Build chunks for all sections but as type='table', not 'clause'
        chunks = []
        for section in EXPECTED_CCOP_2_SECTIONS:
            clause = f"{section}.1"
            metadata = ChunkMetadata(
                document_source="CCoP 2.0",
                section=section,
                clause=clause,
                citation_id=f"CCoP 2.0::{clause}::table::0",
                parent_path=f"Chapter 5 > Section {section} > {clause}",
                chapter="5",
                type="table",
                parent_clause=clause,
            )
            chunks.append(
                CcopChunk(
                    id=f"CCoP 2.0::{clause}::table::0",
                    text="| Col |\n| --- |\n| Val |",
                    metadata=metadata,
                )
            )
        with pytest.raises(RuntimeError):
            _verify_toc_coverage(chunks)

    def test_non_ccop_chunks_ignored(self):
        """Chunks from other documents don't affect the CCoP 2.0 gate."""
        chunks = _make_all_sections_chunks()
        # Add chunks from a different document — these must not confuse the gate
        for section in EXPECTED_CCOP_2_SECTIONS:
            chunks.append(_make_clause_chunk(section, f"{section}.1", doc="Auditing Guidelines"))
        _verify_toc_coverage(chunks)


class TestTocCoverageFailsWhenSectionMissing:
    """Gate raises RuntimeError listing missing sections."""

    def test_fails_when_5_3_missing(self):
        """Primary regression test: section 5.3 loss triggers loud failure."""
        chunks = [c for c in _make_all_sections_chunks() if c.metadata.section != "5.3"]
        with pytest.raises(RuntimeError) as exc_info:
            _verify_toc_coverage(chunks)
        assert "5.3" in str(exc_info.value)

    def test_fails_when_5_4_missing(self):
        chunks = [c for c in _make_all_sections_chunks() if c.metadata.section != "5.4"]
        with pytest.raises(RuntimeError) as exc_info:
            _verify_toc_coverage(chunks)
        assert "5.4" in str(exc_info.value)

    def test_error_message_lists_all_missing_sections(self):
        """Error message enumerates every missing section when multiple are absent."""
        chunks = [
            c for c in _make_all_sections_chunks()
            if c.metadata.section not in ("5.3", "5.7", "5.11")
        ]
        with pytest.raises(RuntimeError) as exc_info:
            _verify_toc_coverage(chunks)
        msg = str(exc_info.value)
        assert "5.3" in msg
        assert "5.7" in msg
        assert "5.11" in msg

    def test_fails_when_all_chunks_are_empty(self):
        with pytest.raises(RuntimeError):
            _verify_toc_coverage([])

    def test_fails_with_only_preamble_chunks(self):
        """Preamble chunks don't count as section evidence."""
        metadata = ChunkMetadata(
            document_source="CCoP 2.0",
            section="preamble",
            clause="",
            citation_id="CCoP 2.0::preamble",
            parent_path="Preamble",
            chapter="0",
        )
        preamble_chunk = CcopChunk(id="CCoP 2.0::preamble", text="Preamble text.", metadata=metadata)
        with pytest.raises(RuntimeError):
            _verify_toc_coverage([preamble_chunk])
