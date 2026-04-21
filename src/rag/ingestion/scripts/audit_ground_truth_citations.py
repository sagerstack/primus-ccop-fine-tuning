"""
Ground Truth Citation Auditor

Audits every v2 ground-truth test case's clause references against the
authoritative clause inventory and Qdrant corpus.  Three audit passes:

  Pass 1 — ID existence: checks metadata.clause_reference values against
            clause_inventory.json.  Flags any (clause_id, source_doc) pair
            that is absent from the inventory.

  Pass 2 — In-text citation: extracts dotted clause numbers and "section N"
            tokens from ground_truth.expected_response via regex, then checks
            each against the inventory.  Deduplicated per test case.

  Pass 3 — Semantic mismatch: for clause_references that PASSED Pass 1,
            fetches the clause body text from Qdrant by citation_id and
            computes cosine similarity against the expected_response embedding.
            Flags when similarity < threshold (default 0.35).

Outputs:
  - ground-truth-audit-report.md  — human-readable, one section per benchmark
  - ground-truth-audit-diff.json  — machine-readable change proposals; reviewer
                                    and accepted fields left blank for human review

The script is READ-ONLY with respect to JSONL files.
All correction proposals are flagged for human review.

Usage:
    cd src && poetry run python -m rag.ingestion.scripts.audit_ground_truth_citations \\
        --inventory src/rag/ingestion/fixtures/clause_inventory.json \\
        --test-suite-dir ground-truth/test-suite \\
        --report-dir .planning/phases/03.2-corpus-ground-truth-correctness/ \\
        --semantic-threshold 0.35
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from rag.infrastructure.adapters.qdrant.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Qdrant / embedding constants — hardcoded to match project defaults.
# (The script does not read Settings to avoid DI container startup costs.)
# ---------------------------------------------------------------------------
QDRANT_URL = "http://localhost:6333"
COLLECTION = "ccop_clauses_hybrid"
DENSE_MODEL = "BAAI/bge-large-en-v1.5"
SPARSE_MODEL = "Qdrant/bm25"

# ---------------------------------------------------------------------------
# Regex patterns for Pass 2 in-text citation extraction
# ---------------------------------------------------------------------------

# CCoP-style dotted clause: "5.3.1(c)", "5.3.1", "10.2", "2.1.1"
# Must be followed by a non-dot character (or end) to exclude "section 5.3"
# being captured by the bare-digit branch when the following char is a digit.
_DOTTED_CLAUSE_RE = re.compile(
    r"\b(\d+(?:\.\d+)+(?:\([a-z]\))?)\b"
)

# Matches version-number-like patterns to exclude from Pass 2 extraction.
# "CCoP 2.0", "version 1.0", "MAS TRM 2.0" — two-segment X.0 forms are
# version numbers, not clause IDs.  Any match of this pattern is filtered out.
_VERSION_NUMBER_RE = re.compile(r"^\d+\.0$")

# Phrase-form dotted clause: "Clause 5.3.1(c)", "clause 5.3.1"
_CLAUSE_PHRASE_RE = re.compile(
    r"[Cc]lause\s+(\d+(?:\.\d+)+(?:\([a-z]\))?)"
)

# "section N" / "Section N" — matches integer optionally followed by an
# uppercase letter (e.g. "section 15A").  The negative lookahead `(?!\.)` is
# critical: prevents "section 5.3" from matching — only bare integers qualify.
_SECTION_RE = re.compile(
    r"\b[Ss]ection\s+(\d+[A-Z]?)(?!\.)"
)

# ---------------------------------------------------------------------------
# Canonical source-doc names (must match clause_inventory.json exactly)
# ---------------------------------------------------------------------------
SOURCE_CCOP = "CCoP 2.0"
SOURCE_CYBERSECURITY_ACT = "Cybersecurity Act 2018"
SOURCE_RESPONSE_TO_FEEDBACK = "CCoP Response to Feedback"
SOURCE_SECURITY_BY_DESIGN = "Security By Design"
SOURCE_RISK_ASSESSMENT = "Risk Assessment Guide"
SOURCE_THREAT_MODELLING = "Threat Modelling Guide"
SOURCE_AUDITING = "Auditing Guidelines"

# Tokens in clause_reference values that indicate a Cybersecurity Act citation.
_CYBERSECURITY_ACT_TOKENS = {"cybersecurity act", "cybersecurity (amendment) act"}

# Recommended action constants
ACTION_CORRECT = "CORRECT"
ACTION_DEPRECATE = "DEPRECATE"
ACTION_HUMAN_REVIEW = "HUMAN_REVIEW"
ACTION_SKIP = "SKIP"  # not in report — used internally for skipped entries


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ParsedClauseRef:
    """Result of parsing one clause_reference string."""
    raw: str               # original string as it appears in the JSONL
    clause_id: str         # normalised clause ID (e.g. "5.3.1(c)", "section 11")
    source_doc: str        # canonical source document name
    skipped: bool = False  # True for refs we cannot validate (N/A, free-text, etc.)
    skip_reason: str = ""  # human-readable explanation when skipped


@dataclass
class AuditFlag:
    """One flagged citation across any of the three passes."""
    test_id: str
    benchmark_id: str
    pass_number: int           # 1, 2, or 3
    field_path: str            # e.g. "metadata.clause_reference[0]"
    old_value: str             # original citation string
    source_doc: str            # inferred source document
    suggested_value: str = ""  # nearest-neighbour suggestion from Qdrant
    confidence: float = 0.0   # cosine similarity of suggested clause, if available
    similarity_score: Optional[float] = None  # Pass 3 similarity (original vs clause)
    reason: str = ""           # human-readable reason for flagging
    action: str = ACTION_HUMAN_REVIEW  # CORRECT / DEPRECATE / HUMAN_REVIEW


# ---------------------------------------------------------------------------
# Inventory loading
# ---------------------------------------------------------------------------

def load_inventory(inventory_path: Path) -> set[tuple[str, str]]:
    """
    Load clause_inventory.json and return a set of (clause_id, source_doc) tuples.

    The set enables O(1) membership tests during Pass 1 and Pass 2.
    """
    with open(inventory_path, encoding="utf-8") as f:
        data = json.load(f)

    inventory: set[tuple[str, str]] = set()
    for entry in data["entries"]:
        inventory.add((entry["clause_id"], entry["source_doc"]))

    logger.info(
        f"Loaded inventory: {len(inventory)} entries across "
        f"{len(data['source_docs'])} source docs"
    )
    return inventory


# ---------------------------------------------------------------------------
# Clause reference parsing — Pass 1
# ---------------------------------------------------------------------------

def parse_clause_reference(raw: str) -> ParsedClauseRef:
    """
    Parse one clause_reference string into a (clause_id, source_doc) pair.

    Handles the following ground-truth formats found in the test suite:
      - Bare CCoP clauses:             "5.3.1(c)", "5.3.1", "10.2"
      - "CCoP 2.0 Section X.Y.Z":     → (X.Y.Z, "CCoP 2.0")
      - "CCoP 2.0 Section X.Y":        → (X.Y, "CCoP 2.0")
      - "CCoP 2.0 ..." (non-clause):   → skip (e.g. "CCoP 2.0 Annex A")
      - "Section N Cybersecurity Act": → ("section N", "Cybersecurity Act 2018")
      - "Section N(7) Cybersecurity":  → ("section N", "Cybersecurity Act 2018")
      - "Cybersecurity Act Section N": → ("section N", "Cybersecurity Act 2018")
      - Bare "Section N":              → ("section N", "Cybersecurity Act 2018")
      - "MAS TRM: X.Y.Z":             → (X.Y.Z, "MAS TRM")  [multi-reg B23]
      - "N/A", "Enforcement", etc.:    → skip
      - "RESPONSE-TO-FEEDBACK Q...":  → skip (not in inventory)
      - "IM8 framework":               → skip
    """
    raw = raw.strip()
    raw_lower = raw.lower()

    # ------------------------------------------------------------------
    # Explicit skip cases
    # ------------------------------------------------------------------
    skip_values = {
        "n/a", "enforcement", "scope definition", "form a1/a2",
        "im8 framework", "ccop 2.0 annex a", "ccop 2.0 ot addendum",
        "ccop 2.0 scope section", "ccop 2.0 digital boundary definition",
        "ccop 2.0 supply chain clauses",
        "cybersecurity (amendment) act 2024",
        "cybersecurity act schedule 1",
        "section 2 cybersecurity act definitions",
    }
    if raw_lower in skip_values:
        return ParsedClauseRef(
            raw=raw, clause_id="", source_doc="",
            skipped=True, skip_reason=f"Non-validatable reference: {raw!r}"
        )
    if raw_lower.startswith("response-to-feedback"):
        return ParsedClauseRef(
            raw=raw, clause_id="", source_doc="",
            skipped=True, skip_reason=f"Response-to-Feedback reference not in clause inventory: {raw!r}"
        )

    # ------------------------------------------------------------------
    # MAS TRM explicit prefix: "MAS TRM: 4.1.2"
    # ------------------------------------------------------------------
    mas_trm_match = re.match(r"^MAS\s+TRM\s*:\s*(.+)$", raw, re.IGNORECASE)
    if mas_trm_match:
        clause_id = mas_trm_match.group(1).strip()
        return ParsedClauseRef(
            raw=raw, clause_id=clause_id, source_doc="MAS TRM",
            skipped=False
        )

    # ------------------------------------------------------------------
    # "CCoP 2.0 Section X.Y.Z" → extract dotted clause
    # ------------------------------------------------------------------
    ccop_section_match = re.match(
        r"^CCoP\s+2\.0\s+[Ss]ection\s+(\d+(?:\.\d+)*(?:\([a-z]\))?)$",
        raw
    )
    if ccop_section_match:
        return ParsedClauseRef(
            raw=raw, clause_id=ccop_section_match.group(1), source_doc=SOURCE_CCOP
        )

    # ------------------------------------------------------------------
    # "CCoP 2.0 Section X.Y" with no match for a specific clause pattern
    # (above should have caught it; this is a belt-and-suspenders fallback)
    # "CCoP 2.0 ..." that we can't resolve → skip
    # ------------------------------------------------------------------
    if raw_lower.startswith("ccop 2.0"):
        # One more try: extract any dotted number from the string
        dotted = re.search(r"(\d+(?:\.\d+)+(?:\([a-z]\))?)", raw)
        if dotted:
            return ParsedClauseRef(
                raw=raw, clause_id=dotted.group(1), source_doc=SOURCE_CCOP
            )
        return ParsedClauseRef(
            raw=raw, clause_id="", source_doc="",
            skipped=True, skip_reason=f"CCoP 2.0 reference without resolvable clause ID: {raw!r}"
        )

    # ------------------------------------------------------------------
    # Cybersecurity Act citations in various formats
    # ------------------------------------------------------------------
    is_cybersec = any(tok in raw_lower for tok in _CYBERSECURITY_ACT_TOKENS)

    # "Section N Cybersecurity Act" / "Cybersecurity Act Section N"
    # "Section N(7) Cybersecurity Act" → base section only (e.g. "section 11")
    if is_cybersec:
        # Try to extract section number
        sec_match = re.search(r"[Ss]ection\s+(\d+[A-Z]?)(?:\(\d+\))?", raw)
        if sec_match:
            return ParsedClauseRef(
                raw=raw,
                clause_id=f"section {sec_match.group(1)}",
                source_doc=SOURCE_CYBERSECURITY_ACT
            )
        # "Cybersecurity Act Section 11(7)" → "section 11"
        fallback_sec = re.search(r"(\d+[A-Z]?)", raw)
        if fallback_sec:
            return ParsedClauseRef(
                raw=raw,
                clause_id=f"section {fallback_sec.group(1)}",
                source_doc=SOURCE_CYBERSECURITY_ACT
            )
        return ParsedClauseRef(
            raw=raw, clause_id="", source_doc="",
            skipped=True,
            skip_reason=f"Cybersecurity Act citation without extractable section: {raw!r}"
        )

    # ------------------------------------------------------------------
    # Bare "Section N" / "Section N(7)" — assumed Cybersecurity Act
    # "Section 11" → ("section 11", "Cybersecurity Act 2018")
    # "Section 17" → same
    # ------------------------------------------------------------------
    bare_section_match = re.match(r"^[Ss]ection\s+(\d+[A-Z]?)(?:\(\d+\))?$", raw)
    if bare_section_match:
        return ParsedClauseRef(
            raw=raw,
            clause_id=f"section {bare_section_match.group(1)}",
            source_doc=SOURCE_CYBERSECURITY_ACT
        )

    # ------------------------------------------------------------------
    # Bare CCoP dotted clause: "5.3.1(c)", "5.3.1", "10.2"
    # ------------------------------------------------------------------
    bare_clause_match = re.match(r"^(\d+(?:\.\d+)*(?:\([a-z]\))?)$", raw)
    if bare_clause_match:
        return ParsedClauseRef(
            raw=raw, clause_id=raw, source_doc=SOURCE_CCOP
        )

    # ------------------------------------------------------------------
    # Fallback: can't parse — skip with reason
    # ------------------------------------------------------------------
    return ParsedClauseRef(
        raw=raw, clause_id="", source_doc="",
        skipped=True,
        skip_reason=f"Could not parse clause reference into (clause_id, source_doc): {raw!r}"
    )


# ---------------------------------------------------------------------------
# Pass 2 — in-text citation extraction
# ---------------------------------------------------------------------------

def extract_intext_citations(expected_response: str) -> list[tuple[str, str]]:
    """
    Extract clause numbers cited inline in expected_response text.

    Returns a deduplicated list of (clause_id, source_doc) pairs.
    The CCoP dotted form goes to SOURCE_CCOP.
    The "section N" form goes to SOURCE_CYBERSECURITY_ACT.

    Deduplication is over the (clause_id, source_doc) pair.
    """
    seen: set[tuple[str, str]] = set()
    results: list[tuple[str, str]] = []

    def _add(clause_id: str, source_doc: str) -> None:
        key = (clause_id, source_doc)
        if key not in seen:
            seen.add(key)
            results.append(key)

    # Phrase-form first (higher specificity) to avoid double-counting
    for m in _CLAUSE_PHRASE_RE.finditer(expected_response):
        _add(m.group(1), SOURCE_CCOP)

    # Bare dotted — skip if already captured via phrase form.
    # Filter out version-number-like patterns (e.g. "2.0" from "CCoP 2.0").
    for m in _DOTTED_CLAUSE_RE.finditer(expected_response):
        token = m.group(1)
        if _VERSION_NUMBER_RE.match(token):
            continue
        _add(token, SOURCE_CCOP)

    # "section N" — Cybersecurity Act citations
    for m in _SECTION_RE.finditer(expected_response):
        _add(f"section {m.group(1)}", SOURCE_CYBERSECURITY_ACT)

    return results


# ---------------------------------------------------------------------------
# Qdrant helpers for Pass 3
# ---------------------------------------------------------------------------

def fetch_clause_text(
    client: QdrantClient, clause_id: str, source_doc: str
) -> Optional[str]:
    """
    Retrieve the primary clause body text from Qdrant by citation_id.

    The citation_id stored in Qdrant follows the pattern:
        "{source_doc}::{clause_id}"

    Falls back to stripping the item-letter suffix (e.g. "5.3.1(c)" → "5.3.1")
    if no exact match found — clause-level chunks embed all sub-items.

    Returns the chunk text, or None if not found.
    """
    # Build candidate citation IDs to try
    candidates = [f"{source_doc}::{clause_id}"]

    # Item-letter fallback: "5.3.1(c)" → try "5.3.1" as well
    if clause_id.endswith(")") and "(" in clause_id:
        base = clause_id.rsplit("(", 1)[0]
        candidates.append(f"{source_doc}::{base}")

    for citation_id in candidates:
        result = client.scroll(
            collection_name=COLLECTION,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="citation_id",
                        match=MatchValue(value=citation_id),
                    )
                ]
            ),
            limit=1,
            with_payload=True,
            with_vectors=False,
        )
        if result[0]:
            return result[0][0].payload.get("text", "")

    return None


def nearest_ccop_clause(
    embedding_service: EmbeddingService,
    client: QdrantClient,
    query_text: str,
    source_doc: str,
) -> tuple[str, float]:
    """
    Find the nearest CCoP clause in Qdrant using dense embedding similarity.

    Queries Qdrant with the expected_response embedding, filtered to the
    given source document.  Returns (suggested_clause_id, score).
    """
    query_embedding = embedding_service.embed_query(query_text)

    results = client.query_points(
        collection_name=COLLECTION,
        query=query_embedding,
        using="dense",
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="document_source",
                    match=MatchValue(value=source_doc),
                )
            ]
        ),
        limit=1,
        with_payload=True,
    )

    if not results.points:
        return ("", 0.0)

    hit = results.points[0]
    # Extract clause_id from citation_id: "CCoP 2.0::5.3.1" → "5.3.1"
    citation_id = hit.payload.get("citation_id", "")
    # Strip document prefix and optional table/chunk suffix
    parts = citation_id.split("::")
    # citation_id format: "{source_doc}::{clause_id}" or "{source_doc}::{clause_id}::table::N"
    suggested_clause = parts[1] if len(parts) >= 2 else citation_id
    score = float(hit.score) if hit.score is not None else 0.0
    return (suggested_clause, score)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two normalized vectors."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ---------------------------------------------------------------------------
# Load all test cases
# ---------------------------------------------------------------------------

def load_test_suite(test_suite_dir: Path) -> list[dict]:
    """
    Load every JSONL file under test_suite_dir.

    Returns a flat list of test case dicts with a "_source_file" key injected.
    Skips deprecated test cases (status == "deprecated").
    """
    test_cases: list[dict] = []
    jsonl_files = sorted(test_suite_dir.glob("*.jsonl"))

    if not jsonl_files:
        raise RuntimeError(f"No JSONL files found under {test_suite_dir}")

    for path in jsonl_files:
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    tc = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON at {path}:{lineno} — {e}")
                    continue

                if tc.get("status") == "deprecated":
                    logger.debug(
                        f"Skipping deprecated case {tc.get('test_id', '?')} in {path.name}"
                    )
                    continue

                tc["_source_file"] = path.name
                test_cases.append(tc)

    logger.info(f"Loaded {len(test_cases)} test cases from {len(jsonl_files)} files")
    return test_cases


# ---------------------------------------------------------------------------
# Core audit logic
# ---------------------------------------------------------------------------

def run_pass1(
    test_cases: list[dict],
    inventory: set[tuple[str, str]],
) -> list[AuditFlag]:
    """
    Pass 1: Check every metadata.clause_reference against the inventory.

    Returns list of AuditFlags for any reference not found in the inventory.
    """
    flags: list[AuditFlag] = []

    for tc in test_cases:
        test_id = tc.get("test_id", "?")
        benchmark_id = tc.get("benchmark_id", "?")
        clause_refs: list[str] = tc.get("metadata", {}).get("clause_reference", [])

        for idx, raw_ref in enumerate(clause_refs):
            parsed = parse_clause_reference(raw_ref)

            if parsed.skipped:
                logger.debug(
                    f"  Pass 1 skip [{test_id}] clause_reference[{idx}]={raw_ref!r}: "
                    f"{parsed.skip_reason}"
                )
                continue

            key = (parsed.clause_id, parsed.source_doc)
            if key not in inventory:
                flags.append(AuditFlag(
                    test_id=test_id,
                    benchmark_id=benchmark_id,
                    pass_number=1,
                    field_path=f"metadata.clause_reference[{idx}]",
                    old_value=raw_ref,
                    source_doc=parsed.source_doc,
                    reason=(
                        f"clause_id={parsed.clause_id!r} not found in inventory "
                        f"for source_doc={parsed.source_doc!r}"
                    ),
                    action=ACTION_HUMAN_REVIEW,
                ))

    logger.info(f"Pass 1 complete: {len(flags)} flags")
    return flags


def run_pass2(
    test_cases: list[dict],
    inventory: set[tuple[str, str]],
) -> list[AuditFlag]:
    """
    Pass 2: Extract in-text clause citations from expected_response and
    check each against the inventory.

    Returns list of AuditFlags for any citation not found in the inventory.
    Skips Cybersecurity Act citations for documents where inventory has
    no entries for that doc (shouldn't happen post Plan-05, but guarded).
    """
    flags: list[AuditFlag] = []

    # Pre-compute the set of source_docs in inventory for fast filtering
    inventory_docs: set[str] = {source_doc for _, source_doc in inventory}

    for tc in test_cases:
        test_id = tc.get("test_id", "?")
        benchmark_id = tc.get("benchmark_id", "?")
        expected_response: str = (
            tc.get("ground_truth", {}).get("expected_response", "")
        )

        if not expected_response:
            continue

        citations = extract_intext_citations(expected_response)

        for clause_id, source_doc in citations:
            if source_doc not in inventory_docs:
                # Source doc not covered by inventory; cannot validate — skip
                logger.debug(
                    f"  Pass 2 skip [{test_id}] source_doc={source_doc!r} not in inventory"
                )
                continue

            key = (clause_id, source_doc)
            if key not in inventory:
                flags.append(AuditFlag(
                    test_id=test_id,
                    benchmark_id=benchmark_id,
                    pass_number=2,
                    field_path="ground_truth.expected_response",
                    old_value=clause_id,
                    source_doc=source_doc,
                    reason=(
                        f"In-text citation {clause_id!r} not found in inventory "
                        f"for source_doc={source_doc!r}"
                    ),
                    action=ACTION_HUMAN_REVIEW,
                ))

    logger.info(f"Pass 2 complete: {len(flags)} flags")
    return flags


def run_pass3(
    test_cases: list[dict],
    inventory: set[tuple[str, str]],
    client: QdrantClient,
    embedding_service: EmbeddingService,
    threshold: float,
) -> list[AuditFlag]:
    """
    Pass 3: Semantic mismatch check.

    For each clause_reference that PASSED Pass 1 (i.e. exists in inventory
    AND is for CCoP 2.0 or another Qdrant-indexed source):
      1. Fetch clause body text from Qdrant by citation_id.
      2. Compute cosine similarity between clause body and expected_response.
      3. Flag if similarity < threshold.

    Returns list of AuditFlags for semantic mismatches.
    """
    flags: list[AuditFlag] = []

    # Only run Pass 3 for source docs that are indexed in Qdrant
    # (we only check CCoP 2.0 — other docs may or may not be indexed)
    qdrant_indexed_docs = {SOURCE_CCOP}

    # Cache embeddings of expected_response to avoid re-embedding per clause_ref
    # Key: test_id, Value: embedding vector
    response_embedding_cache: dict[str, list[float]] = {}

    total_checked = 0
    not_indexed = 0

    for tc in test_cases:
        test_id = tc.get("test_id", "?")
        benchmark_id = tc.get("benchmark_id", "?")
        clause_refs: list[str] = tc.get("metadata", {}).get("clause_reference", [])
        expected_response: str = (
            tc.get("ground_truth", {}).get("expected_response", "")
        )

        if not expected_response:
            continue

        for idx, raw_ref in enumerate(clause_refs):
            parsed = parse_clause_reference(raw_ref)

            if parsed.skipped:
                continue

            key = (parsed.clause_id, parsed.source_doc)
            if key not in inventory:
                # Already flagged in Pass 1 — skip Pass 3
                continue

            if parsed.source_doc not in qdrant_indexed_docs:
                # Cannot perform semantic check — not indexed
                continue

            total_checked += 1

            # Fetch clause body from Qdrant
            clause_text = fetch_clause_text(client, parsed.clause_id, parsed.source_doc)
            if clause_text is None:
                not_indexed += 1
                flags.append(AuditFlag(
                    test_id=test_id,
                    benchmark_id=benchmark_id,
                    pass_number=3,
                    field_path=f"metadata.clause_reference[{idx}]",
                    old_value=raw_ref,
                    source_doc=parsed.source_doc,
                    reason=(
                        f"clause_id={parsed.clause_id!r} exists in inventory but "
                        f"NOT indexed in Qdrant — possible sub-goal A regression"
                    ),
                    action=ACTION_HUMAN_REVIEW,
                ))
                continue

            # Compute cosine similarity
            # Cache response embedding to avoid repeat work
            if test_id not in response_embedding_cache:
                response_embedding_cache[test_id] = embedding_service.embed_documents(
                    [expected_response]
                )[0]

            clause_embedding = embedding_service.embed_documents([clause_text])[0]
            sim = cosine_similarity(
                response_embedding_cache[test_id], clause_embedding
            )

            if sim < threshold:
                # Nearest-neighbour suggestion
                suggested_clause, suggested_score = nearest_ccop_clause(
                    embedding_service, client, expected_response, parsed.source_doc
                )

                flags.append(AuditFlag(
                    test_id=test_id,
                    benchmark_id=benchmark_id,
                    pass_number=3,
                    field_path=f"metadata.clause_reference[{idx}]",
                    old_value=raw_ref,
                    source_doc=parsed.source_doc,
                    suggested_value=suggested_clause,
                    confidence=suggested_score,
                    similarity_score=sim,
                    reason=(
                        f"Semantic similarity={sim:.3f} (threshold={threshold}) — "
                        f"expected_response may not be grounded in {parsed.clause_id!r}"
                    ),
                    action=ACTION_HUMAN_REVIEW,
                ))

    logger.info(
        f"Pass 3 complete: {len(flags)} flags "
        f"({total_checked} checked, {not_indexed} not indexed in Qdrant)"
    )
    return flags


# ---------------------------------------------------------------------------
# Nearest-neighbour suggestion enrichment for Pass 1 & Pass 2 flags
# ---------------------------------------------------------------------------

def enrich_flags_with_suggestions(
    flags: list[AuditFlag],
    test_cases_by_id: dict[str, dict],
    client: QdrantClient,
    embedding_service: EmbeddingService,
) -> None:
    """
    Enrich Pass 1 and Pass 2 flags with nearest-neighbour suggestions from Qdrant.

    Mutates flags in place.  Only enriches CCoP 2.0 references (Qdrant-indexed).
    """
    for flag in flags:
        if flag.pass_number not in (1, 2):
            continue
        if flag.source_doc != SOURCE_CCOP:
            continue
        if flag.suggested_value:
            continue  # already enriched

        tc = test_cases_by_id.get(flag.test_id)
        if not tc:
            continue

        expected_response: str = (
            tc.get("ground_truth", {}).get("expected_response", "")
        )
        if not expected_response:
            continue

        suggested_clause, suggested_score = nearest_ccop_clause(
            embedding_service, client, expected_response, SOURCE_CCOP
        )
        flag.suggested_value = suggested_clause
        flag.confidence = suggested_score

        # Per CONTEXT.md: flag-for-human-review only.  Suggested value is a
        # nearest-neighbour hint; the human decides whether to accept it.
        # Action stays HUMAN_REVIEW for all enriched flags.
        # (CORRECT and DEPRECATE are reserved for cases where confidence is
        #  extremely high — set by the human reviewer in the diff JSON.)


# ---------------------------------------------------------------------------
# Deduplication across passes
# ---------------------------------------------------------------------------

def deduplicate_flags(flags: list[AuditFlag]) -> list[AuditFlag]:
    """
    Deduplicate flags: for a given (test_id, old_value, source_doc), keep the
    lowest pass number flag (Pass 1 supersedes Pass 2 for same citation).

    Pass 3 flags are kept separately (they concern semantic mismatch of valid IDs).
    """
    seen_pass12: dict[tuple[str, str, str], AuditFlag] = {}
    pass3_flags: list[AuditFlag] = []

    for flag in flags:
        if flag.pass_number == 3:
            pass3_flags.append(flag)
            continue

        key = (flag.test_id, flag.old_value, flag.source_doc)
        if key not in seen_pass12:
            seen_pass12[key] = flag
        else:
            # Keep whichever flag has the lower pass number
            if flag.pass_number < seen_pass12[key].pass_number:
                seen_pass12[key] = flag

    result = list(seen_pass12.values()) + pass3_flags
    result.sort(key=lambda f: (f.benchmark_id, f.test_id, f.pass_number))
    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _action_badge(action: str) -> str:
    badges = {
        ACTION_CORRECT: "[CORRECT]",
        ACTION_DEPRECATE: "[DEPRECATE]",
        ACTION_HUMAN_REVIEW: "[HUMAN_REVIEW]",
    }
    return badges.get(action, f"[{action}]")


def generate_report(
    flags: list[AuditFlag],
    stats: dict,
    threshold: float,
    report_path: Path,
) -> None:
    """Write the human-readable markdown audit report."""

    # Group flags by benchmark_id
    by_benchmark: dict[str, list[AuditFlag]] = {}
    for flag in flags:
        by_benchmark.setdefault(flag.benchmark_id, []).append(flag)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = [
        "# Ground Truth Citation Audit Report",
        "",
        f"**Generated:** {now}",
        f"**Semantic threshold (Pass 3):** {threshold}",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Test cases audited | {stats['total_cases']} |",
        f"| clause_reference values audited (Pass 1) | {stats['pass1_audited']} |",
        f"| In-text citations extracted (Pass 2) | {stats['pass2_extracted']} |",
        f"| Clause references semantically checked (Pass 3) | {stats['pass3_checked']} |",
        f"| **Pass 1 flags (invalid clause_reference ID)** | **{stats['pass1_flags']}** |",
        f"| **Pass 2 flags (invalid in-text citation)** | **{stats['pass2_flags']}** |",
        f"| **Pass 3 flags (semantic mismatch)** | **{stats['pass3_flags']}** |",
        f"| **Total unique flags** | **{stats['total_flags']}** |",
        "",
        "### Recommended Actions",
        "",
        f"| Action | Count |",
        f"|--------|-------|",
        f"| CORRECT (clear nearest-neighbour mapping) | {stats['action_correct']} |",
        f"| DEPRECATE (low confidence, no salvageable fix) | {stats['action_deprecate']} |",
        f"| HUMAN_REVIEW (requires expert judgment) | {stats['action_human_review']} |",
        "",
        "---",
        "",
        "## Flagged Cases by Benchmark",
        "",
    ]

    if not flags:
        lines.append("*No flags found. All citations validated successfully.*")
    else:
        for bm_id in sorted(by_benchmark.keys()):
            bm_flags = by_benchmark[bm_id]
            lines.append(f"### {bm_id}")
            lines.append("")

            for flag in bm_flags:
                sim_str = (
                    f", similarity={flag.similarity_score:.3f}"
                    if flag.similarity_score is not None
                    else ""
                )
                if flag.suggested_value:
                    suggestion_line = (
                        f"  - **Suggested correction:** `{flag.suggested_value}` "
                        f"(nearest-neighbour confidence={flag.confidence:.3f})"
                    )
                else:
                    suggestion_line = "  - **Suggested correction:** none (no indexed clause matched)"

                lines.append(
                    f"- **{flag.test_id}** | Pass {flag.pass_number} | "
                    f"`{flag.field_path}` | {_action_badge(flag.action)}"
                )
                lines.append(
                    f"  - **Original:** `{flag.old_value}` (source: {flag.source_doc})"
                )
                lines.append(f"  - **Reason:** {flag.reason}{sim_str}")
                lines.append(suggestion_line)
                lines.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Report written to {report_path}")


def generate_diff(
    flags: list[AuditFlag],
    diff_path: Path,
) -> None:
    """
    Write the machine-readable JSON diff.

    Each entry has reviewer and accepted fields left blank for human review.
    """
    today = date.today().isoformat()

    entries: list[dict[str, Any]] = []
    for flag in flags:
        entries.append({
            "test_id": flag.test_id,
            "benchmark_id": flag.benchmark_id,
            "pass": flag.pass_number,
            "field_path": flag.field_path,
            "old_value": flag.old_value,
            "source_doc": flag.source_doc,
            "suggested_value": flag.suggested_value,
            "confidence": round(flag.confidence, 4) if flag.confidence else 0.0,
            "similarity_score": (
                round(flag.similarity_score, 4)
                if flag.similarity_score is not None
                else None
            ),
            "reason": flag.reason,
            "action": flag.action,
            "date": today,
            "reviewer": "",
            "accepted": None,
        })

    diff_path.parent.mkdir(parents=True, exist_ok=True)
    with open(diff_path, "w", encoding="utf-8") as f:
        json.dump({"entries": entries}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    logger.info(f"Diff written to {diff_path} ({len(entries)} entries)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit ground truth clause references against clause inventory + Qdrant"
    )
    parser.add_argument(
        "--inventory",
        required=True,
        help="Path to clause_inventory.json",
    )
    parser.add_argument(
        "--test-suite-dir",
        required=True,
        help="Directory containing *.jsonl ground truth files",
    )
    parser.add_argument(
        "--report-dir",
        required=True,
        help="Output directory for audit-report.md and audit-diff.json",
    )
    parser.add_argument(
        "--semantic-threshold",
        type=float,
        default=0.35,
        help="Cosine similarity threshold for Pass 3 (default: 0.35)",
    )
    parser.add_argument(
        "--skip-pass3",
        action="store_true",
        help="Skip Pass 3 (semantic mismatch) — useful for quick Pass 1/2 runs",
    )
    parser.add_argument(
        "--qdrant-url",
        default=QDRANT_URL,
        help=f"Qdrant REST API URL (default: {QDRANT_URL})",
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

    inventory_path = Path(args.inventory)
    test_suite_dir = Path(args.test_suite_dir)
    report_dir = Path(args.report_dir)
    report_path = report_dir / "ground-truth-audit-report.md"
    diff_path = report_dir / "ground-truth-audit-diff.json"
    threshold = args.semantic_threshold

    # ------------------------------------------------------------------
    # Validate inputs
    # ------------------------------------------------------------------
    if not inventory_path.exists():
        logger.error(f"Inventory file not found: {inventory_path}")
        sys.exit(1)

    if not test_suite_dir.exists():
        logger.error(f"Test suite directory not found: {test_suite_dir}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Verify Qdrant availability (required for Pass 3)
    # ------------------------------------------------------------------
    if not args.skip_pass3:
        logger.info(f"Verifying Qdrant at {args.qdrant_url} ...")
        try:
            client = QdrantClient(url=args.qdrant_url, timeout=60)
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            if COLLECTION not in collection_names:
                logger.error(
                    f"FATAL: Qdrant collection '{COLLECTION}' not found. "
                    f"Available: {collection_names}. "
                    f"Run sub-goal A ingestion before the semantic audit, "
                    f"or use --skip-pass3."
                )
                sys.exit(1)
            logger.info(f"Qdrant OK — collection '{COLLECTION}' found")
        except Exception as e:
            logger.error(
                f"FATAL: Cannot connect to Qdrant at {args.qdrant_url}: {e}. "
                f"Start Qdrant first, or use --skip-pass3."
            )
            sys.exit(1)
    else:
        client = None
        logger.info("Skipping Pass 3 (--skip-pass3 flag set)")

    # ------------------------------------------------------------------
    # Load inputs
    # ------------------------------------------------------------------
    inventory = load_inventory(inventory_path)
    test_cases = load_test_suite(test_suite_dir)

    test_cases_by_id: dict[str, dict] = {
        tc.get("test_id", ""): tc for tc in test_cases
    }

    # ------------------------------------------------------------------
    # Pass 1 — ID existence
    # ------------------------------------------------------------------
    logger.info("=== Pass 1: ID existence check ===")
    pass1_flags = run_pass1(test_cases, inventory)

    # Count audited (non-skipped) clause_reference values for stats
    pass1_audited = 0
    for tc in test_cases:
        for raw_ref in tc.get("metadata", {}).get("clause_reference", []):
            if not parse_clause_reference(raw_ref).skipped:
                pass1_audited += 1

    # ------------------------------------------------------------------
    # Pass 2 — In-text citation check
    # ------------------------------------------------------------------
    logger.info("=== Pass 2: In-text citation check ===")
    pass2_flags = run_pass2(test_cases, inventory)

    # Count extracted citations for stats
    pass2_extracted = 0
    for tc in test_cases:
        expected_response = tc.get("ground_truth", {}).get("expected_response", "")
        pass2_extracted += len(extract_intext_citations(expected_response))

    # ------------------------------------------------------------------
    # Pass 3 — Semantic mismatch (requires Qdrant)
    # ------------------------------------------------------------------
    pass3_flags: list[AuditFlag] = []
    pass3_checked = 0

    if not args.skip_pass3:
        logger.info("=== Pass 3: Semantic mismatch check ===")
        logger.info("Loading BGE embedding model (this may take 30-60s) ...")
        embedding_service = EmbeddingService(
            dense_model_name=DENSE_MODEL,
            sparse_model_name=SPARSE_MODEL,
        )

        # Count how many we'll check for stats
        qdrant_docs = {SOURCE_CCOP}
        for tc in test_cases:
            for raw_ref in tc.get("metadata", {}).get("clause_reference", []):
                parsed = parse_clause_reference(raw_ref)
                if not parsed.skipped and (parsed.clause_id, parsed.source_doc) in inventory:
                    if parsed.source_doc in qdrant_docs:
                        pass3_checked += 1

        pass3_flags = run_pass3(
            test_cases, inventory, client, embedding_service, threshold
        )

        # Enrich Pass 1 and 2 flags with nearest-neighbour suggestions
        logger.info("Enriching Pass 1/2 flags with nearest-neighbour suggestions ...")
        enrich_flags_with_suggestions(
            pass1_flags + pass2_flags, test_cases_by_id, client, embedding_service
        )

    # ------------------------------------------------------------------
    # Combine and deduplicate
    # ------------------------------------------------------------------
    all_flags = deduplicate_flags(pass1_flags + pass2_flags + pass3_flags)

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------
    action_counts: dict[str, int] = {
        ACTION_CORRECT: 0,
        ACTION_DEPRECATE: 0,
        ACTION_HUMAN_REVIEW: 0,
    }
    for flag in all_flags:
        if flag.action in action_counts:
            action_counts[flag.action] += 1

    stats = {
        "total_cases": len(test_cases),
        "pass1_audited": pass1_audited,
        "pass1_flags": len(pass1_flags),
        "pass2_extracted": pass2_extracted,
        "pass2_flags": len(pass2_flags),
        "pass3_checked": pass3_checked,
        "pass3_flags": len(pass3_flags),
        "total_flags": len(all_flags),
        "action_correct": action_counts[ACTION_CORRECT],
        "action_deprecate": action_counts[ACTION_DEPRECATE],
        "action_human_review": action_counts[ACTION_HUMAN_REVIEW],
    }

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    generate_report(all_flags, stats, threshold, report_path)
    generate_diff(all_flags, diff_path)

    # ------------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("GROUND TRUTH CITATION AUDIT COMPLETE")
    print("=" * 60)
    print(f"Test cases audited:           {stats['total_cases']}")
    print(f"Pass 1 — clause_reference:    {stats['pass1_audited']} checked, "
          f"{stats['pass1_flags']} flagged")
    print(f"Pass 2 — in-text citations:   {stats['pass2_extracted']} extracted, "
          f"{stats['pass2_flags']} flagged")
    print(f"Pass 3 — semantic mismatch:   {stats['pass3_checked']} checked, "
          f"{stats['pass3_flags']} flagged")
    print(f"Total unique flags:           {stats['total_flags']}")
    print()
    print(f"  CORRECT:      {stats['action_correct']}")
    print(f"  DEPRECATE:    {stats['action_deprecate']}")
    print(f"  HUMAN_REVIEW: {stats['action_human_review']}")
    print()
    print(f"Report: {report_path}")
    print(f"Diff:   {diff_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
