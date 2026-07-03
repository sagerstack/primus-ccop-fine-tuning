# Deferred Items — Phase 10

Pre-existing / out-of-scope issues discovered during plan execution, not fixed
(Executor scope boundary: only auto-fix issues directly caused by the current
task's own changes).

## 10-01

- **`.gitignore` `models/` pattern shadows `src/infrastructure/adapters/models/`**
  (line 139, `models/`) — silently excludes `mock_gateway.py`,
  `claude_cli_gateway.py`, `routing_gateway.py` from version control (they
  exist as untracked files in the main working tree only). Same root-cause
  class as the Phase 9 `src/rag/graph/build/` shadowing bug already fixed
  (`STATE.md` [Phase 09-02]). A fresh worktree checkout of this repo cannot
  run `ccop-eval` at all without these three files present, since
  `container.py` imports `mock_gateway` unconditionally. Worked around for
  this plan's execution by copying the untracked files from the main
  checkout into the worktree (not committed, not a code change) — the
  underlying `.gitignore` pattern needs a proper fix (e.g. anchor it to the
  actual model-weights-cache directory it was meant to exclude) in a future
  plan/bugfix, not this one.
  (Note: 10-02 subsequently force-added these three files into version control
  during its worktree commit; the `.gitignore` pattern itself is still unfixed.)

- **`eval-run-hybrid-tests-18-bdc4927d-20260430-0232-primus-reasoning.json`
  has a corrupted `test_id` for the B04 entry** — the top-level
  `test_results[].test_id` for B04 is a whitespace/control-character string
  (`"\n      "`) instead of `"B04-001"`. The sibling
  `...-0232-primus-reasoning.partial.jsonl` for the same run has the correct
  `"B04-001"`, so the 18-id set could still be reliably reconstructed for
  this plan's Task 1. File mtime is 2026-07-02 (today), inconsistent with
  its siblings (April 2026) — something touched this canonical file
  recently. Given `MEMORY.md` designates this exact file as "the canonical
  hybrid baseline run," a corrupted `test_id` on any downstream consumer
  that trusts the top-level JSON (not the partial log) is a latent
  data-integrity bug worth a `bugs.md` entry and a decision on whether the
  file needs restoring/re-deriving. Out of scope for 10-01 (read-only input,
  not a files_modified target).

- **`Neo4jGraphRetrievalAdapter` / `HybridCypherRetriever` Lucene fulltext
  query can throw a lexical error on certain punctuation in the question
  text** — observed during the Task 1 baseline run on B02-001 ("...
  username/password plus an SMS one-time code..."): the raw query text is
  passed to Neo4j's Lucene fulltext query parser un-escaped, and the `/`
  and `'` characters produced `org.apache.lucene.queryparser.classic.
  TokenMgrError: Lexical error ... after prefix "/password..."`. The graph
  node caught this as `RETRIEVAL_FAILURE` / `no_relevant_documents` and
  correctly fell back to the no-context generation path (no crash, but zero
  retrieved documents for that case). This is a pre-existing Phase 9
  retrieval-adapter behavior; Plan 10-01 explicitly forbids touching
  retrieval config ("Do NOT change generator, embedder, or retrieval
  config — this is the identical Phase 9 stack, one label"), so it was
  reproduced faithfully, not patched. Worth a Lucene special-character
  escaping fix in a future retrieval-adapter plan (likely 10-09, since it
  touches the same adapter).

- **`qdrant-local` Docker container reports `unhealthy`** in `docker ps`
  during this plan's execution window. Not a blocker for Task 1/2 (graphrag
  mode uses only Neo4j, not Qdrant), but flagged in case a later Phase 10
  plan needs the hybrid baseline leg and hits Qdrant connectivity issues.

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
