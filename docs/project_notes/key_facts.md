# Key Facts

This file stores project configuration, important constants, and frequently-needed **non-sensitive** information.

## SECURITY WARNING

**NEVER store passwords, API keys, or sensitive credentials in this file.** This file is committed to version control.

**Safe to store:** Hostnames, ports, project identifiers, URLs, service account emails
**NOT safe:** Passwords, API keys, tokens, secrets

---

## Project Information

**Project Name:** CCoP 2.0 Model Evaluation Framework
**Purpose:** Evaluate LLM performance on Singapore's Cybersecurity Code of Practice (CCoP 2.0) standards
**Base Model:** Llama-Primus-Reasoning (trendmicro-ailab/Llama-Primus-Reasoning)

## Configuration

**Environment Prefix:** `CCOP_` (all config keys prefixed)
**Config File:** `src/infrastructure/config/settings.py`
**Example Template:** `src/config/.env.example`

**Key Environment Variables:**
- `CCOP_OLLAMA_HOST` - Ollama endpoint (default: http://localhost:11434)
- `CCOP_OLLAMA_TIMEOUT` - Request timeout seconds (default: 300)
- `CCOP_MODEL_NAME` - Model identifier (default: primus-reasoning)
- `CCOP_MODEL_HF_REPO` - HuggingFace repository
- `CCOP_MODEL_QUANTIZATION` - GGUF quantization level (default: Q5_K_M)
- `CCOP_LOG_LEVEL` - Logging level (default: INFO)
- `CCOP_MOCK_MODE` - Use mock gateway for testing

## Local Development Ports

**Services:**
- Ollama API: `11434`
- (No other services currently)

**Data Directories:**
- Test cases: `ground-truth/phase-2/test-suite/`
- Results output: `results/evaluations/`
- Model cache: `~/.cache/ccop-models/`
- Logs: `logs/`

## CLI Commands

**Entry Point:** `ccop-eval` (via Poetry)

```bash
# From src/ directory
poetry run ccop-eval setup check          # Check prerequisites
poetry run ccop-eval setup model          # Download and setup model
poetry run ccop-eval evaluate run         # Run evaluation
poetry run ccop-eval report generate      # Generate reports
```

## Benchmarks

**Tier 1 (Label-based):** B1, B2, B3, B4, B5, B6
**Tier 2 (Semantic):** B8, B9, B11, B15, B17, B18, B19
**Tier 3 (LLM Judge):** B7, B10, B12, B13, B14, B16, B20, B21

**Unimplemented:** B7, B10, B14, B16 (raise NotImplementedError)

## Thresholds

**Phase Thresholds:**
- Baseline (Phase 1): 15%
- Fine-tuned (Phase 2): 50%
- Deployment (Phase 3): 85%

**Semantic Similarity:**
- High score threshold: >= 0.70
- Low score penalty threshold: < 0.60

## Important URLs

**Documentation:**
- CCoP 2.0 Official: https://www.csa.gov.sg/legislation/codes-of-practice
- Primus Model: https://huggingface.co/trendmicro-ailab/Llama-Primus-Reasoning

**Project Paper:**
- `report/term1-mid/Primus-Fine-Tuning-CCOP2-SG-v2.0-SagarPratapSingh-1010736.md`

## Python Requirements

- Python: 3.10+ (tested through 3.13)
- Package Manager: Poetry
- Type Checking: MyPy (strict mode)
- Formatter: Black (100 char line length)
- Linter: Ruff

---

## Tips

- Keep entries current (update when things change)
- Include both production and development details
- Add URLs to make navigation easier
- Use consistent formatting
