# Architecture

**Analysis Date:** 2026-02-04

## Pattern Overview

**Overall:** Clean Architecture (Hexagonal/Ports & Adapters)

**Key Characteristics:**
- Strict layer independence: Domain has zero dependencies on application/infrastructure
- Port & Adapter pattern: Interfaces defined in application, implementations in infrastructure
- Dependency injection via DI container: All dependencies wired in `infrastructure/config/container.py`
- Async/await throughout: All I/O operations are async for concurrency
- Entity-driven design: Aggregate roots maintain business invariants

## Layers

**Domain Layer:**
- Purpose: Pure business logic for CCoP 2.0 evaluation domain. Encapsulates what the system knows about evaluation, test cases, benchmarks, and scoring.
- Location: `src/domain/`
- Contains: Entities (TestCase, Benchmark, EvaluationResult, ModelResponse), value objects (BenchmarkType, DifficultyLevel, CCoPSection, EvaluationMetric), domain services (ScoringService, BenchmarkValidator), and exceptions
- Depends on: Nothing (stdlib only)
- Used by: Application layer exclusively

**Application Layer:**
- Purpose: Orchestration and business workflow. Defines what the system does through use cases that coordinate domain logic and infrastructure.
- Location: `src/application/`
- Contains: Use cases (EvaluateModelUseCase, SetupModelUseCase, GenerateReportUseCase), DTOs for data transfer, input ports (use case interfaces), output ports (repository/gateway abstractions)
- Depends on: Domain layer only
- Used by: Presentation layer, infrastructure adapters

**Infrastructure Layer:**
- Purpose: External integrations and technical implementation. Provides concrete implementations of abstract ports and handles all I/O.
- Location: `src/infrastructure/`
- Contains: Adapters (Ollama gateway, JSON repositories, logging adapters), external clients (Ollama, HuggingFace), configuration (Settings, DI container), model converters (GGUF quantization)
- Depends on: Application and domain layers
- Used by: Presentation layer to access use cases

**Presentation Layer:**
- Purpose: User interface and command handling. Currently CLI-only, translatable to API.
- Location: `src/presentation/`
- Contains: Typer-based CLI commands (setup, evaluate, report), formatters (Rich output), command handlers
- Depends on: Application layer (use cases), infrastructure (container)
- Used by: End users via command line

## Data Flow

**Model Evaluation Flow:**

1. **Initiation** (Presentation Layer)
   - User invokes: `poetry run ccop-eval evaluate run --model primus-reasoning --benchmarks B1 B2`
   - `src/presentation/cli/commands/evaluate.py::run()` parses arguments

2. **Setup** (Presentation → Application)
   - CLI resolves container: `get_container()` → wires all dependencies
   - Instantiates use case: `EvaluateModelUseCase(model_gateway, test_case_repository, result_repository, logger)`

3. **Load Test Cases** (Application → Infrastructure → Domain)
   - Use case calls: `test_case_repository.load_by_benchmark(benchmark_type)`
   - Repository (`JSONLTestCaseRepository`) discovers `.jsonl` files: `src/ground-truth/phase-*/test-suite/bX.jsonl`
   - Converts raw JSON to domain entities: `TestCase` objects with validation

4. **Generate Responses** (Application → Infrastructure → External)
   - Use case calls: `model_gateway.generate_response(prompt, model_name)`
   - Gateway (`OllamaGateway`) communicates with Ollama API (external service)
   - Returns: `ModelResponse` entity with generated text and metadata

5. **Score Responses** (Application → Domain)
   - Use case calls: `ScoringService.score_response(test_case, model_response)`
   - Service selects benchmark-specific scorer:
     - **Tier 1 (Fully Implemented)**: B1, B2, B3, B4, B5, B6
       - B1: Interpretation accuracy (semantic matching)
       - B2: Citation accuracy (citation extraction)
       - B3: Hallucination rate (fact verification)
       - B4: Terminology accuracy (Singapore terms)
       - B5: Classification accuracy (IT/OT domain classification)
       - B6: Violation detection (code violation patterns)
     - **Tier 2 (Reasoning Track)**: B8, B9, B11, B15, B17, B18, B19
       - Uses: Semantic similarity scoring via transformer embeddings
     - **Tier 3 (LLM Judge)**: B12, B13, B20
       - Uses: LLMJudgeService for subjective evaluation
   - Returns: `EvaluationMetric` list with scores and reasoning

6. **Persist Results** (Application → Infrastructure)
   - Use case calls: `result_repository.save(evaluation_result)`
   - Repository (`JSONResultRepository`) writes to: `src/results/evaluations/model_name_timestamp.json`
   - Persists: Full evaluation with metrics, test case data, and metadata

7. **Generate Summary** (Application → Presentation)
   - Use case aggregates results into: `EvaluationSummaryDTO`
   - CLI displays via Rich formatters: Summary table with pass rates by benchmark

**State Management:**

- **Immutable Entities**: TestCase, EvaluationResult, ModelResponse are immutable after construction (fail-fast validation in `__init__`)
- **Lazy Loading**: Test case repository caches loaded cases in `self._cache`
- **Stateless Services**: ScoringService is pure; no side effects
- **DI Container**: Singleton pattern for external clients (Ollama, HuggingFace) to maintain single connection
- **Repositories**: Act as collection abstractions with in-memory caching, backed by filesystem JSON

## Key Abstractions

**Benchmark (Aggregate Root):**
- Purpose: Groups test cases by benchmark category (B1-B21). Maintains cohesion of related evaluation tests.
- Examples: `src/domain/entities/benchmark.py`
- Pattern: Aggregate root with collection management. Provides filtering (by difficulty, domain), statistics, and weighted scoring calculation.

**TestCase (Entity):**
- Purpose: Represents a single CCoP 2.0 evaluation question with expected answer and criteria.
- Examples: `src/domain/entities/test_case.py`
- Pattern: Entity with identity (test_id format: Bxx-nnn). Validates on construction: test ID format, benchmark membership, question substance (≥50 chars), evaluation criteria presence. Provides business queries: `is_high_priority()`, `is_ot_specific()`, `is_it_specific()`.

**ModelResponse (Value Object):**
- Purpose: Immutable representation of model-generated output for a test case.
- Examples: `src/domain/entities/model_response.py`
- Pattern: Value object wrapping generated text, token counts, and inference metadata. Created by IModelGateway, validated for non-null content.

**EvaluationResult (Entity):**
- Purpose: Immutable record of a test case evaluation, linking test + response + metrics + scoring reasoning.
- Examples: `src/domain/entities/evaluation_result.py`
- Pattern: Entity referencing TestCase and ModelResponse, computed at evaluation time. Stores overall_score (0-1), metric details, and reasoning. Created by application use case, persisted by repository.

**IModelGateway (Output Port):**
- Purpose: Abstraction for LLM inference providers. Decouples application from specific implementation (Ollama, HuggingFace, Mock).
- Examples: `src/application/ports/output/i_model_gateway.py`
- Pattern: Abstract base class defining contract: `generate_response()`, `is_model_available()`, `list_available_models()`, `get_model_info()`. Infrastructure provides implementations: OllamaGateway, HuggingFaceGateway, MockModelGateway.

**ITestCaseRepository (Output Port):**
- Purpose: Abstraction for test case storage/loading. Currently filesystem-backed (JSONL), replaceable with database.
- Examples: `src/application/ports/output/i_test_case_repository.py`
- Pattern: Repository interface defining: `load_all()`, `load_by_benchmark()`, `load_by_test_id()`. Infrastructure provides JSONLTestCaseRepository with auto-discovery of benchmark files.

**IResultRepository (Output Port):**
- Purpose: Abstraction for evaluation result persistence.
- Examples: `src/application/ports/output/i_result_repository.py`
- Pattern: Repository interface defining: `save()`, `load_by_model()`, `load_by_test_id()`. Infrastructure provides JSONResultRepository with structured JSON output.

**ScoringService (Domain Service):**
- Purpose: Stateless scoring logic for benchmark-specific evaluation. Delegates to tier-specific scorers.
- Examples: `src/domain/services/scoring_service.py`
- Pattern: Static methods mapping benchmark type to scoring function. Each function encapsulates domain rules for that benchmark tier. Returns EvaluationMetric list.

**EvaluationMetric (Value Object):**
- Purpose: Immutable representation of a single evaluation dimension (accuracy, completeness, etc.) with score and rationale.
- Examples: `src/domain/value_objects/evaluation_metric.py`
- Pattern: Value object with metric_type, score (0-1), rationale, and evidence. Factory functions for common metrics (accuracy_metric, hallucination_rate_metric, etc.).

## Entry Points

**CLI Command: evaluate run:**
- Location: `src/presentation/cli/commands/evaluate.py::run()`
- Triggers: User runs `poetry run ccop-eval evaluate run --model X --benchmarks B1 B2`
- Responsibilities: Parse CLI args, resolve DI container, instantiate EvaluateModelUseCase, execute async, format output

**CLI Command: setup model:**
- Location: `src/presentation/cli/commands/setup.py::model()`
- Triggers: User runs `poetry run ccop-eval setup model --repo X --name Y --quantization Z`
- Responsibilities: Download model from HuggingFace, convert to GGUF quantization, import to Ollama

**CLI Command: report generate:**
- Location: `src/presentation/cli/commands/report.py::generate()`
- Triggers: User runs `poetry run ccop-eval report generate --model X --format json`
- Responsibilities: Load results from filesystem, aggregate statistics, generate report in requested format

**Async Main Loop:**
- Location: `src/presentation/cli/main.py::main()`
- Triggers: All CLI commands dispatched through this callback
- Responsibilities: Initialize container, enable debug/verbose modes, inject context into commands

## Error Handling

**Strategy:** Domain exceptions bubble up with context added by application layer. Infrastructure catches and logs.

**Patterns:**

- **Domain Exceptions**: `src/domain/exceptions/`
  - `ValidationError`: Raised during entity construction when invariants violated. Contains field name and detail message.
  - `EvaluationError`: Raised during evaluation if test case invalid or response generation fails.
  - Both include full context for debugging.

- **Application Handling**: Use cases catch exceptions, add context, re-raise or handle gracefully.
  - Example: `EvaluateModelUseCase` catches `ModelGatewayError`, logs with test case ID, continues evaluation.

- **Infrastructure Handling**: Adapters log and convert exceptions to domain exceptions.
  - Example: Ollama connection failure → OllamaGateway logs error → raises EvaluationError

- **Presentation Handling**: CLI commands catch exceptions, display user-friendly messages via Rich console.
  - Example: ModelNotFoundError → "Model 'primus-reasoning' not found. Run 'setup model' first."

## Cross-Cutting Concerns

**Logging:**
- Abstraction: `ILogger` port in `src/application/ports/output/i_logger.py`
- Implementations:
  - `ConsoleLogger`: Rich console output for CLI (development)
  - `StructlogAdapter`: JSON structured logging (production)
- Selected at container wiring via config: `log_format` setting
- Usage: Injected into all use cases and adapters; logs include structured context (model name, benchmark type, test count)

**Validation:**
- **Entity-level**: TestCase validates test ID format, question substance, evaluation criteria presence on construction (fail-fast)
- **Service-level**: BenchmarkValidator checks test case consistency, ScoringService validates benchmark type before scoring
- **Repository-level**: JSONLTestCaseRepository validates JSON schema during load, raises ValidationError on malformed data

**Authentication:**
- None currently. External clients (Ollama, HuggingFace) use environment variables (API keys in .env)
- HuggingFace client uses: `HUGGINGFACE_TOKEN` from settings
- Ollama: No auth; local service assumed

**Configuration:**
- Centralized in: `src/infrastructure/config/settings.py` (dataclass with defaults from environment)
- Settings include: Ollama host/port, model cache dir, test cases dir, results dir, log level/format
- Environment variable naming: `CCOP_<SETTING>` (e.g., `CCOP_OLLAMA_HOST`, `CCOP_LOG_LEVEL`)

---

*Architecture analysis: 2026-02-04*
