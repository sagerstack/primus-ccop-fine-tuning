# Scoring Methodology – Phase 2 (Fine-Tuning Evaluation)

## 1. Overview

This document defines the **Phase 2 evaluation and scoring methodology** used to assess the baseline and fine-tuned performance of the Llama-Primus-Reasoning model on **CCoP 2.0 compliance benchmarks**. The methodology retains the original weighted-metric scoring structure for continuity with the mid-term report, while refining metric interpretation, thresholds, and benchmark alignment to support a **fine-tuning–centric research objective**.

Phase 2 evaluation is **diagnostic rather than production-oriented**. A low baseline score is expected and is used to justify domain adaptation through fine-tuning.

---

## 2. Evaluation Flow (Phase 2)

1. **Load Test Case**

   * Question (prompt)
   * Ground-truth answer
   * Benchmark ID (B1–B21)
   * Key facts and evaluation constraints

2. **Generate Model Response**

   * Neutral system prompt (no CCoP-specific priming for baseline evaluation)
   * Model inference using Llama-Primus-Reasoning
   * Capture response text and metadata

3. **Benchmark-Aware Scoring**

   * Accuracy (label-based or semantic, depending on benchmark type)
   * Completeness (key-fact coverage)
   * Regulatory grounding and safety checks
   * Optional concision penalty

4. **Aggregate and Interpret Score**

   * Weighted metric aggregation
   * Phase-aware pass/fail logic
   * Persist results for analysis

---

## 3. Scoring Formula (Unchanged)

For each test case, the overall score is computed as:

```
Overall Score = Σ(metric.value × metric.weight) / Σ(metric.weight)
```

This formulation is unchanged from the mid-term report and ensures continuity across evaluation phases.

---

## 4. Phase-Aware Pass Thresholds

Evaluation thresholds are explicitly **phase-dependent**.

| Phase    | Model              | Purpose                       | Pass Threshold |
| -------- | ------------------ | ----------------------------- | -------------- |
| Phase 2  | Baseline (untuned) | Diagnostic screening          | **≥ 15%**      |
| Phase 3+ | Fine-tuned         | Measure reasoning improvement | ≥ 50%          |
| Future   | Deployment         | Regulatory readiness          | ≥ 85%          |

A ≥15% baseline score is **intentional** and indicates that fine-tuning is required; it does **not** imply regulatory or production readiness.

---

## 5. Metric Definitions (Updated)

### 5.1 Accuracy (Benchmark-Aware)

Accuracy is interpreted based on benchmark type:

* **Classification benchmarks** (e.g., applicability determination, compliance classification):
  Accuracy is scored using label matching (Exact = 1.0, Partial = 0.7, Incorrect = 0.0).

* **Reasoning benchmarks** (interpretation, gap analysis, risk reasoning, remediation):
  Accuracy is assessed using **semantic equivalence**, allowing correct paraphrases and audit-style explanations to be scored appropriately.

* **Safety benchmarks**:
  Accuracy is evaluated using binary pass/fail checks based on hallucination or over-specification.

Lexical similarity metrics (e.g., Jaccard similarity) may be retained **only as diagnostic indicators** and are not treated as the primary measure of correctness for reasoning-based benchmarks.

---

### 5.2 Completeness (Key-Fact Recall)

Completeness is measured by coverage of required regulatory facts rather than sentence-level or keyword overlap.

```
Completeness = (# key facts covered) / (total key facts)
```

Key facts are short, atomic statements derived from the ground-truth answer (typically 3–8 per test case) and represent essential compliance requirements or reasoning elements.

---

### 5.3 Regulatory Grounding and Safety

Hallucination is defined as the introduction of **unsupported or fabricated regulatory claims**, including:

* Invented CCoP obligations
* Incorrect legal or regulatory definitions
* Fabricated or misleading clause references

Uncertainty or conditional reasoning language (e.g., “depends on the implemented controls”) is **not penalised**, as it reflects appropriate compliance reasoning behaviour.

---

### 5.4 Optional Concision Metric

An optional concision or verbosity metric may be applied to discourage excessively long responses that dilute correctness or introduce irrelevant material. This metric is used as a secondary signal and does not dominate the overall score.

---

## 6. Benchmark-Specific Scoring Alignment

Benchmarks are conceptually grouped but evaluated using the same metric framework:

| Benchmark Group                         | Primary Evaluation Signals                      |
| --------------------------------------- | ----------------------------------------------- |
| B1–B5 (Applicability & Interpretation)  | Label accuracy, semantic correctness            |
| B6–B12 (Compliance & Risk Reasoning)    | Key-fact recall, reasoning quality              |
| B13–B16 (Remediation & Audit Reasoning) | Practicality, audit alignment                   |
| B17–B19 (Governance & Consistency)      | Responsibility attribution, reasoning stability |
| B20–B21 (Safety & Grounding)            | Hallucination and over-specification checks     |

Benchmarks without bespoke scoring functions inherit the evaluation behaviour appropriate to their benchmark category.

---

## 7. Interpretation of Results (Phase 2)

Phase 2 results are interpreted diagnostically:

* **Low score with high completeness** indicates verbosity or weak precision.
* **Low score with low completeness** indicates a knowledge or reasoning gap.
* **Hallucination detected** indicates unsafe behaviour for compliance reasoning tasks.

The objective of Phase 2 is to **identify systematic weaknesses** that fine-tuning is expected to address, rather than to demonstrate regulatory correctness.

---

## 8. Limitations

* Semantic evaluation may require expert judgement for some benchmarks.
* Clause citation accuracy is intentionally deprioritised in Phase 2.
* Performance metrics (e.g., latency, memory usage) are out of scope and deferred to later deployment-focused phases.

---

## 9. Implementation Notes

* Scoring Service: `scoring_service.py`
* Evaluation Pipeline: `evaluate_model.py`
* Result Storage: `json_result_repository.py`

---

**Document Version**: 2.0
**Scope**: Phase 2 – Fine-Tuning Evaluation
**Supersedes**: Scoring Methodology v1.0
