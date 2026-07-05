"""
Step-0 Clause-Text Alignment (Phase 11 -- D-13 payload half / D-19 guard).

Attaches verbatim provision text to every seeded `:Clause` node -- the
concrete realization of D-06/D-07's "the clause is only the CU's source
semantic unit + verbatim text carrier + citation anchor". A Compliance Unit
(11-04) can only hard-link text that its source clause node itself carries,
so this MUST run before Wave 3 mints CUs (D-13).

PRECONDITION (D-25 follow-through): the 883-node `:Clause` backbone
(skeleton + `HAS_CHILD` hierarchy + `function_type`) must already be seeded
via `ccop-eval graph seed-clauses` (`rag.graph.ontology.clause_seeder.
ClauseSeeder`) -- Wave 0's `graph build --drop` wipes it. Re-seeding is
idempotent and is run as an explicit first step by the CLI/plan action, NOT
by this module (this module only SETs a `text` property on EXISTING nodes;
it never MERGEs new ones -- D-06/D-07 keep skeleton-creation and
text-enrichment as separate, single-responsibility passes).

Resolution strategy (per `(clause_id, source_doc)` inventory entry), in
descending order of precision -- MUST agree with the 11-01 completeness
gate's coverage (`rag.ingestion.scripts.verify_clause_completeness`, D-19):

1. **Exact `clause` metadata match** -- `clause_aware_chunker.py` stamps the
   literal clause number (or item-composite id, e.g. "10.2.5(a)") onto each
   discrete chunk's `clause` payload field for CLAUSE_AWARE documents (CCoP
   2.0, CCoP Response to Feedback, Security By Design). This is the fast,
   unambiguous path covering the large majority of the 883 entries.
2. **Item-letter decomposition** ("10.2.5(a)" -> base "10.2.5" AND letter
   marker "(i)") -- mirrors `verify_clause_completeness._clause_resolves`;
   prefers a SINGLE chunk carrying both tokens, then falls back to
   whichever of the two independently-matching chunk sets is available (the
   gate's own decomposition check is cross-chunk/whole-document, so a
   same-chunk requirement alone could under-resolve relative to the gate).
3. **"section N" decomposition** (Cybersecurity Act 2018 inventory-label
   convention) -- a PRECISE body-start check (`_body_starts_with_number`)
   fires first (the Act's actual prose renders "N.--(1) ..." for the true
   clause N, so bare-number substring matching alone would fatally collide
   with subsection/cross-reference numbers like "(2)", "(7)" that appear in
   nearly every chunk); falls back to a generic boundary-aware scan
   (preferring the LONGEST match -- a merged/catch-all chunk is a safer bet
   than an unrelated short chunk that only coincidentally contains the bare
   token).
4. **Heading-token match** (`_heading_starts_with`) -- bare chapter ids in
   the SECTION_BASED guides (Auditing Guidelines, Threat Modelling Guide,
   Risk Assessment Guide render "## 7 COI AUDIT" / "## 8 TERMS AND
   DEFINITIONS" as a chunk's own first line).
5. **Generic boundary-aware substring match** (`KGInspector.
   _clause_id_appears`, reused -- Don't-Hand-Roll) -- the final catch-all
   (e.g. Cybersecurity Act "Part N" ids, which only ever appear embedded
   mid-chunk in a merged TOC/preamble blob, never as a chunk's own heading);
   prefers the LONGEST matching chunk for the same reason as (3).

Cypher discipline (T-09-12): `_SET_CLAUSE_TEXT_QUERY` below is a static
module-level string, parameterized via `$entries` -- no value is ever
spliced into query text via f-string/`.format()`.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

import neo4j
from qdrant_client import QdrantClient

from infrastructure.config.settings import Settings
from rag.graph.inspect.metrics import KGInspector
from rag.graph.ontology.clause_seeder import DEFAULT_CLAUSE_INVENTORY_PATH

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]

# Same two-line decomposition regexes as `verify_clause_completeness.py`
# (not imported -- rag.graph.ontology -> rag.ingestion.scripts would be a
# reverse-direction cross-package dependency; these are stable, well-
# understood literals, duplicated rather than imported per that module's own
# precedent).
_ITEM_SUFFIX_RE = re.compile(r"^(?P<base>.+)\((?P<letter>[a-z])\)$")
_SECTION_PREFIX_RE = re.compile(r"^section\s+(?P<num>.+)$", re.IGNORECASE)

# Static, parameterized Cypher (T-09-12) -- $entries is the only variable
# input, bound via session.run(..., entries=entries), never string-
# interpolated. Only SETs `text` on an EXISTING seeded :Clause node (MATCH,
# not MERGE) -- this module never creates the skeleton.
_SET_CLAUSE_TEXT_QUERY = """
UNWIND $entries AS entry
MATCH (c:Clause {clause_id: entry.clause_id, source_doc: entry.source_doc})
SET c.text = entry.text
""".strip()

_COUNT_TEXTLESS_QUERY = """
MATCH (c:Clause)
WHERE c.text IS NULL OR c.text = ''
RETURN count(c) AS c
""".strip()


@dataclass
class UnalignedClause:
    """One clause_inventory.json entry with no resolvable verbatim body."""

    clause_id: str
    source_doc: str


@dataclass
class AlignStats:
    """Aggregate statistics for a clause-text-alignment run (T-09-08: reported, never swallowed)."""

    entries_total: int = 0
    aligned: int = 0
    unaligned: list[UnalignedClause] = field(default_factory=list)
    # Authoritative post-write re-query -- never trusted from in-process
    # counters (T-09-08).
    textless_nodes: int = 0


def _heading_starts_with(text: str, token: str) -> bool:
    """
    True if `text`'s first line is a markdown heading ("#"+) whose content,
    after stripping the "#" marker(s) and leading whitespace, starts with
    `token` as a whole word/number (boundary-aware). Covers the
    SECTION_BASED guides' bare-chapter chunks, e.g. "## 7 COI AUDIT" -> "7".
    """
    first_line = text.split("\n", 1)[0]
    heading = first_line.lstrip("#").strip()
    if not heading:
        return False
    pattern = re.compile(r"^" + re.escape(token) + r"(?![A-Za-z0-9])")
    return bool(pattern.match(heading))


def _body_starts_with_number(text: str, bare_number: str) -> bool:
    """
    True if `text`, with any leading markdown heading lines ("#"+) removed,
    starts with `bare_number` immediately followed by a period -- the
    Cybersecurity Act 2018's actual clause-numbering convention
    ("7.--(1) The Commissioner may...", never "section 7"). Precise enough
    to distinguish the true clause N from an unrelated cross-reference
    number appearing elsewhere in the same or another chunk.
    """
    body_lines = [line for line in text.split("\n") if not line.strip().startswith("#")]
    body = "\n".join(body_lines).strip()
    if not body:
        return False
    pattern = re.compile(r"^" + re.escape(bare_number) + r"\.")
    return bool(pattern.match(body))


class ClauseTextAligner:
    """
    Step-0 clause-text alignment (D-13/D-19): resolves each
    `clause_inventory.json` entry's verbatim body from the re-ingested
    Qdrant corpus and writes it to the corresponding seeded `:Clause` node's
    `text` property.

    PRECONDITION: the `:Clause` backbone must already be seeded (`ccop-eval
    graph seed-clauses` / `ClauseSeeder.seed()`) -- this module only SETs a
    property on EXISTING nodes, it never MERGEs new ones.
    """

    def __init__(
        self,
        settings: Settings,
        driver: Optional["neo4j.Driver"] = None,
        qdrant_client: Optional["QdrantClient"] = None,
        inventory_path: PathLike = DEFAULT_CLAUSE_INVENTORY_PATH,
        collection_name: Optional[str] = None,
    ) -> None:
        self.settings = settings
        self.driver = driver or neo4j.GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        self._owns_qdrant_client = qdrant_client is None
        self.qdrant_client = qdrant_client or QdrantClient(url=settings.qdrant_url)
        self.collection_name = collection_name or settings.qdrant_collection_name
        if not self.collection_name:
            raise ValueError(
                "No Qdrant collection configured (CCOP_QDRANT_COLLECTION_NAME unset)"
            )
        self.inventory_path = Path(inventory_path)

    def close(self) -> None:
        if self._owns_qdrant_client:
            self.qdrant_client.close()

    def load_entries(self) -> list[dict[str, str]]:
        payload = json.loads(self.inventory_path.read_text())
        return payload["entries"]

    def _load_chunks_by_doc(self) -> dict[str, list[dict[str, str]]]:
        """
        Scroll every point in the configured Qdrant collection and group
        `{text, clause}` records by `document_source` -- mirrors
        `verify_clause_completeness._build_haystacks`'s per-document
        grouping (D-08 namespacing: a clause_id is not globally unique
        across the 7 source docs, so resolution must never cross a
        document boundary).
        """
        chunks_by_doc: dict[str, list[dict[str, str]]] = {}
        offset = None
        while True:
            records, offset = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=500,
                offset=offset,
                with_payload=["text", "document_source", "clause"],
                with_vectors=False,
            )
            for record in records:
                payload = record.payload or {}
                doc = payload.get("document_source", "")
                text = payload.get("text", "") or ""
                clause = payload.get("clause", "") or ""
                if not text:
                    continue
                chunks_by_doc.setdefault(doc, []).append({"text": text, "clause": clause})
            if offset is None:
                break
        return chunks_by_doc

    @staticmethod
    def _resolve_text(clause_id: str, doc_chunks: list[dict[str, str]]) -> Optional[str]:
        """Resolve `clause_id`'s verbatim body from this source_doc's chunks (see module docstring, tiers 1-5)."""
        # Tier 1: exact `clause` metadata match (fast, unambiguous).
        exact = [c["text"] for c in doc_chunks if c["clause"] == clause_id]
        if exact:
            return min(exact, key=len)

        lowered = [(c["text"], c["text"].lower()) for c in doc_chunks]

        # Tier 2: item-letter composite ids ("10.2.5(a)").
        item_match = _ITEM_SUFFIX_RE.match(clause_id)
        if item_match:
            base, letter = item_match.group("base"), item_match.group("letter")
            marker = f"({letter})"
            same_chunk = [
                text
                for text, low in lowered
                if KGInspector._clause_id_appears(base, low)
                and KGInspector._clause_id_appears(marker, low)
            ]
            if same_chunk:
                return min(same_chunk, key=len)
            letter_only = [
                text for text, low in lowered if KGInspector._clause_id_appears(marker, low)
            ]
            if letter_only:
                return min(letter_only, key=len)
            base_only = [
                text for text, low in lowered if KGInspector._clause_id_appears(base, low)
            ]
            if base_only:
                return min(base_only, key=len)
            return None

        # Tier 3: "section N" convention (Cybersecurity Act 2018).
        section_match = _SECTION_PREFIX_RE.match(clause_id)
        if section_match:
            bare = section_match.group("num")
            precise = [text for text, _ in lowered if _body_starts_with_number(text, bare)]
            if precise:
                return min(precise, key=len)
            direct = [text for text, low in lowered if KGInspector._clause_id_appears(bare, low)]
            if direct:
                return max(direct, key=len)
            return None

        # Tier 4: heading-token match (bare chapter ids, section-based guides).
        heading = [text for text, _ in lowered if _heading_starts_with(text, clause_id)]
        if heading:
            return min(heading, key=len)

        # Tier 5: generic boundary-aware substring match (final catch-all).
        direct = [
            text for text, low in lowered if KGInspector._clause_id_appears(clause_id, low)
        ]
        if direct:
            return max(direct, key=len)

        return None

    def align(self) -> AlignStats:
        """
        Resolve + write verbatim text for every inventory entry, then report
        authoritative post-write counts re-queried from Neo4j (never
        trusted from in-process counters -- T-09-08).
        """
        entries = self.load_entries()
        chunks_by_doc = self._load_chunks_by_doc()

        stats = AlignStats(entries_total=len(entries))
        to_write: list[dict[str, str]] = []

        for entry in entries:
            clause_id = entry["clause_id"]
            source_doc = entry["source_doc"]
            doc_chunks = chunks_by_doc.get(source_doc, [])
            text = self._resolve_text(clause_id, doc_chunks)
            if text:
                to_write.append(
                    {"clause_id": clause_id, "source_doc": source_doc, "text": text}
                )
                stats.aligned += 1
            else:
                stats.unaligned.append(
                    UnalignedClause(clause_id=clause_id, source_doc=source_doc)
                )

        if to_write:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                session.run(_SET_CLAUSE_TEXT_QUERY, entries=to_write)

        self._accumulate_stats(stats)
        return stats

    def _accumulate_stats(self, stats: AlignStats) -> None:
        """Query Neo4j directly for the authoritative post-write textless-node count (T-09-08)."""
        try:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                stats.textless_nodes = session.run(_COUNT_TEXTLESS_QUERY).single()["c"]
        except Exception as e:
            logger.warning(f"Could not query textless-node stats after alignment: {e}")


__all__: list[str] = [
    "ClauseTextAligner",
    "AlignStats",
    "UnalignedClause",
]
