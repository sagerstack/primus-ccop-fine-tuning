"""
Source-Layer Annotation (Phase 11 -- D-06/D-07/D-08 corrected, SOURCE layer
only).

Annotates every seeded `:Clause` node with a source-doc-namespaced
`citation_id` (D-08 -- fixes Finding 2's clause_id collision across all 7
source docs, e.g. "5.7.2(b)" existing identically shaped ids in multiple
documents), a `doc_class` (`binding` for CCoP 2.0 + Cybersecurity Act 2018,
`guidance` for the 4 guides + Response to Feedback), and an
`is_structural_header` flag (chapter/section skeleton nodes vs operative
leaf clauses -- D-07: structural headers are CONTAIN-hierarchy skeleton,
never a Compliance Unit).

THIS MODULE MINTS NO `:ComplianceUnit` NODES. A Compliance Unit is
GraphCompliance's atomic obligation (4-tuple: subject/constraint/context/
conditions), typed premise/meta-CU/actor-CU -- an OUTPUT of the
classification + formalization pass landing in 11-04 (D-07, corrected), not
derived 1:1 from clause ids here. This module only prepares the SOURCE
layer those CUs will be minted from; there is no operative-leaf/CU-count
reconciliation anywhere in this module (D-06/D-07 explicitly reject that).

Idempotent (MERGE-equivalent SET on the composite `(clause_id, source_doc)`
key `ClauseSeeder` already established, D-10 precedent) -- re-running never
duplicates or corrupts prior annotations.

Cypher discipline (T-09-12): `_ANNOTATE_QUERY` below is a static
module-level string, parameterized via `$entries` -- no value is ever
spliced into query text via f-string/`.format()`.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import neo4j

from infrastructure.config.settings import Settings
from rag.graph.ontology.clause_seeder import (
    DEFAULT_CLAUSE_INVENTORY_PATH,
    _derive_parent,
)
from rag.graph.ontology.clause_seeder import _ITEM_SUFFIX_RE as _CLAUSE_ITEM_SUFFIX_RE

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]

# Same "section N" decomposition regex as `clause_text_aligner.py` /
# `verify_clause_completeness.py` (duplicated, not imported -- a stable,
# two-line literal; see those modules' docstrings for the same
# don't-cross-package-import rationale). Used only to produce the D-08
# example citation form "Act-7" instead of the redundant "Act-section 7".
_SECTION_PREFIX_RE = re.compile(r"^section\s+(?P<num>.+)$", re.IGNORECASE)

# D-08: CCoP 2.0 + Cybersecurity Act 2018 are BINDING (yield judged
# actor-CU/meta-CUs in 11-04); the 4 guides + Response to Feedback are
# GUIDANCE (premise/context, never judged). Verified, documented mapping --
# no silent default guess (mirrors clause_seeder.py's DEFAULT_FUNCTION_TYPE
# fail-loud-over-guessing discipline).
BINDING_SOURCE_DOCS = frozenset({"CCoP 2.0", "Cybersecurity Act 2018"})

# D-08 citation-id namespace prefixes, one per source doc -- prevents the
# Finding 2 clause_id collision (identically-shaped clause ids across all 7
# documents). Short, human-legible, stable; the CCoP/Act examples match
# D-08's own worked example verbatim ("CCoP-5.7.2(b)" vs "Act-7").
_SOURCE_DOC_PREFIX: dict[str, str] = {
    "CCoP 2.0": "CCoP",
    "Cybersecurity Act 2018": "Act",
    "CCoP Response to Feedback": "RtF",
    "Auditing Guidelines": "AuditGuide",
    "Threat Modelling Guide": "ThreatGuide",
    "Risk Assessment Guide": "RiskGuide",
    "Security By Design": "SBD",
}

DOC_CLASS_BINDING = "binding"
DOC_CLASS_GUIDANCE = "guidance"

# Static, parameterized Cypher (T-09-12) -- $entries is the only variable
# input, bound via session.run(..., entries=entries), never string-
# interpolated. MATCH-only (never MERGE) -- this module annotates EXISTING
# seeded :Clause nodes; it never creates the skeleton (ClauseSeeder's job)
# and it never creates a :ComplianceUnit (11-04's job).
_ANNOTATE_QUERY = """
UNWIND $entries AS entry
MATCH (c:Clause {clause_id: entry.clause_id, source_doc: entry.source_doc})
SET c.citation_id = entry.citation_id,
    c.doc_class = entry.doc_class,
    c.is_structural_header = entry.is_structural_header
""".strip()

_COUNT_COMPLIANCE_UNITS_QUERY = "MATCH (cu:ComplianceUnit) RETURN count(cu) AS c"

_COUNT_MISSING_CITATION_QUERY = """
MATCH (c:Clause)
WHERE c.citation_id IS NULL OR c.citation_id = ''
RETURN count(c) AS c
""".strip()

_COUNT_INVALID_DOC_CLASS_QUERY = """
MATCH (c:Clause)
WHERE NOT c.doc_class IN $valid_classes
RETURN count(c) AS c
""".strip()


def source_doc_prefix(source_doc: str) -> str:
    """
    Resolve a source document's D-08 citation-namespace prefix. Fails loud
    (D-19 discipline) on an unrecognized source_doc rather than silently
    minting an ambiguous/collision-prone prefix -- every one of the 7 corpus
    documents is a known, documented quantity (D-06).
    """
    prefix = _SOURCE_DOC_PREFIX.get(source_doc)
    if prefix is None:
        raise ValueError(
            f"No D-08 citation-namespace prefix registered for source_doc "
            f"{source_doc!r} -- add it to _SOURCE_DOC_PREFIX rather than "
            f"silently guessing (D-19 fail-loud discipline)."
        )
    return prefix


def doc_class_for(source_doc: str) -> str:
    """D-08: CCoP 2.0 + Cybersecurity Act 2018 are binding; everything else is guidance."""
    return DOC_CLASS_BINDING if source_doc in BINDING_SOURCE_DOCS else DOC_CLASS_GUIDANCE


def _citation_token(clause_id: str) -> str:
    """
    Normalize the inventory-label form for the citation display string --
    "section 7" -> "7" (matches D-08's own worked example "Act-7", avoiding
    the redundant "Act-section 7"). Every other clause_id form (dotted
    CCoP/guide ids, "Part N") passes through unchanged. Purely cosmetic --
    the underlying `clause_id` node property is never altered.
    """
    section_match = _SECTION_PREFIX_RE.match(clause_id)
    return section_match.group("num") if section_match else clause_id


@dataclass
class SourceAnnotationStats:
    """Aggregate statistics for a source-layer annotation run (T-09-08: reported, never swallowed)."""

    entries_total: int = 0
    annotated: int = 0
    binding_count: int = 0
    guidance_count: int = 0
    structural_header_count: int = 0
    # Authoritative post-write re-queries -- never trusted from in-process
    # counters (T-09-08).
    compliance_unit_count: int = 0
    missing_citation_id_count: int = 0
    invalid_doc_class_count: int = 0

    @property
    def conforms(self) -> bool:
        """
        This module mints NO :ComplianceUnit nodes and every seeded :Clause
        node must carry a namespaced citation_id + a valid doc_class
        (D-06/D-07/D-08) -- explicit, asserted, never assumed.
        """
        return (
            self.compliance_unit_count == 0
            and self.missing_citation_id_count == 0
            and self.invalid_doc_class_count == 0
        )


class ClauseSourceAnnotator:
    """
    Source-layer annotation (D-06/D-07/D-08): namespaces every seeded
    `:Clause` node's citation id by source doc, tags its `doc_class`
    (binding/guidance), and flags structural (chapter/section) headers.

    PRECONDITION: the `:Clause` backbone must already be seeded (`ccop-eval
    graph seed-clauses` / `ClauseSeeder.seed()`) -- this module only SETs
    properties on EXISTING nodes. It never MERGEs new `:Clause` nodes and it
    NEVER creates a `:ComplianceUnit` node (that is 11-04's job).
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

    def load_entries(self) -> list[dict[str, str]]:
        payload = json.loads(self.inventory_path.read_text())
        return payload["entries"]

    @staticmethod
    def _compute_structural_header_ids(entries: list[dict[str, str]]) -> set[tuple[str, str]]:
        """
        A clause is a structural (chapter/section) header iff some OTHER
        entry in the SAME source_doc has it as a TRUE dot-hierarchy parent
        (`_derive_parent` -- reused from `clause_seeder.py`, D-10's dot/
        paren hierarchy parsing, never reimplemented). Leaves (no true
        sub-clause children) are the operative candidates D-07 says become
        CU source material in 11-04.

        Item-letter composite entries (e.g. "5.3.1(a)") are deliberately
        EXCLUDED from contributing a parent here: an operative clause like
        "5.3.1" that merely enumerates lettered sub-items ((a)(b)(c)) is
        itself a leaf CU candidate, NOT a structural chapter/section header
        -- only a REAL deeper dot-hierarchy clause (e.g. a hypothetical
        "5.3.1.1") would make "5.3.1" a container. Without this exclusion,
        every clause with lettered sub-items would be mis-flagged as
        non-operative skeleton, which D-07 does not intend.
        """
        parent_ids: set[tuple[str, str]] = set()
        for entry in entries:
            clause_id = entry["clause_id"]
            if _CLAUSE_ITEM_SUFFIX_RE.match(clause_id):
                continue
            parent_id = _derive_parent(clause_id)
            if parent_id is not None:
                parent_ids.add((parent_id, entry["source_doc"]))
        return parent_ids

    def annotate(self) -> SourceAnnotationStats:
        """
        Annotate every inventory entry's seeded :Clause node, then report
        authoritative post-write counts re-queried from Neo4j (T-09-08).
        """
        entries = self.load_entries()
        structural_ids = self._compute_structural_header_ids(entries)

        stats = SourceAnnotationStats(entries_total=len(entries))
        to_write: list[dict[str, object]] = []

        for entry in entries:
            clause_id = entry["clause_id"]
            source_doc = entry["source_doc"]
            prefix = source_doc_prefix(source_doc)
            doc_class = doc_class_for(source_doc)
            is_structural_header = (clause_id, source_doc) in structural_ids

            to_write.append(
                {
                    "clause_id": clause_id,
                    "source_doc": source_doc,
                    "citation_id": f"{prefix}-{_citation_token(clause_id)}",
                    "doc_class": doc_class,
                    "is_structural_header": is_structural_header,
                }
            )
            stats.annotated += 1
            if doc_class == DOC_CLASS_BINDING:
                stats.binding_count += 1
            else:
                stats.guidance_count += 1
            if is_structural_header:
                stats.structural_header_count += 1

        if to_write:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                session.run(_ANNOTATE_QUERY, entries=to_write)

        self._accumulate_stats(stats)
        return stats

    def _accumulate_stats(self, stats: SourceAnnotationStats) -> None:
        """Query Neo4j directly for authoritative post-write counts (T-09-08)."""
        try:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                stats.compliance_unit_count = session.run(
                    _COUNT_COMPLIANCE_UNITS_QUERY
                ).single()["c"]
                stats.missing_citation_id_count = session.run(
                    _COUNT_MISSING_CITATION_QUERY
                ).single()["c"]
                stats.invalid_doc_class_count = session.run(
                    _COUNT_INVALID_DOC_CLASS_QUERY,
                    valid_classes=[DOC_CLASS_BINDING, DOC_CLASS_GUIDANCE],
                ).single()["c"]
        except Exception as e:
            logger.warning(f"Could not query source-annotation stats after annotate: {e}")


__all__: list[str] = [
    "ClauseSourceAnnotator",
    "SourceAnnotationStats",
    "BINDING_SOURCE_DOCS",
    "DOC_CLASS_BINDING",
    "DOC_CLASS_GUIDANCE",
    "source_doc_prefix",
    "doc_class_for",
]
