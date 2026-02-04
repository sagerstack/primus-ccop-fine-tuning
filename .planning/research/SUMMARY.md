# Project Research Summary

**Project:** CCoP 2.0 Hybrid Compliance Model
**Domain:** Regulatory Compliance AI for Critical Information Infrastructure
**Researched:** 2026-02-04
**Confidence:** HIGH

## Executive Summary

This is a hybrid fine-tuned + RAG compliance assistant for Singapore's Cybersecurity Code of Practice (CCoP 2.0). Experts build such systems by combining retrieval-augmented generation (for factual grounding and citation) with domain-specific fine-tuning (for compliance reasoning patterns). The 2026 architectural consensus treats RAG as infrastructure, compliance validation as domain logic, and adaptive routing as application orchestration.

The recommended approach is **Router-Based Adaptive RAG with QLoRA Fine-Tuning**. RAG infrastructure (ChromaDB + hybrid search + ColBERT re-ranking) provides grounded clause retrieval with citation validation. QLoRA fine-tuning (via Unsloth + Axolotl) adapts Llama-Primus-Reasoning to CCoP-specific compliance reasoning. A query router adaptively selects retrieval strategies based on complexity, optimizing for both speed and accuracy. This hybrid pattern delivers 10-20% factuality gains over RAG-only and 3-5x better ROI than either approach alone.

The critical risk is **hallucination** in regulatory citations (17-88% rates in specialized legal AI tools vs <5% requirement for compliance). Prevention requires zero-tolerance citation validation, unified training across all CCoP sections to avoid catastrophic forgetting, human-in-the-loop expert validation for synthetic dataset quality, and comprehensive governance frameworks for regulatory liability. The phased approach with critical checkpoints (hallucination gates, expert reviews, multi-method evaluation) directly mitigates these documented pitfalls.

## Key Findings

### Recommended Stack

The winning stack prioritizes production-grade accuracy, domain specialization, and air-gapped deployment for CII environments. Core innovation: legal-specialized embeddings (vstackai-law-1), structure-aware PDF parsing (Docling), and hybrid retrieval with re-ranking outperform generic RAG patterns by 20-40%.

**Core technologies:**
- **Docling (PDF parsing)**: Structure-aware layout analysis with TableFormer — 9/10 accuracy on complex PDFs, self-hostable, extracts document hierarchy for semantic chunking
- **vstackai-law-1 (embeddings)**: Legal-specialized embeddings with 32K context — tops MTEB legal leaderboard, outperforms OpenAI by 6-10% on legal retrieval, no chunking needed for most CCoP clauses
- **ChromaDB (vector store)**: Rust-core rewrite with 3-tier storage — 4x performance, billion-scale embeddings, self-hostable with HNSW indexing, built-in metadata filtering
- **Hybrid Search (dense + BM25)**: Reciprocal Rank Fusion — 20-40% precision improvement over dense-only, complements semantic with keyword matching for exact clause citations
- **ColBERT v2 (re-ranking)**: Late-interaction re-ranker — 10-50ms latency, self-hostable, preserves token-level matching, outperforms single-vector by 10-50%
- **Unsloth (QLoRA training)**: 2-5x faster fine-tuning, 80% memory reduction — single GPU optimized, 0% accuracy loss, ideal for resource constraints
- **Axolotl (training orchestration)**: YAML-based config for LoRA/QLoRA — battle-tested, integrates with Unsloth, scales to multi-GPU if needed
- **LlamaIndex (RAG orchestration)**: RAG-first framework — modular architecture, supports hybrid retrieval, cleaner abstractions than LangChain for standard RAG patterns
- **SelfCheckGPT + RAGAS (evaluation)**: Hallucination detection + RAG metrics — zero-resource consistency checks, context precision/recall/faithfulness, industry standard 2026

**Critical version requirements:**
- Python 3.11+ (all libraries compatible, stability priority)
- CUDA 11.8+ (Unsloth, sentence-transformers)
- PyTorch 2.5.0+ (fine-tuning infrastructure)

**Anti-recommendations:**
- LlamaParse (cloud-only, skips critical sections) → use Docling
- Pinecone/Weaviate (cloud-dependent) → use ChromaDB self-hosted
- Dense-only retrieval (20-40% lower precision) → use hybrid search
- Full fine-tuning (16x memory, no accuracy gain) → use QLoRA
- No hallucination detection (violates <5% requirement) → use SelfCheckGPT + RAGAS

### Expected Features

Compliance AI requires three feature tiers: table stakes (15 features), differentiators (8 features), and anti-features (6 to avoid).

**Must have (table stakes):**
- **Clause Citation Accuracy**: RAG-based retrieval with clause-level chunking, FACTUM framework for mechanistic hallucination detection
- **Source Grounding**: Traceable to official CCoP documents with confidence scoring, multi-evidence guided refinement
- **Hallucination Detection**: LLM-as-judge + deterministic checks, <5% requirement (legal AI tools average 17-33%)
- **Singapore Terminology Accuracy**: Fine-tuned awareness + validation layer against official glossary
- **IT vs OT Context Classification**: 60% cross-cutting, 35-40 OT-only clauses require intent classification
- **Uncertainty Expression**: Confidence scoring, appropriate refusal behavior, guard bands for safety
- **Compliance-Appropriate Refusal**: Safety benchmarks (B13-B14), decline attack methodologies and speculation
- **Citation Validation**: Automated verification against official CCoP 2.0 PDF, fabricated clauses are critical failure
- **Audit Trail Generation**: Query-response logging with sources, timestamps, confidence for compliance review
- **Semantic Equivalence Recognition**: Embeddings-based matching for reasoning questions, not keyword-only
- **Multi-Evidence Synthesis**: Multi-hop reasoning across multiple clauses for single compliance question
- **Response Completeness**: 100% key fact coverage for table-stakes requirements

**Should have (competitive):**
- **Cross-Standard Mapping**: Map CCoP to ISO 27001, NIST 800-53, IEC 62443 for multi-framework environments
- **Gap Analysis Automation**: Identify missing controls, required evidence, remediation steps from SOC documentation
- **IaC Misconfiguration Detection**: Security config analysis in Terraform/K8s against CCoP requirements
- **Confidence Calibration**: Numeric confidence scores aligned with actual accuracy, helps escalation decisions
- **Human-in-the-Loop Validation**: Expert review for edge cases, calibrate scoring rubrics, validate high-stakes responses
- **Query Clarification Dialogue**: Detect ambiguous intent and ask clarifying questions before answering

**Defer (v2+):**
- Policy generation (high complexity, audit-ready artifacts required)
- Incident classification (requires incident response domain expertise)
- Cross-standard mapping at scale (valuable but not critical for CCoP-only focus)

**Anti-features (explicitly avoid):**
- Generalized compliance advice (CCoP is Singapore-specific, generic best practices dilute precision)
- Over-confident uncertain answers (17-33% hallucination in "hallucination-free" legal tools shows the danger)
- Citation-free responses (unusable for audit preparation)
- Keyword-only matching (fails on reasoning-based compliance questions)
- Static compliance knowledge (regulatory updates require retraining without RAG)

**Quality thresholds:**
- Citation accuracy: 95% (compliance teams must trust citations for audit work)
- Hallucination rate: <5% (project requirement, legal AI currently 17-33%)
- IT/OT classification: 95% (incorrect classification causes compliance gaps)
- Overall system: 85% (industry standard for enterprise AI compliance automation)

### Architecture Approach

RAG belongs in the **infrastructure layer** as a "knowledge runtime," while compliance reasoning and domain-specific scoring logic remain in the **domain layer**. The application layer orchestrates adaptive retrieval strategies based on query characteristics. This pattern separates technical retrieval mechanics from business compliance validation rules.

**Major components:**
1. **ChromaDBRetrievalGateway (Infrastructure)** — Implements hybrid search (vector + metadata filtering + RRF fusion + ColBERT re-ranking), returns RetrievedContext entities
2. **QueryRouter (Application Service)** — Classifies query complexity (Simple/Medium/Complex) and selects retrieval strategy (single-hop/hybrid/multi-hop), adaptive routing reduces cost 40-60%
3. **CitationVerificationService (Domain Service)** — Validates cited clauses against retrieved context, detects hallucinations (invented clauses), calculates citation accuracy metric
4. **ComplianceValidatorService (Domain Service)** — Validates compliance reasoning quality (clause references, Singapore terminology, IT/OT classification, compliance verdict)
5. **EvaluateWithRAGUseCase (Application Orchestrator)** — Orchestrates: route → retrieve → augment → generate → verify citations → validate compliance → score
6. **PromptAugmenter (Application Service)** — Builds augmented prompts from query + retrieved CCoP clauses with structured context injection

**Integration pattern:** Sequential augmentation where RAG retrieval happens BEFORE model inference to provide context. Fine-tuning adjusts how the model responds, RAG controls what information it uses. Hybrid approach delivers 10-20% factuality gains over zero-shot RAG.

**Data flow:**
```
Query → Router (classify complexity) → Retrieval Gateway (hybrid search + re-rank)
      → Prompt Augmenter (build context) → Fine-tuned Model (augmented prompt)
      → Citation Verifier (validate references) → Compliance Validator (check reasoning)
      → Scoring Service (aggregate metrics) → EvaluationResult
```

**Build order:** 7 incremental phases over 8 weeks (Infrastructure Foundation → Query Routing → Hybrid Search → RAG-Augmented Evaluation → Citation Verification → Compliance Validation → Advanced Retrieval). Validates each component before adding complexity.

### Critical Pitfalls

Based on documented failures in compliance AI systems with regulatory consequences:

1. **Hallucinated Regulatory Citations** — LLMs fabricate non-existent clauses (17-88% rates in legal AI tools). Prevention: Citation validation pipeline, strict retrieval requirements (no generation of clause numbers), zero-tolerance testing with B3 hallucination benchmark gate at every phase. Detection: Model cites clauses not in official documentation. Phase impact: Phase 2 baseline screening, Phase 4 small test, Phase 7 expert review.

2. **Catastrophic Forgetting During Sequential Fine-Tuning** — Model loses IT knowledge when fine-tuned on OT sections. Prevention: Unified training strategy (all 11 CCoP sections simultaneously), QLoRA parameter-efficient approach, continuous validation across all sections, regularization techniques. Detection: Validation loss increases while training loss decreases, early sections degrade. Phase impact: Phase 4 small test validates no forgetting, Phase 6 monitors all sections, Phase 7 validates equal performance.

3. **Synthetic Dataset Bias Amplification** — AI-generated training data amplifies biases, creating monotonous datasets with model collapse risk. Prevention: Human-in-the-loop validation, diversity enforcement (stratified sampling across 11 sections), quality filtering, grounding in real CCoP examples, verification pipeline. Detection: Training examples cluster, underrepresentation of specific sections, formulaic synthetic data. Phase impact: Phase 5 dataset creation with diversity metrics, Phase 6 monitors distribution collapse, Phase 7 tests real-world edge cases.

4. **RAG Retrieval Failures and Poisoned Documents** — Retrieval returns irrelevant documents, truncates context, or retrieves malicious content. Prevention: Retrieval-native access control, multi-hop reasoning support, provenance tracking, security controls, precision testing. Detection: Model cites irrelevant sections, answers lack critical details, anomalous retrieval patterns. Phase impact: Phase 3 comprehensive baseline tests RAG, Phase 5 includes multi-hop scenarios, Phase 7 security assessment.

5. **Evaluation Metric Gaming and Benchmark Overfitting** — Model optimizes for benchmark scores without improving real compliance performance. Prevention: Private held-out test sets, domain-specific metrics (not generic NLP), contamination detection, multi-method validation (70% automated + 20% LLM-judge + 10% expert), progressive difficulty. Detection: Perfect benchmark scores but poor production performance, suspiciously good specific benchmarks. Phase impact: Phase 2 establishes uncontaminated test set, Phase 4 validates no memorization, Phase 7 novel test cases.

**Most critical mitigation:** Zero-tolerance hallucination policy with B3 benchmark gating at every phase, unified training to prevent catastrophic forgetting, human-in-the-loop validation for synthetic data and production deployment, multi-method evaluation, comprehensive governance framework for regulatory compliance.

## Implications for Roadmap

Based on combined research, suggested phase structure aligns with dependency analysis and pitfall mitigation:

### Phase 1: RAG Infrastructure Foundation
**Rationale:** Grounding capability must exist before fine-tuning to reduce hallucination risk. RAG addresses factual benchmarks (B1, B4-B6, B18, B20-B21 at 39% avg). ChromaDB + Docling + hybrid search establishes citation validation infrastructure that gates all subsequent phases.

**Delivers:**
- Document ingestion pipeline for 8 CCoP PDFs with Docling structure-aware parsing
- ChromaDB vector store with vstackai-law-1 embeddings
- Hybrid search (dense + BM25 + ColBERT re-ranking)
- Basic retrieval gateway and query router
- Citation extraction and validation infrastructure

**Addresses Features:** Source grounding, clause citation accuracy, citation validation (table stakes)

**Avoids Pitfalls:** Hallucinated citations (establishes validation pipeline), RAG retrieval failures (tests precision early)

**Research Flag:** Standard patterns for vector DB + retrieval (skip research-phase)

---

### Phase 2: Baseline Evaluation with RAG
**Rationale:** Measure RAG-only improvement over zero-shot baseline (49.2%) before investing in fine-tuning. Validates that hybrid search + re-ranking delivers expected 20-40% precision improvement. Establishes hallucination baseline for gate criteria.

**Delivers:**
- EvaluateWithRAGUseCase orchestrator
- Prompt augmenter for context injection
- RAG-augmented evaluation on existing 118 test cases
- Baseline comparison report (zero-shot vs RAG-augmented)
- Hallucination rate measurement (B21 benchmark)

**Uses Stack:** ChromaDB, LlamaIndex, SelfCheckGPT (evaluation)

**Implements Architecture:** Application layer orchestration, retrieval gateway integration

**Addresses Features:** Hallucination detection, semantic equivalence recognition

**Avoids Pitfalls:** Evaluation metric gaming (private test set), hallucination gate (zero-tolerance requirement)

**Research Flag:** Standard RAG evaluation patterns (skip research-phase)

---

### Phase 3: Ground Truth Dataset Expansion
**Rationale:** Both fine-tuning and proper evaluation need larger dataset. Current 118 cases insufficient for training (need 1,000-5,000) and statistically valid evaluation (need 50+ per benchmark). Synthetic generation must prevent bias amplification.

**Delivers:**
- Synthetic QA generation pipeline with GPT-4o
- Curriculum-based generation (simple → complex)
- Human-in-the-loop expert validation workflow
- Diversity enforcement (stratified sampling across 11 CCoP sections)
- Quality filtering and deduplication
- 1,000-5,000 training examples
- 50+ test cases per benchmark (21 benchmarks)

**Uses Stack:** OpenAI API (GPT-4o), Self-Instruct pipeline, Docling (source extraction)

**Addresses Features:** Singapore terminology accuracy, IT/OT classification, multi-evidence synthesis

**Avoids Pitfalls:** Synthetic dataset bias amplification (human validation + diversity metrics), benchmark overfitting (contamination detection)

**Research Flag:** NEEDS RESEARCH-PHASE for synthetic generation quality control and expert validation protocols

---

### Phase 4: Domain Services for Compliance Validation
**Rationale:** Before fine-tuning, establish domain layer validation services that encode compliance reasoning rules. These services measure whether fine-tuning improves compliance-specific behavior vs generic language modeling.

**Delivers:**
- CitationVerificationService (domain service)
- ComplianceValidatorService (domain service)
- RetrievedContext entity with CCoPClause value objects
- Enhanced ScoringService with compliance-specific metrics
- Response completeness validation
- IT/OT classification validation

**Implements Architecture:** Domain layer services for compliance business rules

**Addresses Features:** Citation validation, IT/OT classification, uncertainty expression, response completeness

**Avoids Pitfalls:** Insufficient expert validation (establishes validation criteria)

**Research Flag:** Standard domain service patterns (skip research-phase)

---

### Phase 5: Small-Scale Fine-Tuning Test
**Rationale:** Validate QLoRA fine-tuning approach on small dataset (100-200 examples) before full training. Tests for catastrophic forgetting, overfitting, and hallucination introduction. Early detection of training pitfalls before expensive compute investment.

**Delivers:**
- Unsloth + Axolotl training pipeline
- QLoRA configuration (r=64, alpha=16, 4-bit quantization)
- Small-scale fine-tune on 100-200 balanced examples
- Catastrophic forgetting tests (all 11 sections)
- Hallucination rate comparison (pre vs post fine-tune)
- Training monitoring with Weights & Biases
- Adapter merging and validation

**Uses Stack:** Unsloth, Axolotl, bitsandbytes, PEFT, transformers, wandb

**Addresses Features:** Singapore terminology, compliance reasoning patterns

**Avoids Pitfalls:** Catastrophic forgetting (validates unified training), benchmark overfitting (no memorization)

**Research Flag:** NEEDS RESEARCH-PHASE for hyperparameter tuning and forgetting mitigation techniques

---

### Phase 6: Comprehensive Fine-Tuning
**Rationale:** Full-scale training on expanded dataset (1,000-5,000 examples) using validated configuration from Phase 5. Targets reasoning benchmarks (B2, B3, B8-B13, B15, B17, B19 at 59% avg). Continuous monitoring for distribution collapse and forgetting.

**Delivers:**
- Full QLoRA fine-tune on expanded dataset
- Balanced sampling across all 11 CCoP sections
- Multi-epoch training with evaluation checkpoints
- Catastrophic forgetting monitoring (all sections tested each epoch)
- Model collapse detection (distribution drift metrics)
- Final adapter weights for production
- Training report with loss curves, perplexity, hallucination tracking

**Uses Stack:** Unsloth, Axolotl, wandb (monitoring)

**Addresses Features:** Query intent understanding, compliance reasoning, multi-evidence synthesis

**Avoids Pitfalls:** Catastrophic forgetting (continuous monitoring), synthetic bias amplification (distribution drift detection)

**Research Flag:** NEEDS RESEARCH-PHASE for monitoring thresholds and early stopping criteria

---

### Phase 7: Hybrid Model Integration and Validation
**Rationale:** Integrate fine-tuned model with RAG infrastructure for hybrid inference. Final validation against 85% accuracy target and <5% hallucination requirement with expert review panel.

**Delivers:**
- Hybrid inference pipeline (RAG context + fine-tuned model)
- Adaptive query routing (simple/medium/complex)
- Citation verification in production pipeline
- Confidence calibration and uncertainty expression
- Expert validation panel review
- Production readiness assessment
- Governance framework and liability documentation
- Final evaluation report on expanded benchmarks

**Implements Architecture:** Complete hybrid integration, all domain services active

**Addresses Features:** All table stakes + differentiators (confidence calibration, expert validation, query clarification)

**Avoids Pitfalls:** Liability and regulatory exposure (governance framework), insufficient expert validation (panel review), regulatory change lag (versioning + monitoring)

**Research Flag:** NEEDS RESEARCH-PHASE for expert panel protocols and governance framework design

---

### Phase Ordering Rationale

**Dependency chain:**
1. RAG infrastructure blocks all features requiring grounding (90% of table stakes)
2. Hallucination detection blocks safety-critical features (gates Phases 2, 4, 6, 7)
3. Dataset expansion blocks fine-tuning (Phase 3 → Phase 5/6)
4. Small test validates approach before expensive full training (Phase 5 → Phase 6)
5. Domain services establish validation criteria before fine-tuning (Phase 4 → Phase 5/6)
6. Hybrid integration requires both RAG and fine-tuning complete (Phase 1-6 → Phase 7)

**Pitfall mitigation through ordering:**
- RAG first reduces hallucination risk during fine-tuning (addresses Pitfall 1)
- Small test before full training prevents catastrophic forgetting (addresses Pitfall 2)
- Dataset phase with diversity enforcement prevents bias amplification (addresses Pitfall 3)
- Early baseline evaluation with private test sets prevents benchmark gaming (addresses Pitfall 5)
- Incremental validation gates catch failures early (all pitfalls)

**Architecture alignment:**
- Infrastructure layer built first (Phase 1)
- Application orchestration next (Phase 2)
- Domain services before fine-tuning (Phase 4)
- Full integration last (Phase 7)
- Clean separation of concerns maintained throughout

### Research Flags

**Phases needing deeper research during planning:**

- **Phase 3 (Dataset Expansion):** Synthetic generation quality control is critical. Need research on GPT-4o prompt engineering for legal/compliance synthesis, expert validation protocols (inter-rater reliability targets), diversity metrics for regulatory datasets, contamination detection methods. High stakes for preventing bias amplification.

- **Phase 5 (Small Fine-Tuning Test):** Hyperparameter tuning for QLoRA on compliance data is niche. Need research on optimal LoRA rank/alpha for legal domain, regularization techniques for catastrophic forgetting, early stopping criteria, hallucination monitoring during training. Limited public benchmarks for OT/ICS compliance.

- **Phase 6 (Comprehensive Fine-Tuning):** Distribution collapse detection thresholds require validation. Need research on monitoring metrics for model collapse, acceptable perplexity ranges, training data exhaustion signals, curriculum learning schedules. Active research area 2026-2027.

- **Phase 7 (Expert Validation):** Human-in-the-loop workflow patterns still evolving. Need research on expert panel composition (how many experts, what expertise mix), validation protocol design (scoring rubrics, edge case prioritization), inter-rater reliability measurement, production governance frameworks for compliance AI under 2026 regulations (EU AI Act, Colorado AI Act).

**Phases with standard patterns (skip research-phase):**

- **Phase 1 (RAG Infrastructure):** Well-documented 2026 patterns for ChromaDB + LlamaIndex + hybrid search. Official documentation sufficient.
- **Phase 2 (Baseline Evaluation):** Standard RAG evaluation methodology with established metrics (RAGAS, SelfCheckGPT).
- **Phase 4 (Domain Services):** Clean Architecture domain service patterns are mature. Apply existing project conventions.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | Docling, vstackai-law-1, ChromaDB, Unsloth, Axolotl verified via official docs and 2026 benchmarks. Hybrid search + re-ranking validated in multiple production sources. QLoRA methodology proven for domain adaptation. Only MEDIUM confidence on GPT-4o for CCoP-specific generation (validated on Singapore regs generally, not CCoP specifically). |
| Features | **HIGH** | Table stakes validated via 2026 industry standards (Clarifai, TechHQ, Promptfoo), enterprise AI evaluation research (FACTUM, MEGA-RAG), legal AI studies (Stanford 2025). Differentiators validated via domain-specific LLM evaluation research. Quality thresholds backed by project requirements (85%, <5% hallucination) and US GSA CUI standards. Anti-features validated via legal AI hallucination studies and compliance best practices. |
| Architecture | **HIGH** | RAG layer placement consensus clear (RAG as infrastructure per multiple 2026 sources). Hybrid pattern benefits validated (10-20% improvement in AWS guide). Adaptive routing proven (40-60% cost reduction). Clean Architecture domain service patterns mature. Build timeline (7-8 weeks) estimated from component complexity. MEDIUM confidence on ChromaDB hybrid search production performance (documented capability, needs verification at scale). |
| Pitfalls | **HIGH** | Hallucination risks extensively documented (peer-reviewed research, industry reports with specific 17-88% statistics). Catastrophic forgetting validated via recent 2025-2026 academic papers. Synthetic bias amplification confirmed via Nature publication on model collapse. RAG vulnerabilities documented in industry analyses. Evaluation gaming validated via LLM benchmark studies. Regulatory liability frameworks official (EU AI Act, Colorado law). |

**Overall confidence:** **HIGH**

Research integrates official documentation (Unsloth, Axolotl, ChromaDB, LlamaIndex), peer-reviewed academic research (catastrophic forgetting, hallucination detection, model collapse), industry standards (2026 RAG architectures, compliance AI evaluation), and regulatory frameworks (EU AI Act, US GSA standards). Multiple independent sources validate key findings. Main uncertainty areas flagged for research-phase investigation.

### Gaps to Address

Areas where research was inconclusive or needs validation during implementation:

- **GPT-4o CCoP-specific generation quality:** Validated on Singapore regulations (AutoLaw 2025) but not specifically on CCoP 2.0 document structure. Expert validation in Phase 3 will determine if GPT-4o maintains quality for compliance-specific scenarios or if alternative generation approach needed. Mitigation: Human-in-the-loop validation with >90% expert approval rate requirement.

- **ColBERT latency at scale:** Re-ranking benchmarks show 10-50ms latency, but performance on full 8-document CCoP corpus (220 clauses) unverified. May need batch optimization or alternative re-ranker if latency exceeds 100ms target. Mitigation: Benchmark in Phase 1 infrastructure setup, fallback to Qwen3-Reranker if needed.

- **Hybrid router query classification accuracy:** Multi-dimensional intent detection is 2026 best practice, but specific accuracy on CCoP compliance queries unknown. May need LLM-based classifier upgrade from rule-based heuristics if classification accuracy <80%. Mitigation: Test in Phase 2 baseline evaluation, iterate based on routing errors.

- **Expert panel inter-rater reliability:** Target >85% agreement, but optimal panel size and expertise mix for CCoP validation undefined. Phase 7 research-phase will establish protocol. Mitigation: Start with 3 experts (CCoP compliance, OT/ICS security, IT security), measure agreement, expand if needed.

- **Regulatory change monitoring procedures:** Project focuses on CCoP 2.0 Revision One snapshot, but production deployment needs update detection. Version tracking established in Phase 6, but automated retraining pipeline and change impact assessment deferred to post-MVP. Mitigation: Document versioning strategy, flag as known production gap.

- **Confidence calibration methodology:** Expected Calibration Error <0.15 target established, but calibration techniques for hybrid RAG + fine-tuned models under-researched. May need temperature scaling, Platt scaling, or ensemble calibration in Phase 7. Mitigation: Defer confidence calibration to "should have" tier if 85% accuracy achieved without it.

## Sources

### Primary (HIGH confidence)

**Official Documentation & Frameworks:**
- Unsloth Documentation — QLoRA optimization, training acceleration, memory efficiency
- Axolotl GitHub & Docs — Training orchestration, YAML configuration, LoRA/QLoRA support
- ChromaDB Official — Vector store architecture, Rust rewrite performance, metadata filtering
- LlamaIndex Documentation — RAG orchestration, query engines, hybrid retrieval
- Docling Research (2026) — Structure-aware PDF parsing, layout analysis, table extraction
- VectorStack Blog — vstackai-law-1 legal embeddings, MTEB leaderboard results
- Voyage AI Blog — voyage-law-2 domain-specific embeddings, legal retrieval benchmarks

**Peer-Reviewed Research:**
- FACTUM: Mechanistic Detection of Citation Hallucination in Long-Form RAG (arXiv, January 2026)
- Learning and Forgetting Unsafe Examples in Large Language Models (arXiv 2312.12736)
- Chained Tuning Leads to Biased Forgetting (arXiv 2412.16469)
- AI models collapse when trained on recursively generated data (Nature, 2024)
- Large Legal Fictions: Profiling Legal Hallucinations in LLMs (Journal of Legal Analytics, 2025)
- AutoLaw: Singapore Regulations LLM (arXiv, 2025)

**Industry Standards:**
- AWS ML Blog: Tailoring Foundation Models (RAG, Fine-Tuning, Hybrid Approaches)
- Building Production RAG Systems in 2026 (Complete Architecture Guide)
- Advanced RAG Techniques (Neo4j, Superlinked, Meilisearch)
- Adaptive RAG: Query Routing and Performance (Meilisearch, 2026)
- Domain-Driven RAG (InfoQ, 2026)

### Secondary (MEDIUM confidence)

**Industry Analysis & Best Practices:**
- RAG vs Fine-Tuning Enterprise AI Strategy (Matillion, 2026)
- Comparing LLM Fine-Tuning Frameworks: Axolotl, Unsloth, TorchTune (Spheron, 2026)
- Top Rerankers for RAG Pipelines 2026 (Analytics Vidhya, SiliconFlow)
- LLM Evaluation Tools 2026 (TechHQ, Clarifai, Promptfoo)
- Hallucination Detection and Mitigation (arXiv, Lakera, Datadog)
- Human-in-the-Loop Review Workflows (Comet, ScienceDirect)

**Compliance & Regulatory:**
- AI Compliance Challenges 2026 (AIM Multiple)
- AI Risk & Compliance 2026: Enterprise Governance (Secure Privacy AI)
- Global AI Regulations: Enforcement, Risks & Fines (Tech Research Online)
- EU AI Act official framework (penalties up to €35M or 7% revenue)
- Colorado AI Act (individual liability for AI harms)

### Tertiary (LOW confidence, needs validation)

**Emerging Research:**
- Confidence calibration techniques for hybrid models (active research 2026-2027)
- OT/ICS compliance benchmarking (limited public datasets)
- Expert validation protocols for compliance AI (evolving standards)
- Synthetic data quality metrics for regulatory domains (SynLexLM research, needs replication)

**Gaps identified for validation:**
- GPT-4o performance on CCoP 2.0 specifically (validated on Singapore regs generally)
- ChromaDB hybrid search at 220-clause scale (documented capability, performance unverified)
- Expert panel inter-rater reliability targets for compliance AI (no industry standard yet)

---
*Research completed: 2026-02-04*
*Ready for roadmap: yes*
