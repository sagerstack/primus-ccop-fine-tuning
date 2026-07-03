---
phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2
plan: 06
subsystem: rag/graph/build
tags: [graphrag, extraction, chunking, gleaning, d-11, neo4j-graphrag]
requires:
  - "clause_aware_chunker.CLAUSE_PATTERN (boundary regex, reused not re-invented)"
  - "neo4j_graphrag 1.18.0 (TextSplitter, LLMEntityRelationExtractor)"
  - "settings.gleaning_max_gleanings (D-11 config, front-loaded in 10-02)"
provides:
  - "SectionAlignedSplitter (coarse text_splitter= component, D-11 extraction unit)"
  - "GleaningEntityRelationExtractor (multi-pass extract_for_chunk override, D-11 gleaning)"
affects:
  - "10-07 ontology_kg_builder pipeline (injects both as text_splitter= and the extractor)"
tech-stack:
  added: []
  patterns:
    - "neo4j-graphrag custom Component (TextSplitter subclass, async .run -> TextChunks)"
    - "library subclass-point override (extract_for_chunk) with factory-injectable ctor param"
    - "reuse base-class JSON-repair/OnError (fix_invalid_json + Neo4jGraph.model_validate)"
key-files:
  created:
    - "src/rag/graph/build/section_aligned_splitter.py"
    - "src/rag/graph/build/gleaning_extractor.py"
    - "tests/rag/graph/build/test_section_aligned_splitter.py"
    - "tests/rag/graph/build/test_gleaning_extractor.py"
  modified: []
decisions:
  - "Group by top-level section key (chapter.section) — strip item-letter suffix before keying"
  - "Preamble (pre-first-clause text) kept as its own leading chunk, not merged into section 1"
  - "Rebind run = LLMEntityRelationExtractor.run to satisfy ComponentMeta per-class run check"
  - "max_gleanings passed at ctor call-site (not read from Settings in the class) for testability"
metrics:
  duration: ~40min (incl. background poetry install + one 5-min test collection)
  tasks: 2
  files: 4
  tests_added: 16
  completed: 2026-07-03
---

# Phase 10 Plan 06: Section-Aligned Splitter + Gleaning Multi-Pass Extractor Summary

Built the two D-11 **extraction-unit** components that decouple the extraction chunk from the retrieval unit: a coarse section-aligned `text_splitter=` (multiple clauses per top-level section boundary) and a gleaning multi-pass `extract_for_chunk` override that recovers entity recall lost to larger chunks — both plug into the 10-07 ontology KG builder.

## What Was Built

### Task 1 — SectionAlignedSplitter (D-11 extraction unit)
- `SectionAlignedSplitter(TextSplitter)` — async `.run(text) -> TextChunks` neo4j-graphrag Component satisfying the `text_splitter=` contract.
- Reuses `clause_aware_chunker.CLAUSE_PATTERN` (the proven Docling `## X.Y heading` boundary regex, bug #10 fix) but groups every clause under one **top-level** section key (`chapter.section`, e.g. `5.3.1`/`5.3.2` → `5.3`), splitting only at the next top-level section (`5.4`).
- Item-letter suffixes (`5.3.1(a)`) are stripped before keying, so sub-item boundaries never start a new chunk. Front-matter before the first clause is emitted as a leading preamble chunk.
- Explicitly NOT clause-granularity (D-05/D-20 extraction-starving anti-pattern) and NOT Phase 9's structure-blind 4000-char FixedSizeSplitter.
- Commit: `7ebaa7f`

### Task 2 — GleaningEntityRelationExtractor (D-11 gleaning)
- `GleaningEntityRelationExtractor(LLMEntityRelationExtractor)` — overrides `extract_for_chunk` only; runs the base single pass, then `max_gleanings` follow-up "what was missed" passes, unioning all passes' `nodes`/`relationships` (no drop).
- Explicit `max_gleanings: int` ctor param (factory-injection discipline mirrored from `kg_builder.py`), defaulting at the call-site to `settings.gleaning_max_gleanings` (D-11).
- Follow-up JSON parsed via the base class's own `fix_invalid_json` + `Neo4jGraph.model_validate` with the same `OnError` semantics — no hand-rolled parser (Don't-Hand-Roll; T-10-06-02 mitigation).
- Follow-up prompt lists already-found entities and asks for ADDITIONAL ones (D-07 ignore-illustrative discipline inherited via the shared prompt template).
- Commit: `f412153`

## Verification

- `poetry run pytest ../tests/rag/graph/build/test_section_aligned_splitter.py ../tests/rag/graph/build/test_gleaning_extractor.py -m "not integration" -q` → **16 passed**.
- Splitter (8): component contract, 5.3/5.4 grouping, 5.3.1(a) no-new-chunk, preamble handling.
- Extractor (8): scripted 2-call union superset, `max_gleanings=0` == single pass, `max_gleanings=2` == 3 calls, glean prompt references prior entities, malformed follow-up JSON handled by inherited repair/OnError (both IGNORE and RAISE).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `ComponentMeta` requires an own-class `run` on the extractor subclass**
- **Found during:** Task 2 (test collection `RuntimeError: You must implement either 'run' or 'run_with_context' in Component 'GleaningEntityRelationExtractor'`).
- **Issue:** neo4j-graphrag's `ComponentMeta.__new__` inspects the class's own `attrs`, not the resolved MRO, so subclassing `LLMEntityRelationExtractor` and overriding only `extract_for_chunk` trips the metaclass check even though `run` is inherited.
- **Fix:** Rebind `run = LLMEntityRelationExtractor.run` as a class attribute — satisfies the metaclass without duplicating the base `run` body. Only `extract_for_chunk` (the documented override point, RESEARCH.md Q2) is customized.
- **Files modified:** `src/rag/graph/build/gleaning_extractor.py`
- **Commit:** `f412153`

## Known Stubs

None. Both components are fully wired; injection into the hand-built ontology pipeline lands in 10-07 (a downstream plan, per the plan's key_links).

## Notes for 10-07

- Inject as `SimpleKGPipeline(..., text_splitter=SectionAlignedSplitter(), ...)`. `SimpleKGPipeline` hardcodes its own `LLMEntityRelationExtractor` and (in 1.18.0) exposes no `extractor=` override — per RESEARCH.md A5, the gleaning extractor requires a **hand-built `Pipeline`** (`loader → splitter → schema → extractor(gleaning) → resolver → writer`). Verify the live `SimpleKGPipeline` constructor signature at build time before assuming the hand-built path is still required.
- The section-aligned decouple is a MEASURE-not-assume hypothesis (RESEARCH.md Q3 caveat): budget an eval pass (RAGAs context metrics + clause-hit@3) to confirm section-aligned + gleaning beats the Phase 9 4000-char default before treating it as settled.

## Self-Check: PASSED

- Files exist: section_aligned_splitter.py, gleaning_extractor.py, test_section_aligned_splitter.py, test_gleaning_extractor.py — all FOUND.
- Commits exist: 7ebaa7f (Task 1), f412153 (Task 2) — both FOUND in git log.
