---
phase: 01-rag-infrastructure
plan: 04
subsystem: rag-integration
tags: [clean-architecture, citations, langgraph, dependency-injection, cli]
dependency-graph:
  requires:
    - 01-03-PLAN.md # LangGraph adaptive RAG graph
  provides:
    - Citation extraction and formatting (end-of-response references)
    - IRagPipeline port (Clean Architecture abstraction)
    - LangGraphRagAdapter (concrete implementation)
    - QueryComplianceUseCase (application orchestration)
    - CLI query command (ccop-eval query ask)
  affects:
    - 01-05-PLAN.md # Will use IRagPipeline for end-to-end testing
    - Phase 2 # Will use IRagPipeline port for RAG evaluation
tech-stack:
  added:
    - pydantic (RagResponse model)
  patterns:
    - Clean Architecture port/adapter pattern
    - Dependency injection with lazy loading
    - TYPE_CHECKING for circular import resolution
key-files:
  created:
    - src/rag/citations/resolver.py # Citation ID extraction and resolution
    - src/rag/citations/formatter.py # End-of-response reference formatting
    - src/rag/application/ports/i_rag_pipeline.py # IRagPipeline port interface
    - src/rag/application/use_cases/query_compliance.py # QueryComplianceUseCase
    - src/rag/infrastructure/adapters/langgraph_rag_adapter.py # LangGraphRagAdapter
    - src/rag/presentation/cli/query.py # CLI query command
  modified:
    - src/rag/retrieval/nodes/generation.py # Post-processing with citation resolution
    - src/rag/retrieval/graph.py # TYPE_CHECKING for Settings import
    - src/infrastructure/config/container.py # RAG providers with lazy imports
    - src/presentation/cli/main.py # Added query subcommand
decisions:
  - decision: "End-of-response citation format"
    rationale: "Clean response text with references listed at bottom. Avoids embedding metadata in chunk text (degrades retrieval quality per research)."
    alternatives: "Inline citations, footnotes"
    chosen: "End-of-response references: [1] Document, Section, Clause"
  - decision: "TYPE_CHECKING for Settings imports"
    rationale: "Avoids circular import between RAG modules and infrastructure.config.settings. Settings triggers container initialization which imports RAG modules."
    alternatives: "String-based providers (failed with partial initialization)"
    chosen: "TYPE_CHECKING + quoted type hints"
  - decision: "Lazy import pattern in DI container"
    rationale: "RAG imports trigger Settings import which triggers container import (circular). Lazy loading via staticmethod breaks the cycle."
    alternatives: "String-based providers (dependency-injector failed), restructure imports"
    chosen: "Static methods returning imported classes"
  - decision: "Graceful degradation when Databricks not configured"
    rationale: "Existing eval framework should work without RAG. Container must initialize successfully even without Databricks credentials."
    alternatives: "Fail fast on startup, separate container"
    chosen: "is_available() check, lazy initialization, error responses"
metrics:
  duration: 10 min
  completed: 2026-02-09
---

# Phase 01 Plan 04: Citation Resolution and Clean Architecture Integration Summary

**One-liner:** Citation extraction/formatting with end-of-response references, RAG pipeline integrated via Clean Architecture port/adapter pattern with DI wiring and CLI command.

## What Was Built

### Citation Resolution and Formatting (Task 1)

**Citation Extraction:**
- `extract_citation_ids()`: Extracts `<c>citation_id</c>` anchors from LLM generation using regex
- Deduplication: Returns unique IDs in order of appearance
- Edge case handling: Empty generation, no citations

**Citation Resolution:**
- `resolve_citations()`: Maps citation IDs to document metadata (document, section, clause)
- Lookup via `citation_id` in document metadata
- Missing citation handling: Logs warning, skips (no crash)

**Citation Formatting:**
- `format_response_with_citations()`:
  - Removes `<c>...</c>` anchors from response text
  - Appends end-of-response references: `[1] Document, Section, Clause`
  - Gracefully omits empty sections/clauses
- `format_model_only_response()`: Prepends notice for fallback generation

**Generation Node Update:**
- Post-processes LLM output after generation
- Calls `build_citations_from_state()` to resolve raw anchors
- Stores both `raw_generation` (with anchors) and `generation` (formatted with references)
- Updates state with resolved citations

### Clean Architecture Integration (Task 2)

**Port Interface:**
- `IRagPipeline`: Abstract interface for RAG operations
  - `query(question: str) -> RagResponse`: Main query method
  - `is_available() -> bool`: Operational check
- `RagResponse`: Pydantic model with response, citations, metadata

**Use Case:**
- `QueryComplianceUseCase`: Orchestrates RAG query execution
  - Validates input (non-empty question)
  - Checks pipeline availability
  - Invokes RAG pipeline
  - Logs execution metadata (is_rag_augmented, citation_count, retrieval_attempts)
  - Returns error response on failure (no crash)

**Adapter:**
- `LangGraphRagAdapter`: Concrete implementation of IRagPipeline
  - Wraps compiled LangGraph graph from `create_rag_pipeline()`
  - Lazy initialization (avoids startup errors when Databricks not configured)
  - Maps graph state to RagResponse
  - Graceful error handling (returns error response, doesn't crash)
  - `is_available()`: Checks Databricks and Ollama configuration

**Dependency Injection:**
- Added RAG providers to `Container`:
  - `rag_pipeline`: Singleton LangGraphRagAdapter
  - `query_compliance_use_case`: Factory QueryComplianceUseCase
- Lazy imports via staticmethods to avoid circular dependency
- Container initializes successfully even without Databricks configuration

**CLI Command:**
- `ccop-eval query ask "question"`: Query CCoP compliance via RAG
- Rich formatting: Markdown response, panel for errors
- Verbose mode: Shows metadata (is_rag_augmented, citations, retrieval attempts, grading scores)
- Configuration help: Guides user if Databricks/Ollama not configured

## Technical Implementation

### Citation Processing Flow

```
LLM Output with Anchors
    |
    v
extract_citation_ids()  --> ["CCoP-2.0.5.5.2.1", ...]
    |
    v
resolve_citations()  --> [{"document": "CCoP 2.0", "section": "...", "clause": "5.2.1", ...}]
    |
    v
format_response_with_citations()  --> "Clean text\n\nReferences:\n[1] CCoP 2.0, Section 5, Clause 5.2.1"
```

### Circular Import Resolution

**Problem:** `LangGraphRagAdapter` imports `Settings` → triggers `infrastructure/__init__.py` → imports `Container` → imports `LangGraphRagAdapter` (circular)

**Solution:**
1. **TYPE_CHECKING imports:** `from typing import TYPE_CHECKING; if TYPE_CHECKING: from infrastructure.config.settings import Settings`
2. **Quoted type hints:** `def __init__(self, settings: "Settings", ...)`
3. **Lazy container imports:** Static methods return imported classes, breaking initialization cycle

### DI Container Wiring

```python
# Lazy import to avoid circular dependency
@staticmethod
def _get_rag_adapter():
    from rag.infrastructure.adapters.langgraph_rag_adapter import LangGraphRagAdapter
    return LangGraphRagAdapter

rag_pipeline = providers.Singleton(
    providers.Callable(_get_rag_adapter),
    settings=config,
    logger=logger,
)
```

## Deviations from Plan

None - plan executed exactly as written.

## Challenges and Solutions

### Challenge 1: Circular Import Between RAG and Settings

**Issue:** Adapter imports Settings → triggers container → imports adapter (cycle)

**Root Cause:** `infrastructure/__init__.py` eagerly imports Container, Settings at module level

**Solution:**
- TYPE_CHECKING for Settings import in adapter and graph.py
- Lazy imports via staticmethods in container
- Quoted type hints for forward references

**Why This Works:** TYPE_CHECKING block only executes during type checking, not runtime. Lazy staticmethods defer import until provider is invoked.

### Challenge 2: Container Initialization Without Databricks

**Issue:** Existing eval framework must work without RAG configuration

**Solution:**
- `is_available()` check in adapter
- Lazy initialization in `_ensure_initialized()`
- Error responses instead of crashes
- Container initializes successfully regardless of Databricks config

**Verification:** `ccop-eval evaluate` and `ccop-eval report` still work without Databricks

## Testing

**Citation Extraction:**
- ✓ Extracts citation IDs from generation with anchors
- ✓ Handles empty generation (returns empty list)
- ✓ Deduplicates citation IDs

**Citation Resolution:**
- ✓ Resolves citation IDs to document metadata
- ✓ Handles missing citation IDs (logs warning, skips)
- ✓ Deduplicates resolved citations

**Citation Formatting:**
- ✓ Removes citation anchors from text
- ✓ Formats end-of-response references correctly
- ✓ Handles missing section/clause gracefully
- ✓ Model-only response includes notice

**Clean Architecture:**
- ✓ Port imports correctly
- ✓ Use case imports correctly
- ✓ Adapter imports correctly (no circular dependency)
- ✓ Container initializes without Databricks
- ✓ Existing tests pass (47/47)

**CLI:**
- ✓ `ccop-eval --help` shows query command
- ✓ `ccop-eval query --help` shows ask subcommand
- ✓ `ccop-eval query ask --help` shows usage

## Performance

**Duration:** 10 minutes
- Task 1 (citation resolution): 4 minutes
- Task 2 (clean architecture): 6 minutes

**Test Coverage:** 60% (existing tests still pass)

## Next Phase Readiness

**For Plan 01-05 (End-to-end testing):**
- IRagPipeline port ready for integration testing
- Citation formatting verified
- CLI command available for manual testing
- Error handling tested (Databricks not configured)

**For Phase 2 (RAG Evaluation):**
- Clean Architecture pattern established
- Port interface defined (easy to mock for testing)
- DI wiring in place
- Same pattern as existing EvaluateModelUseCase

## Commit Log

| Task | Commit | Message |
|------|--------|---------|
| 1 | e743b5d | feat(01-04): implement citation resolution and formatting, update generation node |
| 2 | 965d7eb | feat(01-04): integrate RAG pipeline with Clean Architecture |
| Summary | TBD | docs(01-04): complete citation resolution and clean architecture integration plan |

## Key Learnings

**1. TYPE_CHECKING for Circular Imports:**
- Python's TYPE_CHECKING constant is False at runtime, True during type checking
- Use for imports that create cycles but are only needed for type hints
- Combine with quoted type hints: `"Settings"` instead of `Settings`

**2. Lazy Imports in DI Container:**
- String-based providers fail if module has circular import during initialization
- Staticmethod + Callable provider pattern defers import until first use
- Breaks initialization cycle while maintaining DI benefits

**3. Graceful Degradation:**
- Optional components should not break container initialization
- Use `is_available()` checks instead of failing fast
- Return error responses instead of raising exceptions

**4. End-of-Response Citation Format:**
- Clean response text improves readability
- References at bottom avoid cluttering response
- Consistent with academic/legal citation conventions
- Avoids embedding metadata in chunk text (degrades retrieval per research)

## Files Changed

**Created (11):**
- `src/rag/citations/__init__.py`
- `src/rag/citations/resolver.py`
- `src/rag/citations/formatter.py`
- `src/rag/application/__init__.py`
- `src/rag/application/ports/__init__.py`
- `src/rag/application/ports/i_rag_pipeline.py`
- `src/rag/application/use_cases/__init__.py`
- `src/rag/application/use_cases/query_compliance.py`
- `src/rag/infrastructure/__init__.py`
- `src/rag/infrastructure/adapters/__init__.py`
- `src/rag/infrastructure/adapters/langgraph_rag_adapter.py`
- `src/rag/presentation/__init__.py`
- `src/rag/presentation/cli/__init__.py`
- `src/rag/presentation/cli/query.py`

**Modified (4):**
- `src/rag/retrieval/nodes/generation.py`
- `src/rag/retrieval/graph.py`
- `src/infrastructure/config/container.py`
- `src/presentation/cli/main.py`

**Total:** 15 files created, 4 files modified

---

**Status:** ✅ Complete

**Ready for:** Plan 01-05 (End-to-end RAG testing)
