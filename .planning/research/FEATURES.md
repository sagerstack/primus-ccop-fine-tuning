# Feature Landscape: CCoP 2.0 Compliance Assistant

**Domain:** Regulatory compliance assistant for Critical Information Infrastructure
**Researched:** 2026-02-04
**Overall Confidence:** HIGH

---

## Executive Summary

A CCoP 2.0 compliance assistant for CII organizations requires capabilities spanning query understanding, accurate response generation, source grounding, and safety guardrails. This research categorizes features based on regulatory compliance assistant requirements in 2026, analyzing both established patterns and emerging best practices.

**Key Finding:** The feature set divides into three clear tiers:
1. **Table stakes** (15 features): Requirements without which the system is unusable for compliance work
2. **Differentiators** (8 features): Capabilities that elevate quality and user trust
3. **Anti-features** (6 features): Common mistakes that undermine regulatory utility

**Critical Dependencies:** Citation accuracy and hallucination detection are foundational. Without these, no other feature provides value in a compliance context.

---

## Table Stakes Features

Features that compliance teams expect. Missing any of these renders the product incomplete or unusable for regulatory work.

| Feature | Why Expected | Complexity | Implementation Notes |
|---------|--------------|------------|---------------------|
| **Clause Citation Accuracy** | Compliance professionals must trace advice to specific regulatory text. 2026 standards require policy grounding with retrieval from approved sources, citations, and version control. | High | RAG-based retrieval with clause-level chunking. FACTUM framework (Jan 2026) provides mechanistic citation hallucination detection using Contextual Alignment, Attention Sink Usage, Parametric Force, and Pathway Alignment scores. |
| **Source Grounding** | Every response must be traceable to official CCoP 2.0 documents. Audit readiness requires automatic evidence logs and decision trails. | High | Document retrieval with confidence scoring. Multi-evidence guided answer refinement (MEGA-RAG framework). Responses must include explicit references to source paragraphs/clauses. |
| **Hallucination Detection** | Legal/compliance AI tools from LexisNexis and Thomson Reuters hallucinate 17-33% despite "hallucination-free" claims. CCoP context demands <5% hallucination rate. | High | LLM-as-a-judge combined with deterministic checks. Guardian agents becoming mainstream in 2026. Detection using factual grounding metrics, retrieval quality checks, and compliance risk monitoring. |
| **Singapore Terminology Accuracy** | CCoP uses specific terms (CIIO, CSA, Commissioner, CII) with precise regulatory meanings. Misuse indicates lack of domain grounding. | Medium | Fine-tuned model awareness + terminology validation layer. Reference official glossary from CCoP 2.0 PDF. Domain-specific evaluation required. |
| **IT vs OT Context Classification** | 60% of CCoP clauses are cross-cutting (IT+OT), 35-40 clauses are OT-only (ICS/SCADA). Incorrect classification leads to compliance gaps or over-engineering. | Medium | Intent classification to determine infrastructure context. Multi-dimensional intent detection: definitional, procedural, comparative, conditional queries. |
| **Query Intent Understanding** | Compliance questions have multiple dimensions: intent type (definitional/procedural/comparative), complexity level, domain focus, expected answer type. | Medium | Multi-dimensional intent classifier. When user asks about compliance penalties: simple yes/no vs detailed breakdown vs appeal process vs specific examples each require different retrieval/response strategies. |
| **Uncertainty Expression** | Model must refuse or express low confidence when evidence is insufficient. 67% CEO vs 54% CISO/CSO confidence gap in AI regulation compliance indicates trust challenges. | Medium | Confidence scoring per response. Conditional reasoning language ("depends on implemented controls") is appropriate for compliance—NOT a weakness. Guard bands reduce risk of incorrect decisions. |
| **Compliance-Appropriate Refusal** | Must decline to provide advice on attack methodologies, fabricate compliance evidence, or speculate on audit outcomes without sufficient context. | Medium | Safety benchmarks (B13-B14): prompt injection resistance, jailbreak resistance. Refusal behavior must explain why request can't be answered safely. |
| **Key Facts Extraction** | Responses must cover 3-8 atomic, verifiable statements representing essential compliance requirements. Completeness measured by key-fact coverage, not sentence-level overlap. | Medium | Structured output generation. Key facts are short, atomic statements derived from ground-truth (regulatory text). Example: "Password length minimum 12 characters" as single fact. |
| **Clause Reference Validation** | Citations must be verifiable against official CCoP 2.0 Second Edition Revision One PDF. Fabricated clause numbers are a critical failure mode. | High | Automated validation against official document corpus. Each citation validated before returning to user. Mismatch triggers confidence downgrade or refusal. |
| **Audit Trail Generation** | Every query-response pair logged with sources, confidence scores, and timestamps for compliance review. Regulatory environments require demonstrable decision lineage. | Low | Structured logging with immutable records. Platform integration (e.g., Weave) provides durable audit trail showing exact test scores, human reviews, safety checks before production promotion. |
| **Semantic Equivalence Recognition** | Audit-style explanations and correct paraphrases must score appropriately. Lexical similarity (Jaccard) is insufficient for reasoning-based compliance questions. | High | Embeddings-based semantic matching. Reasoning benchmarks require semantic equivalence assessment, not keyword matching. Accept multiple valid formulations of same requirement. |
| **Entity Extraction** | Identify regulatory entities: specific clauses, requirements, controls, responsible parties, affected infrastructure types. | Medium | NLP entity recognition tuned for compliance domain. Extract: regulation references, section numbers, control IDs, organizational roles (CISO, DPO, etc.). |
| **Multi-Evidence Synthesis** | Single compliance question often requires integrating facts from multiple clauses (e.g., access control + logging + incident response). | High | Multi-hop reasoning across retrieved documents. MEGA-RAG framework guides answer refinement with multiple evidence sources. Prevent contradictions when synthesizing. |
| **Response Completeness Validation** | Missing key facts renders compliance advice incomplete. Baseline expectation: 100% key fact coverage for table-stakes requirements. | Medium | Key-fact checklist verification before response finalization. Current evaluation: completeness = (# key facts covered) / (total key facts). Low completeness + low accuracy = knowledge gap. |

**Total Table Stakes: 15 features**
**Estimated effort: 6-9 months for production-grade implementation**

---

## Differentiators

Features that elevate the product beyond baseline expectations. Not required for MVP, but significantly improve trust, utility, and adoption.

| Feature | Value Proposition | Complexity | Implementation Notes |
|---------|-------------------|------------|---------------------|
| **Cross-Standard Mapping** | Map CCoP clauses to ISO 27001, NIST 800-53, IEC 62443 controls. Reduces compliance burden for multi-framework environments. | Medium | Maintain mapping database. Benchmark B12 tests this capability. Valuable for CIIs subject to multiple regulatory regimes (common in finance, healthcare). |
| **Gap Analysis Automation** | Given a SOC procedure/policy, identify missing CCoP controls, required evidence, and remediation steps. | High | Structural comparison between provided documentation and CCoP requirements. Requires understanding of compliance artifact types (policy, procedure, evidence). |
| **Policy Generation** | Generate compliant password policies, access control procedures, incident response plans referencing relevant CCoP clauses. | High | Template-based generation with clause citations. Must produce audit-ready artifacts, not generic boilerplate. Quality measured by clause relevance and practical applicability. |
| **Incident Classification** | Classify security events (e.g., ransomware + unusual outbound traffic) with severity and CCoP response obligations. | Medium | Multi-signal analysis. Output: incident type, severity, applicable response clauses, required actions. Bridges technical detection and compliance response. |
| **Human-in-the-Loop Expert Validation** | Domain experts adjudicate edge cases, calibrate scoring rubrics, validate high-stakes responses before deployment. | Medium | Workflow integration for expert review. 2026 best practice: combine automated scoring with expert validation. Financial services example: automated tests for accuracy/latency, human scoring for regulatory compliance and tone. |
| **Confidence Calibration** | Provide numeric confidence scores (0-100%) aligned with actual accuracy. Helps users decide when to escalate to legal/compliance team. | High | Calibrated uncertainty quantification. Research shows CEO/CISO confidence gap (67% vs 54%) in AI compliance—accurate confidence reduces this. Guard bands provide simple decision rules. |
| **IaC Misconfiguration Detection** | Identify security misconfigurations in Terraform, Kubernetes, AWS Security Groups against CCoP requirements (open ports, public access, missing least-privilege). | High | Code-level analysis mapped to CCoP clauses. Benchmark B8 tests this. Requires understanding both infrastructure patterns and regulatory requirements. Complements SAST/SCA tools. |
| **Query Clarification Dialogue** | When intent is ambiguous, ask clarifying questions before answering. Examples: "Are you asking about IT or OT infrastructure?" or "Do you need implementation guidance or audit preparation?" | Medium | Intent classifier uncertainty triggers clarification. Modern intent detection operates across multiple dimensions—detecting ambiguity is as important as classification. |

**Total Differentiators: 8 features**
**Estimated effort: 4-6 months for full suite**

---

## Anti-Features

Features to explicitly NOT build. Common mistakes in compliance AI that undermine regulatory utility or create false confidence.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Generalized Compliance Advice** | CCoP is Singapore-specific for CII. Generic "best practices" dilute regulatory precision and may not satisfy CSA requirements. | Always ground in CCoP 2.0 official text. If answer isn't in CCoP, say so explicitly and offer to reference supplementary guidance documents if relevant. |
| **Over-Confident Uncertain Answers** | Expressing high confidence on low-evidence responses creates compliance risk. 17-33% hallucination rate in "hallucination-free" legal AI tools shows the danger. | Calibrate confidence to evidence strength. Use guard bands and refusal criteria. "I'm not certain" is more valuable than confidently wrong. |
| **Citation-Free Responses** | Compliance advice without source references is unusable for audit preparation. 2026 standard: policy grounding requires retrieval from approved sources with citations and version control. | Never provide compliance interpretation without clause citation. If source unclear, refuse rather than speculate. |
| **Keyword-Only Matching** | Lexical similarity (Jaccard, keyword overlap) fails on reasoning-based compliance questions. "Access control must restrict unauthorized users" vs "Implement least-privilege access" are semantically equivalent but lexically different. | Use embeddings-based semantic matching. Accept multiple valid formulations. Benchmark-aware scoring distinguishes classification (label matching) from reasoning (semantic equivalence). |
| **Attack Methodology Guidance** | Providing step-by-step exploitation techniques, even when couched as "security testing," creates liability and violates responsible AI principles. | Decline with explanation: "I can discuss security controls and detection mechanisms, but not attack execution steps." Offer high-level guidance on security testing frameworks instead. |
| **Static Compliance Knowledge** | CCoP 2.0 Revision One (current) may be updated. Compliance requirements evolve. Baking knowledge into model weights means retraining for updates. | Use RAG architecture with updateable document corpus. Model provides reasoning; documents provide current requirements. Decouple reasoning capability from regulatory content. |

**Total Anti-Features: 6 features**

---

## Feature Dependencies

Critical path analysis for implementation sequencing:

```
FOUNDATIONAL LAYER (Must implement first):
├── Source Grounding (RAG infrastructure)
├── Clause Citation Accuracy (retrieval + validation)
└── Hallucination Detection (safety layer)
    │
    ├──> CORE CAPABILITIES (Depend on foundation):
    │    ├── Singapore Terminology Accuracy (domain tuning)
    │    ├── Semantic Equivalence Recognition (evaluation infrastructure)
    │    ├── Query Intent Understanding (routing logic)
    │    ├── IT vs OT Context Classification (domain classifier)
    │    └── Uncertainty Expression (confidence scoring)
    │
    └──> ADVANCED FEATURES (Depend on core + foundation):
         ├── Gap Analysis Automation (requires all core capabilities)
         ├── Policy Generation (requires citation + intent + completeness)
         ├── Cross-Standard Mapping (requires citation + semantic matching)
         ├── Incident Classification (requires context classification + entity extraction)
         ├── IaC Misconfiguration Detection (requires code analysis + clause mapping)
         └── Human-in-the-Loop Validation (requires confidence + audit trail)
```

**Critical Path:** Source Grounding → Citation Accuracy → Hallucination Detection → Core Capabilities → Advanced Features

**Blocker Dependencies:**
- RAG infrastructure blocks 90% of features
- Hallucination detection blocks all safety-critical features
- Intent classification blocks advanced query handling
- Semantic matching blocks reasoning evaluation

---

## Feature Complexity Estimates

| Complexity | Features | Estimated Implementation Time |
|-----------|----------|------------------------------|
| **Low** | Audit Trail Generation | 1-2 weeks |
| **Medium** | Singapore Terminology, IT/OT Classification, Intent Understanding, Uncertainty Expression, Refusal Behavior, Key Facts Extraction, Entity Extraction, Completeness Validation, Cross-Standard Mapping, Incident Classification, Expert Validation, Query Clarification | 2-8 weeks each |
| **High** | Clause Citation Accuracy, Source Grounding, Hallucination Detection, Clause Reference Validation, Semantic Equivalence, Multi-Evidence Synthesis, Gap Analysis, Policy Generation, Confidence Calibration, IaC Detection | 8-16 weeks each |

**MVP Timeline Estimate:**
- Foundation (3 high-complexity features): 6-12 months
- Core Capabilities (5 medium-complexity features): 3-5 months (parallel with foundation)
- Total to production-viable system: 9-15 months

---

## Evaluation Dimensions by Feature Category

| Feature Category | Primary Evaluation Metrics | Current Benchmarks |
|-----------------|---------------------------|-------------------|
| **Query Understanding** | Intent classification accuracy, entity extraction F1, context disambiguation rate | B1, B5 (IT/OT classification) |
| **Response Quality** | Semantic equivalence score, key fact recall (completeness), clause citation accuracy | B1-B12 (compliance & reasoning) |
| **Grounding & Citation** | Citation precision/recall, hallucination rate, source attribution accuracy | B2 (citation accuracy), B3 (hallucination), B20-B21 (safety) |
| **Confidence & Uncertainty** | Confidence calibration error, appropriate refusal rate, uncertainty expression quality | B13-B14 (safety), manual expert review |
| **Safety** | Prompt injection resistance, jailbreak resistance, fabrication detection | B13-B14 (adversarial), B3 (hallucination) |
| **Advanced Capabilities** | Gap analysis completeness, policy generation quality, incident classification accuracy | B9-B12 (advanced reasoning) |

**Evaluation Coverage:**
- Current benchmarks (B1-B21) cover 80% of table stakes features
- Differentiators partially covered (40% benchmark coverage)
- Anti-features covered by safety benchmarks (B13-B14) and hallucination detection (B3)

**Gaps in Current Evaluation:**
- Cross-standard mapping (B12 exists but needs expansion)
- IaC misconfiguration detection (B8 exists but limited)
- Human-in-the-loop workflows (no automated benchmark—requires expert study)
- Query clarification dialogue (requires conversation evaluation)

---

## Quality Thresholds by Feature

Based on 2026 compliance AI standards and CCoP project requirements:

| Feature | MVP Threshold | Production Threshold | Rationale |
|---------|--------------|---------------------|-----------|
| **Clause Citation Accuracy** | 75% | 95% | Compliance teams must trust citations for audit work |
| **Hallucination Rate** | <10% | <5% | Project requirement. Legal AI currently at 17-33% (unacceptable) |
| **Key Fact Coverage (Completeness)** | 70% | 90% | Missing facts create compliance gaps |
| **Semantic Equivalence** | 65% | 85% | Reasoning questions require semantic understanding |
| **IT/OT Classification** | 80% | 95% | Incorrect classification causes compliance gaps or over-engineering |
| **Uncertainty Calibration** | N/A | ECE < 0.15 | Expected Calibration Error. Confidence must match accuracy |
| **Intent Classification** | 70% | 90% | Misrouted queries get wrong response type |
| **Refusal Appropriateness** | 90% | 98% | Over-refusal frustrates users; under-refusal creates risk |

**Overall System Threshold:** 85% accuracy (project requirement, industry standard for enterprise AI compliance automation)

**Phase 2 Baseline:** 15% (diagnostic, justifies fine-tuning)
**Phase 7 Target:** 50-85% (production readiness decision point)

---

## MVP Recommendation

For a compliance assistant MVP, prioritize this sequence:

### Phase 1: Foundation (Months 1-4)
**Must have:**
1. Source Grounding (RAG infrastructure with CCoP 2.0 corpus)
2. Clause Citation Accuracy (retrieval + validation)
3. Hallucination Detection (LLM-as-judge + deterministic checks)
4. Clause Reference Validation (prevent fabricated citations)
5. Audit Trail Generation (compliance logging)

**Success criteria:** <10% hallucination, 75% citation accuracy

### Phase 2: Core Capabilities (Months 3-6, parallel)
**Must have:**
6. Singapore Terminology Accuracy (domain fine-tuning)
7. Query Intent Understanding (multi-dimensional classifier)
8. IT/OT Context Classification (infrastructure context detection)
9. Semantic Equivalence Recognition (evaluation infrastructure)
10. Uncertainty Expression (confidence scoring + refusal)
11. Key Facts Extraction (structured output)
12. Response Completeness Validation (key fact checking)

**Success criteria:** 70% semantic equivalence, 80% intent classification, 70% completeness

### Phase 3: Safety & Utility (Months 5-8)
**Must have:**
13. Compliance-Appropriate Refusal (safety guardrails)
14. Entity Extraction (regulatory entity recognition)
15. Multi-Evidence Synthesis (multi-hop reasoning)

**Differentiators (select 2-3):**
- Human-in-the-Loop Expert Validation (builds trust)
- Confidence Calibration (helps escalation decisions)
- Query Clarification Dialogue (improves UX)

**Success criteria:** 90% refusal appropriateness, 85% overall system accuracy

### Defer to Post-MVP:

**Complex Differentiators:**
- Cross-Standard Mapping (valuable but not critical for CCoP-only focus)
- Gap Analysis Automation (requires mature core capabilities first)
- Policy Generation (high complexity, lower priority)
- IaC Misconfiguration Detection (niche use case, requires code analysis expertise)
- Incident Classification (valuable but requires incident response domain expertise)

**Rationale for deferral:**
- These features depend on mature foundation + core capabilities
- High complexity-to-value ratio for initial launch
- Can be added incrementally based on user feedback
- Require additional domain expertise (ICS/SCADA for OT, code analysis for IaC)

---

## Research Confidence Assessment

| Feature Category | Confidence Level | Source Quality |
|-----------------|------------------|----------------|
| Table Stakes Features | **HIGH** | 2026 industry standards (Clarifai, TechHQ, Promptfoo, Datavid), enterprise AI evaluation research (FACTUM, MEGA-RAG), legal AI studies (Stanford 2025), compliance platform analysis (Datadog, Weave) |
| Differentiators | **HIGH** | Domain-specific LLM evaluation research (LXT.ai, Medium/Online Inference 2026), human-in-the-loop workflows (Comet, ScienceDirect), compliance automation trends (RelyComply, Truzta, KPMG) |
| Anti-Features | **MEDIUM-HIGH** | Legal AI hallucination studies (Stanford), compliance best practices (IBM, Cooley), regulatory AI trends (Pearl Cohen, Perkins Coie), project-specific analysis (CCoP evaluation methodology) |
| Complexity Estimates | **MEDIUM** | Based on project phase timelines (9-month project scope), RAG implementation complexity, fine-tuning research (QLoRA methodology) |
| Quality Thresholds | **HIGH** | Project requirements (85% accuracy, <5% hallucination), US GSA CUI standards (85% threshold), enterprise AI research (Thomson Reuters), compliance statistics (Secureframe, Centraleyes) |

**Overall Research Confidence: HIGH**

**Verification Sources:**
- Project documentation: CCoP 2.0 official PDF, ground truth establishment process, scoring methodology
- Academic research: FACTUM (Jan 2026), MEGA-RAG, legal RAG hallucinations study (Stanford 2025)
- Industry standards: 2026 LLM evaluation platforms, compliance automation trends
- Regulatory guidance: California SB 243 (Jan 2026), OMB M-26-04 (Dec 2025)

**Gaps Identified:**
- Limited public benchmarks for OT/ICS compliance (Section 10 of CCoP)
- Emerging standards for confidence calibration in compliance AI (active research area)
- Human-in-the-loop workflow patterns still evolving (2026-2027 timeframe)

---

## Sources

### Regulatory & Compliance AI (2026)
- [LLM Security Frameworks: ISO, NIST & AI Regulation](https://hacken.io/discover/llm-security-frameworks/)
- [LLM Regulatory Compliance Requirements for Enterprises](https://datavid.com/blog/what-are-llm-regulatory-compliance-requirements-for-enterprises)
- [How AI Regulation Changed in 2025](https://www.promptfoo.dev/blog/ai-regulation-2025/)
- [Chatbots in Regulatory Compliance: Proven Wins](https://digiqt.com/blog/chatbots-in-regulatory-compliance/)
- [Enhancing Regulatory Compliance with Generative AI (IBM)](https://www.ibm.com/think/insights/enhancing-regulatory-compliance-ai-age)
- [AI Chatbots: Navigating New Laws and Compliance Risks (Cooley)](https://www.cooley.com/news/insight/2025/2025-10-21-ai-chatbots-at-the-crossroads-navigating-new-laws-and-compliance-risks)
- [California Companion Chatbot Law (Perkins Coie)](https://perkinscoie.com/insights/update/california-companion-chatbot-law-now-effect)
- [2026 Compliance Trends: Planned Proactive Automations](https://relycomply.com/aml-2026-compliance-trends/)
- [What Good Compliance Looks Like in 2026](https://truzta.com/resources/blog/what-good-compliance-look-like-in-2026/)

### LLM Evaluation & Benchmarking (2026)
- [Top LLMs and AI Trends for 2026 (Clarifai)](https://www.clarifai.com/blog/llms-and-ai-trends)
- [8 LLM Evaluation Tools You Should Know in 2026](https://techhq.com/news/8-llm-evaluation-tools-you-should-know-in-2026/)
- [Best LLM Evaluation Tools for Machine Learning 2026](https://www.prompts.ai/blog/best-llm-evaluation-tools-machine-learning-2026)
- [Top 5 LLM Evaluation Platforms for 2026](https://dev.to/kuldeep_paul/top-5-llm-evaluation-platforms-for-2026-3g3b)
- [Complete Guide to LLM Evaluation Tools in 2026](https://futureagi.substack.com/p/the-complete-guide-to-llm-evaluation)
- [Best LLM Evaluation Tools of 2026 (Medium)](https://medium.com/online-inference/the-best-llm-evaluation-tools-of-2026-40fd9b654dce)
- [RAG Evaluation: 2026 Metrics and Benchmarks](https://labelyourdata.com/articles/llm-fine-tuning/rag-evaluation)
- [LLM Benchmarks in 2026: What They Prove](https://www.lxt.ai/blog/llm-benchmarks/)

### Hallucination Detection & Citation Accuracy
- [FACTUM: Mechanistic Detection of Citation Hallucination in Long-Form RAG](https://arxiv.org/pdf/2601.05866) (January 2026)
- [Hallucination Mitigation for RAG Large Language Models](https://www.mdpi.com/2227-7390/13/5/856)
- [Legal RAG Hallucinations Study (Stanford)](https://dho.stanford.edu/wp-content/uploads/Legal_RAG_Hallucinations.pdf)
- [Detect Hallucinations in RAG LLM Applications (Datadog)](https://www.datadoghq.com/blog/llm-observability-hallucination-detection/)
- [GPTZero Uncovers 50+ Hallucinations in ICLR 2026](https://gptzero.me/news/iclr-2026/)
- [MEGA-RAG: Multi-Evidence Guided Answer Refinement](https://pmc.ncbi.nlm.nih.gov/articles/PMC12540348/)
- [RAG in 2026: Enterprise AI](https://www.techment.com/blogs/blogs-rag-in-2026-enterprise-ai/)

### Human-in-the-Loop & Expert Validation
- [Human-in-the-Loop Review Workflows for LLM Applications](https://www.comet.com/site/blog/human-in-the-loop/)
- [Knowledge Graph Validation with LLMs and Human-in-the-Loop](https://www.sciencedirect.com/science/article/pii/S030645732500086X)
- [Beyond the Prompt: Domain Knowledge Strategies for LLM Optimization](https://arxiv.org/html/2602.02752)

### Intent Classification & Query Understanding
- [Intent Detection for AI Systems: Understanding What Users Really Want](https://medium.com/@tombastaner/intent-detection-for-ai-systems-understanding-what-users-really-want-2399064e3cf4)
- [AI Agents for Compliance: Role, Use Cases, and Applications](https://www.leewayhertz.com/ai-agents-for-compliance/)
- [Understanding AI Intent Classification (FlowHunt)](https://www.flowhunt.io/blog/ai-intent-classification-guide/)
- [Customer Intent: How AI Agents Understand Queries](https://poly.ai/blog/how-do-ai-agents-understand-customer-queries/)

### Project Documentation (Local)
- CCoP 2.0 Official PDF (Second Edition Revision One)
- Phase 2: Ground Truth Establishment Process
- Phase 2: Scoring Methodology (v2.0)
- Mid-Term Report: Fine-Tuning LLM on CCoP 2.0 Standards

---

**Document Version:** 1.0
**Research Date:** 2026-02-04
**Next Review:** Post-Phase 2 baseline evaluation (align thresholds with actual model performance)
