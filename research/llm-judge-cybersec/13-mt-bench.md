# MT-Bench & Chatbot Arena — LLM-as-a-Judge Bias Analysis (Zheng et al., NeurIPS 2023)

**Category**: Academic judge (pairwise, crowd-validated) — primary source for bias taxonomy
**Canonical source**: [Zheng et al., NeurIPS 2023 — arXiv:2306.05685](https://arxiv.org/abs/2306.05685)

## Scoring mechanics

- **Judge model**: GPT-4 is the reference judge; GPT-3.5, Claude variants tested.
- **Three evaluation modes**:
  1. **Pairwise comparison** (A vs B, or tie) — primary method.
  2. **Single-answer grading** on a 1-10 scale.
  3. **Reference-guided grading** — judge receives the expected answer as anchor.
- **Composite**: Pairwise method aggregates over many pairs to produce win rates / Elo.

## Prompt scaffolding

- Question + two responses + judge-role system prompt.
- Optional reference answer when questions have a known solution.
- Explicit prompt to "focus on correctness first, then helpfulness".

## Ground-truth requirements

- MT-Bench: 80 multi-turn questions across 8 categories (writing, roleplay, extraction, reasoning, math, coding, STEM, humanities). For math/coding/reasoning, reference answers are provided.
- Chatbot Arena: 30K+ real user prompts with crowdsourced pairwise preferences — no ground-truth reference, humans vote.
- Key insight: **reference answers are essential for domains requiring correctness**. Without reference, judge agreement drops and biases worsen.

## Annotation cost

- MT-Bench: 3K expert votes collected for calibration — expensive but one-time.
- Chatbot Arena: continuous crowdsourced voting; free but noisier.

## Bias taxonomy (the paper's core contribution for our use case)

Zheng et al. catalog and **quantify** four biases:

| Bias | Definition | Mitigation tested | Effectiveness |
|------|------------|-------------------|---------------|
| **Position bias** | Judge favors first (or second) position in pairwise | Swap positions, count as tie if order-dependent | Highly effective — reduces bias from ~30% asymmetry to <5% |
| **Verbosity bias** | Judge prefers longer responses even when lower quality | Explicit instruction in prompt; length normalization; pairwise swap | Partially effective; GPT-4 least susceptible among tested judges |
| **Self-enhancement bias** | Judge rates outputs from its own family higher | Use different-family judge; cross-check with secondary judge | Effective when using cross-family judges |
| **Limited reasoning (math/code)** | Judge misses subtle errors in domains where it cannot reliably self-solve | Few-shot with known-hard examples; chain-of-thought; use reference answer | Partially effective |

### Position bias quantification

Paper's headline: in pairwise mode without swap, only GPT-4 gives consistent results >60% of the time. Claude-1 and GPT-3.5 flip verdicts depending on position >40% of the time. **Swapping and taking the more conservative (or tie) verdict cuts this to <10%**.

## Reliability

- GPT-4 achieves ~85% agreement with human pairwise preferences — at the level of human-human agreement.
- Single-answer grading is noisier than pairwise — on MT-Bench, pairwise gives higher agreement.

## Reported limitations

- Judge cannot reliably assess math/code where it cannot self-verify; specialized checkers (unit tests) beat the judge.
- Pairwise scales O(n²) for ranking — expensive for large test sets.
- Biases are not fully eliminated even with swap + reference.

## Citation / fact grounding

Not intrinsic to MT-Bench; the paper treats "reference-guided grading" as a deployment pattern for domains that need it. Citation correctness is NOT a first-class concept — the paper's tasks don't require clause-level attribution.

## Domain fit for cybersecurity compliance QA

- **Directly applicable**: position-swap protocol for any pairwise comparison we introduce (e.g., comparing fine-tuned vs baseline model outputs).
- **Applicable as diagnostic**: running our judge in both orders on our 118 cases would expose our own position bias — we currently don't measure this.
- **Less applicable**: pairwise-only evaluation has coarse resolution; our 5-dimension breakdown can't be reproduced from pairwise wins alone. Pairwise is a supplement to direct assessment, not a replacement.
- **Reference-guided grading pattern**: we already do this (inject `expected_response` + clause text); Zheng validates it as best-practice.

## Concrete borrowable patterns

1. **Position swap** when we use pairwise mode (not yet adopted).
2. **Verbosity constraint** in our prompt: explicitly tell the judge to ignore length when scoring — the paper shows even GPT-4 benefits from this instruction.
3. **Cross-family judge for self-enhancement**: if we later evaluate a Claude-family fine-tuned model (Llama-Primus is not Claude-family, so we're safe today), switch judge to GPT-4 or Prometheus.
4. **Reference-guided** single-answer grading with `expected_response` — already aligned with our approach.

## Sources used

- Paper: https://arxiv.org/abs/2306.05685 (accessed 2026-04-24)
- NeurIPS 2023 listing: https://neurips.cc/virtual/2023/poster/73434 (accessed 2026-04-24)
