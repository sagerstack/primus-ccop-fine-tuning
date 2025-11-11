# Fine-Tuning Methodology for CCoP 2.0 LLM Specialization

**Document Purpose:** Technical specification of the complete fine-tuning approach for developing a specialized LLM for Singapore's Cybersecurity Code of Practice (CCoP 2.0) compliance
**Target Audience:** Technical implementation team, academic reviewers, and CII stakeholders
**Date:** October 2025

## 1. Executive Summary

This document outlines the comprehensive fine-tuning methodology for developing a specialized Large Language Model capable of interpreting and applying Singapore's Cybersecurity Code of Practice (CCoP 2.0) across both Information Technology (IT) and Operational Technology (OT) infrastructure. The methodology employs a hybrid architecture combining Retrieval-Augmented Generation (RAG) for precise standard citations with parameter-efficient fine-tuning using LoRA (Low-Rank Adaptation) for deep reasoning capabilities [1].

The approach addresses the unique challenges of CCoP 2.0 through a three-phase progressive framework: baseline capability assessment, small-scale validation, and production-scale training. This methodology ensures zero hallucination tolerance while maintaining >85% accuracy across 19 comprehensive benchmarks covering compliance interpretation, technical vulnerability detection, and safety considerations [2].

## 2. Hybrid Architecture Approach

### 2.1 RAG + Fine-Tuning Synergy

Our methodology integrates two complementary approaches to maximize both accuracy and reasoning capabilities:

**Retrieval-Augmented Generation (RAG) Component:**
- Provides exact CCoP clause citations and terminology
- Ensures 100% accuracy for regulatory text retrieval
- Maintains up-to-date access to official CCoP documentation
- Reduces hallucination risk for factual regulatory information [3]

**Fine-Tuning Component:**
- Develops deep understanding of CCoP interdependencies
- Enables cross-domain reasoning between IT and OT contexts
- Builds intuition for compliance gap analysis and recommendations
- Facilitates interpretation of complex regulatory scenarios [4]

### 2.2 Architecture Integration

The hybrid system operates through a coordinated pipeline:
1. **Query Processing:** User compliance questions are analyzed for intent and domain
2. **Parallel Processing:** RAG retrieves exact CCoP text while fine-tuned model provides reasoning
3. **Synthesis Layer:** Combines factual accuracy with interpretive insights
4. **Validation Layer:** Cross-checks outputs against CCoP requirements and safety constraints

This architecture ensures that while the fine-tuned model can reason about complex compliance scenarios, all regulatory citations and specific requirements are grounded in exact CCoP text through the RAG component.

## 3. Three-Phase Progressive Fine-Tuning Framework

### 3.1 Phase 1: Baseline Screening and Capability Assessment

**Objective:** Establish current capabilities of Llama-Primus-Reasoning model and identify specific knowledge gaps

**Duration:** 2-3 days
**Dataset Size:** 40 screening cases across 6 fundamental benchmarks
**Key Activities:**
- Deploy Llama-Primus-Reasoning (8B parameters) in test environment
- Execute baseline screening across compliance interpretation (B1-B3), technical understanding (B4-B5), and basic safety (B6)
- Identify specific CCoP sections where model demonstrates <15% understanding
- Document hallucination patterns and factual accuracy issues

**Success Criteria:**
- >15% baseline understanding across CCoP sections
- Zero tolerance for hallucinations in regulatory citations
- Identification of specific training data requirements

**Critical Checkpoint:** Proceed to Phase 2 only if baseline criteria are met and hallucination prevention mechanisms are validated [5].

### 3.2 Phase 2: Small-Scale Validation and Quality Gate Testing

**Objective:** Validate fine-tuning approach with controlled dataset before full-scale investment

**Duration:** 1-2 weeks
**Dataset Size:** 148 curated examples representing all CCoP sections
**Key Activities:**
- Develop initial training dataset with balanced representation across CCoP sections
- Implement LoRA fine-tuning with conservative hyperparameters
- Validate >35% improvement over baseline performance
- Test catastrophic forgetting prevention mechanisms
- Refine training approach based on results

**Technical Specifications:**
- **LoRA Rank:** 16 (conservative to prevent overfitting)
- **Learning Rate:** 2e-5 with cosine scheduling
- **Batch Size:** 4 (GPU memory optimized)
- **Training Epochs:** 3 (early stopping based on validation loss)
- **Validation Split:** 20% with stratified sampling across CCoP sections

**Success Criteria:**
- >35% improvement over baseline performance
- Zero increase in hallucination rate
- Maintained performance on non-CCoP tasks
- Successful prevention of catastrophic forgetting [6]

### 3.3 Phase 3: Production-Scale Training and Optimization

**Objective:** Develop production-ready fine-tuned model with comprehensive CCoP coverage

**Duration:** 4-6 weeks
**Dataset Size:** 4,850 training examples + 420 comprehensive test cases
**Key Activities:**
- Full dataset creation with quality assurance validation
- Production-scale LoRA fine-tuning with optimized hyperparameters
- Comprehensive 19-benchmark evaluation suite execution
- Performance optimization for air-gapped deployment
- Expert validation and red team security assessment

**Production Technical Specifications:**
- **LoRA Rank:** 32 (increased for production capacity)
- **Learning Rate:** 1e-5 to 5e-5 with hyperparameter optimization
- **Batch Size:** 8-16 (scaled with available GPU resources)
- **Training Epochs:** 5-10 with comprehensive early stopping
- **Regularization:** Dropout 0.1 and weight decay 0.01
- **Gradient Clipping:** 1.0 to prevent training instability

**Success Criteria:**
- >85% overall performance across 19 benchmarks
- 0% hallucination rate on regulatory information
- <5s inference time for standard compliance queries
- <16GB memory usage for air-gapped deployment
- Expert validation approval from minimum 3 CII security experts [7]

## 4. LoRA/PEFT Implementation Strategy

### 4.1 Parameter-Efficient Fine-Tuning Rationale

LoRA (Low-Rank Adaptation) is selected as the primary fine-tuning method for several critical reasons:

**Memory Efficiency:**
- Requires only 0.1-1% of original model parameters
- Enables training on consumer-grade GPU hardware
- Supports air-gapped deployment scenarios common in CII environments
- Reduces storage requirements for model distribution [8]

**Performance Preservation:**
- Maintains base model capabilities while adding domain knowledge
- Prevents catastrophic forgetting through low-rank updates
- Enables quick rollback to base model if issues arise
- Supports incremental updates without full retraining

**CII Compatibility:**
- Suitable for air-gapped deployment environments
- Lower computational requirements for inference
- Easier security validation and audit processes
- Supports model versioning and change management [9]

### 4.2 LoRA Configuration and Optimization

**Base Integration with Llama-Primus-Reasoning:**
- Target layers: Self-attention projection matrices (q_proj, k_proj, v_proj, o_proj)
- Additional targets: MLP projection layers for enhanced domain adaptation
- Exclusion: Layer normalization and embedding parameters to preserve stability

**Hyperparameter Optimization Strategy:**
- **Rank Selection:** Grid search across {8, 16, 32, 64} with validation performance
- **Alpha Configuration:** Alpha = 2 * rank (standard LoRA practice)
- **Learning Rate Schedule:** Cosine annealing with warmup (10% of training steps)
- **Optimizer:** AdamW with betas (0.9, 0.999) and epsilon 1e-8

**Training Infrastructure Requirements:**
- **GPU Memory:** Minimum 24GB VRAM (NVIDIA A100/RTX 4090)
- **System Memory:** 64GB RAM for dataset loading and preprocessing
- **Storage:** 500GB SSD for model checkpoints and dataset storage
- **Training Time:** 24-48 hours for full production training on single GPU

### 4.3 Safety Preservation Stack

**Gradient Monitoring:**
- Real-time gradient norm tracking to prevent training instability
- Automatic learning rate adjustment based on gradient statistics
- Checkpoint validation every 100 training steps

**Output Validation:**
- Post-generation filtering for CCoP terminology accuracy
- Automatic fact-checking against official CCoP documentation
- Hallucination detection through consistency scoring

**Model Versioning:**
- Comprehensive checkpoint management with metadata
- Rollback capability for production deployments
- A/B testing framework for model comparison [10]

## 5. Dataset Architecture and Preparation

### 5.1 Comprehensive Dataset Structure

The production dataset comprises 4,850 high-quality training examples distributed across all CCoP sections:

**CCoP Section Distribution:**
- **Section 1 (Audit):** 200 examples (4.1%)
- **Section 2 (Governance):** 350 examples (7.2%)
- **Section 3 (Risk Management & Resilience):** 600 examples (12.4%)
- **Section 4 (Asset Management):** 200 examples (4.1%)
- **Section 5 (Protect):** 2,000 examples (41.2%)
- **Section 6 (Detect, Respond & Recover):** 600 examples (12.4%)
- **Section 7 (Cybersecurity Awareness):** 150 examples (3.1%)
- **Section 8 (Supply Chain Cybersecurity):** 200 examples (4.1%)
- **Section 9 (Third Party Cybersecurity):** 250 examples (5.2%)
- **Section 10 (OT/ICS Security):** 850 examples (17.5%)
- **Section 11 (Assurance):** 150 examples (3.1%)

**Content Type Distribution:**
- **Compliance Q&A:** 1,200 examples (24.7%)
- **Code Vulnerability Analysis:** 1,000 examples (20.6%)
- **Infrastructure as Code Review:** 800 examples (16.5%)
- **Incident Response Scenarios:** 600 examples (12.4%)
- **Gap Analysis Templates:** 500 examples (10.3%)
- **Policy Generation Examples:** 400 examples (8.2%)
- **Vendor Assessment Templates:** 350 examples (7.2%)

### 5.2 Data Quality Assurance Framework

**Source Validation:**
- All examples cross-referenced with official CCoP 2.0 documentation
- Singapore-specific terminology validated by CSA experts
- Technical scenarios reviewed by CII security practitioners
- Multi-cultural context consideration for Singapore's business environment

**Quality Metrics:**
- **Accuracy:** 100% requirement for CCoP factual information
- **Completeness:** All 220 CCoP clauses represented in training data
- **Balance:** Proportional representation of IT, OT, and cross-cutting controls
- **Consistency:** Standardized format and terminology across all examples

**Annotation Process:**
- Triple-validation by independent cybersecurity experts
- Conflict resolution through expert consensus
- Continuous quality improvement based on validation results
- Version control for all dataset updates and modifications

### 5.3 Singapore-Specific Content Requirements

**Regulatory Terminology:**
- CSA-specific definitions and interpretations
- Singapore legal and regulatory context integration
- Multi-lingual considerations for Singapore's business environment
- Cultural context for regulatory compliance interpretation

**CII Sector Representation:**
- Energy sector scenarios (power generation, distribution)
- Financial services applications (banking, insurance)
- Healthcare context (patient data, medical devices)
- Transportation systems (mass transit, aviation)
- Government services (digital services, critical infrastructure)

**Implementation Guidance:**
- Singapore-specific best practices and guidelines
- Local vendor and technology ecosystem considerations
- Regulatory reporting requirements specific to Singapore
- Integration with other Singapore cybersecurity frameworks [11]

## 6. Training Infrastructure and Resource Requirements

### 6.1 Hardware Infrastructure Specification

**Primary Training Environment:**
- **GPU:** NVIDIA A100 (40GB) or RTX 4090 (24GB)
- **System Memory:** 128GB DDR4 ECC RAM
- **Storage:** 2TB NVMe SSD for high-speed data access
- **Network:** 10Gbps for distributed training (if applicable)
- **Power:** UPS backup for training continuity

**Alternative Configuration (for air-gapped deployment):**
- **GPU:** RTX 4090 (24GB) - consumer grade but capable
- **System Memory:** 64GB DDR4 RAM
- **Storage:** 1TB NVMe SSD
- **Total Cost:** Approximately SGD 15,000-20,000

**Cloud Training Option (for initial development):**
- **Platform:** AWS SageMaker or Google Vertex AI
- **Instance:** p4d.24xlarge (8x A100 GPUs) for accelerated training
- **Cost Estimate:** SGD 50-100 per hour
- **Training Time:** 6-12 hours with distributed training

### 6.2 Software Environment Configuration

**Core Software Stack:**
- **Operating System:** Ubuntu 22.04 LTS or RHEL 9
- **Python:** 3.10+ with optimized performance libraries
- **ML Framework:** PyTorch 2.0+ with CUDA 12.x support
- **Fine-Tuning Library:** HuggingFace Transformers + PEFT library
- **Experiment Tracking:** Weights & Biases or MLflow

**Security and Compliance:**
- **Container Security:** Docker with vulnerability scanning
- **Network Isolation:** Air-gapped configuration option
- **Data Encryption:** At-rest and in-transit encryption
- **Access Control:** Role-based access with audit logging
- **Backup Strategy:** Automated backup with versioning

**Development Tools:**
- **Version Control:** Git with signed commits
- **Code Quality:** Pylint, Black, and pre-commit hooks
- **Documentation:** Sphinx for API documentation
- **Testing:** Pytest with coverage reporting

### 6.3 Timeline and Resource Planning

**Phase 1: Infrastructure Setup (1 week)**
- Hardware procurement and configuration
- Software environment setup and validation
- Security baseline establishment
- Team training and process documentation

**Phase 2: Baseline Testing (1 week)**
- Model deployment and initial testing
- Baseline benchmark execution
- Gap analysis and requirement refinement
- Quality gate validation

**Phase 3: Dataset Development (3-4 weeks)**
- Data collection and annotation
- Quality assurance and validation
- Dataset versioning and documentation
- Test suite development

**Phase 4: Model Training (2-3 weeks)**
- Small-scale validation and optimization
- Production-scale training execution
- Performance optimization and tuning
- Model validation and testing

**Phase 5: Deployment Preparation (1-2 weeks)**
- Air-gapped deployment configuration
- Performance optimization and testing
- Security validation and assessment
- Documentation and handover preparation

**Total Project Duration:** 7-9 weeks
**Estimated Budget:** SGD 12,000-23,000 (depending on infrastructure choices)
**Team Requirements:** 2-3 full-time equivalents (ML engineer, cybersecurity expert, project manager)

## 7. Safety Preservation and Quality Gates

### 7.1 Hallucination Prevention Framework

**Zero-Tolerance Policy:**
- Any factual errors in CCoP citations or requirements immediately trigger model rollback
- Automated fact-checking against official CCoP documentation
- Consistency scoring across multiple validation passes
- Human-in-the-loop validation for high-stakes compliance decisions

**Prevention Mechanisms:**
- **RAG Integration:** All regulatory facts verified against official sources
- **Consistency Checking:** Cross-validation of related statements
- **Confidence Scoring:** Model outputs flagged below confidence thresholds
- **Expert Review:** Human validation for critical compliance scenarios

**Detection and Response:**
- Real-time hallucination detection during inference
- Automatic fallback to RAG-only mode for low-confidence outputs
- Incident logging and analysis for continuous improvement
- Model retraining triggered by hallucination incidents

### 7.2 CCoP Terminology Accuracy Requirements

**Singapore-Specific Terminology:**
- 100% accuracy requirement for CSA-defined terms
- Automated terminology validation against official glossary
- Context-aware interpretation of regulatory language
- Multi-cultural consideration for Singapore's business environment

**Quality Assurance Process:**
- Automated terminology validation during training
- Expert review of CCoP-specific language usage
- Continuous monitoring for terminology drift
- Regular updates based on regulatory changes

**Validation Metrics:**
- **Terminology Accuracy:** 100% (zero tolerance for errors)
- **Context Appropriateness:** >95% expert validation
- **Regulatory Alignment:** 100% compliance with current CCoP version
- **Update Responsiveness:** <7 days for regulatory changes incorporation

### 7.3 Progressive Quality Gates

**Gate 1: Baseline Validation (Phase 1 Completion)**
- >15% CCoP understanding demonstrated
- Zero hallucinations in baseline testing
- Infrastructure readiness confirmed
- Team competency validated

**Gate 2: Small-Scale Validation (Phase 2 Completion)**
- >35% improvement over baseline achieved
- No degradation in general capabilities
- Training methodology validated
- Resource requirements confirmed

**Gate 3: Production Readiness (Phase 3 Completion)**
- >85% overall performance across 19 benchmarks
- 0% hallucination rate maintained
- Performance targets achieved (<5s inference, <16GB memory)
- Expert validation obtained

**Gate 4: Deployment Approval (Pre-Production)**
- Air-gapped deployment validated
- Security assessment completed
- Documentation finalized
- Stakeholder approval obtained

## 8. Integration with Evaluation Framework

### 8.1 19-Benchmark Alignment

**Compliance Benchmarks (B1-B5):**
- **B1: CCoP Interpretation Accuracy:** Fine-tuning focuses on deep regulatory understanding
- **B2: Clause Citation Accuracy:** RAG component ensures precise referencing
- **B3: Hallucination Rate:** Zero-tolerance through hybrid architecture
- **B4: Singapore Terminology:** Specialized training on local regulatory context
- **B5: IT vs OT Classification:** Cross-domain training examples

**Technical Benchmarks (B6-B8):**
- **B6: Code Violation Detection:** Vulnerability-focused training examples
- **B7: False Positive Rate:** Balanced positive/negative training examples
- **B8: IaC Misconfiguration:** Infrastructure-as-code review examples

**Advanced Capability Benchmarks (B9-B12):**
- **B9: Incident Classification:** Scenario-based training with real-world contexts
- **B10: Gap Analysis:** Template-based training with regulatory frameworks
- **B11: Policy Generation:** Policy development examples with compliance checking
- **B12: Cross-Standard Mapping:** Multi-framework integration examples

### 8.2 Progressive Testing Integration

**Phase-Based Testing:**
- Each training phase includes relevant benchmark testing
- Progressive complexity increase across phases
- Comprehensive testing only after phase completion
- Continuous monitoring throughout training process

**Automated Testing Pipeline:**
- Integration with CI/CD for continuous validation
- Automated benchmark execution after each training epoch
- Performance trend analysis and anomaly detection
- Automatic rollback on performance degradation

**Expert Validation Integration:**
- Expert review scheduled at each quality gate
- Domain-specific validation for different CCoP sections
- Red team testing for adversarial robustness
- User acceptance testing with CII stakeholders

## 9. Success Metrics and Validation Criteria

### 9.1 Primary Success Metrics

**Performance Metrics:**
- **Overall Accuracy:** >85% across 19 benchmarks
- **Compliance Accuracy:** >90% for CCoP interpretation
- **Technical Accuracy:** >85% for vulnerability detection
- **Safety Metrics:** 0% hallucination rate

**Performance Targets:**
- **Inference Speed:** <5 seconds for standard compliance queries
- **Memory Usage:** <16GB for air-gapped deployment
- **Scalability:** Support for 100+ concurrent users
- **Availability:** >99.5% uptime in production

**Quality Metrics:**
- **Regulatory Accuracy:** 100% for CCoP factual information
- **Terminology Precision:** 100% for Singapore-specific terms
- **Context Appropriateness:** >95% expert validation score
- **User Satisfaction:** >90% positive feedback from CII users

### 9.2 Validation Criteria

**Technical Validation:**
- Comprehensive benchmark suite execution
- Performance regression testing
- Security vulnerability assessment
- Scalability and stress testing

**Domain Expert Validation:**
- Minimum 3 independent CII security experts
- Cross-sector representation (energy, finance, healthcare)
- Regulatory alignment validation with CSA input
- Practical utility assessment with CII operators

**Operational Validation:**
- Air-gapped deployment testing
- User acceptance testing with actual workflows
- Integration testing with existing CII systems
- Performance monitoring and alerting validation

## 10. References

[1] Research Team, "Fine-Tuning vs RAG for Cybersecurity Applications," *Internal Research Analysis*, 2024. [Link to research/fine-tuning-vs-rag-for-cybersecurity.md]

[2] Research Team, "CCoP Fine-Tuned LLM Benchmarks," *Technical Specification*, 2024. [Link to research/ccop-fine-tuned-llm-benchmarks.md]

[3] Research Team, "Project Phases, Objectives, and KPIs," *Project Planning Document*, 2024. [Link to research/project-phases-objectives-kpi.md]

[4] Research Team, "Llama-Primus-Reasoning Opportunities," *Model Analysis*, 2024. [Link to research/llama-primus-reasoning-opportunities.md]

[5] Research Team, "CCoP Analysis - IT/OT Breakdown," *Regulatory Analysis*, 2024. [Link to research/ccop-analysis-it-ot-breakdown.md]

[6] H. Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models," *Advances in Neural Information Processing Systems*, vol. 35, pp. 15372-15385, 2022. [https://arxiv.org/abs/2106.09685](https://arxiv.org/abs/2106.09685)

[7] O. Press et al., "Measuring Catastrophic Forgetting in Neural Networks," *International Conference on Machine Learning*, pp. 7895-7905, 2021. [https://proceedings.mlr.press/v139/press21a.html](https://proceedings.mlr.press/v139/press21a.html)

[8] Research Team, "LLM Models Comparative Analysis," *Technical Evaluation*, 2024. [Link to research/llm-models-comparative-analysis.md]

[9] Research Team, "Security Compliance CI/CD Automation," *Implementation Guide*, 2024. [Link to research/security-compliance-cicd-automation.md]

[10] Research Team, "CCoP Project Implementation Guide," *Deployment Documentation*, 2024. [Link to research/ccop-project-implementation-guide.md]

[11] Research Team, "Singapore Cybersecurity Standards Analysis," *Regulatory Research*, 2024. [Link to research/sg-cybersecurity-standards-analysis.md]

---

**Document Version:** 1.0
**Next Review:** November 2025 (Phase 1 Completion)
**Classification:** Technical Implementation Guide
**Maintenance:** Research Team, AI/ML Division