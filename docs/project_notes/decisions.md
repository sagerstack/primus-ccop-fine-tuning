# Architectural Decisions

This file logs architectural decisions (ADRs) with context and trade-offs. Use bullet lists for clarity.

## Format

Each decision should include:
- Date and ADR number
- Context (why the decision was needed)
- Decision (what was chosen)
- Alternatives considered
- Consequences (trade-offs, implications)

---

## Decisions

### ADR-001: Clean Architecture / Hexagonal Pattern (2026-02-04)

**Context:**
- Need strict separation between domain logic and infrastructure concerns
- Want to enable testing without external dependencies (Ollama, file system)
- Framework-agnostic design for potential future changes

**Decision:**
- Use Clean Architecture with Ports & Adapters pattern
- Domain layer has zero dependencies on application/infrastructure
- Dependency injection via `dependency-injector` library
- All I/O operations through abstract ports

**Alternatives Considered:**
- Layered architecture (traditional) -> Rejected: less testability, implicit coupling
- Single-module script -> Rejected: doesn't scale with complexity
- Django/Flask built-in patterns -> Rejected: want framework independence

**Consequences:**
- More boilerplate (interfaces, adapters, DTOs)
- Excellent testability (mock any port)
- Clear boundaries between concerns
- Easy to swap implementations (e.g., Ollama -> HuggingFace API)

### ADR-002: Tiered Evaluation Strategy (2026-02-04)

**Context:**
- Different benchmarks require different scoring approaches
- Some benchmarks need exact matching, others need semantic similarity, others need LLM judges
- Want to minimize compute cost while maintaining accuracy

**Decision:**
- Tier 1 (B1-B6): Label-based and Jaccard scoring (fast, deterministic)
- Tier 2 (B8, B9, B11, B15, B17-B19): Semantic similarity with sentence-transformers
- Tier 3 (B7, B10, B12-B14, B16, B20-B21): LLM-as-judge for subjective evaluation

**Alternatives Considered:**
- All LLM-as-judge -> Rejected: expensive, slow, non-deterministic
- All exact matching -> Rejected: too strict, misses semantic equivalence
- Human review only -> Rejected: doesn't scale

**Consequences:**
- Efficient resource usage (fast tiers run first)
- Appropriate precision for each benchmark type
- Tier 3 requires external LLM calls (cost consideration)
- Clear separation of evaluation complexity

### ADR-003: Ollama for Local Inference (2026-02-04)

**Context:**
- Need to run inference on Llama-Primus-Reasoning model
- Want local development without API costs
- Need to support quantized models (GGUF)

**Decision:**
- Use Ollama as the primary inference engine
- Custom `OllamaClient` for HTTP API communication
- Support for model quantization via GGUF conversion

**Alternatives Considered:**
- HuggingFace Inference API -> Rejected: API costs, network dependency
- vLLM -> Rejected: more complex setup for local dev
- Direct transformers loading -> Rejected: memory requirements too high

**Consequences:**
- Easy local development setup
- Support for quantized models (Q4_K_M to Q8_0)
- Requires Ollama server running locally
- HTTP overhead vs in-process inference

### ADR-004: RAG First, Fine-Tuning on Remaining Gaps (2026-02-04)

**Context:**
- Baseline evaluation revealed clear split: reasoning benchmarks (59% avg) vs factual benchmarks (39% avg)
- Hallucination rate (B21) at 22% is a critical safety issue
- Fine-tuning alone cannot fix factual knowledge gaps (B4, B6 at 21%)
- Need to determine which gaps are retrieval problems vs reasoning problems

**Decision:**
- Implement RAG first using CCoP 2.0 document corpus
- Re-evaluate model against all 21 benchmarks with RAG
- Identify remaining gaps that RAG doesn't address
- Fine-tune only on benchmarks where reasoning (not retrieval) is the bottleneck

**Alternatives Considered:**
- Fine-tuning first, RAG later → Rejected: risk of reinforcing hallucination patterns
- Fine-tuning only → Rejected: can't fix factual gaps, regulatory updates require retraining
- Parallel implementation → Rejected: harder to isolate which approach fixes which gaps

**Consequences:**
- ✅ Hallucination addressed from day one (safety)
- ✅ Clear diagnosis: if RAG doesn't fix it, it's a reasoning problem
- ✅ Fine-tuning dataset becomes smaller and focused
- ✅ Regulatory updates handled by document refresh, not retraining
- ❌ Requires RAG infrastructure before seeing fine-tuning benefits
- ❌ Delays fine-tuning phase until RAG baseline established

**Expected Benchmark Impact:**
- RAG should improve: B1, B4, B5, B6, B18, B20, B21 (factual/grounding)
- RAG may not improve: B3, B8, B9, B11, B12, B15 (reasoning/judgment)
- Fine-tuning targets: benchmarks that remain low after RAG

---

## Tips

- Number decisions sequentially (ADR-001, ADR-002, etc.)
- Always include date for context
- Be honest about trade-offs (use checkmarks and crosses)
- Keep alternatives brief but clear
- Update decisions if they're revisited/changed
