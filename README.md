# CCoP 2.0 Model Evaluation Framework

A Clean Architecture implementation for evaluating Large Language Models on Singapore's Cybersecurity Code of Practice (CCoP 2.0) standards for Critical Information Infrastructure.

## Project Overview

This framework provides baseline evaluation infrastructure for assessing the **Llama-Primus-Reasoning** model's performance on CCoP 2.0 compliance tasks across six benchmarks:

- **B1**: CCoP Interpretation Accuracy
- **B2**: Clause Citation Accuracy
- **B3**: Hallucination Rate
- **B4**: Singapore Terminology Accuracy
- **B5**: IT/OT Infrastructure Classification
- **B6**: Code Violation Detection

## Architecture

Built using **Clean Architecture (Hexagonal/Ports & Adapters)** with strict dependency rules:

```
src/
├── domain/            # Pure business logic (NO dependencies)
│   ├── entities/      # TestCase, EvaluationResult, Benchmark
│   ├── value_objects/ # BenchmarkType, DifficultyLevel, CCoPSection
│   ├── services/      # ScoringService, BenchmarkValidator
│   └── exceptions/    # Domain exceptions
│
├── application/       # Use cases & ports (depends on domain only)
│   ├── dtos/          # Data transfer objects
│   ├── ports/         # Interfaces (input & output ports)
│   └── use_cases/     # Business workflows
│
├── infrastructure/    # External adapters (implements ports)
│   ├── adapters/      # Ollama, repositories, logging
│   ├── external/      # HTTP clients
│   └── config/        # Settings, DI container
│
└── presentation/      # CLI interface
    └── cli/           # Typer-based commands
```

## Quick Start

### Prerequisites

- Python 3.10+
- Poetry
- Ollama (for local inference)

### Installation

```bash
# Navigate to src directory (all operations run from here)
cd src/

# Install dependencies
poetry install

# Check prerequisites
poetry run ccop-eval setup check
```

### Setup Model

```bash
# Option 1: Automated setup (CLI)
poetry run ccop-eval setup model \
  --repo trendmicro-ailab/Llama-Primus-Reasoning \
  --name primus-reasoning \
  --quantization Q5_K_M

# Option 2: Manual setup (shell scripts)
cd scripts/
./setup_ollama.sh
./convert_to_gguf.sh Q5_K_M
```

### Run Evaluation

```bash
# Evaluate on all benchmarks
poetry run ccop-eval evaluate run --model primus-reasoning

# Evaluate specific benchmarks
poetry run ccop-eval evaluate run --model primus-reasoning -b B1 -b B3

# Custom parameters
poetry run ccop-eval evaluate run \
  --model primus-reasoning \
  --temperature 0.7 \
  --benchmark B1 B2 B3
```

### Generate Reports

```bash
# JSON report
poetry run ccop-eval report generate --model primus-reasoning --format json

# Markdown report
poetry run ccop-eval report generate \
  --model primus-reasoning \
  --format markdown \
  --output reports/baseline-evaluation.md

# Quick summary
poetry run ccop-eval report summary --model primus-reasoning
```

## CLI Commands

### Setup Commands

```bash
# Check prerequisites
poetry run ccop-eval setup check

# Setup model
poetry run ccop-eval setup model [OPTIONS]
  --repo, -r TEXT         HuggingFace repository
  --name, -n TEXT         Model name for Ollama
  --quantization, -q TEXT Quantization type (Q4_K_M, Q5_K_M, Q6_K, Q8_0)
  --force, -f             Force reconversion
```

### Evaluate Commands

```bash
# Run evaluation
poetry run ccop-eval evaluate run [OPTIONS]
  --model, -m TEXT        Model name (required)
  --benchmark, -b TEXT    Benchmarks to run (can be specified multiple times)
  --test-id, -t TEXT      Specific test IDs
  --temperature FLOAT     Temperature (default: 0.7)
  --save/--no-save        Save results (default: save)
```

### Report Commands

```bash
# Generate report
poetry run ccop-eval report generate [OPTIONS]
  --model, -m TEXT        Model name (required)
  --format, -f TEXT       Report format (json/markdown/html/csv)
  --output, -o TEXT       Output file path
  --details/--no-details  Include detailed results

# Show summary
poetry run ccop-eval report summary --model MODEL_NAME
```

## Configuration

Configuration via environment variables (prefix: `CCOP_`):

```bash
# Ollama
CCOP_OLLAMA_HOST=http://localhost:11434
CCOP_OLLAMA_TIMEOUT=300

# Model
CCOP_MODEL_NAME=primus-reasoning
CCOP_MODEL_QUANTIZATION=Q5_K_M

# Paths
CCOP_TEST_CASES_DIR=../data/test-cases
CCOP_RESULTS_DIR=results/evaluations

# Logging
CCOP_LOG_LEVEL=INFO
CCOP_LOG_FORMAT=json

# Debug
CCOP_DEBUG=false
CCOP_MOCK_MODE=false
```

See `src/config/.env.example` for all options.

## Project Structure

```
studio-ssdlc/
├── src/                    # ALL SOURCE CODE
│   ├── pyproject.toml     # Poetry configuration
│   ├── config/            # Configuration files
│   ├── scripts/           # Setup scripts
│   ├── domain/            # Domain layer
│   ├── application/       # Application layer
│   ├── infrastructure/    # Infrastructure layer
│   └── presentation/      # CLI layer
│
├── data/
│   └── test-cases/        # JSONL test case files
│
├── tests/                 # Test files
├── docs/                  # Documentation
└── README.md              # This file
```

## Development

### Run Tests

```bash
cd src/
poetry run pytest
```

### Code Quality

```bash
# Format code
poetry run black .

# Lint
poetry run ruff check .

# Type check
poetry run mypy .
```

### Adding New Benchmarks

1. Create test cases in `data/test-cases/`
2. Update `domain/value_objects/benchmark_type.py`
3. Add scoring logic in `domain/services/scoring_service.py`
4. Update repository mappings in `infrastructure/adapters/repositories/`

## References

- [Project Paper](report/term1-mid/Primus-Fine-Tuning-CCOP2-SG-v2.0-SagarPratapSingh-1010736.md)
- [CCoP 2.0 Official Documentation](ccop-official/CCoP---Second-Edition_Revision-One.pdf)
- [Llama-Primus-Reasoning Model](https://huggingface.co/trendmicro-ailab/Llama-Primus-Reasoning)

## License

See project documentation for license details.

## Contributing

This is an academic research project. See CLAUDE.md for development guidelines.
