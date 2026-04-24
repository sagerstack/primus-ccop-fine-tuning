# CyberSecEval 2/3/4 (Meta, 2024-2025)

**Category**: Cybersecurity-specific benchmark
**Canonical sources**:
- CyberSecEval 2: [Bhatt et al., 2024 — arXiv:2404.13161](https://arxiv.org/abs/2404.13161)
- CyberSecEval 3: [Meta research page](https://ai.meta.com/research/publications/cyberseceval-3-advancing-the-evaluation-of-cybersecurity-risks-and-capabilities-in-large-language-models/)
- CyberSecEval 4 docs: [meta-llama.github.io/PurpleLlama/CyberSecEval](https://meta-llama.github.io/PurpleLlama/CyberSecEval/docs/intro)
- Code: [meta-llama/PurpleLlama](https://github.com/meta-llama/PurpleLlama/tree/main/CybersecurityBenchmarks)

## Scoring mechanics

CyberSecEval is a **benchmark suite**, not a rubric — but the scoring methodologies it defines for different cybersecurity tasks are instructive for our design. The most relevant tests for our use case:

| Test | Scoring method | Scale |
|------|---------------|-------|
| **MITRE ATT&CK compliance** | LLM judge classifies response as compliant/non-compliant with attack-assistance refusal | Binary (+refusal type) |
| **False Refusal Rate (FRR)** | LLM judge detects over-refusal on benign security queries | Binary |
| **Secure Code Generation / Instruct / Autocomplete** | Static analysis via ICD (Insecure Code Detector) — a rule-based checker | Binary per rule |
| **Prompt Injection** | LLM judge + rule check — did injection succeed? | Binary |
| **Malware Analysis (CyberSOCEval)** | Multiple-choice grading — answer key ground truth | Precision / recall on MCQ |
| **Threat Intelligence Reasoning** | Multiple-choice grading (multi-answer-correct variant) | Precision / recall |
| **AutoPatchBench** | Differential testing — does the patched binary still fail fuzz? | Binary pass/fail |

Notable: **CyberSecEval mixes LLM-as-judge, rule-based checkers, and MCQ scoring depending on task type.** Not all cyber evaluation is LLM-judged — when deterministic checkers exist (ICD, fuzzers, MCQ keys), they are preferred.

## Prompt scaffolding (LLM-judged components)

For MITRE and FRR tests, the judge prompt follows a structured classification pattern:

1. Present the question and model response.
2. Ask the judge to classify the response type (accept / refuse / partial).
3. Separately ask whether the acceptance/refusal was appropriate.

Two-stage classification reduces single-prompt cognitive load and improves agreement.

## Ground-truth requirements

| Test | GT shape |
|------|----------|
| MITRE | `(prompt, attack_technique_id, is_malicious)` — technique IDs from MITRE ATT&CK framework |
| FRR | `(prompt, intended_benign_label)` |
| Secure Code Gen | `(prompt, language, vulnerability_category)` — checker does the grading |
| MCQ tests | `(question, options[], correct_options)` |
| AutoPatchBench | `(CVE_id, vulnerable_code, fuzz_corpus)` — functional ground truth, no textual reference |

**Key GT innovation for cybersec**: CyberSecEval uses **threat-framework-grounded** ground truth (MITRE ATT&CK IDs, CWE numbers). A response can be scored against a formal taxonomy, not just a reference text.

## Annotation cost

- MITRE mapping requires cybersecurity expert familiar with ATT&CK framework — ~10-30 min per case.
- MCQ tests (malware analysis) built by security analysts; ~15-30 min per case for high-quality distractors.
- Meta released these sets publicly; annotation cost is amortized across the community.

## Bias / reliability controls

- Uses deterministic checkers where possible → no LLM-judge variance.
- Multi-model ensemble judging for MITRE (multiple LLMs classify, majority vote) in CyberSecEval 3+.
- Pre-registered prompts — all judge prompts are published; no silent prompt drift.

## Reported limitations

- MITRE classification has ~75-85% agreement with expert judgment — leaves room for error.
- LLM-as-judge components acknowledged as noisy; static analysis preferred when possible.
- Binary classification is coarse — cannot distinguish partial compliance from full refusal.

## Citation / fact grounding

Not a concept in the suite — CyberSecEval tests focus on behavior (refuse/assist, write secure/insecure code, identify malware) rather than citation fidelity. This is a significant gap for regulatory QA.

## Domain fit for cybersecurity compliance QA

- **Directly applicable**: deterministic-first scoring. We already apply this for B1/B2/B4/B5/B6/B21 (keyword / Jaccard / regex) — CyberSecEval validates this approach for cyber domains.
- **Directly applicable**: the **taxonomy-grounded GT** pattern. CyberSecEval uses MITRE ATT&CK / CWE; we use CCoP clause IDs. Our schema already does this — it's a strength.
- **Partially applicable**: CyberSOCEval's multi-choice questions for unambiguous tasks — we could convert some B21 hallucination tests from open-ended to MCQ and eliminate judge noise entirely (trade: less realistic task, deterministic scoring).
- **Gap revealed**: CyberSecEval has no compliance-QA suite. The closest is MITRE refusal, which is about **attack assistance refusal**, not regulatory interpretation. Our 21 benchmarks fill a niche CyberSecEval does not.

## Concrete borrowable patterns

1. **Prefer deterministic checkers where possible** — our regex-based B21 check is aligned with this philosophy; expand to other benchmarks where feasible.
2. **Multi-stage judge classification** (classify type, then evaluate appropriateness) — more reliable than single-prompt scoring.
3. **Public, version-pinned prompts** — publish all rubric prompts (we already do in `evaluation-rubrics.md`) for reproducibility.
4. **Framework taxonomy as GT** — our `clause_reference` serves this role; could be extended to carry `framework` field ("CCoP 2.0", "Cybersecurity Act 2018") as a first-class dimension.

## Sources used

- CyberSecEval 2 arXiv: https://arxiv.org/abs/2404.13161 (accessed 2026-04-24)
- CyberSecEval 3 page: https://ai.meta.com/research/publications/cyberseceval-3-advancing-the-evaluation-of-cybersecurity-risks-and-capabilities-in-large-language-models/ (accessed 2026-04-24)
- CyberSecEval 4 docs: https://meta-llama.github.io/PurpleLlama/CyberSecEval/docs/intro (accessed 2026-04-24)
- GitHub: https://github.com/meta-llama/PurpleLlama/tree/main/CybersecurityBenchmarks (accessed 2026-04-24)
