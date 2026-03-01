# Hierarchical Domain Specification: CCoP 2.0 Compliance Evaluation

Following LalaEval's domain specification methodology (Sun et al., 2024), this document defines the hierarchical domain structure for evaluating LLMs on Singapore's Cybersecurity Code of Practice (CCoP) 2.0 compliance advisory.

## Domain Hierarchy

```
CCoP 2.0 Compliance Advisory
│
├── L1: General Capabilities
│   │
│   ├── L2: Regulatory Language Understanding
│   │   ├── L3: Terminology Comprehension          ── B4  (7 cases)
│   │   ├── L3: Clause Interpretation               ── B5  (7 cases)
│   │   └── L3: Applicability Determination          ── B1  (8 cases)
│   │
│   ├── L2: Reasoning Quality
│   │   ├── L3: Conditional Logic                    ── B3  (7 cases)
│   │   ├── L3: Cross-Scenario Consistency           ── B19 (3 cases)
│   │   └── L3: Proportional Judgment                ── B11 (7 cases)
│   │
│   └── L2: Safety Boundaries
│       ├── L3: Hallucination Resistance             ── B21 (7 cases)
│       └── L3: Over-Specification Avoidance         ── B20 (3 cases)
│
├── L1: Domain Capabilities
│   │
│   ├── L2: Compliance Assessment
│   │   ├── L3: Binary Compliance Judgment           ── B2  (7 cases)
│   │   ├── L3: Control Intent Understanding         ── B6  (7 cases)
│   │   └── L3: Policy vs Practice Distinction       ── B17 (3 cases)
│   │
│   ├── L2: Gap & Risk Analysis
│   │   ├── L3: Gap Identification                   ── B7  (8 cases) [expert rubric needed]
│   │   ├── L3: Gap Prioritisation                   ── B8  (7 cases)
│   │   ├── L3: Risk Identification                  ── B9  (7 cases)
│   │   ├── L3: Risk Justification                   ── B10 (7 cases) [expert rubric needed]
│   │   └── L3: Residual Risk Awareness              ── B16 (3 cases) [expert rubric needed]
│   │
│   ├── L2: Audit & Evidence
│   │   ├── L3: Audit Perspective Alignment          ── B12 (4 cases)
│   │   └── L3: Evidence Expectation Awareness       ── B13 (3 cases)
│   │
│   ├── L2: Remediation Planning
│   │   ├── L3: Recommendation Quality               ── B14 (3 cases) [expert rubric needed]
│   │   └── L3: Feasibility Assessment               ── B15 (3 cases)
│   │
│   └── L2: IT/OT Convergence
│       └── L3: IT/OT System Classification          ── B4  (7 cases, shared with Terminology)
│
└── L1: Singapore Regulatory Context
    │
    ├── L2: Legal Framework
    │   ├── L3: Cybersecurity Act 2018               ── B1  (8 cases, shared with Applicability)
    │   └── L3: Responsibility Attribution            ── B18 (7 cases)
    │
    └── L2: Institutional Roles
        ├── L3: CIIO Obligations                     ── B18 (shared)
        ├── L3: CSA / Commissioner Powers            ── B18 (shared)
        └── L3: Sector Lead Coordination             ── [no benchmark]
```

## Hierarchy Levels Explained

### L1: Capability Areas (3)

| L1 Area | Purpose | Benchmarks | Cases |
|---------|---------|------------|-------|
| General Capabilities | Language understanding, reasoning quality, safety — capabilities needed regardless of domain | B1, B3, B4, B5, B11, B19, B20, B21 | 49 |
| Domain Capabilities | CCoP-specific compliance reasoning — the core domain expertise being evaluated | B2, B6, B7, B8, B9, B10, B12, B13, B14, B15, B16, B17 | 59 |
| Singapore Regulatory Context | Singapore-specific legal framework and institutional knowledge | B1, B18 | 15 |

### L2: Capability Dimensions (9)

| L2 Dimension | L1 Parent | What It Measures | Benchmarks |
|-------------|-----------|-----------------|------------|
| Regulatory Language Understanding | General | Can the model read and interpret CCoP text correctly? | B1, B4, B5 |
| Reasoning Quality | General | Does the model reason logically and consistently? | B3, B11, B19 |
| Safety Boundaries | General | Does the model avoid fabrication and over-specification? | B20, B21 |
| Compliance Assessment | Domain | Can the model make audit-style compliance judgments? | B2, B6, B17 |
| Gap & Risk Analysis | Domain | Can the model identify, justify, and prioritize compliance gaps and risks? | B7, B8, B9, B10, B16 |
| Audit & Evidence | Domain | Does the model understand audit methodology and evidence requirements? | B12, B13 |
| Remediation Planning | Domain | Can the model recommend practical, feasible remediation? | B14, B15 |
| IT/OT Convergence | Domain | Does the model handle IT/OT boundary complexities correctly? | B4 |
| Legal Framework | Singapore | Does the model understand the Cybersecurity Act and institutional roles? | B1, B18 |

### L3: Evaluation Targets (21+)

Each L3 node maps to a specific benchmark (B1–B21). Some benchmarks serve multiple L2 dimensions (e.g., B4 covers both Terminology and IT/OT Classification, B1 covers both Applicability and Legal Framework).

## Mapping to CCoP 2.0 Sections

| CCoP Section | L2 Dimension | L3 Targets | Benchmarks |
|-------------|-------------|------------|------------|
| Section 1–2: Scope & Definitions | Regulatory Language, Legal Framework | Applicability, Terminology | B1, B4, B5 |
| Section 3: Governance | Compliance Assessment, Legal Framework | Policy vs Practice, Responsibility | B17, B18 |
| Section 5: Protection | Compliance Assessment, Gap & Risk | Compliance Judgment, Gap ID, Risk ID | B2, B3, B6, B7, B8, B9, B10, B11 |
| Section 6: Detection | Gap & Risk, Audit & Evidence | Gap ID, Audit Perspective | B7, B9, B12, B13 |
| Section 7: Response & Recovery | Remediation Planning, Gap & Risk | Recommendation Quality, Feasibility, Residual Risk | B14, B15, B16 |
| Section 9: Training | Audit & Evidence | Evidence Awareness | B13 |
| Section 10: OT Security | IT/OT Convergence, Gap & Risk | IT/OT Classification, Risk ID | B4, B9, B16 |
| Cross-sectional | Reasoning Quality, Safety Boundaries | Consistency, Hallucination, Over-Specification | B19, B20, B21 |

## Mapping to Evaluation Tiers

| Tier | Method | L2 Dimensions Covered | Benchmarks |
|------|--------|----------------------|------------|
| Tier 1: Binary/Rule-Based | Label accuracy, hallucination detection, term matching | Regulatory Language, Compliance Assessment, Safety | B1, B2, B3, B4, B5, B6, B21 |
| Tier 2: Semantic Similarity | Sentence embeddings + key-fact recall | Reasoning Quality, Gap & Risk, Remediation, IT/OT | B8, B9, B11, B15, B17, B18, B19 |
| Tier 3: LLM-as-Judge | Claude evaluates with rubric | Audit & Evidence, Compliance Assessment, Safety | B12, B13, B20 |
| Unimplemented: Expert Rubric | Human expert scoring (1–5 scale) | Gap & Risk, Remediation | B7, B10, B14, B16 |

## Gap Analysis

### Gaps in Domain Hierarchy (no benchmark coverage)

| Gap | L1 | L2 | Description | Severity |
|-----|----|----|-------------|----------|
| G1 | Singapore | Institutional Roles | Sector Lead coordination — no benchmark tests understanding of sector-specific regulatory bodies | Low |
| G2 | Domain | IT/OT Convergence | Only 1 benchmark (B4) covers IT/OT — insufficient for a domain where 59% of test cases are IT/OT scenarios | Medium |
| G3 | General | Contextual Conversation | No multi-turn evaluation — compliance advisory is often conversational | Medium |
| G4 | General | Regulatory Language | No benchmark for understanding regulatory updates or version differences (CCoP 1.0 vs 2.0) | Low |
| G5 | Domain | Compliance Assessment | No benchmark for cross-regulatory mapping (CCoP vs NIST, ISO 27001) | Low |

### Gaps in Dataset Adequacy

| Issue | Affected Benchmarks | Impact |
|-------|-------------------|--------|
| 3 cases per benchmark (statistical inadequacy) | B13, B14, B15, B16, B17, B19, B20 | Cannot compute confidence intervals; results are anecdotal |
| LLM-generated test cases (expert validation pending) | All | Accuracy of expected responses not verified by domain experts |
| 4 benchmarks without automated scoring | B7, B10, B14, B16 | Cannot run full evaluation without human scorers |
| Difficulty levels unused in scoring | All | No stratified analysis (easy vs hard performance) |

### Gaps vs LalaEval Methodology

| LalaEval Requirement | Our Status | Gap |
|---------------------|------------|-----|
| Domain hierarchy drives benchmark creation | Hierarchy created retroactively | Benchmarks predate hierarchy — no top-down design |
| Min 3 human evaluators per response | Automated (Tier 1/2), single LLM judge (Tier 3) | No inter-rater reliability for Tier 3 |
| Anchored rubric levels (0/1/2/3 with definitions) | Continuous scores (0.0–1.0) without interpretive anchors | Scores lack compliance meaning |
| Evaluator training and calibration | N/A | No consistency validation for Claude judge |
| Dispute analysis and grade fluctuation tracking | Not implemented | No variability measurement |
| Quality inspection loop for test cases | Schema validation only | No content quality review by experts |

## Hierarchy-to-Benchmark Coverage Matrix

```
                          B1 B2 B3 B4 B5 B6 B7 B8 B9 B10 B11 B12 B13 B14 B15 B16 B17 B18 B19 B20 B21
Regulatory Language       x        x  x
Reasoning Quality               x                          x                          x
Safety Boundaries                                                                          x   x
Compliance Assessment        x        x     x                                    x
Gap & Risk Analysis                         x  x  x  x                      x
Audit & Evidence                                              x   x
Remediation Planning                                                    x   x
IT/OT Convergence                    x
Legal Framework           x                                                      x
Institutional Roles                                                              x
```

Legend: `x` = benchmark covers this dimension

## References

- Sun, C. et al. (2024). "LalaEval: A Holistic Human Evaluation Framework for Domain-Specific Large Language Models." arXiv:2408.13338
- CCoP 2.0 Second Edition Revision One — Cyber Security Agency of Singapore
- Cybersecurity Act 2018 — Singapore Statutes
