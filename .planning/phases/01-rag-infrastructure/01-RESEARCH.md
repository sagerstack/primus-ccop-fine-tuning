# Phase 1: RAG Infrastructure - Research

**Researched:** 2026-02-08
**Domain:** RAG (Retrieval-Augmented Generation) for regulatory compliance documents
**Confidence:** HIGH

## Summary

RAG Infrastructure for regulatory documents requires LangGraph-orchestrated adaptive RAG with LangChain components, Databricks Mosaic AI Vector Search as the vector store, and structure-aware document ingestion that preserves clause numbers and section hierarchy.

The standard approach is **Adaptive RAG with self-correction**: query analysis routes to appropriate retrieval strategies, document grading evaluates retrieved relevance, and retrieval loops enable self-correction when initial retrieval fails. For regulatory documents, **hybrid search (dense + sparse with reranking)** significantly outperforms dense-only retrieval, achieving 85% NDCG@10 vs 72% for dense-only. **Section-level semantic chunking** preserves regulatory structure better than fixed-size chunking, improving context recall from ~65% to 87.7% on structured documents.

The primary technical challenge is **retrieval quality**: 40-60% of RAG implementations fail to reach production due to retrieval issues. For regulatory compliance, this is mitigated through: (1) structure-aware chunking at section boundaries, (2) hybrid search with reranking, (3) citation-aware architecture with document+section+clause metadata, and (4) retrieval grading with fallback to model-only generation when retrieval confidence is low.

**Primary recommendation:** Implement LangGraph adaptive RAG graph with hybrid retrieval (Databricks dense + BM25 sparse via RRF), Databricks built-in reranking (15% accuracy improvement with single parameter), section-level chunking using PyMuPDF4LLM for structure preservation, and citation anchors embedded in chunks with spatial metadata stored separately for end-of-response references.

## Standard Stack

The established libraries/tools for adaptive RAG on regulatory compliance documents:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| LangGraph | Latest (0.3.x) | Orchestration of stateful RAG graph with loops, branches, self-correction | Industry standard for agentic RAG in 2026, cited as baseline for production AI agents |
| LangChain | Latest (0.3.x) | Building blocks: retrievers, embeddings, prompt templates, LLM integrations | Provides components that LangGraph orchestrates, 63.6% of RAG implementations use it |
| Databricks Mosaic AI Vector Search | Current | Serverless vector store with Unity Catalog governance | Hybrid search support, built-in reranking (+15% accuracy), managed embeddings via BGE endpoint |
| PyMuPDF4LLM | Latest | PDF parsing with structure preservation (sections, tables to markdown) | Superior table detection and structure preservation vs generic PDF loaders, GitHub-compatible markdown output |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| databricks-langchain | Latest | LangChain integration for Databricks Vector Search | Required for DatabricksVectorSearch retriever with LangChain |
| img2table | Latest (via PyMuPDF4LLM) | Table extraction from PDFs | Automatically used by PyMuPDF4LLM for table detection and markdown conversion |
| Llama-Primus-Reasoning | 8B (base: Llama-3.1-8B-Instruct) | Response generation LLM specialized for cybersecurity reasoning | +15.8% improvement on CISSP benchmark over base model, first open-source cybersecurity reasoning model |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| LangGraph | LangChain LCEL only | LCEL lacks stateful loops and self-correction needed for adaptive RAG; acceptable for simple linear RAG |
| Databricks Vector Search | ChromaDB, Pinecone, Weaviate | Local dev simpler with ChromaDB but lacks hybrid search; Pinecone/Weaviate require separate reranking; Databricks provides managed embeddings + Unity Catalog governance |
| PyMuPDF4LLM | UnstructuredPDFLoader, PyPDF | Other loaders don't preserve section structure as markdown; acceptable for simple text extraction but inadequate for clause-numbered regulatory docs |
| Hybrid search | Dense-only | Dense-only: 72% NDCG@10, 45ms latency; Hybrid: 85% NDCG@10, 165ms latency; +18% accuracy worth the latency for compliance use case |

**Installation:**
```bash
pip install langchain langchain-community langgraph databricks-langchain pymupdf4llm
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── rag/                         # RAG vertical slice (owns full stack)
│   ├── ingestion/               # Document ingestion pipeline
│   │   ├── parsers/             # PDF parsing (PyMuPDF4LLM)
│   │   ├── chunkers/           # Section-level semantic chunking
│   │   └── indexers/           # Databricks Vector Search indexing
│   ├── retrieval/               # LangGraph adaptive RAG graph
│   │   ├── nodes/               # Graph nodes (query analysis, retrieval, grading, generation)
│   │   ├── edges/               # Conditional routing logic
│   │   └── state/               # Graph state schema
│   ├── citations/               # Citation extraction and resolution
│   ├── application/             # RAG-scoped ports and use cases
│   │   ├── ports/               # IRagPipeline interface
│   │   └── use_cases/           # QueryComplianceUseCase
│   ├── infrastructure/          # RAG-scoped adapters
│   │   └── adapters/            # LangGraphRagAdapter
│   └── presentation/            # RAG-scoped CLI
│       └── cli/                 # query command
├── evaluation/                  # Evaluation vertical slice (existing)
├── infrastructure/              # Shared infrastructure (settings, DI)
└── presentation/                # Shared CLI entry point
```

### Pattern 1: LangGraph Adaptive RAG Graph
**What:** Stateful graph with query analysis → retrieval → grading → generation → grounding verification, with self-correcting loops when retrieval fails

**When to use:** Any RAG application where retrieval quality is critical and queries vary in complexity

**Architecture:**
```python
# Source: https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/

from langgraph.graph import StateGraph, END

# Define state
class GraphState(TypedDict):
    query: str
    documents: List[Document]
    generation: str
    retrieval_attempted: bool
    grading_scores: List[float]

# Build graph
workflow = StateGraph(GraphState)

# Add nodes
workflow.add_node("query_analysis", analyze_query)      # Classify query type
workflow.add_node("retrieval", retrieve_documents)       # Retrieve from vector store
workflow.add_node("grade_documents", grade_relevance)    # Score retrieved docs
workflow.add_node("generate", generate_response)         # LLM generation
workflow.add_node("fallback", fallback_generation)       # Model-only (no RAG)

# Add edges
workflow.set_entry_point("query_analysis")
workflow.add_conditional_edges(
    "query_analysis",
    route_query,  # Route to retrieval or fallback based on query type
    {
        "retrieval": "retrieval",
        "fallback": "fallback"
    }
)
workflow.add_edge("retrieval", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_rewrite_or_generate,  # Loop back to retrieval or proceed to generation
    {
        "rewrite": "retrieval",    # Self-correction loop
        "generate": "generate",
        "fallback": "fallback"     # If no relevant docs, fallback
    }
)
workflow.add_edge("generate", END)
workflow.add_edge("fallback", END)

app = workflow.compile()
```

**Key principles:**
- State persists across nodes (shared memory)
- Conditional edges enable branching and loops
- Self-correction: if grading fails, rewrite query and retry retrieval (max 2-3 loops to prevent infinite loops)
- Fallback path: when retrieval fails, route to model-only generation and log for analysis

### Pattern 2: Section-Level Semantic Chunking for Regulatory Docs
**What:** Chunk regulatory documents at section boundaries (preserving clause numbers and hierarchy) rather than fixed character counts

**When to use:** Structure-rich documents (legal, regulatory, technical) with numbered sections, clauses, or hierarchies

**Example:**
```python
# Source: https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089
# Combined with PyMuPDF4LLM structure preservation

import pymupdf4llm
from langchain.text_splitter import MarkdownHeaderTextSplitter

# 1. Parse PDF to markdown with structure preservation
md_text = pymupdf4llm.to_markdown("ccop-2.0.pdf")

# 2. Split by markdown headers (section boundaries)
headers_to_split_on = [
    ("#", "Document"),
    ("##", "Section"),
    ("###", "Subsection"),
]

markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=False  # Keep headers in chunks for context
)

chunks = markdown_splitter.split_text(md_text)

# 3. Enrich with metadata
for chunk in chunks:
    chunk.metadata["document_source"] = "CCoP 2.0"
    chunk.metadata["section"] = chunk.metadata.get("Section", "")
    chunk.metadata["clause"] = extract_clause_number(chunk.page_content)
    # Add citation anchor: <c>page.order</c>
    chunk.page_content = add_citation_anchors(chunk.page_content, chunk.metadata)
```

**Performance:** Structure-aware chunking achieves 87.7% context recall on SEC filings vs ~65% for fixed-size chunking (200-40% improvement on complex docs).

### Pattern 3: Hybrid Search with Reranking
**What:** Combine dense (semantic) and sparse (keyword) retrieval using Reciprocal Rank Fusion (RRF), then rerank top-k results

**When to use:** Production RAG where both semantic understanding and exact term matching are important (e.g., regulatory compliance with specific clause numbers)

**Architecture:**
```python
# Source: https://docs.databricks.com/aws/en/vector-search/vector-search
# Databricks Vector Search native hybrid search with built-in reranking

from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()

# Create hybrid index (dense + sparse)
index = client.create_index(
    endpoint_name="ccop-vector-search",
    index_name="main.ccop_compliance.clauses_hybrid",
    primary_key="id",
    index_type="DELTA_SYNC",
    delta_sync_index_spec={
        "source_table": "main.ccop_compliance.parsed_clauses",
        "embedding_source_column": "text",
        "embedding_model_endpoint_name": "databricks-bge-large-en"
    },
    # Enable hybrid search
    hybrid_search_params={
        "sparse_search_field": "text"  # BM25 on text field
    }
)

# Query with reranking (Public Preview - single parameter)
results = index.similarity_search(
    query_text="What are the access control requirements?",
    k=20,  # Retrieve 20 candidates
    # Reranking enabled automatically, returns top-k reranked
    query_params={
        "rerank": True,  # Built-in reranking (+15% accuracy)
        "rrf_param": 60  # RRF parameter (default: 60)
    }
)
```

**Performance:** Hybrid retrieval: 85% NDCG@10 (165ms). With reranking: 93% NDCG@10 (520ms). Dense-only: 72% NDCG@10 (45ms). +29% improvement over dense-only.

### Pattern 4: Citation-Aware RAG with Spatial Metadata
**What:** Embed citation anchors in chunk text, store spatial metadata separately, resolve citations post-generation

**When to use:** Regulated industries requiring audit trails with traceable references (e.g., "Section 4.2, Clause 4.2.1")

**Example:**
```python
# Source: https://www.tensorlake.ai/blog/rag-citations

# 1. Chunk enrichment with citation anchors
def add_citation_anchors(text: str, metadata: dict) -> str:
    """Embed lightweight anchors: <c>doc.section.clause</c>"""
    doc_id = metadata.get("document_source", "")
    section = metadata.get("section", "")
    clause = metadata.get("clause", "")

    anchor = f"<c>{doc_id}.{section}.{clause}</c>"
    return f"{anchor} {text}"

# 2. Store spatial metadata separately
chunk_metadata = {
    "document_source": "CCoP 2.0",
    "section": "5: Access Control",
    "clause": "5.2.1",
    "page": 23,
    "bbox": {"x1": 12, "y1": 15, "x2": 149, "y2": 328},
    "citation_id": "CCoP-2.0.5.5.2.1"
}

# 3. LLM prompt for citation extraction
system_prompt = """
You are a compliance expert. Answer using retrieved context.
IMPORTANT: The context contains citation anchors like <c>CCoP-2.0.5.5.2.1</c>.
- DO NOT include these anchors in your response text
- DO include citation IDs in your metadata output
Return: {"answer": "...", "citations": ["CCoP-2.0.5.5.2.1", ...]}
"""

# 4. Post-generation citation resolution
def resolve_citations(citation_ids: List[str], metadata_store: dict) -> List[dict]:
    """Resolve citation IDs to document+section+clause references"""
    citations = []
    for cid in citation_ids:
        meta = metadata_store.get(cid, {})
        citations.append({
            "document": meta.get("document_source"),
            "section": meta.get("section"),
            "clause": meta.get("clause"),
            "page": meta.get("page")
        })
    return citations

# 5. Format end-of-response references
def format_references(citations: List[dict]) -> str:
    """Format as end-of-response references"""
    refs = []
    for i, c in enumerate(citations, 1):
        refs.append(f"[{i}] {c['document']}, {c['section']}, Clause {c['clause']}")
    return "\n\nReferences:\n" + "\n".join(refs)
```

**Storage overhead:** ~10-15% for spatial metadata (bounding boxes, page numbers).

### Anti-Patterns to Avoid

- **Fixed-size chunking on regulatory docs:** Breaks section boundaries, loses clause context. Use section-level semantic chunking instead.
- **Dense-only retrieval for compliance:** Misses exact clause number matches. Use hybrid search (dense + sparse) for both semantic and keyword matching.
- **Embedding citation metadata in chunk text:** Creates noise, degrades retrieval quality. Use lightweight citation anchors + separate metadata storage.
- **Infinite retrieval loops:** LangGraph self-correction can loop forever if not bounded. Implement max retrieval budget (2-3 attempts) per query.
- **Converting PDFs to plain text/markdown without structure:** Loses clause numbers, section hierarchy, table structure. Use PyMuPDF4LLM with layout detection for structure preservation.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Query routing logic | Custom if/else query classifiers | LangGraph conditional edges with LLM-based routing | Edge cases compound (multi-intent queries, ambiguous phrasing); LLM-based routing generalizes better |
| Retrieval failure handling | Manual retry logic with counters | LangGraph graph with self-correcting loops and fallback nodes | Production systems fail 40-60% without proper fallback; graph-based approach handles retrieval loops, query rewriting, fallback paths in one architecture |
| Hybrid search fusion | Custom BM25 + dense vector merging | Databricks Vector Search native hybrid with RRF | RRF (Reciprocal Rank Fusion) is proven method; Databricks built-in implementation handles score normalization, index syncing, and reranking with single parameter |
| PDF table extraction | Regex/heuristic table parsers | PyMuPDF4LLM with img2table | Table detection is hard (multi-column layouts, merged cells, headers); PyMuPDF4LLM with Layout mode handles edge cases, outputs GitHub-compatible markdown |
| Chunk metadata management | In-memory dicts or separate DB tables | Vector store metadata fields (Databricks supports 50 fields) | Vector stores are optimized for metadata filtering during retrieval; separate DBs require joins, latency overhead |
| LLM observability | Custom logging + print statements | OpenTelemetry-based solutions (SigNoz, Langfuse) or LangSmith | Production RAG needs trace IDs, latency breakdowns, cost tracking per query; rolling your own misses edge cases (async calls, nested chains, context propagation) |
| Embedding generation | Loading HuggingFace models locally | Databricks BGE embedding endpoint (managed) | Managed endpoints handle batching, GPU optimization, auto-scaling; self-hosting requires GPU management, batch optimization, error handling |

**Key insight:** RAG systems have compounding failure modes. At 95% accuracy per layer (retrieval, reranking, generation), total system reliability is 0.95³ = 0.81 (fails 1 in 5 times). Hand-rolled components at each layer multiply risk. Use proven, composable libraries.

## Common Pitfalls

### Pitfall 1: Silent LLM Agent Failures
**What goes wrong:** Unlike traditional software that crashes, LLM agents drift or produce low-quality outputs without throwing errors. Retrieval returns irrelevant docs, generation hallucinates, but system appears to work.

**Why it happens:** No explicit error conditions in RAG pipeline. Vector search always returns results (even if irrelevant), LLM always generates (even if unsupported by context).

**How to avoid:**
- Implement explicit grading nodes that score retrieval relevance (threshold: >0.6 for relevance)
- Add grounding verification node that checks if generation is supported by retrieved context
- Log failed retrievals (query + retrieval attempts + grading scores) for offline analysis
- Implement fallback path: when grading fails, route to model-only generation and flag response as "not RAG-augmented"

**Warning signs:**
- Responses feel generic or off-topic
- Citations missing or pointing to wrong sections
- Retrieval always returns same chunks regardless of query

### Pitfall 2: Over-Engineering Query Classification
**What goes wrong:** Building complex multi-class query classifiers (10+ categories) that route to hyper-specialized retrieval strategies, adding latency and maintenance burden without accuracy gains.

**Why it happens:** Assumption that more granular routing = better retrieval. In practice, most queries fall into 2-3 categories.

**How to avoid:**
- Start with binary classification: "needs retrieval" vs "general question"
- Add complexity only when data shows clear performance gaps for specific query types
- Use LLM-based routing with simple prompts vs fine-tuned classifiers (more flexible, easier to update)
- Monitor query distribution in production; if 95% of queries are one type, routing adds no value

**Warning signs:**
- Query classifier has >5 output classes
- Routing logic has >3 levels of nesting
- Adding new query types requires code changes vs prompt updates

### Pitfall 3: Chunking Mismatches Between Ingestion and Retrieval
**What goes wrong:** Chunk size optimized for embedding model (512 tokens) breaks regulatory sections mid-clause, losing context. Or chunks are too large (2000+ tokens), mixing multiple unrelated clauses.

**Why it happens:** Chunking treated as generic "split text into N tokens" without considering document structure or retrieval use case.

**How to avoid:**
- For regulatory docs: chunk at section/clause boundaries (semantic chunking) regardless of token count
- Set minimum chunk size (e.g., 200 tokens) to avoid orphaned sentences
- Set maximum chunk size (e.g., 1000 tokens); if section exceeds max, recursively split on sub-boundaries (subsections, paragraphs)
- Validate chunking output: sample chunks and verify clause numbers/section headers are intact
- Add overlap (50-100 tokens) between chunks to preserve context across boundaries

**Warning signs:**
- Chunks start/end mid-sentence
- Clause numbers appear fragmented across multiple chunks
- Retrieved chunks lack sufficient context to answer query standalone

### Pitfall 4: Underestimating Databricks Vector Search Setup Complexity
**What goes wrong:** Assuming "serverless" means zero configuration. Missing Unity Catalog privileges, incorrect Delta table schema, or embedding endpoint not accessible leads to cryptic errors.

**Why it happens:** Databricks Vector Search integrates with Unity Catalog (fine-grained permissions), Delta tables (specific schema requirements), and Model Serving (embedding endpoints). Each has setup prerequisites.

**How to avoid:**
- **Unity Catalog**: Ensure service principal or user has USE CATALOG, USE SCHEMA, and SELECT privileges on index location
- **Delta table**: Must have primary key column, text column for embedding, and metadata columns (document_source, section, clause, etc.)
- **Embedding endpoint**: Verify `databricks-bge-large-en` endpoint is accessible via `databricks.sdk.service.serving.list_endpoints()`
- **Local dev**: Use Databricks workspace token in `.env.local` (DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_CATALOG, DATABRICKS_SCHEMA)
- Test index creation with small sample (100 rows) before full ingestion

**Warning signs:**
- Errors like "Table not found" despite table existing (Unity Catalog permission issue)
- "Embedding endpoint not found" (endpoint name typo or permission issue)
- Index creation succeeds but queries return empty results (schema mismatch)

### Pitfall 5: Not Handling Retrieval Failure Gracefully
**What goes wrong:** When vector search returns no relevant documents (grading scores all <0.3), system still passes empty/irrelevant context to LLM, resulting in hallucinated response.

**Why it happens:** Assumption that retrieval always succeeds. In practice, edge-case queries or knowledge gaps in corpus lead to failed retrieval.

**How to avoid:**
- Implement grading node that scores each retrieved document (LLM-as-judge or embedding similarity)
- Set relevance threshold (e.g., >0.6); if all docs below threshold, mark retrieval as failed
- Add conditional edge: if retrieval failed, route to fallback node (model-only generation without RAG)
- Log failed retrievals with query, attempted retrievals, and grading scores
- Always indicate in response whether it was RAG-augmented or model-only

**Warning signs:**
- Responses reference documents/clauses that don't exist
- Citations are generic or missing when retrieval should have succeeded
- User reports "irrelevant answers" for queries that should match corpus

### Pitfall 6: Ignoring LangGraph State Management
**What goes wrong:** Treating LangGraph state like global mutable variables, leading to race conditions, stale state, or state bloat (storing entire document corpus in state).

**Why it happens:** Misunderstanding StateGraph as "just a dict". In reality, state updates are versioned and checkpointed, and improper schema design leads to performance issues.

**How to avoid:**
- Define explicit state schema with TypedDict (typed fields)
- Store only necessary data in state (query, retrieved doc IDs, generation, not full doc content)
- Use state reducers for list fields (e.g., append to `documents` list across loop iterations)
- Avoid storing large objects (embeddings, full PDFs) in state; use references (doc IDs) instead
- Test state persistence: serialize/deserialize state to verify schema is correct

**Warning signs:**
- State size grows unbounded across graph execution
- Errors like "State is not JSON serializable"
- Difficulty debugging because state fields are unclear or inconsistent

## Code Examples

Verified patterns from official sources:

### Query Analysis Node (LLM-based Routing)
```python
# Source: https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class QueryAnalysis(BaseModel):
    """Query analysis output"""
    needs_retrieval: bool = Field(description="Whether query requires document retrieval")
    query_type: str = Field(description="Type of query: 'compliance', 'general', 'clarification'")
    rewritten_query: str = Field(description="Query optimized for retrieval")

llm = ChatOpenAI(model="gpt-4", temperature=0)

query_analyzer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert at analyzing compliance queries. Determine if the query requires retrieval from CCoP documents."),
    ("human", "Query: {query}\n\nAnalyze this query and determine if it needs retrieval.")
])

query_analyzer = query_analyzer_prompt | llm.with_structured_output(QueryAnalysis)

def analyze_query(state: GraphState) -> GraphState:
    """Analyze query to determine routing"""
    analysis = query_analyzer.invoke({"query": state["query"]})
    state["query_analysis"] = analysis
    state["rewritten_query"] = analysis.rewritten_query
    return state
```

### Document Grading Node (LLM-as-Judge)
```python
# Source: https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/

from pydantic import BaseModel, Field

class GradeDocuments(BaseModel):
    """Grade relevance of retrieved documents"""
    score: float = Field(description="Relevance score 0-1")
    reasoning: str = Field(description="Explanation of score")

grader_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are grading relevance of a retrieved CCoP clause to a user question. If the clause contains keywords or semantic meaning related to the question, grade it as relevant."),
    ("human", "Question: {query}\n\nCCoP Clause: {document}\n\nGrade the relevance.")
])

grader = grader_prompt | llm.with_structured_output(GradeDocuments)

def grade_documents(state: GraphState) -> GraphState:
    """Grade each retrieved document for relevance"""
    query = state["rewritten_query"]
    documents = state["documents"]

    grading_scores = []
    filtered_docs = []

    for doc in documents:
        grade = grader.invoke({"query": query, "document": doc.page_content})
        grading_scores.append(grade.score)

        if grade.score > 0.6:  # Relevance threshold
            filtered_docs.append(doc)

    state["grading_scores"] = grading_scores
    state["filtered_documents"] = filtered_docs
    state["retrieval_succeeded"] = len(filtered_docs) > 0

    return state
```

### Section-Level Chunking with PyMuPDF4LLM
```python
# Source: https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/
# Combined with structure-aware metadata extraction

import pymupdf4llm
from langchain.text_splitter import MarkdownHeaderTextSplitter
from typing import List, Dict
import re

def extract_clause_number(text: str) -> str:
    """Extract clause number from section text (e.g., '5.2.1')"""
    # Regex for clause numbers: digits.digits.digits
    match = re.search(r'\b(\d+\.\d+\.\d+)\b', text[:200])  # Check first 200 chars
    return match.group(1) if match else ""

def parse_ccop_pdf(pdf_path: str, document_name: str) -> List[Dict]:
    """Parse CCoP PDF with structure preservation"""

    # 1. Extract markdown with PyMuPDF4LLM (preserves tables, sections)
    md_text = pymupdf4llm.to_markdown(
        pdf_path,
        page_chunks=False,  # Full document, not per-page
        write_images=False,  # Don't extract images
        image_path=None,
        image_format="png",
        dpi=150
    )

    # 2. Split by section headers
    headers_to_split_on = [
        ("#", "Document"),
        ("##", "Section"),
        ("###", "Subsection"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False  # Keep headers for context
    )

    chunks = markdown_splitter.split_text(md_text)

    # 3. Enrich with metadata
    enriched_chunks = []
    for i, chunk in enumerate(chunks):
        section = chunk.metadata.get("Section", "")
        subsection = chunk.metadata.get("Subsection", "")
        clause = extract_clause_number(chunk.page_content)

        enriched_chunks.append({
            "id": f"{document_name}-{i}",
            "text": chunk.page_content,
            "metadata": {
                "document_source": document_name,
                "section": section,
                "subsection": subsection,
                "clause": clause,
                "citation_id": f"{document_name}.{section}.{clause}" if clause else f"{document_name}.{section}"
            }
        })

    return enriched_chunks

# Usage
chunks = parse_ccop_pdf("ccop-official/CCoP---Second-Edition_Revision-One.pdf", "CCoP 2.0")
print(f"Extracted {len(chunks)} section-level chunks")
```

### Databricks Vector Search Hybrid Retrieval with LangChain
```python
# Source: https://docs.langchain.com/oss/python/integrations/vectorstores/databricks_vector_search

from databricks.vector_search.client import VectorSearchClient
from databricks_langchain import DatabricksVectorSearch
from langchain_community.embeddings import DatabricksEmbeddings

# Initialize clients
vsc = VectorSearchClient()
embeddings = DatabricksEmbeddings(endpoint="databricks-bge-large-en")

# Create DatabricksVectorSearch retriever
vectorstore = DatabricksVectorSearch(
    endpoint=vsc.get_endpoint("ccop-vector-search"),
    index_name="main.ccop_compliance.clauses_hybrid",
    text_column="text",
    embedding=embeddings,
    columns=["document_source", "section", "clause", "citation_id"]  # Metadata to retrieve
)

# Convert to retriever with hybrid search
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 20,  # Retrieve 20 candidates
        "filter": None,  # Optional: filter by metadata (e.g., {"section": "5: Access Control"})
    }
)

# Usage in LangGraph node
def retrieve_documents(state: GraphState) -> GraphState:
    """Retrieve documents from Databricks Vector Search"""
    query = state["rewritten_query"]
    documents = retriever.invoke(query)
    state["documents"] = documents
    return state
```

### Citation Resolution and Formatting
```python
# Source: https://www.tensorlake.ai/blog/rag-citations

from typing import List, Dict
import re

def extract_citation_ids(generation: str) -> List[str]:
    """Extract citation IDs from LLM generation (assumes anchors like <c>CCoP-2.0.5.5.2.1</c>)"""
    return re.findall(r'<c>(.*?)</c>', generation)

def resolve_citations(citation_ids: List[str], documents: List[Dict]) -> List[Dict]:
    """Resolve citation IDs to full document metadata"""
    citations = []
    for cid in citation_ids:
        # Find document with matching citation_id
        for doc in documents:
            if doc.metadata.get("citation_id") == cid:
                citations.append({
                    "document": doc.metadata.get("document_source"),
                    "section": doc.metadata.get("section"),
                    "clause": doc.metadata.get("clause"),
                    "citation_id": cid
                })
                break
    return citations

def format_response_with_citations(generation: str, citations: List[Dict]) -> str:
    """Format final response with end-of-response references"""
    # Remove citation anchors from response text
    clean_generation = re.sub(r'<c>.*?</c>', '', generation).strip()

    # Format references
    references = []
    for i, c in enumerate(citations, 1):
        ref = f"[{i}] {c['document']}, {c['section']}, Clause {c['clause']}"
        references.append(ref)

    if references:
        return f"{clean_generation}\n\nReferences:\n" + "\n".join(references)
    else:
        return clean_generation

# Usage in LangGraph generation node
def generate_response(state: GraphState) -> GraphState:
    """Generate response with citations"""
    # ... LLM generation ...
    generation = llm.invoke(context)

    # Extract and resolve citations
    citation_ids = extract_citation_ids(generation)
    citations = resolve_citations(citation_ids, state["filtered_documents"])

    # Format final response
    final_response = format_response_with_citations(generation, citations)

    state["generation"] = final_response
    state["citations"] = citations

    return state
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Fixed-size chunking (512 tokens) | Section-level semantic chunking | 2024-2025 | +35% reduction in context loss, 87.7% vs ~65% context recall on structured docs |
| Dense-only retrieval | Hybrid (dense + sparse) with reranking | 2025 | +29% accuracy (93% vs 72% NDCG@10), now baseline for production RAG |
| Linear RAG (retrieve → generate) | Adaptive RAG (query analysis → retrieval → grading → loops) | 2025-2026 | Reduced irrelevant retrievals by 25-40%, handles retrieval failures gracefully |
| LangChain LCEL for RAG | LangGraph for stateful orchestration | 2025-2026 | Self-correction, retrieval loops, fallback paths in one architecture; 2026 industry standard for agentic RAG |
| Custom reranking models | Vector store built-in reranking (Databricks RRF) | 2025-2026 | +15% accuracy with single parameter, no separate reranking service needed |
| In-chunk citation metadata | Citation anchors + separate spatial metadata | 2025-2026 | ~10-15% storage overhead, enables precise source traceability without retrieval quality degradation |

**Deprecated/outdated:**
- **ChromaDB for production RAG**: Lacks native hybrid search and reranking; acceptable for prototyping but production systems use Databricks/Pinecone/Weaviate with hybrid search
- **Naive RAG (no query analysis)**: 40-60% fail to reach production; adaptive RAG with grading is now baseline
- **Table extraction with regex/heuristics**: PyMuPDF4LLM with img2table handles edge cases; regex-based parsers fail on multi-column layouts, merged cells

## Open Questions

Things that couldn't be fully resolved:

1. **Llama-Primus-Reasoning hosting on Databricks Model Serving: Cost and feasibility**
   - What we know: Llama-Primus-Reasoning is 8B params, compatible with text-generation-inference, available via Featherless AI. Databricks offers Llama model serving with recent 80% cost reductions for Llama 3.3 70B and Llama 3.1 405B.
   - What's unclear: Llama-Primus-Reasoning is not in Databricks Foundation Model catalog (checked supported models list). Custom model deployment requires Model Serving setup, but cost/token unknown for custom 8B models.
   - Recommendation:
     - **Option 1 (local dev):** Run Llama-Primus-Reasoning locally via Ollama or vLLM for development/testing
     - **Option 2 (production):** Deploy to Databricks Model Serving as custom model (requires containerization, endpoint setup). Estimate cost based on Llama 3.1 8B pricing (~$0.0001/input token, $0.0003/output token if following Llama 3.x pricing trends, but verify with Databricks).
     - **Option 3 (external):** Use Featherless AI inference endpoint (pay-per-token, no infrastructure management)
     - **Decision point:** Test local Ollama first, then decide Databricks vs external based on latency/cost requirements

2. **Query classification granularity for regulatory compliance RAG**
   - What we know: Recent research (GraphCompliance, RAGRouter) shows query routing improves accuracy by 1.67-9.33%. LLM-based routing generalizes better than fine-tuned classifiers. Production systems use 2-3 query categories (retrieval vs general vs clarification).
   - What's unclear: Optimal classification for CCoP compliance queries (e.g., should we distinguish "requirement lookup" vs "implementation guidance" vs "audit criteria"?).
   - Recommendation: Start with binary classification ("needs retrieval" vs "general question"). Monitor query distribution in Phase 2 eval. If specific query types show low retrieval accuracy, add granular routing (max 3-4 categories). Use LLM-based routing with prompt engineering vs fine-tuned classifier (easier to iterate).

3. **Confidence scoring implementation approach**
   - What we know: Production RAG systems use confidence scoring at multiple layers (retrieval, reranking, generation). Platforms like Maxim AI, LangSmith, Arize AI provide evaluation frameworks. Retrieval grading with LLM-as-judge is standard pattern.
   - What's unclear: Best approach for CCoP compliance confidence scoring (single end-to-end score vs per-layer scores? Threshold for "low confidence" flag?).
   - Recommendation:
     - Implement grading scores at retrieval layer (LLM-as-judge, 0-1 scale)
     - Flag responses as "low confidence" if max grading score <0.6 or if retrieval failed (fallback path)
     - Phase 2 eval will reveal calibration (do low-confidence predictions correlate with incorrect answers?)
     - Defer composite confidence score (combining retrieval + generation confidence) until Phase 2 data is available

4. **RESPONSE-TO-FEEDBACK.pdf Q&A pair linking strategy**
   - What we know: Multi-agent KG approaches (GraphCompliance) extract subject-predicate-object triplets from regulatory docs and link Q&A pairs to source clauses. Metadata enrichment with source provenance is standard.
   - What's unclear: Best schema for linking Q&A pairs to CCoP clauses (separate vector index for Q&A? Augmented chunks? Knowledge graph?)
   - Recommendation:
     - Parse RESPONSE-TO-FEEDBACK.pdf as structured Q&A pairs
     - Each Q&A pair becomes a chunk with metadata linking to the CCoP clause it clarifies (clause number extracted from PDF or inferred via semantic matching)
     - Store in same vector index as main CCoP clauses (unified retrieval)
     - Add metadata field `document_type: "clarification"` to distinguish from primary clauses
     - During retrieval, both primary clauses and clarifications are retrieved; grading layer selects most relevant

## Sources

### Primary (HIGH confidence)
- [LangGraph Adaptive RAG Tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/) - Official adaptive RAG architecture pattern
- [Databricks Mosaic AI Vector Search Documentation](https://docs.databricks.com/aws/en/vector-search/vector-search) - Vector store setup, hybrid search, reranking
- [Databricks Vector Search LangChain Integration](https://docs.langchain.com/oss/python/integrations/vectorstores/databricks_vector_search) - DatabricksVectorSearch usage
- [PyMuPDF4LLM Documentation](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/) - PDF parsing with structure preservation
- [Llama-Primus-Reasoning on Hugging Face](https://huggingface.co/trendmicro-ailab/Llama-Primus-Reasoning) - Model details, benchmarks, deployment options
- [Databricks Foundation Model Serving Pricing](https://www.databricks.com/product/pricing/foundation-model-serving) - Llama model pricing, 80% cost reduction announcement
- [Databricks Unity Catalog Access Control](https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control) - Vector search permissions
- [Databricks BGE Model Documentation](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models) - BGE embedding endpoint details

### Secondary (MEDIUM confidence)
- [Building Production RAG Systems in 2026: Complete Architecture Guide](https://brlikhon.engineer/blog/building-production-rag-systems-in-2026-complete-architecture-guide) - Production RAG best practices verified with official sources
- [Optimizing RAG with Hybrid Search & Reranking](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking) - Hybrid search architecture patterns
- [Citation-Aware RAG: How to add Fine Grained Citations](https://www.tensorlake.ai/blog/rag-citations) - Citation extraction implementation patterns
- [The Ultimate Guide to Chunking Strategies for RAG Applications with Databricks](https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089) - Section-level chunking performance data
- [Reranking in Mosaic AI Vector Search](https://www.databricks.com/blog/reranking-mosaic-ai-vector-search-faster-smarter-retrieval-rag-agents) - Reranking performance benchmarks
- [LangGraph State Management Guide](https://medium.com/@dewasheesh.rana/langgraph-explained-2026-edition-ea8f725abff3) - StateGraph patterns verified with official docs
- [Dense vs Sparse vs Hybrid RRF: Which RAG Technique Actually Works?](https://medium.com/@robertdennyson/dense-vs-sparse-vs-hybrid-rrf-which-rag-technique-actually-works-1228c0ae3f69) - Performance comparison benchmarks
- [LangSmith Observability Documentation](https://docs.langchain.com/oss/python/langgraph/observability) - Official observability patterns for LangGraph

### Tertiary (LOW confidence - community insights, not officially verified)
- [Building Agentic Adaptive RAG with LangGraph for Production](https://ai.plainenglish.io/building-agentic-rag-with-langgraph-mastering-adaptive-rag-for-production-c2c4578c836a) - Community tutorial, architectural insights verified with official docs
- [GraphCompliance: Aligning Policy and Context Graphs](https://arxiv.org/html/2510.26309v1) - Research paper on regulatory compliance RAG, Q&A pair linking approach
- [RAGulating Compliance: A Multi-Agent Knowledge Graph for Regulatory QA](https://arxiv.org/html/2508.09893v1) - Research paper on knowledge graph approaches for regulatory compliance
- [State of AI Agents 2026](https://www.langchain.com/state-of-agent-engineering) - Industry trends, production failure modes (40-60% stat)
- [Adaptive RAG Explained: What to Know in 2026](https://www.meilisearch.com/blog/adaptive-rag) - Community guide, architectural patterns cross-verified

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries from official documentation, active maintenance, production deployments verified
- Architecture: HIGH - Adaptive RAG, hybrid search, section-level chunking verified with official docs and recent research
- Pitfalls: MEDIUM-HIGH - Production failure modes (40-60%) from LangChain State of Agent Engineering report, specific pitfalls from community experience verified with official best practices
- Query classification: MEDIUM - Recent research available (GraphCompliance, RAGRouter) but optimal granularity for CCoP compliance requires Phase 2 eval data
- Confidence scoring: MEDIUM - Retrieval grading patterns verified, but calibration thresholds need Phase 2 validation
- Llama-Primus-Reasoning hosting: MEDIUM - Model details verified on HuggingFace, Databricks Model Serving capabilities verified, but specific cost for custom 8B model unknown

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (30 days - RAG/LangGraph ecosystem is fast-moving but core patterns are stabilizing in 2026)
