# Testing Patterns

**Analysis Date:** 2026-02-04

## Test Framework

**Runner:**
- pytest 7.4.0+ (configured in `src/pyproject.toml`)
- Config file: `src/pyproject.toml` under `[tool.pytest.ini_options]`

**Assertion Library:**
- Built-in pytest assertions (e.g., `assert x == y`)
- No custom assertion library

**Run Commands:**
```bash
# From src/ directory
pytest ../tests                          # Run all tests
pytest ../tests -v                       # Verbose output
pytest ../tests --cov=domain --cov=application --cov=infrastructure --cov=presentation
                                         # Run with coverage
pytest ../tests -k "test_model_response" # Run specific test pattern
pytest ../tests -m "asyncio"             # Run async tests
pytest ../tests --tb=short               # Short traceback format
```

## Test File Organization

**Location:**
- Tests in `tests/` directory (parallel to `src/`)
- Subdirectory structure mirrors source: `tests/domain/`, `tests/application/`, `tests/infrastructure/`
- Integration tests: `tests/integration/`
- End-to-end tests: `tests/` root level with `test_e2e_*.py`

**Naming:**
- Test modules: `test_*.py` (e.g., `test_scoring_service_option_a.py`)
- Test classes: `Test*` (e.g., `TestSemanticSimilarityPenalty`, `TestTier2SemanticSimilarityE2E`)
- Test methods: `test_*` (e.g., `test_semantic_similarity_high_score_no_penalty`)

**Structure:**
```
tests/
├── conftest.py                                    # Shared fixtures
├── test_model_response.py                         # Entity tests
├── test_e2e_evaluation.py                         # E2E integration tests
├── test_repository_basics.py                      # Repository tests
├── domain/
│   ├── services/
│   │   ├── test_llm_judge_service.py
│   │   ├── test_semantic_similarity_service.py
│   │   └── test_scoring_service_option_a.py
│   └── ...
├── application/
│   └── use_cases/
│       └── test_evaluate_model_metadata.py
├── infrastructure/
│   └── adapters/
│       └── repositories/
│           └── test_json_result_repository.py
└── integration/
    ├── test_tier2_semantic_similarity_e2e.py
    └── test_tier3_llm_judge_e2e.py
```

## Test Structure

**Suite Organization:**

From `tests/conftest.py` - shared fixtures pattern:
```python
@pytest.fixture
def sample_b1_test_case() -> TestCase:
    """Create a sample B1 test case for testing."""
    return TestCase(
        test_id="B1-001",
        benchmark_type=BenchmarkType("B1_CCoP_Applicability_Scope"),
        section=CCoPSection("Cybersecurity Act 2018 Part 3"),
        clause_reference="Section 7(1)",
        difficulty=DifficultyLevel.MEDIUM,
        question="What are the criteria that the Commissioner uses to designate a computer or computer system as Critical Information Infrastructure (CII) under the Cybersecurity Act 2018?",
        expected_response="According to Section 7(1)...",
        evaluation_criteria={
            "accuracy": "Must correctly identify both criteria",
            "completeness": "Should mention written notice requirement",
        },
        metadata={
            "domain": "IT/OT",
            "criticality": "critical",
        }
    )
```

**Patterns:**

- Setup pattern: Fixtures injected as function parameters
- Class-based organization: Group related tests in test classes (e.g., `TestSemanticSimilarityPenalty`)
- Fixture reuse: Common fixtures in `tests/conftest.py` for domain entities, responses, metrics
- Teardown: No explicit teardown needed (pytest cleans up fixtures automatically)
- Assertion pattern: Direct assertions with descriptive test names

From `tests/test_model_response.py`:
```python
class TestModelResponse:
    """Tests for ModelResponse entity - implemented functionality only."""

    def test_extract_citations(self):
        """CRITICAL: Extract section citations from response text."""
        response = ModelResponse(
            content="According to Section 13.1 and Section 9.2, organizations must...",
            model_name="test-model",
            tokens_used=20,
            latency_ms=1000,
        )

        citations = response.extract_citations()
        assert "13.1" in citations
        assert "9.2" in citations
        assert len(citations) == 2
```

## Mocking

**Framework:** pytest-mock (pytest plugin providing `mocker` fixture)

**Patterns:**

From `tests/test_e2e_evaluation.py` - mock external services:
```python
# Create mock Ollama client
mock_ollama_client = Mock(spec=OllamaClient)
mock_ollama_client.list_models = AsyncMock(return_value=[
    {"name": "primus-reasoning:latest"}
])
mock_ollama_client.generate = AsyncMock(return_value={
    "response": "According to Section 7(1)...",
    "eval_count": 150,
    "eval_duration": 5000000000,
    "total_duration": 6000000000
})

# Inject into gateway
model_gateway = OllamaGateway(
    client=mock_ollama_client,
    logger=logger
)
```

**What to Mock:**
- External service clients (OllamaClient, HuggingFace API)
- File I/O operations (repositories that read/write files)
- Network calls (HTTP clients)
- Database operations (if applicable)

**What NOT to Mock:**
- Domain entities and value objects (test the real implementations)
- Domain services and business logic (test actual scoring, validation)
- Repository interfaces (test actual file implementations in local tests)
- DTOs and validation (test real Pydantic models)

## Fixtures and Factories

**Test Data:**

From `tests/conftest.py` - reusable fixtures for all test cases:
```python
@pytest.fixture
def sample_evaluation_metrics() -> List[EvaluationMetric]:
    """Create sample evaluation metrics."""
    return [
        EvaluationMetric(
            name="accuracy",
            description="Answer correctness",
            value=0.95,
            weight=0.5,
        ),
        EvaluationMetric(
            name="completeness",
            description="Response completeness",
            value=0.85,
            weight=0.3,
        ),
        EvaluationMetric(
            name="relevance",
            description="Answer relevance",
            value=0.90,
            weight=0.2,
        ),
    ]
```

**Location:**
- Shared fixtures: `tests/conftest.py`
- Domain entity fixtures: `sample_b1_test_case`, `sample_b2_test_case`, `sample_b3_test_case`
- Response fixtures: `sample_model_response`
- Metric fixtures: `sample_evaluation_metrics`
- Test-specific fixtures: In individual test files when not reusable

## Coverage

**Requirements:**
- Target: 90%+ coverage on `domain`, `application`, `infrastructure`, `presentation`
- Configured in `src/pyproject.toml` under `[tool.coverage.run]` and `[tool.coverage.report]`

**View Coverage:**
```bash
# From src/ directory - generates HTML report
pytest ../tests --cov=domain --cov=application --cov=infrastructure --cov=presentation \
  --cov-report=html --cov-report=term-missing

# View HTML report in terminal
open htmlcov/index.html
```

**Excluded from Coverage:**
- `__init__.py` files
- `conftest.py`
- `def __repr__` methods
- Abstract methods
- `if __name__ == "__main__":`
- `if TYPE_CHECKING:` blocks

## Test Types

**Unit Tests:**
- Scope: Individual entities, value objects, services
- Location: `tests/domain/services/`, `tests/domain/entities/`
- Example: `tests/test_model_response.py` - tests ModelResponse entity in isolation
- Approach: Create minimal fixtures, test one behavior per test method

From `tests/test_model_response.py`:
```python
def test_extract_citations(self):
    """CRITICAL: Extract section citations from response text."""
    # Create test data
    response = ModelResponse(
        content="According to Section 13.1 and Section 9.2, organizations must...",
        model_name="test-model",
        tokens_used=20,
        latency_ms=1000,
    )

    # Execute
    citations = response.extract_citations()

    # Assert
    assert "13.1" in citations
    assert "9.2" in citations
    assert len(citations) == 2
```

**Integration Tests:**
- Scope: Multiple layers working together
- Location: `tests/integration/`
- Example: `tests/integration/test_tier2_semantic_similarity_e2e.py` - tests scoring service with semantic similarity
- Approach: Set up fixtures from multiple layers, test complete workflows

From `tests/integration/test_tier2_semantic_similarity_e2e.py`:
```python
def test_b8_semantic_similarity_good_response(
    self, b8_test_case: TestCase, good_semantic_response: ModelResponse
) -> None:
    """Test that semantically similar response scores well."""
    metrics = ScoringService.score_response(b8_test_case, good_semantic_response)

    # Verify metrics structure
    assert len(metrics) == 3

    accuracy = next(m for m in metrics if m.name == "accuracy")
    completeness = next(m for m in metrics if m.name == "completeness")
    grounding = next(m for m in metrics if m.name == "grounding")

    # Verify scoring logic
    assert accuracy.value > 0.6, "Semantic similarity should score semantically similar response highly"
    assert completeness.value >= 0.0
    assert grounding.value >= 0.7
```

**E2E Tests:**
- Scope: Complete evaluation pipeline from test case loading through result generation
- Location: `tests/test_e2e_evaluation.py`
- Example: `test_full_evaluation_flow_with_b1_data` - loads real B1 test data, mocks model, generates results
- Approach: Use real repositories/file I/O where possible, mock only external services

From `tests/test_e2e_evaluation.py`:
```python
@pytest.mark.asyncio
async def test_full_evaluation_flow_with_b1_data(self, tmp_path):
    """
    CRITICAL E2E TEST: Full evaluation flow with real B1 test data.

    This test verifies:
    1. Test case repository can load B1 JSONL files
    2. Model gateway can generate responses (mocked)
    3. Evaluation use case orchestrates the full flow
    4. Results are properly structured and contain expected fields
    """
```

## Common Patterns

**Async Testing:**

From `tests/test_e2e_evaluation.py`:
```python
@pytest.mark.asyncio
async def test_full_evaluation_flow_with_b1_data(self, tmp_path):
    """Test async evaluation flow."""
    # Create mock async method
    mock_ollama_client.generate = AsyncMock(return_value={"response": "..."})

    # Await async operations
    results = await evaluate_use_case.execute(request)

    # Assert results
    assert len(results) > 0
```

**Error Testing:**

From `src/domain/entities/test_case.py` validation:
```python
def test_invalid_test_id_format(self):
    """Test that invalid test_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        TestCase(
            test_id="INVALID-001",  # Wrong format
            benchmark_type=BenchmarkType("B1_CCoP_Applicability_Scope"),
            section=CCoPSection("Section 5"),
            clause_reference="5.1.1",
            difficulty=DifficultyLevel.MEDIUM,
            question="Question with at least fifty characters for validation to pass successfully",
            expected_response="Expected response",
            evaluation_criteria={"test": "criteria"},
        )

    assert "test_id must match format" in str(exc_info.value)
    assert exc_info.value.field == "test_id"
```

**Parametrized Tests:**

Test multiple benchmark types with shared test logic:
```python
@pytest.mark.parametrize("benchmark_type,expected_scorer", [
    ("B1", ScoringService._score_b1_interpretation),
    ("B2", ScoringService._score_b2_citation),
    ("B3", ScoringService._score_b3_hallucination),
])
def test_scoring_dispatch(self, benchmark_type, expected_scorer):
    """Test that scoring service routes to correct scorer."""
    test_case = TestCase(benchmark_type=benchmark_type, ...)
    response = ModelResponse(content="test", model_name="test")

    metrics = ScoringService.score_response(test_case, response)

    assert metrics is not None
    assert len(metrics) > 0
```

## pytest Configuration

**Key Settings (from `src/pyproject.toml`):**

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["../tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=domain",
    "--cov=application",
    "--cov=infrastructure",
    "--cov=presentation",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
asyncio_mode = "auto"
```

**pytest Plugins:**
- pytest-asyncio: Async/await support for tests marked with `@pytest.mark.asyncio`
- pytest-cov: Coverage reporting
- pytest-mock: Mocking support via `mocker` fixture

## Test Markers

**Custom Markers:**

From `pyproject.toml` - none explicitly defined (uses built-in markers)

**Built-in Markers Used:**
- `@pytest.mark.asyncio` - marks async tests for pytest-asyncio

**Naming Conventions for Test Methods:**
- Critical path tests: Mention "CRITICAL" in docstring
- E2E tests: Prefix with `test_e2e_` or `test_*_e2e`
- Integration tests: Prefix with `test_integration_` or place in `tests/integration/`
- Behavior-driven: Describe the behavior clearly in test name (e.g., `test_semantic_similarity_high_score_no_penalty`)

---

*Testing analysis: 2026-02-04*
