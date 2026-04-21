"""
CCoP Clause Inventory Builder

Extracts every valid clause ID from all CCoP PDFs via Docling and emits a
minimal JSON inventory: {clause_id, source_doc} per entry.

The inventory is the authoritative source for sub-goal B ground-truth audit:
it tells the validator "does this clause exist in this document?"

Schema is intentionally minimal — no titles, pages, or hierarchy. Semantic
mismatch checks source clause text from the Qdrant index at audit time.

Usage:
    python -m rag.ingestion.scripts.build_clause_inventory \\
        --ccop-dir ../ccop-official \\
        [--output path/to/clause_inventory.json]
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from rag.ingestion.parsers.docling_parser import parse_all_ccop_documents_with_docling

logger = logging.getLogger(__name__)

# Default output path — fixtures directory co-located with this script's package
_DEFAULT_OUTPUT = Path(__file__).parent.parent / "fixtures" / "clause_inventory.json"

# Pass 1 — Clause heading pattern (Docling markdown output).
#
# Matches two heading formats emitted by Docling's Classic pipeline:
#   - Bare:      "5.2.1 The CIIO shall perform..."
#   - ## prefix: "## 5.3 Privileged Access Management"
#
# The optional ## prefix is derived from CLAUSE_PATTERN in clause_aware_chunker.py
# (established in Phase 3.2 Plan 01).
#
# Pattern structure:
#   ^(?:##\s+)?      — optional Docling heading prefix
#   (\d+(?:\.\d+)*) — chapter or multi-level clause number (e.g. 5, 5.3, 5.3.1)
#   \s+              — whitespace separator (clause number must be followed by text)
#
# Must be followed by at least one non-whitespace character to avoid matching
# bare digits (page numbers, list items) or empty headings.
CLAUSE_ID_PATTERN = re.compile(
    r"^(?:##\s+)?(\d+(?:\.\d+)*)\s+\S",
    re.MULTILINE,
)

# Pass 2 — Item-letter list item pattern within a clause body.
#
# Docling renders sub-items of a clause as markdown list entries, NOT as
# standalone numbered headings. For example, 5.3.1 body contains:
#   "- (a) Ensure that privileged access..."
#   "- (b) Maintain an updated inventory..."
#   "- (c) Implement multi-factor authentication..."
#
# These sub-items ARE valid citation targets in ground truth (e.g. "5.3.1(c)")
# and MUST appear in the inventory so the validator can confirm they exist.
# We synthesize "5.3.1(c)" by pairing the parent clause ID with the letter.
#
# Pattern matches: "- (a) ...", "- (b) ...", etc.
# The letter is captured in group(1). The surrounding context must be non-empty.
ITEM_LETTER_PATTERN = re.compile(
    r"^-\s+\(([a-z])\)\s+\S",
    re.MULTILINE,
)


def extract_clause_ids(markdown_text: str) -> list[str]:
    """
    Extract all clause IDs from Docling-generated markdown.

    Two-pass approach:
    - Pass 1: Clause headings (e.g. "## 5.3.1 With respect to...")
    - Pass 2: Item-letter sub-items embedded in clause bodies
      (e.g. "- (c) Implement MFA...") synthesised as "5.3.1(c)"

    Deduplicates within the document. Returns IDs in document order.

    Args:
        markdown_text: Markdown text from Docling parser

    Returns:
        Ordered, deduplicated list of clause ID strings
    """
    seen: set[str] = set()
    ordered: list[str] = []

    # Build a position-indexed list of clause matches for pass 2 context
    clause_matches: list[tuple[int, int, str]] = []  # (start, end, clause_id)

    for match in CLAUSE_ID_PATTERN.finditer(markdown_text):
        clause_id = match.group(1)
        if clause_id not in seen:
            seen.add(clause_id)
            ordered.append(clause_id)
        clause_matches.append((match.start(), match.end(), match.group(1)))

    # Pass 2: find item-letter list items and attribute them to the enclosing clause
    # The enclosing clause is the last clause heading that appears BEFORE this position.
    current_clause: str | None = None
    clause_idx = 0
    num_clauses = len(clause_matches)

    for letter_match in ITEM_LETTER_PATTERN.finditer(markdown_text):
        pos = letter_match.start()
        letter = letter_match.group(1)

        # Advance current_clause to the last clause heading before this position
        while clause_idx < num_clauses and clause_matches[clause_idx][0] <= pos:
            current_clause = clause_matches[clause_idx][2]
            clause_idx += 1

        if current_clause is not None:
            item_id = f"{current_clause}({letter})"
            if item_id not in seen:
                seen.add(item_id)
                ordered.append(item_id)

    return ordered


def build_inventory(ccop_dir: str) -> dict:
    """
    Parse all CCoP PDFs and build the clause inventory.

    Args:
        ccop_dir: Path to the ccop-official directory

    Returns:
        Inventory dict with generated_at, source_docs, and entries keys
    """
    logger.info(f"Building clause inventory from {ccop_dir}")

    parsed_docs = parse_all_ccop_documents_with_docling(ccop_dir)

    if not parsed_docs:
        raise RuntimeError(f"No documents parsed from {ccop_dir}")

    entries: list[dict] = []
    source_docs: list[str] = sorted(parsed_docs.keys())
    per_doc_counts: dict[str, int] = {}

    for doc_name in source_docs:
        result = parsed_docs[doc_name]
        clause_ids = extract_clause_ids(result.markdown)
        doc_entries = [
            {"clause_id": cid, "source_doc": doc_name} for cid in clause_ids
        ]
        entries.extend(doc_entries)
        per_doc_counts[doc_name] = len(doc_entries)
        logger.info(f"  {doc_name}: {len(doc_entries)} clause IDs extracted")

    # Sort for stable diffs: primary by source_doc, secondary by clause_id
    entries.sort(key=lambda e: (e["source_doc"], _clause_sort_key(e["clause_id"])))

    inventory = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_docs": source_docs,
        "entries": entries,
    }

    total = len(entries)
    logger.info(f"Total clause IDs across all documents: {total}")
    for doc, count in sorted(per_doc_counts.items()):
        logger.info(f"    {doc}: {count}")

    return inventory


def _clause_sort_key(clause_id: str) -> tuple:
    """
    Build a sortable tuple from a clause ID string for stable ordering.

    Uses a uniform (int, str) element structure so tuples of different lengths
    compare without TypeError in Python's tuple comparison.

    Examples:
        "5"        -> ((5, ""), (0, ""), (0, ""), "")
        "5.3"      -> ((5, ""), (3, ""), (0, ""), "")
        "5.3.1"    -> ((5, ""), (3, ""), (1, ""), "")
        "5.3.1(c)" -> ((5, ""), (3, ""), (1, ""), "c")
    """
    letter_suffix = ""
    if clause_id.endswith(")") and "(" in clause_id:
        base, letter_part = clause_id.rsplit("(", 1)
        letter_suffix = letter_part.rstrip(")")
        clause_id = base

    raw_parts = clause_id.split(".")
    # Pad to a fixed depth (4 levels covers all CCoP nesting) with zero ints
    try:
        numeric_parts = [int(p) for p in raw_parts]
    except ValueError:
        numeric_parts = [0]

    while len(numeric_parts) < 4:
        numeric_parts.append(0)

    return tuple(numeric_parts[:4]) + (letter_suffix,)


def write_inventory(inventory: dict, output_path: Path) -> None:
    """
    Write the inventory JSON to disk, creating parent directories as needed.

    Args:
        inventory: Inventory dict from build_inventory()
        output_path: Destination file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
        f.write("\n")  # POSIX trailing newline
    logger.info(f"Inventory written to {output_path}")
    logger.info(f"  {len(inventory['entries'])} entries, {len(inventory['source_docs'])} source documents")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build authoritative CCoP 2.0 clause inventory from PDFs via Docling"
    )
    parser.add_argument(
        "--ccop-dir",
        required=True,
        help="Path to the ccop-official directory containing CCoP PDFs",
    )
    parser.add_argument(
        "--output",
        default=str(_DEFAULT_OUTPUT),
        help=f"Output path for clause_inventory.json (default: {_DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        inventory = build_inventory(args.ccop_dir)
        output_path = Path(args.output)
        write_inventory(inventory, output_path)
        print(
            f"\nClause inventory written: {output_path}\n"
            f"  Documents: {len(inventory['source_docs'])}\n"
            f"  Total entries: {len(inventory['entries'])}"
        )
        for doc in inventory["source_docs"]:
            count = sum(1 for e in inventory["entries"] if e["source_doc"] == doc)
            print(f"    {doc}: {count}")
    except Exception as e:
        logger.error(f"Failed to build clause inventory: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
