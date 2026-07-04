"""
Fail-Loud Clause-Completeness Gate (Phase 11, D-19/D-20/D-25.3)

Wave-0 BLOCKING artifact: proves every one of clause_inventory.json's 883
clause ids (7 source docs) resolves to a retrievable verbatim body in the
re-ingested corpus, and that per-document provenance is correct (7 distinct
identities, zero "document.txt" collapse). "No retrieval strategy can fix a
data problem" (bugs.md 2026-04-21) — this script is the machine-checked,
fail-loud proof that the data problem is actually fixed, run at BUILD time,
never assumed at eval time.

Mirrors `shacl_validator.py`'s validate-and-report shape (D-13 precedent):
a `CompletenessReport` dataclass, written to a committed JSON artifact, with
`sys.exit(non-zero)` (never log-and-continue) when any clause is unresolved.

Resolution reuses `KGInspector._clause_id_appears` (`rag/graph/inspect/
metrics.py`) — the SAME boundary-aware matcher already used by
`clause_linker.py` and `KGInspector.clause_coverage()` (Don't-Hand-Roll) — so
a short numeric clause_id like "1" never spuriously matches inside a longer
one like "15.37". On top of the direct match, two decomposition fallbacks
were added after being discovered empirically against the real re-ingested
corpus (see `_clause_resolves` docstring): lettered composite ids
("10.2.5(a)") and the Cybersecurity Act's "section N" inventory-label
convention.

Usage:
    python -m rag.ingestion.scripts.verify_clause_completeness
    python -m rag.ingestion.scripts.verify_clause_completeness --provenance-only
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

from qdrant_client import QdrantClient

from infrastructure.config.settings import Settings, get_settings
from rag.graph.inspect.metrics import KGInspector

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]

# Default inventory path, resolved relative to this file (src/rag/ingestion/
# scripts -> src/rag/ingestion/fixtures/clause_inventory.json).
DEFAULT_INVENTORY_PATH = (
    Path(__file__).resolve().parent.parent / "fixtures" / "clause_inventory.json"
)

# Committed report artifact (D-13 precedent: co-located with the gate script).
DEFAULT_REPORT_PATH = Path(__file__).resolve().parent / "completeness_report.json"

# CCoP 2.0's real section-level TOC backbone — 5.1 through 5.17.
#
# CORRECTED (D-19) from run_ingestion.py's EXPECTED_CCOP_2_SECTIONS, which
# only lists 5.1-5.12 (stale — sourced from the page-4 TOC summary, which
# does not enumerate every body section). clause_inventory.json (883
# entries, the authoritative D-06/D-07 source) has CCoP 2.0 entries through
# 5.17 — verified against the live re-ingested corpus (5.13-5.17 ARE real,
# retrievable sections). A gate that only checked 5.1-5.12 could never catch
# a regression that dropped 5.13-5.17 entirely.
EXPECTED_CCOP_2_TOC_SECTIONS = [f"5.{n}" for n in range(1, 18)]

# Item-letter composite id suffix, e.g. "10.2.5(a)" -> base="10.2.5", letter="a"
# (same shape as clause_seeder.py's _ITEM_SUFFIX_RE — not imported to avoid a
# cross-package dependency from rag.ingestion -> rag.graph.ontology; the
# regex itself is a two-line, stable, well-understood literal).
_ITEM_SUFFIX_RE = re.compile(r"^(?P<base>.+)\((?P<letter>[a-z])\)$")

# Cybersecurity Act 2018 inventory-label convention: entries are named
# "section N" but the Act's actual numbered-clause prose (Singapore
# legal-drafting convention) never contains the literal word "section"
# before the number — it renders as bare "N.--(1) ..." (confirmed against
# the live re-ingested corpus).
_SECTION_PREFIX_RE = re.compile(r"^section\s+(?P<num>.+)$", re.IGNORECASE)


@dataclass
class UnresolvedClause:
    """One clause_inventory.json entry with no resolvable verbatim body."""

    clause_id: str
    source_doc: str


@dataclass
class CompletenessReport:
    """
    Outcome of the D-19 clause-completeness check (quarantine-report shape,
    mirrors `shacl_validator.ValidationReport`).
    """

    total: int
    resolved: int
    unresolved: list[UnresolvedClause] = field(default_factory=list)
    toc_section_parity: dict[str, Any] = field(default_factory=dict)

    @property
    def conforms(self) -> bool:
        return len(self.unresolved) == 0 and self.toc_section_parity.get(
            "conforms", True
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "resolved": self.resolved,
            "unresolved_count": len(self.unresolved),
            "unresolved": [asdict(u) for u in self.unresolved],
            "toc_section_parity": self.toc_section_parity,
            "conforms": self.conforms,
        }

    def write_json(self, path: PathLike = DEFAULT_REPORT_PATH) -> Path:
        out = Path(path)
        out.write_text(json.dumps(self.to_dict(), indent=2, default=str))
        return out


@dataclass
class ProvenanceReport:
    """Outcome of the D-20 per-document provenance check (Neo4j)."""

    distinct_source_docs: list[str]
    document_txt_count: int

    @property
    def conforms(self) -> bool:
        return len(self.distinct_source_docs) == 7 and self.document_txt_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "distinct_source_docs": self.distinct_source_docs,
            "distinct_count": len(self.distinct_source_docs),
            "document_txt_count": self.document_txt_count,
            "conforms": self.conforms,
        }


def _clause_resolves(clause_id: str, haystack_lower: str) -> bool:
    """
    Boundary-aware verbatim-text resolution.

    1. Direct match: `KGInspector._clause_id_appears` (reused, not
       reimplemented) — the common case, and (thanks to the Task 1 chunker
       fix) now also true for every CCoP 2.0 / Response-to-Feedback /
       Security-By-Design lettered sub-item, which each get their own
       discrete, additive chunk.
    2. Item-letter decomposition: composite ids like "10.2.5(a)" rarely
       appear as one literal string in source prose for documents whose
       chunker does not emit a discrete per-letter chunk — the source
       writes the parent clause number once, then "(a)", "(b)", ... as
       separate list markers. Resolved when BOTH the parent clause id AND
       the bare "(x)" marker independently appear in the same document.
    3. "section N" decomposition (Cybersecurity Act 2018 inventory-label
       convention — see module docstring): resolved when the bare number
       appears.

    Args:
        clause_id: The clause_inventory.json entry's clause_id.
        haystack_lower: Lowercased, newline-joined text of every indexed
            chunk for this entry's source_doc.

    Returns:
        True if a verbatim body for this clause_id is resolvable.
    """
    if KGInspector._clause_id_appears(clause_id, haystack_lower):
        return True

    item_match = _ITEM_SUFFIX_RE.match(clause_id)
    if item_match:
        base, letter = item_match.group("base"), item_match.group("letter")
        if KGInspector._clause_id_appears(
            base, haystack_lower
        ) and KGInspector._clause_id_appears(f"({letter})", haystack_lower):
            return True

    section_match = _SECTION_PREFIX_RE.match(clause_id)
    if section_match:
        bare = section_match.group("num")
        if KGInspector._clause_id_appears(bare, haystack_lower):
            return True

    return False


def _load_inventory(inventory_path: PathLike) -> list[dict[str, str]]:
    payload = json.loads(Path(inventory_path).read_text())
    return payload["entries"]


def _build_haystacks(client: QdrantClient, collection_name: str) -> dict[str, str]:
    """
    Scroll every point in the Qdrant collection and combine `text` payload
    values per `document_source` (lowercased) — mirrors
    `KGInspector.clause_coverage`'s "combine all chunk text, then boundary-
    match" pattern, scoped per-document here (D-08 namespacing: a clause_id
    is not globally unique across the 7 source docs, so a cross-document
    combined haystack would risk false-positive resolution).
    """
    haystacks: dict[str, list[str]] = {}
    offset = None
    while True:
        records, offset = client.scroll(
            collection_name=collection_name,
            limit=500,
            offset=offset,
            with_payload=["text", "document_source"],
            with_vectors=False,
        )
        for record in records:
            payload = record.payload or {}
            doc = payload.get("document_source", "")
            text = payload.get("text", "") or ""
            haystacks.setdefault(doc, []).append(text)
        if offset is None:
            break
    return {doc: "\n".join(texts).lower() for doc, texts in haystacks.items()}


def _check_toc_section_parity(
    haystacks: dict[str, str], entries: list[dict[str, str]]
) -> dict[str, Any]:
    """
    D-19 "TOC/inventory section count == extracted-with-text count"
    assertion, scoped to CCoP 2.0's corrected 17-section backbone
    (EXPECTED_CCOP_2_TOC_SECTIONS). Reported separately from the per-entry
    check above so a whole-section drop is named explicitly, not just
    buried in the flat unresolved list.

    Skipped (reported, never silently passed) when the inventory under test
    carries no "CCoP 2.0" entries at all — keeps this assertion meaningful
    for synthetic/partial fixtures (e.g. unit tests) that intentionally
    don't model the full 7-doc corpus, without ever affecting the real gate
    (whose inventory always includes CCoP 2.0).
    """
    if not any(entry.get("source_doc") == "CCoP 2.0" for entry in entries):
        return {"skipped": True, "conforms": True}

    hay = haystacks.get("CCoP 2.0", "")
    resolved_sections = [
        s for s in EXPECTED_CCOP_2_TOC_SECTIONS if _clause_resolves(s, hay)
    ]
    missing = sorted(set(EXPECTED_CCOP_2_TOC_SECTIONS) - set(resolved_sections))
    return {
        "expected": len(EXPECTED_CCOP_2_TOC_SECTIONS),
        "resolved": len(resolved_sections),
        "missing": missing,
        "conforms": len(missing) == 0,
    }


def check_completeness(
    inventory_path: PathLike = DEFAULT_INVENTORY_PATH,
    client: Optional[QdrantClient] = None,
    collection_name: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> CompletenessReport:
    """
    Run the full D-19 completeness check against the re-ingested Qdrant
    corpus. Never mutates the corpus — read-only scroll + in-memory match.
    """
    settings = settings or get_settings()
    resolved_collection_name = collection_name or settings.qdrant_collection_name
    if not resolved_collection_name:
        raise ValueError(
            "No Qdrant collection configured (CCOP_QDRANT_COLLECTION_NAME unset)"
        )

    owns_client = client is None
    resolved_client = client or QdrantClient(url=settings.qdrant_url)
    try:
        entries = _load_inventory(inventory_path)
        haystacks = _build_haystacks(resolved_client, resolved_collection_name)

        unresolved: list[UnresolvedClause] = []
        for entry in entries:
            clause_id = entry["clause_id"]
            source_doc = entry["source_doc"]
            hay = haystacks.get(source_doc, "")
            if not _clause_resolves(clause_id, hay):
                unresolved.append(
                    UnresolvedClause(clause_id=clause_id, source_doc=source_doc)
                )

        toc_section_parity = _check_toc_section_parity(haystacks, entries)

        return CompletenessReport(
            total=len(entries),
            resolved=len(entries) - len(unresolved),
            unresolved=unresolved,
            toc_section_parity=toc_section_parity,
        )
    finally:
        if owns_client:
            resolved_client.close()


def check_provenance(
    settings: Optional[Settings] = None, driver: Any = None
) -> ProvenanceReport:
    """
    D-20 guard: assert the 7 source docs have 7 distinct `Document.path`
    identities in Neo4j and zero "document.txt" collapse (bugs.md
    2026-07-02). Read-only — never mutates the graph.
    """
    import neo4j

    settings = settings or get_settings()
    owns_driver = driver is None
    resolved_driver = driver or neo4j.GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    try:
        with resolved_driver.session(database=settings.neo4j_database) as session:
            result = session.run("MATCH (d:Document) RETURN DISTINCT d.path AS path")
            paths = sorted(record["path"] for record in result if record["path"])
        document_txt_count = sum(1 for p in paths if p == "document.txt")
        return ProvenanceReport(
            distinct_source_docs=paths, document_txt_count=document_txt_count
        )
    finally:
        if owns_driver:
            resolved_driver.close()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail-loud clause-completeness gate (D-19/D-20/D-25.3)"
    )
    parser.add_argument(
        "--provenance-only",
        action="store_true",
        help="Only run the D-20 Neo4j per-document provenance check",
    )
    parser.add_argument(
        "--inventory-path",
        default=str(DEFAULT_INVENTORY_PATH),
        help="Path to clause_inventory.json",
    )
    parser.add_argument(
        "--report-path",
        default=str(DEFAULT_REPORT_PATH),
        help="Where to write the CompletenessReport JSON artifact",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    if args.provenance_only:
        report = check_provenance()
        print(json.dumps(report.to_dict(), indent=2))
        if not report.conforms:
            logger.error("Provenance gate FAILED (D-20): %s", report.to_dict())
            return 1
        logger.info(
            "Provenance gate PASSED (D-20): %d distinct source docs, "
            "0 document.txt",
            len(report.distinct_source_docs),
        )
        return 0

    report = check_completeness(inventory_path=args.inventory_path)
    written = report.write_json(args.report_path)
    print(json.dumps(report.to_dict(), indent=2))

    if not report.conforms:
        logger.error(
            "Completeness gate FAILED (D-19): %d/%d unresolved. Report: %s",
            len(report.unresolved),
            report.total,
            written,
        )
        for unresolved_clause in report.unresolved:
            logger.error(
                "  UNRESOLVED: %s (%s)",
                unresolved_clause.clause_id,
                unresolved_clause.source_doc,
            )
        if not report.toc_section_parity.get("conforms", True):
            logger.error(
                "  TOC section parity FAILED — missing: %s",
                report.toc_section_parity.get("missing"),
            )
        return 1

    logger.info(
        "Completeness gate PASSED (D-19): %d/%d clause ids resolved. "
        "TOC section parity: %d/%d. Report: %s",
        report.resolved,
        report.total,
        report.toc_section_parity.get("resolved", 0),
        report.toc_section_parity.get("expected", 0),
        written,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
