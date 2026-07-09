"""
Ontology LOCK builder (D-01 final leg / D-14 / D-17)

The LAST leg of D-01's
`C (grounded synthesis) -> curate (gate a) -> B (clustering) -> reconcile
(gate b) -> LOCK` sequence.

This one-shot, CURATION-TIME CLI script takes the human-approved Method-C
draft (`ontology_draft.json`) plus the Method-B clustering cross-check
(`method_b_reconcile.json`), applies the RECONCILIATION DECISIONS made by the
human at curation gate (b), RE-RUNS both coverage checks (D-14 benchmark
coverage AND D-17 gold-relation coverage) against the reconciled type set,
and -- only if both pass (RESEARCH.md Pitfall 1: never lock before coverage
passes, or out-of-schema entities are silently dropped) -- writes the LOCKED
`ontology_config.json` with `additional_node_types=False` +
`additional_relationship_types=False`.

Gate (b) reconciliation decisions applied here (human-authored, plan 10-04):

  NODE TYPES (20 -> 24): ADD the 4 shortlisted Method-B-only candidate types
    - OperationalTechnology (B04 IT/OT boundary; ICS/SCADA/PLC/DCS terms)
    - ThirdParty (alias Vendor; B18 outsourcing/non-delegable responsibility)
    - EssentialService (B01 applicability scope; Cyber Act "essential service")
    - BusinessEntity (B18 legal-entity forms attributing CIIO liability)
    KEEP MultiFactorAuthentication as its own node type; KEEP all 10
    not-corroborated C types (7 seeded structural = expected non-corroboration).

  RELATIONSHIP TYPES (47 -> 48): SPLIT VIOLATES out as its OWN relation
    (active breach, DISTINCT from CANNOT_SATISFY structural inability) -- and
    it is therefore REMOVED from the gold-verb synonym-collapse map (see
    `coverage_check.GOLD_RELATION_SYNONYM_MAP`). CONFIRM the two remaining
    collapses (MAY_REQUEST -> APPLIES_FOR_WAIVER, ADDRESSES -> MITIGATES).

The locked config is the authoritative build-time schema every mechanical
build wave (10-05 clause seeder, 10-06 splitter+gleaning, 10-07 extraction)
consumes via the `schema=` kwarg + function-type tags.

Usage:
    cd src && poetry run python -m rag.graph.ontology.discovery.lock_ontology \\
        --draft rag/graph/ontology/ontology_draft.json \\
        --method-b rag/graph/ontology/method_b_reconcile.json \\
        --gold-relation-xlsx results/evaluations/eval-report-hybrid-suite-20260630-0907.xlsx \\
        --output rag/graph/ontology/ontology_config.json
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rag.graph.ontology.discovery.coverage_check import benchmark_coverage, gold_relation_coverage

logger = logging.getLogger(__name__)

DEFAULT_DRAFT_PATH = "rag/graph/ontology/ontology_draft.json"
DEFAULT_METHOD_B_PATH = "rag/graph/ontology/method_b_reconcile.json"
DEFAULT_GOLD_RELATION_XLSX = "results/evaluations/eval-report-hybrid-suite-20260630-0907.xlsx"
DEFAULT_GOLD_RELATION_SHEET = "eval-18"
DEFAULT_OUTPUT_PATH = "rag/graph/ontology/ontology_config.json"
DEFAULT_BENCHMARK_DIR = "../ground-truth/test-suite"

_PROVENANCE = "method_b:clustering_cross_check + gate_b"

# --- Gate (b) node-type additions (human decision, 20 -> 24) --------------
NODE_TYPE_ADDITIONS: list[dict[str, Any]] = [
    {
        "label": "OperationalTechnology",
        "description": (
            "Operational-technology (OT) systems -- industrial control systems and their "
            "components -- whose IT/OT boundary determines CCoP scope and control applicability. "
            "Distinct from information-technology systems (B04 IT/OT classification boundary)."
        ),
        "example_terms": [
            "operational technology",
            "OT system",
            "industrial control system",
            "ICS",
            "SCADA",
            "programmable logic controller",
            "PLC",
            "distributed control system",
            "DCS",
        ],
        "provenance": [_PROVENANCE],
        "flagged_ambiguities": ["motivated by B04 (IT/OT classification boundary)"],
    },
    {
        "label": "ThirdParty",
        "description": (
            "An external party (vendor, outsourced service provider, external consultant) to whom "
            "a CIIO delegates work but NOT its non-delegable regulatory responsibility -- the crux "
            "of outsourcing/vendor accountability (B18 responsibility attribution)."
        ),
        "example_terms": [
            "third party",
            "vendor",
            "outsourcing and vendor management",
            "external consultant",
            "service provider",
        ],
        "provenance": [_PROVENANCE],
        "flagged_ambiguities": ["Vendor (alias)", "motivated by B18 (responsibility attribution)"],
    },
    {
        "label": "EssentialService",
        "description": (
            "A Cybersecurity Act 'essential service' whose delivery a Critical Information "
            "Infrastructure supports -- the anchor concept for CII designation and mandatory-"
            "compliance scope (B01 applicability scope)."
        ),
        "example_terms": ["essential service", "essential services", "service provision"],
        "provenance": [_PROVENANCE],
        "flagged_ambiguities": ["motivated by B01 (applicability scope)"],
    },
    {
        "label": "BusinessEntity",
        "description": (
            "The legal-entity form (company, partnership, limited liability partnership, "
            "unincorporated association) used to attribute CIIO liability/responsibility to a "
            "legal person (B18 responsibility attribution)."
        ),
        "example_terms": [
            "business entity",
            "partnership",
            "limited liability partnership",
            "unincorporated association",
        ],
        "provenance": [_PROVENANCE],
        "flagged_ambiguities": ["motivated by B18 (responsibility attribution)"],
    },
]

# --- Gate (b) relationship SPLIT (human decision, 47 -> 48) ----------------
VIOLATES_METADATA = {
    "description": (
        "An ACTIVE breach: a Control or Entity VIOLATES a Requirement/Clause. Split out at "
        "curation gate (b) as DISTINCT from CANNOT_SATISFY (structural inability to meet a "
        "requirement) -- the breach-vs-inability distinction is compliance-critical (B07 gap "
        "identification, B03 conditional reasoning, B21 over-specification)."
    ),
    "domain": "Control",
    "range": "Clause",
    "provenance": [
        "reconciled at curation gate (b) -- SPLIT from CANNOT_SATISFY per human decision (10-04)"
    ],
    "flagged_ambiguities": [],
}

# --- Gate (b) pattern additions (tie the new types into the schema) --------
PATTERN_ADDITIONS: list[list[str]] = [
    ["OperationalTechnology", "IN_SCOPE_ONLY_IF", "Clause"],
    ["OperationalTechnology", "APPLIES_TO", "Clause"],
    ["CriticalInformationInfrastructure", "PROVIDES", "EssentialService"],
    ["ThirdParty", "RESPONSIBLE_FOR", "Obligation"],
    ["BusinessEntity", "RESPONSIBLE_FOR", "Obligation"],
    ["Control", "VIOLATES", "Clause"],
]

FUNCTION_TYPE_TAGS = ["ScopeClause", "ControlClause", "DefinitionClause"]  # D-09


def build_locked_ontology(draft: dict[str, Any], method_b: dict[str, Any]) -> dict[str, Any]:
    """Apply the gate-(b) reconciliation decisions to the Method-C draft."""
    node_types = copy.deepcopy(draft["node_types"])
    existing_labels = {nt["label"] for nt in node_types}
    for addition in NODE_TYPE_ADDITIONS:
        if addition["label"] in existing_labels:
            raise ValueError(f"Gate-b addition {addition['label']!r} already present in draft")
        node_types.append(copy.deepcopy(addition))

    relationship_types = set(draft["relationship_types"])
    if "VIOLATES" in relationship_types:
        raise ValueError("VIOLATES already present -- draft state unexpected")
    relationship_types.add("VIOLATES")
    relationship_types = sorted(relationship_types)

    relationship_metadata = copy.deepcopy(draft.get("relationship_type_metadata", {}))
    relationship_metadata["VIOLATES"] = copy.deepcopy(VIOLATES_METADATA)

    patterns = [list(p) for p in draft.get("patterns", [])] + [list(p) for p in PATTERN_ADDITIONS]

    b_only_added = [nt["label"] for nt in NODE_TYPE_ADDITIONS]
    return {
        "method": "reconciled (C grounded-synthesis + B clustering cross-check), LOCKED at gate (b)",
        "generated_at": datetime.now(UTC).isoformat(),
        "locked": True,
        "sources": {
            "method_c_draft": "ontology_draft.json",
            "method_b_reconcile": "method_b_reconcile.json",
        },
        "node_types": node_types,
        "relationship_types": relationship_types,
        "relationship_type_metadata": relationship_metadata,
        "function_type_tags": FUNCTION_TYPE_TAGS,
        "patterns": patterns,
        # LOCKED vocabulary (D-06/D-07 anti-pattern fix): out-of-schema
        # entities/relations are rejected at extraction time, not silently kept.
        "additional_node_types": False,
        "additional_relationship_types": False,
        "curation": {
            "gate": "b",
            "status": "approved-reconciled-locked",
            "decisions_applied": [
                f"ADD 4 Method-B-only node types ({', '.join(b_only_added)}) -> 24 node types",
                "KEEP MultiFactorAuthentication as its own node type (no fold into AccessControl)",
                "KEEP all 10 not-corroborated C types (7 seeded structural = expected non-corroboration)",
                "SPLIT VIOLATES into its own relation (active breach, distinct from CANNOT_SATISFY) -> 48 relations",
                "CONFIRM collapse MAY_REQUEST -> APPLIES_FOR_WAIVER",
                "CONFIRM collapse ADDRESSES -> MITIGATES",
                "LOCK: additional_node_types=False, additional_relationship_types=False",
            ],
            "method_b_summary": {
                "terms_extracted": len(method_b.get("terms", [])),
                "clusters": len(method_b.get("b_types", [])),
                "b_only_candidates": len(method_b.get("b_only", [])),
                "c_types_corroborated_by_b": len(method_b.get("overlap", [])),
                "b_only_added_at_gate_b": b_only_added,
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "LOCK the reconciled ontology (D-01 final leg). Applies curation-gate-(b) decisions, "
            "re-runs D-14 + D-17 coverage, and locks ontology_config.json ONLY if both pass."
        )
    )
    parser.add_argument("--draft", default=DEFAULT_DRAFT_PATH)
    parser.add_argument("--method-b", default=DEFAULT_METHOD_B_PATH)
    parser.add_argument("--benchmark-dir", default=DEFAULT_BENCHMARK_DIR)
    parser.add_argument("--gold-relation-xlsx", default=DEFAULT_GOLD_RELATION_XLSX)
    parser.add_argument("--gold-relation-sheet", default=DEFAULT_GOLD_RELATION_SHEET)
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s -- %(message)s",
        datefmt="%H:%M:%S",
    )

    draft = json.loads(Path(args.draft).read_text(encoding="utf-8"))
    method_b = json.loads(Path(args.method_b).read_text(encoding="utf-8"))

    config = build_locked_ontology(draft, method_b)

    # --- Re-run BOTH coverage checks against the RECONCILED set (Pitfall 1) ---
    logger.info("Re-running D-14 benchmark-coverage against the reconciled type set...")
    bcr = benchmark_coverage(config, args.benchmark_dir)
    logger.info("Re-running D-17 gold-relation coverage against the reconciled type set...")
    grc = gold_relation_coverage(config, args.gold_relation_xlsx, sheet_name=args.gold_relation_sheet)

    config["benchmark_coverage_report"] = bcr
    config["gold_relation_coverage_report"] = grc

    unmapped = bcr["unmapped"]
    unresolved = grc["unresolved_missing"]
    coverage_ok = not unmapped and not unresolved

    print("\n" + "=" * 60)
    print("ONTOLOGY LOCK -- COVERAGE RE-CHECK")
    print("=" * 60)
    print(f"Node types:            {len(config['node_types'])}")
    print(f"Relationship types:    {len(config['relationship_types'])}")
    print(f"D-14 benchmarks mapped: {bcr['total_benchmarks'] - len(unmapped)}/{bcr['total_benchmarks']} (unmapped: {unmapped})")
    print(f"D-17 unresolved_missing: {unresolved}")
    print(f"D-17 intentionally_excluded_missing: {grc['intentionally_excluded_missing']}")
    print(f"VIOLATES in ontology relations: {'VIOLATES' in config['relationship_types']}")
    print("=" * 60)

    if not coverage_ok:
        raise SystemExit(
            "REFUSING TO LOCK -- coverage did not pass (Pitfall 1). "
            f"unmapped={unmapped}, unresolved_missing={unresolved}"
        )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"LOCKED -> {output_path}")


if __name__ == "__main__":
    main()
