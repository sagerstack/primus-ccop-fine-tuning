# Landscape comparison — open-source judges vs our requirements

**Scope note**: Renamed from `20-landscape-comparison.md`. Complement to the 11 individual candidate files (11-20). The table below is the single artifact meant to anchor the recommendation.

## Comparison table

Columns: Model | Base | License | VRAM (Q4) | Pearson / agreement vs human (reported) | Reference-aware | Instance-rubric | Cybersec eval exists? | Ease of integration

| Model | Base | License | VRAM (Q4) | Reported reliability vs human | Reference-aware | Instance-rubric | Cybersec eval? | Ease of integration |
|-------|------|---------|-----------|--------------------------------|-----------------|-----------------|----------------|---------------------|
| **Prometheus-2-7B** | Mistral-7B-Instruct | Apache-2.0 (model); OpenAI ToU (training data) | ~5 GB | Pearson 0.784 on Feedback-Bench; 0.476 on MT-Bench [paper] | **Yes — first-class** | **Yes — first-class 5-level anchored** | No | Trivial (pip package) |
| **Prometheus-2-8x7B** | Mixtral-8x7B-Instruct | Apache-2.0 | ~26 GB | Pearson 0.800 on Feedback-Bench; 0.515 on MT-Bench [paper] | Yes | Yes | No | Trivial but tight on 24 GB |
| **Prometheus-2-BGB-8x7B** | Continued from 8x7B on BiGGen-Bench | Apache-2.0 | ~26 GB | Claim: "surpasses Claude-3-Opus on absolute grading" [author repo] | Yes | Yes | No | Trivial but tight on 24 GB |
| **M-Prometheus-7B** | Qwen2.5-7B-Instruct | Apache-2.0 derived (Qwen2.5) | ~5 GB | SOTA on 20+ non-English languages; English at-par-with Prometheus-2-7B [paper Appendix] | Yes | Yes | No | Trivial |
| **M-Prometheus-14B** | **Qwen2.5-14B-Instruct** | **Qwen Community** | **~10 GB** | Best multilingual judge 3B-14B; English better base-MMLU than Prometheus-2-7B [paper] | **Yes** | **Yes** | **No** | **Trivial** |
| **JudgeLM-7B** | Vicuna-7B-v1.3 | LLaMA-2 Community (research-safe) | ~4 GB | 81% agreement w/ GPT-4 on JudgeLM test [paper] | Yes (reference support) | No | No | Standard HF |
| **JudgeLM-13B** | Vicuna-13B-v1.3 | LLaMA-2 Community | ~8 GB | 84% agreement w/ GPT-4 [paper] | Yes | No | No | Standard HF |
| **JudgeLM-33B** | Vicuna-33B-v1.3 | LLaMA-1 (research) | ~20 GB (tight) | 89% agreement w/ GPT-4 [paper]; JudgeBench overall 35.71 | Yes | No | No | Standard HF |
| **PandaLM-7B** | LLaMA-1 | Research-only (LLaMA-1) | ~4 GB | 88% of GPT-4 F1 on PandaLM test [paper, ratio not absolute] | Yes | **No (fixed dimensions)** | No | Standard HF |
| **Auto-J (13B)** | LLaMA-2-13B-Chat | LLaMA-2 Community | ~8 GB | 73.7 single-rating agreement in-dist [paper]; Pearson 0.282 VicunaBench [Prom2 paper] | Partial | **Scenario-level only (58 pre-baked)** | No | Standard HF; authors ship GPTQ-4bits |
| **Self-Taught Evaluator 70B** | Llama-3.1-70B-Instruct | **Research-only (gated)** | ~40 GB (needs multi-GPU) | RewardBench 88.3 (88.7 w/ MV) [paper] | Partial | No | No | HF (manual gate) |
| **Skywork-Critic-8B** | Llama-3.1-8B-Instruct | Skywork Community (commercial-OK) | ~5 GB | RewardBench 89.0; authors flag 8B as unreliable | Partial | No | No | Standard HF + GGUF available |
| **Skywork-Critic-70B** | Llama-3.1-70B-Instruct | Skywork Community | ~40 GB (needs multi-GPU) | **RewardBench 93.3 (top-1 generative)** [model card]; JudgeBench 57.43 | Partial | No | No | Standard HF |
| **SFR-Judge-8B** | Llama-3.1-8B-Instruct | Llama-3.1 Community (gated HF) | ~5 GB | RewardBench 88.7; JudgeBench 80.91 pairwise [paper] | **Yes — first-class single-rating** | Partial (classification mode) | No | HF + SFRJudge repo |
| **SFR-Judge-12B** | Mistral NeMo 12B | Mistral research | ~8 GB | RewardBench 90.3 [model card] | Yes | Partial | No | HF |
| **SFR-Judge-70B** | Llama-3.1-70B-Instruct | Llama-3.1 Community | ~40 GB (needs multi-GPU) | **RewardBench 92.7; top-1 Reasoning (97.6)** [paper]; pairwise 84.25 [paper] | Yes | Partial | No | HF |
| **Llama-3.1-70B-Instruct (prompted)** | — | Llama-3.1 Community | ~40 GB (needs multi-GPU) | JuStRank top-15; JudgeBench 52.29 [JudgeBench paper] | Yes (prompt) | Yes (prompt) | No | Ollama one-liner |
| **Qwen2.5-72B-Instruct (prompted)** | — | Qwen Community | **~45 GB (needs multi-GPU)** | **JuStRank τ=0.827 #1** [ACL 2025 paper] | Yes (prompt) | Yes (prompt) | No | Ollama one-liner |
| **Qwen2.5-14B-Instruct (prompted)** | — | Qwen Community | ~10 GB | Less benchmarked as judge; base MMLU ~80 | Yes (prompt) | Yes (prompt) | No | Ollama one-liner |
| **JudgeLRM-3B** | Qwen2.5-3B-Instruct | Research-only (paper) | ~2 GB | PandaLM F1 > GPT-4 [paper abstract] | Yes | Partial | **Yes — chosen by CA-Judge AAAI 2025 paper** (indirect) | Standard HF |
| **JudgeLRM-7B** | Qwen2.5-7B-Instruct | Research-only | ~5 GB | PandaLM F1 > DeepSeek-R1 + 2pp [paper abstract] | Yes | Partial | **Yes — used as CA-Judge in compliance paper** | Standard HF |
| **JudgeLRM-14B** | Qwen2.5-14B-Instruct | Research-only | ~10 GB | Paper claims strongest reasoning-heavy gains [paper] | Yes | Partial | Yes (indirect) | Standard HF |
| **CompassJudger-2-7B** | Qwen2.5-7B-Instruct | Qwen Community + Apache (code) | ~5 GB | Claimed competitive with DeepSeek-V3, Qwen3-235B [paper abstract] | Yes | Partial | No | OpenCompass or HF |
| **CompassJudger-2-32B** | Qwen2.5-32B-Instruct | Qwen Community | ~20 GB (tight) | Tops JudgerBenchV2 at its size tier | Yes | Partial | No | OpenCompass or HF |

## Fit for our 5-dim instance-rubric requirement (ranked)

Filtering for judges that support **both**: (a) per-instance anchored rubric descriptors, and (b) reference-answer first-class slot, we get a clear shortlist:

| Rank | Candidate | Why top |
|------|-----------|---------|
| 1 | **M-Prometheus-14B** | Prometheus 2 recipe on Qwen2.5-14B-Instruct — strictly better base than Prometheus-2-7B; fits 24 GB at Q4/Q5 with headroom; first-class rubric + reference; Apache-based license |
| 2 | **Prometheus-2-7B** | The workhorse. Proven, cited, integrated in prometheus-eval library; Apache-2.0 |
| 3 | **Qwen2.5-14B-Instruct as prompted judge** | No fine-tuning but equal prompt flexibility, strong MMLU ~80; easy ollama integration; Qwen Community License |
| 4 | **JudgeLRM-7B** | Strong external validation (AAAI 2025 CA-Judge compliance paper); but research-only license; partial rubric support |

## Judges that fit 24 GB but don't support instance rubrics

Valuable as **cross-family secondary judges** or for pairwise-only protocols:

- JudgeLM-7B / 13B — good for position-bias diagnostics
- Skywork-Critic-8B — but authors disclaim quality
- SFR-Judge-8B / 12B — strong reasoning, single-rating trained
- CompassJudger-2-7B — dark-horse; worth a pilot

## Judges that don't fit 24 GB on single 4090

- Self-Taught Evaluator 70B (also research-only)
- Skywork-Critic-70B
- SFR-Judge-70B
- Llama-3.1-70B-Instruct (prompted)
- Qwen2.5-72B-Instruct (prompted)

**All of the above require multi-GPU (2× 4090 for Q4) or cloud (A100/H100 or L40S).** If the dissertation pilot expands to cloud, Qwen2.5-72B-Instruct and SFR-Judge-70B are the strongest picks — the former for prompt-flexibility, the latter for rubric-fitness.

## Credible shared benchmarks (for cross-judge comparison in our dissertation)

| Benchmark | Focus | Why credible |
|-----------|-------|--------------|
| **JudgeBench** (ICLR 2025, arXiv:2410.12784) | Reasoning, knowledge, math, coding | Peer-reviewed ICLR 2025; objective correctness labels; includes both prompted and fine-tuned judges |
| **RewardBench v1/v2** (AllenAI) | Chat, Safety, Reasoning, Factuality | Most-cited single benchmark for reward-model + judge quality |
| **JuStRank** (ACL 2025, arXiv:2412.09569) | System-ranking ability | Unique angle: not instance-level, but does this judge produce correct *model rankings*? |
| **JETTS** (ICML 2025, arXiv:2504.15253) | Test-time scaling scenarios | Relevant if we use judges for self-improvement loops |
| **ContextualJudgeBench** (ACL 2025, arXiv:2503.15620) | RAG / contextual faithfulness | Most relevant for our RAG-grounded compliance QA; o1 barely reaches 55% accuracy |

**For our dissertation defense**: JudgeBench is the single benchmark we should cite when comparing judges. It tests reasoning-heavy regimes (closest proxy to compliance reasoning). RewardBench is also citeable but is becoming saturated. ContextualJudgeBench is the most methodologically aligned but newer and less-canonical.

## Headline findings from this table

1. **Only Prometheus-family judges natively support instance-specific anchored rubrics** (our hard requirement #2). M-Prometheus-14B is the best-in-class open-source candidate for our exact architectural pattern.
2. **Qwen2.5-family backbones dominate the 2025 judge landscape**: M-Prometheus (3B/7B/14B), JudgeLRM (3B/7B/14B), CompassJudger-2 (7B/32B) all build on Qwen2.5. This is not coincidence — Qwen2.5 reasoning quality is top of the open-source tier.
3. **Reference-aware is universal across modern judges**; the *instance rubric* is the genuinely differentiating requirement.
4. **70B-class judges strictly exceed 7B-14B on most benchmarks** but are not feasible on a single 4090. Multi-GPU or cloud unlocks Qwen2.5-72B as the best prompted judge and SFR-Judge-70B as the best fine-tuned judge.
5. **No cybersecurity-specific open-source judge exists**. The closest is JudgeLRM via the CA-Judge compliance precedent (AAAI 2025 paper).
