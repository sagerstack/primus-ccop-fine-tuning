# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-04)

**Core value:** Build a hybrid model that CII organizations can trust to interpret CCoP 2.0 correctly
**Current focus:** Phase 2.3 — RAGAs Metric Split & Scoring Formula (urgent insertion after 2.2)

## Current Position

Phase: 2.3 of 8 (RAGAs Metric Split & Scoring Formula)
Plan: 2 of 2 — PHASE COMPLETE
Status: Phase 2.3 complete — ready for Phase 3
Last activity: 2026-03-21 — Completed 02.3-02-PLAN.md

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 26
- Average duration: 6.4 min
- Total execution time: 2.8 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. RAG Infrastructure | 4/5 | 28 min | 7 min |
| 1.1. Evaluation Infrastructure Upgrade | 5/5 | 19 min | 3.8 min |
| 1.2. Local RAG Migration | 4/5 | 17 min | 4.25 min |
| 1.3. RAG Quality - Chunking & Retrieval | 2/4 | 15 min | 7.5 min |
| 2. RAG Evaluation | 3/3 | 10 min | 3.3 min |
| 2.1. Evaluation Quality Categorization | 3/3 | 105 min | 35 min |
| 2.2. RAGAs Hallucination Metric & Renaming | 3/3 | ~17 min | ~6 min |
| 2.3. RAGAs Metric Split & Scoring Formula | 2/2 | ~12 min | ~6 min |

**Recent Trend:**
- Last 5 plans: 02.2-01 (8min), 02.2-02 (5min), 02.2-03 (4min), 02.3-01 (5min), 02.3-02 (7min)
- Trend: Phase 2.3 execution fast — clear metric restructuring, two-wave approach (domain → presentation/persistence)
- Phase 2.3 complete: 2/2 plans (Wave 1: domain, Wave 2: CLI/JSON)

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
- **[02-02] Graph-based evaluation:** Evaluation routes through full LangGraph RAG graph instead of direct model_gateway calls. hybrid mode gets RAG-augmented responses, llm-only mode gets fallback generation
- **[02-02] filtered_documents extraction:** Graph's filtered_documents extracted as retrieved_contexts and passed to RAGAs for context-aware metrics
- **[02-02] Qdrant unavailable raises error:** If Qdrant unavailable in hybrid mode, raise clear error instead of silent fallback. User must explicitly choose --mode llm-only
- **[02-02] Backward compatible fallback:** When rag_pipeline is None (not configured), fall back to existing model_gateway.generate_response() path
- **[02-03] RAG Context truncation at 5 IDs:** Display first 5 chunk IDs in panel, show total count if more
- **[02-03] llm-only suppresses RAG Context line:** No RAG Context shown for llm-only mode
- **[02-03] Mode in JSON filename:** mode-hybrid or mode-llm-only appended for easy run identification
- **[02-03] getattr for backward compat:** Older EvaluationResult objects without RAG fields handled gracefully
- **[02.1-01] Three quality groups:** Retrieval Quality (context_recall, context_precision), Model-RAG Grounding (faithfulness), Model Response Quality (llm_judge, answer_correctness, answer_relevancy). LLM Judge sits inside Model Response Quality, not separate
- **[02.1-01] Category-weighted overall aggregation:** Two-step: Step 1 computes category-level group averages, Step 2 computes weighted sum using EvaluationCategory weights. Prevents over-weighting categories with more benchmarks
- **[02.1-01] quality_categories as Dict[str, Any]:** Avoids Pydantic nested serialization complexity. Structure: {"overall": {"groups": [...]}, "by_benchmark": {"B1": {"groups": [...]}, ...}}
- **[02.1-01] RAGAs error handling:** evaluation_error=True counts as 0.0 in averages (simple math, no None propagation)
- **[02.1-01] llm-only mode N/A display:** Check rag_only_groups list (Retrieval Quality, Model-RAG Grounding) and mark metrics as None when evaluation_mode != "hybrid"
- **[02.1-02] Categorized CLI summary tables:** Replace old Evaluation Summary and Results by Benchmark tables with Overall Quality Summary (all 6 metrics grouped by category) and Per-Benchmark Quality Breakdown (all 6 metrics per benchmark with tree structure)
- **[02.1-02] 3-group per-test-case panels:** Model Response Quality (LLM Judge + answer metrics), Model-RAG Grounding (faithfulness), Retrieval Quality (context metrics). Color-coded headers for diagnostic clarity
- **[02.1-02] Metric display consistency:** QualityGroup.get_display_name() for all metric labels. RAGAs metrics with "RAGAs:" prefix, LLM Judge with "LLM Judge" label
- **[02.1-02] Color-coded metrics:** Green >= 0.7, yellow 0.4-0.7, red < 0.4, dim for N/A. Immediate visual feedback on quality thresholds
- **[02.1-03] Grouped ragas structure:** Per-test-case ragas metrics organized by diagnostic group (retrieval_quality, grounding, response_quality). Breaking change from flat metrics array (schema_version: 2)
- **[02.1-03] Self-describing JSON format:** group_definitions included in both ragas output and quality_categories metadata. Consumers don't need external docs to understand metric groupings
- **[02.1-03] JSON group key mapping:** "Retrieval Quality" -> "retrieval_quality", "Model-RAG Grounding" -> "grounding", "Model Response Quality" -> "response_quality" for JSON-friendly snake_case
- **[02.2-01] Three separate RAGAs evaluate() calls:** Base metrics, hallucination (faithfulness vs ground truth), and context metrics (faithfulness vs retrieved docs). Each uses different `retrieved_contexts` argument
- **[02.2-01] Hallucination via faithfulness trick:** Pass `[expected_response]` as `retrieved_contexts` to RAGAs faithfulness — checks if response claims are supported by ground truth. Always applicable (both modes)
- **[02.2-01] context_faithfulness hybrid-only:** Only computed when actual retrieved_contexts available. Non-RAG mode adds with applicable=False, score=0.0
- **[02.2-01] Overall score normalization fix:** `weighted_sum / total_weight` instead of just `weighted_sum`. Running only B3 (weight 0.25) now returns 0.44, not 0.11
- **[02.2-02] Information flow panel order:** Retrieval Quality → Model-RAG Grounding → Model Response Quality. Left-to-right follows RAG pipeline: retrieve → ground → respond
- **[02.2-02] Two-column Overall Quality Summary:** Quality groups as parent rows, individual metrics as indented children. Replaces 6-column N/A-heavy matrix
- **[02.2-02] Flat benchmark table with color-coded headers:** Abbreviated column headers (ctx_recall, ctx_faith, halluc, etc.), one row per benchmark, yellow/magenta/cyan for quality groups
- **[02.2-02] SC13(c) deferred:** Full prompt display (system prompt + user prompt with RAG context) requires data model changes to propagate llm_context from GraphState through RagResponse to EvaluationResult
- **[02.2-03] JSON schema_version 3:** context_faithfulness in grounding, hallucination in response_quality. Backward compat note for v2 files
- **[02.2-03] Query scoring with --no-score:** Only context_faithfulness and answer_relevancy shown (don't require ground truth). Errors suppressed unless verbose
- **[02.3-01] FactualCorrectness split:** answer_correctness replaced by FactualCorrectness(mode="precision") + FactualCorrectness(mode="recall"). Splits 75% factual F1 into separate precision/recall metrics
- **[02.3-01] Hallucination metric removed:** Redundant with factual_precision — both measure ground truth support. Cleaner metric set
- **[02.3-01] SemanticSimilarity diagnostic:** Display-only metric (not in composite score). Useful for understanding semantic overlap without polluting quality signal
- **[02.3-01] Multiplicative penalty formula:** ragas_score = base_score * factual_precision. Quadratic effect: 0.2 precision → 0.11 score, 0.9 precision → 0.75 score. Dramatic separation vs linear averaging
- **[02.3-01] Domain scoring property:** EvaluationResult.ragas_composite_score centralizes formula logic. Single source of truth, application layer is thin delegate
- **[02.3-01] Combined score removed:** Avg of benchmark + RAGAs dropped. Two scores measure different things at different scales — averaging was meaningless
- **[02.3-02] JSON schema version 4:** response_quality group with factual_precision, factual_recall, answer_relevancy, semantic_similarity. Backward compat note for v3 (answer_correctness, hallucination)
- **[02.3-02] Persistence delegates to domain for ragas_score:** JSON reads from result.ragas_composite_score property. No formula duplication in persistence layer

### Pending Todos

None yet.

### Roadmap Evolution

- Phase 1.1 inserted after Phase 1: MLflow Experiment Tracking (URGENT) — Record and compare results across all 5 model iterations (baseline LLM, naive RAG, optimized RAG, fine-tuned LLM, hybrid). Phase 2 now depends on 1.1.
- Phase 1.2 inserted after Phase 1: Local RAG Migration — Migrate from Databricks to Qdrant + local BGE. Phase 1.2 runs before Phase 1.1.
- Phase 1.3 inserted after Phase 1.2: RAG Quality — Clause-Level Chunking & Retrieval (URGENT) — Replace PyMuPDF4LLM with Docling, clause-aware chunking, cross-encoder reranking, fix RRF threshold. Discovered during Phase 1.2 human verification: 66 chunks too coarse, RRF threshold broken, zero citations resolving. Research completed first. Phase 1.3 runs before Phase 1.1.
- Phase 2.1 inserted after Phase 2: Evaluation Quality Categorization — Categorize 6 metrics into 3 diagnostic groups (retrieval quality, model grounding, response quality), aggregate RAGAs at benchmark/overall level, CLI summary table, JSON persistence. Discovered during Phase 2 manual verification: RAGAs metrics only shown per test case with no aggregation, no categorized view for diagnosis.
- Phase 2.2 inserted after Phase 2.1: RAGAs Hallucination Metric and Metric Renaming (URGENT) — Add ground-truth faithfulness metric for hallucination detection (works in both modes), rename faithfulness → context_faithfulness for clarity. Discovered during Phase 2.1 UAT: no metric checks model response claims against ground truth expected_response, and "faithfulness" name is ambiguous (faithful to what?).
- Phase 2.3 inserted after Phase 2.2: RAGAs Metric Split & Scoring Formula (URGENT) — Replace aggregated answer_correctness (masks hallucination behind semantic similarity) with separate FactualCorrectness(precision/recall), drop redundant hallucination metric, add SemanticSimilarity as diagnostic, implement multiplicative penalty formula. Discovered during Phase 2.3 triple-score UAT: LLM-only (hallucinating) and hybrid (grounded) responses scored nearly identically (0.87 vs 0.85 RAGAs) because answer_correctness blends 75% factual overlap F1 + 25% semantic similarity.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-21
Stopped at: Completed Phase 2.3 (02.3-01-PLAN.md) — ready for Phase 3
Resume file: None
