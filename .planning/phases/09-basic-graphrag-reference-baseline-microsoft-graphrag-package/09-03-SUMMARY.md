---
phase: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package
plan: 03
subsystem: graphrag
tags: [neo4j, kg-quality, kg-inspection, cypher, typer, rich, d-18, d-19]

# Dependency graph
requires:
  - phase: 09-02
    provides: "Live emergent CCoP KG in Neo4j (625 nodes / 1,232 relationships / 179 chunks / 7 documents), ccop-eval graph build CLI, EmergentKGBuilder"
provides:
  - "KGInspector (src/rag/graph/inspect/metrics.py) — D-18 metric methods: node/edge counts, entity-type distribution, degree histogram, orphan-node count, clause coverage vs clause_inventory.json, duplicate-entity grouping, extraction failure rate"
  - "ccop-eval graph inspect (human Rich report) + graph stats (JSON, optional --output) CLI commands"
  - "docs/phase-2/neo4j-browser-workflow.md — visual inspection Cypher snippets + D-19 honesty guardrail"
  - "Live-validated finding: 51 duplicate-entity groups in the current corpus graph (e.g. user123 x20, CII-001 x28) — genuine emergent-extraction boilerplate-ID artifact, surfaced but NOT fixed (out of this plan's scope, flagged for a D-19 iteration decision)"
affects: [09-04-graph-retrieval-provider, 09-05-graphrag-eval-integration, 09-06-comparison-report, 10-ontology-grounded-kg]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cypher COUNT { (n)--() } (Neo4j 5.x) instead of size((n)--()) — the older size()-over-pattern-expression form is a hard syntax error on the installed Neo4j version, not just a deprecation warning"
    - "Chunk-text substring matching (not schema-seeded lookups) for clause coverage — reads all Chunk.text once via a parameterless Cypher query, then does boundary-aware regex matching in Python against clause_inventory.json entries; avoids ever interpolating a clause_id into Cypher"
    - "Priority-ordered display-name extraction for duplicate-entity grouping — entities extracted without a schema (D-03/D-08) have heterogeneous property shapes per type (User.user_id vs Vendor.name vs CIIAsset.asset_id); KGInspector tries a fixed priority list of candidate identifying properties before falling back to a full-property-set join"

key-files:
  created:
    - src/rag/graph/inspect/__init__.py
    - src/rag/graph/inspect/metrics.py
    - tests/rag/graph/test_kg_metrics.py
    - tests/rag/graph/inspect/__init__.py
    - tests/rag/graph/inspect/test_kg_metrics_integration.py
    - tests/rag/graph/test_graph_cli_inspect.py
    - docs/phase-2/neo4j-browser-workflow.md
  modified:
    - src/rag/graph/cli/graph.py

key-decisions:
  - "COUNT { (n)--() } instead of the plan-adjacent size((n)--()) idiom — discovered live against the installed Neo4j version (Rule 1, bug fix during Task 1 development, before commit)"
  - "Clause coverage computed by reading all Chunk.text once and matching in Python (boundary-aware regex), not via a per-clause_id Cypher query — keeps every Cypher statement either parameter-free or free of interpolated values (T-09-09), and is far cheaper than 738 round-trip queries"
  - "duplicate_entities groups on a priority-ordered display name (id-like properties before descriptive ones like username) — verified against the live graph's actual property shapes (User.user_id vs username diverge in the corpus; grouping on the identifier field, not the descriptive label, matches the intended 'same underlying entity' semantics)"
  - "extraction_failure_rate returns a fixed 0.0-with-note payload — BuildStats.failures (EmergentKGBuilder) is an in-memory, per-run result never persisted to Neo4j; there is no durable failure log to query, so honesty (D-19) means reporting 'no data' explicitly rather than fabricating a number from unrelated graph state"

patterns-established:
  - "KGInspector is read-only and stateless (constructed from a driver + database name) — mirrors EmergentKGBuilder's constructor-injection style but has zero write paths, matching the T-09-09/T-09-10 threat-model dispositions for this plan"

requirements-completed: [D-18, D-19]

# Metrics
duration: ~35min
completed: 2026-07-01
---

# Phase 9 Plan 03: KG Quality Inspection (D-18/D-19) Summary

**`ccop-eval graph inspect`/`graph stats` (KGInspector) plus a documented Neo4j Browser workflow make the emergent CCoP graph seen and measured — live-validated against the real 625-node/1,232-edge corpus graph, which it left completely untouched, and which it surfaced 51 duplicate-entity groups and 67.2% clause coverage from.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-07-01 (after context load)
- **Completed:** 2026-07-01
- **Tasks:** 3/3
- **Files modified:** 7 created, 1 modified

## Accomplishments
- `KGInspector` computes all D-18 metrics — node/edge counts, entity-type distribution (excluding neo4j-graphrag's own `__KGBuilder__`/`__Entity__`/`Chunk`/`Document` bookkeeping labels), degree histogram, orphan-node count, clause coverage vs `clause_inventory.json`, duplicate-entity grouping, and extraction failure rate — using exclusively parameterized or static-literal Cypher (T-09-09; grep-gated in acceptance).
- `ccop-eval graph inspect` (Rich human report) and `graph stats` (JSON, `--output` optional) added to the existing `graph_app`, both read-only against Neo4j credentials sourced from settings (T-09-10).
- `docs/phase-2/neo4j-browser-workflow.md` documents the interactive half of D-18: opening Browser at `localhost:7474`, 6 Cypher inspection snippets, and an explicit honesty-guardrail section for D-19 (iterate to fix broken extraction, never to chase B01/B03/B04 scores).
- **Live-validated end-to-end against the real corpus graph** (not a synthetic/mocked one): 625 nodes / 1,232 relationships confirmed intact before and after every command run in this plan. `graph inspect` correctly reported clause_coverage 496/738 (67.2%), 51 duplicate-entity groups, and the full entity-type distribution (18 emergent types, `CybersecurityIncident` dominant at 77).
- Surfaced a genuine, actionable D-19 finding: the emergent (schema-free) extraction has collapsed many distinct source mentions onto generic boilerplate-style identifiers — `CII-001` appears 28 times, `Inc001` 25 times, `user123` 20 times, `asset456` 15 times. This is exactly the "garbage or functional?" signal D-18/D-19 exist to surface; it was **not** fixed in this plan (out of scope — Plan 09-02's build output; a D-19 iteration decision for the coordinator/user to make before Plan 09-05/06 score against this graph).

## Task Commits

Each task was committed atomically:

1. **Task 1: KGInspector metric methods** — `29e553f` (feat, TDD) — RED confirmed (`ModuleNotFoundError`) → GREEN (12/12 unit tests + 2/2 integration tests passing)
2. **Task 2: `graph inspect` + `graph stats` CLI commands** — `d3f859c` (feat) — 5/5 unit tests passing (mocked KGInspector)
3. **Task 3: Neo4j Browser visual-inspection workflow doc** — `f927d0d` (docs)

_TDD note: Task 1 followed RED → GREEN; no separate REFACTOR commit was needed (one mid-development fix — the Neo4j `COUNT {}` syntax correction — was made before the RED→GREEN gate closed, not as a follow-up refactor)._

## Files Created/Modified
- `src/rag/graph/inspect/__init__.py` — package init
- `src/rag/graph/inspect/metrics.py` — `KGInspector` class + `DEFAULT_CLAUSE_INVENTORY_PATH`
- `src/rag/graph/cli/graph.py` — added `inspect_command`/`stats_command` + `_print_inspect_report` helper to the existing `graph_app`
- `tests/rag/graph/test_kg_metrics.py` — 12 unit tests (mocked neo4j session)
- `tests/rag/graph/inspect/__init__.py` — package init
- `tests/rag/graph/inspect/test_kg_metrics_integration.py` — 2 `@pytest.mark.integration` tests, READ-ONLY against the live graph
- `tests/rag/graph/test_graph_cli_inspect.py` — 5 unit tests (mocked `KGInspector` + neo4j driver) for both CLI commands
- `docs/phase-2/neo4j-browser-workflow.md` — Browser workflow + Cypher snippets + honesty guardrail

## Decisions Made
- **`COUNT { (n)--() }` instead of `size((n)--())`:** the plan's natural Cypher idiom for degree (`size()` over a pattern expression) is a hard `CypherSyntaxError` on the installed Neo4j version (5.x removed it, not merely deprecated it). Discovered via live sanity-check before committing; fixed in the same task (Rule 1 — bug, pre-commit).
- **Clause coverage via one bulk Chunk.text read + Python regex, not per-clause_id Cypher:** avoids 738 round-trip queries and keeps every Cypher statement free of interpolated values. Matching uses a boundary-aware regex (`(?<![A-Za-z0-9])...( ?!...)`) so short numeric clause_ids (e.g. `"1"`) don't spuriously match inside longer ones (e.g. `"15.37"`) — verified with a dedicated unit test and against the live graph (496/738 = 67.2% coverage, a plausible number given the fixed-size, non-clause-aware chunk splitter documented in 09-02's SUMMARY).
- **Duplicate-entity display-name priority reordered during TDD:** the first draft tried `username` before `user_id`-style fields, which failed a test asserting that two nodes with the same `user_id` (differing case) but different `username` values should still group together. Reordered priority to put identifier-shaped fields (`user_id`, `asset_id`, `incident_id`, etc.) ahead of descriptive labels (`username`) — the correct semantics for "same underlying entity."
- **`extraction_failure_rate` is a fixed honest default, not a live query:** `BuildStats.failures` (Plan 09-02) is constructed and discarded per `graph build` run; nothing is persisted to Neo4j for KGInspector to read. Rather than approximate this from unrelated graph state, the method returns `{"rate": 0.0, "note": "..."}` — matching the plan's explicit "reads BuildStats-style failures if available else returns 0.0 with a note" instruction.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `size((n)--())` is a hard Cypher syntax error on the installed Neo4j version**
- **Found during:** Task 1, live sanity-check of `degree_distribution()`/`summary()` against the real corpus graph (before any commit)
- **Issue:** `MATCH (n) RETURN size((n)--()) AS degree` raised `neo4j.exceptions.CypherSyntaxError` — Neo4j 5.x requires `COUNT { pattern }` for counting pattern-expression matches; `size()` over a pattern expression is no longer accepted (not just deprecated).
- **Fix:** Changed the query to `MATCH (n) RETURN COUNT { (n)--() } AS degree`; updated the corresponding unit-test query-fixture keys to match.
- **Files modified:** `src/rag/graph/inspect/metrics.py`, `tests/rag/graph/test_kg_metrics.py`
- **Verification:** Re-ran `summary()` against the live graph — succeeded, returned `{"min": 1, "max": 40, "avg": 3.94, ...}`; unit tests green.
- **Committed in:** `29e553f` (Task 1 commit — fixed before commit, not as a follow-up)

---

**Total deviations:** 1 auto-fixed (1 bug fix, caught pre-commit via live sanity-check).
**Impact on plan:** Necessary correctness fix (the plan's intended metric was otherwise unreachable on the installed Neo4j version). No scope creep — no other query, CLI surface, or file beyond what the plan specified was touched.

## Issues Encountered

**Pre-existing test failures (out of scope, NOT fixed):** `poetry run pytest -m "not integration"` surfaces the same 9 pre-existing failures in `tests/domain/services/test_llm_judge_service.py` documented in `09-01-SUMMARY.md` and `09-02-SUMMARY.md` (rubric-dict vs `benchmark_id: str` signature drift from an earlier OpenRouter migration commit, predating this plan). Confirmed identical failure count and file — no new failures introduced by this plan's changes (69 passed, 9 pre-existing failures, 7 deselected integration tests; up from 09-02's 52 passed because this plan added 17 new tests, all passing).

**Extraction-quality finding (not a plan deviation — this is exactly what D-18/D-19 exist to surface):** running the newly built `KGInspector`/`ccop-eval graph inspect` against the live corpus graph revealed that the emergent (schema-free) extraction produced 51 duplicate-entity groups, several dominated by clearly generic/boilerplate-style identifiers (`user123` x20, `CII-001` x28, `asset456` x15, `Inc001` x25) rather than distinct entity mentions. This was **surfaced, not fixed** — it is Plan 09-02's build output, and per the D-19 honesty guardrail (documented in this plan's own `neo4j-browser-workflow.md`), whether/how to address it is an iteration decision for the coordinator, not something to silently patch inside an inspection-tooling plan. Flagged here for visibility before Plan 09-05/06 scores against this graph.

## User Setup Required

None — Neo4j was already live with the real corpus graph per the environment context provided for this plan; no new external service configuration was introduced.

## Next Phase Readiness

- D-18 (KG-quality inspection, both quantitative and visual) and D-19 (the iterate-and-improve loop + honesty guardrail) are fully implemented and live-validated.
- **Coordinator decision point before Plan 09-04/05 proceed:** the live graph currently shows 67.2% clause coverage and significant duplicate-entity collapse on generic identifiers. Per D-19, this is a legitimate moment to decide whether to iterate (rebuild with `--drop` after investigating, e.g., whether chunk splitting or the absence of an entity resolver is the dominant cause) or to proceed and treat the current graph as the honest emergent baseline, documenting the finding in the eventual Plan 09-06 comparison report. This plan does not make that call — it only makes the decision *informed*.
- `ccop-eval graph inspect|stats` is ready to be re-run after any rebuild, and `graph stats --output` is ready to feed Plan 09-06's KG-quality report section (D-15) as-is (JSON schema: `node_count`, `edge_count`, `entity_type_distribution`, `degree_distribution`, `orphan_nodes`, `clause_coverage`, `duplicate_entities`, `extraction_failure_rate`).
- Live graph confirmed intact at the end of this plan: 625 nodes / 1,232 relationships / 179 chunks / 7 documents — unchanged from the state at the start of this plan.

## Self-Check: PASSED

All created files verified on disk (`src/rag/graph/inspect/__init__.py`, `src/rag/graph/inspect/metrics.py`, `tests/rag/graph/test_kg_metrics.py`, `tests/rag/graph/inspect/__init__.py`, `tests/rag/graph/inspect/test_kg_metrics_integration.py`, `tests/rag/graph/test_graph_cli_inspect.py`, `docs/phase-2/neo4j-browser-workflow.md`) and modified file (`src/rag/graph/cli/graph.py`). All three task commits (`29e553f`, `d3f859c`, `f927d0d`) present in `git log`. `poetry run ccop-eval graph inspect --help` and `graph stats --help` both verified exit 0. Live-Neo4j integration tests passed (2 passed). Full `poetry run pytest -m "not integration"` run: 69 passed, 9 pre-existing (unrelated) failures, no regressions. Live graph node/edge/chunk/document counts (625/1232/179/7) verified unchanged before and after every command executed in this plan.

---
*Phase: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package*
*Completed: 2026-07-01*
