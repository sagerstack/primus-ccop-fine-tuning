# Domain Pitfalls: Compliance AI Systems

**Domain:** Regulatory Compliance AI for Critical Infrastructure
**Researched:** 2026-02-04
**Confidence:** HIGH

---

## Executive Summary

Compliance AI systems face unique pitfalls due to high-stakes regulatory environments where errors have legal, financial, and safety consequences. This document catalogs critical mistakes identified through research on LLM hallucination, fine-tuning failures, RAG system vulnerabilities, evaluation methodology traps, dataset quality issues, and production deployment risks.

**Most Critical Finding:** Hallucination rates in specialized legal AI tools range from 17-88%, yet compliance systems require near-zero tolerance. The gap between current capabilities and regulatory requirements creates significant liability exposure.

---

## Critical Pitfalls

Mistakes that cause rewrites, regulatory penalties, or security breaches.

### Pitfall 1: Hallucinated Regulatory Citations

**What goes wrong:** LLMs fabricate non-existent regulatory clauses, cite wrong clause numbers, or invent compliance requirements.

**Why it happens:**
- Training data contains approximations of regulatory language
- Model interpolates between known clauses to fill gaps
- Pressure to provide answers leads to confident fabrication
- Legal hallucination rates: 17-88% across specialized tools

**Consequences:**
- Compliance teams act on fictitious requirements
- Audit failures when cited clauses don't exist
- Regulatory penalties for non-compliance with actual requirements
- Legal liability for incorrect compliance advice
- Industry reports: $47M in legal settlements from incorrect citations in 2025

**Prevention:**
1. **Citation Validation Pipeline**
   - Cross-reference every cited clause against authoritative source
   - Automated clause existence verification
   - Confidence scoring for citation accuracy

2. **Strict Retrieval Requirements**
   - RAG systems must return exact clause text
   - No generation of clause numbers, only retrieval
   - Empty response preferred over hallucinated citation

3. **Zero-Tolerance Testing**
   - B3 Hallucination Rate benchmark mandatory for deployment
   - Test with non-existent clause queries
   - Measure "I don't know" vs fabrication rate

**Detection:**
- Model cites clause numbers not in official documentation
- Clause text doesn't match authoritative source
- Citations reference outdated or superseded clauses
- Inconsistent clause numbering patterns

**Phase Assignment:**
- **Phase 2 (Baseline Screening):** Establish zero-hallucination baseline requirement
- **Phase 4 (Small Fine-tuning Test):** Validate that fine-tuning doesn't introduce hallucination
- **Phase 7 (Production Validation):** Expert review of all citations before deployment

**Sources:**
- [Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models](https://academic.oup.com/jla/article/16/1/64/7699227)
- [Hallucinating Law: Legal Mistakes with Large Language Models](https://hai.stanford.edu/news/hallucinating-law-legal-mistakes-large-language-models-are-pervasive)

---

### Pitfall 2: Catastrophic Forgetting During Sequential Fine-Tuning

**What goes wrong:** Model loses general cybersecurity knowledge or IT-specific knowledge when fine-tuned on OT/ICS sections.

**Why it happens:**
- Sequential training on IT sections then OT sections overwrites earlier learning
- Parameter updates for new domain erase previous domain weights
- Insufficient regularization during fine-tuning
- Chained tuning leads to biased forgetting

**Consequences:**
- Model performs well on most recent training data but fails on earlier sections
- IT compliance checking degrades after OT fine-tuning
- Need to retrain from scratch, losing time and compute
- Production deployment blocked due to inconsistent performance

**Prevention:**
1. **Unified Training Strategy**
   - Train on all 11 CCoP sections simultaneously
   - No sequential IT-then-OT training
   - Balanced sampling across all sections

2. **Parameter-Efficient Fine-Tuning**
   - QLoRA keeps base model frozen
   - Only adapter weights updated
   - Reduces catastrophic forgetting risk

3. **Regularization Techniques**
   - Hierarchical layer-wise regularization
   - Element-wise importance weighting
   - Sharpness-aware minimization

4. **Continuous Validation**
   - Test all sections after each training epoch
   - Early detection of performance degradation
   - Stop training if any section performance drops

**Detection:**
- Validation loss increases while training loss decreases
- Performance on early sections degrades over training
- Model accuracy diverges across CCoP sections
- Perplexity increases on held-out early section examples

**Phase Assignment:**
- **Phase 4 (Small Fine-tuning Test):** Test for forgetting with small dataset before full training
- **Phase 6 (Comprehensive Fine-Tuning):** Monitor all sections during training
- **Phase 7 (Production Validation):** Validate performance across all 11 sections equally

**Sources:**
- [Learning and Forgetting Unsafe Examples in Large Language Models](https://arxiv.org/abs/2312.12736)
- [Chained Tuning Leads to Biased Forgetting](https://arxiv.org/abs/2412.16469)
- [How to Alleviate Catastrophic Forgetting in LLMs Finetuning](https://arxiv.org/abs/2501.13669)

---

### Pitfall 3: Synthetic Dataset Bias Amplification

**What goes wrong:** AI-generated training data inherits and amplifies biases from the base model, creating monotonous, biased datasets.

**Why it happens:**
- LLMs reflect biases in their training data
- Synthetic generation propagates these biases to new examples
- Self-training on synthetic data creates "model collapse"
- Diversity decreases with each generation iteration
- Bias inheritance through data augmentation

**Consequences:**
- Model overfits to specific compliance patterns, missing edge cases
- Underrepresentation of minority scenarios (e.g., OT-specific, rare CCoP clauses)
- Loss of distribution diversity leads to brittle production performance
- Model collapse: increasingly irrelevant, nonsensical outputs over iterations
- Predictions available between 2026-2032: world runs out of quality training data

**Prevention:**
1. **Human-in-the-Loop Validation**
   - Expert review of synthetic examples before inclusion
   - Discard low-quality synthetic data
   - Blend synthetic and real-world data

2. **Diversity Enforcement**
   - Stratified sampling across all 11 CCoP sections
   - Balanced IT/OT representation
   - Coverage metrics for rare clauses

3. **Quality Filtering**
   - Automated quality scoring before inclusion
   - Multi-model consensus for example validation
   - Reject examples with low confidence scores

4. **Grounding in Real Data**
   - Start with real CCoP document examples
   - Synthetic variations of real scenarios only
   - Never train solely on synthetic data

5. **Verification Pipeline**
   - Filter synthetic data with verifier model
   - Cross-validate with alternative generation method
   - Measure distribution drift from authoritative sources

**Detection:**
- Training examples cluster around common patterns
- Underrepresentation of specific CCoP sections
- Synthetic examples look formulaic or repetitive
- Model performance drops on real-world edge cases
- Statistical tests show distribution drift

**Phase Assignment:**
- **Phase 5 (Full Dataset Creation):** Implement diversity metrics and quality filtering
- **Phase 6 (Comprehensive Fine-Tuning):** Monitor for distribution collapse during training
- **Phase 7 (Production Validation):** Test against real-world scenarios not in training set

**Sources:**
- [In-Context Bias Propagation in LLM-Based Tabular Data Generation](https://arxiv.org/html/2506.09630)
- [Understanding and Mitigating the Bias Inheritance in LLM-based Data Augmentation](https://arxiv.org/html/2502.04419v1)
- [AI models collapse when trained on recursively generated data](https://www.nature.com/articles/s41586-024-07566-y)
- [AI training in 2026: anchoring synthetic data in human truth](https://invisibletech.ai/blog/ai-training-in-2026-anchoring-synthetic-data-in-human-truth)

---

### Pitfall 4: RAG Retrieval Failures and Poisoned Documents

**What goes wrong:** Retrieval system returns irrelevant documents, truncates critical context, or retrieves poisoned documents with malicious content.

**Why it happens:**
- Embedding models fail to capture regulatory nuance
- Multi-hop reasoning requires multiple document chunks
- Context window limits force truncation of long clauses
- Security vulnerabilities: BadRAG and TrojanRAG attacks
- Sensitive data leakage through retrieval

**Consequences:**
- Model answers based on wrong regulatory section
- Critical compliance requirements omitted from context
- Poisoned documents trigger specific harmful behaviors
- Privacy violations when regulated data exposed
- Audit failures due to incorrect source attribution

**Prevention:**
1. **Retrieval-Native Access Control**
   - Document-level permissions
   - Role-based access to compliance sections
   - Audit logging of all retrievals

2. **Multi-Hop Reasoning Support**
   - Iterative retrieval for complex questions
   - Cross-reference validation
   - Clause relationship mapping

3. **Provenance Tracking**
   - Link every response to source documents
   - Version tracking for regulatory changes
   - Automated compliance documentation

4. **Security Controls**
   - Document validation before indexing
   - Anomaly detection for poisoned content
   - Isolated retrieval environment

5. **Retrieval Precision Testing**
   - Benchmark retrieval accuracy separately
   - Test multi-hop reasoning scenarios
   - Validate context window handling

**Detection:**
- Model cites irrelevant sections for queries
- Answers lack critical details from authoritative sources
- Performance degrades on multi-clause questions
- Unexpected document retrievals
- Security alerts for anomalous retrieval patterns

**Phase Assignment:**
- **Phase 3 (Comprehensive Baseline):** Test RAG capabilities if using retrieval
- **Phase 5 (Full Dataset Creation):** Include multi-hop reasoning scenarios
- **Phase 7 (Production Validation):** Security assessment of retrieval system

**Sources:**
- [Enhancing the Precision and Interpretability of RAG in Legal Technology](https://ieeexplore.ieee.org/document/10921633/)
- [RAG in 2026: How Retrieval-Augmented Generation Works for Enterprise AI](https://www.techment.com/blogs/blogs-rag-in-2026-enterprise-ai/)
- [The Next Frontier of RAG: Enterprise Knowledge Systems 2026-2030](https://nstarxinc.com/blog/the-next-frontier-of-rag-how-enterprise-knowledge-systems-will-evolve-2026-2030/)

---

### Pitfall 5: Evaluation Metric Gaming and Benchmark Overfitting

**What goes wrong:** Model optimizes for benchmark metrics without improving real-world compliance performance.

**Why it happens:**
- Public benchmarks allow direct overfitting
- Metrics like BLEU/ROUGE don't measure compliance accuracy
- "Benchmaxxing": optimizing for popularity over performance
- Contamination: test data leaks into training
- Models memorize benchmark answers instead of learning reasoning

**Consequences:**
- High benchmark scores but poor production performance
- Fails on actual compliance scenarios not in benchmarks
- False confidence in deployment readiness
- Regulatory failures despite passing internal tests
- Research credibility damaged

**Prevention:**
1. **Private Held-Out Test Sets**
   - Keep test cases separate from training
   - No model access to test data during development
   - Multiple test set versions for different phases

2. **Domain-Specific Metrics**
   - Compliance-specific scoring (not generic NLP metrics)
   - Citation accuracy measurement
   - Hallucination detection
   - Expert agreement rates

3. **Contamination Detection**
   - Test for benchmark memorization
   - Novel test case generation
   - Dynamic benchmark updates

4. **Multi-Method Validation**
   - 70% automated + 20% LLM-judge + 10% human expert
   - No single metric determines success
   - Real-world scenario testing

5. **Progressive Difficulty**
   - From simple interpretation to complex analysis
   - Edge cases and adversarial examples
   - Cross-section reasoning tests

**Detection:**
- Perfect scores on benchmarks but poor production performance
- Model performs worse on novel test cases
- High variance between benchmark and real-world metrics
- Suspiciously good performance on specific benchmarks
- Model outputs match benchmark examples verbatim

**Phase Assignment:**
- **Phase 2 (Baseline Screening):** Establish uncontaminated test set
- **Phase 4 (Small Fine-tuning Test):** Validate no benchmark memorization
- **Phase 7 (Production Validation):** Novel test cases not in any prior benchmarks

**Sources:**
- [LLM benchmarks in 2026: What they prove and what your business actually needs](https://www.lxt.ai/blog/llm-benchmarks/)
- [Pitfalls of Evaluating Language Models with Open Benchmarks](https://arxiv.org/html/2507.00460v1)
- [A benchmark of expert-level academic questions to assess AI capabilities](https://www.nature.com/articles/s41586-025-09962-4)

---

## Moderate Pitfalls

Mistakes that cause delays or technical debt.

### Pitfall 6: Insufficient Expert Validation

**What goes wrong:** LLM-as-judge evaluations disagree with domain experts, or expert annotation quality varies.

**Why it happens:**
- GPT-4 as judge achieves only 80% agreement with humans
- SMEs agree with LLM judgments only 68% of the time
- Criteria drift: evaluators refine criteria mid-evaluation
- Hallucination rate of 28.6% in LLM judges
- Expert availability constraints lead to insufficient validation

**Consequences:**
- Model deployed with undetected compliance errors
- Expert review reveals failures after significant development
- Inconsistent evaluation standards across test cases
- Production incidents due to missed edge cases

**Prevention:**
- Inter-rater reliability >85% requirement
- Multiple expert reviewers for critical test cases
- Clear calibration guidelines for annotators
- Structured review protocols combining automated + expert
- Continuous alignment measurement of automated evaluators vs experts

**Detection:**
- Low agreement rates between evaluators
- Expert feedback contradicts LLM-judge scores
- Inconsistent scoring across similar test cases
- Expert discovery of errors missed by automated evaluation

**Phase Assignment:**
- **Phase 5 (Full Dataset Creation):** Measure inter-rater reliability for generated examples
- **Phase 7 (Production Validation):** Expert review panel for final approval

**Sources:**
- [Beyond Blind Spots: Analytic Hints for Mitigating LLM-Based Evaluation Pitfalls](https://research.ibm.com/publications/beyond-blind-spots-analytic-hints-for-mitigating-llm-based-evaluation-pitfalls)
- [LLM as a Judge: A 2026 Guide to Automated Model Assessment](https://labelyourdata.com/articles/llm-as-a-judge)

---

### Pitfall 7: IT/OT Classification Failures

**What goes wrong:** Model incorrectly determines whether CCoP clauses apply to IT-only, OT-only, or both infrastructure types.

**Why it happens:**
- 60% of CCoP clauses are cross-cutting (apply to both)
- Training data imbalance favors IT scenarios
- OT-specific terminology underrepresented
- Model lacks physical infrastructure context

**Consequences:**
- CII organizations implement controls in wrong infrastructure
- Audit failures for misclassified requirements
- Security gaps in OT environment
- Wasted resources on inapplicable IT controls

**Prevention:**
- Balanced IT/OT representation in training data (60% cross-cutting)
- Dedicated B5 benchmark for IT/OT classification
- OT-specific examples from Section 10 (ICS/SCADA)
- Cross-validation with OT domain experts

**Detection:**
- Model classifies cross-cutting clauses as IT-only
- Poor performance on Section 10 (OT/ICS)
- Confusion between SCADA and traditional IT systems
- Expert reviewers flag classification errors

**Phase Assignment:**
- **Phase 3 (Comprehensive Baseline):** Assess IT/OT classification capability
- **Phase 5 (Full Dataset Creation):** Ensure 300+ OT-specific examples
- **Phase 7 (Production Validation):** OT expert validation

---

### Pitfall 8: Regulatory Change Lag

**What goes wrong:** Model trained on current CCoP 2.0 becomes outdated when regulations update.

**Why it happens:**
- No temporal awareness in model architecture
- Training locked to specific regulatory snapshot
- No monitoring for regulatory amendments
- Production systems continue using stale knowledge

**Consequences:**
- Compliance advice based on superseded requirements
- Audit failures for not following current standards
- Manual intervention required for every regulatory change
- Loss of trust in automated system

**Prevention:**
- Version tracking in training data
- RAG component for current regulatory text
- Automated retraining pipeline for amendments
- Temporal awareness testing (RegBERT approach)
- Change management documentation

**Detection:**
- Model references outdated clause numbers
- Misses recently added requirements
- Conflicts between model output and current regulations
- Expert reviewers identify stale guidance

**Phase Assignment:**
- **Phase 6 (Comprehensive Fine-Tuning):** Version all training data with CCoP dates
- **Phase 7 (Production Validation):** Establish regulatory change monitoring process

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable.

### Pitfall 9: Singapore-Specific Terminology Errors

**What goes wrong:** Model uses generic cybersecurity terms instead of CCoP-specific Singapore definitions.

**Why it happens:**
- Base model trained on international standards
- IMDA/CSA terminology not in general training data
- Ambiguous terms with different meanings in Singapore context

**Consequences:**
- Confusion for CII organizations expecting official terminology
- Minor misalignment with audit language
- Need for post-processing terminology normalization

**Prevention:**
- B4 benchmark for Singapore terminology
- Training examples using official IMDA/CSA definitions
- Glossary of CCoP-specific terms
- Validation against official documentation

**Detection:**
- Model uses "incident" instead of Singapore-specific event types
- Generic "firewall" vs specific CCoP control categories
- International standard references instead of CCoP clauses

**Phase Assignment:**
- **Phase 5 (Full Dataset Creation):** Include glossary-based examples
- **Phase 7 (Production Validation):** Terminology validation

---

### Pitfall 10: False Positive Rate in Code Scanning

**What goes wrong:** Model flags correct code as violating CCoP standards.

**Why it happens:**
- Training data lacks sufficient "clean code" examples
- Model overfits to common vulnerability patterns
- Edge cases trigger false alarms
- Insufficient context for code analysis

**Consequences:**
- Developer fatigue from false alarms
- Reduced trust in automated scanning
- Manual triage workload
- Opportunity cost from investigating non-issues

**Prevention:**
- B7 benchmark specifically for false positive measurement
- Balanced training data: vulnerable + clean code
- Target <5% false positive rate
- Multi-stage validation for code findings

**Detection:**
- High rate of "dismissed" findings
- Developer complaints about incorrect flagging
- Manual review overrides automated findings
- Pattern of false alarms in specific code constructs

**Phase Assignment:**
- **Phase 3 (Comprehensive Baseline):** Establish baseline false positive rate
- **Phase 5 (Full Dataset Creation):** Include 1,500+ clean code examples
- **Phase 7 (Production Validation):** Measure against <5% target

---

## Production Deployment Pitfalls

### Pitfall 11: Liability and Regulatory Exposure

**What goes wrong:** Production deployment creates legal liability when AI provides incorrect compliance advice.

**Why it happens:**
- 2026 regulatory environment enforces strict AI accountability
- EU AI Act: penalties up to €35M or 7% global revenue
- Colorado AI Act: individuals can sue for AI-related harms
- EEOC: employers liable for discriminatory AI outcomes
- EU Product Liability Directive: AI systems as "defective products"

**Consequences:**
- Direct financial penalties for non-compliance
- Legal liability for incorrect compliance advice
- Regulatory sanctions and enforcement actions
- Reputational damage and loss of customer trust
- CII organizations face audit failures and penalties

**Prevention:**
1. **Documented Governance**
   - AI risk management framework
   - Compliance documentation
   - Decision audit trails

2. **Human-in-the-Loop Requirements**
   - Expert review before acting on AI advice
   - Clear disclaimers about AI limitations
   - Human accountability for final decisions

3. **Ongoing Monitoring**
   - Production performance tracking
   - Hallucination detection
   - Regular accuracy audits

4. **Regulatory Compliance Controls**
   - EU AI Act high-risk system requirements
   - Mandatory compliance before deployment
   - Explainability and transparency

5. **Liability Framework**
   - Clear responsibility allocation
   - Insurance considerations
   - Incident response procedures

**Detection:**
- Production incidents with compliance impact
- Regulatory inquiries or enforcement actions
- User complaints about incorrect advice
- Audit findings related to AI recommendations

**Phase Assignment:**
- **Phase 7 (Production Validation):** Legal review and liability framework
- **Post-deployment:** Continuous monitoring and compliance validation

**Sources:**
- [AI Compliance: Top 6 challenges & case studies in 2026](https://research.aimultiple.com/ai-compliance/)
- [AI Risk & Compliance 2026: Enterprise Governance Overview](https://secureprivacy.ai/blog/ai-risk-compliance-2026)
- [Global AI Regulations in 2026: Enforcement, Risks & Fines](https://techresearchonline.com/blog/global-ai-regulations-enforcement-guide/)

---

## Phase-Specific Warnings

| Phase | Likely Pitfall | Mitigation |
|-------|---------------|------------|
| Phase 2 (Baseline Screening) | Hallucinated citations accepted as valid | Implement B3 hallucination detection, zero-tolerance requirement |
| Phase 3 (Comprehensive Baseline) | Benchmark overfitting if test set reused | Create separate test sets for each phase |
| Phase 4 (Small Fine-tuning Test) | Catastrophic forgetting on IT sections after OT training | Monitor all sections during training, not just recent data |
| Phase 5 (Full Dataset Creation) | Synthetic data bias amplification | Human validation, diversity metrics, quality filtering |
| Phase 5 (Full Dataset Creation) | Insufficient OT/ICS representation | Dedicated 300+ OT examples, balanced IT/OT sampling |
| Phase 6 (Comprehensive Fine-tuning) | Model collapse from iterative synthetic training | Blend real and synthetic data, verification pipeline |
| Phase 6 (Comprehensive Fine-tuning) | Distribution shift from authoritative sources | Regular validation against official CCoP documents |
| Phase 7 (Production Validation) | Expert validation reveals systematic failures | Early expert engagement, iterative validation cycles |
| Phase 7 (Production Validation) | Deployment without liability framework | Legal review, governance documentation, human-in-loop controls |
| Production | Regulatory change makes model outdated | Monitoring pipeline, automated retraining capability |

---

## Critical Success Factors

Based on identified pitfalls, these factors are essential for project success:

### 1. Zero-Tolerance Hallucination Policy
- No hallucinated citations acceptable in compliance context
- B3 benchmark mandatory gate at every phase
- Citation validation against authoritative sources

### 2. Unified Training Strategy
- Train all 11 CCoP sections simultaneously
- No sequential IT-then-OT approach
- Continuous validation across all sections

### 3. Human-in-the-Loop Validation
- Expert review of synthetic training data
- Multi-expert validation for test cases
- Inter-rater reliability >85% requirement

### 4. Multi-Method Evaluation
- 70% automated + 20% LLM-judge + 10% human expert
- Domain-specific metrics, not generic NLP metrics
- Real-world scenario validation

### 5. Comprehensive Security Controls
- RAG retrieval access control
- Poisoned document detection
- Audit trail for all compliance recommendations

### 6. Production Governance Framework
- Regulatory compliance documentation
- Liability allocation framework
- Ongoing monitoring and validation

---

## Research Confidence Assessment

| Pitfall Category | Confidence | Source Quality |
|-----------------|------------|---------------|
| Hallucination Risks | HIGH | Peer-reviewed research, industry reports with specific statistics |
| Fine-Tuning Failures | HIGH | Recent 2025-2026 academic papers on catastrophic forgetting |
| RAG Vulnerabilities | MEDIUM | Industry analyses, some recent research |
| Evaluation Traps | HIGH | Multiple sources on benchmark gaming, expert validation |
| Dataset Quality | HIGH | Nature publication on model collapse, multiple 2026 studies |
| Regulatory Liability | HIGH | Official regulatory frameworks (EU AI Act, Colorado law) |

---

## Gaps Requiring Phase-Specific Research

1. **Phase 4:** Optimal hyperparameters for CCoP fine-tuning to minimize catastrophic forgetting
2. **Phase 5:** Specific diversity metrics for regulatory compliance datasets
3. **Phase 6:** Monitoring thresholds for detecting distribution collapse during training
4. **Phase 7:** Expert panel composition and validation protocol design
5. **Production:** Regulatory change monitoring and automated retraining procedures

---

## Conclusion

Compliance AI systems face documented pitfalls with hallucination rates (17-88%), catastrophic forgetting, dataset bias amplification, and regulatory liability exposure. The CCoP 2.0 project's phased approach with critical checkpoints, zero-hallucination requirements, and expert validation directly addresses these risks.

**Most Critical Mitigations:**
1. Zero-tolerance hallucination policy with B3 benchmark gating
2. Unified training to prevent catastrophic forgetting
3. Human-in-the-loop validation for synthetic data and production deployment
4. Multi-method evaluation (automated + LLM-judge + expert)
5. Comprehensive governance framework for regulatory compliance

The research provides high-confidence warnings for 11 specific pitfalls with actionable prevention strategies and phase assignments for the CCoP 2.0 fine-tuning project.

---

## Sources

### Hallucination & Regulatory Compliance
- [Hallucination Rates in 2025 — Accuracy, Refusal, and Liability](https://medium.com/@markus_brinsa/hallucination-rates-in-2025-accuracy-refusal-and-liability-aa0032019ca1)
- [Managing hallucination risk in LLM deployments at the EY organization](https://www.ey.com/en_gl/technical/enterprise-solution-guides-technology-leaders/managing-hallucination-risk-in-llm-deployments-at-the-ey-organization)
- [Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models](https://academic.oup.com/jla/article/16/1/64/7699227)
- [Hallucinating Law: Legal Mistakes with Large Language Models](https://hai.stanford.edu/news/hallucinating-law-legal-mistakes-large-language-models-are-pervasive)

### Catastrophic Forgetting
- [An Empirical Study of Catastrophic Forgetting in Large Language Models During Continual Fine-tuning](https://arxiv.org/abs/2308.08747)
- [How to Alleviate Catastrophic Forgetting in LLMs Finetuning?](https://arxiv.org/abs/2501.13669)
- [Learning and Forgetting Unsafe Examples in Large Language Models](https://arxiv.org/abs/2312.12736)
- [Chained Tuning Leads to Biased Forgetting](https://arxiv.org/abs/2412.16469)

### RAG Failures
- [Enhancing the Precision and Interpretability of Retrieval-Augmented Generation (RAG) in Legal Technology](https://ieeexplore.ieee.org/document/10921633/)
- [The Next Frontier of RAG: How Enterprise Knowledge Systems Will Evolve (2026-2030)](https://nstarxinc.com/blog/the-next-frontier-of-rag-how-enterprise-knowledge-systems-will-evolve-2026-2030/)
- [RAG in 2026: How Retrieval-Augmented Generation Works for Enterprise AI](https://www.techment.com/blogs/blogs-rag-in-2026-enterprise-ai/)

### Evaluation & Benchmarking
- [LLM benchmarks in 2026: What they prove and what your business actually needs](https://www.lxt.ai/blog/llm-benchmarks/)
- [Pitfalls of Evaluating Language Models with Open Benchmarks](https://arxiv.org/html/2507.00460v1)
- [A benchmark of expert-level academic questions to assess AI capabilities](https://www.nature.com/articles/s41586-025-09962-4)
- [Beyond Blind Spots: Analytic Hints for Mitigating LLM-Based Evaluation Pitfalls](https://research.ibm.com/publications/beyond-blind-spots-analytic-hints-for-mitigating-llm-based-evaluation-pitfalls)

### Synthetic Data & Model Collapse
- [In-Context Bias Propagation in LLM-Based Tabular Data Generation](https://arxiv.org/html/2506.09630)
- [Understanding and Mitigating the Bias Inheritance in LLM-based Data Augmentation](https://arxiv.org/html/2502.04419v1)
- [AI models collapse when trained on recursively generated data](https://www.nature.com/articles/s41586-024-07566-y)
- [AI training in 2026: anchoring synthetic data in human truth](https://invisibletech.ai/blog/ai-training-in-2026-anchoring-synthetic-data-in-human-truth)
- [Model collapse explained: How synthetic training data breaks AI](https://www.techtarget.com/whatis/feature/Model-collapse-explained-How-synthetic-training-data-breaks-AI)

### Regulatory & Liability
- [AI Compliance: Top 6 challenges & case studies in 2026](https://research.aimultiple.com/ai-compliance/)
- [How AI will redefine compliance, risk and governance in 2026](https://www.governance-intelligence.com/regulatory-compliance/how-ai-will-redefine-compliance-risk-and-governance-2026)
- [AI Risk & Compliance 2026: Enterprise Governance Overview](https://secureprivacy.ai/blog/ai-risk-compliance-2026)
- [2026 AI Legal Forecast: From Innovation to Compliance](https://www.bakerdonelson.com/2026-ai-legal-forecast-from-innovation-to-compliance)
- [Global AI Regulations in 2026: Enforcement, Risks & Fines](https://techresearchonline.com/blog/global-ai-regulations-enforcement-guide/)
