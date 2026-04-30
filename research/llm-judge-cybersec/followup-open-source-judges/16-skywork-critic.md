# Skywork-Critic (Skywork AI, August-September 2024)

**Category**: Industry fine-tuned generative judge, Llama-3.1-based
**Canonical sources**:
- HF 8B: [Skywork/Skywork-Critic-Llama-3.1-8B](https://huggingface.co/Skywork/Skywork-Critic-Llama-3.1-8B)
- HF 70B: [Skywork/Skywork-Critic-Llama-3.1-70B](https://huggingface.co/Skywork/Skywork-Critic-Llama-3.1-70B)
- GGUF community: [QuantFactory/Skywork-Critic-Llama-3.1-8B-GGUF](https://huggingface.co/QuantFactory/Skywork-Critic-Llama-3.1-8B-GGUF)
- GitHub (Skywork-Reward parent repo): [github.com/SkyworkAI/Skywork-Reward](https://github.com/SkyworkAI/Skywork-Reward)

**Note**: No standalone Skywork-Critic paper. Brief technical description on the model card. Skywork-Reward paper is [arXiv:2410.18451](http://arxiv.org/abs/2410.18451).

## Base model + size

| Variant | Base | Parameters |
|---------|------|-----------|
| Skywork-Critic-Llama3.1-8B | Meta-Llama-3.1-8B-Instruct | 8B |
| Skywork-Critic-Llama3.1-70B | Meta-Llama-3.1-70B-Instruct | 70B |

## Training data / method

- **80K high-quality preference pairs** (authors assert they are curated from publicly-available preference datasets with filtering).
- Trained via supervised fine-tuning (SFT) — not RLHF or DPO.
- Training stack: **not publicly documented in detail** (no paper, only model-card blurb).
- Output format: generative pairwise judge with a score + rationale; 8B variant is noted by the authors as less reliable than 70B ("8B-parameter models struggle to produce reliable judgments for responses").

**Important authorial quote from the 70B model card**: "Our preliminary research indicates that 8B-parameter models struggle to produce reliable judgments for responses. Consequently, we exclusively utilize the Skywork-Critic-Llama3.1-70B model as our judge."

This is a strong signal that the 8B variant is **not recommended for serious use** by its own authors.

## License

- **Skywork Community License** — supports commercial use subject to terms. Model and derivatives are governed by the license; users must adhere to restrictions (e.g., not for national/societal security threats or unlawful actions).
- **License confidence: HIGH** — explicit on model card; [license PDF](https://huggingface.co/datasets/Skywork/SkyPile-150B/resolve/main/Skywork%20Community%20License.pdf?download=true).
- Commercial-use allowed; one must abide by the Community License.
- This is more permissive than Meta's Self-Taught Evaluator (research-only) and Qwen's license, but less permissive than pure Apache-2.0.

## Deployment profile

| Variant | FP16 VRAM | Q4 VRAM | Fits 24 GB? |
|---------|-----------|---------|-------------|
| Skywork-Critic-8B | ~16 GB | ~5 GB | Yes |
| Skywork-Critic-70B | ~140 GB | ~40 GB | No (needs 2× 4090 or A100/H100) |

Authors' GGUF community uploads exist (QuantFactory/Skywork-Critic-Llama-3.1-8B-GGUF) — usable in Ollama/llama.cpp.

Integration: standard HF transformers. 8B fits easily on 4090.

## Reported reliability numbers

**RewardBench leaderboard (as of Sep/Oct 2024, per model card):**

| Model | Chat | Chat Hard | Safety | Reasoning | Overall |
|-------|------|-----------|--------|-----------|---------|
| **Skywork-Critic-Llama3.1-70B** | 96.6 | 87.9 | 93.1 | 95.5 | **93.3** |
| Salesforce SFR-Llama-3.1-70B-Judge-r | 96.9 | 84.8 | 91.6 | 97.6 | 92.7 |
| **Skywork-Critic-Llama3.1-8B** | 93.6 | 81.4 | 91.1 | 89.8 | **89.0** |
| Salesforce SFR-Llama-3.1-8B-Judge-r | 95.5 | 77.7 | 86.2 | 95.1 | 88.7 |
| Self-taught-Llama-3-70B | 96.9 | 84.0 | 91.1 | 82.5 | 88.6 |
| GPT-4o-2024-08-06 | 96.1 | 76.1 | 88.1 | 86.6 | 86.7 |
| Claude-3.5-Sonnet-2024-06-20 | 96.4 | 74.0 | 81.6 | 84.7 | 84.2 |

**Confidence: HIGH** — RewardBench is a well-established benchmark, scores independently run by the Skywork team on the official test script. Cross-validated in JETTS paper (arXiv:2504.15253) — Skywork-Critic-70B leads the generative judge category.

**RewardBench 2 (arXiv:2506.01937, 2025):** Skywork-Critic not in the top results; reward-classification models dominate. Skywork-Reward-Llama-3.1-8B-v0.2 scores 71.8 — but that's a classifier reward model, not Skywork-Critic.

**JudgeBench (arXiv:2410.12784 Table 4):**

| Variant | Knowledge | Reasoning | Math | Coding | Overall |
|---------|-----------|-----------|------|--------|---------|
| Skywork-Llama-3.1-8B | 51.30 | 54.08 | 73.21 | 33.33 | **53.43** |
| Skywork-Llama-3.1-70B | 55.84 | 55.10 | 73.21 | 47.62 | **57.43** |

**On JudgeBench, Skywork-Critic-70B (57.43) beats Prometheus-2-BGB-8x7B (39.43) by ~18 points** — substantial. **Confidence: HIGH** — JudgeBench paper Table 4.

**JETTS (arXiv:2504.15253)** — test-time scaling judge evaluation: Skywork-Critic-70B is competitive; 8B performs noticeably worse than 70B on test-time scaling tasks (specifically flagged as the "8B-vs-70B difficulty gap" in the paper's Figure 2).

## Reference-aware scoring support

**Partial** — Llama-3.1-Instruct base supports reference injection in the system or user prompt; Skywork-Critic prompt template (in model card's example) accepts an instruction + response pair (pairwise-only shown in the model card). For single-response with reference, the user must construct the prompt; no first-class reference slot.

## Instance-rubric support

**No** — pairwise preference judge primarily. Users can include rubric descriptors in the prompt but the model wasn't trained on per-instance anchored rubrics.

**This is a meaningful limitation for our use case.**

## Cybersecurity / regulatory / compliance fit

- Strong RewardBench Safety subset (91.1 for 8B, 93.1 for 70B) — "safety" here means harmful-refusal detection, not regulatory compliance reasoning.
- Base Llama-3.1-8B-Instruct: MMLU ~69%, MMLU-Pro ~43%. Decent but not best-in-class among 7B-class models.
- No direct cybersecurity judge benchmark exists for Skywork-Critic.

## Known failure modes

- **8B variant explicitly flagged as unreliable by authors** (see above).
- **Pairwise-centric**: single-response direct assessment is a secondary mode.
- Position bias: not separately evaluated in a Skywork paper.
- **No instance rubric** — fundamental architecture gap for our use case.
- **No paper** — cannot cite methodology in an academic setting beyond the Skywork-Reward paper (which covers the preference-data curation, not the judge-training specifics).

## Ease of integration

- HuggingFace transformers: trivial.
- GGUF: community QuantFactory quantizations exist.
- Ollama: works via GGUF imports.
- vLLM: standard.

**Integration effort: ~4-8 hours** for 8B.

## Recommendation summary

- **Strength**: 70B variant is the top generative judge on RewardBench (as of Sep-2024) and top-3 on JudgeBench; Skywork Community License permits commercial use.
- **Weakness for us**: 8B authors explicitly say it's unreliable; 70B doesn't fit single 4090; no first-class instance-rubric or reference-answer slot; no paper to cite formally.
- **Verdict**: If we had multi-GPU, Skywork-Critic-70B would be a strong primary candidate. On single 4090, the 8B is disclaimed by its own authors. **Do not use as our primary judge on single 4090.** Consider as a cross-family secondary only if multi-GPU becomes available.

## Sources used (all verified accessible 2026-04-24)

- [huggingface.co/Skywork/Skywork-Critic-Llama-3.1-8B](https://huggingface.co/Skywork/Skywork-Critic-Llama-3.1-8B)
- [huggingface.co/Skywork/Skywork-Critic-Llama-3.1-70B](https://huggingface.co/Skywork/Skywork-Critic-Llama-3.1-70B)
- [huggingface.co/QuantFactory/Skywork-Critic-Llama-3.1-8B-GGUF](https://huggingface.co/QuantFactory/Skywork-Critic-Llama-3.1-8B-GGUF)
- [github.com/SkyworkAI/Skywork-Reward](https://github.com/SkyworkAI/Skywork-Reward)
- [Skywork Community License PDF](https://huggingface.co/datasets/Skywork/SkyPile-150B/resolve/main/Skywork%20Community%20License.pdf?download=true)
- [Skywork-Reward paper (arXiv:2410.18451)](http://arxiv.org/abs/2410.18451)
- [JudgeBench paper (arXiv:2410.12784)](https://arxiv.org/abs/2410.12784) Table 4
- [JETTS paper (arXiv:2504.15253)](https://arxiv.org/pdf/2504.15253) Figure 2
