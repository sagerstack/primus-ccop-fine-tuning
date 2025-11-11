# Fine-Tuning LLM on Singapore's Cybersecurity Code of Practice (CCoP 2.0) Standards for Critical Information Infrastructure: Mid-Term Report

**Project Period:** September 2025 - August 2026
**Author:** Sagar Pratap Singh
**Report Date:** 28 October 2025

## Executive Summary

This project addresses a critical gap in cybersecurity compliance automation by developing a fine-tuned Large Language Model (LLM) specifically trained on Singapore's Cybersecurity Code of Practice (CCoP 2.0) standards. With 220 complex regulatory requirements spanning both Information Technology (IT) and Operational Technology (OT) infrastructure, Critical Information Infrastructure (CII) organizations currently spend 12+ months on manual compliance processes. Our research aims to reduce this timeline significantly while achieving >85% accuracy in compliance violation detection through automated code and infrastructure analysis [1].

[1] Cyber Security Agency of Singapore, "Annual Cybersecurity Review 2024," CSA Singapore, Tech. Rep., 2024. [Online]. Available: https://www.csa.gov.sg/publications/reports


## 1. Project Objectives

1. Benchmark baseline performance of Llama-Primus-Reasoning model (8B parameters) on CCoP standards to establish current capabilities and identify knowledge gaps. Establish additional baseline benchmarks on Large-Language-Models like GPT-5 and DeepSeek-V3.

2. Fine-tune Llama-Primus on CCoP standards using QLoRA (Quantized Low-Rank Adaptation) by creating a comprehensive training dataset and training the model to achieve > 85% accuracy in detecting compliance violations with respect to CCoP (Cybersecurity Code of Practice) standards [2].

3. Deploy model to isolated environment (mimic CII) and integrate with CI/CD pipelines to detect non-compliant source codes and configurations across application and infrastructure with respect to CCoP standards.

[2] T. Dettmers, A. Pagnoni, A. Holtzman, and L. Zettlemoyer, "QLoRA: Efficient Finetuning of Quantized LLMs," arXiv preprint arXiv:2305.14314, 2023. [Online]. Available: https://arxiv.org/abs/2305.14314


## 2. CCoP 2.0 (Cybersecurity Code of Practice) Overview

The Cybersecurity Code of Practice 2.0 (CCoP 2.0) came into effect in August 2023 and became mandatory for all Critical Information Infrastructure Owners (CIIOs) by August 2024. For CIIOs, CCoP 2.0 means implementing comprehensive cybersecurity measures across both IT and OT infrastructure to protect Singapore's most critical assets and services from cyber threats. The regulation covers 220 complex requirements spanning multiple sectors including healthcare, banking, energy, transport, and government services [3].

The scope encompasses both Information Technology (IT) infrastructure - including computer networks, servers, cloud platforms, databases, and enterprise applications - and Operational Technology/Industrial Control Systems (OT/ICS) - which includes industrial control systems, SCADA systems, programmable logic controllers (PLCs), and critical operational equipment that manage physical processes and infrastructure.

[3] Cyber Security Agency of Singapore, "Cybersecurity Code of Practice - Second Edition, Revision One," CSA Singapore, Tech. Rep., 2023. [Online]. Available: https://isomer-user-content.by.gov.sg/36/2df750a7-a3bc-4d77-a492-d64f0ff4db5a/CCoP---Second-Edition_Revision-One.pdf

### 2.1 CCoP 2.0 Clauses & Scope

How CCoP is Organized [3]:

| Section | Section Details | Coverage Description | Infrastructure Type | Clauses | Training Implication |
|---------|----------------|----------------------|---------------------|---------|---------------------|
| 1. Audit | Cross-cutting | Audit trails, logging, monitoring, evidence collection | BOTH IT and OT contexts needed | ~4 | BOTH IT and OT contexts needed |
| 2. Governance | Cross-cutting | Security policies, roles, responsibilities, senior management oversight | BOTH IT and OT contexts needed | ~15-20 | BOTH IT and OT contexts needed |
| 3. Risk Management & Resilience | Mostly Cross-cutting (~80%), Some IT-Cloud (~20%) | Risk assessments, business continuity, disaster recovery, cloud risk management | BOTH IT and OT contexts, plus cloud-specific examples | ~25-30 | BOTH IT and OT contexts, plus cloud-specific examples |
| 4. Asset Management | Cross-cutting | Asset inventory, classification, data protection, hardware/software lifecycle | BOTH IT and OT contexts needed | ~8-10 | BOTH IT and OT contexts needed |
| 5. Protect | MIXED: ~50-60% IT-specific, ~40-50% Cross-cutting | Network security, access control, encryption, secure coding, patch management | IT examples primary, but substantial cross-cutting controls apply to both | ~80-90 | IT examples primary, but substantial cross-cutting controls apply to both |
| 6. Detect, Respond & Recover | Mostly Cross-cutting (~90%), Some IT (~10%) | Incident detection, response procedures, forensics, recovery planning | BOTH IT and OT contexts needed | ~25-30 | BOTH IT and OT contexts needed |
| 7. Cybersecurity Awareness | Mostly Cross-cutting (~90%), Some IT (~10%) | Staff training, security awareness programs, phishing prevention | BOTH IT and OT contexts needed | ~8-10 | BOTH IT and OT contexts needed |
| 8. Supply Chain Cybersecurity | Cross-cutting | Vendor security assessments, supply chain risk management, procurement security | BOTH IT and OT contexts needed | ~10-12 | BOTH IT and OT contexts needed |
| 9. Third Party Cybersecurity | Cross-cutting | Third-party access controls, contractor security, service provider management | BOTH IT and OT contexts needed | ~12-15 | BOTH IT and OT contexts needed |
| 10. OT/ICS Security | OT-only | Industrial control systems, SCADA security, Purdue Model, PLC protection | OT examples exclusively (SCADA, PLCs, Purdue Model) | ~35-40 | OT examples exclusively (SCADA, PLCs, Purdue Model) |
| 11. Assurance | Mostly Cross-cutting (~90%), Some IT (~10%) | Compliance verification, security testing, penetration testing, certification | BOTH IT and OT contexts needed | ~8-10 | BOTH IT and OT contexts needed |
| **TOTAL**                    | All Sections                                              | ~60% Cross-cutting, ~25% IT-specific, ~18% OT-specific      | ~220        | Unified training across all infrastructure types                                                      |

<sub><i>[1]: IT (Information Technology): Traditional enterprise computing systems (servers, databases, cloud, business applications) that process and store data.<br>
[2]: OT (Operational Technology): Industrial control systems (SCADA, PLCs, sensors) that monitor and control physical processes in critical infrastructure like power plants and water facilities.</i></sub>

### 2.2 CCoP 2.0 Training Strategy

Since 60% of CCoP clauses are cross-cutting (apply to both IT and OT), unified training of all 11 sections enables the model to learn relationships between infrastructure types, correctly distinguish when controls apply to IT-only vs OT-only vs both, and deploy as a single production model rather than maintaining separate IT/OT variants. The alternative strategy to train the model sequentially based on IT-only and subsequently OT controls could lead to catastrophic forgetting—if we train IT sections first then fine-tune on OT, the model loses IT knowledge (safety can drop) [4] [5].

[4] W. Zhao, J. Deng, D. Madras, J. Zou, and H. Ren, "Learning and Forgetting Unsafe Examples in Large Language Models," arXiv preprint arXiv:2312.12736, 2023. [Online]. Available: https://arxiv.org/abs/2312.12736

[5] L. Ung, F. Sun, J. Bell, H. Radharapu, L. Sagun, and A. Williams, "Chained Tuning Leads to Biased Forgetting," arXiv preprint arXiv:2412.16469, 2024. [Online]. Available: https://arxiv.org/abs/2412.16469

## 3. Fine-Tuning Strategy

### 3.1 Project Phases and Objectives

| Phase | Phase Name | Primary Objectives | Success Criteria | Dataset Size | Benchmarks |
|-------|------------|-------------------|------------------|--------------|------------|
| Phase 1 | Foundation & Setup | Establish technical infrastructure for model deployment | • GPU infrastructure operational<br>• LoRA framework installed<br>• Evaluation pipeline ready | - | - |
| Phase 2 | Quick Baseline Screening | Determine if base model has sufficient CCoP understanding | • **>15% baseline score**<br>• **Zero hallucinations** | 40 cases | B1-B6 |
| Phase 3 | Comprehensive Baseline | Identify strengths/weaknesses across CCoP sections | • Detailed performance mapping<br>• Gap analysis completed | 170 cases | B1-B12 |
| Phase 4 | Small Fine-Tune Test | Validate fine-tuning approach before full investment | • **>35% improvement**<br>• Training methodology confirmed | 148 examples | B1-B17 |
| Phase 5 | Full Dataset Creation | Create production dataset covering all CCoP sections | • 5,270 examples created<br>• All sections covered<br>• Zero data leakage | 5,270 total<br>(4,850 train + 420 test) | All 19 |
| Phase 6 | Comprehensive Fine-Tuning | Train production model with optimized hyperparameters | • Training convergence<br>• Safety monitoring<br>• Performance targets met | 4,850 training examples | All 19 |
| Phase 7 | Production Validation | Final testing to determine production readiness | • **>85% overall score**<br>• Expert approval<br>• Security assessment | 420 test examples | All 19 |

### 3.2 Critical Checkpoints

| Phase | Decision Point | Pass Criteria | Consequence of Failure |
|-------|----------------|---------------|------------------------|
| Phase 2 | Critical checkpoint | >15% score + zero hallucinations | **Project termination** |
| Phase 4 | Validation checkpoint | >35% improvement | **Re-evaluate approach** |
| Phase 7 | Production decision | >85% score + expert approval | **No deployment** |

### 3.3 Progressive Dataset Scaling Strategy

| Phase | Dataset Purpose | Scale | Risk Level |
|-------|-----------------|-------|------------|
| Phase 2 | Baseline competency test | 40 cases | Low risk |
| Phase 3 | Comprehensive baseline | 170 cases | Low risk |
| Phase 4 | Approach validation | 148 examples | Medium risk |
| Phase 5-6 | Production training | 5,270 examples | High investment |
| Phase 7 | Final validation | 420 test cases | Go/No-Go decision |

