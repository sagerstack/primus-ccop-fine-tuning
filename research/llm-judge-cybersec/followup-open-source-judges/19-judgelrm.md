# JudgeLRM — Large Reasoning Models as a Judge (Chen et al., 2025)

**Category**: Academic RL-trained reasoning judge, Qwen2.5-based
**Canonical sources**:
- Paper: [arXiv:2504.00050](https://arxiv.org/abs/2504.00050) (Chen et al., 2025; v3 November 2025)
- GitHub: [NuoJohnChen/JudgeLRM](https://github.com/NuoJohnChen/JudgeLRM)
- HF paper page: [huggingface.co/papers/2504.00050](https://huggingface.co/papers/2504.00050)
- Demo: [huggingface.co/spaces/nuojohnchen/JudgeLRMDemo](https://huggingface.co/spaces/nuojohnchen/JudgeLRMDemo)

## Base model + size

| Variant | Base | Parameters |
|---------|------|-----------|
| JudgeLRM-3B | Qwen2.5-3B-Instruct | 3B |
| JudgeLRM-4B | Qwen2.5-4B-Instruct or Qwen3-4B | 4B |
| **JudgeLRM-7B** | **Qwen2.5-7B-Instruct** | **7B** |
| JudgeLRM-8B | (likely Llama-3.1-8B or Qwen2.5-7B variant) | 8B |
| JudgeLRM-14B | Qwen2.5-14B-Instruct | 14B |

## Training data / method

**Core contribution**: Pure RL training (not SFT) with judge-wise outcome-driven reward.

- Training objective: Reinforcement Learning with two rewards:
  - **Structural reward** — enforces the expected output format (reasoning trace + score).
  - **Content-based reward** — outcome-driven from judgment correctness against a teacher's known-correct judgment.
- Base models are initialized from Qwen2.5-Instruct and trained via RL on judge tasks.
- **Finding**: SFT-trained judges plateau in reasoning-intensive tasks; RL-trained judges continue to improve. Reasoning rate correlates +0.20 with performance gains — specifically for reasoning-heavy samples.

This is a distinctly different paradigm from Prometheus/JudgeLM/Auto-J (all SFT) or SFR-Judge/Self-Taught Evaluator (DPO/SFT + DPO).

## License

- Weights: **"Released for research purposes only"** per the paper's Limitations section. [OpenReview PDF, §Limitations].
- Underlying Qwen2.5 Community License applies.
- Code: Apache-2.0 per GitHub.

**License confidence: HIGH — explicitly research-only stated in the paper.** This is a key restriction.

**Relevance for dissertation**: research-only is acceptable for academic work. Commercial deployment: not permitted.

## Deployment profile

| Variant | FP16 VRAM | Q4 VRAM | Fits 24 GB? |
|---------|-----------|---------|-------------|
| JudgeLRM-3B | ~6 GB | ~2 GB | Yes |
| JudgeLRM-7B | ~14 GB | ~5 GB | Yes |
| JudgeLRM-14B | ~28 GB | ~10 GB | Yes at Q4/Q5 |

Integration: standard HuggingFace transformers, Qwen2.5-compatible inference stack.

## Reported reliability numbers

**Primary paper (arXiv:2504.00050 v3):**

PandaLM benchmark (out-of-distribution human-annotated):

| Model | F1 |
|-------|----|
| **JudgeLRM-3B/4B** | > GPT-4 |
| **JudgeLRM-7B/8B/14B** | DeepSeek-R1 + 2% |

(Paper Abstract and §5.)

Specific numbers from the abstract: "JudgeLRM-3B/4B exceeds GPT-4, while JudgeLRM-7B/8B/14B outperforms DeepSeek-R1 by over 2% in F1 score."

The paper compares against: Base (Qwen2.5-Instruct vanilla), SFT baselines (SFT-Answer, SFT-Think, SFT-Distill-R1-Think), DPO baselines, and CLS-RM/Bradley-Terry reward models.

**Confidence: MEDIUM-HIGH** — paper is peer-review-submitted (OpenReview shown), but exact benchmark F1 numbers need extraction from full Table (not captured in the highlights). The "surpasses GPT-4" claim is on PandaLM's test set, which has known difficulty characteristics.

**Cross-domain uses in other papers**:
- **CA-Judge for compliance** (AAAI 2025, Chen et al., ojs.aaai.org/index.php/AAAI/article/view/41298): "CA-Judge uses **JudgeLRM-7B**... grounded in domain-specific regulatory logic." This is the MOST DIRECTLY RELEVANT external validation for our use case — another group chose JudgeLRM-7B for a compliance-alignment task.

**Confidence: HIGH** for the CA-Judge endorsement (cited in a separate peer-reviewed AAAI paper).

## Reference-aware scoring support

**Yes.** PandaLM-style judge training includes a reference answer. The paper's experimental setup uses reference answers during RL training.

## Instance-rubric support

**Partial.** JudgeLRM's RL reward is outcome-driven, meaning it's trained to produce a judgment matching the teacher judgment. The prompt format is not explicitly rubric-first (like Prometheus), but arbitrary rubric descriptors can be injected into the instruction/context.

## Cybersecurity / regulatory / compliance fit

**Strongest external signal of all candidates.** The AAAI 2025 CA-Judge paper ("Compliance Alignment Judge") for regulatory-rule compliance verification **explicitly chose JudgeLRM-7B** as its grounding evaluator. Six dimensions covered: auditability (accuracy, fidelity), explainability (clarity, evidence use), reliability (consistency, verification).

While the CA-Judge paper is about modern slavery statement compliance (not cyber compliance), the **methodology transfer is direct**: regulatory rule → model justification → judge scores compliance dimensions. This maps cleanly onto our CCoP clause → model response → 5-dim judge.

- Base Qwen2.5-7B: MMLU ~74%, good reasoning.
- Qwen2.5-14B: MMLU ~80%.
- **Confidence for cybersec fit: MEDIUM** — indirect but the CA-Judge precedent is very strong.

## Known failure modes

- **Research-only license** — blocks deployment.
- RL training is known to be **brittle to reward-hacking**; the paper mitigates but doesn't eliminate.
- Less-established than Prometheus 2 (v3 submission from March 2025; newer in the literature).
- Format-reward may over-weight structural compliance at the cost of content quality — paper notes this trade-off.

## Ease of integration

- HuggingFace transformers: standard.
- Qwen2.5-compatible: same tokenizer, same chat template as M-Prometheus-7B.
- vLLM: compatible.
- Ollama: community GGUFs likely exist but not first-party.
- Demo on HF Spaces available for interactive testing before integration.

**Integration effort: ~1 day** similar to M-Prometheus.

## Recommendation summary

- **Strength**: Purpose-built for reasoning-intensive judge tasks; Qwen2.5 base (strong reasoning); **external validation by CA-Judge compliance paper**; small 7B variant fits 24 GB.
- **Weakness for us**: Research-only license limits deployment options; less rubric-centric than Prometheus; newer (April 2025) with less third-party replication.
- **Verdict**: **A very strong candidate if the license constraint is acceptable.** Specifically for the dissertation evaluation phase where research-only is fine, JudgeLRM-7B (or 14B) is a direct match for our regulatory-compliance domain. **This is the most underrated candidate given the CA-Judge precedent.**

## Sources used (all verified accessible 2026-04-24)

- [arXiv:2504.00050](https://arxiv.org/abs/2504.00050) (paper, v3)
- [github.com/NuoJohnChen/JudgeLRM](https://github.com/NuoJohnChen/JudgeLRM)
- [huggingface.co/papers/2504.00050](https://huggingface.co/papers/2504.00050)
- [huggingface.co/spaces/nuojohnchen/JudgeLRMDemo](https://huggingface.co/spaces/nuojohnchen/JudgeLRMDemo)
- [OpenReview PDF (forum 7JbWlwNltD)](https://openreview.net/forum?id=7JbWlwNltD)
- [CA-Judge compliance paper (AAAI 2025)](https://ojs.aaai.org/index.php/AAAI/article/view/41298/45259)
