---
phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2
plan: 03
subsystem: rag
tags: [ontology, graphrag, neo4j, discovery, method-c, coverage-check, curation-gate, openpyxl, openrouter]

# Dependency graph
requires:
  - phase: 10-02
    provides: "Phase 10 settings (ontology_discovery_model, ontology_config_path) + mode-aware DI provider seam + skeleton ontology adapter"
  - phase: 09
    provides: "corpus_source.load_ccop_corpus_texts (Docling-parsed CCoP markdown, held constant) + graph_extraction_model/openrouter settings"
provides:
  - "Method-C grounded-synthesis ontology draft (ontology_draft.json): 20 node types (7 seeded + 13 discovered) + 47 relationship types, human-curated at gate (a)"
  - "Gold-relation parser (D-17): regex extraction of (subject)-[REL]->(object) triples + bracketed clause citations from eval-report xlsx col-22"
  - "D-14 benchmark-coverage + D-17 gold-relation coverage checkers with synonym->canonical normalization (curation-time diagnostics)"
  - "synonym->canonical collapse map + intentionally-excluded gold-verb set (schema-lean coverage without overfitting to gold surface verbs)"
affects: [10-04, 10-05, 10-06, 10-08, method-b-clustering, clause-seeding, schema-constrained-extraction]

# Tech tracking
tech-stack:
  added: []  # no new packages; reused openpyxl + openai(OpenRouter) + Docling, all already project deps
  patterns:
    - "One-shot curation-time discovery CLI (argparse + if __name__==__main__), NOT a runtime service — mirrors audit_ground_truth_citations.py"
    - "One LLM synthesis call per source category (not per-chunk NER) — the D-04 fix for the Phase 9 emergent-NER failure mode"
    - "Gold-verb synonym->canonical normalization at the coverage-check layer — keeps the ontology schema lean while keeping D-17 coverage honest"

key-files:
  created:
    - src/rag/graph/ontology/__init__.py
    - src/rag/graph/ontology/gold_relation_parser.py
    - src/rag/graph/ontology/discovery/__init__.py
    - src/rag/graph/ontology/discovery/coverage_check.py
    - src/rag/graph/ontology/discovery/method_c_synthesis.py
    - src/rag/graph/ontology/ontology_draft.json
    - tests/rag/graph/ontology/test_gold_relation_parser.py
    - tests/rag/graph/ontology/test_coverage_check.py
  modified:
    - .gitignore  # committed-fixture exception for ontology_draft.json (project-wide *.json ignore)

key-decisions:
  - "Curation gate (a) resolved approve-with-amendments: dropped 11 ...Section node types (mirror the CCoP TOC; clause backbone owns hierarchy), added 17 genuinely-new relation types, collapsed 16+3 gold synonyms onto canonicals"
  - "D-17 coverage normalizes gold verbs to ontology canonicals before diffing — schema stays lean (no synonym fragmentation) while coverage stays honest; unresolved_missing=0 after amendments"
  - "additional_node_types/additional_relationship_types left True (permissive) until a later plan locks the ontology post-gate — RESEARCH Pitfall 1 (premature lock silently drops out-of-schema entities)"
  - "3 ambiguous gold verbs (VIOLATES, MAY_REQUEST, ADDRESSES) provisionally collapsed but flagged as gate-b reconciliation input for plan 10-04"

patterns-established:
  - "Grounded-synthesis discovery: 3 structured anchor sources (section headings / benchmark defs / stratified prose), 1 LLM call each, provenance + flagged_ambiguities per proposed type"
  - "Coverage-report-as-curation-artifact: deterministic D-14/D-17 checkers embed their reports INTO the draft JSON for the human gate to review"

requirements-completed: [RAG-06, D-01, D-02, D-03, D-04, D-08, D-09, D-14, D-17, D-18]

# Metrics
duration: ~47min
completed: 2026-07-03
---

# Phase 10 Plan 03: Method-C Grounded Ontology Discovery Summary

**A human-curated, provenance-carrying CCoP ontology draft (20 node types + 47 relations) discovered — not hand-authored — from structured sources (section headings, 18 benchmark definitions, stratified corpus prose), with deterministic D-14 benchmark-coverage and D-17 gold-relation-coverage tooling that surfaced a concrete per-case gap report for the curation gate.**

## Performance

- **Duration:** ~47 min (incl. a real Docling-parse + 3 live OpenRouter synthesis calls, and a human curation-gate pause)
- **Started:** 2026-07-03T09:34:52+08:00 (first commit)
- **Completed:** 2026-07-03T10:21:04+08:00 (amendment commit) + docs
- **Tasks:** 3/3 (Task 3 = curation gate, human-resolved)
- **Files created:** 8; modified: 1

## Accomplishments

- **Method C (grounded synthesis, D-04):** `method_c_synthesis.py` anchors discovery on three STRUCTURED sources and makes exactly one `gpt-4o-mini` call per category — the deliberate opposite of Phase 9's open per-chunk NER (the D-06 failure mode). Reads only the CCoP corpus + benchmark JSONL; reads **no** emergent-graph artifact (D-02, grep-confirmed).
- **Discovered + seeded ontology:** the real run produced 13 discovered domain-entity types with canonical-name dedup already clean (no CII/CIIAsset-style fragmentation — each carries rejected synonyms in `flagged_ambiguities`). Hand-seeded the D-08 regulatory layer (Clause/Control/Obligation/Definition + 5 relations), D-09 function tags (ScopeClause/ControlClause/DefinitionClause), and all 14 D-18 modal/negation relation families.
- **D-17 gold-relation tooling:** `gold_relation_parser.py` regex-extracts triples + clause citations from the eval-report xlsx col-22 (verified live against B01-001), normalizing the `NOT DESIGNATED_AS`→`NOT_DESIGNATED_AS` whitespace pitfall.
- **Concrete curation gate:** the gate saw a real per-case coverage report (57 gold relation types across 18 cases, 45 initially missing) — not just a type list.
- **Gate (a) resolved (approve-with-amendments)** and fully applied: 20 node types, 47 relations, D-14 18/18 mapped, D-17 unresolved-missing = 0.

## Task Commits

1. **Task 1: Gold-relation parser (D-17) + D-14/D-17 coverage checker** — `0fafe2c` (test)
2. **Task 2: Method-C grounded-synthesis discovery + ontology_draft.json** — `bbacd7e` (feat)
3. **Task 3: Curation gate (a) — session pause** — `26f8fea` (docs); **amendments applied** — `e4d9b03` (feat)

**Plan metadata:** (this SUMMARY + STATE/ROADMAP/REQUIREMENTS) — see final docs commit.

## Files Created/Modified

- `src/rag/graph/ontology/gold_relation_parser.py` — READ-ONLY openpyxl+regex parser for col-22 gold triples/citations (D-17); `TRIPLE_RE`/`CLAUSE_BRACKET_RE`, whitespace→underscore relation normalization, digit-presence filter to exclude relation-name brackets from citation detection.
- `src/rag/graph/ontology/discovery/coverage_check.py` — `benchmark_coverage` (D-14, provenance + keyword-overlap) and `gold_relation_coverage` (D-17). Amended at the gate with `GOLD_RELATION_SYNONYM_MAP` (19 entries) + `INTENTIONALLY_EXCLUDED_GOLD_RELATIONS` (9 verbs); reports `unresolved_missing` vs `intentionally_excluded_missing`.
- `src/rag/graph/ontology/discovery/method_c_synthesis.py` — one-shot discovery CLI; 3 anchor-source builders, per-category LLM synthesis with graceful degradation, D-08/D-09/D-18 seeding, embedded coverage reports.
- `src/rag/graph/ontology/ontology_draft.json` — the curated Method-C draft (committed fixture; consumed by 10-04+).
- `tests/rag/graph/ontology/test_gold_relation_parser.py`, `test_coverage_check.py` — 28 tests (regex/parse logic, coverage diffs, normalization, plus a real-xlsx E2E slice).
- `.gitignore` — `!src/rag/graph/ontology/ontology_draft.json` exception (matches the clause_inventory.json committed-fixture precedent).

## Curation Gate (a) — Decisions Applied

| Decision | Action | Result |
|---|---|---|
| 1 | Drop 11 `...Section` node types (mirror CCoP TOC; clause backbone owns hierarchy) | 31 → 20 node types (7 seeded + 13 discovered) |
| 2a | Add 17 genuinely-new relation types (domain/range + description) | 30 → 47 relationship types |
| 2b | Collapse 16 obligation/inverse-direction gold verbs onto canonicals | synonym map recorded; not added as types |
| 2c | Do NOT model hierarchy verbs (INCLUDES/PART_OF/HAS_CHILDREN/SPANS) | intentionally-excluded (backbone owns hierarchy) |
| 2d | Do NOT model junk fragments (ARE/TO/CANNOT/LISTS/MUST_BE) | intentionally-excluded |
| 2e | Provisionally collapse 3 ambiguous verbs, flag for gate-b | see below |

**Post-amendment coverage:** D-14 = 18/18 benchmarks mapped (0 unmapped); D-17 = 9 remaining "missing", **all** on the intentionally-excluded 2c/2d list → **`unresolved_missing` = 0** real schema gaps.

## Gate (b) reconciliation candidates (input for plan 10-04)

These 3 ambiguous gold verbs were **provisionally** collapsed to keep the schema lean, but the distinction is genuine and must be revisited during the Method-B reconcile (gate b):

- **VIOLATES → CANNOT_SATISFY** — active breach vs. inability. Provisional; 10-04 to confirm collapse or split into a distinct active-breach relation.
- **MAY_REQUEST → APPLIES_FOR_WAIVER** — waiver-request context vs. generic request. Provisional; 10-04 to confirm.
- **ADDRESSES → MITIGATES** — generic "addresses a risk". Provisional; 10-04 to confirm.

They are recorded in `ontology_draft.json` under `gate_b_reconciliation_candidates`.

## Deviations from Plan

**1. [Rule 3 - Blocking] `*.json` gitignore blocked committing the draft**
- **Found during:** Task 2 (staging `ontology_draft.json`).
- **Issue:** The project-wide `*.json` ignore rule (`.gitignore:156`) silently excluded the plan's mandated output artifact.
- **Fix:** Added an explicit `!src/rag/graph/ontology/ontology_draft.json` un-ignore exception, matching the existing `clause_inventory.json` committed-fixture precedent.
- **Commit:** `bbacd7e`.

**2. [Rule 2 - Missing critical functionality] `unresolved_missing` / `intentionally_excluded_missing` split in the D-17 report**
- **Found during:** Task 3 amendment (Decision 3).
- **Issue:** The gate asked only for the synonym map, but a bare post-normalization `missing_relations` would still list the deliberately-dropped 2c/2d verbs, making the coverage headline read as 9 gaps when there are 0 real gaps.
- **Fix:** Added `INTENTIONALLY_EXCLUDED_GOLD_RELATIONS` + report split so the honest headline (`unresolved_missing = 0`) is machine-readable. Covered by new tests.
- **Commit:** `e4d9b03`.

Otherwise the plan executed as written.

## Known Stubs

None. `ontology_draft.json` is a real, populated artifact (live Docling parse + 3 OpenRouter synthesis calls + real gold-relation xlsx). `additional_node_types`/`additional_relationship_types` are intentionally left `True` (permissive) — this is a documented curation choice (RESEARCH Pitfall 1), NOT a stub; a later Phase 10 plan locks them to `False` after the ontology is finalized.

## Threat Flags

None. The two trust boundaries in the plan's threat register are unchanged: (1) corpus/benchmark prose → discovery LLM is mitigated by source-category summaries + the human gate (a) that reviewed every proposed type before it entered the draft (T-10-03-01); (2) the gold-relation xlsx is a committed read-only artifact parsed by regex, no eval (T-10-03-03). The OpenRouter key is sourced via settings/env only, never logged (T-10-03-02).

## For the Next Plan (10-04, Method B clustering cross-check)

- **Input:** the curated `ontology_draft.json` (20 node types + 47 relations) is Method B's comparison target — B-only clusters = candidate missing types → user decides keep/drop at gate (b).
- **Reconciliation queue:** the 3 gate-b candidates above (VIOLATES / MAY_REQUEST / ADDRESSES) are explicit reconciliation input.
- **Tooling ready:** `coverage_check.py` (both D-14 and D-17, with normalization) is reusable to re-diff any reconciled ontology; `gold_relation_parser.py` is the stable gold-triple source.

## Self-Check: PASSED

- All 8 created files verified present on disk.
- All 4 task commits (`0fafe2c`, `bbacd7e`, `26f8fea`, `e4d9b03`) verified in git history.
- 28 ontology unit tests pass (`pytest ../tests/rag/graph/ontology/ -m "not integration" -q`).
- Task-2 structural verify command passes (D-08/D-09/D-18 present: 20 node types, 47 relations).

*Phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2*
