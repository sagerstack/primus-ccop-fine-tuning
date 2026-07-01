---
phase: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package
plan: 02
subsystem: graphrag
tags: [neo4j, neo4j-graphrag, graphrag, simplekgpipeline, gpt-4o-mini, bge-large-en-v1.5, typer]

# Dependency graph
requires:
  - phase: 09-01
    provides: "Neo4j Docker service, neo4j-graphrag/neo4j deps, Pydantic settings (neo4j_*, graph_extraction_model, graph_embedding_model/dimensions, graph_vector_index_name)"
provides:
  - "EmergentKGBuilder — SimpleKGPipeline wrapper with NO schema constraint, gpt-4o-mini extraction, bge-large-en-v1.5 embeddings, 1024-dim cosine vector index"
  - "load_ccop_corpus_texts — Docling corpus loader reused from rag/ingestion, no clause pre-chunking"
  - "ccop-eval graph build CLI command (--drop/--no-drop) as a first-class, repeatable KG-build command (D-17)"
  - "Live-Neo4j validated: tiny 2-doc synthetic KG build (1 integration test, passed)"
affects: [09-03-graph-retrieval-provider, 09-04-graph-cli-inspect, 10-ontology-grounded-kg]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Injectable factory functions (llm_factory/embedder_factory/pipeline_factory) around SimpleKGPipeline construction — enables fully-mocked unit tests and preserves the D-16 Phase-10 additivity seam in one class"
    - "Authoritative graph stats via direct Cypher count queries after pipeline.run_async, rather than trusting PipelineResult internals (not stable across neo4j-graphrag versions)"

key-files:
  created:
    - src/rag/graph/__init__.py
    - src/rag/graph/build/__init__.py
    - src/rag/graph/build/corpus_source.py
    - src/rag/graph/build/kg_builder.py
    - src/rag/graph/cli/__init__.py
    - src/rag/graph/cli/graph.py
    - tests/rag/graph/__init__.py
    - tests/rag/graph/test_corpus_source.py
    - tests/rag/graph/test_kg_builder.py
    - tests/rag/graph/build/__init__.py
    - tests/rag/graph/build/test_kg_builder_integration.py
  modified:
    - src/presentation/cli/main.py
    - .gitignore

key-decisions:
  - "Unignored src/rag/graph/build/ and tests/rag/graph/build/ in .gitignore — the top-level `build/` rule (packaging artifacts) was silently shadowing this plan-mandated directory name; added scoped negation patterns rather than renaming the directory"
  - "load_ccop_corpus_texts(settings, ccop_dir=...) takes an explicit ccop_dir parameter (default \"../ccop-official\", mirroring run_ingestion.py's --ccop-dir convention) since no Settings field for the CCoP directory exists yet; settings param kept for interface symmetry with the plan's specified signature"
  - "Graph stats (nodes/relationships/chunks) are read via direct Cypher queries after each build, not from SimpleKGPipeline's PipelineResult — the pipeline's internal stats schema is not a stable public contract across neo4j-graphrag versions"
  - "Vector index creation swallows only 'already exists' errors; any other failure (e.g. connection refused) propagates — idempotency should never mask real misconfiguration"

patterns-established:
  - "D-16 interception seam: all neo4j-graphrag construction (LLM, embedder, pipeline) lives inside EmergentKGBuilder behind injectable factories, so Phase 10 can add a schema by swapping one factory rather than rewriting the build pipeline"

requirements-completed: [D-03, D-04, D-05, D-06a, D-07, D-08, D-17]

# Metrics
duration: ~25min
completed: 2026-07-01
---

# Phase 9 Plan 02: Emergent GraphRAG Build Summary

**`ccop-eval graph build` constructs an un-governed Neo4j knowledge graph from the same Docling CCoP markdown the hybrid stack indexes, using gpt-4o-mini (OpenRouter) extraction and bge-large-en-v1.5 (in-process) embeddings — validated end-to-end against live Neo4j with a tiny synthetic KG (1 integration test, passed); the full 7-doc corpus build was NOT run.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-07-01T13:05Z (approx, after context load)
- **Completed:** 2026-07-01T13:30Z
- **Tasks:** 3/3
- **Files modified:** 11 created, 2 modified

## Accomplishments
- `load_ccop_corpus_texts` reuses `parse_all_ccop_documents_with_docling` unmodified, returning full per-document markdown (no clause chunking) — the D-04 constant-input contract with the hybrid Qdrant stack.
- `EmergentKGBuilder` wraps `SimpleKGPipeline` with zero schema/entities/relations kwargs (verified by grep and by test assertions on the mocked pipeline call), gpt-4o-mini extraction via OpenRouter, bge-large-en-v1.5 embeddings, and a 1024-dim cosine vector index (idempotent creation).
- `ccop-eval graph build` is registered as a first-class Typer subcommand (D-17) with a `--drop/--no-drop` clean-rebuild flag, defaulting to the safe non-destructive path.
- Validated the whole pipeline against **live Neo4j** with a real `SimpleKGPipeline` run over two short synthetic documents — nodes and relationships were written (integration test passed in ~43s). The full 7-document corpus build was deliberately **not** run (cost control).
- Fixed a repo-wide `.gitignore` defect: the top-level `build/` rule was silently shadowing the plan-mandated `rag/graph/build/` and `tests/rag/graph/build/` directories.

## Task Commits

1. **Task 1: Corpus source loader** — `c0e61d8` (feat) — TDD: RED confirmed (ModuleNotFoundError) → GREEN (4/4 tests passing)
2. **Task 2: EmergentKGBuilder** — `6ccc71c` (feat) — TDD: RED confirmed (ModuleNotFoundError) → GREEN (12/12 unit tests passing) + live-Neo4j integration test run manually (1 passed)
3. **Task 3: `ccop-eval graph build` CLI command** — `7322372` (feat)

_TDD note: Tasks 1 and 2 followed RED → GREEN (no separate REFACTOR commit needed — implementations were correct on first pass after RED confirmation)._

## Files Created/Modified
- `src/rag/graph/build/corpus_source.py` — `load_ccop_corpus_texts(settings, ccop_dir=...)`, reuses Docling parser, no clause chunking (D-04/D-05)
- `src/rag/graph/build/kg_builder.py` — `EmergentKGBuilder` + `BuildStats`; SimpleKGPipeline (no schema), gpt-4o-mini LLM, bge embedder, 1024-dim cosine vector index, injectable factories
- `src/rag/graph/cli/graph.py` — `graph_app` Typer namespace, `build` command with `--drop/--no-drop`, Rich summary table
- `src/presentation/cli/main.py` — registered `graph_app` under the `graph` subcommand namespace
- `.gitignore` — unignored `src/rag/graph/build/` and `tests/rag/graph/build/` (scoped negation of the top-level `build/` rule)
- `tests/rag/graph/test_corpus_source.py` — 4 unit tests (mocked Docling parser)
- `tests/rag/graph/test_kg_builder.py` — 12 unit tests (mocked neo4j-graphrag classes: construction wiring, no-schema assertion, build/failure aggregation)
- `tests/rag/graph/build/test_kg_builder_integration.py` — 1 `@pytest.mark.integration` test, live Neo4j + real SimpleKGPipeline, 2 synthetic docs

## Decisions Made
- **`.gitignore` negation over directory rename:** the plan's `files_modified` list mandates `src/rag/graph/build/...` exactly; renaming to dodge the `build/` gitignore rule would have deviated from the reviewed plan. Added scoped `!src/rag/graph/build/**` / `!tests/rag/graph/build/**` negations instead (Rule 3 — blocking issue, auto-fixed).
- **`ccop_dir` as an explicit parameter, not a new Settings field:** no `Settings.ccop_dir` exists yet; `run_ingestion.py` and `build_clause_inventory.py` both take it as a CLI/function argument with the same `"../ccop-official"` default. Followed that existing convention rather than adding a new settings field out of plan scope.
- **Graph stats via direct Cypher, not PipelineResult:** neo4j-graphrag's `PipelineResult.result` shape is an internal, version-sensitive structure; querying `MATCH (n)`, `MATCH ()-[r]->()`, `MATCH (c:Chunk)` counts directly is simpler and more stable for `BuildStats`.
- **Modernized new-file typing to PEP 585 generics** (`dict[str, str]`, `list[str]`, `collections.abc.Callable`) rather than `typing.Dict/List/Callable` — ruff's `UP035/UP006` flagged the older style; existing codebase files (e.g. `docling_parser.py`, `run_ingestion.py`) still use the deprecated forms as pre-existing debt, left untouched (out of scope for this plan).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `.gitignore`'s `build/` rule silently shadowed the plan-mandated directory name**
- **Found during:** Task 1 (`git add` on newly created `src/rag/graph/build/` and `tests/rag/graph/build/` files)
- **Issue:** `git add` reported the new files as ignored — the repo's top-level `.gitignore` line 7 (`build/`, a standard Python packaging-artifact rule) matches any directory literally named `build` at any depth, silently swallowing the plan's `rag/graph/build/` package.
- **Fix:** Appended scoped negation patterns to `.gitignore` (`!src/rag/graph/build/`, `!src/rag/graph/build/**`, and the `tests/` equivalents) so only this specific source/test package is exempted; the packaging-artifact rule still applies everywhere else.
- **Files modified:** `.gitignore`
- **Verification:** `git check-ignore -v` returns the negation rule (not the original ignore) for files under both directories; `git status --short` shows them as trackable/added.
- **Committed in:** `c0e61d8` (Task 1 commit)

No other deviations. CLAUDE.md conventions (Poetry-only commands, no bare `python`, Clean Architecture layering) were followed throughout; no conflicts with existing ADRs in `docs/project_notes/decisions.md`.

## Issues Encountered

**Pre-existing test failures (out of scope, NOT fixed):** `poetry run pytest -m "not integration"` surfaces the same 9 pre-existing failures in `tests/domain/services/test_llm_judge_service.py` documented in `09-01-SUMMARY.md` (rubric-dict vs `benchmark_id: str` signature drift from an earlier OpenRouter migration commit, predating this plan). Confirmed identical failure count and file — no new failures introduced by this plan's changes (52 passed, 9 pre-existing failures, 5 deselected integration tests).

**neo4j-graphrag deprecation warning (informational only):** `SimpleKGPipeline(from_pdf=False)` emits `DeprecationWarning: from_pdf is deprecated ... use from_file instead`. The installed `neo4j-graphrag==1.18.0` API still accepts and honors `from_pdf`; `from_file` is a separate, newer parameter defaulting to `True` (would attempt to load `text` as a file path if left at its default alongside `from_pdf`). Left as specified in the plan interface (`from_pdf=False`) since changing to `from_file` semantics is an API-behavior change outside this plan's scope — flagged here for Phase 10 or a future minor-version bump to revisit.

## User Setup Required

None — Neo4j and OpenRouter were already live per the environment context provided for this plan.

**Operational note for the coordinator:** the live-Neo4j integration test (run once during execution to validate the pipeline, per the cost-control directive) wrote a tiny 2-node-ish synthetic KG (`synthetic-doc-1`/`synthetic-doc-2`, "Acme Corp"/"Jane Tan"/"Power Grid Control Platform" entities) into the current Neo4j database. **Before running the real full-corpus build, run it with `--drop`** so the synthetic test data doesn't pollute the CCoP graph:

```bash
cd src && poetry run ccop-eval graph build --drop
```

## Full-Corpus Build — NOT Run (Cost Control)

Per the coordinator's cost-control directive, the full 7-document CCoP corpus build was **not** executed during this plan. Exact command for the coordinator to run deliberately before Wave 3:

```bash
cd src && poetry run ccop-eval graph build --drop
```

(`--drop` recommended to clear the synthetic integration-test data first; omit if a from-scratch/no-drop rebuild is preferred and the graph is manually cleared another way.)

**Corpus scope measured directly (Docling parse, no LLM calls — safe to run for sizing):**

| Document | Docling markdown chars |
|---|---|
| CCoP 2.0 | 151,269 |
| CCoP Response to Feedback | 106,164 |
| Auditing Guidelines | 33,379 |
| Threat Modelling Guide | 64,819 |
| Risk Assessment Guide | 54,005 |
| Security By Design | 128,762 |
| Cybersecurity Act 2018 | 127,793 |
| **Total** | **666,191 chars** |

- neo4j-graphrag's default `FixedSizeSplitter` uses `chunk_size=4000`, `chunk_overlap=200` chars (D-08 pure defaults, not overridden).
- **Estimated chunks: ~175** (666,191 / ~3,800 effective chars/chunk after overlap).
- **Estimated gpt-4o-mini extraction calls: ~175** (SimpleKGPipeline issues roughly one extraction call per chunk; entity-resolution may add a modest number of additional calls on top, not separately estimated here).
- At gpt-4o-mini OpenRouter pricing this is a small, bounded cost (low single-digit dollars), consistent with T-09-06's "accept" disposition (local, one-off build over a fixed 7-doc corpus).

## Next Phase Readiness
- Emergent KG build pipeline is implemented, unit-tested, and live-validated end-to-end (tiny synthetic KG). Ready for the coordinator to trigger the real full-corpus build (`ccop-eval graph build --drop`) before Plan 03 (graph retrieval provider) needs a populated graph to retrieve against.
- D-16 additivity seam confirmed: all model/pipeline construction is behind `EmergentKGBuilder`'s injectable factories — Phase 10 can add ontology-schema constraints by swapping the pipeline factory without touching corpus loading or the CLI.
- **Blocker for Plan 03:** the graph currently contains only the tiny synthetic integration-test KG, not real CCoP content — the full-corpus build must run first.

## Self-Check: PASSED

All created files verified on disk (`src/rag/graph/build/corpus_source.py`, `src/rag/graph/build/kg_builder.py`, `src/rag/graph/cli/graph.py`, all test files). All three task commits (`c0e61d8`, `6ccc71c`, `7322372`) present in `git log`. `ccop-eval graph build --help` and `ccop-eval --help` both verified working. Live-Neo4j integration test passed (1 passed, 42.95s).

---
*Phase: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package*
*Completed: 2026-07-01*
