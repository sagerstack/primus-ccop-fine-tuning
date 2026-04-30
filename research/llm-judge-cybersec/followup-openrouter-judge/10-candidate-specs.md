# Candidate specs — OpenRouter judges

All pricing, canonical slugs, and supported-parameter flags verified against OpenRouter's `/api/v1/models` endpoint on **2026-04-25**. Confidence on pricing: **HIGH** (primary source). Confidence on reliability numbers: **MEDIUM** (third-party benchmarks; not CCoP-specific).

Canonical-slug format: OpenRouter exposes both a stable alias (`vendor/family-name`) and a dated canonical (`vendor/family-name-YYYY-MM-DD` or `-YYYYMMDD`). **Always call the canonical slug in code** so the methodology can cite a reproducible version.

---

## A. Tier A — budget-primary contenders

### A.1 `google/gemini-2.5-flash-lite`

- **Canonical slug**: `google/gemini-2.5-flash-lite` (no dated suffix — watch list item)
- **OpenRouter model card**: https://openrouter.ai/models/google/gemini-2.5-flash-lite
- **Pricing** (2026-04-25): $0.10 / 1M input, $0.40 / 1M output, plus $0.10/1K images (not relevant)
- **Context window**: 1,048,576 tokens
- **Supported params**: temperature ✓, seed ✓, logprobs ✗, top_p, top_k, response_format, stop
- **License**: Google proprietary (Gemini API Terms); permits commercial use and academic research.
- **Reported reliability**: Gemini 2.5 family sits behind 2.5-Pro on reasoning benchmarks but ahead of older Flash. No published JudgeBench score for `2.5-flash-lite` specifically (medium-low confidence on judge reliability).
- **Domain fit for compliance QA**: Google RAG/long-context strength is real; cybersecurity-specific pretraining not marketed. Acceptable for rubric-scoring tasks.
- **Known failure modes**: Safety filters occasionally truncate regulatory content containing threat language. Over-cautious on "attacker tactics" framing. Has happened historically with Gemini family; verify on a 10-case pilot.

### A.2 `openai/gpt-4o-mini`

- **Canonical slug**: `openai/gpt-4o-mini-2024-07-18` (OpenRouter API exposes `openai/gpt-4o-mini` as stable alias — verify with OR dated-slug endpoint before pinning)
- **OpenRouter model card**: https://openrouter.ai/models/openai/gpt-4o-mini
- **Pricing** (2026-04-25): $0.15 / 1M input, $0.60 / 1M output
- **Context window**: 128,000 tokens
- **Supported params**: temperature ✓, seed ✓, **logprobs ✓**, top_p, response_format, stop, tools
- **License**: OpenAI commercial terms; permits academic and dissertation use.
- **Reported reliability**: gpt-4o-mini on JudgeBench is slightly below gpt-4o (which is ~57% overall on the ICLR 2025 paper). Strong MT-Bench judge performance in the literature for rubric-scored eval. Confidence: MEDIUM.
- **Domain fit**: Strong on regulatory/legal reasoning per MMLU/LegalBench public reports. Temperature + seed gives byte-level reproducibility — matters for the methodology section.
- **Known failure modes**: Tends toward brevity on free-text justifications; can truncate Chain-of-Thought when `max_tokens` isn't set wide. Mitigation: `max_tokens=1200`.
- **Logprobs**: yes — positions this as the cheapest logprob-capable candidate, unlocking G-Eval in Tier C.

### A.3 `meta-llama/llama-3.3-70b-instruct`

- **Canonical slug**: `meta-llama/llama-3.3-70b-instruct` (no dated suffix; release = Dec 2024)
- **OpenRouter model card**: https://openrouter.ai/models/meta-llama/llama-3.3-70b-instruct
- **Pricing** (2026-04-25): $0.10 / 1M input, $0.32 / 1M output
- **Context window**: 131,072 tokens
- **Supported params**: temperature ✓, seed ✓, logprobs ✗, top_p, top_k, stop
- **License**: Llama 3.3 Community License — commercial use permitted for entities < 700M monthly active users. Academic/dissertation clean.
- **Reported reliability**: Llama-3.1-70B on JudgeBench ~52% overall (Tan et al., ICLR 2025); Llama-3.3-70B is architecturally the same-class model with updated fine-tuning — reliability slightly higher by reported MMLU delta but unverified on JudgeBench directly. Confidence: MEDIUM.
- **Domain fit**: General-purpose; no cybersecurity pretraining. Known to handle RAG-heavy prompts well.
- **Known failure modes**: Can produce "safety preamble" text before answering when judging potentially sensitive responses — prepend "Output only valid JSON" to prompt to suppress.

### A.4 `x-ai/grok-4-fast`

- **Canonical slug**: `x-ai/grok-4-fast` (no dated suffix — watch list)
- **OpenRouter model card**: https://openrouter.ai/models/x-ai/grok-4-fast
- **Pricing** (2026-04-25): $0.20 / 1M input, $0.50 / 1M output
- **Context window**: 2,000,000 tokens
- **Supported params**: temperature ✓, seed ✓, **logprobs ✓**, top_p, stop
- **License**: xAI commercial terms; academic use permitted.
- **Reported reliability**: Grok 4 family has no published JudgeBench number. xAI publishes internal reasoning scores competitive with GPT-4o class. Confidence: LOW-MEDIUM (thin third-party validation for judge task specifically).
- **Domain fit**: Unclear. No published regulatory/legal benchmark numbers.
- **Known failure modes**: Documented informal tone bias (less formal than GPT/Claude). May reduce rubric-scoring consistency. Also: xAI has revised the base model meaningfully without stable dated slugs — **reproducibility risk higher than Anthropic/OpenAI/Google**.
- **Note**: Cheapest option with logprobs AND temperature — attractive on paper, weak on reliability evidence.

### A.5 `qwen/qwen3-235b-a22b-2507`

- **Canonical slug**: `qwen/qwen3-235b-a22b-07-25`
- **OpenRouter model card**: https://openrouter.ai/models/qwen/qwen3-235b-a22b-2507
- **Pricing** (2026-04-25): $0.071 / 1M input, $0.10 / 1M output — **cheapest in the shortlist by a large margin**
- **Context window**: 262,144 tokens
- **Supported params**: temperature ✓, seed ✓, **logprobs ✓**, top_p, top_k, stop
- **License**: Qwen Community License — commercial use permitted under 100M MAU; academic clean.
- **Reported reliability**: Qwen2.5-72B is the highest-ranked prompted judge in JuStRank 2025 (τ=0.827 with human ranking). Qwen3-235B-A22B is the MoE scale-up of that family — expected equal-or-better on judge tasks. Confidence: MEDIUM-HIGH (family-level evidence, not exact-model validation).
- **Domain fit**: Qwen models show strong regulatory/legal text performance in Chinese law benchmarks; English-law performance is weaker but adequate. CCoP is English-only — acceptable.
- **Known failure modes**: MoE models can have output-format inconsistency across routing decisions. Enforce `response_format={"type": "json_object"}` to mitigate.
- **Biggest surprise**: combined cost of input+output is ~$0.17/M. For our workload, this is ~1/50th the cost of Sonnet-4.5.

---

## B. Tier B — mid-range reliability-focused

### B.1 `openai/gpt-4.1-mini`

- **Canonical slug**: `openai/gpt-4.1-mini-2025-04-14` — **dated, reproducible, recommended**
- **OpenRouter model card**: https://openrouter.ai/models/openai/gpt-4.1-mini
- **Pricing** (2026-04-25): $0.40 / 1M input, $1.60 / 1M output
- **Context window**: 1,047,576 tokens
- **Supported params**: temperature ✓, seed ✓, logprobs ✗, top_p, response_format, stop, tools
- **License**: OpenAI commercial terms; academic clean.
- **Reported reliability**: gpt-4.1-mini is marketed by OpenAI as delivering "performance competitive with gpt-4o at substantially lower latency and cost." No published JudgeBench score for `4.1-mini` specifically — **inference from GPT-4.1 family**: strong reasoning + tool use; reliability expected at gpt-4o class. Confidence: MEDIUM.
- **Domain fit**: GPT-4.1 family tops regulatory/legal benchmarks (LegalBench, CaseHOLD) in public comparisons.
- **Known failure modes**: OpenAI's reasoning-effort tuning for 4.1-mini can cause longer outputs than needed. Set `max_tokens` conservatively.
- **Why this tier**: Balances Tier A cost with frontier-ish reliability. Dated slug (`-2025-04-14`) makes this **the most methodology-defensible single pick**.

### B.2 `google/gemini-2.5-flash`

- **Canonical slug**: `google/gemini-2.5-flash` (no dated suffix on OR — risk)
- **OpenRouter model card**: https://openrouter.ai/models/google/gemini-2.5-flash
- **Pricing** (2026-04-25): $0.30 / 1M input, $2.50 / 1M output
- **Context window**: 1,048,576 tokens
- **Supported params**: temperature ✓, seed ✓, logprobs ✗, top_p, top_k
- **License**: Google proprietary; academic use OK.
- **Reported reliability**: Strong on public reasoning benchmarks — MMLU ~84%, comparable to GPT-4o-mini. No direct JudgeBench score published. Confidence: MEDIUM.
- **Domain fit**: Google's long-context + RAG strength is well-documented; judge prompts with full GT injection benefit.
- **Known failure modes**: Same safety-filter truncation risk as flash-lite. Gemini occasionally adds a preamble ("I'll analyze this..."); suppress via system prompt.

### B.3 `deepseek/deepseek-v3.2`

- **Canonical slug**: `deepseek/deepseek-v3.2-20251201` — **dated, reproducible**
- **OpenRouter model card**: https://openrouter.ai/models/deepseek/deepseek-v3.2
- **Pricing** (2026-04-25): $0.252 / 1M input, $0.378 / 1M output
- **Context window**: 131,072 tokens
- **Supported params**: temperature ✓, seed ✓, logprobs ✗, top_p, top_k, response_format, stop, tools
- **License**: DeepSeek License (MIT-style for model, permits commercial use); academic clean.
- **Reported reliability**: V3.2 marketed as "GPT-5 class" on reasoning. DeepSeek R1 (reasoning sibling) scores well on judge-style tasks in third-party reports. Confidence: MEDIUM.
- **Domain fit**: DeepSeek models are strong at structured reasoning and RAG but have lighter English-law pretraining than GPT/Claude/Gemini. Regulatory QA fit: acceptable, not market-leading.
- **Known failure modes**: DeepSeek has a documented history of producing Chinese-language snippets when reasoning about unfamiliar English regulation; mitigation: explicit "respond in English only" instruction.

---

## C. Tier C — quality-primary (reference)

### C.1 `anthropic/claude-sonnet-4.5`

- **Canonical slug**: `anthropic/claude-4.5-sonnet-20250929` — **dated, reproducible**
- **OpenRouter model card**: https://openrouter.ai/models/anthropic/claude-sonnet-4.5
- **Pricing** (2026-04-25): $3 / 1M input, $15 / 1M output
- **Context window**: 1,000,000 tokens
- **Supported params**: temperature ✓, seed ✗ (Anthropic doesn't support seed), logprobs ✗, top_p, top_k, stop
- **License**: Anthropic commercial terms; academic clean.
- **Reported reliability**: Claude-3.5-Sonnet scored 64.3% on JudgeBench (Tan et al., ICLR 2025, Table 2) — highest among general-purpose models in the paper. Sonnet-4.5 is the 2025 refresh on the same line; expected equal-or-better. Confidence: MEDIUM-HIGH.
- **Domain fit**: Claude family is marketed for compliance/legal/regulatory reasoning. CCoP-style work is in-distribution.
- **Known failure modes**: **No seed support** — cannot achieve byte-level reproducibility. Mitigate via N=3 temperature-0.2 sampling and report mode-score only; methodology claim becomes "distributional reproducibility" not "byte-level."
- **Why it's here**: **Null hypothesis baseline**. If we do nothing, we use this. Any cheaper pick must defend that it doesn't sacrifice too much reliability vs this.

### C.2 `google/gemini-2.5-pro`

- **Canonical slug**: `google/gemini-2.5-pro` (no dated suffix — watch list)
- **OpenRouter model card**: https://openrouter.ai/models/google/gemini-2.5-pro
- **Pricing** (2026-04-25): $1.25 / 1M input, $10 / 1M output
- **Context window**: 1,048,576 tokens
- **Supported params**: temperature ✓, seed ✓, logprobs ✗
- **License**: Google proprietary; academic clean.
- **Reported reliability**: 2.5-Pro tops reasoning leaderboards. No public JudgeBench score. Confidence: MEDIUM.
- **Domain fit**: Strong generalist; long-context ideal for full GT injection.
- **Use case**: quality-primary non-Anthropic pick.

### C.3 `openai/gpt-4.1`

- **Canonical slug**: `openai/gpt-4.1` (base alias; OR exposes dated variants per provider)
- **OpenRouter model card**: https://openrouter.ai/models/openai/gpt-4.1
- **Pricing** (2026-04-25): $2 / 1M input, $8 / 1M output
- **Context window**: 1,047,576 tokens
- **Supported params**: temperature ✓, seed ✓, logprobs ✗ (not listed on OR schema; verify per-provider)
- **License**: OpenAI commercial; academic clean.
- **Reported reliability**: GPT-4.1 family is the modern successor to GPT-4o; expected at-or-above gpt-4o JudgeBench (~57%). Confidence: MEDIUM.
- **Use case**: full-strength GPT-4 class if we want to triangulate Claude vs OpenAI frontier.

---

## D. Drop-list (disqualified after spec review)

| Model | Reason |
|---|---|
| `openai/gpt-5*` (all) | `temperature` not exposed on OR endpoint — fails A1 |
| `openai/o1`, `openai/o3*` | No temperature — fails A1 |
| `anthropic/claude-opus-4.5` and above | 5x cost of Sonnet-4.5 without proven judge superiority |
| `anthropic/claude-opus-4.7` | `temperature` parameter flagged NOT supported in OR API schema |
| `qwen/qwen-2.5-7b-instruct`, `meta-llama/llama-3.1-8b-instruct` | 7-8B models likely below reliability floor for compliance reasoning |
| `openai/o1-pro` ($150/$600) | Cost envelope incompatible with ~30K-call project scale |
| `meta-llama/llama-3.3-70b-instruct:free` | Free tier: no seed, rate-limited — fails reproducibility |
| Any non-dated OpenAI search-preview variants | No temp + no seed |

---

## E. Summary flag — reproducibility risk per pick

| Pick | Dated slug | Seed | Reproducibility class |
|---|---|---|---|
| `openai/gpt-4.1-mini-2025-04-14` | Yes | Yes | **A — byte-level with pinned seed** |
| `openai/gpt-4o-mini` | Partial (`-2024-07-18` alias) | Yes | A- |
| `deepseek/deepseek-v3.2-20251201` | Yes | Yes | A |
| `openai/o3-mini-2025-01-31` | Yes | Yes (but no temp → N=1 only) | Restricted (no N-vote) |
| `qwen/qwen3-235b-a22b-07-25` | Yes | Yes | A |
| `google/gemini-2.5-flash` | No (OR exposes stable alias only) | Yes | **B — distributional only** |
| `anthropic/claude-4.5-sonnet-20250929` | Yes | **No** | **B — distributional only** |
| `meta-llama/llama-3.3-70b-instruct` | No | Yes | B-A |
| `x-ai/grok-4-fast` | No | Yes | B (xAI has revised silently) |

**Finding**: only `openai/gpt-4.1-mini`, `deepseek/deepseek-v3.2`, and `qwen/qwen3-235b-a22b-2507` are in reproducibility-class A *and* are budget-friendly enough to be primary. This narrows the recommendation materially.
