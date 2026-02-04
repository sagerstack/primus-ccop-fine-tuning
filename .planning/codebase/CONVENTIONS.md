# Coding Conventions

**Analysis Date:** 2026-02-04

## Naming Patterns

**Files:**
- Module files: `snake_case.py` (e.g., `scoring_service.py`, `test_case.py`)
- Test files: `test_*.py` (e.g., `test_scoring_service_option_a.py`)
- Exception files: `*_error.py` (e.g., `validation_error.py`)
- Configuration files: `settings.py`, `container.py`

**Classes:**
- Entity classes: `PascalCase` (e.g., `TestCase`, `ModelResponse`, `EvaluationResult`)
- DTO classes: `PascalCase` with `DTO` suffix (e.g., `TestCaseDTO`, `EvaluationRequestDTO`)
- Service classes: `PascalCase` with `Service` suffix (e.g., `ScoringService`, `SemanticSimilarityService`)
- Exception classes: `PascalCase` with `Error` suffix (e.g., `ValidationError`)
- Repository/Gateway classes: `PascalCase` with type suffix (e.g., `JSONLTestCaseRepository`, `OllamaGateway`)

**Functions and Methods:**
- Method names: `snake_case` (e.g., `score_response`, `is_high_priority`, `get_passing_threshold`)
- Private methods: Prefix with `_` (e.g., `_validate`, `_is_valid_test_id_format`, `_score_b1_interpretation`)
- Static methods: Same as regular methods, prefixed with `@staticmethod`
- Boolean methods: Start with `is_`, `has_`, or `contains_` (e.g., `is_high_priority`, `contains_hallucination_indicators`)

**Variables:**
- Local variables: `snake_case` (e.g., `test_case`, `response_content`, `accuracy_metric`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`, `PASSING_THRESHOLD`)
- Private attributes: Prefix with `_` (e.g., `self._test_id`, `self._benchmark_type`)
- Properties: `snake_case` - used to expose private attributes (e.g., `@property def test_id`)

**Types:**
- Type hints: Always included in function signatures (e.g., `def score_response(test_case: TestCase, response: ModelResponse) -> List[EvaluationMetric]`)
- Union types: Use `|` syntax for Python 3.10+ (e.g., `dict[str, Any] | None`)
- Generic collections: Use built-in types with brackets (e.g., `list[str]`, `dict[str, Any]`)

## Code Style

**Formatting:**
- Tool: Black (formatter), isort (import sorting), Ruff (linter)
- Line length: 100 characters (configured in `pyproject.toml`)
- Target version: Python 3.11+

**Linting:**
- Tool: Ruff (`ruff` config in `pyproject.toml`)
- Enabled rules: E (pycodestyle errors), W (pycodestyle warnings), F (pyflakes), I (isort), C (comprehensions), B (bugbear), UP (pyupgrade)
- Type checking: MyPy with strict settings (`mypy` config in `pyproject.toml`)

**Indentation:**
- 4 spaces per indentation level

## Import Organization

**Order:**
1. Standard library imports
2. Third-party imports
3. Domain/application layer imports
4. Infrastructure layer imports
5. Presentation layer imports

**Example from `src/domain/services/scoring_service.py`:**
```python
import re
from typing import Any, List

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.llm_judge_service import LLMJudgeService
from domain.services.semantic_similarity_service import SemanticSimilarityService
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.evaluation_metric import (
    EvaluationMetric,
    accuracy_metric,
)
```

**Path Aliases:**
- First party modules defined in `pyproject.toml`: `domain`, `application`, `infrastructure`, `presentation`
- isort configured with profile `black` and skip_gitignore

## Error Handling

**Patterns:**
- Domain-level validation: Raise `ValidationError` from `domain.exceptions.validation_error`
- Domain validation occurs in `__init__` or `_validate()` methods (fail-fast pattern)
- Validation errors include `field` parameter for detailed feedback

**Example from `src/domain/entities/test_case.py`:**
```python
def _validate(self) -> None:
    """Enforce all business rules and invariants."""
    if not self._is_valid_test_id_format():
        raise ValidationError(
            f"test_id must match format Bxx-nnn (e.g., B1-001, B10-042), got '{self._test_id}'",
            field="test_id"
        )
```

## Logging

**Framework:** structlog (configured in `pyproject.toml`)

**Patterns:**
- Logger injected via DI (dependency injector)
- Logger interface defined in `application/ports/output/i_logger.py`
- Implementations: `infrastructure/adapters/logging/console_logger.py`
- Use structured logging with context fields

**Example:**
```python
self._logger.info(
    "evaluation_started",
    test_id=test_case.test_id,
    model_name=model.name,
    phase=self._settings.evaluation_phase
)
```

## Comments

**When to Comment:**
- Complex business logic (e.g., benchmark-specific scoring rules)
- Non-obvious validation rules
- Workarounds or temporary solutions
- References to external specifications (CCoP 2.0 sections, etc.)
- Avoid comments for self-documenting code

**JSDoc/Docstrings:**
- Google-style docstrings for all public classes and methods
- Includes: brief description, Args, Returns, Raises sections
- Private methods: Brief docstring explaining business rule

**Example from `src/domain/entities/test_case.py`:**
```python
def _validate(self) -> None:
    """
    Enforce all business rules and invariants.

    Business rules:
    1. test_id must match format Bxx-nnn (e.g., B1-001, B10-042)
    2. test_id prefix must match benchmark_type
    3. question must be substantial (>= 50 chars)
    4. expected_response cannot be empty
    5. evaluation_criteria must be non-empty dict
    """
```

## Function Design

**Size:** Methods typically 20-50 lines; domain services use `@staticmethod` for reusable logic

**Parameters:**
- Use dataclasses/value objects instead of multiple primitives (e.g., pass `TestCase` instead of individual fields)
- Maximum 4-5 parameters; group related parameters into objects
- All parameters explicitly typed

**Return Values:**
- Explicit return types always specified
- Return domain objects or value objects, not raw dicts/lists
- Use `list[str]` for collections, `dict[str, Any]` for flexible dicts, `Optional[Type]` for nullable returns

**Example from `src/domain/services/scoring_service.py`:**
```python
@staticmethod
def score_response(
    test_case: TestCase,
    response: ModelResponse
) -> List[EvaluationMetric]:
    """Business rule: Score a model response based on benchmark type."""
```

## Module Design

**Exports:**
- Explicit `__all__` lists in `__init__.py` for public API
- Domain layer exports: entities, value objects, exceptions, services
- Application layer exports: use cases, DTOs, ports
- Infrastructure layer: No exports to domain

**Barrel Files:**
- Used in `application/__init__.py` to simplify imports
- Pattern: `from .ports.input import *; from .ports.output import *`

**Architectural Layers:**
- `domain/`: Pure Python, no external dependencies (except standard library)
  - Entities: `entities/test_case.py`, `entities/model_response.py`
  - Value Objects: `value_objects/benchmark_type.py`, `value_objects/difficulty_level.py`
  - Services: `services/scoring_service.py` (stateless, domain logic)
  - Exceptions: `exceptions/validation_error.py`

- `application/`: Orchestration, DTOs, ports (interfaces)
  - DTOs: `dtos/test_case_dto.py`, `dtos/evaluation_result_dto.py`
  - Use Cases: `use_cases/evaluate_model.py`, `use_cases/setup_model.py`
  - Ports: `ports/input/` (input interfaces), `ports/output/` (output interfaces)

- `infrastructure/`: External service adapters, configuration
  - Adapters: `adapters/models/ollama_gateway.py`, `adapters/repositories/jsonl_test_case_repository.py`
  - External: `external/ollama_client.py` (third-party clients)
  - Config: `config/settings.py`, `config/container.py` (DI container)

- `presentation/`: CLI layer
  - CLI: `cli/main.py`, `cli/commands/evaluate.py`

## Type Checking

**Configuration:**
- MyPy strict mode enabled: `disallow_untyped_defs = true`
- Overrides for third-party libraries: `dependency_injector.*`, `huggingface_hub.*`, `openai.*`
- All function signatures must have type hints

**Example from `src/domain/entities/test_case.py`:**
```python
def __init__(
    self,
    test_id: str,
    benchmark_type: BenchmarkType,
    section: CCoPSection,
    clause_reference: str,
    difficulty: DifficultyLevel,
    question: str,
    expected_response: str,
    evaluation_criteria: Dict[str, Any],
    metadata: Dict[str, Any] | None = None,
    key_facts: list[str] | None = None,
    expected_label: str | None = None,
    forbidden_claims: list[str] | None = None,
) -> None:
```

## Testing

**Test File Locations:**
- Unit tests: `tests/domain/`, `tests/application/`, `tests/infrastructure/`
- Integration tests: `tests/integration/`
- Shared fixtures: `tests/conftest.py`

**Test Class Pattern:**
```python
class TestSemanticSimilarityPenalty:
    """Test semantic similarity penalty for low scores (Option A fix)."""

    def test_semantic_similarity_high_score_no_penalty(self):
        """High semantic similarity (>= 0.70) should not be penalized."""
```

---

*Convention analysis: 2026-02-04*
