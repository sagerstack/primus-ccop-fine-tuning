---
phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2
plan: 01
subsystem: testing
tags: [graphrag, neo4j, neo4j-graphrag, vector-index, determinism, evaluation, ragas, ablation]

# Dependency graph
requires:
  - phase: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package
    provides: emergent Neo4j KG, --mode graphrag, HybridCypherRetriever, rubric judge + RAGAs harness
provides:
  - "Phase 9 basic-GraphRAG 18-case baseline eval JSON over the bdc4927d fixed GT (D-16 A/B leg 1)"
  - "Locked exact-vs-ANN vector-search determinism decision for the D-15 clause-hit@3 harness"
affects: [10-09, 10-10, 10-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ANN + deterministic secondary Cypher tie-break (score DESC, citation_id ASC) + frozen index as the determinism strategy for reproducible clause-hit@3"
    - "Force-add gitignored eval-result JSON to preserve the A/B baseline artifact through the worktree merge"

key-files:
  created:
    - "docs/project_notes/research/2026-07-02-neo4j-exact-vector-search-spike.md"
    - "src/results/evaluations/2026-07/eval-run-graphrag-tests-18-bdc4927d-20260702-1459-primus-reasoning.json"
    - "src/results/evaluations/2026-07/eval-run-graphrag-tests-18-bdc4927d-20260702-1459-contexts.json"
  modified: []

key-decisions:
  - "Determinism strategy LOCKED as Option B (ANN + stable tie-break + frozen index), NOT Option A (exact-search API) — no exact mode exists at the neo4j-graphrag retriever layer that preserves hybrid dense+sparse semantics"
  - "Ran the graphrag baseline with --judge-mode rubric (parity with the canonical hybrid baseline), NOT universal, to avoid confounding the A/B"

patterns-established:
  - "Empirical determinism probe: N-repeat same-vector retrieval + exact brute-force cross-check before committing to a harness determinism assumption"

requirements-completed: []  # EVAL-02 remains pending (Phase 4/8 comparison); D-15/D-16 are discussion decisions discharged as prerequisites, not REQUIREMENTS.md checkboxes

# Metrics
duration: 108min
completed: 2026-07-03
---

# Phase 10 Plan 01: Phase-10 Prerequisites (D-16 baseline + D-15 determinism) Summary

**Basic-GraphRAG 18-case baseline (15/18 pass, overall 0.414, RAGAs 0.755) captured as A/B leg 1, and the exact-vs-ANN vector-search question resolved to a locked stable-tie-break determinism strategy for the D-15 harness.**

## Performance

- **Duration:** ~108 min (dominated by the 102-min 18-case eval run; spike ran concurrently)
- **Started:** 2026-07-02T14:59:13Z
- **Completed:** 2026-07-03 (eval completed 2026-07-02T16:41:26Z)
- **Tasks:** 2
- **Files modified:** 3 created

## Accomplishments
- Executed the deferred Phase 9 Wave-6 18-case basic-GraphRAG baseline (D-16 hard dependency) over the exact `bdc4927d` fixed GT — 18/18 cases scored, rubric-judged, identical Phase 9 stack with only the `--mode graphrag` label. This is A/B leg 1 for plan 10-11.
- Resolved RESEARCH Open Question 1 / Pitfall 2: confirmed via official `neo4j-graphrag-python` docs + a live empirical probe that no exact (non-ANN) search mode exists at the retriever layer, and locked the determinism strategy for the D-15 clause-hit@3 harness.
- Discovered and documented a latent non-determinism risk (missing secondary sort key + a real 1.0/1.0 score tie between two distinct chunks) that 10-09/10-10 must fix.

## Task Commits

Each task was committed atomically:

1. **Task 2: Exact vector-search / determinism spike** - `899d46f` (docs)
2. **Task 1: Phase 9 basic-GraphRAG 18-case baseline** - `59ff530` (feat)

_(Task 2 was committed first because its concurrent spike completed before the long eval run; both tasks are fully independent.)_

## Files Created/Modified
- `docs/project_notes/research/2026-07-02-neo4j-exact-vector-search-spike.md` - Spike finding: (a) no exact-search mode at retriever layer, (b) observed bit-stable ANN ordering on a frozen index, (c) LOCKED determinism decision (ANN + `ORDER BY score DESC, citation_id ASC` + frozen index).
- `src/results/evaluations/2026-07/eval-run-graphrag-tests-18-bdc4927d-20260702-1459-primus-reasoning.json` - The graphrag baseline: 18 rubric-judged test_results, overall 0.414, RAGAs 0.755, 15 passed / 3 failed at 15% threshold.
- `src/results/evaluations/2026-07/eval-run-graphrag-tests-18-bdc4927d-20260702-1459-contexts.json` - Retrieved-context sidecar for the run (per-case audit trail).

### Baseline scores (per-case)

| test_id | score | RAGAs | passed |
|---|---|---|---|
| B01-001 | 0.389 | 0.859 | ✓ |
| B02-001 | 0.333 | 0.787 | ✓ |
| B03-001 | 0.333 | 0.876 | ✓ |
| B04-001 | 0.556 | 0.715 | ✓ |
| B05-001 | 0.278 | 0.693 | ✓ |
| B06-001 | 0.222 | 0.775 | ✓ |
| B07-006 | 0.556 | 0.791 | ✓ |
| B08-001 | 0.611 | 0.744 | ✓ |
| B09-001 | 0.556 | 0.758 | ✓ |
| B10-001 | 0.444 | 0.862 | ✓ |
| B12-001 | 0.389 | 0.790 | ✓ |
| B13-001 | 0.056 | 0.557 | ✗ |
| B14-001 | 0.722 | 0.761 | ✓ |
| B18-001 | 0.556 | 0.890 | ✓ |
| B21-001 | 0.556 | 0.732 | ✓ |
| B22-001 | 0.000 | 0.753 | ✗ |
| B23-001 | 0.111 | 0.853 | ✗ |
| B24-001 | 0.278 | 0.670 | ✓ |

**Overall:** benchmark score 0.414, RAGAs overall 0.755, 15/18 passed (baseline 15% threshold).

## Decisions Made
- **Determinism strategy = Option B (ANN + stable tie-break + frozen index).** `neo4j-graphrag-python` 1.18.0 exposes only Neo4j's HNSW-based ANN vector index through every retriever (incl. `HybridCypherRetriever`). A genuine exact path exists only via raw-Cypher `vector.similarity.cosine()`, but that drops the sparse/fulltext leg and would silently change what "graphrag" retrieval means — out of scope for D-16 additivity. So determinism must come from a stable secondary Cypher sort key + a frozen index, not an exact-search API.
- **Rubric judge, not universal.** The canonical hybrid baseline is rubric-judged; the graphrag baseline was run with `--judge-mode rubric` for parity (T-10-01-02 mitigation) so the A/B isolates retrieval, not judge mode.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing gitignored source files prevented CLI startup in the worktree**
- **Found during:** Task 1 (initial `ccop-eval` invocation)
- **Issue:** `src/infrastructure/adapters/models/{mock_gateway,claude_cli_gateway,routing_gateway}.py` are excluded by the `.gitignore` `models/` pattern (line 139) and exist only as untracked files in the main checkout. `container.py` imports `mock_gateway` unconditionally, so a fresh worktree could not run the CLI at all (`ModuleNotFoundError`). Similarly `config/.env.local` (gitignored) was absent.
- **Fix:** Copied the three untracked gateway files and `config/.env.local` from the main checkout into the worktree (runtime prerequisite only — no code change, nothing committed).
- **Verification:** `ccop-eval setup check` and `graph stats` then ran successfully (Ollama up, Neo4j graph = 684 nodes / 1310 edges).
- **Committed in:** N/A (environment fix, not a code change). Root-cause `.gitignore` shadowing logged to `deferred-items.md` — same bug class as the Phase 9 `src/rag/graph/build/` shadowing already fixed; the proper `.gitignore` fix is out of scope for this plan.

**2. [Rule 3 - Blocking] `CCOP_TEST_CASES_DIR` pointed at a non-existent audit subdir**
- **Found during:** Task 1 (first eval run loaded 0 test cases)
- **Issue:** The copied `config/.env.local` set `CCOP_TEST_CASES_DIR=../ground-truth/test-suite/audit-20260629-1245`, which does not exist in the worktree (untracked in main), so 0 test cases were discovered and the run produced an empty result.
- **Fix:** Re-ran with `CCOP_TEST_CASES_DIR=../ground-truth/test-suite` (the committed active suite, the correct source for the bdc4927d ids), which loaded all 18 cases.
- **Verification:** Run log showed "Loaded 18 test cases"; final JSON has 18 test_results with the exact bdc4927d id set.
- **Committed in:** N/A (env override at invocation, not a code change).

---

**Total deviations:** 2 auto-fixed (both Rule 3 blocking, both environment/config — no source code changed).
**Impact on plan:** Both were worktree-environment gaps (gitignored files absent from a fresh checkout), not plan defects. The eval itself ran the identical Phase 9 stack with the single `--mode graphrag` label as specified — no generator/embedder/retrieval config change. No scope creep.

## Issues Encountered
- **Canonical hybrid baseline JSON has a corrupted B04 `test_id`.** `eval-run-hybrid-tests-18-bdc4927d-20260430-0232-primus-reasoning.json` (the `MEMORY.md`-designated canonical run) has `"\n      "` instead of `"B04-001"` at the top-level `test_results[].test_id` for the B04 entry; its sibling `.partial.jsonl` has the correct `"B04-001"`. The 18-id set was reliably reconstructed from the partial log. Logged to `deferred-items.md` as a data-integrity item (out of scope — read-only input here).
- **Lucene fulltext lexical error on B02-001.** The graph retriever's Lucene sparse leg threw a `TokenMgrError` on the `/` and `'` characters in the B02-001 question ("username/password ... user's ..."); the graph node caught it, fell back to the no-context generation path (no crash), and B02-001 still scored (0.333, passed). This is pre-existing Phase 9 retrieval-adapter behavior; the plan forbids touching retrieval config, so it was reproduced faithfully and logged to `deferred-items.md` for a future adapter fix (likely 10-09).

## Known Stubs
None — this plan produced an eval-result artifact and a research note; no application code or UI-facing data paths were created or stubbed.

## Threat Flags
None — no new network endpoints, auth paths, file-access patterns, or schema changes were introduced. The run reads the existing Neo4j graph and sources the OpenRouter judge key via `CCOP_OPENROUTER_API_KEY` env only (T-10-01-01 mitigation held; no key in logs/JSON).

## User Setup Required
None - no external service configuration required (Neo4j, Qdrant, and Ollama were already running; the OpenRouter judge key was already present in the environment).

## Next Phase Readiness
- **D-16 A/B leg 1 is ready:** the graphrag baseline JSON is committed and consumable by plan 10-11's report (pattern `eval-run-graphrag-tests-18-bdc4927d`).
- **D-15 determinism question is resolved:** plans 10-09 (adapter tie-break) and 10-10 (harness) can implement without re-litigating — they MUST add `ORDER BY score DESC, citation_id ASC` (or the seeded-clause-id equivalent) to the retrieval Cypher and document the frozen-index precondition.
- **Carry-forward:** `.gitignore` `models/` shadowing bug, canonical-baseline B04 `test_id` corruption, and the Lucene special-character escaping gap are logged in `deferred-items.md` for future plans/bugfixes.

## Self-Check: PASSED

- Created files verified present: spike note, graphrag baseline JSON, contexts sidecar — all FOUND.
- Task commits verified in git log: `899d46f` (Task 2), `59ff530` (Task 1) — both FOUND.

---
*Phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2*
*Completed: 2026-07-03*
