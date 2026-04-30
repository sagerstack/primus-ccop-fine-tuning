# JudgeLM (Zhu et al., ICLR 2025 Spotlight)

**Category**: Academic fine-tuned evaluator LM, Vicuna-based
**Canonical sources**:
- Paper: [arXiv:2310.17631](https://arxiv.org/abs/2310.17631) (v2 March 2025; accepted ICLR 2025 Spotlight)
- GitHub: [baaivision/JudgeLM](https://github.com/baaivision/JudgeLM)
- OpenReview: [xsELpEPn4A](https://openreview.net/forum?id=xsELpEPn4A)

## Base model + size

| Variant | Base | Parameters |
|---------|------|-----------|
| JudgeLM-7B | Vicuna-7B-v1.3 (Llama-2-based) | 7B |
| JudgeLM-13B | Vicuna-13B-v1.3 | 13B |
| JudgeLM-33B | Vicuna-33B-v1.3 | 33B |

Note: Vicuna-33B is Llama-1-based; Vicuna-7B/13B-v1.3 are Llama-2-based. Confirm by checking the Vicuna model card before deploying.

## Training data / method

- Dataset: ~100K training samples, consisting of task seeds, LLM-generated answers, and GPT-4-generated judgments. Released as "JudgeLM-100K" dataset.
- The dataset also includes a **new benchmark for evaluating judges** (JudgeLM benchmark, ~5K held-out samples).
- Training objective: supervised fine-tuning on GPT-4 judgments (teacher distillation).
- **Three bias-mitigation techniques** that are the paper's main methodological contribution:
  - **Swap augmentation**: swap (A, B) pairs during training to reduce position bias.
  - **Reference support**: use reference answers during training; improves pairwise accuracy.
  - **Reference drop**: randomly drop references 50% of the time so the model handles both reference-present and reference-absent inputs.

## License

- Weights: **"Non-commercial license" per GitHub repo** — the GitHub README states usage is limited to research purposes due to the underlying Vicuna and Llama-2 licenses. Specifically, Vicuna-v1.3 inherits Llama-2 Community License (research + commercial under 700M MAU, with use-case restrictions), and the instruction data from ShareGPT is governed by ShareGPT's terms (research-only).
- Code: Apache-2.0.
- **License confidence: MEDIUM**. The README is not explicit about a single SPDX identifier; researcher-use is safe, commercial deployment requires careful review. For a dissertation evaluation artifact, it's fine.

## Deployment profile

| Variant | FP16 VRAM | Q4 VRAM | Fits 24 GB? |
|---------|-----------|---------|-------------|
| JudgeLM-7B | ~14 GB | ~4 GB | Yes |
| JudgeLM-13B | ~26 GB | ~8 GB | Yes at Q4/Q5 |
| JudgeLM-33B | ~66 GB | ~20 GB | Marginal at Q4; tight on 4090 |

**Inference speed** (from primary paper §3.1): "JudgeLM-7B only needs 3 minutes to judge 5K samples with 8 A100 GPUs." Adjusting for 1× RTX 4090 (~1/4 the throughput of 8× A100 for this workload), expect ~40-60 minutes for our 1,770 judge calls with JudgeLM-7B. Acceptable.

Integration: Standard HuggingFace transformers `AutoModelForCausalLM.from_pretrained("BAAI/JudgeLM-7B-v1.0")`. The repo provides a FastAPI inference server and a vLLM serving script.

## Reported reliability numbers

**Primary paper (arXiv:2310.17631, Table 2 in v2):**

| Model | JudgeLM test Agreement w/ GPT-4 | Consistency |
|-------|--------------------------------|-------------|
| JudgeLM-7B | 81.11% | 83.57% |
| JudgeLM-13B | 84.08% | 85.57% |
| JudgeLM-33B | **89.03%** | **92.37%** |
| GPT-4 (teacher) | N/A (reference) | 87.93% |

**PandaLM benchmark agreement** (Table 3 in v2):

| Model | Agreement | F1 |
|-------|-----------|----|
| JudgeLM-33B | 90.06% | 86.57% |
| GPT-4 | 87.95% | 82.66% |

**Human agreement** (Table 4 in v2; 5K random subset human-annotated): JudgeLM-33B agreement with human = **91.36%**; GPT-4 human agreement = 90.27%.

**Confidence: HIGH** — primary paper, ICLR 2025 Spotlight (peer-reviewed and replicated for publication).

**JudgeBench (ICLR 2025, arXiv:2410.12784) performance** — a harder benchmark than the JudgeLM-authored one:

| Variant | Knowledge | Reasoning | Math | Coding | Overall |
|---------|-----------|-----------|------|--------|---------|
| JudgeLM-7B | 23.38 | 29.59 | 32.14 | 11.90 | 25.14 |
| JudgeLM-13B | 26.62 | 29.59 | 28.57 | 19.05 | 26.86 |
| JudgeLM-33B | 32.47 | 48.98 | 33.93 | 19.05 | 35.71 |

**Note: JudgeLM underperforms Prometheus-2-BGB-8x7B (overall 39.43) on JudgeBench.** On hard reasoning, JudgeLM-33B is actually *better* than Prometheus-2-BGB-8x7B (48.98 vs 30.61) — an interesting asymmetry, likely because the Vicuna base had stronger instruction-following and the reference-support training explicitly trains reasoning-reference alignment.

**Confidence: HIGH** — JudgeBench primary paper Table 4.

## Reference-aware scoring support

**Yes — explicitly designed for it.** "Reference support" is one of the three key techniques. The prompt template takes `{question, reference_answer, answer_1, answer_2}` for pairwise or `{question, reference_answer, answer}` for single.

**Caveat**: JudgeLM was primarily trained in pairwise mode. Single-answer mode is supported but the paper's strongest numbers are pairwise. Our pipeline is **single-response direct assessment** — we would need to use JudgeLM in its less-stressed mode.

## Instance-rubric support

**Partial.** JudgeLM is trained on "general quality" criteria as defined by GPT-4 judgments during training. It does NOT have the Prometheus-style per-instance 5-level anchored descriptor field. Our instance-rubric would need to be injected into the `question` field or as part of the instruction preamble — not as a first-class rubric.

**This is a MEANINGFUL LIMITATION for our use case**: JudgeLM's scoring granularity is 1-10 (or pairwise verdict), not anchored to user-specified descriptors.

## Cybersecurity / regulatory / compliance fit

- No direct cybersecurity benchmarks.
- Base model (Vicuna-7B/13B-v1.3) is Llama-2-based; Llama-2 MMLU is ~54% for 13B. **Weaker base than Qwen2.5-14B or Llama-3.1-8B.**
- The main reliability-mitigation work (swap augmentation) is directly applicable to our position-bias diagnostic plan (main research §3, rank 3 in gap analysis).

## Known failure modes

- **Single-answer mode less-tested** than pairwise. The paper's §4.2 explicitly notes this.
- **Position bias** reduced but not eliminated by swap augmentation (paper §5.3).
- **Knowledge bias**: when the judge's own knowledge disagrees with the reference answer, JudgeLM sometimes defers to its own knowledge. This is especially risky in a regulatory domain where the reference is authoritative.
- **Format bias**: JudgeLM prefers answers with a similar format/style to Vicuna outputs (paper §5.3).

## Ease of integration

- HuggingFace transformers: straightforward.
- vLLM: supported via the official serving script.
- Ollama: community GGUFs exist for 7B/13B; 33B is less commonly converted.
- Python package: No dedicated pip package; the GitHub repo provides utility scripts to run inference.

## Recommendation summary

- **Strength**: Reference-aware, well-documented position-bias mitigation, fast inference.
- **Weakness for us**: Primarily pairwise; no instance-rubric as first-class field; Llama-2-based reasoning ceiling below Qwen2.5.
- **Verdict**: Secondary-quality option behind Prometheus 2 / M-Prometheus for our use case. Main value would be **as a cross-family secondary judge** (different family than Prometheus, good for inter-judge agreement).

## Sources used (all verified accessible 2026-04-24)

- [arXiv:2310.17631](https://arxiv.org/abs/2310.17631)
- [github.com/baaivision/JudgeLM](https://github.com/baaivision/JudgeLM)
- [OpenReview forum xsELpEPn4A](https://openreview.net/forum?id=xsELpEPn4A)
- [JudgeBench paper (arXiv:2410.12784)](https://arxiv.org/abs/2410.12784) for JudgeBench scores
