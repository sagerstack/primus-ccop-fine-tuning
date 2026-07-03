# Deferred Items — Phase 10

Out-of-scope discoveries logged during plan execution, not fixed (scope
boundary: only auto-fix issues directly caused by the current task's changes).

## 10-02

- **`tests/domain/services/test_llm_judge_service.py` — 9 pre-existing
  failures**, unrelated to GraphRAG mode wiring. `LLMJudgeService._build_judge_prompt`
  signature appears to have drifted from what the test file calls (test passes
  `rubric: dict[str, str]` positionally; failure surfaces before any Phase 10
  code runs). Confirmed present on `git stash`-equivalent (pre-plan-10-02)
  state — not introduced by this plan's changes to `run_id.py` / `evaluate.py`
  / `query.py` / `routing.py` / `graph_retrieval_node.py` /
  `neo4j_ontology_graph_retrieval_adapter.py` / `container.py` / `settings.py`
  / `graph_state.py`. Discovered while running the fast slice
  (`pytest -m "not integration"`) as part of this plan's E2E verification.
  Needs its own investigation/fix outside Phase 10 scope.
