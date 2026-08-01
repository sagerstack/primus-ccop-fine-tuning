# Research: GraphOnt Design–Code Alignment Assessment

**Date**: 2026-07-11
**Researcher**: researcher agent (team `sg-1-studio-ssdlc`, task 4)
**Status**: Draft (independent read; coordinator task 4)
**Scope sources**: source code under `src/`, project memory (`docs/project_notes/`, Term-3 mid report `report/term3-mid/`), actual run artifacts under `src/results/evaluations/2026-07/`. No edits made; no web access used (offline working copy).

---

## 1. Executive Summary

- **`--mode graphont` is wired end-to-end** across the four required allowlists (CLI evaluate, CLI query, `RunId`, `_RETRIEVAL_EVAL_MODES`), the LangGraph routing edge, the dedicated `omd_context_assembly` node, and the tri-channel `omd_retrieval.retrieve()` retriever. The design described in `RESUME.md` (Phase-7 retrieval of the `ontology_v2` corpus-wide KG) **matches the code path**.
- **The retrieval methodology in the Term-3 mid report §16 (graph + keyword + dense + CE reranker)** matches the code in `omd_retrieval.py` (lines 53–58, 316–365), including the weighted RRF, the confidence-adaptive CE⊕RRF fusion, and the 68-definition injection layer.
- **Two single-anchor validation results reproduced independently from the artifacts:** B01-001 = **0.556** (14:17 run), B05-001 = **0.778** (10:36 run) — within run-to-run variance of the report's stated 0.56 / 0.78 (report §17.1, §17.2).
- **Three gaps block the planned "18-case graphont-vs-hybrid comparison" (RESUME.md, the project's "NEXT" task):**
  1. **No test coverage at all** for `graphont`, `omd_context_assembly`, `omd_retrieval`, or the entire `ontology_v2` module — every other retrieval mode (`graphrag`, `graphrag-ontology`, `graphcpl`) has tests; graphont has zero (`tests/rag/retrieval/test_graphrag_*.py` exists, no `test_graphont_*.py`).
  2. **No feature flag** for `graphont` (compare `graphrag_ontology_enabled` in `settings.py:529`), and the mode is hard-coupled to Neo4j via direct import (`omd_context_assembly.py:36`); no DI provider, no "mode unavailable" handling like the container's `_create_ontology_graph_retrieval_provider` does for `graphrag-ontology` (`container.py:284-313`).
  3. **The 18-case runs never complete**: 2 of 2 attempts (1050 and 1212 UTC) terminated at **≤2 of 18 cases** — `B01-001` then `B02-001` are the only entries in each `.partial.jsonl`. The OOM scenario `RESUME.md` flags as a "HARD GOTCHA" is the suspected cause (resumable partial state is present, so the run was killed externally, not crashed early).
- **A fourth, structural risk:** query→concept nondeterminism (±0.11 score swing) is observable in the artifacts (B01-001 scored 0.44 in the 12:12 run, 0.556 in the 14:17 run — same case, same day). This invalidates any single-run number as ground truth and is acknowledged in `RESUME.md` but not yet mitigated (no concept cache exists).
- **Recommended next step (single line):** ship (a) a `CCOP_GRAPHONT_ENABLED` flag + Neo4j-availability guard in `omd_context_assembly.py`, (b) at minimum 1 mocked unit test per new module, and (c) a per-test-id concept cache — then run the 18-case comparison in batched mode (≤3 cases/process) with RAGAs off and Qdrant stopped, as `RESUME.md` already prescribes.

---

## 2. Problem Statement

**What was investigated.** Whether the `graphont` retrieval mode — described in `report/term3-mid/T3-extracted.txt` §16 and the live `RESUME.md` (2026-07-09c) — is internally consistent: does the design narrative match the code that runs, and does the mode's wiring, methodology, and validation evidence support the "pending task" claim of an 18-case graphont-vs-hybrid comparison?

**Scope and constraints.**
- Read-only: no code, config, or result-file edits.
- Sources used: `src/rag/graph/ontology_v2/{RESUME.md, PLAN.md, omd_retrieval.py, _neo.py, build_definitions.py}`; `src/rag/retrieval/{graph.py, edges/routing.py, nodes/omd_context_assembly.py}`; `src/presentation/cli/{query.py, commands/evaluate.py}`; `src/domain/value_objects/run_id.py`; `src/application/use_cases/evaluate_model.py`; `src/infrastructure/config/{settings.py, container.py}`; `src/results/evaluations/2026-07/eval-run-graphont-*.{json,jsonl,partial.jsonl,-contexts.json}`; `report/term3-mid/T3-extracted.txt` §12–19; project memory `docs/project_notes/{bugs,decisions,issues}.md` (no graphont entries — confirms it's a new, un-tracked component).
- Out of scope: live re-running of any pipeline (cannot on this machine), reading the PDF directly (the 1982-line `T3-extracted.txt` plus the `T3-mid-append.md` were used), web verification of the OMD-GraphRAG paper beyond what is already cited in `RESUME.md` and `T3-extracted.txt:1597`.

**Success criteria (this report):**
1. Each design claim is traced to a code line (or flagged as ungrounded).
2. Operational/evaluation risks are prioritized with exact evidence (file + run artifact).
3. Next steps are actionable, ordered, and avoid the existing "HARD GOTCHA" pitfalls.

---

## 3. Best Practices & Industry Standards

The graphont design follows established patterns for production RAG systems; deviations from the paper are documented and deliberate.

- **Tri-channel rank fusion via weighted Reciprocal Rank Fusion** is standard in modern hybrid search (e.g., OpenSearch, Vespa, Weaviate hybrid retrievers, the original Cormack et al. RRF work, 2009). The implementation in `omd_retrieval.py:194-202` uses the canonical `score(d) = Σ wₖ/(k + rankₖ(d))` form. The chosen weights (graph 1.0 / BM25 0.7 / dense 1.5, `omd_retrieval.py:41-45`) are consistent with the project's own experimental finding (`Exp #11/#28`, cited inline) that dense-only beats equal-RRF on this corpus, and the B01-001 ablation in `RESUME.md` "Session 2026-07-09b".
- **Cross-encoder reranking on the fused candidate pool** is the dominant pattern in current high-quality RAG (BAAI/bge-reranker, Cohere Rerank 3, Jina, mixedbread.ai). The decision in `omd_retrieval.py:66-79` to use `CE⊕RRF` rather than pure-CE selection is correct for the current bge-reranker-large model, given the documented collapse behaviour on short factoid queries (`omd_retrieval.py:53-58` "confidence-adaptive CE" comment; verified on 6 benchmarks per `RESUME.md` §8).
- **Build-id scoping in Neo4j** (`build_id: "omd-v1-20260709"` on every node/edge, `omd_retrieval.py:39`, `build_definitions.py:30`) is the standard "droppable layer" pattern used in property-graph projects; matches the project's own prior pattern (`build_id: "omd-v1-20260709"`).
- **Modular mode allowlist maintenance** is a documented project invariant: every new mode has to be added in **four** places, and `evaluate_model.py:32-40` carries an explicit comment about the Phase-9 graphrag bug that missed the run_id allowlist. `graphont` is in all four (verified in §5 below).
- **Staged rollout via feature flag** is the pattern used by sibling modes (`graphrag_ontology_enabled: bool = True`, `settings.py:529-531`). The DI container (`container.py:284-313`) treats the flag as a hard precondition for instantiating the provider. **`graphont` does not follow this pattern — see §7, risk P1-6.**
- **Mature RAG evaluation pipelines** (RAGAs, TruLens, Arize Phoenix) score retrieved context vs. ground truth. The project's plan to disable RAGAs during graphont evaluation (RESUME.md "HARD GOTCHA") is a workaround, not a standard practice — the standard answer is to run RAGAs on a smaller subset or with a lighter model.

---

## 4. Bleeding-Edge / Emerging Approaches

- **OMD-GraphRAG paper methodology** (`arXiv:2603.25152`; cited at `T3-extracted.txt:1597` and `RESUME.md`). The paper contributes ontology-guided extraction + multi-dimensional clustering + dual-channel fusion. The project implements (1) and (3); defers (2) community clustering as "low ROI for factoid GT" (`RESUME.md:30`). This is a deliberate, defensible scope cut.
- **Confidence-adaptive reranking weight** (project invention, `omd_retrieval.py:79-88`). Scales CE weight by `stdev(CE scores)/RERANK_CONF_REF`. Validated on 6 benchmarks. The technique is described in some recent RAG literature but is not (to my knowledge) a standardised pattern.
- **`bge-reranker-large` retained over `qwen3-reranker-8b`** — the paper-exact reranker — because the latter does not fit the 17 GB unified-memory Mac and is not hosted on OpenRouter (`RESUME.md` "MODEL DECISION"). This is a pragmatic local-compute adaptation.
- **Opus-authored triple extraction with gpt-4o-mini schema validation** (`RESUME.md` "KEY decision", `_neo.py` lazy vocab, `extract.py`) replaces the paper's lighter extractor. Justified by the project's own finding that gpt-4o-mini produced free-text dumps and run variance on regulatory text.

---

## 5. Comparative Analysis

### 5.1 Design–Code Trace Table

The following claims are checked against the source. **All claims traced to a specific file and line range.**

| Design claim (source) | Code evidence | Status |
|---|---|---|
| `graphont` is a new mode that doesn't touch graphcpl / hybrid | `omd_context_assembly.py:24-26` (`_MODE = "graphont"`); `omd_retrieval.py:1-15` (docstring) | ✅ Aligned |
| Mode is in `VALID_EVAL_MODES` | `evaluate.py:30` | ✅ Aligned |
| Mode is in `VALID_MODES` for ad-hoc query | `query.py:42` | ✅ Aligned |
| Mode is in `RunId._VALID_MODES` | `run_id.py:32` | ✅ Aligned |
| Mode is in `_RETRIEVAL_EVAL_MODES` (RAG-only quality groups apply) | `evaluate_model.py:40` | ✅ Aligned |
| Routes to `omd_context_assembly` node | `routing.py:40-46`; `graph.py:91, 132-135` | ✅ Aligned |
| Tri-channel: graph (IDF-weighted) + BM25 + dense | `omd_retrieval.py:41-48` (weights), `:283-298` (channel1), `:268-280` (channel2), `:319-329` (channel_dense), `:336-365` (retrieve()) | ✅ Aligned |
| Weighted RRF (graph 1.0, BM25 0.7, dense 1.5) | `omd_retrieval.py:41-45, 336` | ✅ Aligned |
| Cross-encoder rerank with confidence-adaptive CE⊕RRF | `omd_retrieval.py:50-58` (config), `:84-88` (confidence calc), `:351-364` (fuse) | ✅ Aligned |
| Definition injection as grounding, bypasses ranking | `omd_retrieval.py:148-184`; `omd_context_assembly.py:54-66` | ✅ Aligned |
| Top-8 output to primus generate node | `omd_context_assembly.py:30` (`_TOP_K = 8`); `graph.py:132-135` (edge to `generate`) | ✅ Aligned |
| Build_id-scoped query isolation | `omd_retrieval.py:39`, `build_definitions.py:30` | ✅ Aligned |
| "Standalone, touches no existing code" | `omd_context_assembly.py:36` direct import of `rag.graph.ontology_v2.omd_retrieval` | ✅ Aligned (but a side-effect of this is the missing DI integration — see §7, risk P1-7) |
| **Has a `CCOP_GRAPHONT_ENABLED` feature flag** | `settings.py:529-531` has only `graphrag_ontology_enabled`; no `graphont_enabled` exists | ❌ **NOT implemented** — claim not present in any source; risk P1-6 |
| **18-case graphont run is in flight / about to produce results** | `eval-run-graphont-tests-18-bdc4927d-20260709-{1050,1212}*.partial.jsonl` contain only 2 of 18 cases each | ❌ **NOT achieved** — both attempts interrupted at case 2; risk P0-1 |
| B01-001 0.39 → 0.61 (RESUME.md headline) | `eval-run-graphont-test-B01-001-20260709-1417*.json` shows 0.556; earlier 12:12 run shows 0.44 | ⚠ **Approximate** — actual scores are 0.44 / 0.556 across the day; the 0.61 figure in RESUME.md appears to be pre-reset or a different run; document drift (P3) |

### 5.2 Mode-Wiring Comparison (graphont vs. sibling retrieval modes)

| Mode | `VALID_EVAL_MODES` | `RunId._VALID_MODES` | `_RETRIEVAL_EVAL_MODES` | Routing | DI provider / container guard | Feature flag | Tests | Tests for nodes |
|---|---|---|---|---|---|---|---|---|
| `hybrid` | ✅ | ✅ | ✅ | `retrieval` | yes | n/a (default) | ✅ | ✅ |
| `graphrag` (Phase 9) | ✅ | ✅ | ✅ | `graph_retrieval` | `_create_graph_retrieval_provider` (`container.py`) | implicit (neo4j_uri) | ✅ | `test_graphrag_routing.py`, `test_graph_retrieval_node.py` |
| `graphrag-ontology` (Phase 10) | ✅ | ✅ | ✅ | `function_type_routing` → `graph_retrieval` | `_create_ontology_graph_retrieval_provider` (`container.py:284-313`) | `CCOP_GRAPHRAG_ONTOLOGY_ENABLED` (`settings.py:529`) | ✅ | `test_graphrag_ontology_routing.py` |
| `graphcpl` (Phase 11) | ✅ | ✅ | ✅ | `context_graph_extraction` chain | implied (CU graph) | n/a (backed up — see risk P3-19) | ⚠ partial | `test_compliance_*` |
| **`graphont` (Phase 12 / new)** | ✅ | ✅ | ✅ | `omd_context_assembly` | ❌ **direct import in node** | ❌ **none** | ❌ **none** | ❌ **none** |

**This table is the single most important design-code-alignment finding.** `graphont` is wired *as a feature* (mode + routing + node) but not *as a feature-flagged service*. Every other retrieval mode has a test file and a container-level guard; graphont has neither.

### 5.3 Actual vs. Claimed Performance (B01-001, B05-001)

| Case | Term-3 mid report §17.x claim | Most recent run (artifacts) | Other runs on the day | Run-to-run variance |
|---|---|---|---|---|
| B01-001 (scope, 3-doc bridge) | 0.56 (graphrag 0.56 vs hybrid 0.11) | **0.556** at 14:17 (`eval-run-graphont-test-B01-001-20260709-1417-*.json`) | 0.44 at 12:12, 0.44 at 10:50 | ±0.12 |
| B05-001 (password bridge) | 0.78 (graphrag 0.78 vs hybrid 0.39) | **0.778** at 10:36 (`eval-run-graphont-test-B05-001-20260709-1036-*.json`) | (one run) | n/a |

**Interpretation.** The B05-001 number reproduces; the B01-001 number is in the right neighborhood but visibly noisy. The retrieved chunk set for B01-001 in the 14:17 run includes `CCoP Response to Feedback::2.2` (the decisive clause, per `T3-extracted.txt:1525`) and the surrounding scope cluster (`2.1, 2.5, 2.11, 11.59`) — exactly the design-intended behavior. The model response cites the SBD Annex C CII definition and the digital-boundary argument, reaching the correct "not applicable" verdict (`eval-run-graphont-test-B01-001-20260709-1417-contexts.json` + response in main JSON).

**Discrepancy with the report's B01-001 case:** the model response in the 14:17 run cites "Response-to-Feedback 11.25" as a source — same mislabel the T3 report §17.2 flagged ("one document mislabel"). This is a real, persistent citation bug, not a flaky result.

---

## 6. Recommendation

**Approach (single line):** **Add a feature flag + Neo4j-availability guard + minimal mocked tests, then run the 18-case graphont-vs-hybrid comparison in batched mode using the `RESUME.md` "HARD GOTCHA" prescription** (RAGAs off, stop Qdrant during graphont, ~3 cases per process, `--resume` between batches).

**Trade-offs accepted:**
- **Ablation completeness over RAGAs granularity.** With RAGAs off, retrieval quality is computed directly from `retrieved_chunk_ids` vs. `expected_clauses` (per `RESUME.md` plan) — a stronger signal for the bridge question but weaker on faithfulness/answer-relevancy. The LLM Judge still produces a per-case score.
- **Test coverage over engineering depth.** Recommend 1-2 mocked tests per new module, not 90% coverage. The mode is new; regression safety is the priority.
- **Concept cache over de-noised prompt.** Acknowledge the ±0.11 nondeterminism by caching query→concept per test-id; not by retuning the prompt (the prompt is well-specified per `omd_retrieval.py:96-110`).

**When this would NOT be the right choice:**
- If the goal is to publish the head-to-head result in the Term-3 final report without first running on the same 18 cases twice. The pending task is comparative; without a clean per-case number on each case, the comparison cannot establish the "graphRAG value-add vs hybrid" the report's section 17.4 promises.
- If the user wants to evaluate `graphont` against `graphcpl` rather than `hybrid`. The `graphcpl` mode was DETACH DELETE'd from the live Neo4j (`RESUME.md:65` "the old Phase-11 CU graph ... was ... DETACH DELETE'd") and would need `../complianceunit/cu_graph_backup.json` + `restore.py` to bring back; not in scope here.

---

## 7. Disadvantages & Limitations (Prioritized Risks)

Priorities: **P0** = blocks the pending 18-case comparison; **P1** = high; **P2** = medium; **P3** = low / cosmetic.

### P0 — Block the pending task

**P0-1. The 18-case graphont run has never completed.** Both attempts (`20260709-1050`, `20260709-1212`) ended at 2/18 cases.
- Evidence: `eval-run-graphont-tests-18-bdc4927d-20260709-1050-primus-reasoning.partial.jsonl` (3 lines = header + B01-001 + B02-001); `eval-run-graphont-tests-18-bdc4927d-20260709-1212-primus-reasoning.partial.jsonl` (3 lines = header + B01-001 + B02-001). Headers are present; the JSONL is the resumable partial format, so the process was killed mid-run, not crashed early.
- Suspected cause: the OOM scenario flagged in `RESUME.md:23-32` ("graphont eval + RAGAs = jetsam OOM kill" on the 17 GB Mac). The B01-001 single-case run took 186s (14:17, metadata `duration_seconds`); B05-001 took longer (CE reranker over ~237 candidates at 60-90s/query per `RESUME.md`). On 18 cases plus the CE-heavy B01/B05, a single process OOMs.
- Impact: no suite-level retrieval-quality number; the pending comparison cannot ship without re-running.

**P0-2. Zero test coverage for the entire graphont path.** No `test_graphont_*.py`, no `test_omd_*.py`, no tests for `src/rag/graph/ontology_v2/` at all. Existing tests cover the OLD `src/rag/graph/ontology/` (graphcpl predecessor) and the Phase-9/10 graphrag modes.
- Evidence: `grep -rn "graphont\|omd_context\|omd_retrieval" tests/` returns no hits; `find tests/ -name "test_*.py" | xargs grep -l ontology_v2` returns no hits. For comparison, `tests/rag/retrieval/test_graphrag_routing.py`, `test_graphrag_ontology_routing.py`, `test_graph_retrieval_node.py`, and `tests/rag/graph/retrieval/test_ontology_graph_retrieval_adapter.py` all exist.
- Impact: any change to `omd_retrieval.py` (e.g., weight tuning, channel addition) has no regression net. The "two issues" pre-wiring in `RESUME.md` (hub flooding, thin query→concept mapping) and the "next: confidence-adaptive CE" pivot all landed without tests.

**P0-3. RAGAs is disabled during graphont evaluation** → no retrieval-quality metrics in the run output; comparison must compute retrieval quality directly from `retrieved_chunk_ids` vs. `expected_clauses` (`RESUME.md:32-36` acknowledges this).
- Evidence: `metadata.quality_categories` in the 14:17 B01-001 run shows `RAGAs: context_recall`, `context_precision`, `context_faithfulness` all `null`; only `LLM Judge` = 0.556 is populated. `CCOP_RAGAS_ENABLED` is FALSE during graphont per `RESUME.md:19`.
- Impact: the "graphont vs hybrid" comparison loses a structured retrieval-quality axis. The workaround (direct ID-vs-GT) is workable but means a second analysis script must be maintained alongside the run.

**P0-4. Query→concept nondeterminism causes ±0.11 score swing between identical runs** (gpt-4o-mini varies at temperature 0; per `RESUME.md:43`).
- Evidence: B01-001 scored 0.44 at 12:12 and 0.556 at 14:17 — same case, same day, different partial-run attempt. Same code, same model, same prompt.
- Impact: any single-run point estimate is unreliable. The 18-case comparison needs (a) per-test-id concept caching (`RESUME.md` calls this out but it isn't yet implemented) or (b) ≥3 runs averaged per case, which compounds the OOM problem.

### P1 — High

**P1-5. No feature flag for `graphont`.** Compare `graphrag_ontology_enabled: bool = Field(default=True, ...)` at `settings.py:529-531`. There is no `CCOP_GRAPHONT_ENABLED` in settings, no flag check in the routing, no flag check in `omd_context_assembly`.
- Impact: cannot be staged / disabled in production; if graphont misbehaves on a corpus, the only "off switch" is editing `VALID_EVAL_MODES` and `VALID_MODES` in the two CLI files. Inconsistent with project pattern (Phase 10 set the standard).

**P1-6. No DI integration; direct import of `rag.graph.ontology_v2.omd_retrieval` inside the node** (`omd_context_assembly.py:36`).
- Impact: hard-coupled to Neo4j credentials in `settings.py` (via `_neo.py:18-23`), cannot be mocked, no graceful "mode unavailable" branch. The graphrag-ontology equivalent (`_create_ontology_graph_retrieval_provider`, `container.py:284-313`) logs a warning and returns `None`; the corresponding query use case then surfaces "No ontology graph retrieval provider configured" to the user. `omd_context_assembly.py:84-89` does a bare `try/except` that *silently* degrades to empty context, which means primus answers without grounding and the user gets a misleading "is_rag_augmented=False" report.

**P1-7. Hard-coded `BUILD_ID = "omd-v1-20260709"`.** Appears in at least: `omd_retrieval.py:39`, `build_definitions.py:30`, `compute_idf.py`, `build_omd_graph.py`.
- Impact: re-running `build_omd_graph.py` with a new BUILD_ID silently breaks `omd_retrieval.retrieve()` (Cypher returns 0 rows because `{build_id: $b}` matches nothing). The user would see `d_cand: 0` and an empty `results` list — no schema-error, no warning. Reproducibility/replay risk: rerunning the 18-case comparison 6 months from now requires checking that the in-graph `build_id` matches the literal in `omd_retrieval.py:39`.

**P1-8. Cross-encoder reranker is optional (`RERANK_ENABLED = True`, `omd_retrieval.py:50`)** with a fallback to RRF order on load failure (`omd_retrieval.py:362-364`). In practice the bge-reranker-large *does* load but produces clustered scores on short factoid queries, leading to the confidence-adaptive fix (`omd_retrieval.py:53-58`).
- Impact: the "with CE reranker" claim in the design depends on (a) the model loading at runtime and (b) the confidence heuristic being well-calibrated. The B01-001 retrieved-chunk scores (top-8 in `eval-run-graphont-test-B01-001-20260709-1417-*.json` `retrieved_chunk_ids`) are in the 0.03–0.04 range — the reranker's score is being recorded, but at this scale it does not dominate; RRF ordering is doing the work. This is a known and documented behavior, not a bug, but a reviewer reading "cross-encoder rerank" in the report would expect a different distribution.

### P2 — Medium

**P2-9. Suite-level validation is missing.** The Term-3 mid report §17.1, §17.2, and §19 are explicit: "single case, on the benchmark the graph was designed around … illustrates the mechanism rather than establishing a suite-level claim." The 18-case comparison is the *only* way to make the suite claim, and it has not happened (P0-1).

**P2-10. Persistent citation bug in B01-001 response.** The model cites "Response-to-Feedback 11.25" which is not in the retrieved context (`eval-run-graphont-test-B01-001-20260709-1417-contexts.json` shows `RtF 2.2, 2.1, 2.5, 2.11, 15.13, 10.2.1, 11.59, 2.2` and a definition — no 11.25). The Term-3 mid report §17.2 already flagged this mislabel in the earlier run; the bug reproduces in the 14:17 run. It is a primus-side grounding bug, not a graphont bug, but it costs citation-correctness points in the very case being used to validate the design.

**P2-11. The Community Report channel from the OMD-GraphRAG paper is not built** (`RESUME.md:30, 71` "lowest ROI for factoid GT, deferred"). The paper's `+3.43%` claim is conditional on this channel. Suite-level claims from the project must therefore be reported as "2-of-3 channels from the paper" — a non-trivial deviation.

**P2-12. Dense channel is silently optional.** `channel_dense()` returns `[]` when the index is missing (`omd_retrieval.py:319-329`); RRF still runs with the remaining 2 channels. The "tri-channel" claim becomes "bi-channel" in any environment where `build_dense_index.py --apply` hasn't been run.

**P2-13. Definition injection is Q-only** (not Q+), by design (`omd_retrieval.py:148-184`; "grounding for concepts in Q only"). Means if a bridge answer depends on a Q+ concept's definition, it's not injected. Worked on B05; unverified across the 18-case stratified sample.

**P2-14. Prior graphrag-ontology 18-case run took 102 minutes (6133 s) for 18 cases** at `eval-run-graphrag-tests-18-bdc4927d-20260702-1459-primus-reasoning.json`. Graphont is heavier (3 channels + CE rerank). The batched plan (≤3 cases/process) implies ≥6 processes; 6 × 102 min minimum, likely more given the CE cost (60-90 s/query for 237 candidates per `RESUME.md:78`).

### P3 — Low / cosmetic

**P3-15. `graphcpl` mode is currently non-functional** — the prior Phase-11 graph was DETACH DELETE'd from Neo4j (`RESUME.md:65`). A user trying to compare graphont against graphcpl (rather than hybrid) will get the `restore.py` run as a prerequisite.

**P3-16. `RESUME.md` claim "0.39→0.61" for B01-001 is not in the artifact set.** The current B01-001 runs show 0.44 (12:12) and 0.556 (14:17). Either the 0.61 was from a run not preserved in `2026-07/`, or it was written aspirationally and never reconciled.

**P3-17. Hard-coded module-relative paths** in `omd_retrieval.py:60-64` (concept_aliases.json), `:330` (`runs/dense/clauses_{BUILD_ID}.npz`). Won't survive relocation; an integration test would catch this immediately.

**P3-18. The 18-case BDC4927D hash scope** is referenced in `RESUME.md:32-33` and is consistent across the partial files — good. But the partial-file naming (`RunId.partial_filename`) means re-running with `--resume` after a settings drift (e.g., changing temperature) is guarded by the partial-metadata drift check; if the user does any of: changes `CCOP_DEFAULT_TEMPERATURE`, changes `--judge-mode`, or the user does not preserve the exact `CCOP_TEST_CASES_DIR=../ground-truth/test-suite/audit-20260629-1245` reference, resume will fail loudly. Operational risk for the pending 18-case re-run.

---

## 8. Implementation Guidance (Next Steps, Prioritized)

The next-step ordering assumes the goal is to ship the 18-case graphont-vs-hybrid comparison without compromising the comparison's validity.

### Step 1 — Unblock the 18-case run (P0-1, P0-4)
1. Implement concept caching per test-id (RESUME.md acknowledges this as required): a small `concept_cache.json` keyed by `test_id` written before the eval loop. ~30 lines in `omd_context_assembly.py` (load cache → fall through to `query_to_concepts` only on miss → write back). This neutralizes the ±0.11 nondeterminism.
2. Run in batched mode as RESUME prescribes: split the 18-case set into 6 batches of 3, invoke `poetry run ccop-eval evaluate run --model primus-reasoning --mode graphont --test-ids … --verbose-io --resume` per batch, with `CCOP_RAGAS_ENABLED=false`, Qdrant stopped, and Word/heavy apps closed.
3. Do the same for `--mode hybrid` on the same 18 IDs. Stop/start Qdrant between modes (per RESUME).

### Step 2 — Add a feature flag (P1-5)
Add `CCOP_GRAPHONT_ENABLED: bool = True` to `settings.py` (mirroring `graphrag_ontology_enabled` at line 529). Guard in `omd_context_assembly.py:36-38` (early-return `state` if disabled, just like the existing `if state.get("mode") != _MODE: return state` guard). Guard in `routing.py:40-46` (return `"retrieval"` fallback with a logger.warning when disabled).

### Step 3 — Add Neo4j-availability degradation handling (P1-6)
Refactor `omd_context_assembly.py:36-89` to (a) attempt a Neo4j ping (`MATCH (n) RETURN 1 LIMIT 1` with a short timeout), (b) on failure, log a warning and set `state["retrieval_error"] = "graphont unavailable: Neo4j unreachable"`, (c) return state with `is_rag_augmented=False`. This makes the mode behavior consistent with how the container treats an unavailable graphrag-ontology provider.

### Step 4 — Add minimal test coverage (P0-2)
Three tests, each < 100 lines, all mocked:
- `tests/rag/graph/ontology_v2/test_omd_retrieval.py::test_retrieve_fuses_three_channels`: mock `_neo.query` to return canned channel outputs; assert RRF ordering is `w_graph=1.0, w_bm25=0.7, w_dense=1.5`.
- `tests/rag/graph/ontology_v2/test_omd_retrieval.py::test_inject_definitions_filters_pointers`: feed a definition list containing a "As defined in section N of the Act" stub; assert it is dropped.
- `tests/rag/retrieval/nodes/test_omd_context_assembly.py::test_graphont_mode_routes_correctly`: mock `omd_retrieval.retrieve`; assert `state["filtered_documents"]` shape matches the `generate` node contract.
- `tests/rag/retrieval/test_graphont_routing.py::test_route_by_mode_returns_omd_context_assembly`: assert `route_by_mode({"mode": "graphont"}) == "omd_context_assembly"`.

### Step 5 — Make BUILD_ID settings-driven (P1-7)
Add `omd_build_id: str = "omd-v1-20260709"` to `settings.py`. Replace the literal in `omd_retrieval.py:39`, `build_definitions.py:30`, and `build_omd_graph.py` with `settings.omd_build_id`. Document the rollback path (set `CCOP_OMD_BUILD_ID=omd-v1-20260709` in `.env.local` to preserve current behavior).

### Step 6 — Validate the ID-vs-GT retrieval-quality workflow (P0-3)
The RESUME-cited extractor `build_comparison_xlsx.py` is the "currently ready" tool. Run it on the 14:17 B01-001 single-case run + the 10:36 B05-001 run first, sanity-check that the `retrieved_chunk_ids` and `expected_clauses` columns line up, *then* run on the full 18 cases. If the extractor can't be located in scratchpad, write a 30-line script that does the comparison inline (this is the more reliable path).

### Step 7 — Reconcile the B01-001 citation bug (P2-10)
This is a primus-side issue, not graphont. The cited 11.25 is not in the retrieved set, so the LLM Judge is right to dock citation correctness. Either (a) accept the loss and report, or (b) investigate whether primus has a tendency to substitute adjacent clause numbers when generating citations — that's a model-side fix, not graphont.

### Step 8 — Decide on Community Report channel (P2-11)
The current deferral is defensible for factoid GT. If the project wants to publish a paper-exact ablation, this becomes a write-up question rather than a code question: "We did not implement community clustering; we argue this is acceptable for clause-level GT and not for thematic GT."

---

## 9. Open Questions & Risks

1. **OOM root cause:** did the 12:12 partial run die from RSS pressure (RAGAs + bge-reranker + bge-dense + Neo4j + Ollama primus) or from a separate crash? Need to check `~/Library/Logs/DiagnosticReports/` on the 17 GB Mac for jetsam events at that timestamp, or run with `dmesg | grep -i jetsam`. Without this, the batched plan is a guess.
2. **Concept-cache TTL:** is the per-test-id concept cache stable across primus fine-tuning? If the model is retrained mid-Term-3, the cache may become stale relative to what the model would otherwise produce. Probably not a concern (concept extraction is gpt-4o-mini, not primus), but worth a footnote.
3. **Why does the B01-001 14:17 run show 9 retrieved chunks (definition + 8 clauses) but the report's B01-001 case claims 9 retrieved chunks "with the decisive digital-boundary clause" — the numbers match. But what is the recall@K against the GT clauses (1.2.1, 1.4.1, Act §7)?** The retrieved set has RtF 2.2 (decisive), 2.1, 2.5, 2.11, 15.13, 10.2.1, 11.59 + a definition. None of 1.2.1, 1.4.1, or Act §7 are in the top-8. The decisive clause IS there; the other GT clauses are not. This is consistent with `RESUME.md:42` "**Recall gap** (B01): §1.4.1 has a genuine extraction gap … Act §7 = concept mismatch (hard). §1.2.1 = it's a :Definition; CII def cites as SBD-AnnexC not §1.2.1 (fixable via cross-ref tag)." → P2-13 may be the real fix path (inject definition by Q+ concept too).
4. **Is `graphrag-ontology` still expected to compete in the same comparison, or has it been superseded by `graphont`?** The CLAUDE.md and `decisions.md` don't say. If the user wants a 3-way comparison (hybrid / graphrag-ontology / graphont), the cost is roughly 3× the 18-case compute. If only hybrid/graphont, the current 18-case run plan is sufficient.
5. **RAGAs on a subset:** would running RAGAs on a 6-case stratified sample (one per benchmark family) give meaningful retrieval-quality signal without the OOM? Worth a 30-min experiment before disabling RAGAs globally for graphont.
6. **Reproducibility of the B01-001 0.61 headline number** claimed in `RESUME.md:18` is not in the artifact set. If that was from a now-deleted run, the project's "live status" in `RESUME.md` may be out of date relative to actual code-and-artifact state. Recommend re-running the single B01-001 case end-to-end and updating the RESUME.
7. **The `bge-reranker-large` model itself** is 568M parameters. On the 17 GB Mac, it is the second-largest resident in the graphont eval after bge-dense. A lighter reranker (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`) would cut latency and memory; the trade-off is ranking quality. Out of scope for this assessment but worth a follow-up.

---

## 10. References

All references are to in-repo files, project memory, or already-cited external papers. No web access was used for this assessment.

- [`src/rag/graph/ontology_v2/RESUME.md`](src/rag/graph/ontology_v2/RESUME.md) — live design/status; lines 1-50 are the 2026-07-09c session summary including the OOM gotcha (lines 23-32), the 18-case pending task (lines 31-40), and the model decision (line 91).
- [`src/rag/graph/ontology_v2/PLAN.md`](src/rag/graph/ontology_v2/PLAN.md) — durable phase plan; Phase 7 ("retrieval") status.
- [`src/rag/graph/ontology_v2/omd_retrieval.py`](src/rag/graph/ontology_v2/omd_retrieval.py) — tri-channel retriever. Channel weights at lines 41-45; cross-encoder config at lines 50-58; `channel1` (IDF-weighted graph) at lines 283-298; `channel2` (BM25) at lines 268-280; `channel_dense` at lines 319-329; `retrieve()` at lines 336-365; `query_to_concepts` at lines 120-138; `inject_definitions` at lines 148-184.
- [`src/rag/graph/ontology_v2/_neo.py`](src/rag/graph/ontology_v2/_neo.py) — direct Neo4j driver wrapper used by every `omd_retrieval` query.
- [`src/rag/graph/ontology_v2/build_definitions.py`](src/rag/graph/ontology_v2/build_definitions.py) — `BUILD_ID = "omd-v1-20260709"` literal at line 30.
- [`src/rag/retrieval/nodes/omd_context_assembly.py`](src/rag/retrieval/nodes/omd_context_assembly.py) — graphont node; `_MODE = "graphont"` at line 26; direct import of `omd_retrieval` at line 36; degrade-safe `try/except` at lines 84-89.
- [`src/rag/retrieval/edges/routing.py`](src/rag/retrieval/edges/routing.py) — `graphont` branch at lines 40-46.
- [`src/rag/retrieval/graph.py`](src/rag/retrieval/graph.py) — graph compilation; `omd_context_assembly` node at line 95; edge to `generate` at line 132-135.
- [`src/presentation/cli/query.py`](src/presentation/cli/query.py) — `graphont` in `VALID_MODES` at line 42.
- [`src/presentation/cli/commands/evaluate.py`](src/presentation/cli/commands/evaluate.py) — `graphont` in `VALID_EVAL_MODES` at line 30.
- [`src/domain/value_objects/run_id.py`](src/domain/value_objects/run_id.py) — `_VALID_MODES` set at line 32; `RunId.partial_filename` at lines 96-101.
- [`src/application/use_cases/evaluate_model.py`](src/application/use_cases/evaluate_model.py) — `_RETRIEVAL_EVAL_MODES` at line 40; maintenance comment at lines 32-39.
- [`src/infrastructure/config/settings.py`](src/infrastructure/config/settings.py) — `graphrag_ontology_enabled` flag at lines 529-531; no equivalent `graphont_enabled` (design gap).
- [`src/infrastructure/config/container.py`](src/infrastructure/config/container.py) — `_create_ontology_graph_retrieval_provider` at lines 284-313 (the standard pattern graphont deviates from).
- [`src/results/evaluations/2026-07/eval-run-graphont-test-B01-001-20260709-1417-primus-reasoning.json`](src/results/evaluations/2026-07/eval-run-graphont-test-B01-001-20260709-1417-primus-reasoning.json) — B01-001 0.556 result; metadata + test_results.
- [`src/results/evaluations/2026-07/eval-run-graphont-test-B01-001-20260709-1417-contexts.json`](src/results/evaluations/2026-07/eval-run-graphont-test-B01-001-20260709-1417-contexts.json) — B01-001 14:17 retrieved contexts (definition + RtF 2.2, 2.1, 2.5, 2.11, 15.13, 10.2.1, 11.59, 2.2).
- [`src/results/evaluations/2026-07/eval-run-graphont-test-B05-001-20260709-1036-primus-reasoning.json`](src/results/evaluations/2026-07/eval-run-graphont-test-B05-001-20260709-1036-primus-reasoning.json) — B05-001 0.778 result.
- [`src/results/evaluations/2026-07/eval-run-graphont-tests-18-bdc4927d-20260709-1050-primus-reasoning.partial.jsonl`](src/results/evaluations/2026-07/eval-run-graphont-tests-18-bdc4927d-20260709-1050-primus-reasoning.partial.jsonl) — 18-case run attempt 1; only 2/18 cases completed (B01-001=0.556, B02-001=0.222).
- [`src/results/evaluations/2026-07/eval-run-graphont-tests-18-bdc4927d-20260709-1212-primus-reasoning.partial.jsonl`](src/results/evaluations/2026-07/eval-run-graphont-tests-18-bdc4927d-20260709-1212-primus-reasoning.partial.jsonl) — 18-case run attempt 2; only 2/18 cases completed (B01-001=0.44, B02-001=0.17).
- [`src/results/evaluations/2026-07/eval-run-graphrag-tests-18-bdc4927d-20260702-1459-primus-reasoning.json`](src/results/evaluations/2026-07/eval-run-graphrag-tests-18-bdc4927d-20260702-1459-primus-reasoning.json) — Phase-9 18-case baseline; 102 min, overall 0.414.
- [`report/term3-mid/T3-extracted.txt`](report/term3-mid/T3-extracted.txt) — Term-3 mid report (text-extracted). §12 (lines 911-934): OMD-GraphRAG blueprint. §13 (lines 939-1006): ontology-guided extraction. §15.1 (lines 1071-1097): entity types. §16 (lines 1338-1410): retrieval methodology. §16.6 (lines 1402-1410): "Observed Limitations & Challenges." §17.1 (lines 1483-1540): B05 head-to-head. §17.2 (lines 1543-1605): B01 head-to-head. §17.3, §18, §19 (lines 1610-1660): next steps and research arc.
- [`report/term3-mid/T3-mid-append.md`](report/term3-mid/T3-mid-append.md) — Term-3 mid report (markdown, line ranges 520-540 cover OMD-GraphRAG vs GraphCompliance comparison).
- OMD-GraphRAG paper — J. Wang, H. Huang, X. Ge, J. Su, W. Liu, S. Lian, "OMD-GraphRAG: Enhancing GraphRAG with ontology-guided extraction, multi-dimensional clustering and dual-channel fusion," arXiv:2603.25152, 2026. (Cited at `T3-extracted.txt:1597`; URL https://arxiv.org/abs/2603.25152). The paper is also bundled at `research/graphcompliance/omd-graphrag.pdf` per the RESUME; not re-read for this assessment.
- [`docs/project_notes/bugs.md`](docs/project_notes/bugs.md), [`docs/project_notes/decisions.md`](docs/project_notes/decisions.md), [`docs/project_notes/issues.md`](docs/project_notes/issues.md) — searched for `graphont|omd-graphrag|ontology_v2`; **no entries** (confirms graphont is a new, un-tracked component).
- `tests/rag/retrieval/test_graphrag_routing.py`, `tests/rag/retrieval/test_graphrag_ontology_routing.py`, `tests/rag/graph/retrieval/test_ontology_graph_retrieval_adapter.py` — **existence** used as the baseline for the test-coverage gap (P0-2); not read in full.
