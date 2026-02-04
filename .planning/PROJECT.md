# CCoP 2.0 Hybrid Compliance Model

## What This Is

A hybrid Fine-tuned + RAG-augmented compliance assistant that helps Critical Information Infrastructure (CII) organizations understand and implement Singapore's Cybersecurity Code of Practice (CCoP 2.0). Combines fine-tuned reasoning capabilities with retrieval-augmented grounding to deliver accurate, citable compliance guidance.

## Core Value

**Build a hybrid model that CII organizations can trust to interpret CCoP 2.0 correctly.**

The model must be accurate enough for compliance decisions (target: 85%+ on evaluation benchmarks), grounded in actual CCoP text (citable), and safe (minimal hallucination).

## Requirements

### Validated

<!-- Existing evaluation framework capabilities -->

- ✓ Clean Architecture evaluation framework with ports & adapters — existing
- ✓ Tier 1 scoring (B1-B6): Label-based and Jaccard scoring — existing
- ✓ Tier 2 scoring (B8, B9, B11, B15, B17-B19): Semantic similarity — existing
- ✓ Tier 3 scoring (B12, B13, B20, B21): LLM-as-judge — existing
- ✓ Ollama integration for local inference — existing
- ✓ JSONL test case loading with schema validation — existing
- ✓ CLI interface (evaluate, setup, report commands) — existing
- ✓ JSON result persistence with evaluation metrics — existing

### Active

<!-- Full hybrid model scope -->

**Ground Truth Dataset:**
- [ ] Dataset generation strategy (synthetic + expert validation)
- [ ] Expanded test suite: 50+ cases per benchmark (currently 3-8)
- [ ] Fine-tuning training dataset derived from ground truth
- [ ] Expert validation workflow
- [ ] Dataset quality assurance and deduplication

**RAG Infrastructure:**
- [ ] Document ingestion pipeline for 8 CCoP PDFs
- [ ] ChromaDB local vector storage
- [ ] Chunking strategy optimized for regulatory documents
- [ ] Embedding generation (domain-appropriate model)
- [ ] Hybrid search (dense + BM25 sparse)
- [ ] Re-ranking layer for precision
- [ ] Citation extraction for grounding

**Fine-Tuning:**
- [ ] Training dataset preparation from ground truth
- [ ] QLoRA fine-tuning pipeline
- [ ] Reasoning capability enhancement (B2, B3, B8, B9, B11-B13, B15, B17, B19)
- [ ] Compliance judgment calibration
- [ ] Catastrophic forgetting mitigation

**Hybrid Integration:**
- [ ] RAG + fine-tuned model orchestration
- [ ] Context injection strategy
- [ ] Response grounding verification
- [ ] Citation generation from retrieved chunks

**Evaluation & Iteration:**
- [ ] Baseline evaluation (fine-tuned model without RAG)
- [ ] RAG-augmented evaluation (hybrid model)
- [ ] Comparison reporting (baseline vs RAG vs hybrid)
- [ ] Per-benchmark gap analysis
- [ ] Iteration based on evaluation results

**Deployment Readiness:**
- [ ] Model packaging for CII organization use
- [ ] Usage documentation for compliance teams
- [ ] Confidence scoring for responses
- [ ] Uncertainty flagging (when to escalate to human)

### Out of Scope

- Production deployment infrastructure — focus on model capability first
- Multi-model support — Llama-Primus-Reasoning only
- Real-time document updates — static corpus for v1
- Web UI — CLI sufficient for evaluation, UI is future work
- Other regulatory frameworks — CCoP 2.0 Singapore only

## Context

**Base Model:** Llama-Primus-Reasoning (trendmicro-ailab/Llama-Primus-Reasoning)
- Cybersecurity-specialized reasoning model
- Already has security domain knowledge
- Fine-tuning adds CCoP-specific compliance reasoning

**Baseline Performance (Phase 1 evaluation with 118 test cases):**
- Overall: 49.2% — below deployment threshold (85%)
- Factual benchmarks (B1, B4-B6, B18, B20-B21): 39% avg — RAG should improve
- Reasoning benchmarks (B2, B3, B8-B13, B15, B17, B19): 59% avg — fine-tuning target
- Hallucination rate (B21): 22% — critical safety issue

**Strategic Approach (ADR-004):**
RAG + Fine-tuning hybrid, built incrementally:
1. Expand ground truth dataset (enables proper evaluation + fine-tuning data)
2. Implement RAG layer (addresses factual grounding, reduces hallucination)
3. Fine-tune on reasoning gaps (addresses compliance judgment)
4. Integrate hybrid model (RAG augments fine-tuned responses)
5. Iterate based on evaluation results

**Document Corpus (8 PDFs confirmed):**
- CCoP 2.0 Second Edition Rev 1 (main regulatory document)
- Response to Feedback (official clarifications)
- Cybersecurity Act 2018 (legal foundation)
- Ensign Implementation Guide (practical guidance)
- 4 supplementary guides (risk assessment, threat modelling, auditing, security by design)

## Constraints

- **Accuracy Threshold**: 85%+ overall for deployment readiness (regulatory compliance use case)
- **Hallucination**: Must approach 0% on B21 — safety critical for compliance advice
- **Architecture**: Follow existing Clean Architecture patterns
- **Local-First**: ChromaDB local, Ollama local — no cloud dependencies for core functionality
- **Base Model**: Llama-Primus-Reasoning — don't switch models mid-project
- **Fine-Tuning Method**: QLoRA (memory-efficient, proven for domain adaptation)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hybrid approach (RAG + fine-tuning) | RAG for grounding, fine-tuning for reasoning — each addresses different gaps | — Pending |
| RAG before fine-tuning | Grounding first reduces hallucination risk during fine-tuning | — Pending |
| Ground truth expansion first | Both evaluation and fine-tuning need larger dataset | — Pending |
| ChromaDB local | Simple, sufficient for 8-doc corpus, matches Ollama local pattern | — Pending |
| Advanced RAG pattern | Query rewriting + hybrid search + re-ranking balances complexity/accuracy | — Pending |
| QLoRA fine-tuning | Memory-efficient, proven for domain adaptation, works with quantized models | — Pending |
| 85% accuracy target | Industry standard for compliance automation (Thomson Reuters, GSA references) | — Pending |

## Success Criteria

**Minimum Viable:**
- All 21 benchmarks evaluated with expanded dataset (50+ cases each)
- RAG improves factual benchmarks by 20%+ over baseline
- Fine-tuning improves reasoning benchmarks by 15%+ over baseline
- Hybrid model achieves 70%+ overall

**Target:**
- Hybrid model achieves 85%+ overall
- Hallucination rate (B21) below 5%
- All responses include citations to source CCoP text
- Model correctly refuses when query is outside CCoP scope

---
*Last updated: 2026-02-04 after scope clarification*
