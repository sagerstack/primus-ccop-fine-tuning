"""
Section-Aligned Extraction Splitter (Phase 10 — D-11 extraction unit)

Implements the "extract-large" half of D-11's chunking decouple: a coarse,
structure-aware neo4j-graphrag `TextSplitter` component that groups every
clause under one top-level section number (e.g. "5.3", "5.3.1", "5.3.2")
into a SINGLE extraction chunk, splitting only at the next top-level section
boundary ("5.4").

This deliberately does NOT reuse `clause_aware_chunker.chunk_by_clauses`
output directly — that produces clause-granularity chunks, which starve
entity/relationship extraction (D-05/D-20 anti-pattern; Phase 9's 4000-char
FixedSizeSplitter is already coarser than clause-level and still under-recalls
without gleaning). Instead this module reuses the SAME proven boundary-regex
(`clause_aware_chunker.CLAUSE_PATTERN`) but merges sub-clauses under their
top-level section before handing chunks to the extraction LLM.

Retrieval stays fine-grained at the seeded clause node (10-05) — this
splitter only controls what the extraction LLM sees per call, not what gets
retrieved at query time.

Boundaries are parsed fresh from the Docling markdown text passed in at
`.run(text)` time — Qdrant `ChunkMetadata` (section/subsection/parent_path)
is NOT available on the raw corpus text `corpus_source.py` feeds into the
GraphRAG build pipeline (confirmed in 10-RESEARCH.md Q3).
"""

import re

from pydantic import validate_call

from neo4j_graphrag.experimental.components.text_splitters.base import TextSplitter
from neo4j_graphrag.experimental.components.types import TextChunk, TextChunks

from rag.ingestion.chunkers.clause_aware_chunker import CLAUSE_PATTERN

# Strips a trailing item-letter suffix (e.g. "(a)") so "5.3.1(a)" and "5.3.1"
# resolve to the same numeric clause id before deriving the section key.
_ITEM_LETTER_SUFFIX = re.compile(r"\([a-z]\)$")

# Sentinel section key for any text appearing before the first clause heading
# (front-matter / preamble) — kept as its own leading chunk rather than
# merged into the first real section.
_PREAMBLE_SECTION_KEY = "__preamble__"


def _section_key(clause_number: str) -> str:
    """
    Derive the TOP-LEVEL section key for a clause number.

    Splits only at the top-level section boundary (chapter.section), never
    at sub-clause granularity:
        "5.3"        -> "5.3"
        "5.3.1"      -> "5.3"
        "5.3.2"      -> "5.3"
        "5.3.1(a)"   -> "5.3"   (item-letter suffix stripped first)
        "5.4"        -> "5.4"
        "5"          -> "5"     (bare chapter number, no sub-parts)
    """
    numeric = _ITEM_LETTER_SUFFIX.sub("", clause_number)
    parts = numeric.split(".")
    if len(parts) >= 2:
        return ".".join(parts[:2])
    return parts[0]


class SectionAlignedSplitter(TextSplitter):
    """
    Coarse, structure-aware `text_splitter=` component for the ontology KG
    build pipeline (D-11 extraction unit).

    Groups multiple clauses under one top-level section boundary into a
    single extraction chunk — NOT clause-granularity (extraction-starving,
    D-05/D-20 forbidden) and NOT Phase 9's arbitrary 4000-char fixed-size
    splitting (structure-blind).

    Satisfies neo4j-graphrag's `TextSplitter`/`Component` contract: an
    async `.run(text) -> TextChunks` method, injectable as
    `SimpleKGPipeline(..., text_splitter=SectionAlignedSplitter(), ...)`.
    """

    @validate_call
    async def run(self, text: str) -> TextChunks:
        """
        Split `text` into section-aligned chunks.

        Args:
            text: Full per-document Docling markdown (unchunked corpus text,
                same input `EmergentKGBuilder`/`corpus_source.py` already
                consume — D-04 constant input across Phase 9/10).

        Returns:
            TextChunks: one chunk per top-level section (plus a leading
            preamble chunk when front-matter precedes the first clause
            heading).
        """
        parts = CLAUSE_PATTERN.split(text)

        # sections: ordered list of (section_key, [block_text, ...])
        sections: list[tuple[str, list[str]]] = []

        preamble = parts[0].strip() if parts else ""
        if preamble:
            sections.append((_PREAMBLE_SECTION_KEY, [preamble]))

        # Groups of 3: clause_number, clause_heading, clause_content —
        # identical parsing shape to clause_aware_chunker.chunk_by_clauses,
        # but grouped by top-level section instead of emitted per-clause.
        i = 1
        while i < len(parts) - 2:
            clause_number = parts[i].strip()
            clause_heading = parts[i + 1].strip()
            clause_content = parts[i + 2].strip() if i + 2 < len(parts) else ""

            block_text = f"{clause_number} {clause_heading}\n\n{clause_content}".strip()
            section_key = _section_key(clause_number)

            if sections and sections[-1][0] == section_key:
                sections[-1][1].append(block_text)
            else:
                sections.append((section_key, [block_text]))

            i += 3

        chunks = [
            TextChunk(text="\n\n".join(blocks), index=idx)
            for idx, (_key, blocks) in enumerate(sections)
        ]
        return TextChunks(chunks=chunks)


__all__: list[str] = ["SectionAlignedSplitter"]
