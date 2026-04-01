---
phase: 03-ground-truth-v2-overhaul
plan: "04"
subsystem: infrastructure
tags: [jsonl, parser, test-case, v2-schema, backward-compatibility, pytest]

# Dependency graph
requires:
  - phase: 03-01
    provides: "V2 schema and directory structure (ground-truth/test-suite/, ground-truth/schema/test-case-v2.schema.json)"
provides:
  - "JSONL repository parser that auto-detects and parses v2 nested format"
  - "Backward-compatible v1 flat format parsing unchanged"
  - "key_facts extracted as list[str] from v2 ground_truth.key_facts[].fact for scorer compatibility"
  - "Enriched metadata with scenario_sector, scenario_role, reasoning_chain, acceptable_variations"
  - "Benchmark file discovery handles both v1 (benchmark_type) and v2 (benchmark_id) fields"
affects:
  - 03-05
  - 03-06
  - 03-07
  - phase-04-re-baseline

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dispatcher pattern for format versioning: _parse_test_case checks version field, routes to _parse_v1_test_case or _parse_v2_test_case"
    - "Enriched metadata merging: v2 input/ground_truth fields merged into metadata dict for downstream access"
    - "String extraction from structured objects: key_facts list[dict] -> list[str] via [kf['fact'] for kf in raw if isinstance(kf, dict)]"

key-files:
  created:
    - src/tests/infrastructure/test_jsonl_v2_parsing.py
  modified:
    - src/infrastructure/adapters/repositories/jsonl_test_case_repository.py
    - src/domain/entities/test_case.py

key-decisions:
  - "evaluation_criteria validation relaxed to allow empty dict: v2 test cases use universal judge with no per-test criteria, Rule 5 now checks isinstance(dict) not non-empty dict"
  - "_discover_benchmark_files checks benchmark_type or benchmark_id: v2 JSONL files use benchmark_id field instead of benchmark_type"
  - "V2 metadata enrichment: scenario_sector/scenario_role/test_category/reasoning_chain/acceptable_variations all merged into TestCase.metadata for transparent downstream access"

patterns-established:
  - "Version-based dispatch: check data.get('version') == '2.0' before routing to v2-specific parser"
  - "Structured-to-primitive extraction: always flatten list[dict] to list[str] at repository layer before passing to domain"
  - "Clause reference normalization: v2 clause_reference is list[str], join with ', ' to produce v1-compatible string"

# Metrics
duration: 16min
completed: 2026-04-01
---

# Phase 3 Plan 4: V2 JSONL Parser Summary

**JSONL repository updated with version-aware dispatcher extracting v2 nested format (input, ground_truth, fail_conditions, metadata) while preserving v1 flat format parsing unchanged**

## Performance

- **Duration:** 16 min
- **Started:** 2026-04-01T02:45:36Z
- **Completed:** 2026-04-01T03:01:15Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Repository parser dispatches v1/v2 based on `version == "2.0"` field — zero change to v1 parsing path
- V2 nested format fully parsed: question from `input.question`, key_facts as `list[str]` from `ground_truth.key_facts[].fact`, forbidden_claims from `fail_conditions.forbidden_claims`
- Enriched metadata merges v2-specific fields (scenario_sector, scenario_role, reasoning_chain, acceptable_variations) for downstream scorer access
- Benchmark discovery handles both `benchmark_type` (v1) and `benchmark_id` (v2) fields

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests for v2 parsing** - `0aee584` (test)
2. **Task 2: Update repository parser for v2 format** - `385db4c` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified

- `src/tests/infrastructure/test_jsonl_v2_parsing.py` - 4 tests covering v2 test_id/question/expected_response, key_facts as strings, forbidden_claims, enriched metadata
- `src/infrastructure/adapters/repositories/jsonl_test_case_repository.py` - Replaced single `_parse_test_case` with dispatcher + `_parse_v1_test_case` + `_parse_v2_test_case`; updated `_discover_benchmark_files` to check `benchmark_type or benchmark_id`
- `src/domain/entities/test_case.py` - Relaxed Rule 5 evaluation_criteria validation to allow empty dict (v2 universal judge requires no per-test criteria)

## Decisions Made

- **evaluation_criteria allows empty dict for v2:** V2 test cases use the universal judge introduced in Phase 2.4 — there are no per-test evaluation criteria. The Rule 5 validation was changed from "non-empty dict required" to "must be dict" to accommodate this. V1 test cases still have non-empty criteria (no change to v1 behavior).
- **_discover_benchmark_files checks both fields:** V2 JSONL files use `benchmark_id` not `benchmark_type` in their first line. The discovery method now reads `data.get("benchmark_type") or data.get("benchmark_id")` to handle both formats without breaking v1 discovery.
- **key_facts flattened at repository layer:** Scorers downstream (B2 word-overlap, B5 key_facts completeness) expect `list[str]`. V2 has `list[dict]` with `fact`, `source`, `tier` fields. Extraction happens in `_parse_v2_test_case` — domain entity never sees the structured format.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] TestCase.evaluation_criteria validation blocked v2 parsing**

- **Found during:** Task 2 (update repository parser for v2 format)
- **Issue:** The reference plan passes `evaluation_criteria={}` for v2 test cases. TestCase Rule 5 validation required a non-empty dict (`if not self._evaluation_criteria`), which would raise `ValidationError` for every v2 test case. The plan did not account for this validation rule.
- **Fix:** Updated Rule 5 in `test_case.py` to only check `isinstance(self._evaluation_criteria, dict)`, not non-empty. Added comment explaining v2 universal judge rationale.
- **Files modified:** `src/domain/entities/test_case.py`
- **Verification:** 99/99 tests pass including 4 new v2 tests — no existing test regressions
- **Committed in:** `385db4c` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Required for v2 parsing to work at all. V1 test cases still have non-empty evaluation_criteria — no behavioral change to existing test cases.

## Issues Encountered

None.

## Next Phase Readiness

- V2 JSONL files can now be loaded by the evaluation infrastructure — prerequisite for Phase 3 test case generation (Plans 05-09) and Phase 4 re-baseline
- V1 archived test cases continue to load correctly for regression comparisons
- `TestCase.metadata` now carries v2-specific fields (`scenario_sector`, `reasoning_chain`, `acceptable_variations`) transparently — no downstream scorer changes required until they are explicitly used

---
*Phase: 03-ground-truth-v2-overhaul*
*Completed: 2026-04-01*
