# Architecture Patterns: Hybrid RAG + Fine-Tuned Compliance Model

**Domain:** CCoP 2.0 Compliance Checking
**Researched:** 2026-02-04
**Confidence:** HIGH

---

## Executive Summary

This research investigates architectural patterns for combining Retrieval-Augmented Generation (RAG) with fine-tuned language models within Clean Architecture principles. Based on 2026 enterprise best practices, the winning pattern is **Router-Based Adaptive RAG** where retrieval is treated as infrastructure, domain services orchestrate compliance logic, and a query router dynamically selects retrieval strategies based on question complexity.

**Key Finding:** RAG belongs in the **infrastructure layer** as a "knowledge runtime," while compliance reasoning and domain-specific scoring logic remain in the **domain layer**. The application layer orchestrates adaptive retrieval strategies based on query characteristics.

---

## Research Questions Answered

### 1. Where does RAG fit in Clean Architecture?

**Answer:** RAG components span multiple layers with clear separation:

| Component | Layer | Rationale | Source |
|-----------|-------|-----------|--------|
| **Vector Store (ChromaDB)** | Infrastructure | External data storage, retrieval mechanics | [Building Production RAG Systems in 2026](https://brlikhon.engineer/blog/building-production-rag-systems-in-2026-complete-architecture-guide) |
| **Retrieval Gateway (IRetrievalGateway)** | Application Port | Interface for retrieval operations (abstraction) | [Clean Architecture Layers](https://www.dandoescode.com/blog/unpacking-the-layers-of-clean-architecture-domain-application-and-infrastructure-services) |
| **Query Router** | Application Service | Adaptive routing based on query complexity | [Adaptive RAG Routing](https://www.meilisearch.com/blog/adaptive-rag) |
| **Compliance Validator** | Domain Service | Business logic for what constitutes valid compliance evidence | [Domain-Driven RAG](https://www.infoq.com/articles/domain-driven-rag/) |
| **Citation Verifier** | Domain Service | Ensures retrieved clauses are accurate and relevant | [Corrective RAG (CRAG)](https://www.meilisearch.com/blog/corrective-rag) |
| **Fine-Tuned Model Gateway** | Infrastructure | Model inference (already exists as IModelGateway) | Current architecture |

**Key Principle:** "RAG retrieval belongs in the infrastructure layer with domain expertise applied through metadata, governance policies, and specialized knowledge models rather than embedding retrieval logic in the domain layer itself." ([RAG as Infrastructure](https://ragaboutit.com/the-enterprise-database-rag-revolution-why-oracles-integrated-approach-challenges-everything-we-know-about-rag-architecture/))

---

### 2. How do fine-tuned model + RAG work together at inference time?

**Answer:** The hybrid integration follows a **sequential augmentation pattern** where RAG retrieval happens BEFORE model inference to provide context, not after.

**Pattern:** RAG for Facts + Fine-Tuning for Behavior

- **RAG responsibility:** Retrieve up-to-date CCoP clauses, supplementary docs, and reference examples
- **Fine-tuned model responsibility:** Interpret clauses, apply domain reasoning, generate compliant responses in CCoP 2.0 style/terminology

"Fine-tuning adjusts how a model responds, while RAG controls what information the model uses." ([RAG vs Fine-Tuning](https://www.oracle.com/artificial-intelligence/generative-ai/retrieval-augmented-generation-rag/rag-fine-tuning/))

**Integration Sequence:**

```
Query → Router (classify complexity) → Retriever (fetch relevant CCoP clauses)
      → Re-ranker (prioritize by relevance) → Fine-tuned Model (augmented prompt)
      → Citation Verifier (validate references) → Response
```

**Benefits of Hybrid Approach:**

- Fine-tuning adds **10-20% factuality gains** over zero-shot RAG ([Hybrid RAG Benefits](https://aws.amazon.com/blogs/machine-learning/tailoring-foundation-models-for-your-business-needs-a-comprehensive-guide-to-rag-fine-tuning-and-hybrid-approaches/))
- Hybrid approaches deliver **3-5x better ROI** than RAG-only or fine-tuning-only ([RAG vs Fine-Tuning Strategy](https://www.matillion.com/blog/rag-vs-fine-tuning-enterprise-ai-strategy-guide))
- System cost drops **40-60%** while accuracy improves when using adaptive retrieval ([Adaptive RAG Performance](https://www.meilisearch.com/blog/adaptive-rag))

---

### 3. What's the data flow for a compliance query?

**Answer:** The production-ready data flow for CCoP 2.0 compliance queries:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER QUERY                                     │
│  "Does this AWS Security Group comply with CCoP Clause 5.3.2?"          │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ QueryRouter (Application Service)                                │   │
│  │ • Classify: "Clause-specific compliance check" → Medium complexity│   │
│  │ • Strategy: Hybrid retrieval (vector + metadata filtering)        │   │
│  │ • Depth: Single-hop retrieval sufficient                          │   │
│  └────────────────────────┬────────────────────────────────────────┘   │
└───────────────────────────┼────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ ChromaDBRetrievalGateway (implements IRetrievalGateway)          │   │
│  │ Step 1: Vector Search                                            │   │
│  │   • Embed query                                                  │   │
│  │   • Semantic search in CCoP clause embeddings                    │   │
│  │   • Return top 20 candidates                                     │   │
│  │                                                                  │   │
│  │ Step 2: Metadata Filtering (Hybrid Search)                       │   │
│  │   • Filter by section="Protect" (Section 5)                      │   │
│  │   • Filter by clause_id="5.3.2"                                  │   │
│  │   • Filter by domain="IT/OT" (apply to both)                     │   │
│  │   • Narrow to 5-10 highly relevant results                       │   │
│  │                                                                  │   │
│  │ Step 3: Re-ranking (Qwen3-Reranker-0.6B)                         │   │
│  │   • Score each result for query relevance                        │   │
│  │   • Re-order by relevance score                                  │   │
│  │   • Return top 3 most relevant clauses                           │   │
│  └────────────────────────┬────────────────────────────────────────┘   │
└───────────────────────────┼────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ EvaluateModelUseCase (Application Service)                       │   │
│  │ • Build augmented prompt:                                        │   │
│  │   "Context: [Retrieved CCoP 5.3.2 clause text]                   │   │
│  │    Question: Does this AWS SG comply with Clause 5.3.2?          │   │
│  │    Instructions: Cite clause references in your response."       │   │
│  └────────────────────────┬────────────────────────────────────────┘   │
└───────────────────────────┼────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ OllamaGateway (implements IModelGateway)                         │   │
│  │ • Send augmented prompt to fine-tuned Llama-Primus-Reasoning     │   │
│  │ • Temperature: 0.7, Top-P: 0.9                                   │   │
│  │ • Model generates response using retrieved context + training    │   │
│  │ • Returns ModelResponse entity                                   │   │
│  └────────────────────────┬────────────────────────────────────────┘   │
└───────────────────────────┼────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ CitationVerificationService (Domain Service)                     │   │
│  │ • Extract clause references from response (e.g., "5.3.2")        │   │
│  │ • Validate references exist in retrieved context                 │   │
│  │ • Flag hallucinations (invented clauses not in retrieval)        │   │
│  │ • Calculate citation accuracy score                              │   │
│  │                                                                  │   │
│  │ ComplianceValidatorService (Domain Service)                      │   │
│  │ • Check if response contains required elements:                  │   │
│  │   ✓ Clause reference cited                                       │   │
│  │   ✓ Singapore-specific terminology (CII, CIIO, CSA)              │   │
│  │   ✓ IT/OT classification correct                                 │   │
│  │   ✓ Compliance verdict (compliant/non-compliant/unclear)         │   │
│  │ • Calculate compliance reasoning score                           │   │
│  │                                                                  │   │
│  │ ScoringService (Domain Service)                                  │   │
│  │ • Aggregate metrics: citation_accuracy + compliance_reasoning    │   │
│  │ • Apply benchmark-specific weights                               │   │
│  │ • Calculate overall score                                        │   │
│  └────────────────────────┬────────────────────────────────────────┘   │
└───────────────────────────┼────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   EvaluationResult Entity                                │
│  • test_case: TestCase                                                  │
│  • model_response: ModelResponse                                        │
│  • retrieved_context: List[CCoPClause]  ← NEW                           │
│  • metrics: List[Metric]                                                │
│  • overall_score: 0.87                                                  │
│  • passed: True                                                         │
│  • citations_verified: True                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Flow Decisions:**

1. **Query Router** (Application Layer) decides retrieval strategy based on query type
2. **Retrieval Gateway** (Infrastructure) fetches and re-ranks context
3. **Model Gateway** (Infrastructure) augments prompt and generates response
4. **Domain Services** validate compliance logic and calculate scores
5. **Application Service** orchestrates the entire flow

---

### 4. How to handle different query types?

**Answer:** Use **Adaptive Retrieval** with a Router Pattern.

"The winning architectural pattern in 2026 is the Router Pattern—a lightweight orchestration layer that sits between the user query and your retrieval infrastructure." ([Query-Adaptive RAG](https://ragaboutit.com/query-adaptive-rag-routing-complex-questions-to-multi-hop-retrieval-while-keeping-simple-queries-fast/))

#### Query Classification Matrix

| Query Type | Complexity | Retrieval Strategy | Depth | Example |
|-----------|------------|-------------------|-------|---------|
| **Clause Lookup** | Simple | Single-hop vector search | Top 1 | "What does Clause 5.3.2 say?" |
| **Compliance Check** | Medium | Hybrid search (vector + metadata) | Top 3 | "Does this code comply with Section 5?" |
| **Gap Analysis** | Complex | Multi-hop graph traversal | Top 10 + related | "What controls are missing for SCADA security?" |
| **Cross-Standard Mapping** | Complex | Graph RAG (CCoP → ISO 27001) | Graph traversal | "Map CCoP to ISO 27001 controls" |
| **Code Violation Detection** | Medium | Keyword + vector (code patterns) | Top 5 | "Find CCoP violations in this Terraform" |

#### Router Decision Logic

```python
# Application Layer - QueryRouter service
class QueryRouter:
    def classify_and_route(self, query: str) -> RetrievalStrategy:
        # Pattern detection
        if "what does clause" in query.lower():
            return SimpleVectorSearch(k=1)

        elif "comply with" in query.lower() or "violation" in query.lower():
            return HybridSearch(
                vector_k=20,
                metadata_filters=extract_clause_filters(query),
                rerank_top=3
            )

        elif "gap analysis" in query.lower() or "missing controls" in query.lower():
            return MultiHopRetrieval(
                initial_k=10,
                expansion_hops=2,
                max_depth=3
            )

        elif "map to" in query.lower() or "cross-standard" in query.lower():
            return GraphRAG(
                source_standard="CCoP 2.0",
                target_standard=extract_standard(query),
                traversal_depth=2
            )

        else:
            # Default: Medium complexity hybrid search
            return HybridSearch(vector_k=10, rerank_top=5)
```

**Performance Benefits:**

- Simple queries: **Fast single-hop retrieval** (< 100ms)
- Complex queries: **Multi-hop synthesis** with full context (< 1s)
- Overall system cost: **40-60% reduction** vs. one-size-fits-all ([Adaptive RAG Performance](https://www.meilisearch.com/blog/adaptive-rag))

---

## Recommended Architecture Pattern

### Pattern: Router-Based Adaptive RAG with Corrective Verification

**Rationale:** This pattern balances flexibility, accuracy, and Clean Architecture principles by treating retrieval as infrastructure, routing as application orchestration, and compliance validation as domain logic.

#### Architecture Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                               │
│                          (Typer CLI - exists)                            │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                                  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Use Cases (Orchestrators)                                         │  │
│  │ • EvaluateModelUseCase ← EXISTING                                 │  │
│  │ • EvaluateWithRAGUseCase ← NEW (wraps EvaluateModelUseCase)      │  │
│  │ • GenerateReportUseCase ← EXISTING                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Application Services                                              │  │
│  │ • QueryRouter ← NEW (adaptive routing logic)                      │  │
│  │ • PromptAugmenter ← NEW (builds augmented prompts)                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Output Ports (Interfaces)                                         │  │
│  │ • IModelGateway ← EXISTING                                        │  │
│  │ • IRetrievalGateway ← NEW                                         │  │
│  │ • ITestCaseRepository ← EXISTING                                  │  │
│  │ • IResultRepository ← EXISTING                                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                     │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Entities                                                          │  │
│  │ • TestCase ← EXISTING                                             │  │
│  │ • ModelResponse ← EXISTING                                        │  │
│  │ • EvaluationResult ← EXISTING                                     │  │
│  │ • RetrievedContext ← NEW (list of CCoP clauses with metadata)     │  │
│  │ • CCoPClause ← NEW (clause_id, text, section, metadata)           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Domain Services                                                   │  │
│  │ • ScoringService ← EXISTING                                       │  │
│  │ • CitationVerificationService ← NEW                               │  │
│  │   - Validate clause references in response                        │  │
│  │   - Detect hallucinations (invented clauses)                      │  │
│  │   - Calculate citation accuracy metric                            │  │
│  │                                                                   │  │
│  │ • ComplianceValidatorService ← NEW                                │  │
│  │   - Validate compliance reasoning quality                         │  │
│  │   - Check for required terminology (CII, CIIO, CSA)               │  │
│  │   - Verify IT/OT classification correctness                       │  │
│  │                                                                   │  │
│  │ • ContextRelevanceService ← NEW (optional, for advanced CRAG)     │  │
│  │   - Score retrieved context relevance to query                    │  │
│  │   - Trigger web search if retrieval confidence is low             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Value Objects                                                     │  │
│  │ • BenchmarkType ← EXISTING                                        │  │
│  │ • DifficultyLevel ← EXISTING                                      │  │
│  │ • RetrievalStrategy ← NEW (enum: Simple/Hybrid/MultiHop/Graph)    │  │
│  │ • QueryComplexity ← NEW (enum: Simple/Medium/Complex)             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Gateways (Adapters)                                               │  │
│  │ • OllamaGateway ← EXISTING (implements IModelGateway)             │  │
│  │ • ChromaDBRetrievalGateway ← NEW (implements IRetrievalGateway)   │  │
│  │   - Vector search                                                 │  │
│  │   - Metadata filtering                                            │  │
│  │   - Hybrid search (RRF fusion)                                    │  │
│  │   - Re-ranking (Qwen3-Reranker)                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ External Systems                                                  │  │
│  │ • ChromaDB (vector store)                                         │  │
│  │ • Ollama (model inference)                                        │  │
│  │ • Qwen3-Reranker-0.6B (re-ranking model)                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Boundaries

### Application Layer Components

#### 1. EvaluateWithRAGUseCase (NEW)

**Responsibility:** Orchestrate RAG-augmented evaluation flow

```python
class EvaluateWithRAGUseCase:
    def __init__(
        self,
        model_gateway: IModelGateway,
        retrieval_gateway: IRetrievalGateway,
        query_router: QueryRouter,
        prompt_augmenter: PromptAugmenter,
        test_case_repository: ITestCaseRepository,
        result_repository: IResultRepository,
        logger: ILogger,
    ):
        # Dependencies injected

    async def execute(self, request: EvaluationRequestDTO) -> EvaluationSummaryDTO:
        # Load test cases (same as existing)
        test_cases = await self._load_test_cases(request)

        # For each test case:
        for test_case in test_cases:
            # 1. Route query to determine retrieval strategy
            strategy = self.query_router.classify_and_route(test_case.question)

            # 2. Retrieve context using strategy
            retrieved_context = await self.retrieval_gateway.retrieve(
                query=test_case.question,
                strategy=strategy,
            )

            # 3. Augment prompt with retrieved context
            augmented_prompt = self.prompt_augmenter.build_prompt(
                question=test_case.question,
                context=retrieved_context,
            )

            # 4. Generate response (via existing ModelGateway)
            model_response = await self.model_gateway.generate_response(
                prompt=augmented_prompt,
                model_name=request.model_name,
            )

            # 5. Score response (via existing ScoringService + NEW domain services)
            metrics = ScoringService.score_response_with_rag(
                test_case=test_case,
                model_response=model_response,
                retrieved_context=retrieved_context,  # NEW
            )

            # 6. Create result
            result = EvaluationResult(
                test_case=test_case,
                model_response=model_response,
                retrieved_context=retrieved_context,  # NEW
                metrics=metrics,
            )
            result.finalize()
            results.append(result)

        # Generate summary (same as existing)
        return self._generate_summary(results)
```

**Key Decision:** This use case WRAPS existing evaluation logic rather than replacing it. Non-RAG evaluation path remains unchanged.

---

#### 2. QueryRouter (NEW Application Service)

**Responsibility:** Classify query complexity and select retrieval strategy

```python
class QueryRouter:
    """
    Application service that classifies queries and selects retrieval strategies.

    Does NOT perform retrieval (that's infrastructure).
    Does NOT validate compliance (that's domain).
    """

    def classify_and_route(self, query: str) -> RetrievalStrategy:
        # Classify query complexity
        complexity = self._classify_complexity(query)

        # Select strategy based on complexity
        if complexity == QueryComplexity.SIMPLE:
            return RetrievalStrategy.simple_vector_search(k=1)

        elif complexity == QueryComplexity.MEDIUM:
            return RetrievalStrategy.hybrid_search(
                vector_k=20,
                metadata_filters=self._extract_filters(query),
                rerank_top=3,
            )

        elif complexity == QueryComplexity.COMPLEX:
            return RetrievalStrategy.multi_hop_retrieval(
                initial_k=10,
                expansion_hops=2,
            )

    def _classify_complexity(self, query: str) -> QueryComplexity:
        # Simple heuristics (can be enhanced with LLM classification later)
        if self._is_direct_clause_lookup(query):
            return QueryComplexity.SIMPLE
        elif self._requires_multi_hop_reasoning(query):
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.MEDIUM
```

---

#### 3. PromptAugmenter (NEW Application Service)

**Responsibility:** Build augmented prompts from query + retrieved context

```python
class PromptAugmenter:
    """
    Application service that constructs augmented prompts.

    Does NOT retrieve context (that's infrastructure).
    Does NOT score responses (that's domain).
    """

    def build_prompt(
        self,
        question: str,
        context: RetrievedContext,
    ) -> str:
        # Build structured prompt
        prompt_parts = []

        # Add retrieved CCoP clauses as context
        if context.clauses:
            prompt_parts.append("# Relevant CCoP 2.0 Clauses:\n")
            for clause in context.clauses:
                prompt_parts.append(
                    f"## {clause.clause_id}: {clause.title}\n"
                    f"{clause.text}\n\n"
                )

        # Add question
        prompt_parts.append(f"# Question:\n{question}\n\n")

        # Add instructions
        prompt_parts.append(
            "# Instructions:\n"
            "- Cite specific clause references in your response\n"
            "- Use Singapore-specific terminology (CII, CIIO, CSA)\n"
            "- Indicate if the question applies to IT, OT, or both\n"
        )

        return "\n".join(prompt_parts)
```

---

### Domain Layer Components

#### 1. CitationVerificationService (NEW Domain Service)

**Responsibility:** Validate clause citations in model responses

```python
class CitationVerificationService:
    """
    Domain service that validates clause citations.

    Business rules:
    - Cited clauses must exist in retrieved context
    - Citation format must match CCoP standards (e.g., "5.3.2")
    - Hallucinated clauses are penalized
    """

    @staticmethod
    def verify_citations(
        response: ModelResponse,
        retrieved_context: RetrievedContext,
    ) -> CitationVerificationResult:
        # Extract cited clauses from response
        cited_clauses = CitationVerificationService._extract_citations(
            response.content
        )

        # Validate each citation
        valid_citations = []
        hallucinated_citations = []

        for cited_clause_id in cited_clauses:
            if retrieved_context.contains_clause(cited_clause_id):
                valid_citations.append(cited_clause_id)
            else:
                hallucinated_citations.append(cited_clause_id)

        # Calculate accuracy
        total = len(cited_clauses)
        accurate = len(valid_citations)
        accuracy = accurate / total if total > 0 else 0.0

        return CitationVerificationResult(
            cited_clauses=cited_clauses,
            valid_citations=valid_citations,
            hallucinated_citations=hallucinated_citations,
            accuracy=accuracy,
        )

    @staticmethod
    def _extract_citations(text: str) -> List[str]:
        # Regex to extract clause IDs like "5.3.2", "Clause 5.3.2"
        import re
        pattern = r'\b(?:Clause\s+)?(\d{1,2}\.\d{1,2}\.\d{1,2})\b'
        return re.findall(pattern, text)
```

---

#### 2. ComplianceValidatorService (NEW Domain Service)

**Responsibility:** Validate compliance reasoning quality

```python
class ComplianceValidatorService:
    """
    Domain service that validates compliance reasoning.

    Business rules:
    - Response must cite relevant clauses
    - Response must use Singapore-specific terminology
    - Response must correctly classify IT/OT applicability
    - Response must provide clear compliance verdict
    """

    @staticmethod
    def validate_compliance_reasoning(
        test_case: TestCase,
        response: ModelResponse,
        retrieved_context: RetrievedContext,
    ) -> ComplianceValidationResult:
        checks = []

        # Check 1: Clause reference present
        has_clause_reference = ComplianceValidatorService._has_clause_reference(
            response.content
        )
        checks.append(("clause_reference", has_clause_reference))

        # Check 2: Singapore terminology used
        has_sg_terminology = ComplianceValidatorService._has_singapore_terminology(
            response.content,
            required_terms=["CII", "CIIO", "CSA", "CCoP"],
        )
        checks.append(("singapore_terminology", has_sg_terminology))

        # Check 3: IT/OT classification correct
        correct_classification = ComplianceValidatorService._validate_it_ot_classification(
            response.content,
            expected_domain=test_case.domain,
        )
        checks.append(("it_ot_classification", correct_classification))

        # Check 4: Compliance verdict present
        has_verdict = ComplianceValidatorService._has_compliance_verdict(
            response.content
        )
        checks.append(("compliance_verdict", has_verdict))

        # Calculate score
        passed = sum(1 for _, result in checks if result)
        score = passed / len(checks)

        return ComplianceValidationResult(
            checks=dict(checks),
            score=score,
        )
```

---

#### 3. RetrievedContext (NEW Entity)

**Responsibility:** Encapsulate retrieved CCoP clauses with metadata

```python
from dataclasses import dataclass
from typing import List

@dataclass
class CCoPClause:
    """Value object representing a single CCoP clause."""
    clause_id: str  # e.g., "5.3.2"
    section: str    # e.g., "Protect"
    title: str
    text: str
    domain: str     # "IT", "OT", or "IT/OT"
    metadata: Dict[str, Any]

@dataclass
class RetrievedContext:
    """Entity representing retrieved context for a query."""
    query: str
    clauses: List[CCoPClause]
    retrieval_strategy: RetrievalStrategy
    relevance_scores: Dict[str, float]  # clause_id -> relevance score

    def contains_clause(self, clause_id: str) -> bool:
        """Check if a clause was retrieved."""
        return any(c.clause_id == clause_id for c in self.clauses)

    def get_clause(self, clause_id: str) -> Optional[CCoPClause]:
        """Get a specific clause by ID."""
        for clause in self.clauses:
            if clause.clause_id == clause_id:
                return clause
        return None
```

---

### Infrastructure Layer Components

#### ChromaDBRetrievalGateway (NEW)

**Responsibility:** Implement retrieval using ChromaDB

```python
class ChromaDBRetrievalGateway(IRetrievalGateway):
    """
    Infrastructure adapter for ChromaDB vector store.

    Implements:
    - Vector search
    - Metadata filtering
    - Hybrid search (RRF fusion)
    - Re-ranking
    """

    def __init__(
        self,
        client: chromadb.Client,
        collection_name: str = "ccop_clauses",
        reranker_model: str = "Qwen3-Reranker-0.6B",
    ):
        self.client = client
        self.collection = client.get_collection(collection_name)
        self.reranker = self._load_reranker(reranker_model)

    async def retrieve(
        self,
        query: str,
        strategy: RetrievalStrategy,
    ) -> RetrievedContext:
        if strategy.type == "simple_vector":
            return await self._simple_vector_search(query, strategy.k)

        elif strategy.type == "hybrid":
            return await self._hybrid_search(
                query,
                strategy.vector_k,
                strategy.metadata_filters,
                strategy.rerank_top,
            )

        elif strategy.type == "multi_hop":
            return await self._multi_hop_retrieval(query, strategy)

    async def _hybrid_search(
        self,
        query: str,
        vector_k: int,
        metadata_filters: Dict[str, Any],
        rerank_top: int,
    ) -> RetrievedContext:
        # Step 1: Vector search
        vector_results = self.collection.query(
            query_texts=[query],
            n_results=vector_k,
            where=metadata_filters,  # Metadata filtering
        )

        # Step 2: Re-rank with Qwen3-Reranker
        reranked_results = self.reranker.rerank(
            query=query,
            documents=vector_results['documents'][0],
            top_k=rerank_top,
        )

        # Step 3: Build RetrievedContext
        clauses = []
        relevance_scores = {}

        for idx, doc in enumerate(reranked_results):
            clause = CCoPClause(
                clause_id=doc['metadata']['clause_id'],
                section=doc['metadata']['section'],
                title=doc['metadata']['title'],
                text=doc['text'],
                domain=doc['metadata']['domain'],
                metadata=doc['metadata'],
            )
            clauses.append(clause)
            relevance_scores[clause.clause_id] = doc['rerank_score']

        return RetrievedContext(
            query=query,
            clauses=clauses,
            retrieval_strategy=RetrievalStrategy.hybrid_search(
                vector_k=vector_k,
                metadata_filters=metadata_filters,
                rerank_top=rerank_top,
            ),
            relevance_scores=relevance_scores,
        )
```

---

## Build Order Recommendations

### Phase Approach: Incremental Integration

**Rationale:** Build RAG capabilities incrementally to validate each component before adding complexity. Do NOT build everything at once.

---

#### Phase 1: Infrastructure Foundation (Week 1-2)

**Objective:** Set up ChromaDB and basic retrieval

**Components:**
1. ChromaDB setup
   - Install ChromaDB
   - Create `ccop_clauses` collection
   - Index all 220 CCoP clauses with metadata

2. IRetrievalGateway port (interface)
   - Define `retrieve()` method signature
   - Define `RetrievedContext` entity
   - Define `CCoPClause` value object

3. ChromaDBRetrievalGateway (simple implementation)
   - Implement basic vector search only
   - No hybrid search yet
   - No re-ranking yet

**Validation:**
- Can retrieve top 5 clauses for "network security" query
- Retrieved clauses have correct metadata (section, domain)

---

#### Phase 2: Query Routing (Week 3)

**Objective:** Add adaptive routing logic

**Components:**
1. QueryRouter application service
   - Implement query classification (simple/medium/complex)
   - Implement strategy selection

2. RetrievalStrategy value object
   - Define strategy types (simple_vector, hybrid, multi_hop)
   - Encapsulate retrieval parameters

3. QueryComplexity value object
   - Define complexity levels (Simple/Medium/Complex)

**Validation:**
- "What does Clause 5.3.2 say?" → Simple strategy
- "Does this code comply with Section 5?" → Medium strategy
- "What controls are missing for SCADA?" → Complex strategy

---

#### Phase 3: Hybrid Search & Re-ranking (Week 4)

**Objective:** Enhance retrieval with metadata filtering and re-ranking

**Components:**
1. ChromaDBRetrievalGateway enhancements
   - Add metadata filtering (hybrid search)
   - Add Reciprocal Rank Fusion (RRF)
   - Integrate Qwen3-Reranker-0.6B

2. PromptAugmenter application service
   - Build augmented prompts from query + context

**Validation:**
- Hybrid search narrows results from 20 to 3
- Re-ranking improves relevance order
- Augmented prompt contains correct clause text

---

#### Phase 4: RAG-Augmented Evaluation (Week 5)

**Objective:** Integrate RAG into evaluation pipeline

**Components:**
1. EvaluateWithRAGUseCase
   - Orchestrate: route → retrieve → augment → generate → score

2. Modify EvaluationResult entity
   - Add `retrieved_context: RetrievedContext` field

**Validation:**
- Run baseline evaluation WITH RAG
- Compare results vs. baseline WITHOUT RAG
- Expect improvement in citation accuracy

---

#### Phase 5: Citation Verification (Week 6)

**Objective:** Add domain service to validate citations

**Components:**
1. CitationVerificationService (domain service)
   - Extract citations from response
   - Validate against retrieved context
   - Calculate citation accuracy metric

2. Update ScoringService
   - Add citation_accuracy to metrics
   - Weight citation accuracy appropriately

**Validation:**
- Detect hallucinated clauses (invented by model)
- Calculate citation accuracy score
- Penalize responses with invalid citations

---

#### Phase 6: Compliance Validation (Week 7)

**Objective:** Add domain service to validate compliance reasoning

**Components:**
1. ComplianceValidatorService (domain service)
   - Check for clause references
   - Validate Singapore terminology
   - Verify IT/OT classification
   - Check for compliance verdict

2. Update ScoringService
   - Add compliance_reasoning to metrics

**Validation:**
- Identify responses missing key elements
- Score compliance reasoning quality
- Compare scores WITH vs. WITHOUT RAG

---

#### Phase 7: Advanced Retrieval Strategies (Week 8+)

**Objective:** Add multi-hop and graph-based retrieval (if needed)

**Components:**
1. Multi-hop retrieval
   - Implement expansion-based retrieval
   - Add iterative refinement

2. Graph RAG (optional)
   - Build CCoP clause relationship graph
   - Implement graph traversal retrieval

**Validation:**
- Multi-hop retrieval for gap analysis queries
- Graph RAG for cross-standard mapping

---

## Alternative Patterns Considered

### Pattern 1: RAG-Only (No Fine-Tuning)

**What:** Use base Llama-Primus-Reasoning with RAG, skip fine-tuning

**Pros:**
- Simpler to build
- No training required
- Always uses latest CCoP clauses

**Cons:**
- Model lacks CCoP-specific reasoning patterns
- May not use Singapore terminology correctly
- No improvement in domain-specific behavior

**Why Not:** Project explicitly requires fine-tuning to achieve 85% accuracy. RAG alone won't teach the model CCoP reasoning patterns.

---

### Pattern 2: Fine-Tuning-Only (No RAG)

**What:** Fine-tune on all CCoP clauses, use as-is without retrieval

**Pros:**
- Simpler architecture
- No retrieval infrastructure needed
- Model "knows" CCoP clauses

**Cons:**
- Training data becomes stale (CCoP updates require retraining)
- Higher hallucination risk (model invents clauses)
- Can't cite specific clause text (only learned patterns)

**Why Not:** CCoP 2.0 is a regulatory document where citation accuracy is critical. Fine-tuning alone doesn't provide traceable clause references.

---

### Pattern 3: Sequential RAG (Retrieve After Generation)

**What:** Generate response first, then retrieve to verify

**Pros:**
- Model not biased by retrieval
- Can detect knowledge gaps

**Cons:**
- Inefficient (model hallucinates, then we correct)
- Higher latency (two model calls)
- Doesn't leverage retrieval to improve generation

**Why Not:** "RAG controls what information the model uses" — retrieval should happen BEFORE generation to provide context, not after for verification.

---

### Pattern 4: RAG in Domain Layer

**What:** Embed retrieval logic inside domain services

**Pros:**
- Domain services directly control retrieval

**Cons:**
- **Violates Clean Architecture** (domain depends on infrastructure)
- Harder to test domain logic in isolation
- Can't swap retrieval implementations

**Why Not:** "RAG retrieval belongs in the infrastructure layer with domain expertise applied through metadata, governance policies, and specialized knowledge models." ([RAG as Infrastructure](https://ragaboutit.com/the-enterprise-database-rag-revolution-why-oracles-integrated-approach-challenges-everything-we-know-about-rag-architecture/))

---

## Adaptive Retrieval: When to Retrieve More vs. Less

### Retrieval Budget Matrix

| Query Type | Retrieval Depth | Rationale | Cost |
|-----------|----------------|-----------|------|
| **Direct Clause Lookup** | Minimal (k=1) | User wants specific clause text | Low |
| **Code Compliance Check** | Medium (k=3-5) | Need clause + examples | Medium |
| **Gap Analysis** | High (k=10+, multi-hop) | Need comprehensive coverage | High |
| **Terminology Definition** | Minimal (k=1-2) | Singapore-specific terms | Low |
| **Cross-Standard Mapping** | Graph traversal | Requires relationship mapping | Very High |

**Cost-Benefit Decision:**

- Simple queries: Over-retrieval wastes compute (40-60% cost reduction from adaptive routing)
- Complex queries: Under-retrieval causes incomplete answers
- **Router Pattern balances both** by matching retrieval depth to query needs

---

## Corrective RAG (CRAG) Integration (Optional Enhancement)

### What is CRAG?

"Corrective-RAG (CRAG) is a strategy for RAG that incorporates self-reflection / self-grading on retrieved documents." ([CRAG Overview](https://www.meilisearch.com/blog/corrective-rag))

### How it Works

1. **Retrieval Evaluator:** Assess retrieved documents for relevance
2. **Confidence Scoring:** Assign confidence to retrieval quality
3. **Corrective Actions:**
   - High confidence → Use retrieved context
   - Medium confidence → Re-rank and filter
   - Low confidence → Trigger web search or knowledge base expansion

### Implementation in This Project

```python
class ContextRelevanceService(DomainService):
    """
    Domain service that evaluates retrieved context relevance.

    Business rules:
    - Retrieved clauses must be relevant to the query
    - Low relevance triggers corrective actions
    - Hallucination risk increases with low-quality retrieval
    """

    @staticmethod
    def evaluate_relevance(
        query: str,
        retrieved_context: RetrievedContext,
    ) -> ContextRelevanceResult:
        # Score each retrieved clause for relevance
        relevance_scores = []
        for clause in retrieved_context.clauses:
            score = ContextRelevanceService._score_relevance(query, clause)
            relevance_scores.append(score)

        # Calculate overall confidence
        avg_relevance = sum(relevance_scores) / len(relevance_scores)

        # Determine confidence level
        if avg_relevance >= 0.8:
            confidence = ConfidenceLevel.HIGH
            action = "USE_AS_IS"
        elif avg_relevance >= 0.5:
            confidence = ConfidenceLevel.MEDIUM
            action = "RE_RANK_AND_FILTER"
        else:
            confidence = ConfidenceLevel.LOW
            action = "EXPAND_RETRIEVAL"

        return ContextRelevanceResult(
            confidence=confidence,
            avg_relevance=avg_relevance,
            recommended_action=action,
        )
```

**When to Add CRAG:**
- After Phase 6 (once basic RAG is working)
- If hallucination rate is still high (> 5%)
- If citation accuracy is below target (< 85%)

---

## Performance Considerations

### Latency Budget

| Component | Target Latency | Optimization Strategy |
|-----------|---------------|----------------------|
| **Query Classification** | < 10ms | Rule-based heuristics (no LLM call) |
| **Vector Search** | < 50ms | ChromaDB optimized indexes |
| **Re-ranking** | < 100ms | Use lightweight Qwen3-Reranker-0.6B |
| **Model Inference** | < 2s | QLoRA quantization, GPU inference |
| **Citation Verification** | < 50ms | Regex extraction, set intersection |
| **Total End-to-End** | < 3s | Acceptable for batch evaluation |

### Scalability Targets

- **Throughput:** 100 evaluations/hour (batch processing acceptable)
- **Concurrent Queries:** 5-10 (not a user-facing system)
- **Vector Store Size:** ~220 clauses (~5 MB embeddings) — easily fits in memory

**No complex optimization needed** — this is a research/compliance checking system, not a real-time API.

---

## Data Flow: Before vs. After RAG

### Before RAG (Current Architecture)

```
Query → Fine-tuned Model → Response → Scoring → Result
```

**Limitation:** Model relies solely on training data (static knowledge)

---

### After RAG (Proposed Architecture)

```
Query → Router (classify) → Retrieval (fetch CCoP clauses)
      → Augmenter (build prompt) → Fine-tuned Model (augmented prompt)
      → Response → Citation Verification → Compliance Validation
      → Scoring → Result
```

**Benefits:**
- Model has up-to-date clause text
- Citations can be verified against retrieval
- Retrieval adapts to query complexity
- Domain services validate compliance reasoning

---

## Summary: Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **RAG Layer Placement** | Infrastructure | Retrieval is a technical concern, not domain logic |
| **Routing Logic** | Application Service | Orchestration of retrieval strategies |
| **Compliance Validation** | Domain Service | Business rules for compliance reasoning |
| **Integration Pattern** | Sequential Augmentation | RAG retrieves BEFORE generation, not after |
| **Retrieval Strategy** | Adaptive (Router Pattern) | Match retrieval depth to query complexity |
| **Hybrid Search** | Vector + Metadata Filtering | Narrow results while maintaining semantic relevance |
| **Re-ranking** | Qwen3-Reranker-0.6B | Improve relevance order after initial retrieval |
| **Citation Verification** | Domain Service | Detect hallucinations, validate clause references |
| **Build Approach** | Incremental (7 phases) | Validate each component before adding complexity |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| **RAG Layer Placement** | HIGH | Clear consensus: RAG is infrastructure ([RAG as Infrastructure](https://ragaboutit.com/the-enterprise-database-rag-revolution-why-oracles-integrated-approach-challenges-everything-we-know-about-rag-architecture/)) |
| **Hybrid Pattern Benefits** | HIGH | Multiple sources confirm 10-20% improvement ([AWS Hybrid Guide](https://aws.amazon.com/blogs/machine-learning/tailoring-foundation-models-for-your-business-needs-a-comprehensive-guide-to-rag-fine-tuning-and-hybrid-approaches/)) |
| **Adaptive Routing** | HIGH | Proven 40-60% cost reduction ([Adaptive RAG](https://www.meilisearch.com/blog/adaptive-rag)) |
| **ChromaDB Hybrid Search** | MEDIUM | Documented capability ([ChromaDB Hybrid Search](https://codesignal.com/learn/courses/implementing-semantic-search-with-chromadb-1/lessons/hybrid-retrieval-combining-metadata-and-vector-search)), need to verify production performance |
| **Re-ranking Model** | MEDIUM | Qwen3-Reranker recommended for 2026 ([Top Rerankers 2026](https://www.siliconflow.com/articles/en/most-accurate-reranker-for-rag-pipelines)), not yet validated for this project |
| **Build Timeline** | MEDIUM | 7-8 weeks is estimated based on component complexity, may vary |

---

## Sources

### RAG Architecture & Best Practices
- [RAG in 2026: Enterprise AI](https://www.techment.com/blogs/blogs-rag-in-2026-enterprise-ai/)
- [Building Production RAG Systems in 2026](https://brlikhon.engineer/blog/building-production-rag-systems-in-2026-complete-architecture-guide)
- [RAG vs Fine-Tuning: Enterprise AI Strategy](https://www.matillion.com/blog/rag-vs-fine-tuning-enterprise-ai-strategy-guide)
- [Tailoring Foundation Models: RAG, Fine-Tuning, and Hybrid Approaches](https://aws.amazon.com/blogs/machine-learning/tailoring-foundation-models-for-your-business-needs-a-comprehensive-guide-to-rag-fine-tuning-and-hybrid-approaches/)
- [Context as Architecture: RAG](https://www.redhat.com/en/blog/context-architecture-practical-look-retrieval-augmented-generation)

### Adaptive Retrieval & Routing
- [Adaptive RAG Explained: What to Know in 2026](https://www.meilisearch.com/blog/adaptive-rag)
- [Query-Adaptive RAG: Routing Complex Questions](https://ragaboutit.com/query-adaptive-rag-routing-complex-questions-to-multi-hop-retrieval-while-keeping-simple-queries-fast/)

### Clean Architecture & DDD
- [Unpacking Clean Architecture: Domain, Application, and Infrastructure Services](https://www.dandoescode.com/blog/unpacking-the-layers-of-clean-architecture-domain-application-and-infrastructure-services)
- [Domain-Driven RAG: Building Accurate Enterprise Knowledge Systems](https://www.infoq.com/articles/domain-driven-rag/)
- [Application Services VS Domain Services in DDD](https://medium.com/@jankrloz/application-services-vs-domain-services-in-ddd-7846dcbd7f95)

### RAG as Infrastructure
- [The Enterprise Database RAG Revolution](https://ragaboutit.com/the-enterprise-database-rag-revolution-why-oracles-integrated-approach-challenges-everything-we-know-about-rag-architecture/)
- [RAG at Scale: How to Build Production AI Systems in 2026](https://redis.io/blog/rag-at-scale/)

### Retrieval Components
- [Rerankers and Two-Stage Retrieval](https://www.pinecone.io/learn/series/rag/rerankers/)
- [Ultimate Guide: Most Accurate Reranker Models For RAG Pipelines In 2026](https://www.siliconflow.com/articles/en/most-accurate-reranker-for-rag-pipelines)
- [ChromaDB Hybrid Search](https://codesignal.com/learn/courses/implementing-semantic-search-with-chromadb-1/lessons/hybrid-retrieval-combining-metadata-and-vector-search)
- [Metadata Filtering and Hybrid Search for Vector Databases](https://www.dataquest.io/blog/metadata-filtering-and-hybrid-search-for-vector-databases/)

### Corrective RAG (CRAG)
- [Corrective RAG (CRAG): Workflow, Implementation, and More](https://www.meilisearch.com/blog/corrective-rag)
- [Corrective Retrieval Augmented Generation (arXiv)](https://arxiv.org/abs/2401.15884)
- [Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection](https://selfrag.github.io/)

### Compliance-Specific RAG
- [Leveraging Graph-RAG and Prompt Engineering to Enhance LLM-Based Automated Requirement Traceability and Compliance Checks](https://arxiv.org/html/2412.08593v1)
- [RAG for Enterprise AI: LLM Accuracy Blueprint 2026](https://dextralabs.com/blog/enterprise-rag-llm-accuracy-blueprint-2026/)

---

**Research Complete:** 2026-02-04
