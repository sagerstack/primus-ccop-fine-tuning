"""
Coverage Checker (D-14 / D-17)

Curation-time diagnostics that diff any candidate ontology draft against:

  - `benchmark_coverage`      (D-14) — does every one of the 18 benchmark
    definitions map to at least one node type in the draft?
  - `gold_relation_coverage`  (D-17) — does the draft's relationship-type
    vocabulary cover every relation named in the hand-authored gold triples
    (eval-report xlsx col 22 `graph_relation`)?

Both functions are READ-ONLY report generators consumed by the human
curation gate (a, plan 10-03) — they never mutate the ontology draft. Both
accept an `ontology` dict matching the
`neo4j_graphrag.experimental.components.schema.GraphSchema` shape:
`{"node_types": [...], "relationship_types": [...], "patterns": [...]}`.
`node_types` entries may be plain strings or dicts with a `label` key (plus
optional `description`, `example_terms`, `provenance`); `relationship_types`
is always a flat list of strings (GraphSchema constraint — relation-level
provenance/ambiguity metadata lives in a sibling `relationship_type_metadata`
dict keyed by relation name, populated by `method_c_synthesis.py`).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from rag.graph.ontology.gold_relation_parser import CaseGoldRelations, parse_gold_relations

logger = logging.getLogger(__name__)

# Small stopword list for the D-14 keyword-overlap heuristic — trimmed to
# common regulatory-prose filler words that would otherwise create false
# "coverage" matches against nearly every node type.
_STOPWORDS = {
    "this", "that", "with", "from", "shall", "have", "were", "been",
    "will", "also", "must", "into", "their", "which", "does", "when",
    "what", "such", "than", "then", "they", "them", "these", "those",
    "each", "only", "over", "under", "within", "should", "about", "would",
    "could", "there", "where", "while", "being", "case", "used", "example",
}

_TOKEN_RE = re.compile(r"[a-z]{4,}")


def _tokenize(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS}


def _node_type_label(entry: Any) -> str:
    if isinstance(entry, str):
        return entry
    return str(entry.get("label", ""))


def _node_type_tokens_and_provenance(entry: Any) -> tuple[set[str], list[str]]:
    if isinstance(entry, str):
        return _tokenize(entry), []
    label = str(entry.get("label", ""))
    description = str(entry.get("description", "") or "")
    example_terms = entry.get("example_terms", []) or []
    provenance = entry.get("provenance", []) or []
    if isinstance(provenance, str):
        provenance = [provenance]
    text = " ".join([label, description, *[str(t) for t in example_terms]])
    return _tokenize(text), [str(p) for p in provenance]


def _relationship_type_labels(ontology: dict) -> set[str]:
    return {str(r) for r in ontology.get("relationship_types", [])}


# ---------------------------------------------------------------------------
# Gold-relation normalization (curation gate a — decisions 2b + 2e)
# ---------------------------------------------------------------------------
# Collapse semantic-duplicate / inverse-direction gold verbs onto the
# ontology's CANONICAL relation types BEFORE the D-17 missing-set diff, so the
# schema stays lean (no synonym fragmentation, per the gate's governing
# principle) while coverage stays honest. This does NOT overfit the schema to
# the gold's surface verbs -- it maps the gold's phrasing onto the schema, not
# the reverse.
GOLD_RELATION_SYNONYM_MAP: dict[str, str] = {
    # 2b -- collapse onto canonical (obligation verbs -> REQUIRES, etc.)
    "MANDATED_BY": "REQUIRES",
    "REQUIRED_BY": "REQUIRES",
    "MANDATORY_FOR": "REQUIRES",
    "MUST_INCLUDE": "REQUIRES",
    "MUST_DETAIL": "REQUIRES",
    "MUST_MAINTAIN": "REQUIRES",
    "MUST_SEPARATELY_COMPLY_WITH": "REQUIRES",
    "LEGALLY_OBLIGED_TO_COMPLY_WITH": "REQUIRES",
    "GOVERNED_BY": "GOVERNS",          # inverse direction
    "SUBJECT_TO": "APPLIES_TO",        # inverse direction
    "NOT_DEFINED_IN": "DEFINES_NO",
    "DOES_NOT_DEFINE": "DEFINES_NO",
    "PREVENTS": "MITIGATES",
    "PREVENT": "MITIGATES",
    "ASSESSES": "AUDITS",
    "LEAVES": "CREATES_RISK",
    # 2e -- best-judgment PROVISIONAL collapse; each flagged for gate-b
    # (plan 10-04) reconciliation in the SUMMARY, not silently locked.
    "VIOLATES": "CANNOT_SATISFY",      # active breach vs inability -- provisional
    "MAY_REQUEST": "APPLIES_FOR_WAIVER",  # waiver-request context -- provisional
    "ADDRESSES": "MITIGATES",          # generic "addresses a risk" -- provisional
}

# Gold verbs intentionally NOT modelled as extraction relation types. Remaining
# post-normalization "missing" entries are expected to be exactly these:
#   - hierarchy verbs owned by the deterministic clause backbone (decision 2c)
#   - junk prose fragments, not reusable relation types (decision 2d)
INTENTIONALLY_EXCLUDED_GOLD_RELATIONS: frozenset[str] = frozenset(
    {
        "INCLUDES", "PART_OF", "HAS_CHILDREN", "SPANS",  # 2c -- clause backbone owns hierarchy
        "ARE", "TO", "CANNOT", "LISTS", "MUST_BE",       # 2d -- junk prose fragments
    }
)


def normalize_gold_relation(relation: str) -> str:
    """Map a raw gold relation label onto its ontology canonical (identity if unmapped)."""
    return GOLD_RELATION_SYNONYM_MAP.get(relation, relation)


# ---------------------------------------------------------------------------
# D-17 — gold-relation coverage
# ---------------------------------------------------------------------------


def gold_relation_coverage_from_cases(
    ontology: dict, cases: list[CaseGoldRelations], normalize: bool = True
) -> dict[str, Any]:
    """
    Pure D-17 diff over already-parsed cases -- no file I/O, unit-testable.

    When `normalize` is True (default), each gold relation label is first mapped
    onto its ontology canonical via GOLD_RELATION_SYNONYM_MAP (curation gate a,
    decisions 2b/2e) before diffing against the ontology's relationship-type
    vocabulary. The returned `missing_relations` is further split into:
      - `unresolved_missing`: gold canonicals absent from the ontology AND not
        on the intentionally-excluded list -- these are real schema gaps.
      - `intentionally_excluded_missing`: gold verbs deliberately not modelled
        (clause-backbone hierarchy + junk, decisions 2c/2d).
    """

    def _norm_set(relations: set[str]) -> set[str]:
        return {normalize_gold_relation(r) for r in relations} if normalize else set(relations)

    ontology_relationship_types = _relationship_type_labels(ontology)

    gold_relation_types: set[str] = set()
    per_case: dict[str, dict[str, Any]] = {}
    for case in cases:
        normed = _norm_set(case.relation_types)
        gold_relation_types |= normed
        per_case[case.test_id] = {
            "relation_types": sorted(case.relation_types),
            "normalized_relation_types": sorted(normed),
            "clause_citations": case.clause_citations,
            "missing_relations": sorted(normed - ontology_relationship_types),
        }

    missing_relations = sorted(gold_relation_types - ontology_relationship_types)
    intentionally_excluded_missing = sorted(
        set(missing_relations) & INTENTIONALLY_EXCLUDED_GOLD_RELATIONS
    )
    unresolved_missing = sorted(
        set(missing_relations) - INTENTIONALLY_EXCLUDED_GOLD_RELATIONS
    )

    return {
        "normalized": normalize,
        "gold_relation_types": sorted(gold_relation_types),
        "ontology_relationship_types": sorted(ontology_relationship_types),
        "missing_relations": missing_relations,
        "unresolved_missing": unresolved_missing,
        "intentionally_excluded_missing": intentionally_excluded_missing,
        "cases_covered": len(cases),
        "per_case": per_case,
    }


def gold_relation_coverage(
    ontology: dict,
    xlsx_path: str | Path,
    sheet_name: str = "eval-18",
) -> dict[str, Any]:
    """D-17 coverage check — parses the gold-relation xlsx, then diffs."""
    cases = parse_gold_relations(xlsx_path, sheet_name=sheet_name)
    return gold_relation_coverage_from_cases(ontology, cases)


# ---------------------------------------------------------------------------
# D-14 — benchmark coverage
# ---------------------------------------------------------------------------


def benchmark_coverage(ontology: dict, benchmark_dir: str | Path) -> dict[str, Any]:
    """
    D-14 coverage check — maps each benchmark JSONL file under `benchmark_dir`
    to >=1 covering node type. Two matching strategies, either qualifies as
    "covered":

      1. Direct provenance — a node type's `provenance` list names the
         benchmark_id or the file stem (Method C's benchmark-definitions
         source category tags discovered types this way).
      2. Keyword overlap — benchmark question/expected_response/key_facts
         tokens intersect the node type's label/description/example_terms
         tokens. This is a heuristic AID for curation review, not
         authoritative — the human gate makes the final keep/drop call on
         any weak or missing mapping.
    """
    benchmark_dir = Path(benchmark_dir)
    jsonl_files = sorted(benchmark_dir.glob("*.jsonl"))

    node_entries: list[tuple[str, set[str], list[str]]] = []
    for nt in ontology.get("node_types", []):
        label = _node_type_label(nt)
        if not label:
            continue
        tokens, provenance = _node_type_tokens_and_provenance(nt)
        node_entries.append((label, tokens, provenance))

    benchmark_map: dict[str, Any] = {}
    unmapped: list[str] = []

    for path in jsonl_files:
        benchmark_id: str | None = None
        text_parts: list[str] = []

        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping invalid JSON line in {path.name}")
                    continue
                if rec.get("status") == "deprecated":
                    continue
                benchmark_id = benchmark_id or rec.get("benchmark_id")
                text_parts.append(rec.get("input", {}).get("question", ""))
                text_parts.append(rec.get("ground_truth", {}).get("expected_response", ""))
                for kf in rec.get("key_facts", []) or []:
                    text_parts.append(kf.get("fact", "") if isinstance(kf, dict) else str(kf))

        if benchmark_id is None:
            # Fallback: derive from filename convention "b01_..." -> "B01"
            benchmark_id = path.stem.split("_")[0].upper()

        bench_tokens = _tokenize(" ".join(text_parts) + " " + path.stem.replace("_", " "))

        covering: set[str] = set()
        for label, type_tokens, provenance in node_entries:
            if any(
                benchmark_id.lower() in p.lower() or path.stem in p.lower()
                for p in provenance
            ):
                covering.add(label)
                continue
            if bench_tokens & type_tokens:
                covering.add(label)

        benchmark_map[benchmark_id] = {
            "file": path.name,
            "covering_types": sorted(covering),
        }
        if not covering:
            unmapped.append(benchmark_id)

    return {
        "benchmark_map": benchmark_map,
        "unmapped": sorted(unmapped),
        "total_benchmarks": len(benchmark_map),
    }
