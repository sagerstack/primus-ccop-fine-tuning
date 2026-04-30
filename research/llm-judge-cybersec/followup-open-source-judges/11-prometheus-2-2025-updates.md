# Prometheus 2 ecosystem — 2025 updates & M-Prometheus

**Category**: Academic fine-tuned evaluator LM (successor ecosystem to `12-prometheus-2.md`)
**Canonical sources**:
- Original paper: [Prometheus 2 — arXiv:2405.01535](https://arxiv.org/abs/2405.01535) (EMNLP 2024)
- M-Prometheus paper: [Pombal et al. 2025 — arXiv:2504.04953](https://arxiv.org/pdf/2504.04953)
- Prometheus-eval GitHub: [prometheus-eval/prometheus-eval](https://github.com/prometheus-eval/prometheus-eval)
- BiGGen-Bench + Prometheus 2 BGB release (June 2024): same repo, `BiGGen-Bench/` subfolder
- M-Prometheus 7B HF card: [Unbabel/M-Prometheus-7B](https://huggingface.co/Unbabel/M-Prometheus-7B)
- M-Prometheus 14B HF card: [Unbabel/M-Prometheus-14B](https://huggingface.co/Unbabel/M-Prometheus-14B)

## Why this file exists

The main research's `12-prometheus-2.md` covered the May-2024 Prometheus 2 paper. Since then, two concrete successor releases happened that change the deployment calculus:

1. **Prometheus 2 BGB (8x7B)** — a continually-trained Prometheus 2 (Mixtral) on the BiGGen-Bench evaluation corpus. Reportedly surpasses Claude-3-Opus on absolute grading. [prometheus-bgb-8x7b-v2.0 on HF](https://huggingface.co/prometheus-eval/prometheus-bgb-8x7b-v2.0).
2. **M-Prometheus (3B / 7B / 14B)** — multilingual reproduction of the Prometheus 2 recipe using **Qwen2.5-Instruct** backbones. Apache-2.0-compatible (Qwen2.5 license) and explicitly trained with the same direct-assessment + pairwise weight-merged format. This is the most important 2025 Prometheus update for our use case because **14B fits in 24 GB VRAM at Q4**.

There is **NO Prometheus 3 paper or weights** as of 2026-04-24. "Prometheus-Mini" does not exist as a separate model — the 7B variant of Prometheus 2 already fills that role.

## Base model + size

| Variant | Base | Parameters | Release |
|---------|------|-----------|---------|
| Prometheus-2-7B | Mistral-7B-Instruct | 7B | May 2024 |
| Prometheus-2-8x7B | Mixtral-8x7B-Instruct | 46.7B total, 12.9B active | May 2024 |
| Prometheus-2-BGB-8x7B | Continual train from Prometheus-2-8x7B on BiGGen-Bench | 46.7B total | June 2024 |
| M-Prometheus-3B | Qwen2.5-3B-Instruct | 3B | April 2025 |
| M-Prometheus-7B | Qwen2.5-7B-Instruct | 7B | April 2025 |
| **M-Prometheus-14B** | **Qwen2.5-14B-Instruct** | **14B** | **April 2025** |

## Training data / method

- **Prometheus 2**: Feedback Collection (100K direct-assessment) + Preference Collection (200K pairwise). Two models trained separately, then **weight-merged** into one evaluator supporting both formats.
- **M-Prometheus**: 480K instances of multilingual direct-assessment and pairwise data with long-form feedback. Uses **synthetic multilingual data** (not translations — the paper ablates and finds translated data ineffective). Same weight-merge trick.
- All variants retain the instance-specific rubric design: each training instance has its OWN 5-level score descriptors (not a universal rubric).

## License

- **Prometheus 2 (7B, 8x7B, BGB)**: Apache-2.0 per paper Appendix D and GitHub repo. Dataset (Feedback/Preference Collection) is subject to OpenAI's Terms of Use for generated data (research purposes only for the dataset; the model itself is commercially usable). [Source: arxiv.org/html/2405.01535v2 Appendix D].
- **M-Prometheus**: Inherits **Qwen2.5 license** (Apache-2.0-based community license for Qwen2.5-14B; ≤3B variants are strictly Apache-2.0). Commercial use is permitted without a paid tier for deployments under 100M monthly active users (Qwen2.5 license terms). [Source: huggingface.co/Qwen/Qwen2.5-14B/blob/main/LICENSE].

**License confidence: HIGH.** Both licenses are unambiguous and verified from primary model-card sources.

## Deployment profile

| Variant | FP16 VRAM | Q4_K_M VRAM | Fits 24 GB (RTX 4090)? | Tokens/sec on 4090 (estimate) |
|---------|-----------|-------------|------------------------|-------------------------------|
| Prometheus-2-7B | ~14 GB | ~5 GB | Yes, easily | ~50-80 tok/s via vLLM |
| Prometheus-2-8x7B | ~90 GB | ~26 GB | No (Q4 marginally over 24 GB) | N/A on single 4090 |
| Prometheus-2-BGB-8x7B | ~90 GB | ~26 GB | No | N/A on single 4090 |
| M-Prometheus-3B | ~6 GB | ~2 GB | Yes | ~120+ tok/s |
| M-Prometheus-7B | ~14 GB | ~5 GB | Yes | ~50-80 tok/s |
| **M-Prometheus-14B** | **~28 GB** | **~10 GB** | **Yes at Q4 or Q5** | **~30-50 tok/s** |

Integration: `prometheus-eval` Python package wraps vLLM and HuggingFace TGI. `transformers.AutoModelForCausalLM.from_pretrained("prometheus-eval/prometheus-7b-v2.0")` works out of the box. Also `litellm` compatible.

## Reported reliability numbers

**Primary paper numbers (arXiv:2405.01535, Tables 2 and 4 in v2 HTML; verified):**

Direct assessment Pearson with human:

| Model | VicunaBench | MT-Bench | FLASK | Feedback-Bench |
|-------|-------------|----------|-------|----------------|
| Prometheus-2-7B | 0.543 | 0.476 | 0.390 | 0.784 |
| Prometheus-2-8x7B | 0.559 | 0.515 | 0.535 | 0.800 |
| GPT-4-1106 | / | 0.553 | / | 0.662 |
| Claude-3-Opus | 0.553 | / | 0.609 | 0.693 |
| Prometheus-1-13B (predecessor) | 0.405 | 0.425 | 0.290 | 0.770 |

**Confidence: HIGH** — primary paper, ACL-published version.

**BiGGen-Bench (BGB-8x7B) claims**: "Even surpassing Claude-3-Opus on absolute grading tasks." Verified from the prometheus-eval repo BiGGen-Bench README. **Confidence: MEDIUM-HIGH** — claim from authors' own repo and paper, not independently replicated in a third-party benchmark at the time of writing.

**M-Prometheus**: "State-of-the-art on more than 20 non-English languages" — primary paper claim. Not directly comparable to Prometheus 2 on English benchmarks in our regime (CCoP is English-only), so the multilingual gain is irrelevant for us; what matters is the **Qwen2.5-based English baseline is at least on par with Mistral-based Prometheus 2**. The M-Prometheus paper ablation (Appendix) shows English performance does not regress vs Prometheus 2. **Confidence: MEDIUM** — primary paper, small English-only ablation table.

**JudgeBench (ICLR 2025, arXiv:2410.12784)** result for Prometheus-2-BGB-8x7B on JudgeBench:

| Category | Score |
|----------|-------|
| Knowledge | 45.45 |
| Reasoning | 30.61 |
| Math | 46.43 |
| Coding | 28.57 |
| **Overall** | **39.43** |

For context, GPT-4o scores 56.57% overall on the same split (JudgeBench paper Table 4). Prometheus-2 is weaker on hard reasoning than the best API judges. **Confidence: HIGH** — JudgeBench paper primary source.

## Reference-aware scoring support

**Yes — first-class.** Prometheus 2's prompt template requires four fields: `{instruction, response, reference_answer, rubric}`. Our pipeline's `{question, response, expected_response, rubric}` maps 1:1. This is a critical fit.

## Instance-rubric support

**Yes — central to the design.** The training dataset was built explicitly around per-instance 5-level score descriptors. The prometheus-eval package exposes `score_rubric_template(criteria_description, score_descriptions)` where `score_descriptions` is a list of 5 strings — the user's instance rubric.

## Cybersecurity / regulatory / compliance fit

- **No direct cybersecurity benchmarks** in the Prometheus 2 or M-Prometheus papers.
- Proxy indicators: Prometheus 2 scored well on FLASK's "Logical Correctness" and "Factuality" dimensions (Pearson 0.475 for 7B on FLASK Factuality, Table 3 in v2). These map loosely to our D2/D3.
- Base-model strength on MMLU security-adjacent subsets: Mistral-7B-Instruct MMLU ~60%; Qwen2.5-14B-Instruct MMLU ~80%. **M-Prometheus-14B has a clear base-model reasoning advantage** over Prometheus-2-7B for security-domain reasoning.
- CA-Judge compliance paper (AAAI 2025, Chen et al., doi ojs.aaai.org/index.php/AAAI/article/view/41298) chose JudgeLRM-7B as its base for compliance-alignment evaluation — i.e., another Qwen2.5-7B-based judge. This is suggestive that the Qwen2.5 family is a defensible backbone for regulatory compliance QA.

**Confidence: MEDIUM** — no direct cybersecurity judge benchmark exists for these models, but backbone quality and proxy MMLU support using M-Prometheus-14B for our task.

## Known failure modes

- Position bias in pairwise mode remains (paper §6.2, v2).
- Self-preference for Mistral-family responses (paper §6.3) — for Prometheus 2. M-Prometheus uses Qwen2.5, so the bias would shift to preferring Qwen-family responses — important if we test Qwen models in the future.
- **Reference-answer dependency is load-bearing** for the 7B variant: without a reference answer, agreement drops significantly (paper §4.4 ablation; the 7B variant underperforms GPT-4 in that regime). For our pipeline this is NOT a failure mode — we always provide the reference.
- On JudgeBench, Prometheus-2-BGB-8x7B underperforms Skywork-Critic-70B by ~18 points overall. On hard reasoning specifically, it's ~24 points below. For CCoP, where most cases are regulatory reasoning, this is a weakness to note.

## Ease of integration

- HuggingFace transformers: **trivial**. `AutoModelForCausalLM.from_pretrained("prometheus-eval/prometheus-7b-v2.0")` loads and runs.
- vLLM: **trivial**. The `prometheus-eval` Python package includes vLLM wrappers.
- Ollama: Not officially published by the authors, but Q4/Q5 GGUF conversions of Prometheus-2-7B exist on HF (community uploads). For M-Prometheus-14B, GGUF quantizations are listed under `Unbabel/M-Prometheus-14B`'s "Quantizations" tab (5 models listed as of April 2025).
- Python library: `pip install prometheus-eval` — wraps both absolute and pairwise grading with a single `PrometheusEval(model=...).single_absolute_grade(...)` API.

**Integration effort for our pipeline: ~1 day** to wire M-Prometheus-14B Q4 into `LLMJudgeService` as a secondary judge alongside Claude.

## Concrete borrowable patterns (beyond what main research captured)

1. **M-Prometheus-14B on Qwen2.5-14B-Instruct is the best fit for our 24 GB constraint among Prometheus-family judges** — strictly better base-model reasoning than Prometheus-2-7B while still fitting a single 4090 at Q4/Q5.
2. **BiGGen-Bench training recipe**: for a future fine-tuned CCoP judge, BiGGen-Bench's "continual training on a diverse evaluation corpus" recipe is the proven path. Our 118 cases would need expansion to ~5-10K synthetic-rubric training examples.
3. **Qwen2.5 license is less restrictive than Llama community license for commercial deployment** — relevant if the dissertation pilot transitions to production.

## Sources used (all verified accessible 2026-04-24)

- [arXiv:2405.01535](https://arxiv.org/abs/2405.01535) (Prometheus 2 paper, v2 Dec-2024)
- [arXiv:2504.04953](https://arxiv.org/pdf/2504.04953) (M-Prometheus paper)
- [prometheus-eval/prometheus-7b-v2.0](https://huggingface.co/prometheus-eval/prometheus-7b-v2.0) (HF model card, verified)
- [prometheus-eval/prometheus-bgb-8x7b-v2.0](https://huggingface.co/prometheus-eval/prometheus-bgb-8x7b-v2.0)
- [Unbabel/M-Prometheus-7B](https://huggingface.co/Unbabel/M-Prometheus-7B)
- [Unbabel/M-Prometheus-14B](https://huggingface.co/Unbabel/M-Prometheus-14B)
- [github.com/prometheus-eval/prometheus-eval](https://github.com/prometheus-eval/prometheus-eval)
- [Qwen/Qwen2.5-14B license](https://huggingface.co/Qwen/Qwen2.5-14B/blob/main/LICENSE)
- [JudgeBench paper](https://arxiv.org/abs/2410.12784) (ICLR 2025) Table 4 for Prometheus-2-BGB scores
