# Scope and shortlist — OpenRouter judge model selection

Date of investigation: 2026-04-25
Source of truth for availability and pricing: OpenRouter live models API (`https://openrouter.ai/api/v1/models`) snapshot taken 2026-04-25.

---

## 1. What this follow-up is

We currently invoke Claude-as-judge via `subprocess.run(["claude", "chat", ...])` (see `src/domain/services/llm_judge_service.py::_call_claude_agent`). This has three gaps:

1. **No temperature control** — A1 variance-reduction plan requires temp=0.2 with N=3 majority vote.
2. **No seed control** — blocks byte-level reproducibility.
3. **No pinned version string** — Anthropic can silently update the subscription model under us. Methodology cannot cite a dated version.

Replacement must be a direct HTTP-API model accessible via OpenRouter with (a) temperature support, (b) dated/pinned version IDs, (c) a license compatible with a university dissertation, and (d) budget-friendly enough to afford ~30K calls over the project lifecycle.

Prior research (`research/llm-judge-cybersec/followup-open-source-judges/30-recommendation.md`) identified M-Prometheus-14B, Prometheus 2, JudgeLRM, and Qwen2.5 as candidate open-source judges for local deployment. **This follow-up scopes the decision to OpenRouter-hosted models only** — self-hosting is out of scope here (tracked separately as a Phase 3 option).

---

## 2. Non-negotiable constraints (hard filters)

| Constraint | Rationale |
|---|---|
| Hosted on OpenRouter.ai with verifiable model ID | Allows a single SDK (OpenAI-compat) to replace the Claude CLI subprocess |
| Supports `temperature` parameter | Required for A1 N-sample majority vote |
| License permits academic / dissertation use | Dissertation publishability |
| Stable, dated model ID (`canonical_slug` with date suffix) | Reproducibility in methodology section |
| Context window ≥ 32K tokens | Judge prompt reaches 8-15K; 32K gives headroom |

**Strong preferences (tie-breakers):**

| Preference | Rationale |
|---|---|
| `seed` parameter supported | Byte-level reproducibility (OpenAI + Google + most open-source models have it; Anthropic does not) |
| Per-1M input + output pricing within budget (target: < $2 input, < $10 output) | ~30K calls at ~3.5K input + 800 output ≈ 105M in + 24M out — affordability line |
| Judge-task reliability evidence (JudgeBench / MT-Bench / Pearson with humans) | Defensibility in dissertation |
| `logprobs` access (nice-to-have) | Future G-Eval continuous-scoring extension |

---

## 3. Candidates investigated (all verified on OpenRouter)

### 3.1 Frontier commercial tier

| Model ID | Canonical slug | Hosted | In/Out $/M | Temp | Seed | Logprobs | Notes |
|---|---|---|---|---|---|---|---|
| `anthropic/claude-sonnet-4.5` | `anthropic/claude-4.5-sonnet-20250929` | Yes | $3 / $15 | Yes | No | No | Current model family. Dated slug available. |
| `anthropic/claude-sonnet-4` | `anthropic/claude-sonnet-4` | Yes | $3 / $15 | Yes | No | No | 1M context. |
| `anthropic/claude-opus-4.5` | `anthropic/claude-opus-4.5` | Yes | $5 / $25 | Yes | No | No | Premium reasoning. |
| `anthropic/claude-haiku-4.5` | `anthropic/claude-4.5-haiku-20251001` | Yes | $1 / $5 | Yes | No | No | Cheap Anthropic option. |
| `anthropic/claude-3.5-haiku` | `anthropic/claude-3-5-haiku` | Yes | $0.80 / $4 | Yes | No | No | Older but cheaper Anthropic. |
| `openai/gpt-5` | `openai/gpt-5` | Yes | $1.25 / $10 | **No** | Yes | No | Temp NOT exposed by OR endpoint for GPT-5 family. |
| `openai/gpt-5-mini` | `openai/gpt-5-mini-2025-08-07` | Yes | $0.25 / $2 | **No** | Yes | No | Temp NOT exposed. |
| `openai/gpt-5.1` | `openai/gpt-5.1-20251113` | Yes | $1.25 / $10 | **No** | Yes | No | Temp NOT exposed. |
| `openai/gpt-4.1` | `openai/gpt-4.1` | Yes | $2 / $8 | Yes | Yes | No | Non-reasoning, full temp + seed. |
| `openai/gpt-4.1-mini` | `openai/gpt-4.1-mini-2025-04-14` | Yes | $0.40 / $1.60 | Yes | Yes | No | **Prime budget-reliable candidate.** |
| `openai/gpt-4.1-nano` | `openai/gpt-4.1-nano` | Yes | $0.10 / $0.40 | Yes | Yes | No | Ultra-cheap; reliability TBD. |
| `openai/gpt-4o` | `openai/gpt-4o` | Yes | $2.50 / $10 | Yes | Yes | **Yes** | JudgeBench workhorse; logprobs for future G-Eval. |
| `openai/gpt-4o-mini` | `openai/gpt-4o-mini` | Yes | $0.15 / $0.60 | Yes | Yes | **Yes** | Cheapest logprob-capable option. |
| `openai/o3` | `openai/o3-2025-04-16` | Yes | $2 / $8 | **No** | Yes | No | Reasoning model, no temp. |
| `openai/o3-mini` | `openai/o3-mini-2025-01-31` | Yes | $1.10 / $4.40 | **No** | Yes | No | Reasoning model, no temp. |
| `openai/o1` | `openai/o1` | Yes | $15 / $60 | **No** | Yes | No | Reasoning, expensive. |
| `google/gemini-2.5-pro` | `google/gemini-2.5-pro` | Yes | $1.25 / $10 | Yes | Yes | No | 1M context; strong reasoning. |
| `google/gemini-2.5-flash` | `google/gemini-2.5-flash` | Yes | $0.30 / $2.50 | Yes | Yes | No | **Prime budget candidate.** |
| `google/gemini-2.5-flash-lite` | `google/gemini-2.5-flash-lite` | Yes | $0.10 / $0.40 | Yes | Yes | No | Ultra-cheap Google option. |
| `x-ai/grok-4` | `x-ai/grok-4-07-09` | Yes | $3 / $15 | Yes | Yes | Yes | Full params + logprobs. |
| `x-ai/grok-4-fast` | `x-ai/grok-4-fast` | Yes | $0.20 / $0.50 | Yes | Yes | Yes | **Extreme-budget candidate w/ logprobs.** |
| `x-ai/grok-3-mini` | `x-ai/grok-3-mini` | Yes | $0.30 / $0.50 | Yes | Yes | Yes | Cheap with full param set. |
| `cohere/command-r-plus-08-2024` | `cohere/command-r-plus-08-2024` | Yes | $2.50 / $10 | Yes | Yes | No | Dated ID; 128K ctx. |
| `mistralai/mistral-large-2411` | `mistralai/mistral-large-2411` | Yes | $2 / $6 | Yes | Yes | No | Dated ID. |
| `mistralai/mistral-large-2512` | `mistralai/mistral-large-2512` | Yes | $0.50 / $1.50 | Yes | Yes | No | Dec-2025 refresh — much cheaper. |

### 3.2 Open-source hosted tier

| Model ID | Canonical slug | Hosted | In/Out $/M | Temp | Seed | Logprobs | Notes |
|---|---|---|---|---|---|---|---|
| `meta-llama/llama-3.3-70b-instruct` | `meta-llama/llama-3.3-70b-instruct` | Yes | $0.10 / $0.32 | Yes | Yes | No | Llama 3.3 Community License. |
| `meta-llama/llama-3.1-70b-instruct` | `meta-llama/llama-3.1-70b-instruct` | Yes | $0.40 / $0.40 | Yes | Yes | No | Older; usually use 3.3. |
| `meta-llama/llama-4-maverick` | `meta-llama/llama-4-maverick` | Yes | $0.15 / $0.60 | Yes | Yes | No | 1M ctx. |
| `qwen/qwen-2.5-72b-instruct` | `qwen/qwen-2.5-72b-instruct` | Yes | $0.12 / $0.39 | Yes | Yes | No | JuStRank 2025 top-ranked family. |
| `qwen/qwen3-235b-a22b-2507` | `qwen/qwen3-235b-a22b-07-25` | Yes | $0.071 / $0.10 | Yes | Yes | Yes | **MoE — very cheap; logprobs.** |
| `qwen/qwen3-next-80b-a3b-instruct` | `qwen/qwen3-next-80b-a3b-instruct-2509` | Yes | $0.09 / $1.10 | Yes | Yes | No | Qwen Community License. |
| `qwen/qwen3-32b` | `qwen/qwen3-32b` | Yes | $0.08 / $0.24 | Yes | Yes | No | Dense, small, cheap. |
| `deepseek/deepseek-v3.2` | `deepseek/deepseek-v3.2-20251201` | Yes | $0.252 / $0.378 | Yes | Yes | No | **Dated ID; full param set.** |
| `deepseek/deepseek-chat-v3.1` | `deepseek/deepseek-chat-v3.1` | Yes | $0.15 / $0.75 | Yes | Yes | Yes | Logprobs + cheap. |
| `deepseek/deepseek-r1-0528` | `deepseek/deepseek-r1-0528` | Yes | $0.50 / $2.15 | Yes | Yes | No | R1 reasoning; dated. |
| `deepseek/deepseek-r1-distill-qwen-32b` | `deepseek/deepseek-r1-distill-qwen-32b` | Yes | $0.29 / $0.29 | Yes | Yes | Yes | Budget reasoning w/ logprobs. |
| `nousresearch/hermes-4-70b` | `nousresearch/hermes-4-70b` | Yes | (check page) | — | — | — | Alternative prompted judge. |

### 3.3 Specialty judges — NOT available on OpenRouter (disqualified)

Prior research flagged these as strong judges, but API snapshot confirms **none are hosted on OpenRouter**:

| Model | OpenRouter availability | Consequence |
|---|---|---|
| M-Prometheus-14B (Unbabel) | Not hosted | Self-host only; out of scope for this follow-up |
| Prometheus 2 (7B / 8x7B) | Not hosted | Self-host only |
| JudgeLM (7B / 13B / 33B) | Not hosted | Self-host only |
| JudgeLRM (7B / 14B) | Not hosted | Self-host only |
| Skywork-Critic | Not hosted | Self-host only |
| SFR-Judge | Not hosted | Self-host only |
| CompassJudger-2 | Not hosted | Self-host only |
| Auto-J-Bilingual | Not hosted | Self-host only |
| PandaLM | Not hosted | Self-host only |
| Self-Taught Evaluator | Not hosted | Self-host only |

**Impact on dissertation narrative**: if we want a judge-fine-tuned OSS model in the evaluation, it has to be self-hosted (as already planned in Phase 3 of the prior recommendation). OpenRouter path is strictly for prompted-generalist judges.

### 3.4 Other drop-list reasons

| Model | Dropped | Reason |
|---|---|---|
| `openai/gpt-5*` family (all) | Dropped | No `temperature` parameter via OR endpoint — violates A1 requirement. |
| `openai/o1`, `openai/o3`, `openai/o3-mini` | Dropped as primary | Reasoning models (no temperature). Retained as backup only for N=1 runs. |
| `openai/o1-pro` ($150 in / $600 out) | Dropped | 100x budget envelope without evidence of judge-specific superiority. |
| `anthropic/claude-opus-4.*` premium | Deprioritized | 5x cost vs Sonnet-4.5 for judge-task work; Sonnet-4.5 already above reliability target. |
| `microsoft/wizardlm-2-8x22b` | Deprioritized | Older (Apr 2024); Llama-3.3-70B and Qwen-2.5-72B supersede it. |
| `meta-llama/llama-3.3-70b-instruct:free` (free tier) | Dropped as methodology primary | Free tier has strict rate limits and does NOT support `seed` — fails reproducibility preference. Useful for dev only. |
| `qwen/qwen-2.5-7b-instruct` | Deprioritized | 7B likely below reliability floor for CCoP regulatory reasoning (see prior research §4). |
| `meta-llama/llama-3.1-8b-instruct` | Deprioritized | Same 7-8B ceiling argument. |
| `openai/gpt-4o-mini-search-preview`, `openai/gpt-4o-search-preview` | Dropped | No temp + no seed per API schema. |
| `qwen/qwen3-coder-*` variants | Dropped | Coder-specialized; domain misfit for regulatory reasoning. |
| Models without dated canonical slug | Deprioritized (not dropped) | Some OR models have only a base slug (no date) — acceptable but noted as higher reproducibility risk. |

---

## 4. Final shortlist (enters detailed eval in `10-candidate-specs.md`)

Nine models, three tiers:

**Tier A — budget-primary contenders (< $0.60 per full milestone):**
1. `google/gemini-2.5-flash-lite`
2. `openai/gpt-4o-mini`
3. `meta-llama/llama-3.3-70b-instruct`
4. `x-ai/grok-4-fast`
5. `qwen/qwen3-235b-a22b-2507`

**Tier B — mid-range reliability-focused (< $5 per full milestone):**
6. `openai/gpt-4.1-mini`
7. `google/gemini-2.5-flash`
8. `deepseek/deepseek-v3.2`

**Tier C — quality-primary (reference point, > $10 per milestone):**
9. `anthropic/claude-sonnet-4.5` (null hypothesis — same model family as current)
10. `google/gemini-2.5-pro`
11. `openai/gpt-4.1`

Each entry gets pricing, param support, license, reported reliability, and failure modes in `10-candidate-specs.md`.

---

## 5. What we deliberately did NOT evaluate

- **Self-hosted Prometheus/M-Prometheus/JudgeLRM**: Prior recommendation document stands; not OpenRouter-scoped.
- **GPT-5 family**: Drop for A1 (no temperature). Revisit if OpenRouter adds temp support later.
- **Reasoning-only models (o1/o3) as primary judges**: Drop for A1 (no temperature).
- **Pairwise-preference RM-style evaluators (Nemotron Reward, RewardBench winners)**: Different regime (pairwise, not direct assessment). Out of scope for this follow-up but noted as future work for Tier C inter-judge agreement.
- **Embedding-only / classifier-only OpenRouter endpoints**: No — we need free-text rubric-scored output.
