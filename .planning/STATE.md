# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-04)

**Core value:** Build a hybrid model that CII organizations can trust to interpret CCoP 2.0 correctly
**Current focus:** Phase 1 - RAG Infrastructure

## Current Position

Phase: 2 of 8 (RAG Evaluation)
Plan: 1 of ? in current phase
Status: In progress
Last activity: 2026-03-18 — Completed 02-01-PLAN.md (RAG Evaluation Mode Foundation)

Progress: [████████░░] 84%

## Performance Metrics

**Velocity:**
- Total plans completed: 16
- Average duration: 5.1 min
- Total execution time: 1.36 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. RAG Infrastructure | 4/5 | 28 min | 7 min |
| 1.1. Evaluation Infrastructure Upgrade | 5/5 | 19 min | 3.8 min |
| 1.2. Local RAG Migration | 4/5 | 17 min | 4.25 min |
| 1.3. RAG Quality - Chunking & Retrieval | 2/4 | 15 min | 7.5 min |
| 2. RAG Evaluation | 1/? | 3 min | 3 min |

**Recent Trend:**
- Last 5 plans: 01.1-04 (5min), 01.1-02 (5min), 01.1-05 (6min), 01.1-03 (3min), 02-01 (3min)
- Trend: Stable (implementation tasks 0-12min, quality maintained)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap reordered: RAG Infrastructure first (learning priority), then RAG Eval on 118 cases, then Dataset Expansion, then Re-baseline
- Existing 49.2% baseline (from paper) used as comparison point — no re-run needed before RAG eval
- No LangGraph for dataset generation: plain Python script with structured prompting (critic's recommendation from team research)
- Tier-specific prompt templates for dataset generation (factual, reasoning, safety)
- Multi-source dataset: CIIO practitioner + audit questions + adapted external compliance datasets (NIST, ISO 27001) + existing CCoP datasets
- Hybrid approach (RAG + fine-tuning): RAG for grounding, fine-tuning for reasoning — each addresses different gaps
- 85% accuracy target: Industry standard for compliance automation (Thomson Reuters, GSA references)
- **[01-01] PyMuPDF4LLM for PDF parsing:** Preserves tables and structure better than generic loaders
- **[01-01] Section-level semantic chunking:** 87.7% context recall vs ~65% for fixed-size chunking
- **[01-01] All 8 CCoP documents as standard sections:** RESPONSE-TO-FEEDBACK marked as clarification type
- **[01-01] Databricks settings no defaults:** Forces explicit configuration via .env.local
- **[01-02] Delta Sync index type:** Automatic updates when source table changes (no manual re-indexing)
- **[01-02] Lazy client initialization:** Enables dry-run mode without Databricks credentials
- **[01-02] Hybrid search (dense + sparse RRF):** 85% NDCG@10 vs 72% for dense-only (research-backed improvement)
- **[01-03] LLM-as-judge grading with 0.6 threshold:** Prevents 40-60% silent failure rate of naive RAG
- **[01-03] Max 3 retrieval attempts:** Balances quality and latency via self-correction loop
- **[01-03] Raw citation anchors:** Generation embeds `<c>citation_id</c>` for downstream resolution (Plan 01-04)
- **[01-04] End-of-response citation format:** Clean text + references at bottom. Avoids embedding metadata in chunks (degrades retrieval)
- **[01-04] TYPE_CHECKING for circular imports:** Breaks Settings → Container → RAG adapter cycle
- **[01-04] Lazy DI container imports:** Staticmethod pattern defers RAG imports until first use
- **[01-04] Graceful degradation without Databricks:** Existing eval framework works without RAG config
- **[01.2-01] Port/adapter pattern for vector stores:** IVectorStore and IIndexer abstractions enable swappable implementations (Qdrant, Databricks)
- **[01.2-01] Lazy embedding model initialization:** Thread-safe double-checked locking avoids loading 1.3GB+ models on import
- **[01.2-01] BGE query prompt only for queries:** Improves retrieval, degrades document embeddings (per model documentation)
- **[01.2-01] FastEmbed for BM25 sparse vectors:** Lightweight, Qdrant-maintained, drop-in BM25 support
- **[01.2-02] Prefetch + RRF for hybrid search:** Qdrant native API for combining dense/sparse results. RRF is rank-based (no score normalization needed)
- **[01.2-02] IDF modifier in sparse vectors:** FastEmbed BM25 outputs raw TF, Qdrant applies IDF server-side when `modifier=Modifier.IDF` configured
- **[01.2-02] Delete+recreate collection for local dev:** Clean slate approach acceptable for local environment, production would need incremental updates
- **[01.2-02] Deterministic UUID for point IDs:** uuid5 with NAMESPACE_URL generates consistent IDs from string chunk IDs, enables re-indexing without duplicates
- **[01.2-03] Thin wrappers for Databricks:** DatabricksVectorStoreAdapter and DatabricksIndexerAdapter delegate to existing classes, zero modification to existing code
- **[01.2-04] DI container selects adapters based on config:** Qdrant (when qdrant_url set) > Databricks (when databricks_host set) > None. Lazy factories maintain circular dependency protection
- **[01.2-04] EmbeddingService created inside factory:** Not a separate provider, avoids loading 1.3GB+ models when using Databricks
- **[01.2-04] Ingestion uses factory not container:** Batch script creates indexer directly via _create_indexer factory function
- **[01.3-01] Docling for PDF parsing:** Classic pipeline extracts hierarchical markdown better than PyMuPDF4LLM for regulatory structure
- **[01.3-01] Clause-level chunking:** Each chunk = one regulatory requirement (e.g., "5.2.1"). Non-negotiable for compliance Q&A where auditors need specific clause citations
- **[01.3-01] Deterministic chunk IDs:** {source}::{clause} format generates collision-free uuid5 point IDs, enables re-indexing
- **[01.3-01] Parent hierarchy in metadata only:** ChunkMetadata.parent_path stores "Chapter 5 > Section 5.2 > 5.2.1" but NOT prepended to chunk text (contextual chunking deferred to Experiment 4)
- **[01.3-02] Remove rag_similarity_threshold:** 0.6 threshold applied to RRF scores (0.001-0.033 range) caused 100% document filtering
- **[01.3-02] Cross-encoder reranking funnel:** Retrieve 20 with bi-encoder, rerank with cross-encoder, keep top-3 for LLM. Improves precision@3 by 25-35%
- **[01.3-02] Measurement-only grading:** No filtering, logs reranker scores for observability. LLM-as-judge grading removed (slow, inconsistent)
- **[01.3-02] Lazy cross-encoder loading:** Thread-safe singleton defers 400MB model load until first use
- **[01.1-04] RAGAs evaluator uses Claude Sonnet:** LangchainLLMWrapper(ChatAnthropic) for RAGAs metrics evaluation
- **[01.1-04] Lazy LLM initialization for RAGAs:** ChatAnthropic not loaded until first evaluate_response() call
- **[01.1-04] RagasEvaluationService independent from ScoringService:** Layer 1 (benchmark scoring) and Layer 2 (RAG quality) are separate domain services with no coupling
- **[01.1-04] langchain-anthropic version constraint:** Used <1.0 constraint to get 0.3.22 (compatible with langchain 0.3.x), avoiding langchain-core version conflict
- **[01.1-01] 0-3 anchored scale for LLM judge dimensions:** Matches criteria-establishment.md Component 2 exactly. Discrete level descriptions with concrete CCoP-specific examples at each anchor. Not continuous 0-1 (no anchors) or 1-5 (wrong scale)
- **[01.1-01] Binary 0/3 for safety dimensions:** Over-specification and hallucination (B20, B21) are pass/fail — any fabrication = failure. No partial credit maintains safety threshold
- **[01.1-01] Chain-of-Thought in judge prompts:** "Think step-by-step" instruction increases transparency and justification coherence per LalaEval methodology
- **[01.1-01] Skip-and-flag error pattern:** judge_error=True with overall_score=0.0 and empty dimensions. No fallback conservative scores (hides failures). Errors flagged for manual review
- **[01.1-01] Dynamic dimension scoring:** List[DimensionScore] replaces fixed accuracy/completeness/alignment fields. Supports any number of dimensions per benchmark
- **[01.1-01] Rubric templates in docs/ not code:** evaluation-rubrics.md is single source of truth. Code references it, doesn't embed prompts. Enables non-engineer rubric iteration
- **[01.1-02] Configurable rubric file path:** LLMJudgeService constructor accepts optional rubric_path. Default resolves from project root via Path(__file__). Enables test isolation
- **[01.1-02] Rubric parsing by markdown structure:** Split on `## B{N}:` headers, extract code block after `### Judge Prompt Template`. Cached at init, never reloaded
- **[01.1-02] Score clamping with warning:** Out-of-range judge scores (below 0 or above 3) are clamped, not rejected. Warning logged for observability
- **[01.1-02] ScoringService dynamic dimension conversion:** Tier 3 scorer converts each DimensionScore to EvaluationMetric (score/3.0 normalization). Judge errors produce single judge_error metric with value 0.0
- **[01.1-05] Conditional DI via factory returning None:** staticmethod factory returns None when ragas_enabled=False. Use case checks for None before calling RAGAs
- **[01.1-05] RAGAs provider placement before use cases:** DeclarativeContainer processes attributes top-to-bottom; ragas_service must be defined before evaluate_model_use_case
- **[01.1-05] retrieved_contexts=None for all RAGAs calls:** Current IModelGateway returns ModelResponse without documents. Context metrics deferred until ModelGateway exposes GraphState
- **[01.1-03] Unified _score_llm_judge for all 15 benchmarks:** Single method routes B3, B7-B20 through LLMJudgeService. Benchmark-specific behavior in rubric templates, not code branching
- **[01.1-03] B3 migrated from hallucination detection to LLM judge:** B3 measures conditional reasoning quality, not hallucination presence. LLM judge with B3-specific rubric evaluates appropriate dimensions
- **[01.1-03] B21 retains rule-based hallucination detection:** B21 is binary pass/fail for fabrication detection, appropriate for rule-based scoring. Stays in 6 rule-based benchmarks
- **[02-01] evaluation_mode defaults to hybrid:** RAG-augmented evaluation is the primary use case
- **[02-01] rag-only excluded from evaluation modes:** Not meaningful for benchmark scoring (per CONTEXT.md)
- **[02-01] RAG metadata fields are optional:** retrieved_chunk_ids, chunk_count, evaluation_mode set to None when not RAG-augmented

### Pending Todos

None yet.

### Roadmap Evolution

- Phase 1.1 inserted after Phase 1: MLflow Experiment Tracking (URGENT) — Record and compare results across all 5 model iterations (baseline LLM, naive RAG, optimized RAG, fine-tuned LLM, hybrid). Phase 2 now depends on 1.1.
- Phase 1.2 inserted after Phase 1: Local RAG Migration — Migrate from Databricks to Qdrant + local BGE. Phase 1.2 runs before Phase 1.1.
- Phase 1.3 inserted after Phase 1.2: RAG Quality — Clause-Level Chunking & Retrieval (URGENT) — Replace PyMuPDF4LLM with Docling, clause-aware chunking, cross-encoder reranking, fix RRF threshold. Discovered during Phase 1.2 human verification: 66 chunks too coarse, RRF threshold broken, zero citations resolving. Research completed first. Phase 1.3 runs before Phase 1.1.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-18
Stopped at: Completed 02-01-PLAN.md — RAG evaluation mode data layer foundation ready
Resume file: None
