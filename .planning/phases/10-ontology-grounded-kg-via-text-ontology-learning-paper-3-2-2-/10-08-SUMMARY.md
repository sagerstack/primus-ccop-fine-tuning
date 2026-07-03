---
phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2
plan: 08
subsystem: graphrag-ontology
tags: [shacl, pyshacl, rdflib, validation, lpg-to-rdf, quarantine, typer-cli, neo4j]

# Dependency graph
requires:
  - phase: 10-04
    provides: locked ontology_config.json (24 node types) — shapes.ttl derives its NodeShapes from these labels
  - phase: 10-05
    provides: ClauseSeeder — seeds the :Clause backbone (clause_id-keyed) the shapes validate without false-flagging
  - phase: 10-07
    provides: OntologyKGBuilder — the built (name-carrying) entities the D-07 canonical-name constraint validates
provides:
  - "shapes.ttl: 24 SHACL NodeShapes encoding D-07 (canonical name REQUIRED, junk names REJECTED) for 20 extracted entity types + clause_id-required for 4 seeded clause-backbone types"
  - "SHACLValidator: pure LPG→RDF export (Neo4j records → rdflib.Graph) + pyshacl.validate + quarantine of violations to validation_report.json (reject + log, never delete)"
  - "ccop-eval graph validate CLI subcommand — operator-facing backstop, exits non-zero on HIGH-severity violations so it can gate a build"
affects: [10-09-clause-anchored-retrieval, 10-10/10-11-graphrag-ontology-mode-eval]

# Tech tracking
tech-stack:
  added:
    - "rdflib 7.6.0 (RDF graph + Turtle parsing for the LPG→RDF export and shapes)"
    - "pyshacl 0.31.0 (pure-Python SHACL validator; + owlrl 7.1.4 transitive)"
  patterns:
    - "Two-family SHACL design: extracted entities keyed on canonical `name` (D-07), seeded clause-backbone keyed on `clause_id` (D-10) — avoids falsely quarantining the 691-clause seeded backbone which carries no `name` property"
    - "Reusable named PropertyShape (ccop:CanonicalNameConstraint) referenced by all 20 extracted-entity NodeShapes so the junk-rejection rule is authored ONCE and cannot drift between types"
    - "Pure LPG→RDF export function (lpg_to_rdf: Neo4j record dicts → rdflib.Graph) + pure validate_rdf core, so the constraint logic is unit-testable in memory with zero live driver; only the top-level validate() orchestration touches Neo4j (mirrors KGInspector session-query style)"
    - "Quarantine-not-delete: validation NEVER mutates the data graph; violations are collected into a serializable ValidationReport and written to validation_report.json (mirrors BuildStats.failures degrade-with-visibility convention)"

key-files:
  created:
    - "src/rag/graph/ontology/shapes.ttl"
    - "src/rag/graph/ontology/shacl_validator.py"
    - "tests/rag/graph/ontology/test_shacl_validation.py"
  modified:
    - "src/pyproject.toml"
    - "src/rag/graph/cli/graph.py"

decisions:
  - "Two-family shape design (name-keyed extracted types vs clause_id-keyed seeded types): the seeded :Clause backbone (D-10 ClauseSeeder) carries clause_id/source_doc/chapter/function_type but NO `name`. Requiring `ccop:name` on Clause-family classes (Clause + the 3 function-tag classes ScopeClause/ControlClause/DefinitionClause) would have falsely quarantined all 691 deterministically-seeded, provably-correct clauses. So the 20 LLM-extracted entity types are validated against a canonical-name constraint (D-07, where Phase 9 produced junk) and the 4 clause-backbone types against a clause_id constraint (D-10)."
  - "Junk rejection uses layered constraints on one reusable PropertyShape: sh:minCount 1 + sh:maxCount 1 (exactly one name) + sh:datatype xsd:string + sh:minLength 2 (rejects 'A'/empty) + sh:pattern '[A-Za-z]{2,}' (must contain a real word — rejects 'N.A.' which has no 2 consecutive letters) + sh:not sh:in (explicit denylist of Phase-9 placeholders: N.A., N/A, John Doe, Company X, TBD, Unknown, None, ...). Belt-and-suspenders: a junk value like 'N.A.' trips both the pattern AND the denylist, so the constraint is robust to either being weakened."
  - "rdflib/pyshacl (pure Python) over n10s: n10s runs SHACL in-DB but has unverified Neo4j 5.26 compatibility, needs RDF-mapping config on the live graph, and a heavier operational surface (RESEARCH Pitfall 5 / Q5). Export-and-validate keeps validation as a stateless batch step with a committed, code-reviewable shapes.ttl and no live-graph mutation."
  - "Exit-code gating: `graph validate` exits non-zero when HIGH-severity (sh:Violation) violations exist so it can gate a build in the D-19 inspect→adjust→rebuild loop; conformant graphs exit 0."

requirements-completed: [RAG-06, D-13]

# Metrics
duration: ~40min (dominated by two long poetry resolver passes — a --dry-run for the package-legitimacy gate, then the real add)
completed: 2026-07-03
---

# Phase 10 Plan 08: SHACL Validation Backstop (D-13) Summary

**A pure-Python SHACL backstop (`shapes.ttl` + `SHACLValidator` + `ccop-eval graph validate`) that exports the built ontology graph LPG→RDF, validates it against committed shapes encoding the D-07 anti-pattern fixes (canonical `name` REQUIRED for the 20 extracted entity types, junk names like "N.A."/"A"/"John Doe" REJECTED; `clause_id` REQUIRED for the 4 seeded clause-backbone types), and quarantines any non-conforming fact to a JSON report — reject + log separately, NEVER silent-delete — proven end-to-end against live Neo4j.**

## Performance

- **Duration:** ~40 min (the two poetry dependency-resolution passes — one `--dry-run` to gather package-legitimacy evidence for the blocking-human gate, then the real `poetry add` — dominated wall-clock time at ~7–8 min each on this resolver)
- **Completed:** 2026-07-03
- **Tasks:** 3 (Task 1 = blocking-human package-legitimacy gate; Task 2 = TDD RED+GREEN shapes+validator; Task 3 = CLI subcommand), plus one within-scope deprecation fix surfaced by the live E2E slice
- **Files touched:** 5 (3 new: shapes.ttl, shacl_validator.py, test file; 2 modified: pyproject.toml, graph.py)

## Accomplishments

- **`shapes.ttl`** — 24 `sh:NodeShape`s (one per locked ontology node type) encoding the D-06/D-07 structural fixes as machine-checked SHACL:
  - 20 **extracted-entity** shapes reference a single reusable `ccop:CanonicalNameConstraint` PropertyShape requiring exactly one canonical string `name` (≥2 chars, containing a real word) and rejecting the Phase-9 junk set via `sh:pattern` + an explicit `sh:not sh:in` denylist.
  - 4 **seeded clause-backbone** shapes (Clause + function tags ScopeClause/ControlClause/DefinitionClause) require a non-empty `clause_id` instead of `name` — the fix for what would otherwise falsely quarantine the entire 691-clause seeded backbone.
- **`shacl_validator.py`** — pure `lpg_to_rdf()` export (Neo4j record dicts → in-memory `rdflib.Graph`: node→URI, label→`rdf:type`, property→literal, relationship→predicate), a pure `validate_rdf()` core running `pyshacl.validate(... abort_on_first=False)`, a `ValidationReport` dataclass (conforms + quarantined `Violation`s with focusNode/resultPath/severity/shape/value/message, severity+shape rollups, `to_dict`/`write_json`), and a `validate()` orchestration that exports the live graph, validates, and quarantines violations to `validation_report.json` — **the data graph is never mutated** (D-13).
- **`ccop-eval graph validate`** CLI subcommand mirroring `inspect`/`stats`: opens the driver, runs the validator, prints conformance + violations-by-severity + violations-by-shape + up to 10 example rows, points at the quarantine report, and **exits non-zero on HIGH-severity (`sh:Violation`) violations** so it can gate a build.
- **Real smallest-slice E2E against live Neo4j** (per `~/.claude/rules/e2e-testing.md`): seeded a controlled 3-node graph (one valid `CriticalInformationInfrastructure`, one junk `OperationalTechnology {name:'N.A.'}`, one seeded `Clause {clause_id:'1.2.1'}`), ran the REAL `SHACLValidator.validate()` export→validate→quarantine path, and asserted the junk node was quarantined while the valid entity AND the clause conformed — then tore down cleanly (0 marker nodes remaining). This exercised the exact cross-layer seams the pure tests can't: Neo4j `elementId` URI format, `dict(props)` conversion, session queries, and the `__Entity__`+type-label dual-label mapping.

## Task Commits

1. **Task 1 gate cleared → dependency add** — `4009c7c` (chore: rdflib 7.6.0 + pyshacl 0.31.0 + owlrl 7.1.4; `src/poetry.lock` is gitignored in this repo, so only `pyproject.toml` was committed)
2. **Task 2 RED: failing SHACL tests** — `2f6ce1b` (test)
3. **Task 2 GREEN: shapes.ttl + shacl_validator.py** — `b33ccb6` (feat)
4. **Task 3: `graph validate` CLI subcommand** — `9974dde` (feat)
5. **Deprecation fix (E2E-surfaced): abort_on_first** — `814e5b0` (fix)

_TDD gate sequence verified: `test(10-08)` (`2f6ce1b`) precedes `feat(10-08): implement` (`b33ccb6`) in git log — RED then GREEN._

## Checkpoint / Gate Outcomes

- **Package-legitimacy gate (Task 1, blocking-human):** Returned structured evidence (pypi.org canonical status for both packages under github.com/RDFLib, pure-Python, no Python-floor conflict, resolved versions from a `poetry add --dry-run`) and STOPPED — did not self-approve. Coordinator returned **"approved"**; install then proceeded.
- **Validation review gate (post-validation):** Ran `graph validate` against the **actual current live graph** (883 seeded `Clause` nodes; 10-07's built entity graph was torn down by its own E2E teardown). Result: **conforms=True, 0 violations, 0 facts quarantined.** Per the coordinator's instruction ("if ZERO facts are quarantined, you may complete the plan without pausing"), the plan completed without pausing. No non-conforming facts required human review. The only quarantine observed was the *deliberately-inserted* junk node in the E2E slice, which was a test artifact and was torn down.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pyshacl 0.31 deprecated `abort_on_error` → `abort_on_first`**
- **Found during:** the live-Neo4j E2E slice, which emitted `Usage of abort_on_error is deprecated. Use abort_on_first instead.`
- **Issue:** the validator initially called `pyshacl.validate(..., abort_on_error=False)`; pyshacl 0.31.0 renamed this parameter (old name still works but is deprecated).
- **Fix:** switched to `abort_on_first=False` (semantically identical, both default False — no behavior change).
- **Files modified:** `src/rag/graph/ontology/shacl_validator.py`
- **Verification:** 17/17 pure tests still pass; no deprecation warning on re-run.
- **Committed in:** `814e5b0`.

**Total deviations:** 1 auto-fixed (1 deprecation, surfaced only by running the real slice — exactly the class of seam mocked tests miss).

## Design Note (not a deviation) — two-family shape design

The plan's `<action>` said "an `sh:NodeShape` per locked node type requiring `sh:minCount 1` ... on the canonical `name` property." Applied literally to **all** 24 types, this would have falsely quarantined all seeded `:Clause` nodes, which carry `clause_id` (D-10) and no `name`. The implementation therefore splits the 24 shapes into a name-keyed family (20 extracted types — where Phase 9 produced junk, so this is exactly where the D-07 constraint belongs) and a clause_id-keyed family (4 seeded clause-backbone types). This honors the plan's intent (structurally reject junk/unnamed extracted facts) while not breaking on the legitimately-named-differently seeded backbone. Verified correct by the live run (883 seeded clauses → 0 false violations).

## Issues Encountered

- **Fresh worktree missing `poetry install` + gitignored `.env.local`** — same friction 10-05/10-07 documented. The `poetry add` performed the install; `src/config/.env.local` was copied from the main checkout (still gitignored, confirmed via `git check-ignore`, never committed) so the live-Neo4j E2E slice + real validation run could execute.
- **Slow poetry resolver** — both the `--dry-run` (legitimacy-gate evidence) and the real `add` took ~7–8 min each to resolve the full dependency graph. Not a defect; just wall-clock cost noted for future estimates.
- **`ccop-eval` entry-point warning** ("not installed as a script") — PRE-EXISTING fresh-worktree behavior (the package isn't `poetry install`-ed as a console script in the worktree); cosmetic, does not affect `--help` exit 0 or the validator. Out of scope.

## Known Stubs

None. All three artifacts are fully wired: shapes.ttl drives real pyshacl validation, the validator runs against live Neo4j, and the CLI is a first-class subcommand — proven end-to-end.

## User Setup Required

None beyond the already-running local Neo4j Docker service and the existing `CCOP_NEO4J_PASSWORD` (both already configured for this worktree via the copied `.env.local`). `poetry.lock` is gitignored in this repo; a fresh checkout gets rdflib/pyshacl via `poetry install` from the committed `pyproject.toml`.

## Next Phase Readiness

- The SHACL backstop is ready to gate any future `graph build-ontology` run: `seed-clauses → build-ontology → validate` is now the full governed-KG construct-and-check chain. When a real corpus build is run, `ccop-eval graph validate` will quarantine (never delete) any extracted fact that lacks a canonical name or carries a Phase-9-style junk value, writing `validation_report.json` for curation.
- 10-09 (clause-anchored retrieval) and 10-10/10-11 (graphrag-ontology A/B) can rely on the validated backbone; the validator is a standalone, re-runnable batch step that does not touch the retrieval path.
- No blockers.

---
*Phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2-*
*Completed: 2026-07-03*

## Self-Check: PASSED

- FOUND: src/rag/graph/ontology/shapes.ttl
- FOUND: src/rag/graph/ontology/shacl_validator.py
- FOUND: tests/rag/graph/ontology/test_shacl_validation.py
- FOUND: `graph validate` subcommand in src/rag/graph/cli/graph.py
- FOUND commit: 4009c7c (chore — rdflib+pyshacl add)
- FOUND commit: 2f6ce1b (test RED)
- FOUND commit: b33ccb6 (feat GREEN — shapes + validator)
- FOUND commit: 9974dde (feat — graph validate CLI)
- FOUND commit: 814e5b0 (fix — abort_on_first deprecation)
- 17/17 pure pytest pass; live-Neo4j E2E slice passed (junk quarantined, valid+clause conform, clean teardown); real 883-node graph conforms with 0 quarantined
