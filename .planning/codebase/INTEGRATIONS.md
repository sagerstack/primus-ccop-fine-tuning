# External Integrations

**Analysis Date:** 2026-02-04

## APIs & External Services

**Model Inference:**
- Ollama - Local/remote LLM inference server
  - SDK/Client: httpx (async HTTP) via custom `OllamaClient` in `src/infrastructure/external/ollama_client.py`
  - Endpoints:
    - POST `/api/generate` - Text completion
    - GET `/api/tags` - List available models
    - POST `/api/show` - Get model info
    - POST `/api/create` - Import custom models
    - DELETE `/api/delete` - Remove models
  - Config: `CCOP_OLLAMA_HOST`, `CCOP_OLLAMA_TIMEOUT`
  - Adapter: `src/infrastructure/adapters/models/ollama_gateway.py` (implements IModelGateway)

**Model Management:**
- HuggingFace Hub - Download models for quantization and inference
  - SDK/Client: huggingface-hub 0.26.0+
  - Function: `snapshot_download()` for bulk model downloads
  - Default Model: `trendmicro-ailab/Llama-Primus-Reasoning`
  - Auth: Optional HuggingFace token (via parameter in `src/infrastructure/external/huggingface_client.py`)
  - Client: `src/infrastructure/external/huggingface_client.py` (HuggingFaceClient class)
  - Config: `CCOP_MODEL_HF_REPO`, `CCOP_MODEL_CACHE_DIR`

## Data Storage

**File Storage (Local Filesystem):**
- Test cases: JSONL format in `ground-truth/phase-2/test-suite/` directory
  - Discovery: Auto-scans for `b*.jsonl` files (b1.jsonl, b2.jsonl, etc.)
  - Format: One JSON object per line (test case metadata, question, expected response)
  - Repository: `src/infrastructure/adapters/repositories/jsonl_test_case_repository.py` (JSONLTestCaseRepository)

- Evaluation results: JSON format in `results/evaluations/` directory
  - Format: Individual JSON files per evaluation run
  - Repository: `src/infrastructure/adapters/repositories/json_result_repository.py` (JSONResultRepository)
  - Config: `CCOP_RESULTS_DIR`, `CCOP_TEST_CASES_DIR`

- Model cache: Local filesystem cache directory
  - Default: `~/.cache/ccop-models/`
  - Config: `CCOP_MODEL_CACHE_DIR`
  - Contents: Downloaded GGUF files, HuggingFace model artifacts

- Logs: Local log files
  - Default path: `logs/ccop-eval.log`
  - Format: JSON or console (configurable)
  - Config: `CCOP_LOG_FILE`, `CCOP_LOG_FORMAT`, `CCOP_LOG_LEVEL`

**Databases:**
- None - This is a stateless evaluation framework with filesystem-based persistence

**Caching:**
- Python memory cache - In-memory caching of test case collections (optional)
- Filesystem cache - HuggingFace and model cache directories

## Authentication & Identity

**Auth Provider:**
- None required for core functionality
- Optional: HuggingFace token for private model repos (parameter-based, not environment variable based)
- Implementation: `src/infrastructure/external/huggingface_client.py` accepts optional token parameter

## Monitoring & Observability

**Error Tracking:**
- None integrated - Errors logged via structlog

**Logs:**
- Structured JSON logging via structlog 24.1.0+
- Adapter: `src/infrastructure/adapters/logging/structlog_adapter.py`
- Alternative: Console logging via `src/infrastructure/adapters/logging/console_logger.py`
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Output destinations: File (`CCOP_LOG_FILE`) and/or console
- Implementation uses dependency injection - selectable at runtime via `CCOP_LOG_FORMAT`

**Metrics & Performance:**
- Manual instrumentation in gateways:
  - Response latency tracked in ModelResponse (milliseconds)
  - Token counts from Ollama captured
  - Evaluation timing for report generation

## CI/CD & Deployment

**Hosting:**
- Self-hosted - Runs locally with Python/Poetry or on deployment servers with same environment

**Deployment Model:**
- CLI-based standalone application (no web server)
- Requires Python 3.10+ and Poetry pre-installed
- Ollama instance must be running (locally or accessible via network)

**CI Pipeline:**
- Not detected - Framework is designed for manual runs via CLI or scripts

## Environment Configuration

**Required Env Vars:**
- `CCOP_OLLAMA_HOST` - Ollama endpoint (default: http://localhost:11434)
- `CCOP_MODEL_NAME` - Model identifier (default: primus-reasoning)
- `CCOP_MODEL_HF_REPO` - HuggingFace repository (default: trendmicro-ailab/Llama-Primus-Reasoning)

**Optional Env Vars:**
- `CCOP_OLLAMA_TIMEOUT` - Request timeout seconds (default: 300)
- `CCOP_MODEL_QUANTIZATION` - GGUF quantization (default: Q5_K_M)
- `CCOP_LOG_LEVEL` - Log level (default: INFO)
- `CCOP_LOG_FORMAT` - Log format json or console (default: json)
- `CCOP_DEBUG` - Enable debug mode (default: false)
- `CCOP_MOCK_MODE` - Use mock gateway instead of Ollama (default: false)
- `CCOP_MODEL_CACHE_DIR` - Model cache path (default: ~/.cache/ccop-models)
- `CCOP_RESULTS_DIR` - Results output path (default: results/evaluations)
- `CCOP_TEST_CASES_DIR` - Test cases input path (default: ../ground-truth/phase-2/test-suite)
- `CCOP_BASELINE_THRESHOLD`, `CCOP_FINETUNED_THRESHOLD`, `CCOP_DEPLOYMENT_THRESHOLD` - Phase-specific pass thresholds

**Secrets Location:**
- None required - No API keys or credentials needed for core functionality
- Optional HuggingFace token passed as parameter, not via environment

## Webhooks & Callbacks

**Incoming:**
- None - This is a batch evaluation framework without network listeners

**Outgoing:**
- None - Evaluations run locally with no external API calls except model downloads and inference

## Model Quantization & Conversion

**GGUF Conversion Pipeline:**
- Source: HuggingFace transformers models (safetensors format)
- Target: GGUF quantized format for llama.cpp/Ollama
- Tool: llama.cpp (external, not packaged)
- Converter: `src/infrastructure/adapters/converters/gguf_converter.py` (GGUFConverter class)
- Status: Stub implementation - conversion expected to be done via manual shell scripts (`scripts/convert_to_gguf.sh`)
- Quantization levels: Q4_K_M, Q5_K_M (default), Q6_K, Q8_0

## Evaluation Data Flow

**Inference Pipeline:**
1. Test case loaded from JSONL (JSONLTestCaseRepository)
2. Test case sent to Ollama via OllamaClient HTTP API
3. Model response captured with latency metrics
4. Response parsed into ModelResponse entity
5. Evaluation results stored as JSON (JSONResultRepository)

**Semantic Similarity (Tier 2):**
- Uses sentence-transformers 3.3.1+ for embedding-based evaluation
- Model: Default all-MiniLM-L6-v2 (auto-downloaded from HuggingFace on first use)
- Computed locally via PyTorch
- No external API calls for semantic scoring

---

*Integration audit: 2026-02-04*
