# Technology Stack

**Analysis Date:** 2026-02-04

## Languages

**Primary:**
- Python 3.10+ - Core application language, specified in `src/pyproject.toml` with compatibility through 3.13+

## Runtime

**Environment:**
- Python 3.10-3.13+ (Poetry enforces 3.10 minimum, targeting 3.11 for type checking)

**Package Manager:**
- Poetry 1.x - Dependency and project management
- Lockfile: `poetry.lock` (ignored in git, generated locally)

## Frameworks

**Core Application:**
- Clean Architecture / Hexagonal Architecture - Implemented via Ports & Adapters pattern
  - Domain layer: Pure business logic (zero external dependencies)
  - Application layer: Use cases and ports/interfaces
  - Infrastructure layer: External adapters and clients
  - Presentation layer: CLI interface

**CLI & Interaction:**
- Typer 0.12.5+ - Type-safe CLI framework (built on Click)
- Click 8.1.7 - Pinned to avoid 8.2+ breaking changes
- Rich 13.7.0+ - Beautiful terminal output and formatting

**Testing:**
- pytest 7.4.0+ - Test runner and framework
- pytest-asyncio 0.21.0+ - Async test support
- pytest-cov 4.1.0+ - Coverage reporting
- pytest-mock 3.12.0+ - Mocking utilities

**Dependency Injection:**
- dependency-injector 4.41.0+ - DI container implementation in `src/infrastructure/config/container.py`

**Build/Dev:**
- Black 23.12.0+ - Code formatting (100 char line length)
- Ruff 0.1.9+ - Linting (pycodestyle, pyflakes, isort, comprehensions, bugbear, pyupgrade)
- MyPy 1.7.0+ - Static type checking (strict mode)
- isort 5.13.0+ - Import sorting (aligned with Black)

## Key Dependencies

**Critical - Model Inference:**
- openai 1.50.0+ - OpenAI-compatible client for Ollama API
- httpx 0.27.0+ - Async HTTP client for Ollama endpoints
- huggingface-hub 0.26.0+ - Model downloads from HuggingFace Hub

**Critical - ML/Semantic Analysis:**
- sentence-transformers 3.3.1+ - Semantic similarity scoring (Tier 2 evaluation)
- torch 2.5.0+ - PyTorch backend for sentence-transformers (CPU/GPU compatible)

**Critical - Configuration & Logging:**
- pydantic 2.5.0+ - Data validation and serialization for DTOs
- pydantic-settings 2.1.0+ - Environment-based configuration management
- structlog 24.1.0+ - Structured JSON logging

**File Processing:**
- openpyxl 3.1.5+ - Excel file parsing and generation

**Type Stubs:**
- types-requests 2.31.0+ - Type hints for requests library

## Configuration

**Environment Management:**
- Settings loaded via Pydantic BaseSettings from `.env` files
- Environment variable prefix: `CCOP_` (all config keys prefixed with CCOP_)
- Configuration file: `src/infrastructure/config/settings.py`
- Example config template: `src/config/.env.example`

**Key Configuration Values:**
- `CCOP_OLLAMA_HOST` - Ollama API endpoint (default: http://localhost:11434)
- `CCOP_OLLAMA_TIMEOUT` - Request timeout in seconds (default: 300)
- `CCOP_MODEL_NAME` - Model identifier for inference (default: primus-reasoning)
- `CCOP_MODEL_HF_REPO` - HuggingFace repository (default: trendmicro-ailab/Llama-Primus-Reasoning)
- `CCOP_MODEL_QUANTIZATION` - GGUF quantization level (default: Q5_K_M)
- `CCOP_LOG_LEVEL` - Logging level (default: INFO)
- `CCOP_LOG_FORMAT` - Logging format: json or console (default: json)
- `CCOP_DEBUG` - Debug mode flag
- `CCOP_MOCK_MODE` - Use mock model gateway instead of real Ollama

**Build Configuration:**
- Black configuration in `src/pyproject.toml`: 100 char line length, Python 3.11 target
- Ruff configuration in `src/pyproject.toml`: 100 char line length, Python 3.11 target
- MyPy configuration in `src/pyproject.toml`: strict mode with exceptions for dependency-injector, huggingface_hub, openai
- pytest configuration in `src/pyproject.toml`: coverage targets all layers, HTML + XML + terminal reporting
- isort configuration in `src/pyproject.toml`: Black-compatible profile with 100 char line length

## Platform Requirements

**Development:**
- Python 3.10+ (tested up to 3.13)
- Poetry (package management)
- Ollama server running locally (for model inference)
- ~2GB disk space for model cache (~1.2GB for quantized Llama-Primus-Reasoning)

**Production/Deployment:**
- Same Python/Poetry requirements
- Ollama instance (local or remote)
- Read access to test case files in `ground-truth/phase-2/test-suite/`
- Write access to `results/evaluations/` for storing evaluation outputs

## Entry Points

**CLI Application:**
- Entry point: `src/presentation/cli/main.py` (Typer app)
- Installed command: `ccop-eval` (via Poetry scripts in `pyproject.toml`)
- Subcommands:
  - `ccop-eval setup` - Model setup and prerequisites checking
  - `ccop-eval evaluate` - Run evaluations on test cases
  - `ccop-eval report` - Generate evaluation reports

**Container/DI:**
- `src/infrastructure/config/container.py` - Dependency injection container (dependency-injector)
- Singleton pattern for settings, clients, and adapters
- Lazy initialization of external services

---

*Stack analysis: 2026-02-04*
