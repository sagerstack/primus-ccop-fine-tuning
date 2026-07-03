"""
Deterministic Clause-Backbone Seeder (Phase 10 — D-10/D-09/D-11).

MERGE-seeds `:Clause` nodes from `clause_inventory.json` (committed fixture,
IDs + source_doc only, NO titles/text — Phase 3.2 clause-extraction pass).
There is no LLM call anywhere in this module: every `:Clause` node is either
a real `clause_id` already present in the fixture, or is not created at all.
This is the D-10 fix for the Phase 9 D-06 anti-pattern (hallucinated/unnamed
instances) applied specifically to the regulatory-structure layer (D-08).

Node identity (MERGE key) = `(clause_id, source_doc)` composite — `clause_id`
alone is NOT globally unique across the 7 source documents (e.g. "1" is the
first top-level clause of six different docs). Verified against the live
fixture: every `(clause_id, source_doc)` pair is unique (0 duplicates).

Parent-child hierarchy is derived purely from the `clause_id` string
structure, reusing `rag.ingestion.chunkers.clause_aware_chunker`'s
dot-splitting rule (`_extract_section`/`_build_parent_path`, D-10: Title ->
Chapter -> Article -> Item), extended to also strip a trailing `"(x)"`
item-letter suffix — the fixture's audit pass introduced synthetic
item-letter clause_ids like `"10.2.5(a)"` that the un-extended dot-rsplit
would mis-parent (`"10.2.5(a)".rsplit(".", 1)` yields `"10.2"`, skipping the
`"10.2.5"` level). See `_derive_parent` for the extension. Both ends of a
`:HAS_CHILD` edge share the same `source_doc`; clauses with no dot and no
item-letter suffix (e.g. `"1"`, `"Part 1"`, `"section 5"`) are hierarchy
roots (Title/Chapter level) and receive no parent edge.

function_type tagging (D-09): `ontology_config.json`'s `function_type_tags`
list names the three tags (ScopeClause/ControlClause/DefinitionClause) but
carries NO clause-level mapping — `clause_inventory.json` has no titles to
classify against, and the locked ontology config doesn't encode a per-clause
mapping either. This module encodes ONE static, source-verified mapping: the
CCoP 2.0 official Table of Contents (`ccop-official/CCoP---Second-Edition_
Revision-One.pdf`, pages 2-3 — committed, versioned document structure, not
a guess) shows Chapter 1 "Preliminary" is the applicability/scope chapter
(matches B01's grounding on CCoP §1.2.1 + §1.4.1), Section 1.2 specifically
is titled "Glossary and Interpretation" (the definitions section), and
Sections 10.1/11.1 ("Application of this Section") are per-chapter
scope-setting clauses. Every other CCoP 2.0 clause, and every clause from
the other 6 source documents (no verified TOC available this plan), falls
through to the documented `DEFAULT_FUNCTION_TYPE` fallback = ControlClause
(majority case for a Code of Practice — overwhelmingly control/obligation
text). See `_derive_function_type`.

Cypher discipline (T-09-12 / threat T-10-05-01): all Cypher below is a
static, module-level string parameterized via `$entries` — no value is ever
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

from infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]

# Resolved relative to this file so it is correct regardless of the caller's
# working directory (src/rag/graph/ontology -> src/rag/ingestion/fixtures).
DEFAULT_CLAUSE_INVENTORY_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "ingestion"
    / "fixtures"
    / "clause_inventory.json"
)

FUNCTION_TYPE_TAGS = ("ScopeClause", "ControlClause", "DefinitionClause")

# Documented fallback (D-09) — applied whenever a clause falls outside the
# verified CCoP 2.0 TOC mapping below (all non-CCoP-2.0 source docs, and any
# CCoP 2.0 clause not explicitly listed).
DEFAULT_FUNCTION_TYPE = "ControlClause"

# Verified against the official TOC: ccop-official/CCoP---Second-Edition_
# Revision-One.pdf, pages 2-3 (Document History + Table of Contents).
_CCOP_2_0_SOURCE_DOC = "CCoP 2.0"
_CCOP_2_0_SECTION_FUNCTION_TYPE: dict[str, str] = {
    "1": "ScopeClause",  # Chapter 1 "Preliminary" (top-level clause itself)
    "1.1": "ScopeClause",  # Citation and Commencement
    "1.2": "DefinitionClause",  # Glossary and Interpretation
    "1.3": "ScopeClause",  # Purpose of this Code
    "1.4": "ScopeClause",  # Legal Effect of this Code
    "1.5": "ScopeClause",  # Recurring Requirements
    "1.6": "ScopeClause",  # Waiver
    "1.7": "ScopeClause",  # Amendment and Revocation
    "10.1": "ScopeClause",  # OT chapter — "Application of this Section"
    "11.1": "ScopeClause",  # Domain-Specific chapter — "Application of this Section"
}

_ITEM_SUFFIX_RE = re.compile(r"^(?P<base>.+)\((?P<letter>[a-z])\)$")


def _strip_item_suffix(clause_id: str) -> str:
    """Strip a trailing '(x)' item-letter suffix, if present (e.g. '10.2.5(a)' -> '10.2.5')."""
    match = _ITEM_SUFFIX_RE.match(clause_id)
    return match.group("base") if match else clause_id


def _derive_parent(clause_id: str) -> Optional[str]:
    """
    Derive the parent clause_id from clause_id's dot/paren structure (D-10).

    Extends `clause_aware_chunker._extract_section`'s dot-splitting rule to
    also strip a trailing "(x)" item-letter suffix first.

    Examples:
        "10.2.5(a)" -> "10.2.5"   (item -> its enclosing clause)
        "6.1.2"     -> "6.1"      (plain dot-hierarchy, matches _extract_section)
        "6.1"       -> "6"
        "6"         -> None       (chapter/title root, no parent)
        "Part 1"    -> None       (Cybersecurity Act root, no dot/paren)
    """
    item_match = _ITEM_SUFFIX_RE.match(clause_id)
    if item_match:
        return item_match.group("base")
    if "." in clause_id:
        return clause_id.rsplit(".", 1)[0]
    return None


def _derive_chapter(clause_id: str) -> str:
    """
    Derive the top-level chapter/title token from clause_id (D-10).

    Examples: "10.2.5(a)" -> "10", "6.1.2" -> "6", "Part 1" -> "Part 1".
    """
    base = _strip_item_suffix(clause_id)
    return base.split(".", 1)[0]


def _derive_function_type(clause_id: str, source_doc: str) -> str:
    """
    Assign a D-09 function_type tag using the verified CCoP 2.0 TOC mapping,
    falling back to DEFAULT_FUNCTION_TYPE for every clause outside that
    mapping (documented fallback — see module docstring).
    """
    if source_doc != _CCOP_2_0_SOURCE_DOC:
        return DEFAULT_FUNCTION_TYPE

    base = _strip_item_suffix(clause_id)
    parts = base.split(".")
    section_key = ".".join(parts[:2]) if len(parts) >= 2 else parts[0]
    return _CCOP_2_0_SECTION_FUNCTION_TYPE.get(section_key, DEFAULT_FUNCTION_TYPE)


@dataclass
class SeedStats:
    """Aggregate statistics for a clause-seeding run (T-09-08: reported, never swallowed)."""

    entries_total: int = 0
    nodes_seeded: int = 0
    edges_created: int = 0
    function_type_distribution: dict[str, int] = field(default_factory=dict)


class ClauseSeeder:
    """
    Deterministically MERGE-seeds the 691-clause backbone (D-10) — no LLM,
    no hallucinated/unnamed clauses, idempotently re-runnable.

    Reads `clause_inventory.json`, derives `chapter` / `parent_id` /
    `function_type` per entry, then writes via a single static parameterized
    Cypher `UNWIND $entries AS entry MERGE (...)` pass for nodes and a
    second pass for `:HAS_CHILD` parent-child edges.
    """

    def __init__(
        self,
        settings: Settings,
        driver: Optional["neo4j.Driver"] = None,
        inventory_path: PathLike = DEFAULT_CLAUSE_INVENTORY_PATH,
    ) -> None:
        self.settings = settings
        self.driver = driver or neo4j.GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        self.inventory_path = Path(inventory_path)
        self._ensure_constraint()

    def _ensure_constraint(self) -> None:
        """
        Idempotently create a composite uniqueness constraint on
        (clause_id, source_doc) — mirrors `kg_builder.py`'s
        "already exists"-swallow pattern for index/constraint creation.
        `IF NOT EXISTS` already makes this idempotent; the try/except is a
        defensive fallback for Neo4j editions/versions where this composite
        constraint form is unsupported (non-fatal — MERGE alone still
        guarantees idempotent seeding without it).
        """
        try:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                session.run(
                    "CREATE CONSTRAINT clause_id_source_doc_unique IF NOT EXISTS "
                    "FOR (c:Clause) REQUIRE (c.clause_id, c.source_doc) IS UNIQUE"
                )
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("Clause uniqueness constraint already exists — skipping creation.")
            else:
                logger.warning(f"Could not create Clause uniqueness constraint (non-fatal): {e}")

    def load_entries(self) -> list[dict[str, Any]]:
        """
        Read `clause_inventory.json` and enrich each flat
        `{clause_id, source_doc}` entry with derived `chapter`, `parent_id`,
        and `function_type` fields (D-09/D-10).
        """
        payload = json.loads(self.inventory_path.read_text())
        raw_entries = payload["entries"]

        enriched: list[dict[str, Any]] = []
        for entry in raw_entries:
            clause_id = entry["clause_id"]
            source_doc = entry["source_doc"]
            enriched.append(
                {
                    "clause_id": clause_id,
                    "source_doc": source_doc,
                    "chapter": _derive_chapter(clause_id),
                    "parent_id": _derive_parent(clause_id),
                    "function_type": _derive_function_type(clause_id, source_doc),
                }
            )
        return enriched

    def seed(self) -> SeedStats:
        """
        MERGE all clause nodes + parent-child edges, then report authoritative
        counts read back from Neo4j (never trusted from summary counters —
        matches `kg_builder.py`'s `_accumulate_graph_stats` convention).
        """
        entries = self.load_entries()

        with self.driver.session(database=self.settings.neo4j_database) as session:
            session.run(
                "UNWIND $entries AS entry "
                "MERGE (c:Clause {clause_id: entry.clause_id, source_doc: entry.source_doc}) "
                "SET c.chapter = entry.chapter, c.function_type = entry.function_type",
                entries=entries,
            )
            session.run(
                "UNWIND $entries AS entry "
                "WITH entry WHERE entry.parent_id IS NOT NULL "
                "MATCH (parent:Clause {clause_id: entry.parent_id, source_doc: entry.source_doc}) "
                "MATCH (child:Clause {clause_id: entry.clause_id, source_doc: entry.source_doc}) "
                "MERGE (parent)-[:HAS_CHILD]->(child)",
                entries=entries,
            )

        return self._accumulate_stats(entries)

    def _accumulate_stats(self, entries: list[dict[str, Any]]) -> SeedStats:
        """Query Neo4j directly for authoritative post-seed counts (T-09-08)."""
        stats = SeedStats(entries_total=len(entries))
        try:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                stats.nodes_seeded = session.run(
                    "MATCH (c:Clause) RETURN count(c) AS c"
                ).single()["c"]
                stats.edges_created = session.run(
                    "MATCH (:Clause)-[r:HAS_CHILD]->(:Clause) RETURN count(r) AS c"
                ).single()["c"]
                distribution_result = session.run(
                    "MATCH (c:Clause) RETURN c.function_type AS function_type, "
                    "count(c) AS c ORDER BY function_type"
                )
                stats.function_type_distribution = {
                    record["function_type"]: record["c"] for record in distribution_result
                }
        except Exception as e:
            logger.warning(f"Could not query clause-seeding stats after seed: {e}")
        return stats


__all__: list[str] = [
    "ClauseSeeder",
    "SeedStats",
    "DEFAULT_CLAUSE_INVENTORY_PATH",
    "DEFAULT_FUNCTION_TYPE",
    "FUNCTION_TYPE_TAGS",
]
