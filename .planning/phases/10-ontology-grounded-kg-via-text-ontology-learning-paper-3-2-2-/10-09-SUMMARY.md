---
phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2
plan: 09
subsystem: graphrag-ontology
tags: [neo4j, neo4j-graphrag, cypher, function-type-routing, lucene, determinism, langgraph, ranking]

# Dependency graph
requires:
  - phase: 10-05
    provides: ClauseSeeder / seeded :Clause backbone with function_type tags (D-09/D-10)
  - phase: 10-07
    provides: OntologyKGBuilder + ClauseLinker (:Chunk/:Entity -[:LINKED_TO]-> :Clause edges)
provides:
  - "Real clause-anchored RETRIEVAL_QUERY in Neo4jOntologyGraphRetrievalAdapter: OPTIONAL MATCH LINKED_TO :Clause, real clause_id as citation_id (fixes Phase 9 honesty note)"
  - "Function-type boost (D-12): CASE WHEN c.function_type = $function_type THEN score * $boost, both bound Cypher params"
  - "Deterministic tie-break: ORDER BY boosted_score DESC, resolved_citation_id ASC (D-15, LOCKED 10-01 decision)"
  - "Lucene special-character escaping (_escape_lucene_query_text) fixing the B02-001-class TokenMgrError for the ontology adapter's sparse leg"
  - "function_type_routing LangGraph node classifying question intent (ScopeClause/ControlClause/DefinitionClause) into state[function_type], gated on mode==graphrag-ontology"
  - "Real LangGraph wiring: function_type_routing node runs before graph_retrieval on the ontology path (graph.py), verified state mutations do NOT persist through conditional-edge side effects"
affects: [10-10, 10-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dense leg embeds the original un-escaped query; sparse/Lucene leg gets a separately-escaped copy of the same query text -- avoids corrupting semantic embedding while fixing Lucene parser errors"
    - "Concrete adapter override adds an additional optional kwarg (function_type) beyond the shared port's abstract signature -- Python ABC does not enforce exact signature parity, so Phase 9's adapter and the port stay untouched (D-16 additivity)"
    - "LangGraph conditional-edge functions cannot persist state mutations (verified empirically) -- classification must be a real graph node with its own edge, never a route-function side effect"

key-files:
  created:
    - src/rag/retrieval/nodes/function_type_routing.py
    - tests/rag/graph/retrieval/test_ontology_graph_retrieval_adapter.py
    - tests/rag/retrieval/nodes/test_function_type_routing.py
    - tests/rag/retrieval/__init__.py
    - tests/rag/retrieval/nodes/__init__.py
  modified:
    - src/rag/graph/retrieval/neo4j_ontology_graph_retrieval_adapter.py
    - src/rag/retrieval/graph.py
    - src/rag/graph/retrieval/graph_retrieval_node.py
    - src/rag/retrieval/edges/routing.py

key-decisions:
  - "graph.py and graph_retrieval_node.py were modified beyond the plan's declared files_modified list -- necessary Rule 2 (missing critical functionality): a LangGraph conditional-edge function (route_by_mode) cannot persist state mutations to downstream nodes (verified empirically with a minimal StateGraph reproduction), so state[function_type] can only reach the boosted Cypher query via a real graph node + edge, and graph_retrieve_documents must be the one to thread it into the ontology provider's retrieve() call"
  - "retrieve()'s function_type parameter is an ADDITIONAL optional kwarg on the concrete Neo4jOntologyGraphRetrievalAdapter override only -- the shared IGraphRetrievalProvider port and Phase 9's Neo4jGraphRetrievalAdapter.retrieve(query, top_k) are both completely untouched (D-16 additivity); Python's ABC machinery does not enforce exact signature parity between an abstract method and its override"
  - "Lucene escaping applies ONLY to the fulltext/sparse leg's query_text parameter -- the dense leg is embedded once via self._embedder.embed_query(query) on the original un-escaped text and passed explicitly as query_vector, so HybridCypherRetriever's internal 'if query_text and not query_vector: embed' branch is skipped and the semantic embedding is never affected by escaping"
  - "ontology_discovery_model (already in settings.py from plan 10-02) is reused for function-type classification rather than adding a new settings field -- semantically the correct existing seam (an ontology-guided LLM task) and avoids a settings.py write outside this plan's declared scope"

patterns-established:
  - "Live-Neo4j smallest-slice E2E via a tiny synthetic multi-clause text string (not the CLI's --sample flag, which parses the FULL first real CCoP document via Docling and is too slow for a verification slice) -- proves the seed -> build -> link -> retrieve -> classify chain in under a minute"

requirements-completed: [RAG-02, D-12, D-11, D-15]

# Metrics
duration: ~40min
completed: 2026-07-03
---

# Phase 10 Plan 09: Real Clause-Anchored Retrieval + Function-Type Routing (D-12) Summary

**Filled the 10-02 skeleton adapter with a real clause-anchored, function-type-boosted Cypher query (D-12/D-11) plus a deterministic tie-break (D-15) and a Lucene-escaping fix, and wired a new `function_type_routing` LangGraph node so the classified question intent reaches the boosted query before it executes — proven live against Neo4j with a real boosted-vs-unboosted score difference (1.5 vs 1.0).**

## Performance

- **Duration:** ~40 min (includes a fresh-worktree `poetry install`, killing an oversized `--sample` CLI build attempt, and a targeted live E2E slice)
- **Completed:** 2026-07-03
- **Tasks:** 2 completed (both TDD-shaped: mocked unit tests + a live-Neo4j E2E slice)
- **Files modified:** 9 (2 new source modules, 4 new/modified test files, 2 modified LangGraph wiring files, 1 modified port-caller node)

## Accomplishments

- `Neo4jOntologyGraphRetrievalAdapter.RETRIEVAL_QUERY` now `OPTIONAL MATCH`-expands every matched `:Chunk` to its seeded `:Clause` via `LINKED_TO` (ClauseLinker, plan 10-07), returning the REAL `clause_id` as `citation_id`/`section` — the concrete fix for the Phase 9 "Honesty note" (`citation_id` was previously `elementId(chunk)` only).
- `CASE WHEN c.function_type = $function_type THEN score * $boost ELSE score END AS boosted_score` implements the D-12 ranking lever; `$function_type` and `$boost` are bound Cypher parameters passed via `HybridCypherRetriever.search(query_params=...)`, never string-interpolated (T-09-12/T-10-09-01).
- `ORDER BY boosted_score DESC, resolved_citation_id ASC` implements the LOCKED 10-01 determinism decision (D-15: ANN + stable secondary sort key + frozen index — no exact-search API exists at the retriever layer that preserves hybrid dense+sparse semantics).
- `_escape_lucene_query_text` fixes the B02-001-class `TokenMgrError` (deferred from plan 10-01) by escaping Lucene classic-QueryParser special characters (`/`, `'`, and the standard set) in the sparse/fulltext `query_text` parameter, while the dense leg embeds the original un-escaped query — verified live with a question containing both `/` and `'`.
- `function_type_routing.py`'s `classify_function_type` mirrors `query_analysis.py`'s HyDE call shape (settings-gated OpenRouter gpt-4o-mini, try/except-log-return degradation), classifying into exactly one of the D-09 locked tags (`ScopeClause`/`ControlClause`/`DefinitionClause`), gated on `mode == "graphrag-ontology"`, with output validated against the 3-value enum before it can reach the Cypher-bound parameter.
- Discovered (via an empirical LangGraph reproduction) that conditional-edge functions like `route_by_mode` cannot persist state mutations to downstream nodes — classification therefore had to be wired as a REAL LangGraph node (`function_type_routing`) with its own edge into `graph_retrieval`, not a side effect inside the router. `graph_retrieve_documents` now threads `state["function_type"]` into the ontology provider's `retrieve()` call only when `mode == "graphrag-ontology"`; Phase 9's call site is unchanged.
- **Real smallest-slice E2E**, run live against local Neo4j + real OpenRouter: seeded the 883-clause backbone, built a tiny synthetic two-clause document (`OntologyKGBuilder.build()`, one real gpt-4o-mini extraction call), linked it (`ClauseLinker.link()`, 329 `LINKED_TO` edges), then called the real adapter and the real classifier. The ScopeClause-boosted query returned clause `"1"` FIRST at `boosted_score=1.5` (base score `1.0 × function_type_boost 1.5`), with every other tied result at `1.0` ordered alphabetically by `citation_id` (`"1"`, `"1.2"`, `"1.2.1"`, `"2"`, ...) — proving the boost arithmetic, the tie-break, and the real-clause-id citations all execute correctly in live Cypher, not just in mocks. A Lucene-escaping smoke query ("username/password plus the user's SMS OTP") returned 47 documents with no `TokenMgrError`. `classify_function_type` correctly classified a live scope question as `"ScopeClause"` via a real OpenRouter call. Graph cleaned up to the 883-clause baseline afterward (verified via direct Cypher count).

## Task Commits

Each task was committed atomically:

1. **Task 1: Clause-anchored ontology retrieval adapter — function-type boost + stable tie-break (D-12/D-11/D-15)** — `62ecb43` (feat)
2. **Task 2: Function-type routing node (D-12) + graph wiring** — `83d8c4e` (feat)

**Plan metadata:** `2b75a14` (docs: mark the Lucene bug resolved for the ontology adapter in deferred-items.md; still open for Phase 9's untouched adapter)

## Files Created/Modified

- `src/rag/graph/retrieval/neo4j_ontology_graph_retrieval_adapter.py` — real `RETRIEVAL_QUERY` (LINKED_TO clause anchoring + boost + tie-break), `_escape_lucene_query_text`, `retrieve(..., function_type="")`.
- `tests/rag/graph/retrieval/test_ontology_graph_retrieval_adapter.py` — 20 unit tests (metadata mapping, bound-param assertions, boost-ordering passthrough, real-clause-id citations, Cypher-safety string assertions, Lucene escaping, construction wiring).
- `src/rag/retrieval/nodes/function_type_routing.py` — `classify_function_type`, `FUNCTION_TYPE_PROMPT`, `VALID_FUNCTION_TYPES`.
- `tests/rag/retrieval/nodes/test_function_type_routing.py` — 12 unit tests (mode gating, fixture classification, graceful degradation, enum validation).
- `tests/rag/retrieval/__init__.py`, `tests/rag/retrieval/nodes/__init__.py` — new test-package markers (mirrors existing `tests/rag/graph/**/__init__.py` convention).
- `src/rag/retrieval/graph.py` — new `function_type_routing` node registered and wired between `query_analysis`'s conditional edge and `graph_retrieval` on the ontology path only.
- `src/rag/graph/retrieval/graph_retrieval_node.py` — mode-aware `retrieve()` call now threads `state["function_type"]` for the ontology branch.
- `src/rag/retrieval/edges/routing.py` — docstring updated to describe the new node target (return value/route key unchanged).

## Decisions Made

- **`graph.py`/`graph_retrieval_node.py` modified beyond the plan's declared `files_modified`** — this is documented as a Rule 2 deviation below; it was structurally required, not scope creep.
- **`function_type` is an additional optional kwarg on the concrete adapter override, not a port-signature change** — preserves `IGraphRetrievalProvider`'s existing abstract contract and Phase 9's untouched adapter (D-16 additivity).
- **Reused `settings.ontology_discovery_model`** for the classification LLM rather than adding a new settings field — avoids a `settings.py` write outside this plan's scope (10-02 established it as the single-owner file for the rest of Phase 10) and is the semantically correct existing seam.
- **Lucene escaping scoped to the sparse leg only** — the dense-vector embedding always uses the original, un-escaped query text (embedded explicitly via `self._embedder.embed_query(query)` and passed as `query_vector`), so escaping cannot silently degrade semantic retrieval quality.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] `graph.py` and `graph_retrieval_node.py` required modification beyond the plan's declared `files_modified` list to make D-12 actually function**
- **Found during:** Task 2, while implementing the "wire the node... in routing.py" instruction.
- **Issue:** The plan's Task 2 action text says to wire `function_type_routing` "into the ontology retrieval path in `routing.py`" and lists only `function_type_routing.py`, `edges/routing.py`, and its test as files to modify. `routing.py` contains only conditional-edge *route-selector* functions (`route_by_mode`, `decide_after_grading`) — it does not register LangGraph nodes. I empirically verified (a minimal `StateGraph` reproduction) that LangGraph conditional-edge functions do NOT persist state mutations to downstream nodes — only a node function's return value is merged into graph state. A side-effect mutation inside `route_by_mode` would therefore silently fail to set `state["function_type"]` before the ontology query runs, making the entire D-12 mechanism dead code despite passing a naive smoke test.
- **Fix:** Registered `function_type_routing` as a real LangGraph node in `src/rag/retrieval/graph.py` (`workflow.add_node(...)` + a new edge into `graph_retrieval`), and changed the `graphrag-ontology` conditional-edge target from `graph_retrieval` directly to the new node. Modified `src/rag/graph/retrieval/graph_retrieval_node.py` so the mode-aware `graph_retrieve_documents` node threads `state["function_type"]` into the ontology provider's `retrieve()` call (Phase 9's call site is unchanged, preserving D-16 additivity). `route_by_mode`'s return value/route key (`"graph_retrieval_ontology"`) is UNCHANGED, so `test_graphrag_ontology_routing.py` (from plan 10-02) continues to pass unmodified.
- **Files modified:** `src/rag/retrieval/graph.py`, `src/rag/graph/retrieval/graph_retrieval_node.py`.
- **Verification:** Live E2E slice shows `state["function_type"]` correctly reaching the boosted Cypher query (boosted result at `score=1.5` vs. unboosted ties at `1.0`); full `pytest ../tests/rag -m "not integration"` suite (155 passed) shows no regressions in existing routing/graph tests.
- **Committed in:** `83d8c4e` (Task 2 commit).

---

**Total deviations:** 1 auto-fixed (1 missing-critical-functionality fix, structurally required for the plan's own stated purpose).
**Impact on plan:** Positive — without this fix, the function-type classification would have been unreachable dead code and the D-12 ranking lever would not actually apply. No unrelated scope creep: both added files are direct, minimal, mode-gated additions to the exact call path the plan specifies.

## Issues Encountered

- **`poetry install` had not been run in this fresh worktree** — `neo4j-graphrag`, `neo4j`, `langgraph`, etc. were missing on first attempt. Ran `poetry install --no-interaction` (zero `pyproject.toml`/`poetry.lock` diff, confirmed via `git status`) before proceeding. Same class of friction noted in 10-05/10-07's summaries.
- **`src/config/.env.local` (gitignored Neo4j/OpenRouter credentials) was not present** in this fresh worktree checkout — copied (not committed, still gitignored, confirmed via `git status --short`) from the main repo checkout, same as prior Phase 10 plans.
- **The CLI's `ccop-eval graph build-ontology --sample --link` command is too slow for a verification E2E slice** — `--sample` still Docling-parses ALL 7 real CCoP source PDFs before selecting the first document to build on, and the resulting document is a full ~90-page regulatory text (not a small sample), so extraction+gleaning over it did not complete within a reasonable verification window. Killed the process (confirmed zero partial writes — only the pre-existing 883 seeded `:Clause` nodes remained, no orphaned `:Chunk`/`:Entity` nodes) and instead used a tiny synthetic-text E2E slice mirroring plan 10-07's own E2E test pattern (`OntologyKGBuilder.build()` with a two-clause synthetic string), which completed in well under a minute and exercised the identical seed→build→link→retrieve→classify chain. Not logged as a code-level deferred item (no source change needed) — flagged here for future plans that might reach for `--sample` as a "smallest slice" and hit the same wall.
- Confirmed pre-existing `tests/rag/test_container_vector_store.py` / `tests/rag/test_port_adapters.py` mlflow `ImportError` collection failures (same as 10-05/10-07) — excluded via `--ignore` from this plan's verification runs; unrelated to this plan's files.

## Known Stubs

None — the adapter and routing node are both fully wired to real Neo4j/OpenRouter calls, proven via the live E2E slice, not stubbed or mocked in the shipped code path.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes. The classification LLM call reuses the existing `openrouter_api_key`/`openrouter_base_url` settings (same env-sourced discipline as HyDE, T-10-09-02 mitigation); the RETRIEVAL_QUERY remains a static class-level string with all user/classifier-controlled values passed as bound Cypher parameters (T-10-09-01 mitigation), and classifier output is validated against the locked 3-value enum before ever reaching `$function_type`.

## User Setup Required

None — no external service configuration required beyond the already-running local Neo4j Docker service (`docker compose up -d neo4j`) and the existing `CCOP_OPENROUTER_API_KEY` (both already configured for this worktree via the copied `.env.local`).

## Next Phase Readiness

- The ontology adapter and function-type routing node are ready for 10-10 (the deterministic clause-hit@3 harness, D-15) to evaluate against — the boost mechanism and tie-break are both proven live, not just unit-tested.
- The live-built synthetic E2E graph nodes (`:Chunk`, `:__Entity__`, `:Document`) were cleaned up by the E2E script's own `finally` block; the Neo4j graph currently holds exactly the 883 seeded `:Clause` nodes (verified via direct Cypher count) — the next consumer (10-10/10-11) should run `ccop-eval graph build-ontology` (full corpus, no `--sample`) before any evaluation that needs the real corpus KG, same as 10-07's guidance.
- **Carry-forward for a future plan:** Phase 9's `Neo4jGraphRetrievalAdapter` still has the unescaped-Lucene-text bug (only the ontology adapter was fixed here, per D-16 additivity — Phase 9's adapter is untouched); the CLI's `--sample` flag is a real-full-document sample, not a small one, which is worth flagging in a future plan/docs pass so it is not assumed to be a fast smoke-test path.

---
*Phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2*
*Completed: 2026-07-03*

## Self-Check: PASSED

- FOUND: src/rag/graph/retrieval/neo4j_ontology_graph_retrieval_adapter.py
- FOUND: src/rag/retrieval/nodes/function_type_routing.py
- FOUND: tests/rag/graph/retrieval/test_ontology_graph_retrieval_adapter.py
- FOUND: tests/rag/retrieval/nodes/test_function_type_routing.py
- FOUND: src/rag/retrieval/graph.py (modified)
- FOUND: src/rag/graph/retrieval/graph_retrieval_node.py (modified)
- FOUND: src/rag/retrieval/edges/routing.py (modified)
- FOUND: .planning/phases/10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2-/deferred-items.md (updated)
- FOUND commit: 62ecb43 (Task 1: adapter + boost + tie-break + Lucene escaping)
- FOUND commit: 83d8c4e (Task 2: function_type_routing node + graph wiring)
- FOUND commit: 2b75a14 (docs: deferred-items update)
