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
# Pattern structure:
#   ^(?:##\s+)?      — optional Docling heading prefix
#   (\d+(?:\.\d+)*)  — chapter or multi-level clause number (e.g. 5, 5.3, 5.3.1)
#   \s+              — whitespace separator (clause number must be followed by text)
#
# Must be followed by at least one non-whitespace character to avoid matching
# bare digits (page numbers, list items) or empty headings.
CLAUSE_ID_PATTERN = re.compile(
    r"^(?:##\s+)?(\d+(?:\.\d+)*)\s+\S",
    re.MULTILINE,
)

# Pass 1b — Hierarchical clause IDs rendered as list items.
#
# Docling assimilates numbered clauses into surrounding markdown lists when
# the clause introduces a "- (a) ... - (b) ..." sub-list. Known cases in
# CCoP 2.0: 6.1.1 and 8.2.5. Without this pass, those clauses are silently
# dropped from the inventory, producing false-positive Pass 1 audit flags.
#
# Restricted to clause IDs with at least one dot (\d+(?:\.\d+)+) to avoid
# collecting plain numbered list items like "- 1 Something" in legal documents
# (the Cybersecurity Act 2018 body contains many such items that are not
# canonical section IDs — the dedicated legal pass extracts those).
CLAUSE_ID_LIST_ITEM_PATTERN = re.compile(
    r"^-\s+(\d+(?:\.\d+)+)\s+\S",
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

# Cybersecurity Act 2018 — legal-numbering document name.
# Only this document gets the legal-numbering extraction pass.
CYBERSECURITY_ACT_DOC_NAME = "Cybersecurity Act 2018"

# Legal pass 1 — section headings in the Cybersecurity Act 2018.
#
# Docling renders section headings as bare-number lines, e.g.:
#   "11. Powers of Commissioner..."
#   "15A. ..." (section suffix letters preserved)
#
# NOTE: The document does NOT use "section N" as a heading keyword — the word
# "section" appears only in cross-references within body text. We synthesize
# clause_id="section <N>" from the bare-number heading to match ground-truth
# citation convention (GT test cases cite as "section 11", not "11").
#
# Pattern structure:
#   ^           — start of line
#   (\d+[A-Z]?) — section number with optional suffix letter (e.g. 11, 15A)
#   \.\s+       — period and whitespace (heading format)
#   [A-Z]       — title starts with capital letter (filters out list items,
#                 numbered lists in body text, and TOC page-number entries)
LEGAL_SECTION_PATTERN = re.compile(
    r"^(\d+[A-Z]?)\.\s+[A-Z]",
    re.MULTILINE,
)

# Legal pass 2 — Part headings in the Cybersecurity Act 2018.
#
# Docling renders Part headings with optional ## prefix and Arabic numerals:
#   "## Part 1 PRELIMINARY"
#   "## Part 2 ADMINISTRATION"
#   "## Part 3 CRITICAL INFORMATION INFRASTRUCTURE"
#
# Deviation from original spec: the original spec called for Roman numerals
# ([IVX]+) but the actual PDF uses Arabic. Adapted to source format; emitted
# clause_id preserved as "Part <N>" to match ground-truth citation convention.
LEGAL_PART_PATTERN = re.compile(
    r"^(?:##\s+)?Part\s+(\d+)",
    re.MULTILINE,
)


def extract_clause_ids(markdown_text: str, source_doc: str = "") -> list[str]:
    """
    Extract all clause IDs from Docling-generated markdown.

    Primary CCoP-style extraction (applied to all documents):
    - Pass 1: Clause headings (e.g. "## 5.3.1 With respect to...")
    - Pass 2: Item-letter sub-items embedded in clause bodies
      (e.g. "- (c) Implement MFA...") synthesised as "5.3.1(c)"

    Legal-numbering extraction (applied ONLY when source_doc matches
    CYBERSECURITY_ACT_DOC_NAME — the Cybersecurity Act 2018 uses section/Part
    numbering instead of CCoP-style X.Y.Z hierarchy):
    - Legal pass 1: Bare-number section headings ("11. Powers...") → "section 11"
    - Legal pass 2: Part headings ("## Part 3 ...") → "Part 3"

    Deduplicates within the document. Returns IDs in document order.

    Args:
        markdown_text: Markdown text from Docling parser
        source_doc: Document name — used to gate the legal-numbering pass

    Returns:
        Ordered, deduplicated list of clause ID strings
    """
    seen: set[str] = set()
    ordered: list[str] = []

    # Build a position-indexed list of clause matches for pass 2 context.
    # Pass 1 and Pass 1b both contribute; they are merged and sorted by position
    # so Pass 2's sub-item attribution walks them in document order.
    clause_matches: list[tuple[int, int, str]] = []  # (start, end, clause_id)

    for match in CLAUSE_ID_PATTERN.finditer(markdown_text):
        clause_id = match.group(1)
        if clause_id not in seen:
            seen.add(clause_id)
            ordered.append(clause_id)
        clause_matches.append((match.start(), match.end(), clause_id))

    for match in CLAUSE_ID_LIST_ITEM_PATTERN.finditer(markdown_text):
        clause_id = match.group(1)
        if clause_id not in seen:
            seen.add(clause_id)
            ordered.append(clause_id)
        clause_matches.append((match.start(), match.end(), clause_id))

    clause_matches.sort(key=lambda m: m[0])

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

    # Legal-numbering pass — scoped to Cybersecurity Act 2018 only.
    # This document uses bare-number section headings and Arabic Part labels
    # rather than CCoP's X.Y.Z hierarchy. Without this pass the document would
    # contribute 0 entries to the inventory, blocking ground-truth validation
    # of the 57 citations that reference "section N" or "Part N".
    if source_doc == CYBERSECURITY_ACT_DOC_NAME:
        for section_match in LEGAL_SECTION_PATTERN.finditer(markdown_text):
            section_id = f"section {section_match.group(1)}"
            if section_id not in seen:
                seen.add(section_id)
                ordered.append(section_id)

        for part_match in LEGAL_PART_PATTERN.finditer(markdown_text):
            part_id = f"Part {part_match.group(1)}"
            if part_id not in seen:
                seen.add(part_id)
                ordered.append(part_id)

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
        clause_ids = extract_clause_ids(result.markdown, source_doc=doc_name)
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

    Handles three clause_id formats:
      - CCoP hierarchical: "5", "5.3", "5.3.1", "5.3.1(c)"
      - Legal section:     "section 11", "section 15A"
      - Legal Part:         "Part 3"

    Sort contract (groups first, then numerically within each group):
      - Group 0: CCoP hierarchical (default — sorted by numeric parts + letter)
      - Group 1: Legal Part
      - Group 2: Legal section

    Examples:
        "5"          -> (0, 5, 0, 0, 0, "")
        "5.3.1(c)"   -> (0, 5, 3, 1, 0, "c")
        "Part 3"     -> (1, 3, 0, 0, 0, "")
        "section 11" -> (2, 11, 0, 0, 0, "")
        "section 15A"-> (2, 15, 0, 0, 0, "A")
    """
    # Legal Part: "Part <N>"
    if clause_id.startswith("Part "):
        try:
            num = int(clause_id[5:].strip())
        except ValueError:
            num = 0
        return (1, num, 0, 0, 0, "")

    # Legal section: "section <N>" — optional suffix letter (e.g. "15A")
    if clause_id.startswith("section "):
        body = clause_id[8:].strip()
        m = re.match(r"^(\d+)([A-Z]?)$", body)
        if m:
            return (2, int(m.group(1)), 0, 0, 0, m.group(2))
        return (2, 0, 0, 0, 0, "")

    # CCoP hierarchical: "X.Y.Z" with optional "(letter)" suffix
    letter_suffix = ""
    if clause_id.endswith(")") and "(" in clause_id:
        base, letter_part = clause_id.rsplit("(", 1)
        letter_suffix = letter_part.rstrip(")")
        clause_id = base

    raw_parts = clause_id.split(".")
    try:
        numeric_parts = [int(p) for p in raw_parts]
    except ValueError:
        numeric_parts = [0]

    while len(numeric_parts) < 4:
        numeric_parts.append(0)

    return (0,) + tuple(numeric_parts[:4]) + (letter_suffix,)


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
