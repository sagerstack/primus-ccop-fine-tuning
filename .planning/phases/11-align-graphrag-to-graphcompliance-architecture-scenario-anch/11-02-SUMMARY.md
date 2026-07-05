---
phase: 11-align-graphrag-to-graphcompliance-architecture-scenario-anch
plan: 02
subsystem: graph
tags: [neo4j, qdrant, cypher, clause-alignment, citation-namespacing, graphcompliance]

# Dependency graph
requires:
  - phase: 11-01
    provides: "Re-ingested, clause-complete corpus (883/883 clause ids resolve, 17/17 CCoP TOC sections) verified by verify_clause_completeness.py; the 883-node :Clause backbone fixture (clause_inventory.json)"
provides:
  - "ClauseTextAligner: verbatim provision text attached to every seeded :Clause node (5-tier resolution against the re-ingested Qdrant corpus)"
  - "ClauseSourceAnnotator: source-doc-namespaced citation_id + doc_class (binding/guidance) + is_structural_header flag on every seeded :Clause node"
  - "Source layer ready for 11-04's CU classification/formalization pass (zero :ComplianceUnit nodes minted here, by design)"
affects: [11-04, 11-05, 11-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "5-tier text resolution: exact clause metadata match -> item-letter decomposition -> section-N body-start match -> heading-token match -> generic boundary-aware substring fallback"
    - "MATCH-only Cypher (never MERGE) for property-annotation passes on an already-seeded backbone -- single-responsibility separation between skeleton creation (ClauseSeeder) and text/citation enrichment (this plan)"
    - "Fail-loud unregistered-source-doc guard (source_doc_prefix raises ValueError) mirrors clause_seeder.py's DEFAULT_FUNCTION_TYPE discipline"

key-files:
  created:
    - src/rag/graph/ontology/clause_text_aligner.py
    - src/rag/graph/ontology/clause_source_annotator.py
    - tests/rag/graph/ontology/test_clause_text_aligner.py
    - tests/rag/graph/ontology/test_clause_source_annotator.py
  modified:
    - src/config/.env.example

key-decisions:
  - "Citation-token normalization: Cybersecurity Act's 'section N' inventory label is stripped to bare N for the citation_id display string (Act-7), matching D-08's own worked example verbatim, rather than the redundant Act-section 7"
  - "Structural-header definition excludes item-letter composite children: an operative clause with lettered sub-items (e.g. 5.3.1 -> 5.3.1(a)(b)(c)) is itself a CU candidate, not a chapter/section skeleton node -- only a true deeper dot-hierarchy clause makes its parent structural"
  - "Text resolution prefers the SHORTEST matching chunk when a metadata/heading match exists (most specific chunk), but the LONGEST matching chunk for the generic substring fallback tier (a merged/catch-all chunk is a safer bet than an unrelated short chunk containing a bare digit as a cross-reference)"

requirements-completed: [R11-3, R11-8]

# Metrics
duration: ~50min
completed: 2026-07-04
---

# Phase 11 Plan 02: Source Layer (Text Alignment + Citation Annotation) Summary

**ClauseTextAligner + ClauseSourceAnnotator attach verbatim provision text and source-doc-namespaced citation ids/doc_class to all 883 seeded :Clause nodes, minting zero :ComplianceUnit nodes -- the source layer 11-04 will classify into Compliance Units.**

## Performance

- **Duration:** ~50 min (incl. worktree dependency install: `poetry lock` + `poetry install` had to run from scratch, ~15 min of that total)
- **Started:** 2026-07-04T15:10:00Z (approx, after context/pattern reading)
- **Completed:** 2026-07-04T15:50:30Z
- **Tasks:** 2 of 3 (both `auto` tasks complete; task 3 is the terminal `checkpoint:human-verify` gate -- STOPPED there per plan)
- **Files modified:** 5 (2 source modules created, 2 test files created, 1 config bugfix)

## Accomplishments

- Re-seeded the 883-node `:Clause` backbone via `ccop-eval graph seed-clauses` (idempotent no-op, confirmed 883 nodes / 765 `HAS_CHILD` edges -- proves the phase is reproducible from a dropped graph, D-25 follow-through)
- `ClauseTextAligner`: every one of the 883 seeded clause nodes now carries verbatim provision text resolved from the re-ingested Qdrant corpus; zero textless nodes; 5.3/5.4 (the Finding-1 regression clauses) verified to carry their real bodies ("Privileged Access Management" / "Domain Controller")
- `ClauseSourceAnnotator`: every clause node now carries a namespaced `citation_id` (`CCoP-5.7.2(b)`, `Act-7`, `Act-Part 1`), a `doc_class` (`binding`/`guidance` per D-08), and an `is_structural_header` flag; zero `:ComplianceUnit` nodes minted (verified live)
- Both passes are idempotent (re-running produces identical stats, no duplicate nodes) and use only static, parameterized Cypher (T-09-12)

## Task Commits

Each task was committed atomically (test-then-feat pairs):

1. **Task 1: Step-0 clause-text alignment** - `f0495e4` (test) + `2fd3426` (feat)
2. **Task 2: Source-layer annotation** - `8ecbdb9` (test) + `fd38e98` (feat)

_Note: both tasks are `tdd="true"`; each landed as a `test(...)` commit followed by a `feat(...)` commit, satisfying the plan-level RED/GREEN gate sequence._

## Files Created/Modified

- `src/rag/graph/ontology/clause_text_aligner.py` - `ClauseTextAligner`, 5-tier verbatim-text resolution + Neo4j write
- `src/rag/graph/ontology/clause_source_annotator.py` - `ClauseSourceAnnotator`, namespaced citation_id + doc_class + structural-header annotation
- `tests/rag/graph/ontology/test_clause_text_aligner.py` - unit (15) + live-integration (4) tests
- `tests/rag/graph/ontology/test_clause_source_annotator.py` - unit (15) + live-integration (5, incl. explicit `:ComplianceUnit` count == 0 assertions) tests
- `src/config/.env.example` - bugfix, see Deviations

## Decisions Made

See `key-decisions` frontmatter above. In addition: chose to duplicate the small, stable "section N" / item-letter decomposition regexes across `clause_text_aligner.py` and `clause_source_annotator.py` rather than cross-importing between them or from `rag.ingestion.scripts.verify_clause_completeness` -- matches that module's own documented precedent (avoids a reverse-direction cross-package dependency for a two-line literal).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed `config/.env.example`'s comment-swallowing empty-value line**
- **Found during:** Task 1 (live Neo4j connectivity required for the mandatory E2E slice)
- **Issue:** `CCOP_NEO4J_PASSWORD=  # set a value before 'docker compose up neo4j'` — an inline `#` comment trailing an EMPTY value is not stripped by python-dotenv the same way it is for a populated value; the whole comment string was parsed as the value. Because `Settings.model_config`'s `env_file` tuple lists `config/.env.example` before `config/.env.local`, this bogus value silently won, so `get_settings().neo4j_password` resolved to a comment string instead of the real local dev password — blocking any live Neo4j connection.
- **Fix:** Moved the explanation to its own comment line above the assignment; `CCOP_NEO4J_PASSWORD=` is now comment-free.
- **Files modified:** `src/config/.env.example`
- **Verification:** `get_settings().neo4j_password` now resolves correctly once a real value is supplied via `config/.env.local`.
- **Committed in:** `2fd3426` (part of Task 1 feat commit)

**2. [Environment, not a code deviation] Worktree-local dependency + secrets bootstrap**
- Ran `poetry lock && poetry install` in this worktree's `src/` (fresh `.venv`, no committed `poetry.lock` — matches the standing MEMORY note "worktree poetry add + lock gitignored").
- Copied the main checkout's gitignored `src/config/.env.local` into this worktree's `src/config/.env.local` (same machine, same user, never touched by git — `git status` confirms it stays untracked) so `poetry run ccop-eval` / pytest could reach the live Neo4j + Qdrant services described in the environment brief.
- Not a plan deviation — purely local environment setup required to run the mandated E2E slice from a freshly created worktree.

---

**Total deviations:** 1 auto-fixed (1 blocking, Rule 3) + 1 environment bootstrap note (no rule, not a code change).
**Impact on plan:** The `.env.example` fix is a small, isolated hygiene fix that unblocks live-service testing for this and all future plans/worktrees; no scope creep into 11-04/CU-minting work.

## Issues Encountered

- Cybersecurity Act 2018's numbering convention ("section N" inventory label vs. the real "N.--(1)..." clause-body prose) required a dedicated precision heuristic (`_body_starts_with_number`) beyond a naive boundary-aware substring match — bare single/double-digit numbers collide constantly with unrelated subsection/cross-reference numbers in that document's prose. Verified against the live corpus that the precise heuristic resolves 46/53 Act entries unambiguously, with the remaining "Part N" ids and a handful of small-number sections falling back to a longest-match generic scan (the only chunk containing them is a large merged TOC/preamble blob) — consistent with, and never less permissive than, the 11-01 completeness gate's own cross-chunk decomposition check (both agree on 883/883 resolved).

## User Setup Required

None - no external service configuration required (Neo4j/Qdrant already running per the environment brief; the only local action taken was copying an already-gitignored `.env.local`, not creating a new secret).

## Next Phase Readiness

- Source layer is ready for 11-04's classification/formalization pass (premise/meta-CU/actor-CU typing + 4-tuple extraction) to mint `:ComplianceUnit` nodes on top of this text + citation layer.
- **BLOCKED on human approval (D-26 wave gate):** this plan's terminal task is `type="checkpoint:human-verify"` — Wave 2 (11-02 + 11-03) requires explicit human sign-off before Wave 3 (11-04) may begin. See the CHECKPOINT REACHED message returned alongside this summary for the exact verification commands/output to review.

---
*Phase: 11-align-graphrag-to-graphcompliance-architecture-scenario-anch*
*Plan: 02 (awaiting human verification -- NOT fully complete)*
*Completed (auto tasks only): 2026-07-04*

## Self-Check: PASSED

All created files verified present on disk; all 4 task commit hashes (`f0495e4`, `2fd3426`, `8ecbdb9`, `fd38e98`) verified present in `git log --all`.
