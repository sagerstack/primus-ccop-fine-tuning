# Evaluation Benchmarks for CCoP 2.0

The initial benchmark design included clause citation–oriented metrics intended to assess regulatory grounding. Following an extended analysis of related work and a clearer separation between compliance reasoning (addressed by fine-tuning) and regulatory retrieval (better addressed by retrieval-based mechanisms), the benchmarks were refined to better align with the fine-tuning–centric scope of Phase 2. Specifically, benchmarks B1–B14 now focus on audit-style compliance reasoning capabilities—such as scenario interpretation, control relevance assessment, gap identification, risk justification, and remediation reasoning—that can be directly improved through fine-tuning. Benchmarks B15–B17 assess reasoning stability and governance awareness, while B18–B19 serve as safety-oriented checks for over-specification and regulatory hallucination. Clause citation–dependent metrics were removed from primary evaluation, ensuring methodological consistency and clearer interpretation of results.

## Rationale
Fine-tuning remains a valuable approach for applying large language models to CCoP 2.0 because it improves the model’s ability to reason about compliance scenarios in a way that reflects audit practice. Through domain-adapted fine-tuning, the model can better interpret operational contexts, identify likely control gaps, articulate risk-based justifications, and propose practical remediation actions. However, fine-tuning encodes regulatory knowledge implicitly in model parameters, which limits traceability, robustness to regulatory updates, and explicit clause citation. As a result, while fine-tuning is well suited for compliance reasoning, it is less suitable for regulatory grounding, motivating the separation of reasoning-focused benchmarks in Phase 2 and the identification of retrieval-based grounding as future work.

## List of Benchmarks (updated)

| Benchmark Category      | Benchmark ID | Benchmark Name                                  | Example Prompt                                                                                    | Fine-Tuning Impact | Why Fine-Tuning Has Strong Impact / What Is Evaluated                                                      |
| ----------------------- | ------------ | ----------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------- |
| Applicability & Scope   | **B1**       | CCoP Applicability & Core Terminology           | “Does CCoP apply to this system? Is it a CII or essential service? What is the digital boundary?” | **High**           | Evaluates understanding of CII/CIIO scope, digital boundary, and applicability under the Cybersecurity Act |
| Compliance Judgement    | **B2**       | Compliance Classification Accuracy              | “Given that CCoP applies, is the setup compliant?”                                                | **High**           | Learns audit-style compliance judgement once applicability is established                                  |
| Compliance Judgement    | **B3**       | Conditional Compliance Reasoning                | “Is the setup acceptable if compensating controls are in place?”                                  | **High**           | Evaluates nuanced conditional reasoning common in audits                                                   |
| Control Relevance       | **B4**       | Scenario-to-Control Mapping                     | “Which CCoP control domains apply here?”                                                          | **High**           | Baseline knowledge check for CCoP structure and control coverage                                           |
| Control Interpretation  | **B5**       | Control Requirement Comprehension               | “What does Clause 5.1.5 require regarding authentication?”                                        | **Medium**         | Evaluates accurate paraphrasing and literal understanding of CCoP control requirements                     |
| Control Interpretation  | **B6**       | Control Intent Understanding                    | “What is the intent of this access control requirement?”                                          | **High**           | Evaluates understanding beyond literal wording                                                             |
| Gap Analysis            | **B7**       | Gap Identification Quality                      | “What control gaps exist in the current setup?”                                                   | **High**           | Learns common compliance failure patterns                                                                  |
| Gap Analysis            | **B8**       | Gap Prioritisation                              | “Which gaps should be addressed first and why?”                                                   | **High**           | Encodes risk-based prioritisation logic                                                                    |
| Risk Reasoning          | **B9**       | Risk Identification Accuracy                    | “What risks arise from shared vendor accounts?”                                                   | **High**           | Improves recognition of compliance-specific risks                                                          |
| Risk Reasoning          | **B10**      | Risk Justification Coherence                    | “Why does this setup increase compliance risk?”                                                   | **High**           | Structured risk explanation, scored via expert rubric                                                      |
| Risk Reasoning          | **B11**      | Risk Severity Assessment                        | “How severe is the risk?”                                                                         | **High**           | Learns proportional judgement of severity                                                                  |
| Audit Reasoning         | **B12**      | Audit Perspective Alignment                     | “How would a CSA auditor assess this?”                                                            | **High**           | Encodes CSA-style audit reasoning                                                                          |
| Audit Reasoning         | **B13**      | Evidence Expectation Awareness                  | “What evidence would auditors expect?”                                                            | **High**           | Learns typical audit evidence expectations                                                                 |
| Remediation Reasoning   | **B14**      | Remediation Recommendation Quality              | “What remediation actions should be taken?”                                                       | **High**           | Learns practical, proportionate remediation                                                                |
| Remediation Reasoning   | **B15**      | Remediation Feasibility                         | “Are these remediation steps feasible in a CII?”                                                  | **High**           | Filters unrealistic advice                                                                                 |
| Remediation Reasoning   | **B16**      | Residual Risk Awareness                         | “What residual risks remain?”                                                                     | **High**           | Evaluates post-control reasoning                                                                           |
| Governance (SG Context) | **B17**      | Policy vs Practice Distinction                  | “If policies exist but are not enforced, how does this affect compliance?”                        | **Medium**         | Distinguishes documented policy from operational reality                                                   |
| Governance (SG Context) | **B18**      | Responsibility Attribution (Singapore-Specific) | “Who is accountable under CCoP for vendor access?”                                                | **Medium**         | Evaluates understanding of CIIO, CSA, Commissioner roles                                                   |
| Consistency             | **B19**      | Cross-Scenario Consistency                      | “Would the assessment change for an internal provider?”                                           | **Medium**         | Tests reasoning stability                                                                                  |
| Safety / Grounding      | **B20**      | Over-Specification Avoidance                    | “Does the response introduce unsupported requirements?”                                           | **Low**            | Lightweight grounding sanity check                                                                         |
| Safety / Grounding      | **B21**      | Regulatory Hallucination Rate                   | “Does the response fabricate CCoP obligations?”                                                   | **Low**            | Detects non-existent regulatory claims                                                                     |


Benchmarks B1–B15 evaluate compliance reasoning capabilities that are highly sensitive to domain-adapted fine-tuning. Benchmarks B16–B18 assess governance understanding and reasoning stability, including Singapore-specific regulatory context. Benchmarks B19–B20 serve as lightweight grounding and safety checks to prevent fabricated or over-specified regulatory claims without relying on retrieval-based citation. The benchmark framework was further refined to explicitly include foundational regulatory comprehension and Singapore-specific terminology. In particular, CCoP applicability and core terminology are evaluated upfront to ensure that subsequent compliance reasoning is applied only within the correct regulatory scope. A dedicated control requirement comprehension benchmark is included to verify accurate understanding of CCoP clauses before higher-order gap analysis and risk reasoning. These refinements preserve the fine-tuning-centric focus of Phase 2 while strengthening regulatory correctness and interpretability.

## Evaluation Methodology

Tier 1 – Binary Metrics (Automated / Rule-Based)
Benchmarks: B1, B2, B21

Scoring: binary (correct / incorrect)

Inter-rater reliability: not required

Tier 2 – Expert Rubric Metrics (Human-Scored)
Benchmarks: B7, B10, B14, B16

Scoring: 1–5 scale

Criteria:

Accuracy

Completeness

Practicality

Clarity

Inter-rater agreement: ≥80%

Tier 3 – Assisted Judgement (LLM-as-Judge + Human Validation)
Benchmarks: B12, B13, B20

Structured rubric evaluation using a general-purpose LLM

Human validation on ≥20% of samples

Human override if confidence <0.8

This tiered evaluation approach balances objectivity, expert judgement, and scalability, consistent with standard practice for evaluating reasoning-centric language model capabilities.