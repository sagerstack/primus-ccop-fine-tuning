# Llama-3.1-70B-Instruct and Qwen2.5-72B-Instruct as prompted judges

**Category**: General-purpose instruction-tuned LLMs used as zero-shot judges via careful prompting
**Canonical sources**:
- Llama-3.1: [meta-llama/Meta-Llama-3.1-70B-Instruct](https://huggingface.co/meta-llama/Meta-Llama-3.1-70B-Instruct)
- Qwen2.5: [Qwen/Qwen2.5-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct)
- JuStRank (most credible judge benchmark for 2025): [arXiv:2412.09569](https://arxiv.org/abs/2412.09569), ACL 2025
- JudgeBench: [arXiv:2410.12784](https://arxiv.org/abs/2410.12784), ICLR 2025
- JETTS: [arXiv:2504.15253](https://arxiv.org/pdf/2504.15253), ICML 2025

## Base model + size

| Model | Parameters |
|-------|-----------|
| Llama-3.1-70B-Instruct | 70B |
| Qwen2.5-72B-Instruct | 72B |

**Smaller same-family siblings** (relevant if we're constrained to 24 GB VRAM):
- Llama-3.1-8B-Instruct — 8B
- Qwen2.5-14B-Instruct — 14B (closest to our 24 GB fit)
- Qwen2.5-7B-Instruct — 7B

## Training data / method

**N/A** — these are general-purpose instruction-tuned LLMs, not specifically trained to be judges. We are using them "as-is" with carefully engineered judge prompts.

This is exactly analogous to what our current pipeline does with Claude Sonnet, just swapped to an open-source model.

## License

- **Llama-3.1**: Llama 3.1 Community License — commercial use permitted under 700M MAU, with use-case restrictions. [Source: HF model card].
- **Qwen2.5-72B**: Qwen Community License — commercial use permitted. (Apache-2.0 for smaller ≤3B variants; 7B/14B are Qwen Community License.)

**License confidence: HIGH.**

## Deployment profile

| Model | FP16 VRAM | Q4_K_M VRAM | Fits 24 GB single 4090? |
|-------|-----------|-------------|--------------------------|
| Llama-3.1-70B | ~140 GB | ~40 GB | **No** — needs 2× 4090 or A100/H100 |
| **Qwen2.5-72B** | ~144 GB | **~45 GB** | **No** — needs 2× 4090, A100 80GB, or H100 |
| Qwen2.5-14B-Instruct | ~28 GB | ~10 GB | Yes at Q4/Q5 |
| Qwen2.5-7B-Instruct | ~14 GB | ~5 GB | Yes |
| Llama-3.1-8B-Instruct | ~16 GB | ~5 GB | Yes |

[Source for Qwen2.5-72B VRAM: nodepedia.com/models/qwen2-5-72b].

**Cloud cost for 70B/72B judges** (rough): L40S 48GB at ~$0.19/hr runs Q4_K_M. 1,770 judge calls × ~5 sec/call ≈ 2.5 hrs ≈ $0.48. Very affordable if multi-GPU or cloud is in scope.

## Reported reliability numbers

### JuStRank (ACL 2025 — the most credible system-ranking judge benchmark)

Top 10 judges by Kendall's Tau agreement with human ranking (from Table 1 of arXiv:2412.09569):

| Rank | Judge | Realization | Agreement τ |
|------|-------|-------------|-------------|
| 1 | **Qwen2.5-72B-Instruct** | Likert, Win-Rate aggregation | **0.827** |
| 2 | Qwen2.5-72B-Instruct | Likert, Bradley-Terry | 0.817 |
| 3 | Qwen2.5-72B-Instruct | Numeric, BT | 0.814 |
| 4 | Qwen2.5-72B-Instruct | Numeric, Win-Rate | 0.813 |
| 5 | Qwen2.5-72B-Instruct | Likert, Mean | 0.801 |

Qwen2.5-72B-Instruct dominates the JuStRank leaderboard across all aggregation strategies. Llama-3.1-70B-Instruct is also in the top-15 but below Qwen.

**This is a very strong signal: Qwen2.5-72B prompted as a judge beats Llama-3.1-70B and is competitive with much larger/more expensive closed judges in system-ranking.**

**Confidence: HIGH** — ACL 2025 peer-reviewed benchmark, 48 judges evaluated.

### JudgeBench (ICLR 2025)

Primary prompted judges (Table 4, arXiv:2410.12784):

| Model | Knowledge | Reasoning | Math | Coding | Overall |
|-------|-----------|-----------|------|--------|---------|
| Llama-3.1-405B-Instruct | 55.84 | 54.08 | 69.64 | 50.00 | 56.86 |
| Llama-3.1-70B-Instruct | 51.30 | 48.98 | 60.71 | 52.38 | 52.29 |
| Llama-3.1-8B-Instruct | (not detailed) | (not detailed) | ~ | ~ | ~37 |

Qwen2.5-72B not explicitly in the JudgeBench table I verified, but **IF-RewardBench (arXiv 2603.04738v2)** reports Qwen2.5-72B-Instruct τ_b = 0.052 at constraint assessment without guidance and 0.840 with guidance — slightly weaker than JuStRank numbers but in a different setting.

**Confidence: HIGH** for JudgeBench numbers.

### RewardBench 2 (2025)

Llama-3.1-70B-Instruct-RM-RB2 (a fine-tuned reward model, not the vanilla instruct): **76.1 overall, Factuality 81.3, Safety 88.4**. Vanilla instruct is weaker. **Confidence: HIGH** — AllenAI paper arXiv:2506.01937.

### JETTS (ICML 2025)

Llama-3.1-70B-Instruct scores roughly at "greedy" baseline level on response reranking — i.e., vanilla prompted judges are outperformed by dedicated judges (Skywork-Critic, SFR-Judge) on test-time scaling tasks. **Confidence: HIGH** — primary paper.

## Reference-aware scoring support

**Yes — trivially.** Any instruction-tuned LLM supports arbitrary prompt formats. We would construct the prompt exactly like our current Claude pipeline:

```
System: You are a judge. Score from 0-3 on each of 5 dimensions.
User: Question: {q}. Reference: {ref}. Response: {r}. Rubric: {rubric}. Output JSON.
```

## Instance-rubric support

**Yes — trivially.** Users can inject any rubric descriptor format into the prompt. This is the same flexibility Claude offers today.

**Critical observation**: prompted generalist judges have **the same rubric flexibility as our current Claude judge**. The only difference is reasoning depth.

## Cybersecurity / regulatory / compliance fit

**Qwen2.5-72B-Instruct**:
- MMLU ~84%, MMLU-Pro ~51% (per published results and reproductions on tenstorrent/tt-inference-server).
- GPQA-Diamond: ~49%.
- Strong on knowledge-heavy tasks. Top of the non-proprietary open models on many benchmarks.
- In the CompassJudger-2 paper (arXiv:2507.09104), Qwen2.5-72B-Instruct is used as the base for judge-data synthesis and verification — which is a strong implicit endorsement for its reasoning quality.

**Llama-3.1-70B-Instruct**:
- MMLU ~82%, MMLU-Pro ~52%.
- Strong general reasoning.

**Confidence: HIGH** — published benchmarks across multiple independent evaluations.

**Neither has been benchmarked on a cybersecurity/regulatory judge task specifically.** The closest proxies are general reasoning (Qwen2.5 slightly ahead) and instruction following (Llama-3.1 slightly ahead).

## Known failure modes

- **No dedicated judge training**: vanilla instruct models can exhibit positive/negative bias towards certain systems (JuStRank §5 documents this).
- **Position bias**: not benchmarked specifically; probably exists at similar level to Claude.
- **Consistency across repeat calls**: temp=0.2 + seed pinning required, as with any LLM judge.
- **VRAM: 70B-class requires multi-GPU or cloud**.

## Ease of integration

- HuggingFace transformers: trivial.
- vLLM: trivial and recommended for serving the 70B/72B.
- Ollama: first-party Llama-3.1 and Qwen2.5 GGUFs available (`ollama pull qwen2.5:72b`, `ollama pull llama3.1:70b`). **This is the easiest path.**
- Smaller variants (Qwen2.5-14B, Llama-3.1-8B): trivially fit on single 4090 at high quality.

**Integration effort: ~2-4 hours** (swap our existing Claude-CLI subprocess call for an Ollama API call pointing at `qwen2.5:72b` or `llama3.1:70b`).

## Recommendation summary

- **Strength**: State-of-the-art reasoning; Qwen2.5-72B leads JuStRank; trivially integrates with existing pipeline (just swap the API); same rubric/reference flexibility as Claude.
- **Weakness for us**: 70B/72B variants need cloud or multi-GPU — not single 4090. Smaller variants (Qwen2.5-14B, Llama-3.1-8B) are **single-4090-compatible** and usable as prompted judges, but their judge reliability is less-benchmarked than the 70B counterparts.
- **Verdict**:
  - If multi-GPU or cloud budget exists: **Qwen2.5-72B-Instruct is the strongest prompted-judge pick** (JuStRank winner; trivial integration via Ollama).
  - On single 4090 only: **Qwen2.5-14B-Instruct as a prompted judge is a reasonable lower-cost option** — but M-Prometheus-14B (Qwen2.5-14B fine-tuned as a judge) is **strictly better** in most cases.

## Sources used (all verified accessible 2026-04-24)

- [huggingface.co/meta-llama/Meta-Llama-3.1-70B-Instruct](https://huggingface.co/meta-llama/Meta-Llama-3.1-70B-Instruct)
- [huggingface.co/Qwen/Qwen2.5-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct)
- [huggingface.co/Qwen/Qwen2.5-72B-Instruct-GGUF](https://api-inference.hf-mirror.com/Qwen/Qwen2.5-72B-Instruct-GGUF)
- [JuStRank (arXiv:2412.09569)](https://arxiv.org/abs/2412.09569)
- [JuStRank PDF (aclanthology)](https://aclanthology.org/2025.acl-long.34.pdf)
- [JudgeBench (arXiv:2410.12784)](https://arxiv.org/abs/2410.12784)
- [JETTS (arXiv:2504.15253)](https://arxiv.org/pdf/2504.15253)
- [RewardBench 2 (arXiv:2506.01937)](https://arxiv.org/abs/2506.01937)
- [nodepedia Qwen2.5-72B VRAM estimates](https://nodepedia.com/models/qwen2-5-72b/)
