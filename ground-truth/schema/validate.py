#!/usr/bin/env python3
"""
V2 Ground Truth Schema Validator

Validates JSONL test case files against test-case-v2.schema.json.
Runs JSON Schema validation, business rule checks, and (Phase 3.2) clause-
reference ID-existence + semantic-mismatch gates against the authoritative
clause inventory and the Qdrant corpus.

Usage:
    python validate.py                                 # Validate all files in ../test-suite/
    python validate.py --file ../test-suite/b03_conditional_compliance_reasoning.jsonl
    python validate.py --strict                        # Fail on warnings too
    python validate.py --semantic-check                # Enable Pass 3 cosine-similarity gate
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

from jsonschema import Draft202012Validator

# Allow standalone execution from repo root — audit-script helpers live under
# src/ which is NOT on sys.path by default when invoked as `python ground-truth/schema/validate.py`.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from rag.ingestion.scripts.audit_ground_truth_citations import (  # noqa: E402
    SOURCE_CCOP,
    extract_intext_citations,
    load_inventory,
    parse_clause_reference,
)

_DEFAULT_INVENTORY_PATH = (
    _SRC_DIR / "rag" / "ingestion" / "fixtures" / "clause_inventory.json"
)
_DEFAULT_SEMANTIC_THRESHOLD = 0.35
_QDRANT_COLLECTION = "ccop_clauses_hybrid"


def load_schema() -> dict:
    schema_path = Path(__file__).parent / "test-case-v2.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_clause_inventory(fixtures_path: Path) -> set[tuple[str, str]]:
    """Load `clause_inventory.json` as a set of `(clause_id, source_doc)` tuples."""
    return load_inventory(fixtures_path)


def validate_business_rules(
    test_case: dict, warnings: list[str], errors: list[str]
) -> None:
    """Business rules beyond what JSON Schema can enforce."""
    test_id = test_case.get("test_id", "UNKNOWN")
    benchmark_id = test_case.get("benchmark_id", "")

    if not test_id.startswith(f"{benchmark_id}-"):
        errors.append(
            f"{test_id}: test_id prefix does not match benchmark_id '{benchmark_id}'"
        )

    rule_based_benchmarks = {"B1", "B2", "B4", "B21"}
    ground_truth = test_case.get("ground_truth", {})
    if benchmark_id not in rule_based_benchmarks:
        if not ground_truth.get("reasoning_chain"):
            warnings.append(f"{test_id}: LLM-judge benchmark missing reasoning_chain")
        if not ground_truth.get("acceptable_variations"):
            warnings.append(
                f"{test_id}: LLM-judge benchmark missing acceptable_variations"
            )

    if benchmark_id in rule_based_benchmarks:
        if not ground_truth.get("expected_label"):
            errors.append(f"{test_id}: rule-based benchmark missing expected_label")

    key_facts = ground_truth.get("key_facts", [])
    critical_count = sum(1 for kf in key_facts if kf.get("tier") == "critical")
    if benchmark_id not in rule_based_benchmarks and critical_count < 2:
        warnings.append(
            f"{test_id}: reasoning benchmark has {critical_count} critical key_facts (recommend >= 2)"
        )

    fail_conditions = test_case.get("fail_conditions", {})
    if not fail_conditions.get("forbidden_claims"):
        warnings.append(f"{test_id}: no forbidden_claims defined")


def validate_clause_references(
    test_case: dict,
    inventory: set[tuple[str, str]],
    errors: list[str],
) -> None:
    """Hard-fail check: every clause reference must exist in the inventory.

    Pass 1: `metadata.clause_reference[]` — each entry parsed and checked.
    Pass 2: `ground_truth.expected_response` — in-text dotted clauses
    (e.g. "5.3.1(c)") and legal "section N" forms extracted by the shared
    regex helpers and checked against the inventory.

    B21 hallucination-benchmark rows opt out via `metadata.audit_exempt=true`.
    """
    test_id = test_case.get("test_id", "UNKNOWN")
    metadata = test_case.get("metadata", {})

    if metadata.get("audit_exempt"):
        return

    for raw in metadata.get("clause_reference", []):
        parsed = parse_clause_reference(str(raw))
        if parsed.skipped:
            continue
        if not any(cand in inventory for cand in parsed.candidates):
            errors.append(
                f"{test_id}: clause_reference '{raw}' not found in inventory"
            )

    expected_response = test_case.get("ground_truth", {}).get("expected_response", "")
    for clause_id, source_doc in extract_intext_citations(expected_response):
        if (clause_id, source_doc) not in inventory:
            errors.append(
                f"{test_id}: in-text citation '{clause_id}' (source={source_doc}) "
                f"in expected_response not found in inventory"
            )


def validate_semantic_mismatch(
    test_cases: list[dict],
    inventory: set[tuple[str, str]],
    threshold: float,
    errors: list[str],
) -> None:
    """Pass 3: cosine-similarity gate between expected_response and clause body.

    Requires Qdrant reachable. Per CONTEXT.md locked decisions, an unreachable
    Qdrant is a validation failure — not a silent skip. Use the CLI
    `--no-semantic` flag to opt out explicitly.
    """
    try:
        from qdrant_client import QdrantClient  # noqa: E402
        from qdrant_client.http import models as qdrant_models  # noqa: E402

        from infrastructure.config.settings import get_settings  # noqa: E402
        from rag.infrastructure.adapters.qdrant.embedding_service import (  # noqa: E402
            EmbeddingService,
        )
    except ImportError as exc:
        errors.append(
            f"semantic-check: required imports unavailable ({exc}). "
            "Install Qdrant client + infrastructure dependencies, or use --no-semantic."
        )
        return

    try:
        settings = get_settings()
        qdrant_url = getattr(settings, "qdrant_url", "http://localhost:6333")
        client = QdrantClient(url=qdrant_url, timeout=10)
        client.get_collection(_QDRANT_COLLECTION)
    except Exception as exc:
        errors.append(
            f"semantic-check: Qdrant unreachable at {qdrant_url} ({exc}) — "
            f"semantic validation cannot run; start Qdrant and retry, "
            f"or pass --no-semantic to bypass explicitly."
        )
        return

    embedder = EmbeddingService()
    for test_case in test_cases:
        test_id = test_case.get("test_id", "UNKNOWN")
        metadata = test_case.get("metadata", {})
        if metadata.get("audit_exempt"):
            continue

        expected_response = test_case.get("ground_truth", {}).get(
            "expected_response", ""
        )
        if not expected_response:
            continue

        response_vec = embedder.embed_dense([expected_response])[0]

        for raw in metadata.get("clause_reference", []):
            parsed = parse_clause_reference(str(raw))
            if parsed.skipped:
                continue
            if parsed.source_doc != SOURCE_CCOP:
                continue

            citation_id = f"{SOURCE_CCOP}::{parsed.clause_id}"
            hits = client.scroll(
                collection_name=_QDRANT_COLLECTION,
                scroll_filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="citation_id",
                            match=qdrant_models.MatchValue(value=citation_id),
                        )
                    ]
                ),
                limit=1,
                with_vectors=True,
            )
            points = hits[0] if hits else []
            if not points:
                continue

            chunk_vec = points[0].vector
            if isinstance(chunk_vec, dict):
                chunk_vec = chunk_vec.get("dense") or next(iter(chunk_vec.values()))
            if chunk_vec is None:
                continue

            similarity = _cosine(response_vec, chunk_vec)
            if similarity < threshold:
                errors.append(
                    f"{test_id}: semantic mismatch for clause '{parsed.clause_id}' — "
                    f"cosine={similarity:.3f} < threshold={threshold}"
                )


def _cosine(vec_a: Iterable[float], vec_b: Iterable[float]) -> float:
    a = list(vec_a)
    b = list(vec_b)
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def validate_file(
    filepath: Path,
    schema: dict,
    inventory: set[tuple[str, str]] | None = None,
    collect_cases: list[dict] | None = None,
    strict: bool = False,
) -> tuple[int, int, int]:
    """Validate a single JSONL file. Returns (valid_count, warning_count, error_count).

    Deprecated test cases (`status == "deprecated"`) are skipped — they stay
    on disk for history but do not run through JSON Schema, business-rule,
    or clause-reference gates.

    When `inventory` is provided, Pass 1 (clause_reference) and Pass 2
    (in-text citations) hard-fail on missing IDs. When `collect_cases` is
    provided, non-deprecated parsed objects are appended for downstream
    Pass 3 semantic checks.
    """
    validator = Draft202012Validator(schema)
    valid_count = 0
    warning_count = 0
    error_count = 0
    seen_ids: set[str] = set()

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                test_case = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  ERROR line {line_num}: Invalid JSON — {e}")
                error_count += 1
                continue

            if test_case.get("status") == "deprecated":
                test_id = test_case.get("test_id", f"line-{line_num}")
                print(f"  SKIP  {test_id}: deprecated")
                continue

            test_id = test_case.get("test_id", f"line-{line_num}")

            if test_id in seen_ids:
                print(f"  ERROR {test_id}: Duplicate test_id")
                error_count += 1
            seen_ids.add(test_id)

            schema_errors = list(validator.iter_errors(test_case))
            if schema_errors:
                for err in schema_errors:
                    path = ".".join(str(p) for p in err.absolute_path) or "(root)"
                    print(f"  ERROR {test_id} [{path}]: {err.message}")
                error_count += len(schema_errors)
                continue

            warnings: list[str] = []
            biz_errors: list[str] = []
            validate_business_rules(test_case, warnings, biz_errors)
            if inventory is not None:
                validate_clause_references(test_case, inventory, biz_errors)

            for w in warnings:
                print(f"  WARN  {w}")
                warning_count += 1

            for e in biz_errors:
                print(f"  ERROR {e}")
                error_count += 1

            if collect_cases is not None:
                collect_cases.append(test_case)

            if not schema_errors and not biz_errors:
                valid_count += 1

    return valid_count, warning_count, error_count


def run_validation(
    test_suite_dir: Path | None = None,
    file: Path | None = None,
    inventory_path: Path | None = None,
    use_inventory: bool = True,
    semantic_check: bool = False,
    semantic_threshold: float = _DEFAULT_SEMANTIC_THRESHOLD,
    strict: bool = False,
) -> int:
    """Programmatic entry point. Returns process exit code (0 = pass).

    `file` overrides `test_suite_dir`. If both are None, defaults to
    `ground-truth/test-suite` next to this script.
    """
    schema = load_schema()
    resolved_dir = test_suite_dir or (Path(__file__).parent.parent / "test-suite")

    if file is not None:
        files = [file]
    else:
        files = sorted(resolved_dir.glob("b*.jsonl"))
        if not files:
            print(f"No JSONL files found in {resolved_dir}")
            return 1

    inventory: set[tuple[str, str]] | None = None
    if use_inventory:
        resolved_inventory = inventory_path or _DEFAULT_INVENTORY_PATH
        if not resolved_inventory.exists():
            print(
                f"ERROR: clause inventory not found at {resolved_inventory}. "
                f"Run `poetry run python -m rag.ingestion.scripts.build_clause_inventory ...` first.",
                file=sys.stderr,
            )
            return 2
        inventory = load_clause_inventory(resolved_inventory)

    total_valid = 0
    total_warnings = 0
    total_errors = 0
    collected_cases: list[dict] = []

    for filepath in files:
        print(f"\n--- {filepath.name} ---")
        valid, warnings, errors = validate_file(
            filepath,
            schema,
            inventory=inventory,
            collect_cases=collected_cases if semantic_check else None,
            strict=strict,
        )
        total_valid += valid
        total_warnings += warnings
        total_errors += errors
        print(f"  Result: {valid} valid, {warnings} warnings, {errors} errors")

    if semantic_check and inventory is not None:
        print("\n--- Pass 3: semantic mismatch gate ---")
        semantic_errors: list[str] = []
        validate_semantic_mismatch(
            collected_cases, inventory, semantic_threshold, semantic_errors
        )
        for e in semantic_errors:
            print(f"  ERROR {e}")
        total_errors += len(semantic_errors)
        print(
            f"  Pass 3 complete: {len(semantic_errors)} error(s) at threshold={semantic_threshold}"
        )

    print(
        f"\n=== TOTAL: {total_valid} valid, {total_warnings} warnings, {total_errors} errors ==="
    )

    if total_errors > 0 or (strict and total_warnings > 0):
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate v2 ground truth test cases")
    parser.add_argument("--file", type=Path, help="Validate a single JSONL file")
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )
    parser.add_argument(
        "--semantic-check",
        action="store_true",
        help="Enable Pass 3 semantic mismatch gate (requires Qdrant).",
    )
    parser.add_argument(
        "--semantic-threshold",
        type=float,
        default=_DEFAULT_SEMANTIC_THRESHOLD,
        help="Cosine similarity threshold for Pass 3 (default: 0.35)",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=_DEFAULT_INVENTORY_PATH,
        help="Path to clause_inventory.json",
    )
    parser.add_argument(
        "--no-inventory",
        action="store_true",
        help="Disable clause-reference ID-existence gate (debugging only)",
    )
    args = parser.parse_args()

    exit_code = run_validation(
        file=args.file,
        inventory_path=args.inventory,
        use_inventory=not args.no_inventory,
        semantic_check=args.semantic_check,
        semantic_threshold=args.semantic_threshold,
        strict=args.strict,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
