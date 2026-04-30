# Cost projection — OpenRouter judge candidates

Date: 2026-04-25
Pricing source: OpenRouter model pages (verified 2026-04-25 via WebFetch on `openrouter.ai/<vendor>/<model>` URLs cited in `10-candidate-specs.md`).
Confidence: **HIGH** for pricing (primary source). **MEDIUM** for token-count assumptions (project averages).

---

## 1. Workload model

The judge is invoked once per (test_case, mode, dimension, sample). Per spec:

| Dimension | Value |
|---|---|
| Test cases per milestone | 30 |
| Modes per case (hybrid, llm-only) | 2 |
| Dimensions scored per case (universal 5-dim rubric) | 5 |
| Samples per call (N=3 majority vote) | 3 |
| **Calls per milestone** | **900** |

Per-call token assumptions (mid-range):

| Component | Tokens |
|---|---|
| Question + response + GT block + rubric (input) | **3,500** |
| Justification + 5 integer scores + JSON (output) | **800** |

These are the means cited in the brief. Sensitivity analysis (high-bound: 4,000 in / 1,000 out) at the bottom of this file.

---

## 2. Cost lookup table

Per-call cost = (3,500 / 1,000,000) × $in_per_M + (800 / 1,000,000) × $out_per_M

| # | Model | $in/M | $out/M | $/call | $/milestone (900) | $/full-eval (13,050)¹ | $/project (30,000)² |
|---|---|---|---|---|---|---|---|
| **Tier A — budget-primary** | | | | | | | |
| 1 | `qwen/qwen3-235b-a22b-2507` | 0.071 | 0.10 | $0.000329 | **$0.30** | $4.29 | **$9.86** |
| 2 | `meta-llama/llama-3.3-70b-instruct` | 0.10 | 0.32 | $0.000606 | $0.55 | $7.91 | $18.18 |
| 3 | `google/gemini-2.5-flash-lite` | 0.10 | 0.40 | $0.000670 | $0.60 | $8.74 | $20.10 |
| 4 | `openai/gpt-4o-mini` | 0.15 | 0.60 | $0.001005 | $0.90 | $13.12 | $30.15 |
| 5 | `x-ai/grok-4-fast` | 0.20 | 0.50 | $0.001100 | $0.99 | $14.36 | $33.00 |
| **Tier B — mid-range reliability** | | | | | | | |
| 6 | `deepseek/deepseek-v3.2-20251201` | 0.252 | 0.378 | $0.001184 | $1.07 | $15.45 | $35.53 |
| 7 | `google/gemini-2.5-flash` | 0.30 | 2.50 | $0.003050 | $2.75 | $39.80 | $91.50 |
| 8 | `openai/gpt-4.1-mini-2025-04-14` | 0.40 | 1.60 | $0.002680 | **$2.41** | $34.97 | **$80.40** |
| **Tier C — quality-primary** | | | | | | | |
| 9 | `openai/gpt-4.1` | 2.00 | 8.00 | $0.013400 | $12.06 | $174.87 | $402.00 |
| 10 | `google/gemini-2.5-pro` | 1.25 | 10.00 | $0.012375 | $11.14 | $161.49 | $371.25 |
| 11 | `anthropic/claude-sonnet-4.5` | 3.00 | 15.00 | $0.022500 | **$20.25** | $293.63 | **$675.00** |

¹ Full 435-case evaluation run = 435 × 2 × 5 × 3 = **13,050 calls**.
² Project lifecycle assumption from brief = **30,000 calls**.

---

## 3. Cost-of-mistake comparison

The "null hypothesis" is to keep using Sonnet-4.5 via OpenRouter (same family, pinned). Switching saves:

| Switch | $ saved / milestone | $ saved / full-eval | $ saved / project |
|---|---|---|---|
| Sonnet-4.5 → Qwen3-235B | $19.95 (-99%) | $289.34 | **$665.14** |
| Sonnet-4.5 → GPT-4.1-mini | $17.84 (-88%) | $258.66 | **$594.60** |
| Sonnet-4.5 → DeepSeek-V3.2 | $19.18 (-95%) | $278.18 | $639.47 |
| Sonnet-4.5 → Llama-3.3-70B | $19.70 (-97%) | $285.72 | $656.82 |
| Sonnet-4.5 → Gemini-2.5-Pro | $9.11 (-45%) | $132.14 | $303.75 |
| Sonnet-4.5 → GPT-4.1 | $8.19 (-40%) | $118.76 | $273.00 |

**Reading**: even the most expensive Tier A pick (Grok-4-fast at $33 for the project) is < 1/20 of Sonnet-4.5 ($675).

---

## 4. Sensitivity — what if inputs run hot?

Worst-case per-call (4,000 input + 1,000 output tokens):

| Model | $/call (mid) | $/call (high) | $/project (high) |
|---|---|---|---|
| Qwen3-235B | $0.000329 | $0.000384 | $11.51 |
| GPT-4.1-mini | $0.002680 | $0.003200 | $96.00 |
| DeepSeek-V3.2 | $0.001184 | $0.001386 | $41.58 |
| Llama-3.3-70B | $0.000606 | $0.000720 | $21.60 |
| Sonnet-4.5 | $0.022500 | $0.027000 | $810.00 |

**Reading**: even at the high bound, every Tier A pick stays under **$50** for the full project. GPT-4.1-mini stays under **$100**. Sonnet-4.5 approaches **$1K**.

---

## 5. Hidden-cost notes (read before signing)

- **Implicit OpenRouter platform markup**: OpenRouter takes a margin on model calls (typically passed through transparently in the published $/M numbers). Pricing above is what your card is charged.
- **Streaming is not free**: streaming responses are billed identically; no surcharge or discount.
- **Rate limits on cheap models**: Qwen3-235B and Llama-3.3-70B may hit provider-side rate limits during burst evaluation (900 calls in a few hours). Plan for `tenacity`-style retry with exponential backoff. Realistic throughput: 10-30 calls/min for the cheap-tier providers vs 60-100/min for OpenAI/Anthropic.
- **Failed calls aren't usually billed** for parse failures, but timeouts past first-byte often are. Budget +5% headroom for `judge_error=True` retries.
- **N=3 majority vote multiplies cost 3x**: already factored in. If you need to cut cost mid-project, dropping to N=1 with seed-pinning (where supported) cuts $/project by 3x.

---

## 6. Bottom-line takeaways

1. **Sonnet-4.5 = $675 for the project.** Any cheap Tier A pick saves > $640.
2. **Qwen3-235B = $9.86 for the project.** Cheapest defensible pick. Almost free at this scale.
3. **GPT-4.1-mini = $80.40 for the project.** Mid-cost, dated/reproducible, evidence-backed. **Strongest cost-vs-defensibility ratio.**
4. **Below ~$10/project, model cost is no longer the binding constraint** — pick on reliability/reproducibility.
