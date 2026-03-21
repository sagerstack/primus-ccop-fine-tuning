# Roadmap: CCoP 2.0 Hybrid Compliance Model

## Overview

This roadmap delivers a hybrid Fine-tuned + RAG-augmented compliance assistant that helps Critical Information Infrastructure (CII) organizations understand and implement Singapore's Cybersecurity Code of Practice (CCoP 2.0). The journey begins with building RAG infrastructure for document grounding (learning priority), evaluates RAG against the existing 49.2% baseline on 118 test cases, then expands the ground truth dataset to 1000+ cases informed by RAG gap analysis, re-evaluates both base model and RAG on the expanded set, fine-tunes the model on reasoning weaknesses, integrates both approaches into a hybrid system, adds safety guardrails, and concludes with comprehensive comparison across all model iterations. The critical decision point is after Phase 4, where re-evaluation results on the expanded dataset determine the scope and focus areas for Phase 5 fine-tuning.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: RAG Infrastructure** - Document ingestion, vector storage, retrieval pipeline with citations
- [ ] **Phase 1.2: Local RAG Migration** (INSERTED) - Migrate from Databricks to Qdrant + local BGE with port/adapter abstraction
- [ ] **Phase 1.3: RAG Quality — Clause-Level Chunking & Retrieval** (INSERTED) - Replace PyMuPDF4LLM with Docling, clause-aware chunking, cross-encoder reranking, fix RRF threshold
- [x] **Phase 1.1: Evaluation Infrastructure Upgrade** (INSERTED) - LLM-as-Judge rubrics for 15 benchmarks, RAGAs quality metrics, SemanticSimilarityService removed
- [ ] **Phase 2: RAG Evaluation** - Run RAG-augmented model against 49.2% baseline on 118 cases, identify gaps
- [x] **Phase 2.1: Evaluation Quality Categorization** (INSERTED) - Categorize and aggregate metrics by retrieval quality, model grounding, and response quality
- [x] **Phase 2.2: RAGAs Hallucination Metric and Metric Renaming** (INSERTED) - Add ground-truth faithfulness metric for hallucination detection, rename existing metrics for clarity
- [x] **Phase 2.3: RAGAs Metric Split & Scoring Formula** (INSERTED) - Replace aggregated answer_correctness with separate FactualCorrectness (precision/recall), SemanticSimilarity (diagnostic), and multiplicative hallucination penalty formula
- [ ] **Phase 2.4: LLM Judge Redesign and Metric Simplification** (INSERTED) - Replace per-benchmark rubrics with universal reasoning depth + hallucination check dimensions, drop factual_precision from scoring
- [ ] **Phase 3: Ground Truth Dataset Expansion** - Expand from 118 to 1000+ test cases across all 21 benchmarks
- [ ] **Phase 4: Re-Baseline & Re-Evaluate** - Run both base model and RAG-augmented on expanded dataset for statistically valid comparison
- [ ] **Phase 5: Fine-Tuning Pipeline** - QLoRA training on reasoning gaps identified by Phase 4
- [ ] **Phase 6: Hybrid Integration** - Combine fine-tuned model + RAG with adaptive routing
- [ ] **Phase 7: Safety & Validation** - Hallucination detection, uncertainty flagging, out-of-scope refusal
- [ ] **Phase 8: Final Evaluation & Comparison** - Full comparison report across all model iterations

## Phase Details

### Phase 1: RAG Infrastructure
**Goal**: Implement document ingestion, vector storage, and retrieval pipeline that returns relevant CCoP clauses with citations. Learning RAG implementation is the primary skill acquisition goal.
**Depends on**: Nothing (first phase)
**Requirements**: RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, RAG-06
**Success Criteria** (what must be TRUE):
  1. All 8 CCoP PDF documents ingested with structure-aware parsing (sections, clauses, tables preserved)
  2. Databricks Mosaic AI Vector Search contains embedded document chunks with metadata (document source, section, clause number)
  3. Retrieval pipeline returns top-k relevant CCoP clauses for compliance queries with precision >80%
  4. Re-ranking layer improves retrieval precision by 10-20% over dense-only search
  5. Citation extraction links retrieved chunks to source document and clause numbers (e.g., "CCoP 2.0 Section 3.2.1")
  6. RAG components integrated into existing Clean Architecture as ports/adapters
**Plans**: 5 plans

Plans:
- [ ] 01-01-PLAN.md — Dependencies, PDF parsing, section-level chunking for all 8 CCoP documents
- [ ] 01-02-PLAN.md — Databricks Vector Search indexing with hybrid search and reranking
- [ ] 01-03-PLAN.md — LangGraph adaptive RAG graph (query analysis, retrieval, grading, generation, fallback)
- [ ] 01-04-PLAN.md — Citation extraction/formatting and Clean Architecture integration (port/adapter/DI/CLI)
- [ ] 01-05-PLAN.md — Unit tests and end-to-end verification with human inspection

### Phase 1.2: Local RAG Migration (INSERTED)
**Goal**: Migrate RAG infrastructure from Databricks (Mosaic AI Vector Search + managed BGE) to fully local stack (Qdrant + sentence-transformers BGE-large-en). Introduce IVectorStore/IIndexer port abstractions. Keep Databricks as alternate adapter.
**Depends on**: Phase 1
**Requirements**: RAG-02, RAG-03, RAG-04
**Success Criteria** (what must be TRUE):
  1. Qdrant running locally via Docker with hybrid search (dense + sparse) matching Databricks RRF capabilities
  2. BGE-large-en embeddings generated locally via sentence-transformers (same model as Databricks endpoint)
  3. IVectorStore port in domain layer with QdrantAdapter and DatabricksAdapter implementations
  4. IIndexer port in domain layer with QdrantIndexer and DatabricksIndexer implementations
  5. LangGraph retrieval node uses IVectorStore (not DatabricksVectorSearch directly)
  6. Ingestion orchestrator uses IIndexer (not DatabricksIndexer directly)
  7. DI container selects adapter based on .env.local configuration (Qdrant by default)
  8. All 8 CCoP documents re-ingested into Qdrant with identical metadata schema
  9. Retrieval quality on sample queries comparable to Databricks pipeline (manual inspection)
  10. Unit tests and E2E verification for Qdrant-based pipeline
**Plans**: 5 plans

Plans:
- [ ] 01.2-01-PLAN.md -- Foundation: Docker Compose, ports (IVectorStore, IIndexer), EmbeddingService, Settings, dependencies
- [ ] 01.2-02-PLAN.md -- Qdrant adapters: QdrantVectorStoreAdapter + QdrantIndexerAdapter
- [ ] 01.2-03-PLAN.md -- Databricks port wrappers: DatabricksVectorStoreAdapter + DatabricksIndexerAdapter
- [ ] 01.2-04-PLAN.md -- DI wiring: container, retrieval node, ingestion orchestrator, LangGraphRagAdapter
- [ ] 01.2-05-PLAN.md -- Re-ingestion, unit tests, E2E verification with human inspection

### Phase 1.3: RAG Quality — Clause-Level Chunking & Retrieval (INSERTED)
**Goal**: Fix retrieval precision by replacing flat PDF parsing with structure-aware Docling parser, implementing clause-boundary chunking for regulatory documents, removing broken RRF threshold, and adding cross-encoder reranking. Transforms 66 coarse chunks into ~180+ clause-level chunks where each chunk maps to one regulatory requirement.
**Depends on**: Phase 1.2
**Requirements**: RAG-03, RAG-04, RAG-05, RAG-06
**Success Criteria** (what must be TRUE):
  1. Docling parser extracts hierarchical structure from all 8 CCoP PDFs (sections, clauses, sub-clauses, tables detected)
  2. Clause-aware chunker produces ~180+ chunks where each chunk corresponds to one regulatory requirement (e.g., Clause 5.2.1)
  3. ToC pages and boilerplate excluded from indexing (no noise chunks)
  4. Chunk IDs include source file and clause ID — no UUID collisions across documents
  5. RRF threshold removed — top-N selection replaces hardcoded 0.6 cosine threshold
  6. Cross-encoder reranker (ms-marco-MiniLM-L12-v2) re-scores top-20 candidates before passing top-3 to LLM
  7. Citations resolve to specific clause numbers (e.g., "CCoP 2.0 Clause 5.2.1"), not section-level references
  8. Retrieval quality verified on sample compliance queries with human inspection
  9. Experiment log updated with before/after metrics for each change
**Plans**: 3 plans

Plans:
- [ ] 01.3-01-PLAN.md — Docling parser, clause-aware chunker, ingestion model extensions, orchestrator update
- [ ] 01.3-02-PLAN.md — Cross-encoder reranking node, grading refactor (measurement-only), funnel settings, graph wiring
- [ ] 01.3-03-PLAN.md — Re-ingestion into Qdrant, end-to-end retrieval verification, experiment log update, human inspection

**Research**: `artifacts/research/2026-03-02-rag-chunking-retrieval-strategies-technical.md`
**Experiment Log**: `research/eval/experiment-log.md`

### Phase 1.1: Evaluation Infrastructure Upgrade (INSERTED)
**Goal**: Upgrade evaluation scoring methodology with two complementary layers: (1) LLM-as-Judge rubrics for 15 benchmarks replacing semantic similarity proxies, and (2) RAGAs metrics for RAG pipeline quality evaluation. Infrastructure concerns (ModelGateway, MLflow, CLI flags, evaluation runs) deferred to subsequent phase.
**Depends on**: Phase 1.3
**Requirements**: EVAL-01, EVAL-02
**Success Criteria** (what must be TRUE):
  1. LLM-as-Judge scoring replaces semantic similarity for 7 reasoning benchmarks (B8, B9, B11, B15, B17, B18, B19) using dimension-specific rubric prompts with anchored 0-3 scale
  2. LLM-as-Judge scoring replaces hallucination-detection misuse for B3 (Conditional Logic) -- evaluates conditional reasoning, not word overlap
  3. LLM-as-Judge scoring implemented for 4 previously unimplemented benchmarks (B7, B10, B14, B16) -- removes `NotImplementedError`, enables full 21-benchmark evaluation
  4. Existing LLM-as-Judge benchmarks (B12, B13, B20) upgraded with anchored 0-3 rubric prompts aligned to criteria-establishment.md
  5. 6 rule-based benchmarks (B1, B2, B4, B5, B6, B21) retain automated scoring unchanged
  6. All 21 benchmarks scoreable in a single evaluation run -- no manual/expert scoring dependencies
  7. Evaluation rubrics document (Component 4) formalizes 15 benchmark-specific rubric prompt templates
  8. SemanticSimilarityService removed -- no semantic similarity scoring in evaluation pipeline
  9. RagasEvaluationService provides Layer 2 quality metrics: answer_correctness, answer_relevancy for all responses; faithfulness, context_precision, context_recall for RAG responses
  10. RAGAs evaluator uses Claude Sonnet via LangchainLLMWrapper(ChatAnthropic)
**Plans**: 5 plans

Plans:
- [x] 01.1-01-PLAN.md — Evaluation rubrics document (Component 4) + JudgeEvaluation redesign (dynamic dimensions)
- [x] 01.1-02-PLAN.md — LLMJudgeService upgrade (rubric loading, 0-3 scale, skip-and-flag)
- [x] 01.1-03-PLAN.md — ScoringService migration (rewire 15 benchmarks) + SemanticSimilarityService removal
- [x] 01.1-04-PLAN.md — RagasEvaluationService (RAGAs metrics, ChatAnthropic wrapper, dependencies)
- [x] 01.1-05-PLAN.md — RAGAs pipeline wiring (settings, entity, DTO, use case, container, JSON serialization)

### Phase 2: RAG Evaluation
**Goal**: Evaluate RAG-augmented model against 49.2% baseline (from Phase 1 paper) on existing 118 test cases to measure factual grounding improvements and identify benchmark gaps
**Depends on**: Phase 1.1
**Requirements**: EVAL-02, EVAL-03, EVAL-04
**Success Criteria** (what must be TRUE):
  1. RAG-augmented model evaluated on all 118 existing test cases with retrieval context injected
  2. Per-benchmark scores compared against existing 49.2% baseline results
  3. Gap analysis identifies which benchmarks improved with RAG and which still underperform
  4. Findings inform Phase 3 dataset expansion priorities (which benchmarks need more test cases)
  5. Initial signal on hallucination reduction from RAG grounding
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md — DTOs, entity RAG metadata fields, CLI --mode parameter
- [ ] 02-02-PLAN.md — EvaluateModelUseCase wires RAG graph, container DI, RAGAs context injection
- [ ] 02-03-PLAN.md — CLI panel RAG context display, JSON result serialization, .env.example

### Phase 2.1: Evaluation Quality Categorization (INSERTED)
**Goal**: Categorize evaluation metrics into three diagnostic groups — (a) Retrieval Quality vs Ground Truth (context_recall, context_precision), (b) Model Response vs Retrieved Chunks (faithfulness), (c) Model Response vs Ground Truth (LLM Judge, answer_correctness, answer_relevancy) — with aggregation at benchmark and overall level, CLI summary display, and JSON persistence.
**Depends on**: Phase 2
**Requirements**: EVAL-02, EVAL-03
**Success Criteria** (what must be TRUE):
  1. All 6 evaluation metrics categorized into three diagnostic groups with clear labels
  2. RAGAs metrics aggregated at benchmark level (currently only per test case)
  3. RAGAs metrics aggregated at overall level across all benchmarks
  4. CLI displays categorized quality summary replacing existing flat tables
  5. Categorized aggregate scores persisted in JSON result metadata
  6. Per-test-case panels reorganized into 3 diagnostic groups matching summary structure
**Plans**: 3 plans

Plans:
- [x] 02.1-01-PLAN.md — QualityGroup value object, DTO extensions, aggregation logic in EvaluateModelUseCase
- [x] 02.1-02-PLAN.md — CLI categorized summary tables and reorganized per-test-case panels
- [x] 02.1-03-PLAN.md — JSON persistence with grouped ragas structure and quality_categories in metadata

### Phase 2.2: RAGAs Hallucination Metric and Metric Renaming (INSERTED)
**Goal**: Add a new RAGAs "hallucination" metric that runs faithfulness against the ground-truth expected_response (detecting claims beyond/contradicting the correct answer), and rename existing metrics for clarity: faithfulness → context_faithfulness. The new hallucination metric works in both hybrid and llm-only modes since it uses expected_response as context, not retrieved documents.
**Depends on**: Phase 2.1
**Requirements**: EVAL-02, EVAL-03
**Success Criteria** (what must be TRUE):
  1. New "hallucination" metric computed via RAGAs faithfulness with `[expected_response]` as context instead of retrieved documents
  2. Existing "faithfulness" metric renamed to "context_faithfulness" throughout codebase (service, DTOs, CLI, JSON, quality groups)
  3. Hallucination metric available in both hybrid and llm-only modes (not dependent on RAG retrieval)
  4. context_faithfulness remains hybrid-only (requires retrieved documents)
  5. Hallucination metric placed in "Model Response Quality" group (checks response vs ground truth)
  6. context_faithfulness remains in "Model-RAG Grounding" group (checks response vs retrieved context)
  7. Per-test-case panel group order changed to information flow: Retrieval Quality → Model-RAG Grounding → Model Response Quality (currently reversed)
  8. Overall Quality Summary table restructured: quality groups as parent rows with individual metrics as indented children (two-column layout: name + score), replacing the 6-column N/A-heavy matrix
  9. Per-Benchmark Quality Breakdown table restructured: multi-level header (row 1 = quality group names spanning columns, row 2 = metric names), flat benchmark rows with code + name (e.g., "B3: Conditional Logic"), column order follows information flow (Retrieval Quality → Model-RAG Grounding → Model Response Quality)
  10. CLI displays and JSON output updated with renamed and new metrics
  11. Overall Score normalizes by present category weights (currently sums weighted contributions without dividing by total weight of present categories, producing incorrect scores when running a subset of benchmarks)
  12. `query ask` command shows RAGAs quality scores (context_faithfulness, answer_relevancy) after response — metrics that don't require ground truth. Enabled by default in hybrid mode, suppressible with `--no-score`
  13. Per-test-case panel in hybrid mode expanded to show: (a) question (already exists), (b) retrieved citations with first 10 words of each source, (c) full prompt sent to model (system prompt + user prompt with RAG context), (d) model response
  14. Existing tests updated, new tests added for hallucination metric
**Plans**: 3 plans

Plans:
- [x] 02.2-01-PLAN.md — Domain layer: rename faithfulness to context_faithfulness, add hallucination metric, fix overall score normalization
- [x] 02.2-02-PLAN.md — CLI display: restructure panels/tables with information flow order, two-column summary, expanded hybrid panels
- [x] 02.2-03-PLAN.md — JSON persistence (schema v3) and query ask scoring with --no-score flag

### Phase 2.3: RAGAs Metric Split & Scoring Formula (INSERTED)
**Goal**: Replace the aggregated `answer_correctness` metric (which masks hallucination behind semantic similarity) with separate `FactualCorrectness` (precision + recall modes), keep `answer_relevancy`, add `SemanticSimilarity` as display-only diagnostic, drop the `hallucination` metric (redundant with FactualCorrectness precision), and implement a multiplicative penalty scoring formula: `ragas_score = base_score * factual_precision` where `base_score = w1*factual_recall + w2*factual_precision + w3*answer_relevancy`. This ensures hallucinating responses receive dramatically lower scores than grounded ones.
**Depends on**: Phase 2.2
**Requirements**: EVAL-02, EVAL-03
**Success Criteria** (what must be TRUE):
  1. `answer_correctness` metric removed, replaced by `FactualCorrectness(mode="precision")` and `FactualCorrectness(mode="recall")` as separate metrics
  2. `hallucination` metric removed (redundant with factual_precision)
  3. `SemanticSimilarity` metric added as display-only diagnostic (not included in aggregated RAGAs score)
  4. `answer_relevancy` retained unchanged
  5. Context metrics unchanged: `context_faithfulness`, `context_precision`, `context_recall`
  6. Multiplicative penalty formula implemented in domain entity (`EvaluationResult.ragas_composite_score`): `ragas_score = (w1*factual_recall + w2*factual_precision + w3*answer_relevancy) * factual_precision`
  7. Combined score dropped — benchmark and RAGAs scores shown independently (averaging incompatible scoring methods produces meaningless numbers)
  8. Hallucinating LLM-only responses score dramatically lower than grounded hybrid responses (verified on B3-001)
  9. Quality groups updated: "Model Response Quality" contains factual_precision, factual_recall, answer_relevancy, semantic_similarity, llm_judge
  10. CLI displays updated with new metric names, 2 overall scores (Benchmark + RAGAs, no Combined)
  11. JSON serialization updated with new metric names, schema v4, no combined_score
  12. All existing tests updated, new tests added for scoring formula
**Plans**: 3 plans

Plans:
- [x] 02.3-01-PLAN.md — Domain layer: FactualCorrectness + SemanticSimilarity metrics, QualityGroup update, multiplicative penalty formula
- [x] 02.3-02-PLAN.md — CLI display and JSON serialization with new metric names and schema v4
- [x] 02.3-03-PLAN.md — Update all tests for new metrics and scoring formula

### Phase 2.4: LLM Judge Redesign and Metric Simplification (INSERTED)
**Goal:** [Urgent work - to be planned]
**Depends on:** Phase 2.3
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 2.4 to break down)

**Details:**
[To be added during planning]

### Phase 3: Ground Truth Dataset Expansion
**Goal**: Expand test dataset from 118 to 1000+ cases with multi-source generation, enabling statistically valid evaluation and providing training data for fine-tuning
**Depends on**: Phase 2.3 (gap analysis informs expansion priorities)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06
**Success Criteria** (what must be TRUE):
  1. Each of 21 benchmarks has minimum 50 test cases (1050+ total test cases)
  2. Test cases cover all 11 CCoP sections with balanced distribution across IT, OT, and cross-cutting scenarios
  3. Multi-source questions: CIIO practitioner scenarios, audit/assessment questions, adapted external compliance datasets (NIST, ISO 27001), and any existing CCoP datasets
  4. Tier-specific generation: factual, reasoning, and safety tiers use separate prompt templates
  5. Synthetic QA pairs validated by domain experts with >90% approval rate
  6. Fine-tuning instruction-tuning dataset prepared in format compatible with Unsloth/Axolotl
  7. Dataset diversity metrics confirm no section underrepresentation (each section >5% of total)
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 4: Re-Baseline & Re-Evaluate
**Goal**: Run both base model and RAG-augmented model on expanded 1000+ dataset for statistically valid comparison, replacing the 118-case results
**Depends on**: Phase 3
**Requirements**: EVAL-01, EVAL-02, EVAL-03, EVAL-06
**Success Criteria** (what must be TRUE):
  1. Base Llama-Primus-Reasoning model evaluated on all 1050+ expanded test cases
  2. RAG-augmented model evaluated on all 1050+ expanded test cases
  3. Per-benchmark scores calculated for all 21 benchmarks with confidence intervals for both models
  4. Factual vs reasoning benchmark performance split documented for both models
  5. Hallucination rate baseline established on expanded B21 benchmark for both models
  6. Comparison report identifies which benchmarks are below 85% target and by how much
  7. Gap analysis determines scope for Phase 5 fine-tuning (which benchmarks need fine-tuning focus)
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 5: Fine-Tuning Pipeline
**Goal**: QLoRA fine-tune Llama-Primus-Reasoning on CCoP compliance reasoning patterns targeting gaps identified in Phase 4
**Depends on**: Phase 4 (decision point: gap analysis determines scope)
**Requirements**: FT-01, FT-02, FT-03, FT-04, FT-05, DATA-06
**Success Criteria** (what must be TRUE):
  1. QLoRA training pipeline operational with Unsloth optimization and Axolotl orchestration
  2. Fine-tuned model improves targeted reasoning benchmarks by 10-20% over base model
  3. Catastrophic forgetting monitoring shows no degradation (>5%) on non-targeted CCoP sections
  4. Hyperparameter search identifies optimal training configuration (LoRA rank, alpha, learning rate)
  5. Training checkpoints evaluated at intervals to detect overfitting or hallucination introduction
  6. Final fine-tuned model adapter weights saved and validated for hybrid integration
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 6: Hybrid Integration
**Goal**: Combine fine-tuned model with RAG infrastructure in adaptive routing pipeline that leverages both capabilities
**Depends on**: Phase 5
**Requirements**: HYB-01, HYB-02, HYB-03, HYB-04
**Success Criteria** (what must be TRUE):
  1. Hybrid inference pipeline injects RAG-retrieved context into fine-tuned model prompts
  2. Query router classifies incoming questions by complexity and routes to appropriate retrieval strategy
  3. Response grounding verification confirms model outputs align with retrieved CCoP clauses
  4. All model responses include citations referencing specific CCoP source clauses (document, section, clause number)
  5. Hybrid model evaluated on test set shows combined improvement over RAG-only and fine-tuned-only baselines
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 7: Safety & Validation
**Goal**: Implement safety guardrails for hallucination detection, uncertainty expression, and out-of-scope refusal with expert validation
**Depends on**: Phase 6
**Requirements**: SAFE-01, SAFE-02, SAFE-03, EVAL-05
**Success Criteria** (what must be TRUE):
  1. Hallucination detection flags model responses that cite non-existent clauses or make unsupported claims
  2. Out-of-scope classifier correctly refuses queries outside CCoP domain (attack methodologies, speculation, non-Singapore standards)
  3. Confidence scoring assigns numeric confidence to each response, calibrated to actual accuracy
  4. Uncertainty flagging identifies low-confidence responses requiring human expert review
  5. Expert validation panel reviews edge cases and high-stakes responses with >85% inter-rater reliability
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 8: Final Evaluation & Comparison
**Goal**: Generate comprehensive comparison report across all model iterations (baseline, RAG-only, fine-tuned-only, hybrid) demonstrating deployment readiness
**Depends on**: Phase 7
**Requirements**: EVAL-02, EVAL-03
**Success Criteria** (what must be TRUE):
  1. All model iterations evaluated on identical expanded test set with consistent scoring methodology
  2. Comparison report shows per-benchmark improvements from baseline -> RAG -> fine-tuned -> hybrid
  3. Hybrid model achieves minimum 70% overall (target: 85%+) across all 21 benchmarks
  4. Hallucination rate (B21) below 5% for hybrid model
  5. Final report includes deployment readiness assessment, known limitations, and recommended use cases
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

## Progress

**Execution Order:**
Phases execute: 1 -> 1.2 -> 1.3 -> 1.1 -> 2 -> 2.1 -> 2.2 -> 2.3 -> 2.4 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8
Note: Phase 1.2 runs before 1.3 (quality fixes build on local stack). Phase 1.3 runs before 1.1 so eval infrastructure measures improved retrieval.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. RAG Infrastructure | 4/5 | Plan 05 skipped (replaced by 1.2 tests) | - |
| 1.2. Local RAG Migration | 0/5 | Planning complete | - |
| 1.3. RAG Quality — Clause-Level Chunking & Retrieval | 0/3 | Planning complete | - |
| 1.1. Evaluation Infrastructure Upgrade | 0/4 | Planning complete | - |
| 2. RAG Evaluation | 0/TBD | Not started | - |
| 2.1. Evaluation Quality Categorization | 3/3 | Complete | 2026-03-20 |
| 2.2. RAGAs Hallucination Metric and Metric Renaming | 3/3 | Complete | 2026-03-20 |
| 2.3. RAGAs Metric Split & Scoring Formula | 3/3 | Complete | 2026-03-21 |
| 2.4. LLM Judge Redesign & Metric Simplification | 0/TBD | Not started | - |
| 3. Ground Truth Dataset Expansion | 0/TBD | Not started | - |
| 4. Re-Baseline & Re-Evaluate | 0/TBD | Not started | - |
| 5. Fine-Tuning Pipeline | 0/TBD | Not started | - |
| 6. Hybrid Integration | 0/TBD | Not started | - |
| 7. Safety & Validation | 0/TBD | Not started | - |
| 8. Final Evaluation & Comparison | 0/TBD | Not started | - |

---
*Roadmap created: 2026-02-05*
*Last updated: 2026-03-21*
