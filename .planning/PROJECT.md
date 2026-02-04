# CCoP 2.0 RAG Evaluation

## What This Is

A RAG-augmented evaluation system for testing LLM performance on Singapore's Cybersecurity Code of Practice (CCoP 2.0) standards. Expands the existing evaluation framework with retrieval-augmented generation to improve factual accuracy, then measures improvement against baseline to identify remaining gaps for fine-tuning.

## Core Value

**Measure RAG effectiveness on CCoP benchmarks and identify what remains for fine-tuning.**

If RAG improves factual benchmarks (B1, B4, B5, B6, B18, B20, B21), the remaining low-performing reasoning benchmarks become the fine-tuning dataset scope.

## Requirements

### Validated

<!-- Existing evaluation framework capabilities -->

- ✓ Clean Architecture evaluation framework with ports & adapters — existing
- ✓ Tier 1 scoring (B1-B6): Label-based and Jaccard scoring — existing
- ✓ Tier 2 scoring (B8, B9, B11, B15, B17-B19): Semantic similarity — existing
- ✓ Tier 3 scoring (B7, B10, B12-B14, B16, B20-B21): LLM-as-judge — existing
- ✓ Ollama integration for local inference — existing
- ✓ JSONL test case loading with schema validation — existing
- ✓ CLI interface (evaluate, setup, report commands) — existing
- ✓ JSON result persistence with evaluation metrics — existing

### Active

<!-- New work for this project -->

**Ground Truth Generation:**
- [ ] Ground truth generation strategy (synthetic + expert validation)
- [ ] Expanded dataset: 50+ cases per benchmark (currently 3-8)
- [ ] Expert validation workflow integration
- [ ] Dataset quality assurance and deduplication

**RAG Infrastructure:**
- [ ] Document ingestion pipeline for 8 CCoP PDFs
- [ ] ChromaDB local vector storage setup
- [ ] Chunking strategy for regulatory documents
- [ ] Embedding generation (BGE or similar)
- [ ] Hybrid search (dense + BM25 sparse)
- [ ] Re-ranking layer (cross-encoder)

**Integration:**
- [ ] RAG retrieval port (IRetrievalGateway) following Clean Architecture
- [ ] ChromaDB adapter implementation
- [ ] RAG-augmented prompt construction
- [ ] Benchmark-specific retrieval strategy (research needed)

**Evaluation:**
- [ ] Run all 21 benchmarks with RAG augmentation
- [ ] Comparison report: RAG vs baseline
- [ ] Per-benchmark improvement analysis
- [ ] Gap identification for fine-tuning scope

### Out of Scope

- Fine-tuning implementation — separate project after RAG evaluation identifies gaps
- Graph RAG / knowledge graph — may add later if Advanced RAG insufficient
- Cloud vector DB hosting — local ChromaDB sufficient for document corpus size
- Real-time document updates — static corpus for evaluation
- Multi-model comparison — focus on Llama-Primus-Reasoning only

## Context

**Baseline Performance (from Phase 1 evaluation):**
- Overall: 49.2% across 97 test cases
- RAG-target benchmarks (factual): 39.3% average — room for improvement
- Fine-tuning targets (reasoning): 59.4% average — less retrieval-dependent
- B21 hallucination rate: 22% — critical safety issue RAG should address

**Strategic Decision (ADR-004):**
RAG first, fine-tuning on remaining gaps. Rationale:
- RAG addresses factual knowledge gaps immediately
- Hallucination mitigated from day one (safety)
- Fine-tuning dataset becomes smaller and focused on reasoning
- Regulatory updates handled by document refresh, not retraining

**Existing Codebase:**
- Clean Architecture with dependency injection
- Async/await throughout for I/O operations
- Tier-based scoring system already implemented
- 118 test cases across 21 benchmarks (thin coverage)

## Constraints

- **Document Corpus**: 8 PDFs only (CCoP main, supplementary guides, Cybersecurity Act, Ensign guide)
- **Architecture**: Must follow existing Clean Architecture patterns (ports & adapters)
- **Storage**: ChromaDB local (decided) — no cloud dependencies
- **Model**: Llama-Primus-Reasoning via Ollama (existing setup)
- **Integration**: Research needed for how RAG plugs into evaluation pipeline

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| RAG before fine-tuning | Can't fine-tune away factual gaps; RAG addresses grounding issues | — Pending |
| External retriever pattern | Simpler than in-context, model-agnostic | — Pending |
| Advanced RAG architecture | Query rewriting + hybrid search + re-ranking balances complexity/accuracy | — Pending |
| ChromaDB local storage | Simple setup, sufficient for small corpus, matches Ollama local pattern | — Pending |
| Single project (dataset + RAG + eval) | Dataset generation is upstream dependency, cohesive scope | — Pending |

## Document Corpus

Confirmed for ingestion:

| Document | Path |
|----------|------|
| CCoP 2.0 Second Edition Rev 1 | `ccop-official/CCoP---Second-Edition_Revision-One.pdf` |
| Response to Feedback | `ccop-official/RESPONSE-TO-FEEDBACK.pdf` |
| Cybersecurity Act 2018 | `ccop-official/references/Cybersecurity Act 2018.pdf` |
| Ensign Implementation Guide | `ccop-official/references/Ensign's_Cybersecurity_Guide_on_CCoP_2_0_for_CII_Sep_2022.pdf` |
| Risk Assessment Guide | `ccop-official/supplementary/Guide-to-Conducting-Cybersecurity-Risk-Assessment-for-CII.pdf` |
| Threat Modelling Guide | `ccop-official/supplementary/Guide-to-Cyber-Threat-Modelling.pdf` |
| Auditing Guidelines | `ccop-official/supplementary/Guidelines_for_Auditing_Critical_Information_Infrastructure.pdf` |
| Security by Design Framework | `ccop-official/supplementary/Security_By_Design_Framework.pdf` |

---
*Last updated: 2026-02-04 after initialization*
