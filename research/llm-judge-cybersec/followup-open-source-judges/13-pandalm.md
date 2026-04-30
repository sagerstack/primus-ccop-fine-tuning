# PandaLM (Wang et al., arXiv:2306.05087)

**Category**: Academic fine-tuned evaluator LM, Llama-based
**Canonical sources**:
- Paper: [arXiv:2306.05087](https://arxiv.org/abs/2306.05087) (v2 May 2024)
- GitHub: [WeOpenML/PandaLM](https://github.com/WeOpenML/PandaLM)
- HF paper page: [huggingface.co/papers/2306.05087](https://huggingface.co/papers/2306.05087)

## Base model + size

| Variant | Base | Parameters |
|---------|------|-----------|
| PandaLM-7B | LLaMA-7B | 7B |
| PandaLM-13B | LLaMA-13B | 13B |
| PandaLM-70B | LLaMA-2-70B | 70B (released later in paper's v2) |

## Training data / method

- Training data: 300K instruction-tuning samples of responses from LLaMA-7B, OPT-7B, and Pythia-6.9B across Alpaca-52K instructions.
- Each sample contains a reference answer, candidate responses, and a GPT-3.5 (or GPT-4 in v2) preference judgment.
- **Objective**: Fine-tune to predict which of two candidate responses is better, with rationale. Includes a reference answer and rationale generation.
- Training signal: GPT-3.5 for the original data collection; GPT-4-refined for the 70B variant.

## License

- Weights for 7B and 13B: **Apache 2.0** per GitHub repo, but based on LLaMA-1, which requires researcher access under Meta's original LLaMA license. Effective status: **research-only** for the underlying weights.
- Weights for 70B: Llama-2-based, so Llama-2 Community License (commercial-use permitted under 700M MAU).
- Training data: not redistributed for commercial use due to the ShareGPT/Alpaca derivation.
- Code: Apache 2.0.

**License confidence: MEDIUM-LOW**. LLaMA-1-based PandaLM-7B/13B are effectively research-only. PandaLM-70B (Llama-2) is commercially usable but is not strictly needed if you're using a 70B anyway — newer judges like Skywork-Critic-70B or SFR-Judge-70B are better.

## Deployment profile

| Variant | FP16 VRAM | Q4 VRAM | Fits 24 GB? |
|---------|-----------|---------|-------------|
| PandaLM-7B | ~14 GB | ~4 GB | Yes |
| PandaLM-13B | ~26 GB | ~8 GB | Yes at Q4 |
| PandaLM-70B | ~140 GB | ~40 GB | No |

Integration: standard HuggingFace transformers. The repo provides a web UI (`serve_demo.py`) and a CLI inference script.

## Reported reliability numbers

**Primary paper (arXiv:2306.05087 v1/v2, Table 3-4):**

| Model | F1 vs human on PandaLM test set |
|-------|-------------------------------|
| PandaLM-7B | 88.28% (reported as "88.28% of GPT-4's F1") |
| PandaLM-70B (v2 update) | Surpasses GPT-4 |
| GPT-3.5 (reference) | ~baseline |
| GPT-4 | ~reference ceiling |

The claim "PandaLM-7B achieves 93.75% of GPT-3.5's evaluation ability and 88.28% of GPT-4's" is a **ratio-of-F1-scores**, not absolute F1. Absolute F1 is ~0.64 for PandaLM-7B vs GPT-4's ~0.73 on the PandaLM-authored test set.

**Confidence: MEDIUM-HIGH** for the F1 ratio claim (authors' primary test set); **MEDIUM** for the 70B "surpasses GPT-4" claim (only reported in v2, no third-party replication).

**JudgeBench result**: PandaLM appears in the JudgeBench paper's baseline comparison (arXiv:2410.12784 Table 4). Scores:

| Variant | Knowledge | Reasoning | Math | Coding | Overall |
|---------|-----------|-----------|------|--------|---------|
| PandaLM (7B, implied from context) | ~30 | ~30 | ~30 | ~15 | ~27 |

(Approximate — the exact row I could not fully verify in the highlight data. Treat with MEDIUM-LOW confidence; double-check the JudgeBench paper Table 4 directly before citing.)

## Reference-aware scoring support

**Yes.** PandaLM's input format includes a "reference response" field. However, the reference is treated as one candidate, not as a gold anchor. The paper does not benchmark "reference-aware vs reference-free" — reference support is implicit.

## Instance-rubric support

**No.** PandaLM evaluates along fixed implicit dimensions: conciseness, clarity, adherence to instructions, comprehensiveness, formality. Users cannot inject per-case rubric descriptors. This is a **hard miss** for our requirement.

## Cybersecurity / regulatory / compliance fit

- **No cybersecurity benchmarks** in PandaLM papers.
- Base model (LLaMA-1-7B/13B) has MMLU ~35-47%, *substantially weaker* than Qwen2.5-14B (~80%) or even Llama-3-8B (~68%). **This is 2023-era reasoning capacity.**
- PandaLM is now primarily cited as a **baseline** (e.g., by JudgeLM, Prometheus 2, SFR-Judge).

## Known failure modes

- **Preference for longer responses** (paper §4.3): PandaLM has measurable length bias.
- **Position bias**: the paper reports a 2-5% consistency gap on swapped positions.
- **Fixed subjective criteria**: the "conciseness, clarity, ..." dimensions are baked in — cannot be reweighted or replaced.
- **Outdated base model**: LLaMA-1 has been superseded multiple generations over. The reasoning ceiling is well below current-gen judges.

## Ease of integration

- HuggingFace transformers: standard.
- No vLLM-specific script from authors, but works with vLLM generically.
- Python library: `pip install pandalm` installs a small wrapper.
- Ollama: no first-party GGUF; community ones exist for 7B only.

## Recommendation summary

- **Strength**: Early judge, human-annotated test set, low VRAM.
- **Weakness for us**: No instance rubric; outdated base model; no cybersecurity benchmarking; fixed subjective criteria.
- **Verdict**: Historical interest only. **Do not deploy as a secondary judge for our pipeline** — the base-model reasoning is too weak compared to Qwen2.5/Llama-3 alternatives.

## Sources used (all verified accessible 2026-04-24)

- [arXiv:2306.05087](https://arxiv.org/abs/2306.05087) (paper, v2)
- [github.com/WeOpenML/PandaLM](https://github.com/WeOpenML/PandaLM)
- [huggingface.co/papers/2306.05087](https://huggingface.co/papers/2306.05087)
- [JudgeBench paper (arXiv:2410.12784)](https://arxiv.org/abs/2410.12784) for PandaLM comparative scores
