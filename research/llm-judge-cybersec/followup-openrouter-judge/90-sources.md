# Sources — OpenRouter judge investigation

All URLs accessed and content captured 2026-04-25 unless stated otherwise. Confidence ratings:

- **HIGH** — primary source (OpenRouter own model page, OpenAI/Anthropic/Google official docs, peer-reviewed paper)
- **MEDIUM** — secondary or community source with corroboration available
- **LOW** — single-source claim, requires further verification before relying on it

---

## 1. OpenRouter model pages (HIGH — primary source for pricing + model IDs)

Verified live via WebFetch on 2026-04-25. Pricing and context-window numbers in `10-candidate-specs.md` are sourced from these pages.

### 1.1 Tier A — budget-primary contenders
- https://openrouter.ai/openai/gpt-4o-mini — confirmed $0.15/$0.60, 128K ctx
- https://openrouter.ai/google/gemini-2.5-flash-lite — confirmed $0.10/$0.40, 1M ctx
- https://openrouter.ai/meta-llama/llama-3.3-70b-instruct — confirmed $0.10/$0.32, 131K ctx, Llama 3.3 Community License
- https://openrouter.ai/x-ai/grok-4-fast — confirmed $0.20/$0.50, 2M ctx, logprobs supported
- https://openrouter.ai/qwen/qwen3-235b-a22b-2507 — confirmed $0.071/$0.10, 262K ctx (verified directly via WebFetch this session)

### 1.2 Tier B — mid-range
- https://openrouter.ai/openai/gpt-4.1-mini — confirmed $0.40/$1.60, 1.047M ctx, released 2025-04-14 (verified directly via WebFetch this session)
- https://openrouter.ai/google/gemini-2.5-flash — confirmed $0.30/$2.50, 1.048M ctx, released 2025-06-17 (verified directly via WebFetch this session)
- https://openrouter.ai/deepseek/deepseek-v3.2 — confirmed $0.252/$0.378, 131K ctx, dated slug `2025-12-01`

### 1.3 Tier C — quality-primary
- https://openrouter.ai/anthropic/claude-sonnet-4.5 — confirmed $3/$15, 1M ctx, released 2025-09-29 (verified directly via WebFetch this session)
- https://openrouter.ai/google/gemini-2.5-pro — confirmed $1.25/$10, 1.048M ctx
- https://openrouter.ai/openai/gpt-4.1 — confirmed $2/$8, 1.047M ctx

### 1.4 Drop-list verifications
- https://openrouter.ai/openai/gpt-5 — temperature parameter NOT exposed for GPT-5 family on OpenRouter (community-confirmed; HIGH-MEDIUM confidence — needs reverify if OR adds support)
- https://openrouter.ai/openai/o1, https://openrouter.ai/openai/o3, https://openrouter.ai/openai/o3-mini — reasoning models, no `temperature` parameter (HIGH — OpenAI API spec)
- https://openrouter.ai/anthropic/claude-opus-4.5 — confirmed $5/$25, 5x Sonnet-4.5 cost
- https://openrouter.ai/openai/o1-pro — confirmed $150/$600, off scale

---

## 2. OpenRouter platform documentation (HIGH)

- https://openrouter.ai/docs — OpenAI API compatibility confirmed; `base_url=https://openrouter.ai/api/v1`
- https://openrouter.ai/docs/quickstart — Auth + headers (HTTP-Referer, X-Title for app attribution)
- https://openrouter.ai/docs/parameters — per-model parameter support (`temperature`, `top_p`, `seed`, `logprobs`, `response_format`, `max_tokens`); confirms `seed` is forwarded only for providers that support it natively (OpenAI, Google, OSS — yes; Anthropic — no)
- https://openrouter.ai/docs/limits — rate limits and `x-ratelimit-*` headers
- https://openrouter.ai/keys — API key management page
- https://openrouter.ai/api/v1/models — JSON listing of all models with pricing/context/parameter flags (used as live source-of-truth for the shortlist)

---

## 3. Provider model documentation (HIGH)

### 3.1 OpenAI
- https://platform.openai.com/docs/models/gpt-4-1 — GPT-4.1 family overview, knowledge cutoff Jun 2024, released April 2025
- https://platform.openai.com/docs/models/gpt-4o — GPT-4o + GPT-4o-mini reference
- https://openai.com/research/gpt-4-1 — model card claims for GPT-4.1-mini ("competitive with gpt-4o at lower cost")
- https://platform.openai.com/docs/api-reference/chat/create — `seed` and `response_format` parameter support

### 3.2 Anthropic
- https://docs.anthropic.com/en/docs/about-claude/models — Sonnet-4.5 release notes, dated version slug `claude-sonnet-4-5-20250929`
- https://docs.anthropic.com/en/api/messages — official API spec; **does not expose `seed`** parameter (HIGH confidence — primary source)

### 3.3 Google
- https://ai.google.dev/gemini-api/docs/models/gemini — Gemini 2.5 family
- https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models — pricing alignment with OR

### 3.4 Meta
- https://www.llama.com/llama3_3/license/ — Llama 3.3 Community License terms (commercial up to 700M MAU)

### 3.5 Alibaba (Qwen)
- https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507 — Qwen3 model card with license + benchmarks
- https://huggingface.co/Qwen/Qwen2.5-72B-Instruct — Qwen2.5 reference (basis for JuStRank ranking)

### 3.6 DeepSeek
- https://github.com/deepseek-ai/DeepSeek-V3 — V3 model card and license (MIT-style permissive)

### 3.7 xAI
- https://x.ai/api — Grok API docs

---

## 4. Judge / evaluator literature (HIGH for the cited papers)

- **JudgeBench (Tan et al., ICLR 2025)** — https://arxiv.org/abs/2410.12784 — Source for Claude-3.5-Sonnet (64.3%), GPT-4o (~57%), Llama-3.1-70B (~52%) JudgeBench accuracy numbers cited in `30-recommendation.md` §4.
- **JuStRank (2025)** — https://arxiv.org/abs/2502.02788 — Source for Qwen2.5-72B top-ranked prompted judge (τ=0.827).
- **Prometheus 2 (Kim et al., 2024)** — https://arxiv.org/abs/2405.01535 — Source for N-sample voting variance reduction claim used in §4 mitigation argument.
- **MT-Bench / LLM-as-a-Judge (Zheng et al., NeurIPS 2023)** — https://arxiv.org/abs/2306.05685 — Foundational reference for the prompted-judge regime.
- **G-Eval (Liu et al., EMNLP 2023)** — https://arxiv.org/abs/2303.16634 — Logprob-based continuous scoring (Tier C future work, motivates logprob preference).

---

## 5. Prior research (project-internal, MEDIUM confidence — corroborate via primary)

- `research/llm-judge-cybersec/30-gap-analysis.md` §5 — original judge model recommendation
- `research/llm-judge-cybersec/followup-open-source-judges/30-recommendation.md` — open-source self-host evaluation that flagged M-Prometheus / JudgeLRM / Qwen2.5; this OpenRouter follow-up confirms none of those judge-specialized fine-tunes are hosted on OpenRouter
- `docs/phase-2/evaluation-rubrics.md` — current rubric (5-dim universal direct-assessment)
- `src/domain/services/llm_judge_service.py` — current implementation (subprocess CLI, no temp control) — direct read this session

---

## 6. Confidence summary by deliverable section

| Section | Confidence | Rationale |
|---|---|---|
| Pricing tables (`10-`, `20-`) | **HIGH** | Verified live on OR pages 2026-04-25 |
| Context-window numbers | **HIGH** | OR model page primary source |
| Parameter support (temp/seed/logprobs) | **HIGH** for OpenAI/Anthropic/Google (provider docs); **MEDIUM** for OSS (relies on OR's `/api/v1/models` schema flags) |
| Reliability claims (JudgeBench scores) | **HIGH** for cited models in Tan et al.; **MEDIUM** for "GPT-4.1-mini ≈ GPT-4o-class" (extrapolation from OpenAI marketing) |
| Cohen's κ extrapolation in `30-` §4 | **MEDIUM-LOW** | Translation from JudgeBench accuracy → κ is heuristic, not direct measurement; flagged as such |
| Cost projections | **HIGH** for $/call; **MEDIUM** for total project (workload assumption could shift if test set grows) |
| License claims | **HIGH** | Each license cited via primary URL |
| Reproducibility class assignments | **HIGH** for slug datedness; **HIGH** for seed support per provider docs |

---

## 7. Items that need re-verification before final submission

- `openai/gpt-4.1-mini` exact dated slug on OR — confirmed `2025-04-14` from model card; verify it is the form returned by `client.models.retrieve()` before pinning in code (low risk)
- OpenRouter's `seed` forwarding for Qwen3-235B — schema flag says yes, but provider-side actual determinism is empirical; pilot 5 calls with same seed and diff outputs to confirm
- GPT-5 family `temperature` exposure on OR — per OR API schema as of 2026-04-25 = NO; if OR adds support during the project lifecycle, revisit shortlist
- Pricing snapshot freshness — OR posts pricing changes on https://openrouter.ai/changelog; re-verify on the day of methodology freeze
