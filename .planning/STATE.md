# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-04)

**Core value:** Build a hybrid model that CII organizations can trust to interpret CCoP 2.0 correctly
**Current focus:** Phase 1 - RAG Infrastructure

## Current Position

Phase: 1.1 of 8 (Evaluation Infrastructure Upgrade)
Plan: 2 of 5 in current phase
Status: In progress
Last activity: 2026-03-15 — Completed 01.1-04-PLAN.md (RAGAs Evaluation Service)

Progress: [███████░░░] 67%

## Performance Metrics

**Velocity:**
- Total plans completed: 12
- Average duration: 5.4 min
- Total execution time: 1.08 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. RAG Infrastructure | 4/5 | 28 min | 7 min |
| 1.1. Evaluation Infrastructure Upgrade | 2/5 | 5 min | 2.5 min |
| 1.2. Local RAG Migration | 4/5 | 17 min | 4.25 min |
| 1.3. RAG Quality - Chunking & Retrieval | 2/4 | 15 min | 7.5 min |

**Recent Trend:**
- Last 5 plans: 01.2-04 (10min), 01.3-01 (12min), 01.3-02 (3min), 01.1-01 (0min), 01.1-04 (5min)
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

### Pending Todos

None yet.

### Roadmap Evolution

- Phase 1.1 inserted after Phase 1: MLflow Experiment Tracking (URGENT) — Record and compare results across all 5 model iterations (baseline LLM, naive RAG, optimized RAG, fine-tuned LLM, hybrid). Phase 2 now depends on 1.1.
- Phase 1.2 inserted after Phase 1: Local RAG Migration — Migrate from Databricks to Qdrant + local BGE. Phase 1.2 runs before Phase 1.1.
- Phase 1.3 inserted after Phase 1.2: RAG Quality — Clause-Level Chunking & Retrieval (URGENT) — Replace PyMuPDF4LLM with Docling, clause-aware chunking, cross-encoder reranking, fix RRF threshold. Discovered during Phase 1.2 human verification: 66 chunks too coarse, RRF threshold broken, zero citations resolving. Research completed first. Phase 1.3 runs before Phase 1.1.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-15
Stopped at: Completed 01.1-04-PLAN.md (RAGAs Evaluation Service)
Resume file: None
