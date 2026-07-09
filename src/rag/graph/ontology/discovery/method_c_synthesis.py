"""
Method C: Grounded-Synthesis Ontology Discovery (D-01/D-02/D-04/D-08/D-09/D-18)

One-shot, CURATION-TIME CLI script (NOT a runtime service) that produces
`ontology_draft.json` -- the first leg of D-01's
`C (grounded synthesis) -> curate -> B (clustering) -> reconcile -> lock`
ontology-construction sequence.

Anchor sources (D-04, exactly three, all STRUCTURED -- not open per-chunk
NER, which was the Phase 9 failure mode this phase exists to fix):

  (a) CCoP section/clause HEADINGS parsed from the Docling-parsed corpus
      markdown (control taxonomy) -- reuses the SAME `## X.Y heading`
      regex shape `rag.ingestion.chunkers.clause_aware_chunker.CLAUSE_PATTERN`
      already proves against this corpus, restricted here to the markdown-
      heading branch only (a header LIST, not the clause-body chunk
      boundaries `chunk_by_clauses` splits on).
  (b) The 18 benchmark JSONL definitions (question / expected_response /
      key_facts / clause_reference) -- reasoning and relation vocabulary.
  (c) A stratified prose sample across all 7 CCoP `source_docs` -- domain
      entities actually named in the regulatory text.

This script reads ONLY the CCoP PDFs (via the same Docling parser the
Phase 9/10 KG builders already use, `rag.graph.build.corpus_source`) and the
18 benchmark JSONL files. It does NOT read any previously-built knowledge-
graph artifact -- discovery runs fresh from the corpus + structured taxonomy
only, per D-02.

Exactly ONE `ontology_discovery_model` (gpt-4o-mini via OpenRouter) synthesis
call is made per source category -- three calls total, not per-chunk. Each
call follows the project's established graceful-degradation pattern (see
`rag.retrieval.nodes.query_analysis._generate_hyde`): missing API key or any
LLM/parse failure logs a warning and degrades to an empty result for that
category rather than raising.

The D-08 regulatory-structure layer (Clause/Control/Obligation/Definition +
GOVERNS/REQUIRES/APPLIES_TO/RESPONSIBLE_FOR/MITIGATES), the D-09
clause-function tags (ScopeClause/ControlClause/DefinitionClause), and the
D-18 negation/modal relation families (14 total) are HAND-SEEDED, not
discovered -- grounded synthesis over scenario-centric prose cannot surface
the regulatory-structure layer on its own (D-08's own rationale).

The Task-1 coverage checkers (`discovery.coverage_check`) run against the
assembled draft and their D-14/D-17 reports are embedded in the output JSON
for the human curation gate (a, plan 10-03 Task 3) to review.

Usage:
    cd src && poetry run python -m rag.graph.ontology.discovery.method_c_synthesis \\
        --ccop-dir ../ccop-official \\
        --benchmark-dir ../ground-truth/test-suite \\
        --gold-relation-xlsx results/evaluations/eval-report-hybrid-suite-20260630-0907.xlsx \\
        --output rag/graph/ontology/ontology_draft.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.config.settings import Settings, get_settings
from rag.graph.build.corpus_source import DEFAULT_CCOP_DIR, load_ccop_corpus_texts
from rag.graph.ontology.discovery.coverage_check import benchmark_coverage, gold_relation_coverage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults (relative to src/, matching this codebase's script convention)
# ---------------------------------------------------------------------------
DEFAULT_BENCHMARK_DIR = "../ground-truth/test-suite"
DEFAULT_GOLD_RELATION_XLSX = "results/evaluations/eval-report-hybrid-suite-20260630-0907.xlsx"
DEFAULT_GOLD_RELATION_SHEET = "eval-18"
DEFAULT_OUTPUT_PATH = "rag/graph/ontology/ontology_draft.json"

# Restricted to the "## X.Y heading" branch of
# clause_aware_chunker.CLAUSE_PATTERN -- section/clause HEADINGS only
# (Docling Classic pipeline markdown, ~56 headings across the corpus per
# decision [03.2-01]), not every bare-digit clause-BODY line CLAUSE_PATTERN
# also matches (that's the clause-fragment chunk-boundary detector
# `chunk_by_clauses` splits on -- a different job: hundreds of matches, not
# a compact header list suitable for one LLM call).
HEADING_RE = re.compile(r"^##\s+(\d+(?:\.\d+)*(?:\([a-z]\))?)\s+(.+?)$", re.MULTILINE)

# ---------------------------------------------------------------------------
# D-08 / D-09 / D-18 seed vocabulary (hand-added, not discovered)
# ---------------------------------------------------------------------------
D08_RELATIONSHIP_TYPES = ["GOVERNS", "REQUIRES", "APPLIES_TO", "RESPONSIBLE_FOR", "MITIGATES"]

D18_RELATIONSHIP_TYPES = [
    "NOT_DESIGNATED_AS", "CANNOT_SATISFY", "DOES_NOT_WAIVE", "DEFINES_NO",
    "DOES_NOT_SPECIFY", "PERMITS_WHERE_NECESSARY", "TECHNOLOGY_NEUTRAL_ON",
    "RECOMMENDS_AGAINST", "DEFERS_TO", "IS_A", "DEFINED_AS", "CLASSIFIED_AS",
    "DESIGNATES", "DETERMINED_BY",
]
assert len(D18_RELATIONSHIP_TYPES) == 14, "D-18 requires exactly 14 relation families, none omitted"

# ---------------------------------------------------------------------------
# LLM synthesis prompt (one call per source category, D-04)
# ---------------------------------------------------------------------------

SYNTHESIS_PROMPT = """You are assisting with GROUNDED ontology discovery for a knowledge graph over \
Singapore's CCoP 2.0 Cybersecurity Code of Practice. You are given ONE category of structured \
source material below. Propose CANDIDATE entity (node) types and relationship types that this \
SPECIFIC source material evidences -- do not invent generic categories unrelated to the text.

Rules:
- Output STRICT JSON only, no prose, matching exactly this shape:
  {{
    "node_types": [
      {{"label": "PascalCaseLabel", "description": "...", "example_terms": ["...", "..."], "flagged_ambiguities": ["..."]}}
    ],
    "relationship_types": [
      {{"label": "UPPER_SNAKE_CASE", "description": "...", "flagged_ambiguities": ["..."]}}
    ]
  }}
- Labels must be canonical, non-overlapping, and reusable. Avoid near-duplicate labels for the \
same concept (e.g. do not emit "CII", "CIIAsset", and "CriticalInformationInfrastructure" as \
three separate types) -- pick ONE canonical label and note rejected synonyms in \
flagged_ambiguities.
- flagged_ambiguities lists any near-duplicate/overlapping concept you considered but did NOT \
pick as the canonical label, or any genuine ambiguity a human curator should review.
- Do NOT extract instances/examples (no specific organization names, no placeholder names) -- \
only TYPES.
- {category_instruction}

SOURCE MATERIAL ({category_label}):
{source_text}
"""

CATEGORY_A_LABEL = "control_taxonomy_headers"
CATEGORY_A_INSTRUCTION = (
    "This source is the CCoP section/clause HEADING structure (the control taxonomy) -- propose "
    "types that capture the STRUCTURE of control/topic groupings these headings organize (e.g. "
    "control-category or process groupings). Do NOT propose Clause/Control/Obligation/Definition "
    "or ScopeClause/ControlClause/DefinitionClause -- those are the regulatory-structure layer "
    "and are already seeded separately."
)

CATEGORY_B_LABEL = "benchmark_definitions"
CATEGORY_B_INSTRUCTION = (
    "This source is a sample from the 18 benchmark definitions (question + expected answer + key "
    "facts), one per benchmark, each prefixed with its [benchmark_id]. Propose types/relations "
    "that capture the REASONING CONCEPTS these benchmarks test (e.g. scope-determination actors, "
    "waiver/exception concepts, risk concepts, incident-response roles). Where a type is clearly "
    "motivated by one or more specific benchmarks, name the benchmark_id(s) in that type's "
    "flagged_ambiguities list (e.g. \"motivated by B22\") so downstream benchmark-coverage mapping "
    "can trace it."
)

CATEGORY_C_LABEL = "corpus_prose_sample"
CATEGORY_C_INSTRUCTION = (
    "This source is a stratified sample of corpus PROSE across all 7 CCoP source documents, one "
    "section per document. Propose DOMAIN ENTITY types actually named in this regulatory text "
    "(e.g. organizational roles, asset/system categories, process concepts). Ignore illustrative "
    "examples, hypothetical scenarios, and placeholder names."
)


def _synthesize_category(
    source_text: str,
    category_instruction: str,
    category_label: str,
    settings: Settings,
) -> dict[str, list[dict[str, Any]]]:
    """One gpt-4o-mini synthesis call for one source category.

    Mirrors `rag.retrieval.nodes.query_analysis._generate_hyde`'s
    graceful-degradation pattern: missing key or any failure logs a warning
    and returns an empty result rather than raising -- the overall draft
    build must not abort because one category's LLM call failed.
    """
    empty: dict[str, list[dict[str, Any]]] = {"node_types": [], "relationship_types": []}

    if not settings.openrouter_api_key:
        logger.warning(
            f"Ontology discovery ({category_label}) skipped -- CCOP_OPENROUTER_API_KEY not set"
        )
        return empty
    if not source_text.strip():
        logger.warning(f"Ontology discovery ({category_label}) skipped -- empty source text")
        return empty

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=120,
        )
        prompt = SYNTHESIS_PROMPT.format(
            category_instruction=category_instruction,
            category_label=category_label,
            source_text=source_text,
        )
        resp = client.chat.completions.create(
            model=settings.ontology_discovery_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )
        raw = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(raw)
        node_types = parsed.get("node_types", [])
        relationship_types = parsed.get("relationship_types", [])
        if not isinstance(node_types, list) or not isinstance(relationship_types, list):
            raise ValueError(f"Malformed synthesis response shape: {parsed!r}")

        logger.info(
            f"Ontology discovery ({category_label}): {len(node_types)} node types, "
            f"{len(relationship_types)} relationship types proposed"
        )
        return {"node_types": node_types, "relationship_types": relationship_types}
    except Exception as e:
        logger.warning(f"Ontology discovery ({category_label}) synthesis failed: {e}")
        return empty


# ---------------------------------------------------------------------------
# Source-category material builders
# ---------------------------------------------------------------------------


def extract_section_headings(corpus_texts: dict[str, str]) -> str:
    """Source (a): dedup'd `[doc] clause_id title` lines for every markdown heading."""
    lines: list[str] = []
    for doc_name, text in corpus_texts.items():
        seen: set[str] = set()
        for match in HEADING_RE.finditer(text):
            clause_id, title = match.group(1), match.group(2).strip()
            if clause_id in seen:
                continue
            seen.add(clause_id)
            lines.append(f"[{doc_name}] {clause_id} {title}")
    return "\n".join(lines)


def load_benchmark_definitions(benchmark_dir: str | Path) -> str:
    """Source (b): one representative case per benchmark file."""
    benchmark_dir = Path(benchmark_dir)
    lines: list[str] = []
    for path in sorted(benchmark_dir.glob("*.jsonl")):
        first_case: dict[str, Any] | None = None
        with open(path, encoding="utf-8") as f:
            for raw_line in f:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    rec = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if rec.get("status") == "deprecated":
                    continue
                first_case = rec
                break

        if first_case is None:
            logger.warning(f"No usable case found in {path.name}; skipping for benchmark source")
            continue

        benchmark_id = first_case.get("benchmark_id", path.stem)
        question = first_case.get("input", {}).get("question", "")
        expected = first_case.get("ground_truth", {}).get("expected_response", "")
        clause_refs = first_case.get("metadata", {}).get("clause_reference", [])
        key_facts = [
            kf.get("fact", "") if isinstance(kf, dict) else str(kf)
            for kf in (first_case.get("key_facts", []) or [])
        ]
        lines.append(
            f"[{benchmark_id}] Q: {question}\n"
            f"  Expected: {expected}\n"
            f"  Clause refs: {clause_refs}\n"
            f"  Key facts: {key_facts}"
        )
    return "\n\n".join(lines)


def stratified_prose_sample(corpus_texts: dict[str, str], words_per_doc: int = 700) -> str:
    """Source (c): a stratified sample of body prose across all 7 source_docs."""
    parts: list[str] = []
    for doc_name, text in corpus_texts.items():
        body_lines = [ln for ln in text.splitlines() if not ln.strip().startswith("#")]
        body_text = " ".join(body_lines)
        words = body_text.split()
        sample = " ".join(words[:words_per_doc])
        parts.append(f"=== {doc_name} ===\n{sample}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Merge + seed
# ---------------------------------------------------------------------------


def _merge_discovered(
    results: list[dict[str, list[dict[str, Any]]]],
    category_labels: list[str],
) -> tuple[list[dict[str, Any]], list[str], dict[str, dict[str, Any]]]:
    """Merge the three per-category synthesis results, deduping by label."""
    node_types_by_label: dict[str, dict[str, Any]] = {}
    relationship_types: set[str] = set()
    relationship_metadata: dict[str, dict[str, Any]] = {}

    for category_label, result in zip(category_labels, results):
        for nt in result.get("node_types", []):
            label = str(nt.get("label", "")).strip()
            if not label:
                continue
            entry = node_types_by_label.setdefault(
                label,
                {
                    "label": label,
                    "description": "",
                    "example_terms": [],
                    "provenance": [],
                    "flagged_ambiguities": [],
                },
            )
            entry["provenance"].append(f"method_c:{category_label}")
            if not entry["description"] and nt.get("description"):
                entry["description"] = nt["description"]
            for term in nt.get("example_terms", []) or []:
                if term not in entry["example_terms"]:
                    entry["example_terms"].append(term)
            for amb in nt.get("flagged_ambiguities", []) or []:
                if amb not in entry["flagged_ambiguities"]:
                    entry["flagged_ambiguities"].append(amb)

        for rt in result.get("relationship_types", []):
            label = str(rt.get("label", "")).strip().upper()
            if not label:
                continue
            relationship_types.add(label)
            meta = relationship_metadata.setdefault(
                label, {"description": "", "provenance": [], "flagged_ambiguities": []}
            )
            meta["provenance"].append(f"method_c:{category_label}")
            if not meta["description"] and rt.get("description"):
                meta["description"] = rt["description"]
            for amb in rt.get("flagged_ambiguities", []) or []:
                if amb not in meta["flagged_ambiguities"]:
                    meta["flagged_ambiguities"].append(amb)

    return list(node_types_by_label.values()), sorted(relationship_types), relationship_metadata


def _seed_regulatory_layer(node_types: list[dict[str, Any]]) -> None:
    """D-08: hand-add the regulatory-structure node types if not already discovered."""
    existing = {nt["label"] for nt in node_types}
    seeds = {
        "Clause": (
            "A CCoP 2.0 (or supplementary-document) regulatory clause or provision -- the atomic "
            "seeded backbone node (D-10)."
        ),
        "Control": "A specific control/safeguard a Clause requires the CIIO to implement.",
        "Obligation": (
            "A compliance obligation imposed on a CIIO, Sector Lead, or Commissioner by a Clause."
        ),
        "Definition": "A defined term whose meaning a Clause fixes for interpretation purposes.",
    }
    for label, description in seeds.items():
        if label in existing:
            continue
        node_types.append({
            "label": label,
            "description": description,
            "example_terms": [],
            "provenance": ["seeded (D-08 regulatory-structure layer)"],
            "flagged_ambiguities": [],
        })


def _seed_function_tags(node_types: list[dict[str, Any]]) -> None:
    """D-09: hand-add the clause-function tags if not already discovered."""
    existing = {nt["label"] for nt in node_types}
    seeds = {
        "ScopeClause": (
            "A Clause whose primary function is determining mandatory-compliance scope/"
            "applicability."
        ),
        "ControlClause": "A Clause whose primary function is mandating a specific control/safeguard.",
        "DefinitionClause": "A Clause whose primary function is defining a term.",
    }
    for label, description in seeds.items():
        if label in existing:
            continue
        node_types.append({
            "label": label,
            "description": description,
            "example_terms": [],
            "provenance": ["seeded (D-09 clause-function tags)"],
            "flagged_ambiguities": [],
        })


def _seed_relationships(
    relationship_types: list[str], relationship_metadata: dict[str, dict[str, Any]]
) -> list[str]:
    """D-08 + D-18: hand-add the regulatory-structure relations and all 14 modal/negation
    relation families discovered from the gold-relation xlsx, regardless of what Method C's
    LLM calls surfaced on their own."""
    merged = set(relationship_types)
    seed_groups = [
        (D08_RELATIONSHIP_TYPES, "seeded (D-08 regulatory-structure layer)"),
        (D18_RELATIONSHIP_TYPES, "seeded (D-18 negation/modal relation families, gold-relation xlsx)"),
    ]
    for labels, provenance_note in seed_groups:
        for label in labels:
            merged.add(label)
            meta = relationship_metadata.setdefault(
                label, {"description": "", "provenance": [], "flagged_ambiguities": []}
            )
            if provenance_note not in meta["provenance"]:
                meta["provenance"].append(provenance_note)
    return sorted(merged)


def _default_patterns() -> list[list[str]]:
    """A small illustrative pattern seed for the regulatory-structure layer. Draft only --
    the full pattern set is a curation-time decision (Wave 1 gates), not fixed here."""
    return [
        ["Clause", "GOVERNS", "Control"],
        ["Clause", "REQUIRES", "Obligation"],
        ["Clause", "APPLIES_TO", "Definition"],
    ]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def build_ontology_draft(
    settings: Settings,
    ccop_dir: str = DEFAULT_CCOP_DIR,
    benchmark_dir: str | Path = DEFAULT_BENCHMARK_DIR,
) -> dict[str, Any]:
    """Run the full Method-C pipeline and return the assembled ontology draft dict
    (without coverage reports attached -- see `attach_coverage_reports`)."""
    logger.info("Loading CCoP corpus (Docling-parsed markdown, same text the KG builders consume)...")
    corpus_texts = load_ccop_corpus_texts(settings, ccop_dir)

    logger.info("Building source-category material for the three Method-C anchors (D-04)...")
    headings_text = extract_section_headings(corpus_texts)
    benchmarks_text = load_benchmark_definitions(benchmark_dir)
    prose_text = stratified_prose_sample(corpus_texts)

    category_labels = [CATEGORY_A_LABEL, CATEGORY_B_LABEL, CATEGORY_C_LABEL]
    results = [
        _synthesize_category(headings_text, CATEGORY_A_INSTRUCTION, CATEGORY_A_LABEL, settings),
        _synthesize_category(benchmarks_text, CATEGORY_B_INSTRUCTION, CATEGORY_B_LABEL, settings),
        _synthesize_category(prose_text, CATEGORY_C_INSTRUCTION, CATEGORY_C_LABEL, settings),
    ]

    node_types, relationship_types, relationship_metadata = _merge_discovered(
        results, category_labels
    )

    _seed_regulatory_layer(node_types)
    _seed_function_tags(node_types)
    relationship_types = _seed_relationships(relationship_types, relationship_metadata)

    return {
        "method": "C (grounded synthesis)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "node_types": node_types,
        "relationship_types": relationship_types,
        "relationship_type_metadata": relationship_metadata,
        "patterns": _default_patterns(),
        # Permissive during Wave-1 curation (RESEARCH.md Pitfall 1: locking
        # `additional_*_types=False` before the D-14/D-17 coverage gates
        # pass silently drops out-of-schema entities at extraction time).
        # Lock to False only after the human curation gate (a) approves.
        "additional_node_types": True,
        "additional_relationship_types": True,
    }


def attach_coverage_reports(
    ontology_draft: dict[str, Any],
    benchmark_dir: str | Path,
    gold_relation_xlsx: str | Path,
    gold_relation_sheet: str,
) -> None:
    """Embed the D-14 benchmark-coverage and D-17 gold-relation-coverage reports
    (Task 1 checkers) into the draft, mutating it in place."""
    logger.info("Running D-14 benchmark-coverage check...")
    ontology_draft["benchmark_coverage_report"] = benchmark_coverage(ontology_draft, benchmark_dir)

    logger.info("Running D-17 gold-relation coverage check...")
    ontology_draft["gold_relation_coverage_report"] = gold_relation_coverage(
        ontology_draft, gold_relation_xlsx, sheet_name=gold_relation_sheet
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Method C: grounded-synthesis ontology discovery (D-01/D-04). "
            "One-shot curation-time script -- NOT a runtime service."
        )
    )
    parser.add_argument("--ccop-dir", default=DEFAULT_CCOP_DIR, help="CCoP PDFs base directory")
    parser.add_argument(
        "--benchmark-dir", default=DEFAULT_BENCHMARK_DIR, help="18-benchmark JSONL directory"
    )
    parser.add_argument(
        "--gold-relation-xlsx",
        default=DEFAULT_GOLD_RELATION_XLSX,
        help="Path to the eval-report gold-relation xlsx (D-17)",
    )
    parser.add_argument("--gold-relation-sheet", default=DEFAULT_GOLD_RELATION_SHEET)
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT_PATH, help="Output path for ontology_draft.json"
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s -- %(message)s",
        datefmt="%H:%M:%S",
    )

    settings = get_settings()

    ontology_draft = build_ontology_draft(
        settings, ccop_dir=args.ccop_dir, benchmark_dir=args.benchmark_dir
    )
    attach_coverage_reports(
        ontology_draft,
        benchmark_dir=args.benchmark_dir,
        gold_relation_xlsx=args.gold_relation_xlsx,
        gold_relation_sheet=args.gold_relation_sheet,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ontology_draft, f, indent=2, ensure_ascii=False)
        f.write("\n")

    bcr = ontology_draft["benchmark_coverage_report"]
    grc = ontology_draft["gold_relation_coverage_report"]
    mapped = bcr["total_benchmarks"] - len(bcr["unmapped"])

    print("\n" + "=" * 60)
    print("METHOD-C ONTOLOGY DRAFT COMPLETE")
    print("=" * 60)
    print(f"Node types:             {len(ontology_draft['node_types'])}")
    print(f"Relationship types:     {len(ontology_draft['relationship_types'])}")
    print(f"D-14 benchmarks mapped: {mapped}/{bcr['total_benchmarks']} (unmapped: {bcr['unmapped']})")
    print(f"D-17 missing gold relations: {grc['missing_relations']}")
    print(f"Output: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
