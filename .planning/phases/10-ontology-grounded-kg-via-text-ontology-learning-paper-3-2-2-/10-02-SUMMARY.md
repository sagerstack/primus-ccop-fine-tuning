---
phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2
plan: 02
subsystem: rag
tags: [graphrag, neo4j, langgraph, dependency-injection, mode-routing, ontology]

# Dependency graph
requires:
  - phase: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package
    provides: Neo4jGraphRetrievalAdapter, IGraphRetrievalProvider port, graph_retrieval_provider DI singleton, route_by_mode/graph_retrieve_documents node (all untouched, D-16 additivity)
provides:
  - "graph_retrieval_provider_ontology DI singleton (mode-aware second provider)"
  - "Skeleton Neo4jOntologyGraphRetrievalAdapter implementing IGraphRetrievalProvider (real clause-anchored query lands in 10-09)"
  - "All Phase 10 settings fields (ontology_config_path, shacl_shapes_path, ontology_discovery_model, function_type_boost, gleaning_max_gleanings, graphrag_ontology_enabled) — single owner of settings.py for the rest of Phase 10"
  - "function_type field on GraphState TypedDict (D-12 seam)"
  - "--mode graphrag-ontology accepted end-to-end: RunId, evaluate CLI, query CLI, evaluate_model retrieval-eval modes, and LangGraphRagAdapter.is_available (fifth gate found live)"
  - "route_by_mode distinct route key (graph_retrieval_ontology) mapped to the existing mode-aware graph_retrieval node"
  - "Live-Neo4j E2E proof that graphrag-ontology and graphrag resolve to different, provably-distinct providers"
affects: [10-03, 10-04, 10-05, 10-06, 10-07, 10-08, 10-09, 10-10, 10-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Mode-aware DI provider pair: two Singleton factories (_create_graph_retrieval_provider / _create_ontology_graph_retrieval_provider) selected by the consuming node based on state['mode'], not by the container itself"
    - "Distinct routing key mapped to a shared physical node: route_by_mode returns different string labels per mode, but the LangGraph conditional-edges map can route multiple labels to the SAME node when that node is itself mode-aware"
    - "dependency_injector test override: container.config.override(mock_settings) / reset_override() — NOT patching the get_settings name, which does not affect an already-constructed Singleton provider"

key-files:
  created:
    - src/rag/graph/retrieval/neo4j_ontology_graph_retrieval_adapter.py
    - tests/infrastructure/config/test_graph_provider_selection.py
    - tests/rag/graph/retrieval/test_graphrag_ontology_routing.py
    - .planning/phases/10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2-/deferred-items.md
  modified:
    - src/infrastructure/config/settings.py
    - src/infrastructure/config/container.py
    - src/rag/retrieval/state/graph_state.py
    - src/domain/value_objects/run_id.py
    - src/presentation/cli/commands/evaluate.py
    - src/rag/presentation/cli/query.py
    - src/rag/retrieval/edges/routing.py
    - src/rag/retrieval/graph.py
    - src/rag/graph/retrieval/graph_retrieval_node.py
    - src/rag/infrastructure/adapters/langgraph_rag_adapter.py
    - tests/rag/graph/retrieval/test_graphrag_retrieval_only.py

key-decisions:
  - "route_by_mode returns a route key DISTINCT from graphrag ('graph_retrieval_ontology' vs 'graph_retrieval') even though both target the physical graph_retrieval node — satisfies the plan's 'provably distinguishable routing' acceptance criterion without duplicating the node"
  - "Skeleton Neo4jOntologyGraphRetrievalAdapter reuses Phase 9's existing vector/fulltext index names (no new indexes yet) — real clause-anchored schema and function-type boosting land in plan 10-09"
  - "dependency_injector container tests must use container.config.override()/reset_override(), not patch(get_settings) — that patch pattern (present in the pre-existing tests/rag/test_container_vector_store.py) is a no-op against an already-constructed Singleton provider and was silently passing only because local dev env happens to match the asserted branch"

patterns-established:
  - "Second mode-aware DI singleton alongside a Phase-N provider: sibling _create_* staticmethod + Singleton, selection logic lives in the CONSUMING node (not the container), Phase-N provider/method never modified"
  - "Live-Neo4j E2E tests instantiate a FRESH Container() (not the process-wide get_container() singleton) so per-test driver.close() cannot poison a cached instance other tests in the same session might reuse"

requirements-completed: [RAG-06, D-16]

# Metrics
duration: 24min
completed: 2026-07-02
---

# Phase 10 Plan 02: Mode-Aware Provider Wiring + Ontology Skeleton Summary

**Mode-aware `graph_retrieval_provider_ontology` DI singleton + skeleton `Neo4jOntologyGraphRetrievalAdapter` + all four `--mode graphrag-ontology` CLI allowlists (plus a fifth `is_available()` gate found live), proven end-to-end against a real Neo4j instance.**

## Performance

- **Duration:** ~24 min
- **Started:** 2026-07-02T22:53:00+08:00 (approx.)
- **Completed:** 2026-07-02T23:11:49+08:00
- **Tasks:** 3
- **Files modified:** 15 (11 planned + 4 deviation files: `graph.py`, `langgraph_rag_adapter.py`, `test_graphrag_retrieval_only.py`, `deferred-items.md`) + 3 gitignore-fix source files force-added

## Accomplishments

- Closed RESEARCH Pitfall 3: `graph_retrieval_provider_ontology` is a genuine second mode-aware DI singleton; provider selection now happens inside `graph_retrieve_documents` based on `state["mode"]`, not hardcoded to Phase 9's provider
- Front-loaded ALL Phase 10 settings fields into `settings.py` in one commit, establishing single ownership for the rest of the phase (avoids Wave 3/5 write conflicts)
- Skeleton `Neo4jOntologyGraphRetrievalAdapter` implements `IGraphRetrievalProvider` and tags every returned Document with `metadata["provider"] = "graphrag-ontology"` — a live, provable routing marker (real clause-anchored query lands in plan 10-09)
- Patched all four documented `--mode` allowlists (`run_id.py`, `evaluate.py`, `query.py`, verified `evaluate_model.py`) AND discovered/fixed a fifth, undocumented gate (`LangGraphRagAdapter.is_available()`) via the plan-mandated `grep -rn "graphrag" src/` sweep — exactly the class of bug this plan exists to prevent
- Proved the routing distinction with a REAL, live-Neo4j E2E test (not just mocks): `graphrag-ontology` retrieval returns documents ALL carrying the marker, `graphrag` retrieval returns documents with NO such key, against the same live corpus KG
- Confirmed Phase 9's `graph_retrieval_provider` / `Neo4jGraphRetrievalAdapter` / `_create_graph_retrieval_provider` are byte-for-byte unchanged (`git diff` against the pre-plan commit shows zero delta in `neo4j_graph_retrieval_adapter.py`)

## Task Commits

Each task was committed atomically:

1. **Task 1: Front-load Phase 10 settings + mode-aware DI provider + skeleton ontology adapter + GraphState field** - `925edb0` (feat)
2. **Task 2: Multi-allowlist mode wiring + mode-aware retrieval node + routing branch** - `6e0113d` (feat)
3. **Task 3: E2E smallest-slice — prove graphrag-ontology routes to the NEW provider and P9 is untouched** - `74c39cf` (test)

_Note: Task 2's commit message required one in-place amend (`git commit --amend -F <file>`) to fix a tool-level backtick-expansion artifact that leaked `grep` stdout into the commit message text — the code diff itself was correct and unaffected; only the message text was corrected._

## Files Created/Modified

- `src/infrastructure/config/settings.py` - Phase 10 ontology/SHACL/routing settings block (6 new fields)
- `src/infrastructure/config/container.py` - `graph_retrieval_provider_ontology` singleton + `_create_ontology_graph_retrieval_provider`
- `src/rag/graph/retrieval/neo4j_ontology_graph_retrieval_adapter.py` - Skeleton adapter, `metadata["provider"]` routing marker
- `src/rag/retrieval/state/graph_state.py` - `function_type` field (D-12 seam)
- `src/domain/value_objects/run_id.py` - `_VALID_MODES` allowlist
- `src/presentation/cli/commands/evaluate.py` - `VALID_EVAL_MODES` allowlist + help text
- `src/rag/presentation/cli/query.py` - `VALID_MODES` allowlist + spinner_label + error-help branch
- `src/rag/retrieval/edges/routing.py` - `route_by_mode` new `graphrag-ontology` branch (distinct route key)
- `src/rag/retrieval/graph.py` - conditional-edges map entry for the new route key (deviation, see below)
- `src/rag/graph/retrieval/graph_retrieval_node.py` - mode-aware provider selection in `graph_retrieve_documents`
- `src/rag/infrastructure/adapters/langgraph_rag_adapter.py` - `is_available()` fifth gate fix (deviation, see below)
- `tests/infrastructure/config/test_graph_provider_selection.py` - DI selection + settings default tests
- `tests/rag/graph/retrieval/test_graphrag_ontology_routing.py` - routing, RunId, mode-aware node, live E2E tests
- `tests/rag/graph/retrieval/test_graphrag_retrieval_only.py` - updated 2 pre-existing exact-list assertions (deviation)
- `.planning/phases/10-.../deferred-items.md` - logged unrelated pre-existing test failure (out of scope)

## Decisions Made

- `route_by_mode` returns a route key distinct from `graphrag` while both target the same physical `graph_retrieval` node — see key-decisions in frontmatter.
- Skeleton ontology adapter reuses Phase 9's vector/fulltext index names for now; real ontology-seeded schema lands in plan 10-09.
- DI container tests use `container.config.override()` / `reset_override()`, not `patch(get_settings)` — the latter is a documented no-op against `providers.Singleton`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Force-added 3 gitignored-but-required source files**
- **Found during:** Task 1 (first attempt to run any container-importing test)
- **Issue:** `src/infrastructure/adapters/models/{mock_gateway,claude_cli_gateway,routing_gateway}.py` are imported by `container.py` at module load but are gitignored (`.gitignore`'s `models/` rule, intended for ML checkpoint directories, unintentionally shadows this source directory — same bug class as the prior `build/` shadow fixed in Phase 09-02). Without these files present, no test that imports the container could even collect in this worktree.
- **Fix:** Copied the 3 files from the main repo checkout and `git add -f`'d them into this worktree's branch.
- **Files modified:** `src/infrastructure/adapters/models/mock_gateway.py`, `claude_cli_gateway.py`, `routing_gateway.py`
- **Verification:** `tests/rag/test_container_vector_store.py` collects and passes after the fix
- **Committed in:** `925edb0` (Task 1 commit)

**2. [Rule 3 - Blocking issue] `rag/retrieval/graph.py` conditional-edges map entry**
- **Found during:** Task 2 (implementing the distinct route key)
- **Issue:** `graph.py` was not in the plan's `files_modified` list, but the plan's explicit acceptance criterion ("`route_by_mode({"mode":"graphrag-ontology"})` returns a route distinct from the `graphrag` route") combined with Task 3's requirement (a REAL `build_rag_graph().invoke()` with `mode=graphrag-ontology`) cannot both be satisfied unless the new route key resolves to a node — otherwise LangGraph raises a `KeyError` at graph-invoke time.
- **Fix:** Added one entry to the existing conditional-edges dict mapping `"graph_retrieval_ontology"` to the SAME `"graph_retrieval"` node (which is itself mode-aware — no new node created).
- **Files modified:** `src/rag/retrieval/graph.py`
- **Verification:** `test_graphrag_ontology_state_invokes_graph_retrieval_node` + the live E2E test both pass
- **Committed in:** `6e0113d` (Task 2 commit)

**3. [Rule 1 - Bug] Fifth mode-gating site: `LangGraphRagAdapter.is_available()`**
- **Found during:** Task 2, via the plan-mandated `grep -rn "graphrag" src/` sweep before declaring done
- **Issue:** `is_available()` gated only `("graphrag", "graphrag-retrieval")` against the Neo4j check; an unlisted `graphrag-ontology` would silently fall through to the vector-store (Qdrant/Databricks) availability check — exactly threat `T-10-02-01` in this plan's own threat register, and the same failure class as the Phase-9 multi-allowlist near-miss this plan exists to close.
- **Fix:** Added `"graphrag-ontology"` to the `mode in (...)` tuple.
- **Files modified:** `src/rag/infrastructure/adapters/langgraph_rag_adapter.py`
- **Verification:** No dedicated unit test added (out of the plan's explicit test list), but the fix is a one-line tuple extension mirroring the already-tested pattern; flagged here for visibility and future coverage
- **Committed in:** `6e0113d` (Task 2 commit)

**4. [Rule 1 - Bug] Two pre-existing exact-list assertions broke**
- **Found during:** Task 2 regression run (`pytest tests/rag/graph/retrieval/`)
- **Issue:** `test_graphrag_retrieval_only.py` asserted `VALID_EVAL_MODES == [...]` / `VALID_MODES == [...]` with exact-list equality against the SAME allowlists this task intentionally extends.
- **Fix:** Updated both assertions to include `"graphrag-ontology"`.
- **Files modified:** `tests/rag/graph/retrieval/test_graphrag_retrieval_only.py`
- **Verification:** Full `tests/rag/graph/retrieval/` suite green (63 passed)
- **Committed in:** `6e0113d` (Task 2 commit)

---

**Total deviations:** 4 auto-fixed (2 blocking, 2 bugs)
**Impact on plan:** All four directly necessary for correctness or to satisfy the plan's own explicit acceptance criteria. No scope creep beyond what the plan's threat model and e2e-testing mandate required.

## Issues Encountered

- **Worktree missing `.venv` and `src/config/.env.local`:** The worktree checkout lacks the gitignored Python virtualenv and Neo4j credentials present in the main repo. Symlinked `.venv` (Poetry `virtualenvs.in-project=true`, identical dependency set — no `pyproject.toml` changes in this plan) and copied `.env.local` (never committed, gitignored, contains the real `CCOP_NEO4J_PASSWORD` matching the running `neo4j-local` Docker container) so tests — including the live-Neo4j E2E — could actually run in this environment.
- **`dependency_injector.providers.Singleton(get_settings)` does not respect `patch("...get_settings")`:** Discovered while writing Task 1's tests — the Singleton captures the function object at container.py's IMPORT time, so patching the name afterward is a no-op. The pre-existing `tests/rag/test_container_vector_store.py` uses this ineffective pattern and only passes because the local dev environment happens to match the asserted branch. Not fixed (out of scope, unrelated file), but avoided in all new tests via `container.config.override()` / `reset_override()`.
- **9 pre-existing failures in `tests/domain/services/test_llm_judge_service.py`:** Confirmed unrelated to any file this plan touches (LLMJudgeService signature drift). Logged to `deferred-items.md`, not fixed.

## User Setup Required

None - no external service configuration required. (Neo4j was already running locally; no new services introduced by this plan.)

## Next Phase Readiness

- Plans 10-03 through 10-11 can now read all Phase 10 settings fields without touching `settings.py` (single-owner seam established)
- `graph_retrieval_provider_ontology` and `Neo4jOntologyGraphRetrievalAdapter` are a stable, live-proven seam for plan 10-09 to fill in the real clause-anchored, function-type-boosted retrieval query
- `--mode graphrag-ontology` is fully wired end-to-end (CLI → RunId → routing → DI → skeleton adapter) and provably distinct from Phase 9's `graphrag` — the A/B comparison this phase exists to produce has a correct, non-confounded routing foundation
- No blockers for downstream plans

---
*Phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2*
*Completed: 2026-07-02*
