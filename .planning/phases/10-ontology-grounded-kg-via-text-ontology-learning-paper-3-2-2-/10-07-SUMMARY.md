---
phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2
plan: 07
subsystem: graphrag-ontology
tags: [neo4j, neo4j-graphrag, schema-constrained-extraction, gleaning, entity-resolution, clause-linking, cypher, typer-cli]

# Dependency graph
requires:
  - phase: 10-04
    provides: locked ontology_config.json (24 node types, 48 relationship types, additional_node_types=false)
  - phase: 10-05
    provides: ClauseSeeder / `graph seed-clauses` CLI (the seeded :Clause backbone to link to)
  - phase: 10-06
    provides: SectionAlignedSplitter (text_splitter=) and GleaningEntityRelationExtractor (extraction override point)
provides:
  - "OntologyKGBuilder: schema-constrained (locked ontology), gleaning-enabled, section-aligned, deduped KG builder"
  - "ClauseLinker: deterministic (no-LLM) entity/chunk -> :Clause LINKED_TO post-extraction pass"
  - "ccop-eval graph build-ontology CLI subcommand (build + link chain, --permissive/--sample/--link flags)"
affects: [10-08-shacl-validation, 10-09-clause-anchored-retrieval, 10-10/10-11-graphrag-ontology-mode-eval]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SimpleKGPipelineConfig subclass overriding ONLY _get_extractor() -- the library's documented per-component extension point (TemplatePipelineConfig._get_component dynamic dispatch) -- to inject a custom extractor without hand-building a Pipeline graph from scratch"
    - "Injectable runner_factory seam (mirrors kg_builder.py's PipelineFactory) so unit tests assert on schema/prompt/splitter/gleaning arguments without constructing a real PipelineRunner (which eagerly queries the live driver for server version at construction time)"
    - "Post-hoc deterministic entity/chunk->clause linking via reused boundary-aware text match (KGInspector._clause_id_appears), not extraction-time LLM-emitted clause_id strings"

key-files:
  created:
    - "src/rag/graph/build/ontology_kg_builder.py"
    - "src/rag/graph/ontology/clause_linker.py"
    - "tests/rag/graph/build/test_ontology_kg_builder.py"
    - "tests/rag/graph/ontology/test_clause_linker.py"
  modified:
    - "src/rag/graph/cli/graph.py"

decisions:
  - "SimpleKGPipeline has NO extractor= override kwarg (confirmed live), but the underlying SimpleKGPipelineConfig resolves each pipeline component via _get_<name>() methods, dynamically dispatched by TemplatePipelineConfig._get_component -- subclassing and overriding only _get_extractor() reuses the library's own proven loader->splitter->schema->extractor->pruner->writer->resolver wiring instead of hand-reproducing it. Verified live that the subclass identity survives PipelineRunner.from_config()'s pydantic discriminated-union validation. This supersedes 10-RESEARCH.md Q2/A5's hand-built-Pipeline assumption per A5's own verify-at-implementation-time instruction."
  - "SinglePropertyExactMatchResolver dedup (D-07) needs NO override -- it is already SimpleKGPipelineConfig's default resolver when perform_entity_resolution=True, with its own default resolve_property='name' matching the locked ontology's canonical-name convention exactly."
  - "Entity->clause linking is post-hoc and deterministic (RESEARCH.md Q4's recommended strategy), not extraction-time: entities inherit their extraction chunk's clause links via the neo4j-graphrag lexical-graph :FROM_CHUNK edge, rather than asking the LLM to emit a clause_id string (hallucination risk)."

requirements-completed: [RAG-02, RAG-06, D-06, D-07, D-11]

# Metrics
duration: ~100min (incl. fresh-worktree poetry install ~7min, live neo4j-graphrag source verification, one real E2E OpenRouter call)
completed: 2026-07-03
---

# Phase 10 Plan 07: Schema-Constrained OntologyKGBuilder + Clause Linking Summary

**`OntologyKGBuilder` (locked 24-node/48-relation ontology + canonical-name/ignore-illustrative prompt + section-aligned gleaning extraction + exact-match resolver) and `ClauseLinker` (deterministic entity/chunk -> seeded :Clause `LINKED_TO` anchoring), wired into a new `ccop-eval graph build-ontology` CLI command and proven end-to-end against live Neo4j with one real gpt-4o-mini extraction call.**

## Performance

- **Duration:** ~100 min (includes a fresh-worktree `poetry install`, live introspection of the installed `neo4j-graphrag==1.18.0` source to verify the extractor-injection mechanism, and one real E2E OpenRouter call)
- **Completed:** 2026-07-03
- **Tasks:** 2 completed (both TDD: RED + GREEN, plus a CLI-wiring commit for Task 2's `build-ontology` subcommand)
- **Files modified:** 5 (2 new source modules, 2 new test files, 1 modified CLI file)

## Accomplishments

- `OntologyKGBuilder` loads the LOCKED `ontology_config.json` (24 node types, 48 relationship types, 9 patterns) into the `schema=` shape `GraphSchema` expects, with `additional_node_types=False`/`additional_relationship_types=False` in strict mode and a `--permissive` escape hatch (RESEARCH.md Pitfall 1) that flips both to `True` for iteration.
- A custom extraction prompt (`ONTOLOGY_EXTRACTION_PROMPT`) instructs the extraction LLM to ignore illustrative/example passages and placeholder names ("John Doe", "Company X", "N.A.") and to always assign a canonical `name` property using the exact source term (D-07) — the structural fix for the Phase 9 D-06 anti-patterns.
- The 10-06 `SectionAlignedSplitter` (`text_splitter=`) and `GleaningEntityRelationExtractor` (multi-pass recall recovery) are injected via `_OntologyKGPipelineConfig`, a one-method `SimpleKGPipelineConfig` subclass overriding only `_get_extractor()` — the library's own documented per-component extension point, verified live against the installed package source rather than assumed.
- `SinglePropertyExactMatchResolver` dedup (D-07) runs automatically — it is `SimpleKGPipelineConfig`'s own default resolver (`resolve_property="name"`) whenever entity resolution is enabled, requiring no override.
- `ClauseLinker` deterministically matches every extracted `:Chunk`'s text against every seeded `:Clause`'s `clause_id` (reusing `KGInspector._clause_id_appears`'s boundary-aware match, no reimplementation), `MERGE`s `:Chunk-[:LINKED_TO]->:Clause` edges, then propagates the same links to entities via the neo4j-graphrag lexical-graph `:FROM_CHUNK` edge — anchoring extracted entities to the D-10 seeded clause backbone with zero LLM calls.
- `ccop-eval graph build-ontology` CLI subcommand mirrors the existing `graph build` shape, chaining `OntologyKGBuilder.build()` -> `ClauseLinker.link()`, with `--permissive`/`--strict`, `--sample`/`--full`, `--link`/`--no-link`, and `--drop` flags.
- **Real smallest-slice E2E**, run live against local Neo4j + real OpenRouter: `seed-clauses` -> `OntologyKGBuilder.build()` (one real gpt-4o-mini extraction call, one synthetic clause-5.3.1 document) -> `ClauseLinker.link()` produced ≥1 `LINKED_TO` edge, and every extracted entity carried a canonical, non-junk `name` — proving the full wiring, not just mocked units (per `~/.claude/rules/e2e-testing.md`).

## Task Commits

Each task was committed atomically (TDD RED/GREEN for both tasks):

1. **Task 1 RED: failing test for OntologyKGBuilder** — `3b16db8` (test)
2. **Task 1 GREEN: implement OntologyKGBuilder** — `7494c7a` (feat)
3. **Task 2 RED: failing test for clause linker** — `78e3ec4` (test)
4. **Task 2 GREEN: implement ClauseLinker** — `4f1a1ca` (feat)
5. **Task 2: `graph build-ontology` CLI subcommand** — `b4ceef9` (feat)

_TDD gate sequence verified for both tasks: `test(10-07): ...` commit precedes `feat(10-07): implement ...` commit in git log — RED then GREEN, no REFACTOR commit needed (implementation was clean on first pass after live-source verification)._

## Files Created/Modified

- `src/rag/graph/build/ontology_kg_builder.py` — `OntologyKGBuilder`, `BuildStats`, `_OntologyKGPipelineConfig` (the `_get_extractor()` override subclass), `load_locked_schema()`, `ONTOLOGY_EXTRACTION_PROMPT`.
- `src/rag/graph/ontology/clause_linker.py` — `ClauseLinker`, `LinkStats`, static parameterized Cypher for chunk/entity linking.
- `src/rag/graph/cli/graph.py` — added `build_ontology_command` (`ccop-eval graph build-ontology`) + `_print_ontology_build_summary`/`_print_link_summary` helpers.
- `tests/rag/graph/build/test_ontology_kg_builder.py` — 20 unit tests (locked-schema loading, permissive toggle, prompt content, splitter/gleaning/resolver wiring via the real `_OntologyKGPipelineConfig`, provenance-preserving build loop, vector-index idempotency).
- `tests/rag/graph/ontology/test_clause_linker.py` — 6 unit tests (pure boundary-aware match), 3 live-Neo4j integration tests (chunk/entity linking, idempotent re-link), 1 live E2E slice test (real seed -> build -> link chain).

## Decisions Made

- **Extractor injection via `SimpleKGPipelineConfig` subclass, not a hand-built `Pipeline`:** 10-RESEARCH.md Q2/A5 assumed a fully hand-built `Pipeline` (`loader -> splitter -> schema -> extractor -> resolver -> writer`) would be required since `SimpleKGPipeline` has no `extractor=` kwarg (confirmed true). Live introspection of the installed `neo4j-graphrag==1.18.0` source found that `SimpleKGPipelineConfig` (a `TemplatePipelineConfig`) resolves every component through `_get_<name>()` methods, dynamically dispatched — the library's own documented extension point for this exact need. Subclassing and overriding only `_get_extractor()` reuses the library's proven wiring rather than risking an incorrectly hand-reproduced pipeline graph. Verified live: the subclass identity and its override both survive `PipelineRunner.from_config()`'s pydantic discriminated-union validation (`isinstance(parsed_config, MySubclass)` holds after `.model_validate()`).
- **`runner_factory` injection seam:** `PipelineRunner.from_config()` eagerly constructs a `Neo4jWriter`, which queries the live driver for its server version at CONSTRUCTION time (not at `.run()` time) — a bare `MagicMock()` driver cannot satisfy this. `OntologyKGBuilder` therefore takes an injectable `runner_factory` callable (mirrors `kg_builder.py`'s `PipelineFactory` pattern) so unit tests assert on the schema/prompt/splitter/gleaning arguments without constructing a real `PipelineRunner`. A separate, targeted test class (`TestOntologyKGPipelineConfigExtractor`) exercises the REAL `_OntologyKGPipelineConfig._get_extractor()`/`_get_resolver()` directly using `MagicMock(spec=...)` driver/llm/embedder objects (which satisfy neo4j-graphrag's pydantic `isinstance` validation with zero network access) — proving the gleaning extractor and exact-match resolver are actually wired, not just passed as opaque arguments.
- **Post-hoc, not extraction-time, clause linking:** followed RESEARCH.md Q4's explicit recommendation — asking the extraction LLM to emit `(entity)-[:GOVERNED_BY]->(Clause {clause_id:"5.3.1"})` directly risks the LLM hallucinating clause_id strings. `ClauseLinker` instead runs a deterministic post-build pass reusing the SAME boundary-aware `KGInspector._clause_id_appears` match already proven for D-18 clause coverage.
- **Entities inherit clause links from their chunk, not independently text-matched:** extracted `:__Entity__` nodes do not themselves carry the source prose (only their originating `:Chunk` does), so `ClauseLinker` matches at the `:Chunk` level and propagates `LINKED_TO` to entities via the neo4j-graphrag lexical-graph `:FROM_CHUNK` edge — one deterministic match pass, two edge types.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected a stale assumption from 10-RESEARCH.md/10-06-SUMMARY: no hand-built Pipeline needed**
- **Found during:** Task 1, live source verification per the plan's `<read_first>` instruction to "verify the live SimpleKGPipeline/Pipeline signatures at build time before wiring."
- **Issue:** Both 10-RESEARCH.md (Q2, flagged assumption A5) and 10-06-SUMMARY's "Notes for 10-07" stated the gleaning extractor "requires a hand-built Pipeline" since `SimpleKGPipeline` hardcodes its own extractor with no `extractor=` kwarg. This is true for the public `SimpleKGPipeline` class, but live introspection of the installed `neo4j-graphrag==1.18.0` source found the underlying `SimpleKGPipelineConfig` exposes a documented, purpose-built per-component override mechanism (`_get_<component_name>()`, dynamically dispatched by `TemplatePipelineConfig._get_component`) that achieves the identical integration goal with far less risk (reusing the library's own proven component-graph wiring instead of hand-reproducing `loader->splitter->schema->extractor->pruner->writer->resolver` connections and their `ConnectionDefinition` input-mapping from scratch).
- **Fix:** Implemented `_OntologyKGPipelineConfig(SimpleKGPipelineConfig)` overriding only `_get_extractor()`; verified live (before writing any test) that (a) the subclass instance and its override survive `PipelineRunner.from_config()`'s pydantic discriminated-union validation, (b) `SinglePropertyExactMatchResolver`'s default `resolve_property="name"` already satisfies D-07 with zero extra code, (c) the full 24-node/48-relation locked schema validates cleanly through `GraphSchema.model_validate()` with extra JSON keys (`example_terms`, `provenance`, `flagged_ambiguities`) silently ignored.
- **Files modified:** `src/rag/graph/build/ontology_kg_builder.py` (documented at length in the module docstring, per A5's own "verify constructor signature at implementation time" instruction).
- **Verification:** `TestOntologyKGPipelineConfigExtractor` exercises the real subclass end-to-end (no mocks beyond `MagicMock(spec=...)` for network-touching objects); all 20 unit tests + all 4 live-Neo4j integration tests + the 1 real E2E slice test pass.
- **Committed in:** `7494c7a` (Task 1 GREEN commit).

---

**Total deviations:** 1 auto-fixed (1 bug — corrected a research-stage assumption via live verification, resulting in a simpler and more robust integration than originally planned).
**Impact on plan:** Positive — the actual implementation is LESS code and LOWER risk than the plan anticipated (a one-method subclass override vs. a full hand-built pipeline graph), while satisfying every plan acceptance criterion (locked schema, canonical-name/ignore-illustrative prompt, section splitter + gleaning + resolver all wired, provenance preserved, `--permissive` escape hatch). No scope creep.

## Issues Encountered

- **Fresh worktree missing `poetry install` and gitignored `.env.local`** — same class of friction noted in 10-05's SUMMARY. Ran `poetry install --no-interaction` (zero `pyproject.toml`/`poetry.lock` diff) and copied `src/config/.env.local` from the main repo checkout (still gitignored, confirmed via `git status --short`, never committed) so live-Neo4j integration tests and the real E2E slice could run.
- **`PytestUnknownMarkWarning` for `@pytest.mark.integration`** — observed when running the new test files directly; confirmed this is PRE-EXISTING behavior (reproduced identically against `test_clause_seeding.py`, an already-committed file from 10-05) and not something introduced by this plan's changes. Cosmetic only (does not fail tests, marker still filters correctly via `-m integration`/`-m "not integration"`). Out of scope per the scope-boundary rule — not logged to `deferred-items.md` since it is a pytest-config-level warning already present across the whole `tests/rag/graph/` tree, not a new discovery.

## User Setup Required

None — no external service configuration required beyond the already-running local Neo4j Docker service (`docker compose up -d neo4j`) and the existing `CCOP_OPENROUTER_API_KEY` (both already configured for this worktree via the copied `.env.local`).

## Next Phase Readiness

- `OntologyKGBuilder` and `ClauseLinker` are ready for 10-08 (SHACL validation — validates the graph THIS plan's builder produces) and 10-09 (clause-anchored retrieval — consumes the `:Chunk-[:LINKED_TO]->:Clause` and `:Entity-[:LINKED_TO]->:Clause` edges THIS plan creates as the retrieval-routing signal).
- `ccop-eval graph build-ontology` is a first-class, re-runnable operator command (mirrors `graph build`/`graph seed-clauses`) — `seed-clauses -> build-ontology` is the full governed-KG construction chain, no manual Cypher needed.
- The live-seeded/built/linked graph from the E2E slice test was cleaned up by the test's own teardown (`MATCH (n) DETACH DELETE n` in the `finally` block) — confirmed via a direct post-test node-count query (0 nodes). The next consumer (10-08/10-09) or the user should run `ccop-eval graph seed-clauses` then `ccop-eval graph build-ontology` (full corpus, no `--sample`) to (re)establish real deliverable state before building on top of it.
- No blockers.

---
*Phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2-*
*Completed: 2026-07-03*

## Self-Check: PASSED

- FOUND: src/rag/graph/build/ontology_kg_builder.py
- FOUND: src/rag/graph/ontology/clause_linker.py
- FOUND: tests/rag/graph/build/test_ontology_kg_builder.py
- FOUND: tests/rag/graph/ontology/test_clause_linker.py
- FOUND: src/rag/graph/cli/graph.py (modified, `build-ontology` subcommand present)
- FOUND commit: 3b16db8 (test RED, Task 1)
- FOUND commit: 7494c7a (feat GREEN, Task 1)
- FOUND commit: 78e3ec4 (test RED, Task 2)
- FOUND commit: 4f1a1ca (feat GREEN, Task 2)
- FOUND commit: b4ceef9 (feat, CLI subcommand)
