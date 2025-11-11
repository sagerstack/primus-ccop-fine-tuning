# CCoP 2.0 Fine-Tuned LLM Project Implementation Guide

## Executive Summary

**Project Goal:** Fine-tune Llama-Primus-Reasoning on Singapore's CCoP 2.0 standard to create production-ready compliance validation tool for Critical Information Infrastructure (CII) organizations.

**Total Timeline:** 7-9 weeks from foundation to production deployment

**Key Success Metrics:**
- >90% accuracy on CCoP compliance detection
- 0% hallucination rate on regulatory requirements
- <5 second inference time for code scanning
- Production-ready for air-gapped CII deployment

---

## Phase 0: Foundation & Setup

### **Duration:** 3-5 days

### **Objective:**
Establish technical infrastructure and prepare evaluation framework before any model training or testing begins.

### **Key Activities:**

| Activity | Description | Deliverable |
|----------|-------------|-------------|
| **Infrastructure Setup** | Provision GPU environment (A100/H100 or equivalent) | Working compute environment |
| **Model Deployment** | Install Llama-Primus-Reasoning base model (8B parameters) | Deployed base model |
| **Framework Installation** | Set up LoRA fine-tuning framework (PEFT, Hugging Face) | Training pipeline ready |
| **Evaluation Pipeline** | Create automated benchmark testing scripts | Evaluation codebase |
| **CCoP Documentation** | Organize CCoP 2.0 into structured format (220 clauses, 11 sections) | CCoP knowledge base |
| **Safety Stack** | Install Prompt Guard 2, Llama Guard 4 for adversarial testing | Safety testing tools |

### **Training Dataset Requirements:**
**None** - Infrastructure setup only

### **Benchmarks in Scope:**
**None** - No model evaluation in this phase

### **Target Metrics:**
- Infrastructure operational: 100%
- All dependencies installed: 100%
- Evaluation scripts functional: 100%

### **Go/No-Go Decision:**
✅ **PROCEED if:** All infrastructure and tools functional  
❌ **STOP if:** GPU infrastructure unavailable or budget constraints

---

## Phase 1: Quick Baseline Screening

### **Duration:** 2-3 days

### **Objective:**
Determine if unmodified Llama-Primus-Reasoning shows baseline understanding (15-20%) of CCoP 2.0 requirements before investing in comprehensive testing.

### **Key Activities:**

| Activity | Description | Deliverable |
|----------|-------------|-------------|
| **Minimal Test Creation** | Create 40 quick screening tests across 6 core benchmarks | Phase 1 test set |
| **Baseline Testing** | Run unmodified Primus on test set, no fine-tuning | Baseline scorecard |
| **Gap Analysis** | Identify what Primus knows vs doesn't know about CCoP | Knowledge gap report |
| **Decision Making** | Determine if baseline justifies proceeding to Phase 2 | Go/No-Go recommendation |

### **Training Dataset Requirements:**

**TEST SET ONLY (40 test cases) - NO TRAINING DATA YET**

| Dataset Type | Count | Example |
|--------------|-------|---------|
| Factual CCoP Q&A | 5 | "What does Section 5.12 require?" |
| Ambiguous CCoP Q&A | 5 | "What are 'reasonable security measures'?" |
| Violation → Citation | 5 | "SQL injection" → Which CCoP section? |
| Fake Clause Tests | 5 | "Explain Section 5.25" (doesn't exist) |
| Singapore Terminology | 5 | Use of "Commissioner," "CII," etc. |
| IT vs OT Scenarios | 5 | "Is SCADA system IT or OT?" |
| Vulnerable Code Samples | 10 | OWASP Top 10 vulnerabilities |
| **TOTAL** | **40** | **Screening set** |

### **Benchmarks in Scope:**

| Benchmark ID | Benchmark Name | Target (Baseline) | Dataset Size |
|--------------|----------------|-------------------|--------------|
| **B1** | CCoP Interpretation Accuracy | >15% overall | 10 questions |
| **B2** | Clause Citation Accuracy | >5% (low bar) | 5 scenarios |
| **B3** | Hallucination Rate | No fabrications | 5 tests |
| **B4** | Singapore Terminology Accuracy | >10% | 5 checks |
| **B5** | IT vs OT Classification | >40% | 5 scenarios |
| **B6** | Code Violation Detection Rate | >60% | 10 samples |

**NOT tested:** B7-B19 (deferred to Phase 2)

### **Target Metrics:**

| Metric | Minimum Threshold | Ideal Target |
|--------|------------------|--------------|
| **Overall Baseline Score** | >15% | >20% |
| **Hallucination Rate (B3)** | 0% | 0% |
| **Code Detection (B6)** | >50% | >60% |
| **Average Confidence** | Not critical | - |

### **Go/No-Go Decision:**

| Overall Score | Decision | Reasoning |
|---------------|----------|-----------|
| **>20%** | ✅ **PROCEED to Phase 2** | Strong baseline, fine-tuning should work |
| **15-20%** | ✅ **PROCEED with caution** | Acceptable baseline |
| **10-15%** | ⚠️ **RECONSIDER** | Weak baseline, may need different model |
| **<10%** | ❌ **STOP - Pivot** | Fundamentally can't understand domain |
| **Hallucinations present** | ❌ **STOP** | Safety risk regardless of score |

**Investment to Decision Point:** 2-3 days, 40 test cases

---

## Phase 2: Comprehensive Baseline + Small Fine-Tune Test

### **Duration:** 1-2 weeks

### **Objective:**
Conduct detailed baseline measurement across all benchmarks, then validate that small-scale fine-tuning can improve performance by >35% before committing to full dataset creation.

### **Phase 2A: Comprehensive Baseline (3-4 days)**

#### **Key Activities:**

| Activity | Description | Deliverable |
|----------|-------------|-------------|
| **Expanded Test Creation** | Create 170 comprehensive test cases across 12 benchmarks | Phase 2 test set |
| **Detailed Baseline Testing** | Test unmodified Primus on all compliance, code, and advanced benchmarks | Detailed baseline report |
| **Benchmark Analysis** | Identify which benchmarks Primus performs well/poorly on | Strengths/weaknesses analysis |
| **Training Data Planning** | Design 148 training examples based on baseline gaps | Training dataset specification |

#### **Test Dataset Requirements (170 test cases):**

| Dataset Category | Count | Purpose |
|------------------|-------|---------|
| CCoP Q&A (Interpretation) | 20 | Understanding of CCoP requirements |
| Violation → Citation | 20 | Clause citation accuracy |
| Hallucination Tests | 15 | Safety validation |
| Singapore Terminology | 10 | Regional knowledge |
| IT vs OT Classification | 15 | Infrastructure distinction |
| Vulnerable Code Samples | 25 | SAST detection capability |
| Clean Code Samples | 20 | False positive measurement |
| IaC Configurations | 15 | Infrastructure compliance |
| Incident Scenarios | 10 | CSA reporting classification |
| Organization Profiles | 5 | Gap analysis capability |
| Policy Generation Prompts | 5 | Documentation quality |
| Cross-Standard Mappings | 15 | Multi-framework knowledge |
| **TOTAL** | **170** | **Comprehensive baseline** |

#### **Benchmarks in Scope (Phase 2A):**

| Category | Benchmarks | Dataset Size | Expected Baseline |
|----------|-----------|--------------|-------------------|
| **Compliance** | B1-B5 | 55 tests | 20-30% |
| **Code/Infrastructure** | B6-B8 | 80 tests | 60-70% (B6), unknown (B7-B8) |
| **Advanced Capabilities** | B9-B12 | 35 tests | 10-20% |

**NOT tested yet:** B13-B19 (safety, training quality, performance)

---

### **Phase 2B: Small Fine-Tune Test (3-4 days)**

#### **Key Activities:**

| Activity | Description | Deliverable |
|----------|-------------|-------------|
| **Training Data Creation** | Create 148 high-quality training examples | Phase 2 training set |
| **Quick Fine-Tuning** | LoRA fine-tune with small dataset (1-2 days training) | Fine-tuned model v0.1 |
| **Re-Testing** | Test on same 170 test cases to measure improvement | Improvement delta report |
| **Safety Validation** | Test adversarial robustness (B13-B14) | Safety scorecard |
| **Training Monitoring** | Track training loss, validation loss, perplexity | Training metrics report |
| **Decision Making** | Determine if full Phase 3 training justified | Go/No-Go recommendation |

#### **Training Dataset Requirements (148 examples):**

| Dataset Category | Training Examples | Purpose |
|------------------|------------------|---------|
| CCoP Q&A | 25 | Interpretation and citation |
| Hallucination Prevention | 10 | Safety training |
| Singapore Terminology | 15 | Regional language patterns |
| IT vs OT Examples | 15 | Infrastructure classification |
| Vulnerable Code | 30 | SAST detection training |
| IaC Configs | 15 | Infrastructure scanning |
| Incident Scenarios | 10 | Classification training |
| Gap Analysis | 3 | Compliance assessment |
| Policy Generation | 5 | Documentation creation |
| Cross-Standard Mappings | 20 | Multi-framework knowledge |
| **TOTAL** | **148** | **Small fine-tune set** |

**CRITICAL:** Training set is completely separate from 170 test cases (no data leakage)

#### **Benchmarks in Scope (Phase 2B):**

**ALL benchmarks B1-B17 tested**

| Category | Benchmarks | Why Added in Phase 2B |
|----------|-----------|----------------------|
| **Compliance** | B1-B5 | Re-test to measure improvement |
| **Code/Infrastructure** | B6-B8 | Re-test to measure improvement |
| **Advanced** | B9-B12 | Re-test to measure improvement |
| **Safety** 🆕 | B13-B14 | Verify fine-tuning didn't break safety |
| **Training Quality** 🆕 | B15-B17 | Monitor during fine-tuning |

**NOT tested yet:** B18-B19 (performance - not critical for small test)

#### **Additional Test Data for Phase 2B (20 tests):**

| Dataset Type | Count | Purpose |
|--------------|-------|---------|
| Prompt Injection Attacks | 10 | B13 - Can model be tricked? |
| Jailbreak Attempts | 10 | B14 - Can model bypass safety? |
| **TOTAL NEW** | **20** | **Safety validation** |

**Phase 2B Total:** 170 original tests + 20 safety tests = 190 test cases

### **Target Metrics (Phase 2B - Post Fine-Tune):**

| Benchmark | Baseline (Phase 2A) | Post-Fine-Tune Target | Improvement Required |
|-----------|--------------------|-----------------------|---------------------|
| **B1** - CCoP Interpretation | 20-30% | 60-70% | +40% |
| **B2** - Clause Citation | 5-10% | 50-60% | +45% |
| **B3** - Hallucination | Low | 0% | Must improve |
| **B4** - Singapore Terms | 10-20% | 80-90% | +70% |
| **B5** - IT vs OT | 40-50% | 85-90% | +40% |
| **B6** - Code Detection | 60-70% | 75-85% | +15% |
| **B7** - False Positives | Unknown | <15% | Establish baseline |
| **B8** - IaC Detection | Unknown | 70-80% | Establish baseline |
| **B9-B12** - Advanced | 10-20% | 50-60% | +40% |
| **B13-B14** - Safety | N/A | >90% | Critical |
| **B15-B17** - Training | N/A | Healthy convergence | Monitor |

### **Go/No-Go Decision (Phase 2B):**

| Outcome | Decision | Next Action |
|---------|----------|-------------|
| **Average improvement >35%** | ✅ **PROCEED to Phase 3** | Full dataset creation justified |
| **Average improvement 20-35%** | ⚠️ **ADJUST & RETRY** | Improve training example quality |
| **Average improvement <20%** | ❌ **PIVOT MODEL** | Primus can't learn CCoP effectively |
| **B13-B14 (Safety) <90%** | ❌ **STOP** | Safety vulnerabilities introduced |
| **B16 (Val Loss) increasing** | ❌ **ADJUST** | Overfitting detected |
| **Hallucinations (B3) increased** | ❌ **STOP** | Safety degradation |

**Investment to Decision Point:** 1-2 weeks, 318 total examples (170 test + 148 training)

---

## Phase 3: Production Training & Comprehensive Validation

### **Duration:** 5-6 weeks

### **Objective:**
Create production-ready CCoP 2.0 fine-tuned model with comprehensive training data, achieving >90% accuracy on all compliance benchmarks and <10% false positives for deployment to CII organizations.

### **Phase 3A: Full Dataset Creation (3-4 weeks)**

#### **Key Activities:**

| Activity | Description | Deliverable |
|----------|-------------|-------------|
| **Comprehensive Data Collection** | Curate 4,850 high-quality training examples across all CCoP sections | Phase 3 training set |
| **Expert Validation** | Security experts review training data for accuracy | Validated dataset |
| **Data Augmentation** | Generate variations of examples for robustness | Expanded dataset |
| **Quality Assurance** | Remove duplicates, fix errors, balance distribution | Clean dataset |
| **Test Set Expansion** | Expand to 420 comprehensive test cases | Phase 3 test set |

#### **Training Dataset Requirements (4,850 examples):**

**Dataset Distribution by CCoP Section:**

| Section | Clauses | Training Examples | % of Total | Rationale |
|---------|---------|------------------|------------|-----------|
| **Section 1** - Audit | 4 | 50 | 1% | Small section, organizational focus |
| **Section 2** - Governance | 15-20 | 200 | 4% | Policy generation heavy |
| **Section 3** - Risk & Resilience | 25-30 | 400 | 8% | Cloud security, change mgmt |
| **Section 4** - Asset Management | 8-10 | 150 | 3% | Inventory, SBOM generation |
| **Section 5** - Protect | 80-90 | 2,000 | 41% | **Largest - code scanning focus** |
| **Section 6** - Detect/Respond/Recover | 25-30 | 600 | 12% | Incident response, CSA reporting |
| **Section 7** - Awareness | 8-10 | 150 | 3% | Training content generation |
| **Section 8** - Supply Chain | 10-12 | 200 | 4% | SBOM, code signing |
| **Section 9** - Third Party | 12-15 | 200 | 4% | Vendor assessment |
| **Section 10** - OT/ICS | 35-40 | 850 | 18% | **Critical differentiator** |
| **Section 11** - Assurance | 8-10 | 150 | 3% | Testing, validation |
| **TOTAL** | **~220** | **4,850** | **100%** | **Comprehensive coverage** |

**Dataset Distribution by Type:**

| Dataset Category | Training Examples | Purpose |
|------------------|------------------|---------|
| **CCoP Q&A** | 500 | Interpretation, citation, factual knowledge |
| **Hallucination Prevention** | 100 | Fake clauses, incorrect citations |
| **Singapore Terminology** | 200 | Commissioner, CII, prescribed timeframes |
| **IT vs OT Classification** | 300 | Infrastructure type distinction |
| **Vulnerable Code Samples** | 1,500 | SAST detection (Python, Java, JS, etc.) |
| **IaC Configurations** | 800 | Terraform, K8s, CloudFormation scanning |
| **Incident Scenarios** | 300 | CSA notification determination |
| **Gap Analysis Cases** | 150 | Organization compliance assessment |
| **Policy Generation** | 200 | Access control, incident response, etc. |
| **Cross-Standard Mappings** | 500 | ISO 27001, NIST 800-53 → CCoP |
| **Architecture Reviews** | 100 | Network diagrams, OT architecture |
| **Sector-Specific Scenarios** | 200 | Energy, Water, Transport, Banking |
| **TOTAL** | **4,850** | **Production dataset** |

#### **Test Dataset Requirements (420 test cases):**

**Expanded from Phase 2's 170 tests**

| Dataset Category | Test Cases | Notes |
|------------------|-----------|-------|
| CCoP Q&A | 50 | Factual + ambiguous questions |
| Hallucination Tests | 30 | Comprehensive safety validation |
| Singapore Terminology | 25 | All key regional terms |
| IT vs OT Classification | 30 | All CII sectors covered |
| Vulnerable Code | 60 | Multiple languages, frameworks |
| Clean Code (False Positives) | 40 | Should NOT trigger violations |
| IaC Configurations | 40 | All major cloud providers |
| Incident Scenarios | 25 | Edge cases, multi-system incidents |
| Gap Analysis | 15 | Various organization maturity levels |
| Policy Generation | 15 | All major CCoP sections |
| Cross-Standard Mappings | 40 | Comprehensive framework coverage |
| Architecture Reviews | 20 | IT, OT, hybrid designs |
| Sector-Specific | 30 | Industry-appropriate guidance |
| **TOTAL** | **420** | **Production test set** |

---

### **Phase 3B: Comprehensive Fine-Tuning (1 week)**

#### **Key Activities:**

| Activity | Description | Deliverable |
|----------|-------------|-------------|
| **Full Fine-Tuning** | LoRA fine-tune with complete 4,850-example dataset | Fine-tuned model v1.0 |
| **Training Monitoring** | Real-time tracking of loss, perplexity, safety metrics | Training dashboard |
| **Hyperparameter Tuning** | Optimize learning rate, batch size, LoRA rank | Optimal configuration |
| **Safety Preservation** | Continuous monitoring with Llama Guard 4 | Safety validation log |
| **Checkpoint Management** | Save intermediate checkpoints for rollback if needed | Model checkpoints |

#### **Training Configuration:**

```
LoRA Configuration:
- Rank (r): 16-32
- Alpha: 32-64
- Target modules: q_proj, v_proj, k_proj, o_proj, gate_proj, up_proj, down_proj
- Dropout: 0.1

Training Parameters:
- Learning rate: 2e-5 with warmup
- Batch size: 4 per GPU with gradient accumulation
- Epochs: 3-5 (monitor validation loss)
- Mixed precision: FP16/BF16
- Gradient checkpointing: Enabled

Safety Stack:
- Prompt Guard 2 (pre-screening)
- Llama Guard 4 (content moderation)
- Continuous perplexity monitoring
```

---

### **Phase 3C: Production Validation (1 week)**

#### **Key Activities:**

| Activity | Description | Deliverable |
|----------|-------------|-------------|
| **Comprehensive Testing** | Test on all 420 test cases across 19 benchmarks | Complete scorecard |
| **Expert Review Panel** | Panel reviews subjective benchmarks (B10, B11) | Expert validation report |
| **Red Team Testing** | Adversarial attacks on safety (B13-B14) | Security assessment |
| **Performance Profiling** | Measure inference speed and memory usage (B18-B19) | Performance report |
| **Deployment Preparation** | Package model for air-gapped deployment | Deployment package |
| **Documentation** | User guide, API docs, compliance reports | Complete documentation |

#### **Expert Review Panel Composition:**

| Role | Count | Purpose |
|------|-------|---------|
| CSA-certified CCoP auditors | 2-3 | Validate compliance interpretation |
| CII organization CISOs | 2 | Validate practical applicability |
| OT/ICS security specialists | 1 | Validate Section 10 accuracy |
| **TOTAL** | **5-6 experts** | **Production validation** |

### **Benchmarks in Scope (Phase 3):**

**ALL 19 BENCHMARKS (B1-B19)**

| Category | Benchmarks | Dataset Size | Target Metrics |
|----------|-----------|--------------|----------------|
| **Compliance** | B1-B5 | 140 tests | B1: >85% (ambiguous), >95% (factual)<br>B2: >90%<br>B3: 0%<br>B4: 100%<br>B5: >95% |
| **Code/Infrastructure** | B6-B8 | 140 tests | B6: >90% for high/critical<br>B7: <10%<br>B8: >85% |
| **Advanced Capabilities** | B9-B12 | 90 tests | B9: >95%<br>B10: Precision >85%, Recall >80%<br>B11: >90%<br>B12: >85% |
| **Safety & Security** | B13-B14 | 50 tests | B13: >95%<br>B14: >90% |
| **Training Quality** | B15-B17 | Monitored | B15: <0.5<br>B16: Stable/decreasing<br>B17: <20 |
| **Performance** | B18-B19 | Profiling | B18: <5s per scan<br>B19: <16GB VRAM |

### **Target Metrics (Phase 3 - Production):**

#### **Must-Pass Criteria:**

| Benchmark | Minimum Requirement | Notes |
|-----------|---------------------|-------|
| **B3** - Hallucination | 0% fabricated clauses | **Non-negotiable** |
| **B4** - Singapore Terms | 100% correct usage | **Non-negotiable** |
| **B13-B14** - Safety | >95% attack resistance | **Critical for production** |
| **B1** - Interpretation | Ambiguous: >85%, Factual: >95% | Core capability |
| **B2** - Citation | >90% exact match | Audit requirement |
| **B5** - IT vs OT | >95% correct | Safety-critical distinction |
| **B6** - Code Detection | >90% for high/critical | Core value proposition |
| **B7** - False Positives | <10% | Developer trust |

#### **Should-Pass Criteria:**

| Benchmark | Target | Acceptable Range |
|-----------|--------|------------------|
| **B8** - IaC Detection | >85% | 80-85% acceptable |
| **B9** - Incident Classification | >95% | 90-95% acceptable |
| **B10** - Gap Analysis | Precision >85%, Recall >80% | 80-85% acceptable |
| **B11** - Policy Generation | >90% audit-ready | 85-90% acceptable |
| **B12** - Cross-Standard Mapping | >85% | 80-85% acceptable |

#### **Performance Requirements:**

| Benchmark | Target | Maximum Acceptable |
|-----------|--------|--------------------|
| **B18** - Inference Speed | <5s per code scan | <8s acceptable |
| **B19** - Memory Usage | <16GB VRAM | <24GB acceptable (2x T4 GPUs) |

### **Success Criteria (Phase 3):**

**Production Readiness Requirements:**

1. **ALL Must-Pass criteria met** (B3, B4, B13-B14, B1, B2, B5, B6, B7)
2. **80% of Should-Pass criteria in target range**
3. **Performance acceptable for CI/CD integration** (B18, B19)
4. **Expert panel approval** (>4/5 rating on subjective benchmarks)
5. **Zero critical safety issues** in red team testing

**If ANY Must-Pass fails:**
- Additional training iteration required
- Root cause analysis
- Dataset quality improvement
- Hyperparameter adjustment

**Investment:** 5-6 weeks, ~5,270 total examples (4,850 training + 420 test)

---

## Training Data Sources & Collection Strategy

### **Primary Data Sources:**

| Source Type | Examples | Coverage |
|-------------|----------|----------|
| **Official CCoP Documentation** | CSA CCoP 2.0 document, guidance notes, advisories | B1, B2, B4 |
| **Singapore Regulatory** | CSA enforcement actions, MAS TRM, PDPC guidelines | B4, B9 |
| **Vulnerability Databases** | OWASP WebGoat, CVE examples, CWE patterns | B6, B8 |
| **Open Source Projects** | GitHub vulnerable code, OpenPLC, SCADA configs | B6, B8 |
| **Industry Standards** | ISO 27001, NIST 800-53, IEC 62443 | B12 |
| **CII Organizations** | Anonymized case studies (with permission) | B10, B5 |
| **Security Consultancies** | Expert-validated scenarios | All benchmarks |

### **Data Quality Assurance:**

| Quality Check | Method | Target |
|---------------|--------|--------|
| **Accuracy** | Expert review of all examples | 100% validated |
| **Diversity** | Coverage across all 11 CCoP sections | Balanced distribution |
| **Difficulty** | Mix of easy, medium, hard scenarios | 30% easy, 50% medium, 20% hard |
| **Language Balance** | Multiple programming languages for code samples | Python, Java, JS, Go, C++ |
| **Sector Coverage** | Examples from Energy, Water, Transport, Banking | 25% each |
| **IT/OT Balance** | Appropriate mix of infrastructure types | 45% IT, 18% OT, 37% cross-cutting |

---

## Risk Management & Mitigation

### **Technical Risks:**

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Catastrophic Forgetting** | Medium | High | Train all sections together, not sequentially |
| **Safety Degradation** | Medium | Critical | Continuous monitoring with B13-B14, safety stack |
| **Hallucination Increase** | Low | Critical | Rigorous B3 testing at every phase |
| **Overfitting** | Medium | Medium | Monitor B16 validation loss, early stopping |
| **Performance Issues (B18-B19)** | Low | Medium | Quantization, model pruning if needed |

### **Data Risks:**

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Insufficient OT Examples** | High | Medium | Partner with OT security firms, use IEC 62443 |
| **Data Quality Issues** | Medium | High | Expert review, validation pipeline |
| **Singapore Context Missing** | Medium | High | CSA consultant on advisory board |
| **Biased Training Data** | Low | Medium | Diversity checks, sector balance |

### **Project Risks:**

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Phase 1 Fails (<15%)** | Low | High | Have backup models ready (Qwen, DeepSeek) |
| **Phase 2 Low Improvement** | Medium | High | Iterate on training data quality |
| **Expert Unavailability** | Medium | Medium | Engage experts early, contract agreements |
| **Timeline Slippage** | Medium | Low | Built-in buffer (7-9 weeks vs 6-7 minimum) |

---

## Resource Requirements

### **Human Resources:**

| Role | Commitment | Phase Focus |
|------|-----------|-------------|
| **ML Engineer** | Full-time | All phases - training, evaluation |
| **Security Domain Expert** | Part-time (30%) | Dataset creation, validation |
| **CCoP Compliance Specialist** | Part-time (20%) | CCoP interpretation, clause mapping |
| **OT/ICS Security Expert** | Part-time (15%) | Section 10 validation |
| **DevOps Engineer** | Part-time (20%) | Infrastructure, CI/CD integration |

### **Compute Resources:**

| Resource | Specification | Usage |
|----------|--------------|-------|
| **Training GPU** | 1x A100 (80GB) or 2x H100 | Phase 2B, Phase 3B fine-tuning |
| **Inference GPU** | 1-2x T4 (16GB each) | Testing, validation |
| **Storage** | 500GB SSD | Datasets, models, checkpoints |
| **Memory** | 128GB RAM | Data preprocessing |

### **Budget Estimate:**

| Item | Cost (USD) | Notes |
|------|-----------|-------|
| **Cloud GPU Compute** | $3,000-5,000 | A100 for ~100 hours |
| **Expert Consultation** | $5,000-10,000 | 5-6 experts, ~40 hours each |
| **Data Collection/Labeling** | $2,000-3,000 | If outsourcing any labeling |
| **Software/Tools** | $0-1,000 | Open source primary, some subscriptions |
| **Contingency (20%)** | $2,000-4,000 | Buffer for unknowns |
| **TOTAL** | **$12,000-23,000** | **End-to-end project cost** |

---

## Deliverables Summary

### **Phase 0:**
- ✅ Operational GPU infrastructure
- ✅ Llama-Primus-Reasoning deployed
- ✅ Evaluation pipeline functional

### **Phase 1:**
- ✅ 40-test screening set
- ✅ Baseline scorecard (B1-B6)
- ✅ Go/No-Go recommendation

### **Phase 2:**
- ✅ 170-test comprehensive set
- ✅ 148-example training set
- ✅ Detailed baseline report (B1-B12)
- ✅ Fine-tuned model v0.1
- ✅ Improvement delta analysis
- ✅ Safety validation (B13-B14)
- ✅ Go/No-Go for Phase 3

### **Phase 3:**
- ✅ 4,850-example production training set
- ✅ 420-test production validation set
- ✅ Fine-tuned model v1.0 (production-ready)
- ✅ Complete benchmark scorecard (B1-B19)
- ✅ Expert validation report
- ✅ Performance optimization report
- ✅ Deployment package (air-gapped ready)
- ✅ User documentation and API reference
- ✅ Compliance reports for CII organizations

---

## Success Metrics Dashboard

### **Phase 1 Success:**
```
Baseline Score: 22% ✅ (>20% target)
Hallucinations: 0% ✅ (0% required)
Code Detection: 67% ✅ (>60% target)
→ PROCEED to Phase 2
```

### **Phase 2 Success:**
```
Average Improvement: +42% ✅ (>35% target)
Safety (B13-B14): 93% ✅ (>90% target)
Validation Loss: Stable ✅
Hallucinations: 0% ✅
→ PROCEED to Phase 3
```

### **Phase 3 Success (Production):**
```
Compliance (B1-B5): 94% average ✅
Code Scanning (B6-B8): 91% detection, 8% FP ✅
Advanced (B9-B12): 87% average ✅
Safety (B13-B14): 96% average ✅
Performance: 3.2s/scan, 14GB VRAM ✅
Expert Rating: 4.3/5.0 ✅
→ PRODUCTION READY
```

---

## Appendix: Benchmark Quick Reference

### **B1-B5: Compliance Benchmarks**
Core CCoP understanding and regulatory accuracy

### **B6-B8: Code & Infrastructure Benchmarks**
Technical vulnerability detection (SAST, SCA, IaC)

### **B9-B12: Advanced Capability Benchmarks**
Broader use cases (gap analysis, policy generation, incident response)

### **B13-B14: Safety & Security Benchmarks**
Adversarial robustness (prompt injection, jailbreak resistance)

### **B15-B17: Training Quality Benchmarks**
Model learning effectiveness (loss, perplexity, convergence)

### **B18-B19: Performance Benchmarks**
Operational efficiency (inference speed, memory usage)

---

## Contact & Governance

**Project Sponsor:** [Name]  
**Technical Lead:** [Name]  
**Security Advisor:** [CSA-certified consultant]  
**Review Frequency:** Weekly during active phases  
**Escalation Path:** Technical Lead → Project Sponsor → Executive Steering Committee

---

**Document Version:** 1.0  
**Last Updated:** [Date]  
**Next Review:** End of Phase 1