# SFR-Judge (Salesforce AI Research, September 2024)

**Category**: Industry fine-tuned generative judge, multi-mode (pairwise + single-rating + classification)
**Canonical sources**:
- Salesforce blog: [Accelerating Your Model Evaluation and Fine-tuning with SFR-Judge](https://www.salesforce.com/blog/sfr-judge/)
- Paper: "Direct Judgement Preference Optimization" — [arXiv:2409.14664](https://arxiv.org/abs/2409.14664), published EMNLP 2025 ([aclanthology.org/2025.emnlp-main.103](https://aclanthology.org/2025.emnlp-main.103.pdf))
- GitHub: [SalesforceAIResearch/SFRJudge](https://github.com/SalesforceAIResearch/SFRJudge)

**Important distinction**: "SFR-LLaMa-3.1-70B-Judge-r" on RewardBench leaderboard = the paper's SFR-Judge-70B. Sometimes shortened to "SFR-Judge-r".

## Base model + size

| Variant | Base | Parameters |
|---------|------|-----------|
| SFR-Judge-8B | Llama-3.1-8B-Instruct | 8B |
| SFR-Judge-12B | NeMo-Instruct-12B (Mistral NeMo) | 12B |
| SFR-Judge-70B | Llama-3.1-70B-Instruct | 70B |

## Training data / method

- **Three evaluation tasks trained jointly**:
  1. **Pairwise**: "Is output A better than output B?"
  2. **Single rating** (Likert 1-5): "Rate this response 1 to 5."
  3. **Classification**: "Does this output meet criterion X (binary)?"

- Training method: **Direct Judgement Preference Optimization** — a DPO variant specifically for judge training. Uses teacher Llama-3.1-70B-Instruct to sample judgments via DCoT (deep chain-of-thought) and rejection-sample high-quality training data.
- Key design choice: the model is trained to **produce both explanations and judgments** — not just a preference label. This matches our requirement for a "5 integer scores + justifications" judge.

## License

- Underlying weights: Llama-3.1 Community License (for 8B, 70B) or Mistral NRAIL license (for 12B NeMo).
- SFR-Judge weights on HuggingFace: model cards have been published by Salesforce (the github org `SalesforceAIResearch` hosts inference code) but the weights themselves are **gated**. Commercial availability at release time was framed as "research preview" — check current HF page before citing commercial usability.
- Code: Apache-2.0 (standard Salesforce practice for research code).

**License confidence: MEDIUM**. Verify HF model-card license fields directly before deployment. Llama-3.1 base allows commercial use under 700M MAU; SFR's release terms may add constraints.

## Deployment profile

| Variant | FP16 VRAM | Q4 VRAM | Fits 24 GB? |
|---------|-----------|---------|-------------|
| SFR-Judge-8B | ~16 GB | ~5 GB | Yes |
| SFR-Judge-12B | ~24 GB | ~8 GB | Yes at Q4/Q5 |
| SFR-Judge-70B | ~140 GB | ~40 GB | No (needs 2× 4090 or A100) |

Paper §6 (experiments): "scores reported in our paper were obtained by running evaluation with 8× A100 40GB GPUs" — for the 70B, matches expectations.

Integration: HF transformers; SFRJudge repo has evaluation scripts for 13 benchmarks.

## Reported reliability numbers

**Primary paper (aclanthology.org/2025.emnlp-main.103.pdf, Table 3-4):**

Pairwise benchmarks (out of 7, scores are aggregate):

| Model | Aggregate Pairwise |
|-------|--------------------|
| SFR-Judge-70B | **84.25** |
| Skywork-Critic-70B | 80.03 |
| Self-taught-evaluator-70B | 82.26 |
| SFR-Judge-12B | ~79 |
| SFR-Judge-8B | 80.91 |
| Skywork-Critic-8B | 77.49 |

**Confidence: HIGH** — peer-reviewed EMNLP 2025 paper.

**RewardBench (official leaderboard, Oct 2024):**

| Model | Chat | Chat Hard | Safety | Reasoning | Overall |
|-------|------|-----------|--------|-----------|---------|
| Skywork-Critic-70B | 96.6 | 87.9 | 93.1 | 95.5 | 93.3 |
| **SFR-Llama-3.1-70B-Judge-r** | 96.9 | 84.8 | 91.6 | 97.6 | **92.7** |
| SFR-nemo-12B-Judge-r | 97.2 | 82.2 | 86.5 | 95.1 | 90.3 |
| SFR-Llama-3.1-8B-Judge-r | 95.5 | 77.7 | 86.2 | 95.1 | 88.7 |

SFR-Judge-70B is top-3 on RewardBench; top on Reasoning (97.6). **Confidence: HIGH**.

**JudgeBench (ICLR 2025, Table 4)**: SFR-Judge-70B competitive (~60-65 range; not the absolute top but close to Skywork-Critic-70B).

**JETTS (arXiv:2504.15253) test-time scaling**:

| Variant | ~score |
|---------|--------|
| SFR-Judge-8B | 0.941 |
| SFR-Judge-12B | 0.943 |
| SFR-Judge-70B | 0.951 |

On test-time scaling scenarios, SFR-Judge-70B is top among 70B-class generative judges. **Confidence: HIGH.**

## Reference-aware scoring support

**Yes — strongest in the cohort.** The training format explicitly includes reference answers for single-rating tasks. Salesforce blog: "trained to perform three different types of evaluation tasks, including... single ratings ('Rate the output on a Likert scale of 1-5')".

**Critical: SFR-Judge is the only open-source judge we surveyed that was explicitly trained on all three modes including single-rating with reference.** This is a strong architectural match for our pipeline.

## Instance-rubric support

**Yes — via the classification mode**, which accepts arbitrary binary criteria ("Does the output meet the specified criteria?"). For 1-5 Likert mode, the criteria field is included in the prompt but not with per-level anchored descriptors like Prometheus.

**Partial match for our use case.** Better than Skywork-Critic / Self-Taught Evaluator (which don't support user-specified criteria) but weaker than Prometheus/M-Prometheus (which have first-class per-level descriptors).

## Cybersecurity / regulatory / compliance fit

- No direct cybersecurity benchmark.
- Base Llama-3.1-8B: MMLU ~69%; Llama-3.1-70B: MMLU ~82%.
- Safety RewardBench subset: SFR-70B = 91.6 (refusal detection strong).
- Top on Reasoning subset (97.6 for 70B, 95.1 for 12B, 95.1 for 8B). **Strongest reasoning of the 8B/12B cohort.**

## Known failure modes

- **70B training compute heavy**, not accessible to most research groups.
- Explanation quality varies by mode — paper shows classification-mode explanations are shorter than pairwise.
- Position bias not separately evaluated in the paper.
- **HF gated weights**: Access may require request.

## Ease of integration

- HuggingFace transformers: standard; the SFRJudge repo provides direct evaluation scripts.
- No native vLLM script from the authors, but standard compatibility.
- No Ollama release.
- Python package: `SalesforceAIResearch/SFRJudge` repo is the primary code path.

**Integration effort for 8B: ~1 day** (gated-access acceptance + prompt adaptation). **For 12B: same** — and the 12B fits 24 GB VRAM at Q5_K_M with the Mistral NeMo base.

## Recommendation summary

- **Strength**: Only open-source judge with explicit single-rating + reference-answer training; strong RewardBench Reasoning scores; 12B variant fits on 24 GB; Apache code license; published by a major industrial lab.
- **Weakness for us**: No per-instance anchored rubric (only classification-style criteria); 70B not feasible on single 4090; weights are gated.
- **Verdict**: **Strong secondary candidate.** Particularly SFR-Judge-12B (Mistral NeMo) as a 12B option that fits 24 GB at Q4/Q5. If we wanted a non-Qwen, non-Mistral reference-aware judge as the cross-family secondary, SFR-Judge-8B is a defensible pick.

## Sources used (all verified accessible 2026-04-24)

- [Salesforce blog](https://www.salesforce.com/blog/sfr-judge/)
- [SFR-Judge paper (aclanthology.org/2025.emnlp-main.103)](https://aclanthology.org/2025.emnlp-main.103.pdf)
- [SFR-Judge paper on arXiv:2409.14664](https://arxiv.org/abs/2409.14664)
- [github.com/SalesforceAIResearch/SFRJudge](https://github.com/SalesforceAIResearch/SFRJudge)
- [allenai/reward-bench-results entry for SFR-LLaMa-3.1-70B-Judge-r](https://huggingface.co/datasets/allenai/reward-bench-results/commit/ede56ac110e4440c9617cdf4f9e216e83c1cd10a)
- [JETTS paper Table 2 (arXiv:2504.15253)](https://arxiv.org/pdf/2504.15253)
