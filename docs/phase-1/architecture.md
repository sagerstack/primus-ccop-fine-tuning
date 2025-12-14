# Architecture Documentation

## Clean Architecture Overview

This project implements **Clean Architecture** (also known as Hexagonal Architecture or Ports & Adapters pattern) with strict adherence to the **Dependency Rule**: dependencies point inward only.

## Layers

### 1. Domain Layer (Core)

**Location**: `src/domain/`

**Dependencies**: NONE (pure Python, framework-agnostic)

**Responsibilities**:
- Pure business logic
- Entities with identity and lifecycle
- Value objects (immutable)
- Domain services (stateless business logic)
- Domain exceptions

**Key Classes**:
- `TestCase`: Entity representing a CCoP 2.0 test case
- `EvaluationResult`: Entity representing evaluation outcome
- `BenchmarkType`: Value object for benchmark categories (B1-B6)
- `ScoringService`: Domain service for scoring logic
- `BenchmarkValidator`: Domain service for validation logic

**Business Rules Examples**:
- Test ID must match format `B{1-6}-{001-999}`
- High/Critical difficulty tests are high priority
- Different benchmarks require different metadata fields
- Passing thresholds vary by difficulty level

### 2. Application Layer (Use Cases)

**Location**: `src/application/`

**Dependencies**: Domain layer only

**Responsibilities**:
- Orchestrate domain objects
- Define interfaces (ports) for external dependencies
- Data Transfer Objects (DTOs) for crossing boundaries
- Application workflows (use cases)

**Key Components**:
- **DTOs**: `TestCaseDTO`, `EvaluationRequestDTO`, `EvaluationSummaryDTO`
- **Input Ports**: Use case interfaces (what the application can do)
- **Output Ports**: Repository/gateway interfaces (what the application needs)
- **Use Cases**: `EvaluateModelUseCase`, `SetupModelUseCase`, `GenerateReportUseCase`

**Use Case Flow Example**:
```
User → CLI → EvaluateModelUseCase:
  1. Load test cases (via ITestCaseRepository port)
  2. Generate responses (via IModelGateway port)
  3. Score responses (via ScoringService domain service)
  4. Save results (via IResultRepository port)
  5. Return summary
```

### 3. Infrastructure Layer (Adapters)

**Location**: `src/infrastructure/`

**Dependencies**: Application + Domain layers

**Responsibilities**:
- Implement application ports (interfaces)
- Handle external dependencies (Ollama, file I/O, etc.)
- Configuration management
- Dependency injection

**Key Adapters**:
- `OllamaGateway`: Implements `IModelGateway` for Ollama
- `JSONLTestCaseRepository`: Implements `ITestCaseRepository` for JSONL files
- `GGUFConverter`: Implements `IModelConverter` for model conversion
- `StructlogAdapter`: Implements `ILogger` for structured logging

**Adapter Pattern Benefits**:
- Easy to swap implementations (Ollama → vLLM → HuggingFace)
- Testable (can use mock adapters)
- External dependencies isolated from business logic

### 4. Presentation Layer (UI/CLI)

**Location**: `src/presentation/`

**Dependencies**: Application + Infrastructure layers

**Responsibilities**:
- User interface (CLI commands)
- Input validation
- Output formatting
- Dependency injection wiring

**CLI Commands**:
- `setup`: Model setup and prerequisite checking
- `evaluate`: Run model evaluation
- `report`: Generate evaluation reports

## Dependency Flow

```
┌─────────────────────────────────────────────────────┐
│              Presentation Layer (CLI)               │
│  Depends on: Application, Infrastructure            │
│  Role: User interface, DI wiring                    │
└──────────────────┬──────────────────────────────────┘
                   │ uses
                   ↓
┌─────────────────────────────────────────────────────┐
│           Infrastructure Layer (Adapters)           │
│  Depends on: Application (implements ports)         │
│  Role: External system integration                  │
└──────────────────┬──────────────────────────────────┘
                   │ implements ports defined in
                   ↓
┌─────────────────────────────────────────────────────┐
│         Application Layer (Use Cases & Ports)       │
│  Depends on: Domain only                            │
│  Role: Orchestration, define interfaces             │
└──────────────────┬──────────────────────────────────┘
                   │ uses
                   ↓
┌─────────────────────────────────────────────────────┐
│            Domain Layer (Business Logic)            │
│  Depends on: NOTHING                                │
│  Role: Core business rules                          │
└─────────────────────────────────────────────────────┘
```

## Ports & Adapters Pattern

### Output Ports (Driven/Secondary)

Application defines what it **needs** from external systems:

```python
# Port (interface) - defined in application layer
class IModelGateway(ABC):
    @abstractmethod
    async def generate_response(...) -> ModelResponse:
        pass

# Adapter (implementation) - in infrastructure layer
class OllamaGateway(IModelGateway):
    async def generate_response(...) -> ModelResponse:
        # Actual Ollama API call
```

**Benefits**:
- Application doesn't know about Ollama
- Easy to swap (Ollama → vLLM → Mock)
- Testable with mock implementations

### Input Ports (Driving/Primary)

Application defines what it **can do**:

```python
# Port (interface)
class IEvaluateModelUseCase(ABC):
    @abstractmethod
    async def execute(request: EvaluationRequestDTO) -> EvaluationSummaryDTO:
        pass

# Implementation
class EvaluateModelUseCase(IEvaluateModelUseCase):
    async def execute(...):
        # Orchestrate evaluation workflow
```

## Dependency Injection

Uses `dependency-injector` library for wiring dependencies:

```python
# infrastructure/config/container.py
class Container(containers.DeclarativeContainer):
    config = providers.Singleton(get_settings)

    ollama_client = providers.Singleton(OllamaClient, ...)

    model_gateway = providers.Singleton(
        OllamaGateway,
        client=ollama_client,
        logger=logger,
    )

    evaluate_use_case = providers.Factory(
        EvaluateModelUseCase,
        model_gateway=model_gateway,
        test_case_repository=test_case_repository,
        result_repository=result_repository,
        logger=logger,
    )
```

**Benefits**:
- Centralized configuration
- Easy to change implementations
- Supports testing with mocks

## Testing Strategy

### Unit Tests
- **Domain Layer**: Test entities, value objects, services in isolation
- **Application Layer**: Test use cases with mock ports
- **Infrastructure Layer**: Test adapters with real/mock external systems

### Integration Tests
- Test full stack with real Ollama
- Test repository implementations with real files
- Test CLI commands end-to-end

### Test Isolation
```
Domain Tests → No mocks needed (pure logic)
Application Tests → Mock all ports
Infrastructure Tests → Mock external APIs or use testcontainers
```

## Benefits of This Architecture

1. **Testability**: Each layer can be tested independently
2. **Flexibility**: Easy to swap implementations (databases, LLM providers, etc.)
3. **Maintainability**: Clear separation of concerns
4. **Independence**: Business logic independent of frameworks
5. **Scalability**: Easy to add new features without breaking existing code

## Design Decisions

### Why Clean Architecture?
- Academic research project requiring rigorous engineering
- Need to swap LLM providers (Ollama → vLLM → Cloud APIs)
- Must be testable without external dependencies
- Framework-agnostic domain logic

### Why Pydantic for DTOs?
- Type safety and validation
- Easy serialization/deserialization
- Good developer experience

### Why Dependency Injection Container?
- Centralized wiring
- Easy testing
- Configuration management

### Why Async?
- Future-proof for API implementation
- Better concurrency for batch evaluations
- Modern Python best practice

## Anti-Patterns Avoided

❌ **Don't**: Import infrastructure in domain
✅ **Do**: Keep domain pure

❌ **Don't**: Put business logic in infrastructure
✅ **Do**: Keep adapters thin (just translation)

❌ **Don't**: Skip interfaces
✅ **Do**: Define ports for all external dependencies

❌ **Don't**: Mix layers
✅ **Do**: Respect dependency direction

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Ports & Adapters Pattern](https://herbertograca.com/2017/09/14/ports-adapters-architecture/)
