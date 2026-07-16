---
phase: 12-agentic-graphont-retrieval-quality-loop
slice: A0
type: analysis
status: draft
author: scout (recon, read-only)
date: 2026-07-13
depends_on: ["12-02-PLAN.md §7, §8.0, §9 steps 1-2", "ADR-008", "ADR-009"]
code_changes: none
---

# Phase 12 Slice A0 — Signal Inventory, Retrieval-Path Recon, Baseline Measurement Approach

**Scope note:** This document is pure analysis. No code was modified. All line references are
against the current `HEAD` of the files listed, verified 2026-07-13 (git log tip for the relevant
files: `e3339b8 feat(graphont): OMD-GraphRAG retrieval mode — tri-channel + rerank + definitions`).

---

## 1. Signal inventory table (Deliverable 1, plan §7)

Legend — **Available today?**: does the value currently get *computed* anywhere in the live
`graphont` code path (even if immediately discarded). **Persisted to GraphState?**: does any node
write it into `GraphState` (i.e. survives past the node that computed it). **Runtime-cheap?**:
deterministic and cheap enough to gate on inside the request path (no extra LLM call, no extra
DB round-trip beyond what's already made). **Causal availability**: pre-generation (computable
before `generate` runs) or post-generation (only knowable after the model responds).

| Signal | Source file (function) | Available today? | Persisted to `GraphState`? | Runtime-cheap? | Pre- vs post-generation |
|---|---|---|---|---|---|
| `retrieval_succeeded` (hard sentinel) | `omd_context_assembly.py:91` (`bool(docs)`) | Yes — computed | **Yes** — written to `state["retrieval_succeeded"]` | Yes (already computed) | Pre-generation |
| Empty / near-empty candidate pool | `omd_retrieval.py:retrieve()` — `d_cand = len(rrf)` (~line 401, 424) | Yes — computed inside `retrieve()`'s return dict `out["d_cand"]` | **No** — `omd_context_assembly.py` reads `out.get("d_cand", 0)` only for a log line (docstring/comment "for logging"), never assigns to `state[...]` | Yes (already computed, just needs a state write) | Pre-generation |
| Rank-normalized bi-encoder (dense) score distribution | `omd_retrieval.py:channel_dense()` (~line 327) → `out["dense"]` list of `(cid, cosine)` | Yes — full per-candidate list returned by `retrieve()` | **No** — discarded; `omd_context_assembly.py` only pulls `r.get("score")` (the *fused* score) per selected doc, not the raw per-channel dense scores | Yes (already computed) | Pre-generation |
| Rank-normalized cross-encoder (CE) score distribution | `omd_retrieval.py:rerank()` (~line 337) → `ce_score` dict inside `retrieve()` | Yes — computed for every candidate in the RRF union when `do_rerank=True` | **No** — only the winning top-8's `ce_score` survives into `out["results"]`; full-pool CE distribution (needed for stdev/margin/entropy features) is not returned or persisted | Yes (already computed for the full pool internally, just not exposed) | Pre-generation |
| Top-1/top-k margin & entropy, conditioned on pool size | Not computed anywhere | **No** | No | Would be cheap to derive from CE/RRF distributions above once persisted | Pre-generation |
| Cross-channel agreement/disagreement (`graph` vs `bm25` vs `dense`) | `omd_retrieval.py:retrieve()` — `ch1_by`, `bm_by`, `dn_by` dicts (per-candidate per-channel scores), lines ~405-410 | Yes — computed internally as part of `_rec()` (each result record already carries `ch1`, `bm25`, `dense` sub-scores, ~line 415-419) | **Partially** — this breakdown exists on `out["results"]` records but `omd_context_assembly.py` does not copy `ch1`/`bm25`/`dense`/`rrf` fields into the `Document.metadata` it builds (`_doc()`/`_def_doc()` only keep `citation_id`, `document_source`, `section`, `similarity_score`) — so it's computed but dropped at the state boundary | Yes (already computed) | Pre-generation |
| Candidate count before/after rerank | `omd_retrieval.py:retrieve()` — `d_cand` (pre-rerank pool size) vs `len(out["results"])` (post-rerank, capped at `k=8`) | Yes — both values exist in the return dict | **No** — neither written to `GraphState`; `omd_context_assembly.py` only logs `len(docs)` (post) | Yes | Pre-generation |
| Query concept/entity coverage | `omd_retrieval.py:query_to_concepts()` (~line 178) → `Q` list; `expand()` → `Qplus` | Yes — computed, returned as `out["query_concepts"]` and `out["expanded"]` | **No** — `omd_context_assembly.py` never reads `out["query_concepts"]`/`out["expanded"]`; not written to state | Yes (already computed; note: involves one GPT-4o-mini call via OpenRouter inside `query_to_concepts()`, so not "free," but it's already paid for in every graphont request today) | Pre-generation |
| Query **relation** coverage (typed relationship coverage, not just concept nodes) | Not computed — `query_to_concepts()` maps only to `:Concept` nodes, no relation-type classification step exists | **No** | No | Would need new logic — not free | Pre-generation |
| Source/section/clause-family/document diversity of retrieved set | Not computed as a metric; raw material (`doc` field per candidate, `citation_id` prefix before `::`) exists in `_passages()` and per-result records | Partially — raw fields exist, diversity metric itself not computed | **No** | Would be cheap to derive (Counter over `doc` field) from data already in `out["results"]` once persisted | Pre-generation |
| Whether retrieved clauses form a connected, query-aligned subgraph | Not computed — `channel1()` scores clauses independently; no post-hoc connectivity check over the selected top-8's underlying concept sets | **No** | No | Would need new graph-traversal logic — not free (Neo4j round-trip per check) | Pre-generation |
| Provenance-text availability (verbatim clause text present for map-back) | `_passages()` (~line 214) always hydrates `text` from the unified passage store; `_rec()` always includes `"text": p.get("text", "")` | Yes — always true for `:Clause`/`:Definition` nodes today (no graph-only, summary-only nodes exist yet in `graphont`) | **Yes** — the `text` ends up in `Document.page_content` via `_doc()`/`_def_doc()` | Yes (trivially true today; becomes a real signal only once Slice E graph-expansion introduces non-verbatim graph paths) | Pre-generation |
| Exact/rare-term coverage (clause numbers, regulator names, deadlines) | `omd_retrieval.py:channel2()` BM25 (~line 250) implicitly weights rare terms via IDF (`_build_bm25()`'s `idf` dict), but no explicit "did the query's exact clause-number / rare-term appear in top results" check exists | Partially — BM25 IDF machinery exists and could be probed | **No** | Cheap to derive post-hoc from `_BM25["idf"]` + query tokens once exposed | Pre-generation |
| `ce_confidence` (CE score stdev vs `RERANK_CONF_REF`) | `omd_retrieval.py:retrieve()` (~line 431-433, `conf = min(statistics.pstdev(...) / rerank_conf_ref, 1.0)`) | Yes — computed, returned as `out["ce_confidence"]` and folded into `out["ranked_by"]` label (e.g. `"ce+rrf(conf=0.42)"`) | **No** — `omd_context_assembly.py` logs `out.get("ranked_by")` (string) but never persists the numeric `ce_confidence` to `GraphState` | Yes (already computed every call) | Pre-generation |
| `ranked_by` label (which fusion strategy actually fired: `"rrf"` vs `"ce+rrf(conf=X)"` vs `"none"`) | `omd_retrieval.py:retrieve()` return dict | Yes | **No** — logged only, not persisted | Yes | Pre-generation |
| Injected-definitions count/coverage | `omd_retrieval.py:inject_definitions()` → `out["definitions"]` | Yes | **Partially** — the definitions themselves DO end up in `filtered_documents` (as `Document` objects via `_def_doc()`), but the *count relative to query concepts* (i.e. "how many of the N query concepts got a definition") is not persisted as a discrete signal | Yes | Pre-generation |
| ~~Final generated citations present in retrieved context~~ | `src/rag/citations/resolver.py:build_citations_from_state()` — parses `state["generation"]`'s `**Sources:**` footer | Yes — computed after `generate` | **Yes** — `state["citations"]` | N/A — **excluded from runtime detector per ADR-009**; only knowable after `generate` runs | **Post-generation** — confirmed correctly excluded from Tier 1/Tier 2 candidate signal list per plan §7 "Removed from runtime" |

### Summary of the signal-inventory finding

The single biggest fact this table establishes: **almost every signal in plan §7's candidate list
is already computed inside `omd_retrieval.py:retrieve()`'s internals, but `omd_context_assembly.py`
(the only consumer) discards nearly all of it at the state boundary.** Only 3 of ~15 candidate
signals reach `GraphState` today (`retrieval_succeeded`, verbatim provenance text via
`page_content`, and the fused per-candidate `similarity_score`). The rest — `d_cand`,
`ce_confidence`, `ranked_by`, per-channel (`ch1`/`bm25`/`dense`/`rrf`) sub-scores,
`query_concepts`/`expanded`, definitions-coverage — are all live values inside `retrieve()`'s
return dict (`out`) that `omd_context_assembly.py` either logs-and-drops or never touches at all.
This means Slice A0's signal-availability question has a clean answer per signal (see table), and
**Slice C's detector will need at minimum a state-persistence change** (not a retrieval-logic
change) to have these signals available at decision time — this is the "minimal export hook" this
report flags below (§4) as unavoidable but NOT implemented here.

---

## 2. Current retrieval-path inventory (Deliverable 2, plan §9 step 1)

Re-verified against current code (all five files read in full for this task).

### 2.1 Node/edge flow for `mode="graphont"`

```
query_analysis (nodes/query_analysis.py)
  - reads: state["query"], state["mode"]
  - writes: state["needs_retrieval"]=True; state["rewritten_query"]=query (unchanged copy —
    HyDE is explicitly gated to mode in ("hybrid","rag-only") only, graphont never gets HyDE);
    state["hyde_query"]=""
  |
  v  route_by_mode(state)  [edges/routing.py:41-46]
  "graphont" -> returns "omd_context_assembly"
  |
  v
omd_context_assembly (nodes/omd_context_assembly.py)
  - mode-gated: `if state.get("mode") != "graphont": return state` (line ~40) — no-op passthrough
    for every other mode, confirming additivity
  - reads: state["query"]
  - calls: rag.graph.ontology_v2.omd_retrieval.retrieve(question, k=8)  [_TOP_K=8, line 27]
  - writes: state["filtered_documents"]=docs; state["documents"]=docs;
    state["is_rag_augmented"]=True; state["retrieval_succeeded"]=bool(docs)
  - degrade-safe: any exception inside the try/except -> docs stays [] -> empty context,
    no crash, no error propagated to state["error"] (silent-empty behavior, see §2.3 below)
  |
  v  workflow.add_edge("omd_context_assembly", "generate")  [graph.py:136]
  (bypasses "retrieval" / "reranking" / "grade_documents" / decide_after_grading entirely —
   graphont is the ONLY live mode whose retrieval node edges directly to generate with no
   shared-node pass-through)
  |
  v
generate (nodes/generation.py) — SAME node used by hybrid/graphcpl, no mode branching inside it
  - reads: state["query"], state["filtered_documents"]
  - writes: state["generation"], state["raw_generation"], state["is_rag_augmented"] (re-set True),
    state["citations"] (via citations/resolver.py parse of the model's own **Sources:** footer),
    state["system_prompt"], state["user_prompt"], token/latency fields,
    state["retrieved_contexts_detailed"] (built from filtered_docs metadata BEFORE the LLM call,
    generation.py:151-161)
  |
  v END
```

### 2.2 Retrieval outputs (what `omd_retrieval.retrieve()` actually returns, vs what survives)

`retrieve()` (`src/rag/graph/ontology_v2/omd_retrieval.py`, function starts ~line 366) returns a
dict with keys: `query_concepts`, `expanded`, `definitions`, `channel1`, `channel2`, `dense`,
`d_cand`, `ranked_by`, `ce_confidence`, `results`. Of these, `omd_context_assembly.py` (the sole
caller in the live pipeline) reads only:
- `out.get("definitions", [])` → converted to `Document` objects (kept)
- `out.get("results", [])` → converted to `Document` objects (kept, but only `text`,
  `citation_id`, `doc`, `score` survive per result — `ce_score`, `rrf`, `ch1`, `bm25`, `dense`
  sub-fields on each result record are dropped)
- `out.get("ranked_by")`, `out.get("d_cand", 0)` → used **only** in a `logger.info(...)` call
  (line ~83-86), never assigned to state

Everything else (`query_concepts`, `expanded`, `channel1`, `channel2`, `dense` raw lists,
`ce_confidence`) is computed and immediately discarded when `retrieve()` returns and
`omd_context_assembly.py`'s local `out` variable goes out of scope at function return.

### 2.3 Empty-retrieval behavior

- If `retrieve()` raises (e.g. Neo4j down, dense index missing, OpenRouter timeout inside
  `query_to_concepts()`) → caught by the bare `except Exception as e` in `omd_context_assembly.py`
  → logged as a `logger.warning`, `docs` stays `[]`.
- If `retrieve()` succeeds but the RRF union is empty (`if not rrf: return {...,"results": []}`,
  `omd_retrieval.py` ~line 396-400) → `docs` stays `[]` (no definitions either, since
  `inject_definitions()` is only skipped if `Q` itself is empty, not if `rrf` is empty — actually
  definitions ARE still possible with empty clause results, since definitions come from `Q`
  independent of the RRF pool).
- Either way: `state["retrieval_succeeded"] = bool(docs)` → `False` if `docs == []`.
- **Critically**: `decide_after_grading` (the shared conditional edge that would normally route an
  empty-retrieval hybrid case to `fallback`) is **never reached** for graphont — the edge
  `omd_context_assembly -> generate` is unconditional (`workflow.add_edge`, not
  `add_conditional_edges`). So an empty-retrieval graphont case still proceeds straight to
  `generate` with `filtered_documents=[]` and gets a context-free "no grounding" answer from
  Primus, with no fallback branch, no retry, no explicit "insufficient evidence" outcome. This is
  the literal current behavior the plan's `assess_retrieval_quality` gate (§8.3) and `empty`
  runtime grade are meant to intercept.

### 2.4 Hidden/discarded signals — consolidated list

Confirms §1's findings in flow terms: `d_cand`, `ranked_by`, `ce_confidence`, per-channel
(`ch1`/`bm25`/`dense`) sub-scores on each result, `rrf` scores per candidate, `query_concepts`,
`expanded` (1-hop concept set) — all computed inside `retrieve()`, all discarded before reaching
`GraphState`. None of these appear in any of: `GraphState` TypedDict, the `-contexts.json`
sidecar, or the `retrieved_contexts_detailed` field built by `generate` (which only round-trips
`Document.metadata`, itself already a lossy projection of `out["results"]`).

### 2.5 `GraphState` schema — graphont's actual read/write footprint

Re-verified against `src/rag/retrieval/state/graph_state.py` (89 lines, unchanged since earlier
recon — confirmed no drift). Graphont touches:
- **reads:** `mode`, `query`
- **writes:** `filtered_documents`, `documents`, `is_rag_augmented`, `retrieval_succeeded`
- **left at `create_rag_pipeline()`'s initial defaults** (never overwritten by graphont's own
  nodes): `rewritten_query` (set to a no-op copy by `query_analysis`, not graphont-specific),
  `hyde_query`, `dense_ranks`, `rrf_scores`, `merged_groups`, `reranker_scores`,
  `grading_scores`, `retrieval_attempts`, `function_type`, `context_graph_triples`, `anchors`,
  `hypernym_mappings`, `cu_plan`, `verbatim_clause_texts`. None of these fields are graphont-aware;
  they belong to other modes (`hybrid`'s Exp#41 fields, `graphcpl`'s Context Graph fields). This
  confirms the plan's §9 step 7 intent: Phase 12 needs **new** state fields
  (`retrieval_trace`, `retrieval_grade`, `retrieval_grade_reasons`, `should_requery`,
  `requery_count`, `requery_action`, `retrieval_overrides`, `pre_retry_summary`,
  `post_retry_summary`, traversal-provenance fields) — none of the existing unused fields can be
  repurposed without risking cross-mode confusion.

---

## 3. Baseline retrieval measurement approach (Deliverable 3, plan §9 step 1 baseline + §8.0)

### 3.1 Existing instrumentation, checked first (per instruction)

**`--verbose-io` / `-contexts.json` sidecar**
- Wiring: `presentation/cli/commands/evaluate.py:69-71` (CLI flag) →
  `infrastructure/adapters/repositories/json_result_repository.py:77-79` (sidecar writer, only
  emitted `if contexts_by_test_id` is provided).
- **Content actually captured** (verified by reading a real sidecar,
  `eval-run-graphont-test-B05-001-20260709-1036-contexts.json`): a list per test_id of the
  **final packed `Document` objects** graphont produced — `text`, `citation_id`, `section`
  (hardcoded to `"Clause (OMD-GraphRAG)"`/`"Definition (...)"` string, not the real source
  document split out), `document="OMD-GraphRAG"` (constant, not per-doc source), and the single
  **fused** `score` (whatever `_rec()`'s `score` field held — CE+RRF fused value or raw RRF).
  **No `ce_confidence`, no `d_cand`, no `ranked_by`, no per-channel (`ch1`/`bm25`/`dense`)
  breakdown, no `query_concepts`, no `rrf` raw score.** This is exactly the lossy projection
  identified in §2.2 — the sidecar is downstream of `retrieved_contexts_detailed`, which is
  downstream of `Document.metadata`, which is downstream of `omd_context_assembly.py`'s already-lossy
  read of `out`.
- **Existing 18-case calibration-candidate runs found**: two prior `graphont` runs already exist
  on the `tests-18-bdc4927d` stratified set —
  `eval-run-graphont-tests-18-bdc4927d-20260709-1050-primus-reasoning.partial.jsonl` and
  `...-1212-...partial.jsonl` — **but neither was run with `--verbose-io`**, so no
  `-contexts.json` sidecar exists for either (confirmed: `find src/results -iname
  "*graphont*18*contexts*"` → zero results). Several single-case (`B01-001`, `B05-001`) ad-hoc
  runs from earlier development DO have sidecars, useful as worked micro-examples but not a
  calibration set.

**`--verbose` / `rag.retrieval.*` logs**
- Wiring: `presentation/cli/commands/evaluate.py:74-95` — raises pipeline logger level to `INFO`
  for `rag.retrieval.*` loggers.
- `omd_context_assembly.py`'s logger (`logging.getLogger(__name__)` = `rag.retrieval.nodes.omd_context_assembly`)
  emits one `INFO` line per call: doc count, clause/definition split, `ranked_by`, `d_cand`
  (line ~93-96) — a human-readable summary, not structured/parseable, and still only a subset
  (no `ce_confidence` numeric value, no per-candidate breakdown, no `query_concepts`).
- `omd_retrieval.py`'s own logger (`rag.graph.ontology_v2.omd_retrieval`) only fires a `WARNING`
  on reranker failure (line ~435) — no `INFO`-level trace of retrieval internals in the live
  pipeline path. (The rich diagnostic printout in `omd_retrieval.py`'s `if __name__ ==
  "__main__":` block — channel1/channel2/dense top-10 printouts — is CLI-debug-only code, never
  invoked from the LangGraph pipeline.)

### 3.2 Conclusion: does existing tooling suffice?

**No — not for the full signal set the plan requires, but partially sufficient for a narrower
baseline measurement.**

- **`clause-hit@k` / `recall@pool` against GT `clause_reference`** (the plan's §8.0 core
  requirement): **can be computed today with zero code changes**, using the existing
  `-contexts.json` sidecar (`citation_id` field per retrieved doc) joined against each test
  case's `ground_truth.metadata.clause_reference` array (verified format via
  `ground-truth/test-suite/b05_control_comprehension.jsonl` — e.g.
  `["RESPONSE-TO-FEEDBACK 11.28", "5.9.2(b)"]`, needing a citation-id-normalization join since
  sidecar `citation_id` uses `"CCoP Response to Feedback::11.28"`-style `Doc::clause` strings
  while GT uses `"RESPONSE-TO-FEEDBACK 11.28"`-style space-separated short names — a normalization
  mapping, not new pipeline code). **Path: re-run the stratified 18-case set with `--verbose-io`
  enabled** (a CLI-flag-only re-run, not a code change) to get a fresh sidecar, then compute
  recall metrics as a standalone offline analysis script (also not a pipeline code change — an
  analysis script lives outside `src/rag/` and doesn't touch the mode-gated code ADR-008/009
  protect).
- **The richer signal-separability analysis Slice A/C need** (`ce_confidence`, `d_cand`,
  per-channel agreement, `query_concepts` coverage, etc. — §1's "available today but discarded"
  rows): **existing tooling does NOT suffice.** These values live and die inside a single call to
  `omd_retrieval.retrieve()` and are never written anywhere (not state, not the sidecar, not logs
  in structured form). No re-run with existing flags will surface them — they are discarded
  before `omd_context_assembly.py` returns, regardless of `--verbose`/`--verbose-io` settings.

### 3.3 Recommended baseline-measurement approach for A0, staged by what needs code vs not

**Stage 1 — zero code (do this first, satisfies the plan's baseline-number requirement):**
1. Re-run `poetry run ccop-eval evaluate run --model primus-reasoning --mode graphont --test-ids
   B01-001 [...all 18 stratified test-ids] --verbose-io` (CLI flags only) to produce a fresh
   `-contexts.json` sidecar for the full 18-case stratified set.
2. Write a standalone offline analysis script (outside `src/rag/`, e.g. under a `scripts/` or
   `notebooks/` location, reading the sidecar + `ground-truth/test-suite/*.jsonl` — this is
   analysis tooling, not pipeline code, and does not touch any ADR-008/009-protected file) that:
   - normalizes GT `clause_reference` strings to the sidecar's `Document::clause` citation_id
     format (both are string identifiers derived from the same source documents, so this is a
     lookup-table/regex normalization, not new retrieval logic)
   - computes `clause-hit@k` (was ≥1 GT clause in the top-k retrieved) and `recall@pool` (fraction
     of GT clauses present anywhere in the retrieved pool) per test case and aggregated
   - This yields the plan's required "baseline recall numbers" deliverable with **zero changes to
     any file the plan's `files_expected` or ADR-008/009 constrain.**

**Stage 2 — the minimal export hook (NOT implemented here; flagged per instructions, §4 below):**
Needed only for the deeper signal-separability work in Slice A (development/validation split
signal analysis) and Slice C (detector design), not for A0's baseline recall number. This is
explicitly out of scope for A0 to write.

---

## 4. Explicit flag: minimal export hook (proposal only, NOT written)

Per the coordinator's instruction ("if a minimal export hook is unavoidable, FLAG it explicitly
and DO NOT write it"): **a minimal hook is unavoidable for the Slice A/C signal-separability
analysis (not for A0's own baseline-recall deliverable, which Stage 1 above covers with zero
code).** Proposal, for future approval — **not implemented, no file touched**:

- **What:** in `omd_context_assembly.py`, after calling `omd_retrieval.retrieve(...)`, add a
  **read-only, additive** capture of the full `out` dict (minus large text blobs already available
  via `page_content`) into a **new** `GraphState` field, e.g. `state["retrieval_trace"] = {
  "query_concepts": out.get("query_concepts"), "expanded": out.get("expanded"), "d_cand":
  out.get("d_cand"), "ranked_by": out.get("ranked_by"), "ce_confidence": out.get("ce_confidence"),
  "per_candidate": [{"citation_id": r["citation_id"], "rrf": r["rrf"], "ch1": r["ch1"], "bm25":
  r["bm25"], "dense": r["dense"], "ce_score": r.get("ce_score")} for r in out.get("results", [])]
  }`.
- **Why additive/safe:** new dict key on `GraphState`, mode-gated exactly like the existing
  `filtered_documents`/`documents` writes (`if state.get("mode") != "graphont": return state`
  guard already present); does not alter `filtered_documents` construction, candidate order, or
  the packed context/generation prompt in any way — pure side-channel telemetry, zero behavior
  change to `graphont`'s existing generation path. This satisfies ADR-009's parity requirement
  (candidate order → packed context → generation prompt stays byte-identical) since the hook only
  *adds* a state key, never reads or reorders `docs`.
- **Why NOT written now:** still a code change to a `files_expected` file
  (`omd_context_assembly.py`) under this plan; per the coordinator's explicit "plan-approval
  posture" instruction, this must be approved before implementation, not written speculatively
  during a read-only A0 pass.

---

## 5. Constraint compliance confirmation

- **Zero files modified.** Only this new analysis file was written (`.planning/phases/...`), plus
  read-only `Read`/`Bash` (grep/find/head/python3 -c json.load) commands against existing files.
- **`mode=graphont` untouched** — no edits to `graph.py`, `routing.py`, `omd_context_assembly.py`,
  `omd_retrieval.py`, or `graph_state.py`.
- **No corpus/index changes** — no Qdrant or Neo4j writes; all reads were local file/JSON
  inspection.
- **No new nodes, no routing changes** — confirmed by re-reading `graph.py`/`routing.py` against
  the current commit; matches the state documented in the earlier TASK 1 recon with no drift.
- Proposed minimal export hook (§4) is a **proposal only**, explicitly not implemented.
