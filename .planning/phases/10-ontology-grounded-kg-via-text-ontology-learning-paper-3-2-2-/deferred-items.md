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

## 10-09

- **RESOLVED (carried from 10-01):** the Lucene fulltext lexical-error bug on
  `/` and `'` characters (flagged above under `## 10-01`) is fixed for the
  ontology adapter by `_escape_lucene_query_text` in
  `neo4j_ontology_graph_retrieval_adapter.py` — verified live in this plan's
  E2E slice with the exact B02-001-class question shape
  ("username/password plus the user's SMS OTP"), which returned documents
  with no `TokenMgrError`/`SearchQueryParseError`. **Still open for Phase 9's
  `Neo4jGraphRetrievalAdapter`** (`neo4j_graph_retrieval_adapter.py`) — that
  file is untouched by this plan (D-16 additivity: Phase 9's adapter must
  stay unmodified), so `--mode graphrag` (as opposed to `--mode
  graphrag-ontology`) still has the unescaped-Lucene-text bug. A future
  bugfix plan could either backport the same `_escape_lucene_query_text`
  helper to Phase 9's adapter or leave it as a Phase-9-only known limitation.

- **`tests/rag/test_container_vector_store.py` and
  `tests/rag/test_port_adapters.py` collection errors** (same `mlflow`
  `ImportError`, see `## 10-05` below) still present in this plan's worktree;
  confirmed pre-existing and unrelated to this plan's files (`git diff --stat`
  shows zero changes to `pyproject.toml`/`poetry.lock`). Excluded from this
  plan's `pytest -m "not integration"` verification runs via `--ignore`.

## 10-05

- **`tests/rag/test_container_vector_store.py` and
  `tests/rag/test_port_adapters.py` — collection errors, `ImportError: cannot
  import name 'Dataset' from 'mlflow.entities'`** — pre-existing installed-
  package version mismatch inside `mlflow`'s own internal imports
  (`mlflow.data.dataset` importing `mlflow.entities.Dataset`, which the
  currently-locked `mlflow` version doesn't expose). `poetry.lock` /
  `pyproject.toml` are untouched by this plan (`git status` confirms zero
  diff on both), so this is an environment state issue, not something this
  plan's `clause_seeder.py` / `graph.py` changes caused. Unrelated to the
  `src/rag/graph/ontology/` and `src/rag/graph/cli/` files this plan
  modifies. Needs its own investigation (likely an `mlflow` version bump or
  pin) outside Phase 10 scope.

## 10-11 (A/B interpretation — ROOT-CAUSE FINDINGS)

These surfaced while manually triaging the graphrag-ontology eval leg
(B01–B04 of the `bdc4927d` set) before the full A/B run. They are not minor
deferrals — collectively they mean the ontology leg's "clause-grounded
retrieval" was not actually clause-grounded, so the phase's headline metric
(clause-hit@3) is being measured on a broken layer. Evidence gathered by direct
Cypher against the built graph (`graph build-ontology`, 221 chunks / 2751 nodes).

- **FINDING 1 — The `:Clause` retrieval unit carries NO text (the core defect).**
  0 of 500 sampled `:Clause` nodes have a `.text` property — they are pure
  structural anchors (`clause_id`, `chapter`, `source_doc`, `function_type`).
  The only nodes with retrievable text are `:Chunk` nodes: **221 chunks, avg
  3,010 chars (~750 words = a section, many clauses), max 127,793 chars (~an
  entire document)**, each `LINKED_TO` ~30 clauses on average (max 217). So the
  D-11 promise — *coarse chunks for extraction, fine `:Clause` nodes as the
  retrieval/citation unit* — is broken: there is nothing clause-sized to
  retrieve, so the adapter (`neo4j_ontology_graph_retrieval_adapter.py`
  `RETRIEVAL_QUERY` returns `chunk.text`) always returns the coarse chunk and
  bolts a clause-id *label* onto it. **Retrieval returns sections/documents, not
  clauses.** Fix options: (1) attach each clause's own provision text to the
  `:Clause` node and retrieve/rank those; or (2) split chunks to clause size and
  cite the leaf (re-opens the extraction-recall tension D-11 tried to resolve).

- **FINDING 2 — `clause_id` is not unique; it collides across all 6 source
  documents.** `clause_id="1"` returns **6 nodes** (one per doc: Risk Assessment
  Guide, Security By Design, Threat Modelling Guide, CCoP 2.0, Audit Guide,
  Response-to-Feedback); same for `"2"`, `"5"`, etc. `clause_seeder.py` assigned
  `clause_id` = the raw section number without namespacing by `source_doc`, so a
  citation of "clause 5" is ambiguous across six chapter-5s. Fix: namespace
  `clause_id` (e.g. `{source_doc}::{clause_id}`) or include `source_doc` in the
  citation.

- **FINDING 3 — Short-id substring over-linking floods the coarse anchors.**
  `ClauseLinker` links via substring-ish matching, so short chapter ids act as
  magnets: `clause "1"` ← **1,471 chunks**, `"2"` ← 1,383, `"5"` ← 1,087, while
  the specific leaf `"10.1.1"` ← only 12. Average **45.9 clauses linked per
  chunk, max 217**; 85,269 `LINKED_TO` edges total. Consequence: the leaf clause
  the answer needs (e.g. `5.7.2`, which *does* exist in the graph) is buried
  under the content-empty chapter anchor (`5`) it shares a prefix with. This
  also inflates retrieval pools to 1,880–2,391 docs/case (→ ~20 min/case rerank
  latency). Fix: exact/boundary clause-id match only, link to the most specific
  clause, drop/de-prioritize chapter-level anchors as citation targets.

- **FINDING 4 — The RAGAs metrics in these runs are rate-limit-corrupted and
  must not be trusted as-is.** RAGAs LLM calls hit OpenRouter 429s (2 of 3 jobs
  failed on B01). Tell-tale: `context_precision` = `0.9999999999666667` appears
  BYTE-IDENTICAL across B01 and B02 in the killed multi-case run (a degenerate
  default), whereas the completed single-case B01 rerun computed precision =
  0.00. So `context_recall`/`precision`/`faithfulness` from the multi-case run
  are unreliable; only the deterministic citation-id evidence and the rubric
  judge are trustworthy. Fix: throttle/batch RAGAs judge calls (or add backoff)
  before the A/B, else the A/B is measured with a broken ruler.

- **FINDING 5 — Per-case score instability.** B01-001 scored 0.111 (killed
  multi-case run) vs 0.44 (single-case rerun) — same case, same mode. Generation
  temperature + judge variance (compounded by Finding 4). The ontology-vs-
  baseline delta may sit inside this noise band. Fix: temp 0 for the A/B or
  multi-seed averaging.

- **FINDING 6 — Systematic "hedge instead of decide" in the generator.** Across
  B01–B03 (scenario questions) the model gave a verdict in 0/3 — it emits a
  canned "Summary of Key Points" of CCoP admin trivia instead of answering
  yes/no/it-depends. Every GT expected answer gives a crisp verdict. This is a
  generation/prompt failure independent of retrieval (B02 had a real question,
  no verdict). Fix: prompt guard — answer the verdict first, grounded in
  retrieved clauses; say "insufficient context" rather than dumping general
  knowledge.

- **FINDING 7 (GT quality) — B02-001 question/GT clause mismatch.** The question
  asks about "Clause 5.1.5 multi-factor authentication" but the GT expected
  answer cites §5.7.2(b) for MFA. Flag for the ground-truth audit (`/gt-audit`).

- **FINDING 8 — No dedup anywhere in the retrieve→rerank path; the
  cross-encoder scores 1,880 mostly-duplicate rows and the top-3 collapse to a
  single chunk. (Code-level locus of Findings 1 & 3.)** Settings in play:
  `rag_retrieval_top_k=50`, `rerank_top_n=3`, `rag_merge_parent_enabled=True`,
  cross-encoder `BAAI/bge-reranker-large`, `function_type_boost=1.5`. Trace:
  - `graph_retrieval_node.py:95` → `provider.retrieve(query, top_k=50, function_type)`.
  - Adapter `neo4j_ontology_graph_retrieval_adapter.py:208` →
    `HybridCypherRetriever.search(top_k=50)`. `top_k=50` bounds only the
    vector+fulltext index pre-fetch (~50 fused chunks); the custom
    `RETRIEVAL_QUERY` (line 108) then `OPTIONAL MATCH (chunk)-[:LINKED_TO]->(c:Clause)`
    fans each chunk into one row per linked clause and has **no final `LIMIT`**
    → ~50 × ~37 = **1,880 rows** (matches the "returned 1880 documents" log).
    `graph_retrieval_node` sets all 1,880 as `state["documents"]` by design
    ("the reranker owns the final top-N").
  - `reranking.py::rerank_documents` builds `pairs = [(query, doc.page_content)
    for doc in documents]` and runs `bge-reranker-large` on **all 1,880**
    (lines 85–91) — a heavy cross-encoder, most inferences redundant (identical
    `page_content`); a big share of the ~20 min/case cost. Identical chunk texts
    → identical CE scores → they cluster; RRF (dense_rank+ce_rank) tie-breaks by
    tiny dense_rank deltas so they stay adjacent.
  - The **parent-child merge** (enabled) groups by `parent_path_of(citation_id)`
    (line 139), but bare chapter ids `1`/`10`/`11` have no dotted parent → each
    is its own parent → **no merge fires**; and it merges by clause parent-path,
    **not by chunk identity**, so it structurally cannot collapse "same chunk
    under different clause labels."
  - `top_docs = scored_for_topn[:rerank_top_n]` (=3) → the top-3 are **3
    adjacent rows of the SAME chunk** (B01: `1/10/11`, byte-identical text).
    **No dedup step exists at any stage.**
  Fix locations (any one breaks the duplication; source-most preferred):
  1. **`RETRIEVAL_QUERY` (adapter:108)** — collapse to **one row per chunk** at
     the source: aggregate linked clauses per chunk, pick the single best
     (most-specific, boosted) `clause_id` as citation, add `LIMIT $top_k`.
     Eliminates the 1,880 explosion AND the ~37× redundant CE calls. Best.
  2. **`graph_retrieval_node.py` (after line 95)** — dedup returned Documents by
     chunk identity before the reranker (requires the adapter to also RETURN
     `elementId(chunk)` so dedup keys on the true chunk, not text).
  3. **`reranking.py` (before line 85)** — dedup `documents` by `page_content`
     (or chunk id), keeping the best-ranked instance, before CE scoring.
     Furthest downstream; also protects hybrid mode if it ever fans out.
  Note: even after dedup the top-3 are 3 **distinct coarse chunks** — still not
  clause-grained (Finding 1). Dedup + `LIMIT` is necessary but not sufficient;
  pair with giving `:Clause` nodes real text.

**Net implication for the A/B:** the ontology leg should NOT be reported as a
fair result until Findings 1–4 are addressed. Findings 1–3 are upstream data-
model bugs (`clause_seeder.py` + `clause_linker.py`), Finding 4 is a harness
reliability bug. Reporting the A/B now would measure a mislabelled, coarse
retrieval layer with a corrupted metric — understating the approach's real
capability (B04, the one case with a specific clause anchor, was the only real
answer). Recommend a fast-follow fix plan before the full 18-case A/B.
