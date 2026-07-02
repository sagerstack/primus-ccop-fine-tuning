# Phase 9 — Resume Notes (updated 2026-07-02, post-B01-001 diagnosis)

Read this first when resuming.

## ⚠️ OPEN DELIVERABLE — Wave 6 (18-case comparison) DEFERRED, Phase 10 started against a PARTIAL baseline
User chose (2026-07-02) to commit the harness fixes + fix P3, but **defer the full
18-case graphrag-vs-hybrid comparison** and move to Phase 10. Consequence to carry:
**Phase 10's "A/B vs basic GraphRAG" has no measured basic-GraphRAG baseline yet** —
only B01-001 was ever run (n=1, and it swung 0.50→0.33 between two runs = within noise).
Before any Phase-10 conclusion is trusted, run Wave 6 (18-case graphrag on the
`bdc4927d` GT vs canonical hybrid `...20260430-0232`, rubric judge, deep-dive
B01/B03/B04). All harness blockers are now cleared (funnel parity, provenance, P3).

## Status: waves + post-execution harness fixes
| Wave | Plan | State |
|---|---|---|
| 1 | 09-01 Neo4j foundation | ✅ committed |
| 2 | 09-02 KG build | ✅ committed — **live graph rebuilt 2026-07-02 with 7 DISTINCT Document paths (provenance fix)** |
| 3 | 09-03 inspect/stats | ✅ committed |
| 4 | 09-04 retrieval provider + `--mode graphrag` | ✅ committed |
| 5 | 09-05 CLI modes + B04/B4 fix | ✅ committed (`5a25c8d`) + hotfix `run_id.py _VALID_MODES` |
| **6** | **09-06 eval + comparison report** | ⏳ **DEFERRED (harness ready; not run)** |

### Post-execution harness fixes (2026-07-02, all committed)
- **Q1/Q2 retrieval parity** (`597d909`): graph retrieve-wide→shared rerank→top-3; dense+sparse via HybridCypherRetriever (+ fulltext index). Isolates graph structure from the untuned-funnel confound.
- **Provenance fix** (`c5740e6`): docs no longer collapse to "document.txt"; requires the rebuild already done.
- **P3 reporting** (`7658505`): `_RETRIEVAL_EVAL_MODES` — graphrag context metrics now roll up in summary/report (were N/A). Phase 10: add `graphrag-ontology` to that set (already pre-added) AND to `run_id._VALID_MODES` + `VALID_EVAL_MODES`.
- **Known residual**: `evaluate_model.py:269` hardcodes `mode=="hybrid"` for the fail-loud-if-RAG-unavailable guard — graphrag has no such guard (degrades to empty+error). Low priority.
- **Clause-grounding gap (Phase 10, ADR-007/D-16a)**: B01-001 still fabricated clause numbers even after provenance fix — chunks lack clause-level metadata. This is the genuine limitation Phase 10 addresses via clause-node seeding + clause-anchored retrieval.

## Environment (already up — verify on resume)
- Neo4j `neo4j-local` running + populated (625 nodes). Repo-root `.env` is a **symlink → `src/config/.env.local`** so `docker compose up -d neo4j` interpolates `CCOP_NEO4J_PASSWORD` (compose doesn't read `.env.local` directly — this was a plan gap, fixed via symlink).
- Ollama + `primus-reasoning` up; `CCOP_OPENROUTER_API_KEY` set.
- Verify: `docker ps | grep neo4j-local`; graph node count via settings-based neo4j driver.

## ⚠️ CRITICAL FINDING — the comparison is confounded (do NOT run Wave 6 as-is)
First real E2E run (`evaluate run --mode graphrag --test-ids B01-001`) completed but scored **judge 0.06 vs hybrid 0.44** — graphrag below "naive RAG". Root cause is a **retrieval-primitive asymmetry**, NOT graph structure:

| | hybrid ("naive RAG") | graphrag (as built) |
|---|---|---|
| chunks | clause-level Docling (~100–500 chars) | neo4j-graphrag **default 4000-char coarse** |
| dense | bge | bge |
| sparse BM25 | ✅ RRF | ❌ none |
| cross-encoder rerank | ✅ 50→top-3 | ❌ none |
| tuning | heavy (Phase 1.3 + .lab exps) | none |
| chunks → primus | **3 focused** | **50 raw** (top_k=50, no funnel) |

Result: graph `context_recall` 0.88 → **0.00**; retrieved 50 off-target "Response-to-Feedback" chunks; primus produced a generic non-answer. **We're measuring "untuned vs tuned retrieval," not "graph vs vector."**

## DECISIONS SETTLED 2026-07-02 (retrieval parity) — ready to implement
Isolate *graph structure* by giving the graph a comparable retrieval funnel (NOT re-tuning the graph):
1. **Funnel to 3 via retrieve-wide→rerank→3 (Q1 ✅):** graph retrieves a WIDE candidate pool (~50), routes through the SAME cross-encoder reranker (`graph_retrieval → reranking → grade_documents`), funnels to `rerank_top_n`=3. NOT "retrieve 3" (that makes rerank a no-op). Impl: drop `filtered_documents` pre-set in `graph_retrieval_node.py`; re-route the edge; reranker already RRF-combines `dense_rank`+`ce_rank` which the graph node sets.
2. **Dense + sparse via HybridCypherRetriever (Q2 ✅):** swap `VectorCypherRetriever`→`HybridCypherRetriever` (dense vector index + NEW Lucene fulltext index on `Chunk.text`). Keeps dense, ADDS sparse. Caveat: Lucene BM25 ≠ Qdrant fastembed BM25 → approximate parity, reported as such.
3. **Chunk parity: NO — report coarse chunking as intrinsic OOTB limitation (Q3 ✅, D-20 / ADR-007).** Do NOT re-chunk (violates D-05: starves relationship extraction; D-01: 2nd ablation var). Clause granularity is Phase 10's job (D-16a: clause-node seeding + clause-anchored fine retrieval). Research: `docs/project_notes/research/2026-07-02-graphrag-chunking-regulatory.md`.
Design principle: graph adds **structure on top of a comparable retrieval funnel**, not a replacement for the whole tuned pipeline. Chunk granularity is the one confound deliberately left as a reported limitation.

## Other known issues
- **RAGAs `429` rate limits** (OpenRouter) during eval — lower RAGAs concurrency / add backoff before the 18-case run.
- `--judge-mode` **rubric** is the parity mode: the canonical hybrid baseline run (`...20260430-0232`) used **rubric** (its `judge_mode` metadata is unset = default rubric; its dims are the per-benchmark rubric dims). Verified 2026-07-02 by reading the file. (Earlier note claiming "universal" was WRONG — do NOT pass `--judge-mode universal`.)
- 9 pre-existing `test_llm_judge_service.py` failures = stale/unrelated (do not fix, not regressions).
- D-19 decision: emergent graph accepted as honest baseline — do NOT tune the graph itself; retrieval-funnel parity is a harness concern, not graph tuning.

## Resume steps
1. `/clear`
2. Decide retrieval-parity approach (the 3 fixes above) — confirm scope with user.
3. Implement + **E2E re-run B01-001** (fair) to validate before scaling.
4. Run Wave 6: `/gsd-execute-phase 9 --wave 6` (or the eval directly) → 18-case graphrag vs hybrid comparison report, deep-dive B01/B03/B04, decide by LLM-judge + context_faithfulness.

## Process reminder (new global rule)
`~/.claude/rules/e2e-testing.md`: run the smallest real E2E slice per wave (not just mocked units); confirm E2E scope with the user if unsure. This phase's stalls + the `run_id` gap are why.
