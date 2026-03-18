# Phase 2: RAG Evaluation - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire the RAG pipeline (LangGraph graph) into the evaluation command so benchmark test cases can run in hybrid mode (RAG-augmented) or llm-only mode. Add `--mode` parameter to `evaluate run`. Existing flexibility preserved: single benchmark or full set. No comparison tooling or report generation this phase.

</domain>

<decisions>
## Implementation Decisions

### RAG-eval integration mode
- Port the existing `--mode` parameter from `query ask` to `evaluate run`
- Valid modes for evaluation: `hybrid` and `llm-only` (rag-only skipped — not meaningful for benchmark scoring)
- Default mode: `hybrid` (RAG by default). Users opt out with `--mode llm-only`
- Graceful fallback: if Qdrant unavailable in hybrid mode, error with clear message (don't silently fall back to llm-only)

### Context injection strategy
- Use the **full LangGraph graph** for all modes — evaluation pipeline calls the graph, not model_gateway directly
- `hybrid` mode: full graph path (query analysis → retrieval → reranking → grading → generation). Graph's `generation` output becomes the model response. `filtered_documents` passed as `retrieved_contexts` to RAGAs
- `llm-only` mode: graph skips retrieval entirely (query analysis → generation with empty context). No Qdrant call
- Backward compatibility: existing evaluation pipeline (LLM judge scoring, RAGAs metrics, pass/fail) works on the graph's output. The graph replaces model_gateway as the response source
- Token/latency metrics: not a priority for this phase. Focus on scoring quality

### Per-test-case panel output (hybrid mode)
- Show retrieved chunk count + citation IDs in panels: `RAG Context: 3 chunks (CCoP 2.0::5.2.1, Security By Design::1.1, ...)`
- RAGAs context metrics (faithfulness, context_precision, context_recall) appear in the same RAGAs section — show scores when available, N/A when not
- Existing panel structure unchanged — RAG info is additive

### Saved JSON results
- Add `evaluation_mode` (hybrid/llm-only) to saved JSON per evaluation run
- Add `retrieved_chunk_ids` and `chunk_count` per test case in saved results
- Enables downstream comparison between runs (manual, no automated tooling this phase)

### Claude's Discretion
- How to adapt LangGraph graph to accept mode parameter (new parameter vs separate graph configs)
- How to wire graph into evaluate_model use case (new port/adapter vs direct injection)
- Error handling when Qdrant is down mid-evaluation (fail entire run vs skip that test case)
- Whether to create a new ModelResponse-like object from graph output or adapt existing one

</decisions>

<specifics>
## Specific Ideas

- Reuse the same `VALID_MODES = ["hybrid", "llm-only", "rag-only"]` pattern from query.py, but restrict evaluate to hybrid and llm-only
- The LangGraph graph already handles mode routing (query_analysis routes based on mode). Leverage existing routing logic
- `retrieved_contexts=None` is currently hardcoded in evaluate_model.py — this is the exact integration point for passing graph's filtered_documents to RAGAs

</specifics>

<deferred>
## Deferred Ideas

- Baseline comparison tooling (evaluate compare command) — separate capability, not Phase 2
- Report generation with per-benchmark deltas — future phase
- rag-only mode for evaluation (retrieval quality scoring without LLM) — could be useful but not this phase
- Token/latency tracking from LangGraph LLM calls — nice-to-have, not blocking

</deferred>

---

*Phase: 02-rag-evaluation*
*Context gathered: 2026-03-18*
