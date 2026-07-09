---
phase: 11-align-graphrag-to-graphcompliance-architecture-scenario-anch
plan: "04"
subsystem: rag-graph-ontology
tags: [graphcompliance, compliance-unit, claude-cli, opus-4.8, 4-tuple, policy-graph, neo4j]
requirements-completed: [R11-2, R11-4]
completed: 2026-07-05
---

# Phase 11 Plan 04: Mint Compliance Units + 4-tuples (Policy Graph Stage 1–2) Summary

**Minted the `:ComplianceUnit` layer on the 883-clause source graph and extracted the GraphCompliance 4-tuple on every obligation CU using `claude-opus-4-8` via the local Claude CLI gateway (user directive — proper CUs over extraction-model parity).**

## Accomplishments

- **Task 1 (committed `5a018f9`): Stage-1 classify + mint.** Added `settings.cu_extraction_model` (default `claude-opus-4-8`). `cu_classifier.py` warm-starts from Phase-10 `function_type` tags (ControlClause→actor-CU, ScopeClause→meta-CU, DefinitionClause→premise) so classification needs ~zero LLM calls; mints one typed `:ComplianceUnit` per operative clause, MERGE-linked to its source clause. **113 structural headers correctly excluded** (883 − 113 = 770). Result: **770 CUs** — actor-CU 744, meta-CU 20, premise 6.
- **Task 2 (Stage-2 4-tuple extraction): `cu_extractor.py`.** Routes the extraction LLM call through `ClaudeCliGateway` (`claude -p --model claude-opus-4-8`), Pydantic-validated `CUTuple`, degrade-to-empty on bad JSON / CLI failure (never aborts the batch). Ran over all **764 obligation CUs** (actor + meta). Result: **764 / 764 obligation CUs carry a complete ⟨subject, constraint, context, conditions⟩ 4-tuple**; premises (6) correctly carry no tuple; source `text` untouched.
- **Model:** `claude-opus-4-8` via local Claude CLI (no OpenRouter on this path), per the 2026-07-05 user directive.

## Live verification (Neo4j bolt://localhost:7687)

- `:ComplianceUnit` = 770 (actor-CU 744 / meta-CU 20 / premise 6)
- obligation CUs with 4-tuple = 764 / 764 (0 missing)
- CUs without hard-linked source text = 0
- `:Clause` backbone = 883 (unchanged)
- Unit tests (fake gateways, no Opus): 33 passed.

## Deviations from Plan

**[Rule 1 — infra] Executor terminated on Claude monthly spend limit AFTER completing the extraction but BEFORE committing Task 2 code + SUMMARY.**
- The background executor agent hit "You've hit your monthly spend limit" partway through the run's *polling*, but by that point all 764 4-tuples were already extracted and written to Neo4j (verified: REMAINING 0). `cu_extractor.py` + `test_cu_extractor.py` were written to disk but uncommitted.
- **Recovery (orchestrator, no re-run / zero additional Opus spend):** validated the on-disk code (33 tests pass on fake gateways), removed a throwaway `run_cu_extraction_scratch.py`, and committed Task 2 + this SUMMARY. The expensive Opus build was not repeated — the graph already carried the complete result.

## Next Phase Readiness

- Policy Graph Stage 1–2 complete: typed CUs + 4-tuples on the source layer. Wave 4 (11-05) may now build `REFERS_TO` edges and the `build-compliance` orchestrator on top.
- Per user directive, Wave 4's implicit-reference LLM will also use `claude-opus-4-8` via `claude -p`.

## Self-Check: PASSED
- FOUND: src/rag/graph/ontology/cu_classifier.py, cu_extractor.py, tests, settings.cu_extraction_model
- CONFIRMED: 770 CUs minted; 764/764 obligation CUs carry a 4-tuple; 0 CUs without source text; 883 clauses intact
