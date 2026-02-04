# Codebase Structure

**Analysis Date:** 2026-02-04

## Directory Layout

```
/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/
├── src/                           # Main application source code
│   ├── domain/                    # Pure business logic (no dependencies)
│   │   ├── entities/              # Aggregate roots: TestCase, Benchmark, EvaluationResult, ModelResponse
│   │   ├── value_objects/         # BenchmarkType, DifficultyLevel, CCoPSection, EvaluationMetric
│   │   ├── services/              # ScoringService, BenchmarkValidator, evaluation-specific scorers
│   │   └── exceptions/            # ValidationError, EvaluationError
│   │
│   ├── application/               # Use cases & ports (depends on domain only)
│   │   ├── dtos/                  # Data transfer objects for input/output
│   │   ├── ports/
│   │   │   ├── input/             # Input port interfaces (use case contracts)
│   │   │   └── output/            # Output port interfaces (repository, gateway, logger abstractions)
│   │   └── use_cases/             # EvaluateModelUseCase, SetupModelUseCase, GenerateReportUseCase
│   │
│   ├── infrastructure/            # External integrations & implementations
│   │   ├── adapters/              # Concrete implementations of ports
│   │   │   ├── models/            # OllamaGateway, MockModelGateway, HuggingFaceGateway
│   │   │   ├── repositories/      # JSONLTestCaseRepository, JSONResultRepository
│   │   │   ├── logging/           # ConsoleLogger, StructlogAdapter
│   │   │   └── converters/        # GGUFConverter for model quantization
│   │   ├── external/              # External service clients (Ollama, HuggingFace)
│   │   └── config/                # Settings (dataclass), DI container, initialization
│   │
│   ├── presentation/              # User interface layer
│   │   ├── cli/
│   │   │   ├── commands/          # evaluate.py, setup.py, report.py (Typer command groups)
│   │   │   ├── formatters/        # Rich output formatters
│   │   │   └── main.py            # CLI app entry point
│   │   └── __init__.py
│   │
│   ├── scripts/                   # Utility scripts (model setup, data generation)
│   ├── results/                   # Output directory for evaluation results (generated)
│   ├── logs/                      # Log files (generated)
│   └── __init__.py
│
├── tests/                         # Test suite (external tests directory)
│   ├── conftest.py                # Shared pytest fixtures and configuration
│   ├── fixtures/                  # Test data files
│   ├── domain/                    # Domain layer unit tests
│   │   └── services/              # ScoringService, BenchmarkValidator tests
│   ├── integration/               # Integration tests (e2e evaluation)
│   └── test_e2e_evaluation.py     # Full pipeline end-to-end test
│
├── ground-truth/                  # Evaluation test cases & ground truth data
│   ├── phase-1/                   # Baseline phase test cases
│   ├── phase-2/                   # Fine-tuned phase test cases
│   │   ├── test-suite/            # bX.jsonl files (test cases by benchmark)
│   │   ├── expert-validation/     # Expert review results
│   │   └── archive/               # Previous versions (skip these)
│   └── README.md
│
├── ccop-official/                 # Official CCoP 2.0 regulatory documents
│   ├── CCoP---Second-Edition_Revision-One.pdf
│   ├── supplementary/             # Auditing, threat modeling, risk assessment guides
│   └── references/                # Implementation guides
│
├── docs/                          # Project documentation
│   ├── phase1/                    # Phase 1 planning documents
│   └── phase2/                    # Phase 2 planning documents
│
├── models/                        # Downloaded model artifacts (generated)
├── report/                        # Generated reports and presentations
├── research/                      # Research papers and archived work
├── .planning/                     # GSD planning documents (generated)
│   └── codebase/                  # This directory: ARCHITECTURE.md, STRUCTURE.md, etc.
│
├── README.md                      # Quick start guide
├── CLAUDE.md                      # Project context and references
└── .gitignore
```

## Directory Purposes

**src/domain/:**
- Purpose: Business logic encapsulation. Zero external dependencies. Contains core concepts: test cases, benchmarks, evaluation results.
- Contains: Python modules organized by domain concept (entities, value objects, services, exceptions)
- Key files: `benchmark.py`, `test_case.py`, `evaluation_result.py`, `model_response.py`

**src/domain/entities/:**
- Purpose: Aggregate roots maintaining business invariants
- Key files:
  - `benchmark.py`: Collection of test cases with filtering, weighting, statistics
  - `test_case.py`: CCoP test question with expected answer and evaluation criteria
  - `evaluation_result.py`: Immutable record of test evaluation with metrics
  - `model_response.py`: LLM-generated response with metadata

**src/domain/value_objects/:**
- Purpose: Immutable concepts used by entities (enums, categorizations)
- Key files:
  - `benchmark_type.py`: Enum-like for B1-B21 benchmark categories
  - `difficulty_level.py`: EASY, MEDIUM, HIGH, CRITICAL with priority scoring
  - `ccop_section.py`: CCoP regulation sections (Section 3, 4, 5, 6, etc.)
  - `evaluation_metric.py`: Metric types with factory functions for domain metrics
  - `evaluation_category.py`: Evaluation tier classification (Tier 1, 2, 3)
  - `evaluation_tier.py`: Maps tiers to benchmark sets

**src/domain/services/:**
- Purpose: Business logic that doesn't naturally belong to a single entity
- Key files:
  - `scoring_service.py`: Benchmark-specific scoring delegates (B1-B6 fully implemented, B8-B21 reasoning/LLM judge)
  - `benchmark_validator.py`: Cross-test-case validation rules
  - `llm_judge_service.py`: Subjective evaluation using another LLM
  - `semantic_similarity_service.py`: Semantic matching for reasoning benchmarks
  - `human_validation_service.py`: Human review scoring integration

**src/application/:**
- Purpose: Orchestration of domain logic into business workflows
- Contains: DTOs for data marshaling, port interfaces, use cases

**src/application/dtos/:**
- Purpose: Transfer objects for crossing layer boundaries (not domain entities)
- Key files:
  - `evaluation_request_dto.py`: Input parameters for evaluation (model_name, benchmarks, etc.)
  - `evaluation_result_dto.py`: Output summary with scores and metadata
  - `test_case_dto.py`: Serialized test case for API responses

**src/application/ports/input/:**
- Purpose: Interfaces that presentation layer calls (input boundaries)
- Key files:
  - `i_evaluate_model_use_case.py`: Contract for model evaluation workflow
  - `i_setup_model_use_case.py`: Contract for model download/setup
  - `i_generate_report_use_case.py`: Contract for report generation

**src/application/ports/output/:**
- Purpose: Interfaces that use cases depend on (output boundaries, implemented by infrastructure)
- Key files:
  - `i_model_gateway.py`: LLM inference abstraction
  - `i_test_case_repository.py`: Test case loading abstraction
  - `i_result_repository.py`: Evaluation result persistence abstraction
  - `i_logger.py`: Logging abstraction
  - `i_model_converter.py`: Model format conversion (GGUF quantization)

**src/application/use_cases/:**
- Purpose: Business workflows orchestrating domain + infrastructure
- Key files:
  - `evaluate_model.py`: Load test cases, generate responses, score, aggregate results, persist
  - `setup_model.py`: Download model, quantize to GGUF, import to Ollama
  - `generate_report.py`: Load results, aggregate statistics, format for JSON/Markdown/Excel output

**src/infrastructure/:**
- Purpose: External integrations, configuration, and dependency injection
- Contains: Adapters, external clients, configuration

**src/infrastructure/config/:**
- Purpose: Application configuration and dependency wiring
- Key files:
  - `settings.py`: Dataclass with all configurable parameters (Ollama host, model cache dir, etc.)
  - `container.py`: DI container wiring all dependencies via dependency-injector library

**src/infrastructure/adapters/:**
- Purpose: Concrete implementations of abstract ports

**src/infrastructure/adapters/models/:**
- Purpose: LLM inference provider implementations
- Key files:
  - `ollama_gateway.py`: Ollama local inference (primary for development)
  - `mock_gateway.py`: Mock responses for testing
  - `huggingface_gateway.py`: HuggingFace Inference API (future)

**src/infrastructure/adapters/repositories/:**
- Purpose: Test case and result persistence implementations
- Key files:
  - `jsonl_test_case_repository.py`: Auto-discovers bX.jsonl files, caches in memory
  - `json_result_repository.py`: Writes evaluation results to JSON files with timestamps

**src/infrastructure/adapters/logging/:**
- Purpose: Logging implementations
- Key files:
  - `console_logger.py`: Rich-formatted console output
  - `structlog_adapter.py`: JSON structured logging

**src/infrastructure/adapters/converters/:**
- Purpose: Data format conversions
- Key files:
  - `gguf_converter.py`: HuggingFace SafeTensors → GGUF quantization

**src/infrastructure/external/:**
- Purpose: HTTP clients for external services
- Key files:
  - `ollama_client.py`: Ollama REST API client wrapper
  - `huggingface_client.py`: HuggingFace model download client

**src/presentation/cli/:**
- Purpose: Command-line interface
- Key files:
  - `main.py`: Typer app initialization with subcommand registration
  - `commands/evaluate.py`: `evaluate run` command
  - `commands/setup.py`: `setup model` / `setup check` commands
  - `commands/report.py`: `report generate` command
  - `formatters/`: Rich output table/summary formatting

**src/scripts/:**
- Purpose: Utility scripts for development workflows
- Usage: Data generation, model setup

**src/results/ (generated):**
- Purpose: Output directory for evaluation results
- Structure: `evaluations/model_name_YYYYMMDD_HHMMSS.json`

**src/logs/ (generated):**
- Purpose: Log output files (when structured logging enabled)

**tests/:**
- Purpose: Comprehensive test suite
- Key files:
  - `conftest.py`: Shared pytest fixtures (sample test cases, responses, results)
  - `test_e2e_evaluation.py`: Full evaluation pipeline test
  - `domain/services/test_*.py`: Domain service unit tests
  - `integration/test_tier*_e2e.py`: Tier-specific end-to-end tests

**ground-truth/:**
- Purpose: Evaluation test case datasets organized by phase
- Structure:
  - `phase-1/`: Baseline (15%) test cases
  - `phase-2/test-suite/`: Fine-tuned (50%) test cases in bX.jsonl format
    - `b1.jsonl`: B1 interpretation tests
    - `b2.jsonl`: B2 citation tests
    - ... (one file per benchmark)
  - `phase-2/expert-validation/`: Expert review results
  - `phase-2/archive/`: Previous versions (skip)

## Key File Locations

**Entry Points:**

- `src/presentation/cli/main.py`: CLI application entry point (Typer app)
- `src/presentation/cli/commands/evaluate.py`: Evaluate command implementation
- `src/presentation/cli/commands/setup.py`: Setup command implementation
- `src/presentation/cli/commands/report.py`: Report generation command

**Configuration:**

- `src/infrastructure/config/settings.py`: All configuration parameters
- `src/infrastructure/config/container.py`: Dependency injection wiring
- `src/domain/value_objects/evaluation_tier.py`: Tier definitions (maps tiers to benchmarks)

**Core Logic:**

- `src/domain/services/scoring_service.py`: Main scoring orchestration (delegates to tier-specific scorers)
- `src/domain/services/benchmark_validator.py`: Test case validation rules
- `src/application/use_cases/evaluate_model.py`: Evaluation workflow

**Data Access:**

- `src/infrastructure/adapters/repositories/jsonl_test_case_repository.py`: Test case loading
- `src/infrastructure/adapters/repositories/json_result_repository.py`: Result persistence
- `ground-truth/phase-2/test-suite/bX.jsonl`: Actual test case data files

**External Integration:**

- `src/infrastructure/adapters/models/ollama_gateway.py`: Ollama inference
- `src/infrastructure/external/ollama_client.py`: Ollama REST client

**Testing:**

- `tests/conftest.py`: Shared test fixtures
- `tests/test_e2e_evaluation.py`: End-to-end pipeline test

## Naming Conventions

**Files:**

- Entities & Aggregates: `snake_case.py` (e.g., `test_case.py`, `model_response.py`)
- Interfaces: `i_<name>.py` prefix (e.g., `i_model_gateway.py`, `i_logger.py`)
- Adapters: `<type>_<impl>.py` (e.g., `ollama_gateway.py`, `json_result_repository.py`)
- Test files: `test_<module>.py` or `test_<module>_<aspect>.py` (e.g., `test_scoring_service_option_a.py`)
- DTOs: `<concept>_dto.py` (e.g., `evaluation_request_dto.py`)

**Directories:**

- Feature domains: `<plural>` (e.g., `entities/`, `services/`, `repositories/`)
- Layer names: Lowercase (e.g., `domain/`, `application/`, `infrastructure/`, `presentation/`)
- Package groups: `adapters/`, `ports/`, `external/`, `config/`

**Classes & Functions:**

- Classes: `PascalCase` (e.g., `TestCase`, `EvaluateModelUseCase`, `OllamaGateway`)
- Private methods: `_snake_case` prefix (e.g., `_validate()`, `_score_b1_interpretation()`)
- Public methods: `snake_case` (e.g., `generate_response()`, `load_by_benchmark()`)
- Constants: `UPPER_SNAKE_CASE` (when used in value objects as enum patterns)
- Dataclass fields: `snake_case` (e.g., `test_id`, `benchmark_type`, `expected_response`)

## Where to Add New Code

**New Benchmark Scoring:**
- Domain service method: `src/domain/services/scoring_service.py::_score_bX_<name>()`
  - Add to benchmark_scorers dict mapping benchmark type to scorer function
  - Return: `List[EvaluationMetric]`
  - Keep stateless; no external calls in domain service
- External evaluator: If needs LLM call, implement in `src/infrastructure/adapters/llm_judge_service.py` and call from domain scorer

**New Repository/Data Access:**
- Interface: Add method to `src/application/ports/output/i_<repository>.py`
- Implementation: Add method to `src/infrastructure/adapters/repositories/<repo_impl>.py`
- Example: Adding filtering by metadata
  - Interface: `async def load_by_metadata(key: str, value: any) -> List[TestCase]`
  - Implementation: Scan loaded data, filter by metadata dict

**New CLI Command:**
- Command file: Create `src/presentation/cli/commands/<command_name>.py`
- Use case: Ensure use case exists in `src/application/use_cases/<action>.py`
- Registration: Add to typer app in `src/presentation/cli/main.py`: `app.add_typer(my_app, name="<command>")`
- Pattern: Follow existing commands (evaluate.py, setup.py, report.py)

**New Entity/Value Object:**
- Domain entity: Create `src/domain/entities/<entity_name>.py`
  - Include validation in `__init__`
  - Use value objects for typed fields
  - Add business methods (queries, mutations)
  - Export in `src/domain/__init__.py`
- Value object: Create `src/domain/value_objects/<concept>.py`
  - Make immutable (no setters)
  - Implement `__eq__`, `__hash__` if used as dict keys
  - Export in `src/domain/__init__.py`

**New External Service Integration:**
- Client: Create `src/infrastructure/external/<service>_client.py`
  - Handle HTTP, auth, error conversion
  - Return domain types, not raw responses
- Gateway: Create `src/infrastructure/adapters/models/<service>_gateway.py` (if model-related)
  - Implement abstract port from `src/application/ports/output/`
  - Use client from external/
- Container: Wire in `src/infrastructure/config/container.py`
  - Add provider: `<service>_client = providers.Singleton(...)`
  - Inject into gateway/adapter

**New Use Case:**
- Location: `src/application/use_cases/<action>.py`
- Implement: Inherit from input port interface `src/application/ports/input/i_<action>_use_case.py`
- Dependencies: Inject via constructor (use case is responsible for coordinating)
- Return: DTO from `src/application/dtos/`
- Pattern: Load → transform → persist / aggregate → return summary

**New Test:**
- Unit tests: `src/tests/<layer>/test_<module>.py` for domain/application
  - Use fixtures from `tests/conftest.py`
- Integration tests: `tests/integration/test_<scenario>_e2e.py`
  - Use real infrastructure (file system, may need mock Ollama)
- Pattern: Arrange → act → assert; use pytest fixtures for setup

## Special Directories

**src/results/ (generated):**
- Purpose: Output directory for evaluation results
- Generated: Yes (created by application)
- Committed: No (ignored in .gitignore)
- Contents: JSON files with evaluation metadata, test results, metrics
- Naming: `<model_name>_<timestamp>.json`

**src/logs/ (generated):**
- Purpose: Log output when structured logging enabled
- Generated: Yes (created by adapters)
- Committed: No (ignored in .gitignore)
- Contents: Application logs in JSON or text format

**src/htmlcov/ (generated):**
- Purpose: Test coverage report (HTML)
- Generated: Yes (by pytest --cov)
- Committed: No (ignored)

**ground-truth/phase-*/test-suite/ (committed):**
- Purpose: Test case source data
- Generated: No (authored by domain experts)
- Committed: Yes (part of evaluation ground truth)
- Format: JSONL, one test case per line

**ground-truth/phase-*/expert-validation/ (committed):**
- Purpose: Expert review results and validation data
- Generated: No (created by expert review process)
- Committed: Yes (historical record)
- Format: Excel spreadsheets, JSON

**ground-truth/phase-*/archive/ (committed but ignored):**
- Purpose: Previous versions, obsolete data
- Generation note: Not part of current evaluation
- Skip: These should not be processed in current pipelines

---

*Structure analysis: 2026-02-04*
