# Deferred Items — Phase 09

Out-of-scope discoveries found during execution. NOT fixed here (SCOPE BOUNDARY).

## Pre-existing test failures: `tests/domain/services/test_llm_judge_service.py` (9 tests)

- **Discovered during:** Plan 09-01, Task 3 (full `poetry run pytest -m "not integration"` run).
- **Symptom:** 9 tests fail with `TypeError: unhashable type: 'dict'` in
  `LLMJudgeService._build_judge_prompt` (e.g. `test_build_judge_prompt`,
  `test_parse_judge_response_*`, `test_call_claude_agent_*`, `test_evaluate_response_*`).
- **Root cause (pre-existing):** Commit `a34c18c` ("refactor(judge): migrate LLMJudgeService
  from Claude CLI to OpenRouter") changed `_build_judge_prompt`'s third argument from a rubric
  **dict** to a `benchmark_id: str`, but the test file was last updated in `6b134e3` (predates
  the migration). The tests still pass a dict where a string is now expected.
- **Confirmed pre-existing:** `git merge-base --is-ancestor a34c18c 4efc77e` = YES (migration
  predates the 09-01 base commit `4efc77e`). Unrelated to 09-01's settings/Neo4j changes and
  unrelated to the neo4j-graphrag transitive dependency downgrades (a Python `dict`-unhashable
  error cannot originate from a package version change).
- **Why not fixed here:** Out of scope — these are stale tests against the DEPRECATED legacy
  Claude-CLI judge path, orphaned by a prior phase's refactor. Fixing them is unrelated to the
  Neo4j GraphRAG foundation this plan delivers.
- **Suggested owner:** A judge-tests cleanup task (update the stale tests to the OpenRouter
  `benchmark_id: str` signature, or remove them if the legacy path is fully retired).

## Chunk granularity → Phase 10 (clause-anchored retrieval), not Phase 9

- **Discovered during:** Wave-6 confound analysis (`--mode graphrag` judge 0.06 vs hybrid 0.44 on
  B01-001) + deep-research pass on GraphRAG chunking for regulatory text (2026-07-02).
- **Decision (D-20 / ADR-007):** Phase 9 keeps neo4j-graphrag's default coarse `FixedSizeSplitter`
  (4000 char / 200, single-pass, no gleaning) and **reports coarse chunking as an intrinsic OOTB
  limitation** — NOT re-chunked here. Re-chunking would violate D-05 (starves relationship
  extraction) and D-01 (adds a 2nd ablation variable).
- **Carried to Phase 10 (D-16a):** deliver clause granularity via the decouple — section-level
  extraction chunks (+ gleaning/multi-pass, user-added since neo4j-graphrag lacks it) → clause-
  hierarchy node seeding → **clause-anchored fine retrieval**. ⚠️ Seeding alone is insufficient:
  if P10 retrieval still returns the coarse chunk, the return-unit confound rides into Phase 10.
- **Research report:** `docs/project_notes/research/2026-07-02-graphrag-chunking-regulatory.md`
  (22/25 claims survived 3-vote adversarial verification).
- **In scope for Phase 9 (NOT deferred):** rerank + sparse + `top_n`→3 retrieval-funnel parity
  (Wave-6 harness work) — orthogonal to chunking.
