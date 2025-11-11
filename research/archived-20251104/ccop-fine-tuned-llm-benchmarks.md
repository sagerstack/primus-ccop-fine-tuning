# CCoP 2.0 Fine-Tuned LLM Benchmarks - Complete Reference

## Overview

This document contains all 19 benchmarks for evaluating the CCoP 2.0 fine-tuned Llama-Primus-Reasoning model, organized by thematic categories.

---

## Category 1: Compliance Benchmarks (B1-B5)

**Purpose:** Measure the model's understanding of CCoP 2.0 requirements and regulatory accuracy

| Benchmark ID | Benchmark Name | Description | Target Metric | Dataset Size | Phase Introduced |
|--------------|----------------|-------------|---------------|--------------|------------------|
| **B1** | CCoP Interpretation Accuracy | Measures model's ability to correctly interpret and explain CCoP 2.0 clauses, handling both factual and ambiguous questions | **Factual:** >95%<br>**Ambiguous:** >85% | 50 test cases (20 factual, 20 ambiguous, 10 edge cases) | Phase 1 (5 tests)<br>Phase 2A (20 tests)<br>Phase 3 (50 tests) |
| **B2** | Clause Citation Accuracy | Evaluates whether model correctly cites specific CCoP sections when identifying violations | >90% exact section match | 20 violation scenarios | Phase 1 (5 tests)<br>Phase 2A (20 tests)<br>Phase 3 (20 tests) |
| **B3** | Hallucination Rate | Measures frequency of fabricated clauses, non-existent sections, or incorrect regulatory requirements | **0% tolerance** (Critical) | 30 tests (fake clauses, incorrect citations, misleading scenarios) | Phase 1 (5 tests)<br>Phase 2A (15 tests)<br>Phase 3 (30 tests) |
| **B4** | Singapore Terminology Accuracy | Tests correct usage of Singapore-specific regulatory terms (Commissioner, CII, prescribed timeframes, etc.) | **100% accuracy** (Non-negotiable) | 25 tests covering all key terms | Phase 1 (5 tests)<br>Phase 2A (10 tests)<br>Phase 3 (25 tests) |
| **B5** | IT vs OT Classification Accuracy | Measures ability to distinguish between IT and OT infrastructure types and apply appropriate CCoP sections | >95% correct classification | 30 scenarios across all CII sectors | Phase 1 (5 tests)<br>Phase 2A (15 tests)<br>Phase 3 (30 tests) |

---

## Category 2: Code & Infrastructure Benchmarks (B6-B8)

**Purpose:** Evaluate technical vulnerability detection capabilities (SAST, SCA, IaC scanning)

| Benchmark ID | Benchmark Name | Description | Target Metric | Dataset Size | Phase Introduced |
|--------------|----------------|-------------|---------------|--------------|------------------|
| **B6** | Code Violation Detection Rate | Measures ability to detect security vulnerabilities in source code (Python, Java, JavaScript, Go, C++) | **High/Critical:** >90%<br>**Medium:** >75%<br>**Low:** >60% | 60 vulnerable code samples across languages/frameworks | Phase 1 (10 tests)<br>Phase 2A (25 tests)<br>Phase 3 (60 tests) |
| **B7** | False Positive Rate | Evaluates how often model incorrectly flags secure code as vulnerable | <10% (Target)<br><15% (Acceptable) | 40 clean code samples that should NOT trigger violations | Phase 2A (20 tests)<br>Phase 3 (40 tests) |
| **B8** | IaC Misconfiguration Detection | Tests detection of security misconfigurations in Infrastructure as Code (Terraform, Kubernetes, CloudFormation) | >85% detection rate | 40 IaC configs (20 misconfigured, 20 correct) | Phase 2A (15 tests)<br>Phase 3 (40 tests) |

---

## Category 3: Advanced Capability Benchmarks (B9-B12)

**Purpose:** Assess broader use cases beyond basic code scanning (incident response, gap analysis, policy generation, cross-standard mapping)

| Benchmark ID | Benchmark Name | Description | Target Metric | Dataset Size | Phase Introduced |
|--------------|----------------|-------------|---------------|--------------|------------------|
| **B9** | Incident Classification Accuracy | Measures ability to correctly determine if incidents require CSA notification per CCoP reporting requirements | >95% correct classification | 25 incident scenarios (varying severity, multi-system, edge cases) | Phase 2A (10 tests)<br>Phase 3 (25 tests) |
| **B10** | Gap Analysis Quality | Evaluates quality of compliance gap analysis for organizations (subjective, requires expert review) | **Precision:** >85%<br>**Recall:** >80% | 15 organization profiles with varying maturity levels | Phase 2A (5 tests)<br>Phase 3 (15 tests) |
| **B11** | Policy Generation Quality | Assesses quality of generated security policies (access control, incident response, etc.) for audit readiness | >90% audit-ready without major revisions | 15 policy generation prompts across CCoP sections | Phase 2A (5 tests)<br>Phase 3 (15 tests) |
| **B12** | Cross-Standard Mapping Accuracy | Tests ability to map CCoP requirements to other frameworks (ISO 27001, NIST 800-53, IEC 62443, PCI DSS) | >85% correct mappings | 40 mapping scenarios across major frameworks | Phase 2A (15 tests)<br>Phase 3 (40 tests) |

---

## Category 4: Safety & Security Benchmarks (B13-B14)

**Purpose:** Validate adversarial robustness and safety preservation after fine-tuning

| Benchmark ID | Benchmark Name | Description | Target Metric | Dataset Size | Phase Introduced |
|--------------|----------------|-------------|---------------|--------------|------------------|
| **B13** | Prompt Injection Resistance | Measures resistance to adversarial prompts attempting to extract training data or bypass safety guidelines | >95% attack resistance | 10-25 injection attack variants | Phase 2B (10 tests)<br>Phase 3 (25 tests) |
| **B14** | Jailbreak Attempt Resistance | Tests resilience against jailbreak attempts to make model generate harmful security advice or bypass restrictions | >90% resistance | 10-25 jailbreak scenarios | Phase 2B (10 tests)<br>Phase 3 (25 tests) |

---

## Category 5: Training Quality Benchmarks (B15-B17)

**Purpose:** Monitor model learning effectiveness during fine-tuning process

| Benchmark ID | Benchmark Name | Description | Target Metric | Monitoring | Phase Introduced |
|--------------|----------------|-------------|---------------|------------|------------------|
| **B15** | Training Loss | Tracks loss during training to ensure model is learning | <0.5 at convergence | Continuous during training | Phase 2B (training monitoring)<br>Phase 3B (training monitoring) |
| **B16** | Validation Loss | Monitors validation loss to detect overfitting | Stable or decreasing trend | Continuous during training | Phase 2B (training monitoring)<br>Phase 3B (training monitoring) |
| **B17** | Perplexity Score | Measures model's prediction uncertainty (lower is better) | <20 | Continuous during training | Phase 2B (training monitoring)<br>Phase 3B (training monitoring) |

---

## Category 6: Performance Benchmarks (B18-B19)

**Purpose:** Ensure model meets operational efficiency requirements for production deployment

| Benchmark ID | Benchmark Name | Description | Target Metric | Measurement | Phase Introduced |
|--------------|----------------|-------------|---------------|-------------|------------------|
| **B18** | Inference Speed | Measures time to analyze single code file or configuration | <5 seconds per scan (Target)<br><8 seconds (Acceptable) | Production profiling | Phase 3C (performance profiling) |
| **B19** | Memory Usage | Tracks VRAM requirements for model inference | <16GB VRAM (Target)<br><24GB (Acceptable) | Production profiling | Phase 3C (performance profiling) |

---

## Benchmark Testing Schedule by Phase

### Phase 1: Quick Baseline Screening (2-3 days)
- **Benchmarks Tested:** B1, B2, B3, B4, B5, B6
- **Dataset Size:** 40 tests
- **Purpose:** Determine if baseline model has 15-20% understanding

### Phase 2A: Comprehensive Baseline (3-4 days)
- **Benchmarks Tested:** B1-B12
- **Dataset Size:** 170 tests
- **Purpose:** Detailed measurement across compliance, code, and advanced capabilities

### Phase 2B: Small Fine-Tune Test (3-4 days)
- **Benchmarks Tested:** B1-B17 (ALL except performance)
- **Dataset Size:** 190 tests (170 original + 20 safety tests)
- **Purpose:** Validate fine-tuning improves performance by >35%

### Phase 3C: Production Validation (1 week)
- **Benchmarks Tested:** B1-B19 (ALL)
- **Dataset Size:** 420 tests + profiling
- **Purpose:** Comprehensive production readiness validation

---

## Critical Success Metrics Summary

### Must-Pass (Non-Negotiable)
| Benchmark | Requirement | Consequence if Failed |
|-----------|-------------|----------------------|
| **B3** | 0% hallucinations | Project STOP - Safety risk |
| **B4** | 100% terminology accuracy | Project STOP - Regulatory risk |
| **B13-B14** | >95% attack resistance | Project STOP - Security vulnerability |

### Core Capabilities (Primary Value)
| Benchmark | Target | Acceptable Range |
|-----------|--------|------------------|
| **B1** | Factual: >95%, Ambiguous: >85% | Factual: 90-95%, Ambiguous: 80-85% |
| **B2** | >90% citation accuracy | 85-90% acceptable |
| **B5** | >95% IT/OT classification | 90-95% acceptable |
| **B6** | >90% high/critical detection | 85-90% acceptable |
| **B7** | <10% false positives | <15% acceptable |

### Advanced Features (Secondary Value)
| Benchmark | Target | Acceptable Range |
|-----------|--------|------------------|
| **B8** | >85% IaC detection | 80-85% acceptable |
| **B9-B12** | >85% average | 80-85% acceptable |

### Performance Requirements
| Benchmark | Target | Maximum Acceptable |
|-----------|--------|-------------------|
| **B18** | <5s per scan | <8s acceptable |
| **B19** | <16GB VRAM | <24GB acceptable |

---

## Benchmark Weighting for Overall Score

| Category | Weight | Rationale |
|----------|--------|-----------|
| **Compliance (B1-B5)** | 35% | Core regulatory accuracy |
| **Code Scanning (B6-B8)** | 30% | Primary technical value |
| **Advanced (B9-B12)** | 15% | Differentiating features |
| **Safety (B13-B14)** | 15% | Critical for production |
| **Performance (B18-B19)** | 5% | Operational efficiency |

**Overall Score Calculation:**
```
Total Score = (0.35 × Compliance) + (0.30 × Code) + (0.15 × Advanced) + (0.15 × Safety) + (0.05 × Performance)
```

**Production Ready Threshold:** >85% overall score with ALL must-pass criteria met

---

## Dataset Size Progression

| Phase | Training Data | Test Data | Total Examples |
|-------|--------------|-----------|----------------|
| **Phase 0** | 0 | 0 | 0 (Infrastructure only) |
| **Phase 1** | 0 | 40 | 40 |
| **Phase 2A** | 0 | 170 | 170 |
| **Phase 2B** | 148 | 190 | 338 |
| **Phase 3** | 4,850 | 420 | 5,270 |

---

## Benchmark Data Sources

| Benchmark Category | Primary Sources |
|-------------------|-----------------|
| **B1-B5 (Compliance)** | CCoP 2.0 official documentation, CSA guidance notes, enforcement actions |
| **B6-B8 (Code/IaC)** | OWASP WebGoat, GitHub vulnerable repos, OpenPLC, SCADA configs, CVE database |
| **B9 (Incidents)** | CSA incident reports, anonymized CII case studies |
| **B10-B11 (Gap/Policy)** | ISO 27001 gap assessments, real organization profiles |
| **B12 (Mapping)** | ISO 27001, NIST 800-53, IEC 62443, PCI DSS official mappings |
| **B13-B14 (Safety)** | Adversarial ML research, Prompt Guard 2 test cases, Llama Guard 4 scenarios |
| **B15-B17 (Training)** | Model training logs, validation metrics |
| **B18-B19 (Performance)** | Production profiling, benchmark testing |

---

## Expert Review Requirements

### Benchmarks Requiring Expert Validation
| Benchmark | Expert Type | Review Criteria |
|-----------|-------------|----------------|
| **B1** (Ambiguous Q&A) | CSA-certified CCoP auditor | Interpretation reasonableness |
| **B10** (Gap Analysis) | CII organization CISO | Practical applicability |
| **B11** (Policy Generation) | Compliance consultant | Audit readiness |
| **B5** (IT/OT) + **B8** (IaC) | OT/ICS security specialist | Section 10 accuracy |

### Expert Panel Composition (Phase 3)
- 2-3 CSA-certified CCoP auditors
- 2 CII organization CISOs
- 1 OT/ICS security specialist
- **Total:** 5-6 experts

---

## Version Control

**Document Version:** 1.0  
**Last Updated:** [Current Date]  
**Next Review:** End of Phase 1  
**Owner:** [Project Technical Lead]

---

## Quick Reference: Benchmark IDs

```
B1  - CCoP Interpretation Accuracy
B2  - Clause Citation Accuracy  
B3  - Hallucination Rate (0% required)
B4  - Singapore Terminology (100% required)
B5  - IT vs OT Classification
B6  - Code Violation Detection
B7  - False Positive Rate
B8  - IaC Misconfiguration Detection
B9  - Incident Classification
B10 - Gap Analysis Quality
B11 - Policy Generation Quality
B12 - Cross-Standard Mapping
B13 - Prompt Injection Resistance
B14 - Jailbreak Resistance
B15 - Training Loss
B16 - Validation Loss
B17 - Perplexity Score
B18 - Inference Speed
B19 - Memory Usage
```