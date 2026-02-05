# Roadmap: CCoP 2.0 Hybrid Compliance Model

## Overview

This roadmap delivers a hybrid Fine-tuned + RAG-augmented compliance assistant that helps Critical Information Infrastructure (CII) organizations understand and implement Singapore's Cybersecurity Code of Practice (CCoP 2.0). The journey begins with expanding the ground truth dataset from 118 to 1000+ test cases, establishes a statistically valid baseline with the expanded dataset, implements RAG infrastructure for document grounding, evaluates RAG-only performance to identify gaps, fine-tunes the model on reasoning weaknesses discovered by RAG evaluation, integrates both approaches into a hybrid system, adds safety guardrails and validation, and concludes with comprehensive evaluation comparing baseline vs RAG vs fine-tuned vs hybrid approaches. The critical decision point is after Phase 4, where RAG evaluation results determine the scope and focus areas for Phase 5 fine-tuning.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Ground Truth Dataset Expansion** - Expand from 118 to 1000+ test cases across all 21 benchmarks
- [ ] **Phase 2: Base Model Re-Baseline** - Run base model against expanded dataset for statistically valid baseline
- [ ] **Phase 3: RAG Infrastructure** - Document ingestion, vector storage, retrieval pipeline with citations
- [ ] **Phase 4: RAG Evaluation** - Run RAG-augmented model, compare to baseline, identify gaps
- [ ] **Phase 5: Fine-Tuning Pipeline** - QLoRA training on reasoning gaps identified by Phase 4
- [ ] **Phase 6: Hybrid Integration** - Combine fine-tuned model + RAG with adaptive routing
- [ ] **Phase 7: Safety & Validation** - Hallucination detection, uncertainty flagging, out-of-scope refusal
- [ ] **Phase 8: Final Evaluation & Comparison** - Full comparison report across all model iterations

## Phase Details

### Phase 1: Ground Truth Dataset Expansion
**Goal**: Expand test dataset from 118 to 1000+ cases with expert validation, enabling statistically valid evaluation and providing training data for fine-tuning
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06
**Success Criteria** (what must be TRUE):
  1. Each of 21 benchmarks has minimum 50 test cases (1050+ total test cases)
  2. Test cases cover all 11 CCoP sections with balanced distribution across IT, OT, and cross-cutting scenarios
  3. Synthetic QA pairs validated by domain experts with >90% approval rate
  4. Fine-tuning instruction-tuning dataset prepared in format compatible with Unsloth/Axolotl
  5. Dataset diversity metrics confirm no section underrepresentation (each section >5% of total)
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 2: Base Model Re-Baseline
**Goal**: Establish statistically valid baseline performance with expanded dataset, replacing the 49.2% result from 118-case evaluation
**Depends on**: Phase 1
**Requirements**: EVAL-01, EVAL-06
**Success Criteria** (what must be TRUE):
  1. Base Llama-Primus-Reasoning model evaluated on all 1050+ expanded test cases
  2. Per-benchmark baseline scores calculated for all 21 benchmarks with confidence intervals
  3. Factual vs reasoning benchmark performance split documented (replacing previous 39% factual / 59% reasoning)
  4. Hallucination rate baseline established on expanded B21 benchmark
  5. Baseline report identifies which benchmarks are below 85% target and by how much
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 3: RAG Infrastructure
**Goal**: Implement document ingestion, vector storage, and retrieval pipeline that returns relevant CCoP clauses with citations
**Depends on**: Phase 2
**Requirements**: RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, RAG-06
**Success Criteria** (what must be TRUE):
  1. All 8 CCoP PDF documents ingested with structure-aware parsing (sections, clauses, tables preserved)
  2. ChromaDB vector store contains embedded document chunks with metadata (document source, section, clause number)
  3. Retrieval pipeline returns top-k relevant CCoP clauses for compliance queries with precision >80%
  4. Re-ranking layer improves retrieval precision by 10-20% over dense-only search
  5. Citation extraction links retrieved chunks to source document and clause numbers (e.g., "CCoP 2.0 Section 3.2.1")
  6. RAG components integrated into existing Clean Architecture as ports/adapters
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 4: RAG Evaluation
**Goal**: Evaluate RAG-augmented model against baseline to measure factual grounding improvements and identify remaining reasoning gaps for fine-tuning
**Depends on**: Phase 3
**Requirements**: EVAL-02, EVAL-03, EVAL-04
**Success Criteria** (what must be TRUE):
  1. RAG-augmented model evaluated on all 1050+ test cases with retrieval context injected
  2. RAG improves factual benchmarks (B1, B4-B6, B18, B20-B21) by 15-25% over baseline
  3. Hallucination rate on B21 reduced by 50%+ compared to baseline
  4. Per-benchmark gap analysis identifies which reasoning benchmarks (B2, B3, B8-B13, B15, B17, B19) still underperform
  5. Decision made on Phase 5 scope based on gap analysis results (which benchmarks need fine-tuning focus)
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
  2. Comparison report shows per-benchmark improvements from baseline → RAG → fine-tuned → hybrid
  3. Hybrid model achieves minimum 70% overall (target: 85%+) across all 21 benchmarks
  4. Hallucination rate (B21) below 5% for hybrid model
  5. Final report includes deployment readiness assessment, known limitations, and recommended use cases
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Ground Truth Dataset Expansion | 0/TBD | Not started | - |
| 2. Base Model Re-Baseline | 0/TBD | Not started | - |
| 3. RAG Infrastructure | 0/TBD | Not started | - |
| 4. RAG Evaluation | 0/TBD | Not started | - |
| 5. Fine-Tuning Pipeline | 0/TBD | Not started | - |
| 6. Hybrid Integration | 0/TBD | Not started | - |
| 7. Safety & Validation | 0/TBD | Not started | - |
| 8. Final Evaluation & Comparison | 0/TBD | Not started | - |

---
*Roadmap created: 2026-02-05*
*Last updated: 2026-02-05*
