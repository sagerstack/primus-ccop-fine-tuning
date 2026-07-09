---
phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2-
plan: 05
subsystem: graphrag-ontology
tags: [neo4j, cypher, clause-seeding, deterministic, typer-cli, ontology]

# Dependency graph
requires:
  - phase: 10-04
    provides: locked ontology_config.json (24 node types, 48 relations, function_type_tags)
  - phase: 03.2
    provides: clause_inventory.json fixture (deterministic clause-ID source, no LLM)
provides:
  - "ClauseSeeder: deterministic Cypher MERGE seeder for the :Clause backbone (D-10)"
  - "ccop-eval graph seed-clauses CLI subcommand"
  - "883 :Clause nodes with :HAS_CHILD hierarchy edges + function_type tags (D-09), idempotently re-seedable"
affects: [10-07-entity-clause-linking, 10-09-clause-anchored-retrieval]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Composite (clause_id, source_doc) MERGE key for globally-unique clause identity across 7 source docs"
    - "Static CCoP-2.0-TOC-verified section->function_type lookup table with a single documented ControlClause fallback"

key-files:
  created:
    - src/rag/graph/ontology/clause_seeder.py
    - tests/rag/graph/ontology/test_clause_seeding.py
  modified:
    - src/rag/graph/cli/graph.py

key-decisions:
  - "MERGE key is the composite (clause_id, source_doc), not clause_id alone — verified clause_id is NOT globally unique across the 7 source docs (e.g. every doc has its own clause '1')"
  - "Parent-child hierarchy extends clause_aware_chunker's dot-rsplit rule to also strip a trailing '(x)' item-letter suffix, so '10.2.5(a)' parents to '10.2.5' (its enclosing clause), not the naive dot-rsplit's '10.2'"
  - "function_type (D-09) assigned via a static, source-verified CCoP 2.0 TOC lookup (Chapter 1 Preliminary=ScopeClause, Section 1.2 Glossary and Interpretation=DefinitionClause, 10.1/11.1 'Application of this Section'=ScopeClause) with a single documented fallback (ControlClause) for every other clause and all 6 non-CCoP-2.0 source docs — clause_inventory.json has no titles to classify against, and ontology_config.json's function_type_tags list has no clause-level mapping to reuse"
  - "Fixture entry count is 883, not the plan's literal 691 — the Phase 3.2 ground-truth audit correction (commit 9662d1c, after 10-RESEARCH.md/10-PATTERNS.md were authored) regenerated clause_inventory.json with more entries. Seeder and tests assert against the live fixture count (len(entries)), not a hardcoded literal, so the module stays correct as the fixture evolves"

patterns-established:
  - "Deterministic Cypher MERGE seeding from a committed JSON fixture with zero LLM calls in the path — the D-10 anti-hallucination pattern any future seeded-backbone work (e.g. Control/Obligation/Definition seeding) should copy"

requirements-completed: [RAG-01, RAG-02, D-10, D-09]

# Metrics
duration: ~30min
completed: 2026-07-03
---

# Phase 10 Plan 05: Deterministic Clause-Backbone Seeder Summary

**Cypher `MERGE`-based `ClauseSeeder` (no LLM) plus a `ccop-eval graph seed-clauses` CLI command that seeds 883 `:Clause` nodes from `clause_inventory.json` with dot-hierarchy `:HAS_CHILD` parent-child edges and D-09 `function_type` tags, verified idempotent and live-tested against local Neo4j.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-07-03T05:00:00Z (approx, worktree checkout)
- **Completed:** 2026-07-03T05:30:00Z (approx)
- **Tasks:** 2 completed (Task 1 TDD: RED + GREEN; Task 2: CLI subcommand)
- **Files modified:** 3 (1 new source module, 1 new test file, 1 modified CLI file)

## Accomplishments

- `ClauseSeeder` deterministically MERGE-seeds every entry in `clause_inventory.json` as a `:Clause` node keyed on the composite `(clause_id, source_doc)` — verified against the live fixture that this pair is unique across all 883 entries (0 duplicates), unlike `clause_id` alone which repeats across the 7 source documents.
- Parent-child `:HAS_CHILD` hierarchy is derived purely from `clause_id` string structure, reusing `clause_aware_chunker._extract_section`'s dot-splitting rule and extending it to correctly parent item-letter clauses (e.g. `"10.2.5(a)"` → `"10.2.5"`, not the naive dot-rsplit's `"10.2"`).
- Every seeded clause carries a D-09 `function_type` tag (`ScopeClause`/`ControlClause`/`DefinitionClause`) from a static, TOC-verified lookup for CCoP 2.0 (Chapter 1 "Preliminary" = scope, Section 1.2 "Glossary and Interpretation" = definitions) with a single documented fallback (`ControlClause`) for everything else.
- Idempotent composite uniqueness constraint on `(clause_id, source_doc)`, mirroring `kg_builder.py`'s "already exists"-swallow pattern.
- `ccop-eval graph seed-clauses` CLI subcommand mirrors the existing `build`/`inspect`/`stats` Typer shape, printing a node/edge summary and `function_type` distribution table.
- Full E2E verification against a live local Neo4j instance: seeded 883 `:Clause` nodes, 765 `:HAS_CHILD` edges, `function_type` distribution `{ControlClause: 847, DefinitionClause: 7, ScopeClause: 29}`; re-running left the graph unchanged (idempotent), confirmed via both the pytest integration suite and two consecutive live CLI invocations.

## Task Commits

Each task was committed atomically (TDD RED/GREEN for Task 1):

1. **Task 1 RED: failing test for clause seeder** — `9724f8d` (test)
2. **Task 1 GREEN: implement ClauseSeeder** — `de540e4` (feat)
3. **Task 2: `graph seed-clauses` CLI subcommand** — `65bae81` (feat)
4. **Deferred-item log (pre-existing mlflow import error, out of scope)** — `0f63b38` (docs)

_TDD gate sequence verified: `test(10-05): ...` commit precedes `feat(10-05): implement...` commit in git log — RED then GREEN, no REFACTOR commit needed (implementation was clean on first pass)._

## Files Created/Modified

- `src/rag/graph/ontology/clause_seeder.py` — `ClauseSeeder` class, `SeedStats` dataclass, parent/chapter/function_type derivation helpers, module-level docstring documenting the TOC-verified function_type mapping and its fallback.
- `tests/rag/graph/ontology/test_clause_seeding.py` — 8 unit tests (pure derivation helpers, no external deps) + 4 live-Neo4j integration tests (exact count, hierarchy edges, idempotent re-seed, valid function_type on every node).
- `src/rag/graph/cli/graph.py` — added `seed_clauses_command` (`ccop-eval graph seed-clauses`) + `_print_seed_summary` helper.

## Decisions Made

- **Composite MERGE key `(clause_id, source_doc)`:** `clause_id` alone repeats across the 7 source documents (e.g. every doc has its own top-level clause `"1"`); the composite is verified unique across all 883 fixture entries.
- **Item-letter suffix parenting extension:** `clause_aware_chunker._extract_section`'s plain `rsplit(".", 1)` mis-parents synthetic item-letter clause_ids introduced by the Phase 3.2 audit pass (e.g. `"10.2.5(a)".rsplit(".", 1)` → `"10.2"`, skipping the `"10.2.5"` level). Added a `_ITEM_SUFFIX_RE` strip-first step so item clauses parent to their enclosing clause, not their grandparent section.
- **function_type mapping source:** Since `clause_inventory.json` has no titles (by design, D-04) and `ontology_config.json` carries only the three tag *names* (no clause-level mapping), I read the official CCoP 2.0 Table of Contents (`ccop-official/CCoP---Second-Edition_Revision-One.pdf`, pages 2-3 — public, committed, versioned document structure) to build a small, explicit, source-cited section→function_type table for CCoP 2.0 only, with `DEFAULT_FUNCTION_TYPE = "ControlClause"` as the single documented fallback for every clause outside that table (all 6 non-CCoP-2.0 docs, and any CCoP 2.0 clause not in the explicit list). This satisfies the plan's "default to a documented fallback if a clause is unmapped" instruction without guessing at clause content that doesn't exist in the fixture.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixture entry count is 883, not the plan's literal 691 — assert against the live fixture, not a hardcoded number**
- **Found during:** Task 1, while reading `clause_inventory.json` per `<read_first>` before writing the test.
- **Issue:** `10-RESEARCH.md` and `10-PATTERNS.md` (and the plan's `must_haves.truths`/acceptance criteria) state "691 entries" / "Exactly 691 :Clause nodes". The live fixture on this worktree's base commit has 883 entries (738 unique bare `clause_id` values, 883 unique `(clause_id, source_doc)` pairs — no duplicates). `git log --follow` on the fixture shows a later commit, `9662d1c` ("apply audit corrections, regenerate JSONL, finalize Term 2 dissertation"), landed after 10-RESEARCH.md/10-PATTERNS.md were authored and grew the fixture past 691. A test hardcoded to `== 691` would fail against current data through no fault of the seeder.
- **Fix:** `ClauseSeeder.seed()` returns `SeedStats.entries_total` computed from `len(entries)` read live from the fixture at call time; the test suite asserts `count(:Clause) == <live fixture length>` (computed via a `_fixture_entries_count()` helper reading the same JSON file), never a hardcoded literal. The seeder's behavior (MERGE every fixture entry, no LLM, no filtering) is unchanged from the plan's intent — only the *expected number* is now data-driven instead of a stale literal.
- **Files modified:** `src/rag/graph/ontology/clause_seeder.py`, `tests/rag/graph/ontology/test_clause_seeding.py`.
- **Verification:** Live E2E run seeds and reports exactly 883 `:Clause` nodes (matches `len(clause_inventory.json["entries"])`); `poetry run pytest ../tests/rag/graph/ontology/test_clause_seeding.py -m integration -x -q` → 4 passed.
- **Committed in:** `de540e4` (Task 1 GREEN commit), `9724f8d` (Task 1 RED commit — test already written data-driven).

---

**Total deviations:** 1 auto-fixed (1 bug — stale plan literal vs. live data).
**Impact on plan:** Necessary for correctness against the actual committed fixture; the seeder's mechanics (MERGE-only, no LLM, composite key, idempotent) match the plan's intent exactly. No scope creep — the fixture drift was upstream of this plan (a later Phase 3.2 audit-correction commit), not introduced here.

## Issues Encountered

- **`src/config/.env.local` (Neo4j/OpenRouter credentials) was not present in this fresh worktree checkout** — the file is correctly `.gitignore`d and lives only in the main repo checkout. Copied (not committed — still gitignored, confirmed via `git status --short`) from `/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/src/config/.env.local` into the worktree so the live-Neo4j integration tests and CLI E2E run could execute. Same class of "fresh worktree missing gitignored local config" friction as prior Phase 10 plans' `deferred-items.md` entries — not a code change, no action needed beyond noting it here.
- **`poetry install` had not been run in this fresh worktree** — `neo4j` and other dependencies were missing on first attempt. Ran `poetry install --no-interaction` (no `pyproject.toml`/`poetry.lock` changes — confirmed via `git status`/`git diff --stat`, zero diff) before proceeding.
- Discovered (not fixed, out of scope) — two pre-existing test-collection errors (`tests/rag/test_container_vector_store.py`, `tests/rag/test_port_adapters.py`, `ImportError: cannot import name 'Dataset' from 'mlflow.entities'`), unrelated to this plan's files. Logged to `deferred-items.md` under `## 10-05` per the scope-boundary rule (commit `0f63b38`).

## User Setup Required

None — no external service configuration required beyond the already-running local Neo4j Docker service (`docker compose up -d neo4j`), which was already up for this worktree.

## Next Phase Readiness

- The `:Clause` backbone (883 nodes, hierarchy, `function_type` tags) is ready for 10-07 (entity→clause linking) and 10-09 (clause-anchored retrieval) to consume via `clause_id` matching.
- `ccop-eval graph seed-clauses` is a first-class, re-runnable operator command — no manual Cypher needed to (re)establish the backbone before a rebuild.
- No blockers. The live-seeded `:Clause` nodes were cleaned up by the integration test suite's teardown fixture at the end of this plan's verification run (Neo4j graph currently has 0 `:Clause` nodes) — this is expected test hygiene, not a deliverable state; the next consumer (10-06/10-07) or the user should run `ccop-eval graph seed-clauses` again before building on top of it.

---
*Phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2-*
*Completed: 2026-07-03*

## Self-Check: PASSED

- FOUND: src/rag/graph/ontology/clause_seeder.py
- FOUND: tests/rag/graph/ontology/test_clause_seeding.py
- FOUND: .planning/phases/10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2-/10-05-SUMMARY.md
- FOUND commit: 9724f8d (test RED)
- FOUND commit: de540e4 (feat GREEN)
- FOUND commit: 65bae81 (CLI subcommand)
- FOUND commit: 0f63b38 (deferred-items docs)
- FOUND commit: 1321423 (SUMMARY docs)
