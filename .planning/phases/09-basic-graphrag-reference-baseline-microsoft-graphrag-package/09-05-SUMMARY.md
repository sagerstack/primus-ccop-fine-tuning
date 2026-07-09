---
phase: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package
plan: 05
subsystem: rag
tags: [langgraph, typer, graphrag, neo4j, benchmark-id, ground-truth]

# Dependency graph
requires:
  - phase: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package
    provides: "Plan 04's graph_retrieval node, route_by_mode(graphrag), Neo4jGraphRetrievalAdapter"
provides:
  - "`evaluate run --mode graphrag` (scored: graph retrieval -> unchanged primus generation)"
  - "`query ask --mode graphrag` (scored) and `--mode graphrag-retrieval` (inspection-only, no generation)"
  - "route_by_mode/decide_after_grading handling for graphrag-retrieval mirroring rag-only"
  - "LangGraphRagAdapter.is_available() graph-provider awareness for both graphrag modes"
  - "domain.value_objects.benchmark_id.normalize()/ids_match() — B4/B04 casing canonicalization"
  - "Padding-agnostic lookups in JSONLTestCaseRepository (load_by_id/load_by_ids/load_by_benchmark)"
affects: [10-ontology-grounded-kg]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "graphrag-retrieval as the rag-only analog: routes graph_retrieval -> rag_response, no LLM call, token counts stay 0 (nodes are mode-agnostic — no branch needed in graph_retrieval_node.py or rag_response.py)"
    - "normalize() applied at repository lookup boundaries, not inside BenchmarkType — keeps the padding-agnostic fix isolated to id comparison, doesn't touch benchmark numbering"

key-files:
  created:
    - src/domain/value_objects/benchmark_id.py
    - tests/rag/graph/retrieval/test_graphrag_retrieval_only.py
    - tests/domain/test_benchmark_id_casing.py
  modified:
    - src/presentation/cli/commands/evaluate.py
    - src/rag/presentation/cli/query.py
    - src/rag/retrieval/edges/routing.py
    - src/rag/infrastructure/adapters/langgraph_rag_adapter.py
    - src/infrastructure/adapters/repositories/jsonl_test_case_repository.py

key-decisions:
  - "evaluate run VALID_EVAL_MODES gets ONLY 'graphrag' (no retrieval-only value) — unscoreable retrieval-only results have no place in a scored eval run (D-10)"
  - "query ask gets both 'graphrag' and 'graphrag-retrieval' — mirrors the existing hybrid/rag-only split for per-question KG iteration"
  - "graph_retrieval_node.py and rag_response.py needed NO code changes — both were already mode-agnostic (no `if mode ==` branching), so extending routing.py alone was sufficient to wire graphrag-retrieval end-to-end"
  - "normalize() lives in a new benchmark_id.py VO rather than modifying BenchmarkType — BenchmarkType.short_name already strips padding internally (via int() parsing) for its own equality checks; the actual blocker was id-based (test_id/benchmark string) comparisons in the repository that bypass BenchmarkType entirely"

patterns-established:
  - "Padding-agnostic id comparison: normalize('B4') == normalize('B04') == 'B04'; applied at every JSONLTestCaseRepository lookup method so CLI/GT id casing mismatches never silently drop or duplicate a result row"

requirements-completed: [D-10]

# Metrics
duration: ~35min
completed: 2026-07-02
---

# Phase 9 Plan 05: GraphRAG CLI Mode Surface + B04/B4 Casing Fix Summary

**`evaluate run --mode graphrag` (scored) and `query ask --mode graphrag`/`graphrag-retrieval` (scored/inspection) are wired through routing and the LangGraph adapter; ground-truth B4/B04 id casing is now canonicalized in the test-case repository via a new `benchmark_id.normalize()` value object.**

## Performance

- **Duration:** ~35 min
- **Tasks:** 2 (both `type="auto" tdd="true"`)
- **Files modified:** 5
- **Files created:** 3

## Accomplishments
- `evaluate run` exposes `--mode graphrag` only (no retrieval-only value — deliberately unscoreable and excluded per D-10)
- `query ask` exposes `--mode graphrag` (graph -> primus, scored) and `--mode graphrag-retrieval` (graph only, no generation, token counts 0) — the rag-only analog for per-question KG iteration
- `route_by_mode` routes both `graphrag` and `graphrag-retrieval` to `graph_retrieval`; `decide_after_grading` routes `graphrag-retrieval` to `rag_response` (mirrors `rag-only`) and `graphrag` to `generate`/`fallback` based on retrieval success
- `LangGraphRagAdapter.is_available()` now reports availability for graphrag modes based on `CCOP_NEO4J_URI` configuration (previously only checked Qdrant/Databricks, which would have incorrectly reported graphrag as unavailable even with Neo4j configured)
- New `domain.value_objects.benchmark_id.normalize()`/`ids_match()` canonicalize `B4`/`B04` (and full test ids `B4-001`/`B04-001`) to one identity
- `JSONLTestCaseRepository.load_by_id`, `load_by_ids`, `load_by_benchmark` now match padding-agnostically — a caller passing either form resolves to exactly one ground-truth row, never dropped or duplicated

## Task Commits

Not committed by this executor — coordinator commits per orchestration instructions (pre-commit hook is slow and stalls subagents). All changes are staged/unstaged on disk, ready for the coordinator's commit pass.

1. **Task 1: Add graphrag to evaluate + query mode sets (+ graph-retrieval-only)** — uncommitted
2. **Task 2: Normalize B04/B4 test_id casing for GT alignment** — uncommitted

## Files Created/Modified

- `src/presentation/cli/commands/evaluate.py` — `VALID_EVAL_MODES = ["hybrid", "llm-only", "graphrag"]`; updated `--mode` help text
- `src/rag/presentation/cli/query.py` — `VALID_MODES` extended with `graphrag`/`graphrag-retrieval`; spinner labels; graph-specific config help block; examples in docstring
- `src/rag/retrieval/edges/routing.py` — `route_by_mode` routes both graphrag modes to `graph_retrieval`; `decide_after_grading` routes `graphrag-retrieval` to `rag_response` (mirrors `rag-only`), `graphrag` unchanged (falls through to `generate`/`fallback`)
- `src/rag/infrastructure/adapters/langgraph_rag_adapter.py` — `is_available()` gains a graphrag branch checking `settings.neo4j_uri`; docstrings updated for both new modes
- `src/infrastructure/adapters/repositories/jsonl_test_case_repository.py` — `load_by_id`/`load_by_ids`/`load_by_benchmark` apply `normalize_benchmark_id()` at comparison points
- `src/domain/value_objects/benchmark_id.py` (new) — `normalize()`/`ids_match()` pure functions, zero-padding canonicalization only (no benchmark renumbering)
- `tests/rag/graph/retrieval/test_graphrag_retrieval_only.py` (new) — 14 tests: mode-set constants, routing for both graphrag modes, end-to-end mocked graph_retrieve_documents -> rag_only_response with zero token counts, adapter availability
- `tests/domain/test_benchmark_id_casing.py` (new) — 16 tests: `normalize()`/`ids_match()` unit tests, repository-level padding-agnostic lookup tests (fabricated B04 GT fixture, requested via both `B4-001` and `B04-001`)

## Decisions Made

- **No retrieval-only mode on `evaluate run`:** unscoreable results have no place in a scored eval run; only `query ask` gets the inspection-only `graphrag-retrieval` variant. Matches the existing `rag-only` precedent (also `query`-only).
- **`graph_retrieval_node.py` and `rag_response.py` required zero changes** — both were already mode-agnostic (never branch on `state["mode"]`), confirming Plan 04's design already supported this extension; only `routing.py`'s edge functions needed the new mode value added to their conditionals.
- **`normalize()` isolated to id-comparison boundaries, not `BenchmarkType`:** `BenchmarkType.short_name` already strips zero-padding internally via `int()` parsing (so `BenchmarkType("B04").short_name == BenchmarkType("B4").short_name == "B4"`), meaning object-level comparisons already worked. The actual blocker was in the repository's raw-string id lookups (`test_id in test_id_set`, `case.test_id == test_id`) that bypass `BenchmarkType` entirely — that's where `normalize()` was applied.

## Deviations from Plan

**1. [Rule 2 - Missing Critical] `load_by_benchmark`'s existing string-matching branches were preserved and a third normalize()-based branch added, rather than replaced**
- **Found during:** Task 2 investigation
- **Issue:** The plan's grep-first step revealed `load_by_benchmark` already had a padding-agnostic comparison via `BenchmarkType.from_string(bt_str).short_name` (int-parsing already strips zero-padding). Removing it in favor of only `normalize()` risked losing the existing exact-string-match fast path.
- **Fix:** Added `normalize()` comparison as a third `or` branch alongside the two existing checks, rather than replacing them — defense in depth, no regression risk.
- **Files modified:** `src/infrastructure/adapters/repositories/jsonl_test_case_repository.py`
- **Verification:** `test_load_by_benchmark_resolves_unpadded_benchmark_type` passes; existing behavior unchanged for already-working paths.

---

**Total deviations:** 1 (defensive, no scope creep — purely additive to preserve existing working code paths while closing the actual gap in `load_by_id`/`load_by_ids`)

## Issues Encountered

- Initial `tests/domain/test_benchmark_id_casing.py` fixture used a too-short `question`/`expected_response` (< 50 chars), tripping `TestCase`'s domain validation (`ValidationError: Question too short`). Fixed by using realistic CCoP-shaped strings matching the actual `ground-truth/test-suite/b04_it_ot_classification_boundary.jsonl` content length. All 16 tests then passed on first subsequent run.

## User Setup Required

None — no external service configuration required. All changes are code + tests; Neo4j graph itself was not touched (already live with 625 nodes per guardrails).

## Next Phase Readiness

- D-10's full mode surface is now complete across both CLIs: `hybrid`, `llm-only`, `rag-only` (query-only), `graphrag`, `graphrag-retrieval` (query-only).
- The carried B04/B4 casing blocker (STATE.md Blockers/Concerns) is resolved for the test-case repository layer — graphrag eval results will align 1:1 with ground-truth ids regardless of which padding form a caller uses.
- No blockers for subsequent phases. The `normalize()` VO is available for reuse anywhere else id casing comparisons are needed (e.g., result repository, report generation) if further drift is discovered.

---
*Phase: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package*
*Completed: 2026-07-02*
