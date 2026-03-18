---
phase: 02-rag-evaluation
plan: 02
subsystem: evaluation-infrastructure
tags: [rag-pipeline, langgraph, dependency-injection, evaluation-modes, ragas-integration]

# Dependency graph
requires:
  - phase: 02-01
    provides: evaluation_mode field in DTOs and CLI parameter
provides:
  - RAG pipeline wired into evaluation use case (IRagPipeline integration)
  - Graph-based evaluation replacing direct model_gateway calls
  - retrieved_contexts field in RagResponse for RAGAs evaluation
  - Chunk IDs and contexts extracted from graph and passed to RAGAs
  - DI container wires rag_pipeline into evaluate_model_use_case
affects: [02-03, rag-evaluation-cli, report-generation]

# Tech tracking
tech-stack:
  added: []
  patterns: [rag-pipeline-evaluation-integration, graph-output-to-benchmark-scoring]

key-files:
  created: []
  modified:
    - src/application/use_cases/evaluate_model.py
    - src/infrastructure/config/container.py
    - src/rag/application/ports/i_rag_pipeline.py
    - src/rag/infrastructure/adapters/langgraph_rag_adapter.py

key-decisions:
  - "Evaluation routes through full LangGraph graph, not direct model calls"
  - "retrieved_contexts extracted from graph's filtered_documents for RAGAs"
  - "Backward compatible: falls back to model_gateway when rag_pipeline is None"
  - "Qdrant unavailable in hybrid mode raises clear error (no silent fallback)"

patterns-established:
  - "RAG pipeline as evaluation source: graph output becomes benchmark scoring input"
  - "Graph state extraction pattern: filtered_documents → retrieved_contexts for downstream evaluation"

# Metrics
duration: 4min
completed: 2026-03-18
---

# Phase 02 Plan 02: RAG Pipeline Integration Summary

**LangGraph RAG pipeline wired into evaluation pipeline — test cases now route through full graph (hybrid mode) or LLM-only path, with filtered_documents flowing to RAGAs as retrieved_contexts**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-18T22:57:51Z
- **Completed:** 2026-03-18T23:01:44Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- EvaluateModelUseCase routes evaluation through IRagPipeline instead of direct model_gateway calls
- RagResponse carries retrieved_contexts field populated from graph's filtered_documents
- Graph output (generation text) drives benchmark scoring and RAGAs evaluation
- DI container wires rag_pipeline into evaluate_model_use_case
- Backward compatible: existing tests pass, falls back to model_gateway when rag_pipeline is None

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire RAG pipeline into EvaluateModelUseCase** - `82b3907` (feat)
2. **Task 2: Wire rag_pipeline into DI container** - `94a3bbc` (feat)

## Files Created/Modified
- `src/rag/application/ports/i_rag_pipeline.py` - Added retrieved_contexts field to RagResponse for RAGAs evaluation
- `src/rag/infrastructure/adapters/langgraph_rag_adapter.py` - Populate retrieved_contexts from filtered_documents in graph state
- `src/application/use_cases/evaluate_model.py` - Route evaluation through RAG pipeline, extract chunk IDs and contexts, pass to RAGAs
- `src/infrastructure/config/container.py` - Wire rag_pipeline into evaluate_model_use_case factory

## Decisions Made
- **Graph-based evaluation:** Evaluation routes through the full LangGraph RAG graph instead of direct model_gateway calls. This means hybrid mode gets RAG-augmented responses and llm-only mode gets fallback generation from the graph.
- **filtered_documents extraction:** Graph's filtered_documents are extracted as retrieved_contexts and passed to RAGAs for context-aware metrics (faithfulness, context_precision, context_recall).
- **Error handling for hybrid mode:** If Qdrant is unavailable in hybrid mode, raise clear error instead of silently falling back to llm-only. User must explicitly choose --mode llm-only.
- **Backward compatibility:** When rag_pipeline is None (not configured), fall back to existing model_gateway.generate_response() path.
- **DI container provider ordering:** Moved rag_pipeline provider definition before evaluate_model_use_case to avoid Python class body evaluation order issues.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Python class body evaluation order in DI container:** Initially placed rag_pipeline=rag_pipeline in evaluate_model_use_case factory, but rag_pipeline provider was defined later in the file (line 268 vs line 133). Python evaluates class body sequentially, causing NameError. Fixed by moving rag_pipeline provider definition (and _create_rag_adapter static method) before evaluate_model_use_case.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

RAG pipeline integration complete. Evaluation infrastructure now routes through the same LangGraph graph that `query ask` uses. Ready for Plan 03 to add CLI wiring and end-to-end testing.

No blockers. The graph integration is tested and backward compatible.

---
*Phase: 02-rag-evaluation*
*Completed: 2026-03-18*
