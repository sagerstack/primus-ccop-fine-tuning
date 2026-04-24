# A Survey on LLM-as-a-Judge (Li / Jiang et al., 2024-2025)

**Category**: Academic meta-analysis — bias, reliability, calibration reference
**Canonical sources**:
- Survey: [Jiang et al., 2024 — arXiv:2411.15594](https://arxiv.org/abs/2411.15594) (v6 as of Oct 2025)
- Related position-bias study: [Shi et al., 2024 — arXiv:2406.07791](https://arxiv.org/abs/2406.07791)
- Awesome list: [CSHaitao/Awesome-LLMs-as-Judges](https://github.com/CSHaitao/Awesome-LLMs-as-Judges)
- Justice or Prejudice bias framework: [OpenReview 3GTtZFiajM](https://openreview.net/forum?id=3GTtZFiajM)

## Why a survey in our method list

The survey consolidates reliability, bias, and calibration findings across dozens of LLM-as-judge papers 2023-2025. For us, it's the single best source for **bias taxonomies** and **calibration strategies** — which is the single biggest weakness of our current judge.

## Bias taxonomy (expanded vs MT-Bench's 4)

The survey and companion CALM framework ([Justice or Prejudice](https://openreview.net/forum?id=3GTtZFiajM)) enumerate **12 biases**:

| # | Bias | Short description | Mitigation |
|---|------|-------------------|------------|
| 1 | Position bias | Prefers earlier or later position in pairwise | Position swap, averaging |
| 2 | Verbosity bias | Prefers longer responses | Length normalization, explicit instruction |
| 3 | Self-enhancement | Prefers outputs from own model family | Cross-family judge |
| 4 | Length bias | Related to verbosity but for single-answer scoring | Explicit anchor in rubric |
| 5 | Authority bias | Prefers responses that name authoritative sources even when wrong | Ground-truth-anchored rubric |
| 6 | Sycophancy bias | Agrees with user-stated preferences even when wrong | Hide user preference from judge |
| 7 | Beauty bias | Prefers formatted / structured output over content-equivalent unstructured | Content-only focus instruction |
| 8 | Refinement bias | Over-values polish over substance | Explicit rubric separation |
| 9 | Order bias (list) | Prefers certain orderings in list-wise | Randomize |
| 10 | Nepotism / Familiarity | Lower perplexity → higher score | Different judge family |
| 11 | Compassion/cultural bias | Scoring affected by demographic cues in content | Blind-scoring protocol |
| 12 | Chain-of-thought bias | CoT improves scores by laundering weak reasoning | Constrain CoT to specific form |

Position bias is strongly influenced by the **quality gap between solutions** (small gaps amplify position dependence) rather than prompt length — a finding from [Shi et al., 2024 arXiv:2406.07791](https://arxiv.org/abs/2406.07791).

## Calibration strategies (for single-answer scoring — our primary mode)

| Strategy | Description | Reported gain |
|----------|-------------|---------------|
| **Multiple Evidence Calibration** | Judge outputs multiple independent evidences, final score is an aggregate | 10-30% reduction in variance |
| **Balanced Position Calibration** | Run pairwise in both orders, average | Reduces position bias from ~30% asymmetry to <5% |
| **Human-in-the-loop Calibration** | Seed 5-10 human-scored cases, fit a linear correction | Bridges persistent model-human gap |
| **N-sample + Majority Vote** | 3-5 samples, integer modal score | Cuts variance ~40-60% per paper's summary |
| **Self-Consistency CoT** | N samples of CoT reasoning, majority on final score | Highest gain when model reasoning is the bottleneck |
| **Logprob-weighted scoring** (G-Eval) | Continuous score via token probabilities | Better continuous-metric correlation but needs logprob access |
| **Temperature-0 deterministic** | Single sample at temperature=0 | Sacrifices diversity; stable but not necessarily more accurate |

## Agreement metrics the field uses

The survey recommends reporting:
- **Pearson** correlation (interval agreement).
- **Spearman** correlation (rank agreement).
- **Cohen's κ / Fleiss' κ** (categorical agreement) — for discrete-anchored scores like our 0-3.
- **Krippendorff's α** (multi-rater, interval/ordinal).
- **Accuracy of verdict-direction** for binary tasks.

Our current evaluation does not compute any of these — we have no inter-judge agreement number and no judge-human agreement number.

## Reliability: target numbers the field reports

- GPT-4 judge vs human on MT-Bench: ~85% agreement (Zheng 2023).
- Prometheus-2-7B vs human: Pearson 0.897 on direct assessment (Kim 2024).
- RAGAS faithfulness vs human: ~0.80-0.85 Pearson on WikiEval (Es 2024).
- Open-source 7B judge ceiling without fine-tuning: ~60-70% accuracy vs GPT-4 judge.

**Implication for us**: we should target ≥0.80 Pearson with a gold human judgment subset before claiming the judge is reliable.

## Citation / fact grounding in the survey

The survey discusses grounding in the context of **reference-aware** vs **reference-free** judging. Reference-aware (which is our mode) has markedly higher human agreement on domains requiring correctness. The survey specifically flags hallucination-prone domains (medical, legal, regulatory) as requiring reference-aware judging.

## Domain fit for cybersecurity compliance QA

- **Direct application**: the bias taxonomy informs which biases to audit on our current judge. Position bias is the highest-priority candidate since we've never measured it.
- **Direct application**: the calibration table is a menu of concrete additions. Biggest-bang-for-buck for single-answer scoring: N-sample majority vote (cheap, high gain) and human-in-the-loop calibration (moderate effort, high gain).
- **Direct application**: agreement-metric recommendations — we should compute Cohen's κ between our judge and a small human-labeled subset (~20 cases) to establish baseline reliability.

## Concrete borrowable patterns

1. **Measure our own biases before mitigating** — run our current judge with position swap on a subset, report asymmetry.
2. **N=3 sample majority vote** as a cheap-first calibration step (cost: 3x judge calls; expected variance reduction: ~50%).
3. **Seed 20 human-labeled cases for calibration** — enables reporting Cohen's κ and a linear correction coefficient.
4. **Cross-family validation** — when we have Prometheus-2 running locally, use it as a secondary judge and report agreement between Claude and Prometheus.

## Sources used

- Main survey: https://arxiv.org/abs/2411.15594 (accessed 2026-04-24)
- Position bias study: https://arxiv.org/abs/2406.07791 (accessed 2026-04-24)
- CALM bias framework: https://openreview.net/forum?id=3GTtZFiajM (accessed 2026-04-24)
- Awesome-LLMs-as-Judges: https://github.com/CSHaitao/Awesome-LLMs-as-Judges (accessed 2026-04-24)
