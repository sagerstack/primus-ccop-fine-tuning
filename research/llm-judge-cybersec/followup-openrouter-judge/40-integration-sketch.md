# Integration sketch — replacing Claude CLI subprocess with OpenRouter

Date: 2026-04-25
Target file: `src/domain/services/llm_judge_service.py`
Adjacent files: `src/infrastructure/config/settings.py`, `.env.local`, `pyproject.toml`

This document is a **sketch**, not a refactor. Code blocks here are illustrative — final implementation belongs in a separate ticket.

---

## 1. Setup (one-time)

### 1.1 OpenRouter account + key

1. Visit https://openrouter.ai and sign in (Google / GitHub OAuth).
2. Top up account (start with $20 credit — covers ~150 full-eval runs of the budget-primary).
3. Create an API key: https://openrouter.ai/keys → name it `studio-ssdlc-judge`, copy the `sk-or-v1-...` value.
4. **Save the key**: it is shown once. Drop it into `.env.local` and the `secrets/` workflow if used.

### 1.2 Env variables

Add to `.env.local` (and mirror in `.env.test` with a separate dev-tier key if available):

```dotenv
# OpenRouter judge configuration
OPENROUTER_API_KEY=sk-or-v1-...
CCOP_LLM_JUDGE_PROVIDER=openrouter
CCOP_LLM_JUDGE_MODEL=openai/gpt-4.1-mini-2025-04-14
CCOP_LLM_JUDGE_TEMPERATURE=0.2
CCOP_LLM_JUDGE_SEED=42
CCOP_LLM_JUDGE_MAX_TOKENS=1200
CCOP_LLM_JUDGE_N_SAMPLES=3
CCOP_LLM_JUDGE_TIMEOUT_S=120

# Optional: inter-judge agreement (Tier C)
CCOP_LLM_JUDGE_BACKUP_MODEL=qwen/qwen3-235b-a22b-07-25
CCOP_LLM_JUDGE_AUDIT_MODEL=anthropic/claude-4.5-sonnet-20250929
```

### 1.3 Dependency

OpenRouter is OpenAI-API-compatible. Use the official OpenAI SDK (already familiar; widely supported) by overriding `base_url`:

```bash
poetry add openai tenacity
```

`tenacity` handles retries on rate-limit and 5xx.

### 1.4 Settings extension

In `src/infrastructure/config/settings.py`, add fields:

```python
class Settings(BaseSettings):
    # ... existing ...

    # OpenRouter judge
    openrouter_api_key: str | None = Field(default=None, env="OPENROUTER_API_KEY")
    llm_judge_provider: Literal["claude_cli", "openrouter"] = Field(
        default="claude_cli", env="CCOP_LLM_JUDGE_PROVIDER"
    )
    llm_judge_model: str = Field(default="sonnet", env="CCOP_LLM_JUDGE_MODEL")
    llm_judge_temperature: float = Field(default=0.2, env="CCOP_LLM_JUDGE_TEMPERATURE")
    llm_judge_seed: int | None = Field(default=42, env="CCOP_LLM_JUDGE_SEED")
    llm_judge_max_tokens: int = Field(default=1200, env="CCOP_LLM_JUDGE_MAX_TOKENS")
    llm_judge_n_samples: int = Field(default=3, env="CCOP_LLM_JUDGE_N_SAMPLES")
    llm_judge_timeout_s: int = Field(default=120, env="CCOP_LLM_JUDGE_TIMEOUT_S")
```

Note: `llm_judge_provider="claude_cli"` keeps the old subprocess path live during migration.

---

## 2. Code changes to `llm_judge_service.py`

### 2.1 Constructor — pluggable provider

```python
def __init__(self, model_name: Optional[str] = None, rubric_path: Optional[str] = None) -> None:
    from infrastructure.config.settings import get_settings
    settings = get_settings()

    self._provider = settings.llm_judge_provider
    self._model = model_name or settings.llm_judge_model
    self._temperature = settings.llm_judge_temperature
    self._seed = settings.llm_judge_seed
    self._max_tokens = settings.llm_judge_max_tokens
    self._timeout = settings.llm_judge_timeout_s
    self._rubric_path = Path(rubric_path) if rubric_path else (
        _PROJECT_ROOT / "docs" / "phase-2" / "evaluation-rubrics.md"
    )
    self._rubrics = self._load_rubrics()
    self._inventory_ids = self._load_inventory_ids()
    self._clause_text_cache = self._load_clause_text_cache()

    # Lazy-init OpenRouter client (only if provider=openrouter)
    self._or_client = None
    if self._provider == "openrouter":
        from openai import OpenAI
        if not settings.openrouter_api_key:
            raise RuntimeError(
                "CCOP_LLM_JUDGE_PROVIDER=openrouter but OPENROUTER_API_KEY not set"
            )
        self._or_client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=self._timeout,
        )
```

### 2.2 Replace `_call_claude_agent` with provider switch

```python
def _call_judge(self, prompt: str) -> str:
    """Provider-agnostic single judge call. Returns the model's text output."""
    if self._provider == "openrouter":
        return self._call_openrouter(prompt)
    return self._call_claude_cli(prompt)  # legacy fallback

def _call_openrouter(self, prompt: str) -> str:
    """Call OpenRouter via OpenAI-compat SDK."""
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    from openai import APIError, RateLimitError, APITimeoutError

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
        reraise=True,
    )
    def _do_call() -> str:
        kwargs = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        # Seed only added if provider supports it (OpenAI/Google/most OSS — yes; Anthropic — no)
        if self._seed is not None and not self._model.startswith("anthropic/"):
            kwargs["seed"] = self._seed
        # JSON mode for providers that support response_format
        if any(self._model.startswith(p) for p in ("openai/", "deepseek/", "qwen/", "mistralai/")):
            kwargs["response_format"] = {"type": "json_object"}

        # OpenRouter app-attribution headers (visible on dashboard)
        extra_headers = {
            "HTTP-Referer": "https://github.com/sagerstack/studio-ssdlc",
            "X-Title": "studio-ssdlc CCoP eval",
        }
        resp = self._or_client.chat.completions.create(
            extra_headers=extra_headers,
            **kwargs,
        )
        if not resp.choices:
            raise RuntimeError("OpenRouter returned empty choices array")
        content = resp.choices[0].message.content
        if not content:
            raise RuntimeError("OpenRouter returned empty content")
        return content

    return _do_call()

def _call_claude_cli(self, prompt: str) -> str:
    """Legacy: original subprocess path retained during migration."""
    result = subprocess.run(
        ["claude", "chat", "--model", self._model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=self._timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude Agent SDK error: {result.stderr}")
    return result.stdout
```

Then change every `self._call_claude_agent(prompt)` callsite (two: `evaluate_response` and `universal_evaluate_response`) to `self._call_judge(prompt)`.

### 2.3 N-sample majority vote (new — A1 requirement)

```python
def _call_judge_with_voting(self, prompt: str, n_samples: int) -> tuple[str, list[str]]:
    """
    Call judge n_samples times at the configured temperature.
    Returns (majority_response, all_responses) for downstream parse + vote.
    Caller is responsible for parsing each response and voting on dimension scores.
    """
    responses = []
    for i in range(n_samples):
        # Vary seed deterministically per sample if seed is set, else just resample
        if self._seed is not None and not self._model.startswith("anthropic/"):
            saved = self._seed
            self._seed = saved + i  # deterministic per-sample seed
            try:
                responses.append(self._call_judge(prompt))
            finally:
                self._seed = saved
        else:
            responses.append(self._call_judge(prompt))
    return responses[0], responses  # first as fallback; voting elsewhere
```

The vote logic (per-dimension mode of the 0-3 scores across N=3 calls) lives in the caller — keep this method dumb and let evaluation logic stay in `evaluate_response` / `universal_evaluate_response`.

---

## 3. Backward compatibility plan

| Phase | Setting | Behavior |
|---|---|---|
| **Phase 0 — current** | (no setting) | Subprocess to `claude chat` (today) |
| **Phase 1 — both paths live** | `CCOP_LLM_JUDGE_PROVIDER=claude_cli` | Subprocess path (default for safety) |
| **Phase 1 — both paths live** | `CCOP_LLM_JUDGE_PROVIDER=openrouter` | OpenRouter path (opt-in, run pilot) |
| **Phase 2 — switch default** | flip default in `Settings` to `openrouter` | OpenRouter is default; subprocess still callable for emergency |
| **Phase 3 — remove legacy** | delete `_call_claude_cli` + subprocess import | Clean cut after 2 weeks of green builds |

The pilot in Phase 1 should be a 10-case A/B: same test cases, both providers, manual diff of judge outputs. If JSON parses cleanly and dimension scores match within ±1 on > 80% of cases, promote to default.

---

## 4. Rate limits and error handling specifics

### 4.1 OpenRouter rate-limit headers

OpenRouter returns these per response:

```
x-ratelimit-limit: 200
x-ratelimit-remaining: 187
x-ratelimit-reset: 1714075200
```

Tenacity retry handles rate-limit 429s by default. The 4-attempt exponential backoff (2s → 4s → 8s → 16s) is enough for typical bursts. Log `x-ratelimit-remaining` per call when below 20% to detect pressure.

### 4.2 Provider-side hiccups

OpenRouter routes to upstream providers (OpenAI, Anthropic, etc.). Common upstream errors and handling:

| Error class | Cause | Handling |
|---|---|---|
| `RateLimitError` (429) | Upstream rate limit | Retry with backoff |
| `APITimeoutError` | Upstream slow | Retry once, then surface |
| `APIError` (5xx) | Upstream outage | Retry up to 4x; on 4th fail, return `JudgeEvaluation.error()` (skip-and-flag — already in service) |
| `BadRequestError` (400) | Bad model ID / prompt-too-long | Don't retry — log and skip |
| `AuthenticationError` (401) | Bad API key | Don't retry — fail loudly |

The existing `JudgeEvaluation.error()` skip-and-flag pattern (line 162) absorbs the final-fail case cleanly. No change to evaluation pipeline contract.

### 4.3 Throughput target

For a full milestone (900 calls):
- At 30 calls/min sustained → 30 min wall-clock.
- At 100 calls/min (OpenAI-class burst) → 9 min.

Run sequentially first; only parallelize via `asyncio` + `httpx` if a milestone takes > 1 hour to judge.

### 4.4 Cost-cap defense

Add a per-run hard cap so a runaway loop doesn't drain the OpenRouter balance:

```python
class JudgeCostGuard:
    def __init__(self, max_calls: int, model: str):
        self._max = max_calls
        self._n = 0
        self._model = model
    def tick(self):
        self._n += 1
        if self._n > self._max:
            raise RuntimeError(
                f"Judge cost guard tripped: {self._n} calls > {self._max} cap on {self._model}"
            )
```

Wire into `_call_judge` with `max_calls = settings.llm_judge_n_samples * 5 * cases * modes` set per run.

---

## 5. Methodology change-log additions

When this lands, the methodology section needs three lines added:

> Judge model: `openai/gpt-4.1-mini-2025-04-14` accessed via OpenRouter (`https://openrouter.ai/api/v1`), called with `temperature=0.2`, `seed=42`, `max_tokens=1200`, `response_format={"type":"json_object"}`. N=3 samples per (case, mode, dimension) with majority vote on 0-3 dimension scores. Sampling seed varies per sample as `42 + i` for `i in {0,1,2}`. Backup judge for inter-judge agreement: `qwen/qwen3-235b-a22b-07-25` at the same parameters.

Pinning the dated slug, the temperature, the seed scheme, and the JSON mode is what makes this a defensible reproducible methodology line.

---

## 6. Open questions for the implementation ticket

1. Does `infrastructure/config/settings.py` already use `pydantic-settings` BaseSettings? (Likely yes — confirm before adding fields.)
2. Should we expose `provider/model` per-call (override) for the audit-spot-check case? (Recommendation: yes — add `model_override` kwarg on `evaluate_response` so a single-line caller can route a subset of cases through Sonnet-4.5 for arbitration.)
3. Where does the cost-cap setting live? (Suggest: per-CLI-run flag, default high, override low for dev.)
4. Do we keep the old `claude chat` subprocess as a fallback for offline dev? (Recommendation: yes for one milestone, then delete.)
