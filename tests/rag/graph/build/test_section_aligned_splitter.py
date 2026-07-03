"""
Unit tests for SectionAlignedSplitter (Phase 10 — D-11 extraction unit).

No network/LLM/Neo4j — pure regex-driven text splitting, mirrors the
CLAUSE_PATTERN boundary detection already proven against Docling markdown
in clause_aware_chunker.py, but asserts SECTION-level (not clause-level)
chunk grouping.
"""

import pytest

from neo4j_graphrag.experimental.components.text_splitters.base import TextSplitter
from neo4j_graphrag.experimental.components.types import TextChunks

from rag.graph.build.section_aligned_splitter import SectionAlignedSplitter

FIXTURE_MARKDOWN = """## 5.3 Privileged Access Management

Organizations shall manage privileged access to critical systems.

## 5.3.1 Access Reviews

With respect to privileged accounts, the CIIO shall conduct periodic reviews.

## 5.3.2 Access Revocation

The CIIO shall revoke privileged access promptly upon role change.

## 5.4 Network Security

The CIIO shall segment operational technology networks from IT networks.
"""


class TestSectionAlignedSplitterContract:
    """Confirms the component satisfies neo4j-graphrag's text_splitter= contract."""

    def test_is_a_text_splitter_component(self):
        assert issubclass(SectionAlignedSplitter, TextSplitter)

    @pytest.mark.asyncio
    async def test_run_returns_text_chunks(self):
        splitter = SectionAlignedSplitter()
        result = await splitter.run(FIXTURE_MARKDOWN)
        assert isinstance(result, TextChunks)
        assert all(hasattr(chunk, "text") for chunk in result.chunks)


class TestSectionAlignedSplitterGrouping:
    """5.3/5.3.1/5.3.2/5.4 fixture: merge under top-level section, split at 5.4."""

    @pytest.mark.asyncio
    async def test_subclauses_group_under_top_level_section(self):
        splitter = SectionAlignedSplitter()
        result = await splitter.run(FIXTURE_MARKDOWN)

        # Exactly two section chunks: one for all of 5.3.*, one for 5.4.*
        assert len(result.chunks) == 2

    @pytest.mark.asyncio
    async def test_section_5_3_chunk_contains_all_subclauses(self):
        splitter = SectionAlignedSplitter()
        result = await splitter.run(FIXTURE_MARKDOWN)

        section_5_3_chunk = result.chunks[0]
        assert "5.3 Privileged Access Management" in section_5_3_chunk.text
        assert "5.3.1 Access Reviews" in section_5_3_chunk.text
        assert "5.3.2 Access Revocation" in section_5_3_chunk.text
        # Does NOT bleed into the next top-level section.
        assert "5.4 Network Security" not in section_5_3_chunk.text

    @pytest.mark.asyncio
    async def test_section_5_4_is_a_separate_chunk(self):
        splitter = SectionAlignedSplitter()
        result = await splitter.run(FIXTURE_MARKDOWN)

        section_5_4_chunk = result.chunks[1]
        assert "5.4 Network Security" in section_5_4_chunk.text
        assert "5.3" not in section_5_4_chunk.text

    @pytest.mark.asyncio
    async def test_sub_clause_boundary_does_not_create_new_chunk(self):
        """5.3.1(a)-style item-letter boundaries stay within the 5.3 section chunk."""
        markdown_with_item_letter = """## 5.3 Privileged Access Management

Organizations shall manage privileged access.

## 5.3.1(a) Multi-factor authentication

Implement multi-factor authentication for all privileged accounts.

## 5.4 Network Security

Segment OT networks from IT networks.
"""
        splitter = SectionAlignedSplitter()
        result = await splitter.run(markdown_with_item_letter)

        assert len(result.chunks) == 2
        assert "5.3.1(a)" in result.chunks[0].text
        assert "Multi-factor authentication" in result.chunks[0].text


class TestSectionAlignedSplitterPreamble:
    """Text preceding the first clause heading is kept as its own leading chunk."""

    @pytest.mark.asyncio
    async def test_preamble_becomes_leading_chunk(self):
        markdown = "This is front-matter text before any clause heading.\n\n" + FIXTURE_MARKDOWN
        splitter = SectionAlignedSplitter()
        result = await splitter.run(markdown)

        assert len(result.chunks) == 3
        assert "front-matter" in result.chunks[0].text

    @pytest.mark.asyncio
    async def test_no_preamble_yields_only_section_chunks(self):
        splitter = SectionAlignedSplitter()
        result = await splitter.run(FIXTURE_MARKDOWN)

        assert len(result.chunks) == 2
