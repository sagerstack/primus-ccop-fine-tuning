# Requirements: CCoP 2.0 Hybrid Compliance Model

**Defined:** 2026-02-04
**Core Value:** Build a hybrid model that CII organizations can trust to interpret CCoP 2.0 correctly

## Requirements

### Ground Truth Dataset

- [ ] **DATA-01**: Synthetic QA generation from CCoP document corpus using LLM
- [ ] **DATA-02**: Scenario-based questions covering real-world CII compliance situations
- [ ] **DATA-03**: Gap analysis questions testing identification of compliance gaps
- [ ] **DATA-04**: Diversity enforcement across all CCoP sections and supplementary docs
- [ ] **DATA-05**: Minimum 50 test cases per benchmark (21 benchmarks)
- [ ] **DATA-06**: Fine-tuning instruction-tuning format conversion from ground truth

### RAG Infrastructure

Research will determine specific implementation approach. Requirements define outcomes.

- [ ] **RAG-01**: Ingest 8 CCoP PDF documents with structure-aware parsing
- [ ] **RAG-02**: Vector storage with metadata (section, clause, document source)
- [ ] **RAG-03**: Retrieval that returns relevant CCoP clauses for compliance queries
- [ ] **RAG-04**: Re-ranking to prioritize most relevant results
- [ ] **RAG-05**: Citation extraction linking retrieved chunks to source document/clause
- [ ] **RAG-06**: Integration with existing Clean Architecture (port/adapter pattern)

### Fine-Tuning

Research will determine optimal configuration. Requirements define outcomes.

- [ ] **FT-01**: QLoRA training pipeline for Llama-Primus-Reasoning
- [ ] **FT-02**: Catastrophic forgetting monitoring across all CCoP sections during training
- [ ] **FT-03**: Training evaluation checkpoints (evaluate model at intervals)
- [ ] **FT-04**: Hyperparameter search for optimal training configuration
- [ ] **FT-05**: Reasoning capability improvement on benchmarks B2, B3, B8-B13, B15, B17, B19

### Hybrid Integration

- [ ] **HYB-01**: RAG-augmented inference (retrieval context injected into fine-tuned model)
- [ ] **HYB-02**: Adaptive query routing based on query type (factual vs reasoning)
- [ ] **HYB-03**: Response grounding verification against retrieved context
- [ ] **HYB-04**: Citation generation in model output referencing CCoP source clauses

### Evaluation

- [ ] **EVAL-01**: Re-baseline the base model against expanded dataset (replace 49.2% from 118-case sample)
- [ ] **EVAL-02**: Multi-model comparison report (baseline vs RAG vs fine-tuned vs hybrid)
- [ ] **EVAL-03**: Per-benchmark gap analysis identifying which improved and which didn't
- [ ] **EVAL-04**: Hallucination rate tracking (B21) across all model iterations
- [ ] **EVAL-05**: Confidence scoring per response (model reports uncertainty)
- [ ] **EVAL-06**: All evaluations run against the same expanded dataset (DATA-05)

### Safety

- [ ] **SAFE-01**: Hallucination detection flagging unsupported claims
- [ ] **SAFE-02**: Out-of-scope refusal for queries outside CCoP domain
- [ ] **SAFE-03**: Uncertainty flagging when response confidence is low

## Out of Scope

| Feature | Reason |
|---------|--------|
| Production deployment infra | Focus on model capability first |
| Web UI | CLI sufficient for evaluation |
| Multi-model support | Llama-Primus-Reasoning only |
| Real-time document updates | Static corpus for this project |
| Other regulatory frameworks | CCoP 2.0 Singapore only |
| Graph RAG | May add later if Advanced RAG insufficient |
| Human escalation routing | Future work, depends on deployment context |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1, 3.2 | Pending — ground-truth clause-reference audit happens in Phase 3.2 sub-goal B |
| DATA-02 | Phase 1, 3.2 | Pending — ground-truth clause-reference audit happens in Phase 3.2 sub-goal B |
| DATA-03 | Phase 1 | Pending |
| DATA-04 | Phase 1 | Pending |
| DATA-05 | Phase 1 | Pending |
| DATA-06 | Phase 1 | Pending |
| RAG-01 | Phase 3 | Pending |
| RAG-02 | Phase 3 | Pending |
| RAG-03 | Phase 3, 3.2 | Pending — corpus re-ingestion + chunker fix in Phase 3.2 sub-goal A |
| RAG-04 | Phase 3, 3.2 | Pending — corpus re-ingestion + chunker fix in Phase 3.2 sub-goal A |
| RAG-05 | Phase 3, 3.2 | Pending — corpus re-ingestion + chunker fix in Phase 3.2 sub-goal A |
| RAG-06 | Phase 3 | Pending |
| FT-01 | Phase 5 | Pending |
| FT-02 | Phase 5 | Pending |
| FT-03 | Phase 5 | Pending |
| FT-04 | Phase 5 | Pending |
| FT-05 | Phase 5 | Pending |
| HYB-01 | Phase 6 | Pending |
| HYB-02 | Phase 6 | Pending |
| HYB-03 | Phase 6 | Pending |
| HYB-04 | Phase 6 | Pending |
| EVAL-01 | Phase 2 | Pending |
| EVAL-02 | Phase 3.1, 4, 8 | Infrastructure ready (Phase 3.1 complete 2026-04-21); evaluation still pending Phase 4 re-baseline |
| EVAL-03 | Phase 3.1, 4, 8 | Infrastructure ready (Phase 3.1 complete 2026-04-21); evaluation still pending Phase 4 re-baseline |
| EVAL-04 | Phase 4 | Pending |
| EVAL-05 | Phase 7 | Pending |
| EVAL-06 | Phase 2 | Pending |
| SAFE-01 | Phase 7 | Pending |
| SAFE-02 | Phase 7 | Pending |
| SAFE-03 | Phase 7 | Pending |

**Coverage:**
- Requirements: 30 total
- Mapped to phases: 30 (100% coverage)
- Unmapped: 0

**Note:** EVAL-02 and EVAL-03 appear in Phase 3.1 (traceability infrastructure), Phase 4 (RAG evaluation), and Phase 8 (final comparison). Phase 3.1 delivers the `run_id`, full prompt + retrieved contexts capture, and token/latency propagation that Phase 4 relies on; actual comparison evaluations happen in Phase 4 and Phase 8.

---
*Requirements defined: 2026-02-04*
*Last updated: 2026-04-21 — (1) EVAL-02/EVAL-03 phase mapping expanded with Phase 3.1 infrastructure status after Phase 3.1 verified complete (9/9 success criteria PASS); (2) former Phases 3.2 (ingestion correctness) and 3.3 (clause audit) merged into single Phase 3.2 "Corpus and Ground Truth Correctness" — DATA-01/-02 and RAG-03/-04/-05 mappings updated accordingly*
