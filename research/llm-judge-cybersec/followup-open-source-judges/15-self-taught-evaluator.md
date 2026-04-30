# Self-Taught Evaluator (Meta FAIR, August 2024)

**Category**: Academic fine-tuned evaluator, Llama-3.1-70B-based, iteratively self-improved
**Canonical sources**:
- Paper: [arXiv:2408.02666](https://arxiv.org/abs/2408.02666) (Wang et al., Meta FAIR, August 2024)
- HF weights: [facebook/Self-taught-evaluator-llama3.1-70B](https://huggingface.co/facebook/Self-taught-evaluator-llama3.1-70B) (**gated**)
- Code: [github.com/facebookresearch/RAM/tree/main/projects/self_taught_evaluator](https://github.com/facebookresearch/RAM/tree/main/projects/self_taught_evaluator)
- DPO training data (gated): [facebook/Self-taught-evaluator-DPO-data](https://huggingface.co/datasets/facebook/Self-taught-evaluator-DPO-data)

## Base model + size

| Variant | Base | Parameters |
|---------|------|-----------|
| Self-Taught Evaluator | Llama-3.1-70B-Instruct | 70B |

**Only the 70B release is official.** The paper implies the method generalizes but no smaller checkpoints published.

## Training data / method

**Key contribution**: no human-annotated preference data used. Pipeline:

1. Start from seed instructions (WildChat prompts).
2. Use seed LLM (Llama-3.1-70B-Instruct) to generate baseline response.
3. Prompt the LLM to generate a **deliberately-worse** modified response (inferior by construction).
4. Train the LLM-as-Judge on these synthetic preference pairs: generate reasoning trace + judgment; use synthetic label as supervision.
5. Iterate: use the improved judge to generate higher-quality pairs for the next DPO round.
6. Final training: SFT + DPO + NLL combined losses.

Paper reports: Llama-3.1-70B-Instruct baseline RewardBench = 75.4 → Self-Taught Evaluator RewardBench = 88.3 (88.7 with majority vote over 3 samples).

## License

- **Self-taught Evaluator Research License and Acceptable Use Policy** — NOT Apache-2.0, NOT Llama-3 Community License. A specific research-only license.
- **Gated model** — requires HuggingFace login + agreement to the research license before download.
- Dataset (DPO training data) is under the same research-only license.
- Commercial deployment: **NOT PERMITTED** under the research license.

**License confidence: HIGH** — HF model card explicitly states "gated / manual" and links "Research License for Self-taught Evaluator.pdf". Verified on 2026-04-24.

**Critical caveat for our use case**: dissertation-level academic use is permitted. Deploying this judge in any production-adjacent context is not.

## Deployment profile

| Variant | FP16 VRAM | Q4 VRAM | Q2 VRAM | Fits 24 GB? |
|---------|-----------|---------|---------|-------------|
| Self-Taught Evaluator 70B | ~140 GB | ~40 GB | ~20 GB | **Only at Q2**, which hurts quality significantly |

**On a single RTX 4090 (24 GB), this model is effectively unusable at useful quality.** Running at Q2 is risky for a judge where sub-percent accuracy differences matter. You'd need:

- 2× RTX 4090 (48 GB total) for Q4 — feasible but not in scope per our constraints.
- 1× A100 80GB for FP16 — not available per task brief.
- H100 or dual-A6000 — cloud rental ~$1.50/hr; full eval at 1,770 calls would complete in ~1-2 hours and cost ~$3-5. That's the most realistic path if we wanted to use this judge.

Integration: HF transformers with the `subfolder="dpo_model"` argument (two checkpoints in the repo: SFT and DPO — use DPO for inference).

## Reported reliability numbers

**Primary paper (arXiv:2408.02666):**

| Metric | Llama-3.1-70B baseline | Self-Taught Evaluator |
|--------|-----------------------|----------------------|
| RewardBench overall | 75.4 | **88.3** (88.7 w/ majority vote) |

RewardBench subsets (from the paper):

| Subset | Score |
|--------|-------|
| Chat | 96.9 |
| Chat Hard | 84.0 |
| Safety | 91.1 |
| Reasoning | 82.5 |

**Confidence: HIGH** — primary paper, Meta FAIR, replicated in the SFR-Judge paper's Table 2 (80.54 on Chat Hard, 93.67 on Safety — slight revision).

**JudgeBench / JuStRank**: Included as a baseline in both. On JudgeBench (Table 4, arXiv:2410.12784), Self-Taught Evaluator ~57.43 overall — strong. On JuStRank (arXiv:2412.09569), Self-Taught Evaluator competitive with the top prompted Llama-3.1-70B baselines.

## Reference-aware scoring support

**Yes.** The training data format includes instruction + two response candidates. For single-response with reference, the reference can be injected but was not the primary training format (pairwise-centric).

**Important limitation**: Self-Taught Evaluator is **pairwise-only** in its primary mode. The SFR-Judge paper (arXiv 2409.14664 / aclanthology.org/2025.emnlp-main.103) explicitly classifies it as "pairwise-only" vs SFR-Judge which handles all three modes (pairwise, single rating, classification).

For our pipeline (single-response direct assessment with reference), Self-Taught Evaluator would need to be coerced into a mode it wasn't trained for.

## Instance-rubric support

**No.** Training data was constructed from synthetic preference pairs over WildChat prompts; there is no rubric field. Users cannot inject per-case rubric descriptors.

**This is a hard miss for our requirement.**

## Cybersecurity / regulatory / compliance fit

- No cybersecurity benchmarks.
- Strong on RewardBench Safety subset (91.1) — but that's "refuse harmful requests," not "regulatory compliance reasoning."
- Base model Llama-3.1-70B has MMLU ~82%, MMLU-Pro ~55% — strong general reasoning.
- **Base-model strength is the best argument for this judge**; training method doesn't specialize it for regulatory reasoning.

## Known failure modes

- **Pairwise-centric**: less validated on single-response direct assessment.
- **Synthetic data bias**: training pairs are constructed by asking the same model to write a "worse" response — any systematic pattern in how Llama-3.1 produces degraded versions becomes a judge-bias.
- Research license restricts downstream use.
- 70B footprint — infeasible on single consumer GPU at reasonable precision.

## Ease of integration

- HuggingFace transformers with `subfolder="dpo_model"`.
- Gated download (manual HF license acceptance).
- No vLLM-specific serving script, but vLLM works out of the box.
- No Ollama release.

**Integration effort for our pipeline: HIGH** — infrastructure (multi-GPU or cloud A100), plus gated-download access request, plus pairwise-to-single-response prompt adaptation.

## Recommendation summary

- **Strength**: Strongest base model in the open-judge landscape; no human labels required for training (interesting methodology); high RewardBench score.
- **Weakness for us**: Research-only license, 70B size incompatible with single 4090, pairwise-centric, no instance rubric, no reference-anchored training.
- **Verdict**: Do not use as our judge. Cite as evidence that "synthetic-only training reaches GPT-4 judge quality" in the methodology discussion.

## Sources used (all verified accessible 2026-04-24)

- [arXiv:2408.02666](https://arxiv.org/abs/2408.02666) (paper)
- [huggingface.co/facebook/Self-taught-evaluator-llama3.1-70B](https://huggingface.co/facebook/Self-taught-evaluator-llama3.1-70B) (gated)
- [github.com/facebookresearch/RAM/tree/main/projects/self_taught_evaluator](https://github.com/facebookresearch/RAM/tree/main/projects/self_taught_evaluator)
- [RewardBench paper and leaderboard](https://huggingface.co/spaces/allenai/reward-bench)
- [SFR-Judge paper (aclanthology.org/2025.emnlp-main.103)](https://aclanthology.org/2025.emnlp-main.103.pdf) — competitive comparison
- [JudgeBench (arXiv:2410.12784)](https://arxiv.org/abs/2410.12784)
