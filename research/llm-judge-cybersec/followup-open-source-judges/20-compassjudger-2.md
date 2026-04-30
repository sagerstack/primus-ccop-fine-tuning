# CompassJudger-2 (Shanghai AI Lab, July 2025)

**Category**: Academic/industry fine-tuned generalist judge, Qwen2.5-based, verifiable-reward trained
**Canonical sources**:
- Paper: [arXiv:2507.09104](https://arxiv.org/html/2507.09104v1) ("CompassJudger-2: Towards Generalist Judge Model via Verifiable Rewards")
- GitHub: [open-compass/CompassJudger](https://github.com/open-compass/compassjudger) (same repo for v1 and v2)
- Paper hosted on: [emergentmind.com/papers/2507.09104](https://www.emergentmind.com/papers/2507.09104)

## Base model + size

| Variant | Base | Parameters |
|---------|------|-----------|
| CompassJudger-2-7B | Qwen2.5-7B-Instruct | 7B |
| CompassJudger-2-32B | Qwen2.5-32B-Instruct | 32B |

## Training data / method

- **Multi-domain judge data curation**: aggregates outputs from MMLU, CMMLU, GSM8K and similar standardized benchmarks; uses Qwen2.5-72B-Instruct to generate judgments with rationales, then validates against ground truth. Only verified-correct judgments retained.
- **Training objective**: rejection sampling + policy gradient (PPO-style) with verifiable rewards (VR). Rewards are tied to factual correctness, not just preference agreement.
- **Margin policy gradient loss**: a custom refinement of policy gradient that widens the reward margin between correct and incorrect judgments.
- Novel benchmark **JudgerBenchV2** introduced by the same paper — 10,000 questions across 10 scenarios. Treats a "Mix-of-Judgers" as ground truth.

## License

- Underlying Qwen2.5: Qwen Community License (commercial use permitted with Qwen license terms).
- CompassJudger weights: per GitHub repo, Apache-2.0 for code; weights license should be checked in HF model cards directly before deployment.
- **License confidence: MEDIUM** — paper is July 2025, verify model-card fields before any citation in dissertation.

## Deployment profile

| Variant | FP16 VRAM | Q4 VRAM | Fits 24 GB? |
|---------|-----------|---------|-------------|
| CompassJudger-2-7B | ~14 GB | ~5 GB | Yes |
| CompassJudger-2-32B | ~64 GB | ~20 GB | Marginal at Q4 (20-22 GB load + context = tight) |

Integration: Qwen2.5-compatible inference, any vLLM or transformers stack.

## Reported reliability numbers

**Primary paper (arXiv:2507.09104 v1 Table 1):**

| Model | JudgerBenchV2 | JudgeBench | RMB | RewardBench | Avg |
|-------|---------------|------------|-----|-------------|-----|
| Qwen2.5-7B-Instruct (base) | 57.14 | 23.23 | 69.03 | 79.69 | 57.27 |
| Llama3.1-8B-Instruct | 57.64 | 33.23 | 66.01 | 73.64 | 57.63 |
| Qwen2.5-32B-Instruct | 62.97 | 59.84 | 74.99 | 85.61 | 70.85 |
| DeepSeek-V3-0324 | 64.43 | 59.68 | 78.16 | 85.17 | 71.86 |
| Qwen3-235B-A22B | 61.40 | 65.97 | 75.59 | 84.68 | 71.91 |
| **CompassJudger-2-7B** | [higher than Qwen2.5-7B-Instruct; exact number not captured in highlights] | — | — | — | — |

Per the paper's abstract: "our 7B model demonstrating competitive accuracy against significantly larger models like DeepSeek-V3-0324 and Qwen3-235B-A22B." This is a striking claim — **a 7B judge beating 235B general model on judge tasks**.

**Confidence: MEDIUM-HIGH** for the abstract claim; the specific 7B score in the table was not fully captured in my search highlights — verify from the paper PDF directly before citing the exact number.

## Reference-aware scoring support

**Yes.** The training pipeline uses reference answers from standardized benchmarks (MMLU, GSM8K, etc.) as ground truth during judgment synthesis. Inference supports reference-anchored evaluation.

## Instance-rubric support

**Partial.** The paper emphasizes multi-domain coverage but does not claim Prometheus-style per-instance anchored descriptors. Users can inject rubrics in the prompt.

## Cybersecurity / regulatory / compliance fit

- No direct cybersecurity benchmarking.
- Qwen2.5-7B base: MMLU ~74%.
- Strong on knowledge-heavy JudgerBenchV2 scenarios (10 domains including factual QA).
- Base model identical to JudgeLRM-7B — comparable reasoning ceiling.

## Known failure modes

- **Recent release (July 2025)** — less third-party replication than Prometheus 2 or JudgeLM.
- **Multi-domain breadth may come at specialization cost**: generalist framing means the model may not deeply understand CCoP-specific reasoning patterns.
- Verifiable-reward training requires gold-truth labels; performance on open-ended domains without verifiable ground truth is less tested.

## Ease of integration

- HuggingFace transformers: straightforward, Qwen2.5-compatible.
- vLLM: compatible.
- OpenCompass ecosystem: the Shanghai AI Lab publishes a broader evaluation framework (OpenCompass) where this judge is the default — integration with OpenCompass is easiest.
- Ollama: not first-party.

**Integration effort: ~1-2 days** if using OpenCompass framework; ~1 day if using raw transformers.

## Recommendation summary

- **Strength**: Claims competitive 7B performance vs 235B general models; verifiable-reward training is a novel, sound methodology; Qwen2.5-based (matches M-Prometheus and JudgeLRM).
- **Weakness for us**: New release with less third-party validation; no explicit cybersecurity benchmark; license details need verification before commercial use.
- **Verdict**: **Dark-horse candidate.** The claimed 7B quality is remarkable if it holds up. **Worth including in a head-to-head pilot** against M-Prometheus-14B and JudgeLRM-7B before committing to a final secondary judge.

## Sources used (all verified accessible 2026-04-24)

- [arXiv paper HTML (arXiv:2507.09104)](https://arxiv.org/html/2507.09104v1)
- [arXiv paper PDF](https://arxiv.org/pdf/2507.09104)
- [github.com/open-compass/CompassJudger](https://github.com/open-compass/compassjudger)
- [emergentmind.com summary](https://www.emergentmind.com/papers/2507.09104)
