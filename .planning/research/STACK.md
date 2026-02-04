# Technology Stack

**Project:** CCoP 2.0 Compliance Assistant (Hybrid Fine-tuning + RAG)
**Researched:** 2026-02-04
**Overall Confidence:** HIGH

## Executive Summary

The 2026 stack for a hybrid fine-tuned + RAG compliance assistant prioritizes production-grade accuracy, domain specialization, and on-premise deployment capability. Key decisions favor legal-specialized embeddings (vstackai-law-1), structure-aware PDF parsing (Docling), hybrid retrieval with ColBERT re-ranking, and QLoRA fine-tuning via Unsloth. ChromaDB serves as the vector store, with LlamaIndex orchestrating the hybrid architecture. All components support air-gapped deployment critical for CII environments.

---

## Recommended Stack

### 1. Document Processing & Parsing

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **Docling** | Latest (2026) | PDF parsing, layout analysis, table extraction | Open-source, specialized AI models for layout (DocLayNet) and tables (TableFormer), 9/10 accuracy on financial PDFs, modular pipeline, self-hostable for air-gapped environments |
| **PyMuPDF** | ^1.24.0 | Fallback/fast text extraction | Extremely fast (<1s), reliable for simple PDFs, complements Docling for text-heavy documents |
| **LangChain Document Loaders** | ^0.3.0 | Document ingestion abstraction | Unified interface for multiple formats, preprocessing utilities |

**Chunking Strategy:**
- **Semantic Chunking with Structure Awareness** (custom implementation)
  - Extract document hierarchy (sections, subsections, clauses)
  - Chunk at semantic boundaries (200-1000 tokens)
  - Preserve metadata: section_id, clause_number, document_type, parent_section
  - 35% reduction in context loss vs fixed-size chunking

**Confidence:** HIGH
- Docling verified via official docs and recent benchmarks
- Structure-aware chunking validated in legal RAG research (2025)

### 2. Embeddings

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **vstackai-law-1** | Latest | Primary embeddings for legal/compliance text | Tops MTEB legal leaderboard, 32K token context (no chunking needed for most docs), outperforms OpenAI text-embedding-3-large and voyage-law-2 |
| **sentence-transformers** | ^3.3.1 (existing) | Embedding infrastructure | Already in project, supports custom models, Python 3.13 compatible |
| **Fallback: voyage-law-2** | API | Alternative if vstackai-law-1 unavailable | 16K context, tops MTEB leaderboard by 6% over OpenAI, proven in production |

**Why NOT:**
- ❌ **OpenAI text-embedding-3-large**: Generic, not legal-specialized, 6-10% lower accuracy on legal retrieval tasks
- ❌ **BAAI/bge-base-en**: General-purpose, lower accuracy for compliance-specific terminology
- ❌ **Fine-tuning embeddings**: Unnecessary given vstackai-law-1's specialization, adds complexity

**Confidence:** HIGH
- vstackai-law-1 verified via Milvus, VectorStack official sources
- voyage-law-2 verified via Voyage AI blog and MTEB leaderboard

### 3. Vector Storage

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **ChromaDB** | ^0.5.0 | Vector database | Rust-core rewrite (4x performance), 3-tier storage (buffer→HNSW→Arrow), built-in metadata filtering, self-hostable, no external dependencies, supports billion-scale embeddings |
| **HNSW Index** | Built-in | Fast approximate search | Default in ChromaDB, balances accuracy and speed |

**Configuration:**
```python
# Optimized for compliance retrieval
chroma_client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

collection = chroma_client.create_collection(
    name="ccop_compliance",
    metadata={
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 200,  # Higher for better accuracy
        "hnsw:search_ef": 100,
    },
    embedding_function=vstackai_law_1_embedder
)
```

**Metadata Schema:**
```python
{
    "document_id": "ccop-2.0-section-5.3.2",
    "section": "5.3.2",
    "section_title": "Change Management Logging",
    "clause_type": "IT|OT|BOTH",
    "parent_section": "5.3",
    "document_source": "CCoP-SecondEdition_Revision-One.pdf",
    "page_number": 42,
    "chunk_index": 3,
    "token_count": 487
}
```

**Why NOT:**
- ❌ **Pinecone/Weaviate**: Cloud-dependent, cannot run air-gapped, cost scaling issues
- ❌ **FAISS**: Requires more manual management, no built-in metadata filtering, harder to scale

**Confidence:** HIGH
- ChromaDB Rust rewrite verified via official docs and Airbyte guide
- HNSW configuration based on ChromaDB documentation

### 4. Retrieval & Re-ranking

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **Hybrid Search** | Custom | Combine dense + sparse retrieval | Industry standard 2026, 20-40% precision improvement over dense-only |
| **BM25** | via rank-bm25 ^0.2.2 | Keyword/sparse retrieval | Lightweight, complements dense embeddings, good for exact clause citations |
| **ColBERT v2** | via ragatouille ^0.0.8 | Re-ranking | Late-interaction model, 10-50ms latency, self-hostable, outperforms single-vector by preserving token-level matching |
| **RRF (Reciprocal Rank Fusion)** | Custom | Fuse dense + sparse results | Standard fusion method, simple and effective |

**Retrieval Pipeline:**
```
1. Dense retrieval (top 100 from ChromaDB)
2. Sparse retrieval (top 100 from BM25)
3. Fusion via RRF → top 100 candidates
4. ColBERT re-ranking → top 10 for context
5. Citation extraction → link to source clauses
```

**Alternative (API-based):**
- **Cohere Rerank 3.5**: Fastest (595ms), highest accuracy, but requires API access (not air-gapped compatible)
- Use for cloud deployments or validation benchmarking

**Why NOT:**
- ❌ **Dense-only retrieval**: 20-40% lower precision, misses exact keyword matches
- ❌ **LLM-as-reranker** (GPT-4, etc.): Too slow (2-5s per batch), expensive, inconsistent
- ❌ **Full cross-encoder on all candidates**: Too slow for production (>1s), ColBERT provides 90% of benefit at 10% cost

**Confidence:** HIGH
- Hybrid search + ColBERT verified via multiple 2025-2026 production sources
- RRF standard validated in Neo4j, Superlinked guides

### 5. Fine-Tuning (QLoRA)

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **Unsloth** | ^2024.12 | QLoRA training acceleration | 2-5x faster, 80% memory reduction, single GPU optimized, 0% accuracy loss, ideal for resource constraints |
| **Axolotl** | ^0.4.0 | Training orchestration & config | Battle-tested, YAML-based config, LoRA/QLoRA/full fine-tune support, integrates with Unsloth, scales to multi-GPU if needed |
| **bitsandbytes** | ^0.44.0 | 4-bit quantization | Industry standard for QLoRA, required dependency |
| **PEFT** | ^0.13.0 | LoRA adapters | HuggingFace PEFT library, adapter management |
| **transformers** | ^4.47.0 | Model loading & inference | HuggingFace transformers, base infrastructure |

**Training Configuration (via Axolotl YAML):**
```yaml
base_model: trendmicro-ailab/Llama-Primus-Reasoning
model_type: LlamaForCausalLM
load_in_4bit: true
adapter: lora
lora_r: 64
lora_alpha: 16
lora_dropout: 0.05
lora_target_modules:
  - q_proj
  - v_proj
  - k_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj

# Training hyperparameters
sequence_len: 4096
micro_batch_size: 1
gradient_accumulation_steps: 4
num_epochs: 3
learning_rate: 0.0002
lr_scheduler: cosine
warmup_steps: 100

# Evaluation
eval_sample_packing: false
evals_per_epoch: 4
saves_per_epoch: 2

# Unsloth optimization
plugins:
  - unsloth
```

**Why Unsloth over Alternatives:**
- ✅ **vs Axolotl-only**: Unsloth gives 2-5x speed boost, critical for iterative experimentation
- ✅ **vs LLaMA-Factory**: Unsloth faster, simpler for single-GPU; LLaMA-Factory better for multi-model management
- ✅ **vs Native PyTorch**: Unsloth abstracts away CUDA optimization, maintains accuracy

**Why NOT:**
- ❌ **Full fine-tuning**: 16x more memory, 10x slower, no accuracy benefit for domain adaptation
- ❌ **Multi-GPU** (for Phase 4-6): Single GPU sufficient with Unsloth, multi-GPU adds complexity without benefit at 5K examples scale

**Confidence:** HIGH
- Unsloth verified via official docs and 2026 framework comparisons
- Axolotl configuration validated via official documentation

### 6. Dataset Generation

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **OpenAI API** (GPT-4o) | Latest | Synthetic QA generation | Most capable for legal/compliance synthesis, used in AutoLaw (2025) for Singapore regulation scenarios, strong few-shot learning |
| **Gemini Pro** | Latest (API) | Alternative generator | Used in SynLexLM (2025) for legal data augmentation, good at question generation |
| **Self-Instruct Pipeline** | Custom | Structured generation | Formalized instruction-response pairs, filtering invalid/redundant samples |

**Dataset Generation Pipeline:**
```
1. Source: CCoP 2.0 PDFs + supplementary docs (8 docs total)
2. Extraction: Docling → structured sections
3. Synthesis:
   a. GPT-4o generates QA pairs from sections
   b. Curriculum progression: simple → complex
   c. Categories: interpretation, citation, code violation, IaC, incident classification
4. Validation:
   a. Expert review (manual)
   b. Duplicate detection (embedding similarity)
   c. Hallucination check (grounding verification)
5. Augmentation:
   a. Paraphrasing (GPT-4o)
   b. Multi-turn conversations
   c. Negative examples (non-violations)
6. Quality control:
   a. Target: >90% expert approval rate
   b. Diversity: Ensure all 11 CCoP sections represented
   c. Balance: 60% IT/OT overlap, 20% IT-only, 20% OT-only
```

**Data Format (JSON):**
```json
{
  "id": "ccop-train-0042",
  "category": "code_violation_detection",
  "section": "5.3.2",
  "clause": "Change management procedures must log all configuration changes",
  "instruction": "Analyze this Terraform code for CCoP 2.0 compliance violations in change management logging.",
  "input": "<terraform code>",
  "output": "VIOLATION: Section 5.3.2 - No audit logging configured...",
  "reasoning": "<step-by-step>",
  "metadata": {
    "difficulty": "medium",
    "infrastructure_type": "IaC",
    "clause_type": "BOTH"
  }
}
```

**Why NOT:**
- ❌ **Smaller models (Llama-3-8B) for generation**: Lower quality, higher hallucination risk for legal content
- ❌ **Pure rule-based generation**: Insufficient diversity, brittle, doesn't capture nuance
- ❌ **No validation pipeline**: Legal content requires expert validation, can't skip quality control

**Confidence:** MEDIUM
- GPT-4o validated via AutoLaw (2025) research on Singapore regulations
- Self-Instruct pipeline validated via 2025 domain adaptation research
- Specific GPT-4o performance on CCoP 2.0 generation unverified (LOW for exact performance)

### 7. Hybrid Orchestration (RAG + Fine-tuned)

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **LlamaIndex** | ^0.12.0 | RAG orchestration | Most mature RAG framework 2026, modular architecture, supports hybrid retrieval, query engines, agent workflows |
| **LangChain** | ^0.3.0 | Alternative orchestration | More flexible for custom workflows, LangGraph for agent orchestration, LangSmith for observability |
| **Custom Integration Layer** | - | RAG → Fine-tuned handoff | Routes query based on type: retrieval-heavy → RAG, reasoning-heavy → fine-tuned model |

**Hybrid Architecture:**
```
Query → Query Router
         ├─> RAG Path (retrieval-heavy)
         │   ├─> Hybrid Search (ChromaDB + BM25)
         │   ├─> ColBERT Rerank
         │   ├─> Context Assembly (top 10 chunks)
         │   └─> Fine-tuned Model (context-augmented)
         │
         └─> Reasoning Path (reasoning-heavy)
             └─> Fine-tuned Model (zero-shot or few-shot)

Response → Citation Extractor → Final Output
```

**Query Classification:**
- **Retrieval-heavy**: "What does Clause 5.3.2 require?", "List all incident response clauses"
- **Reasoning-heavy**: "Is this code compliant?", "Classify this incident", "Generate gap analysis"
- **Hybrid**: "Does this AWS config violate CCoP 2.0?" (retrieve relevant clauses + reason over code)

**Implementation (LlamaIndex):**
```python
from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

# RAG setup
vector_retriever = VectorIndexRetriever(
    index=vector_index,
    similarity_top_k=100,
)

reranker = ColBERTReranker(top_n=10)

query_engine = RetrieverQueryEngine(
    retriever=vector_retriever,
    node_postprocessors=[reranker],
    response_synthesizer=response_synthesizer,
)

# Hybrid router
def route_query(query: str) -> str:
    if is_retrieval_query(query):
        context = query_engine.query(query)
        return fine_tuned_model(query, context=context)
    else:
        return fine_tuned_model(query)
```

**Why LlamaIndex over LangChain:**
- ✅ **RAG-first design**: Purpose-built for retrieval workflows
- ✅ **Simpler abstractions**: Less boilerplate for standard RAG patterns
- ✅ **Better indexing**: Built-in vector store integrations, query engines
- ⚖️ **LangChain alternative**: Better for complex agents, custom workflows, more LLM integrations

**Why NOT:**
- ❌ **Always using RAG**: Slows down reasoning tasks, adds latency, unnecessary for memorized knowledge
- ❌ **Always using fine-tuned only**: Misses recent updates, lower accuracy on factual lookup
- ❌ **No router (random selection)**: Inefficient, inconsistent performance

**Confidence:** HIGH
- LlamaIndex vs LangChain validated via 2026 framework comparisons
- Hybrid routing pattern validated in AWS ML blog (2024) and Matillion guide (2025)

### 8. Evaluation & Monitoring

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **SelfCheckGPT** | ^0.2.0 | Hallucination detection | Zero-resource, measures self-consistency across multiple responses, standard in 2026 |
| **RAGAS** | ^0.2.0 | RAG evaluation metrics | Context precision, context recall, faithfulness, answer relevance, industry standard |
| **LangSmith** (optional) | API | Training/inference observability | Traces, debugging, experiment tracking (cloud-based, not for air-gapped) |
| **Weights & Biases** | ^0.18.0 | Training monitoring | Experiment tracking, hyperparameter logging, loss curves, self-hostable |
| **Custom Benchmark Suite** | - | 19 CCoP-specific benchmarks | As defined in project paper (B1-B19) |

**Hallucination Detection Pipeline:**
```
1. Generate response
2. SelfCheckGPT: Sample 5 responses, measure consistency
3. RAGAS faithfulness: Check against retrieved context
4. Citation verification: Ensure all claims have source
5. Score threshold: <5% hallucination rate
```

**Training Monitoring:**
```python
# Weights & Biases integration
import wandb

wandb.init(
    project="ccop-finetuning",
    config={
        "learning_rate": 0.0002,
        "epochs": 3,
        "batch_size": 4,
    }
)

# Log during training
wandb.log({
    "train_loss": loss,
    "eval_loss": eval_loss,
    "perplexity": perplexity,
    "hallucination_rate": hallucination_rate,
})
```

**Why NOT:**
- ❌ **No hallucination detection**: Unacceptable for compliance, 5% threshold requirement
- ❌ **Generic metrics only** (accuracy, F1): Insufficient for RAG, need faithfulness, context relevance
- ❌ **Manual evaluation only**: Doesn't scale to 5K+ training examples, need automated + manual

**Confidence:** HIGH
- SelfCheckGPT verified via 2025 hallucination detection research
- RAGAS verified as industry standard via multiple sources

---

## Supporting Libraries (Existing Project)

### Already in Use (Keep)

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| pydantic | ^2.5.0 | Data validation, DTOs | Core to application layer |
| structlog | ^24.1.0 | Structured logging | Production-grade logging |
| sentence-transformers | ^3.3.1 | Embedding infrastructure | Keep, supports vstackai-law-1 |
| torch | ^2.5.0 | PyTorch backend | Required for embeddings, fine-tuning |
| openai | ^1.50.0 | OpenAI-compatible client | Works with Ollama, GPT-4o |
| httpx | ^0.27.0 | HTTP client | Ollama API, external services |
| click | 8.1.7 | CLI framework | Core to presentation layer |
| rich | ^13.7.0 | Terminal output | Enhanced UX |
| typer | ^0.12.5 | Type-safe CLI | Built on Click |
| pytest | ^7.4.0 | Testing framework | Essential |
| dependency-injector | ^4.41.0 | DI container | Clean architecture |

### New Dependencies

```toml
[tool.poetry.dependencies]
# Document processing
docling = "^0.1.0"
pymupdf = "^1.24.0"

# Embeddings
# Note: vstackai-law-1 integration via sentence-transformers API

# Vector storage
chromadb = "^0.5.0"

# Retrieval
rank-bm25 = "^0.2.2"
ragatouille = "^0.0.8"  # ColBERT

# RAG orchestration
llama-index = "^0.12.0"
llama-index-vector-stores-chroma = "^0.4.0"

# Fine-tuning
unsloth = {version = "^2024.12", source = "pypi"}
axolotl = "^0.4.0"
bitsandbytes = "^0.44.0"
peft = "^0.13.0"
transformers = "^4.47.0"

# Evaluation
ragas = "^0.2.0"
selfcheckgpt = "^0.2.0"
wandb = "^0.18.0"

[tool.poetry.group.dev.dependencies]
# Keep existing dev dependencies
```

---

## Installation

```bash
# Core dependencies
poetry add docling pymupdf chromadb rank-bm25 ragatouille
poetry add llama-index llama-index-vector-stores-chroma
poetry add unsloth axolotl bitsandbytes peft transformers
poetry add ragas selfcheckgpt wandb

# Note: vstackai-law-1 requires API key or model download
# Setup via sentence-transformers custom model loading
```

---

## Anti-Recommendations

### What to Avoid

| Technology | Why Avoid | Better Alternative |
|------------|-----------|-------------------|
| **LlamaParse** | Cloud-only, skips critical sections in complex docs, slower (53s) | Docling (self-hosted, 9/10 accuracy) |
| **Pinecone/Weaviate** | Cloud-dependent, cannot run air-gapped | ChromaDB (self-hosted) |
| **OpenAI text-embedding-3-large** | Generic, 6-10% lower accuracy on legal text | vstackai-law-1 (legal-specialized) |
| **Dense-only retrieval** | 20-40% lower precision, misses keyword matches | Hybrid search (dense + BM25) |
| **LLM-as-reranker** (GPT-4) | Too slow (2-5s), expensive, inconsistent | ColBERT (10-50ms, consistent) |
| **Full fine-tuning** | 16x memory, 10x slower, no accuracy gain | QLoRA via Unsloth |
| **Multi-GPU training** (for this scale) | Unnecessary complexity at 5K examples | Unsloth single GPU (sufficient) |
| **No hallucination detection** | Violates <5% hallucination requirement | SelfCheckGPT + RAGAS |
| **Cohere Rerank** (for air-gapped) | API-only, cloud-dependent | ColBERT (self-hosted) |
| **Smaller LLMs for dataset generation** | Higher hallucination risk on legal content | GPT-4o (validated on Singapore regs) |

---

## Deployment Considerations

### Air-Gapped Environment (CII Requirement)

**Self-Hosted Stack:**
- ✅ Docling (open-source)
- ✅ ChromaDB (local persistent storage)
- ✅ ColBERT (self-hosted model)
- ✅ Unsloth + Axolotl (local training)
- ✅ Fine-tuned Llama-Primus (Ollama deployment)
- ✅ BM25 (pure Python)

**Cloud-Based (for development/validation only):**
- Cohere Rerank (benchmarking)
- GPT-4o (dataset generation)
- LangSmith (training observability)
- Voyage-law-2 embeddings (validation)

**Hybrid Development:**
1. **Development phase**: Use cloud services for dataset generation, validation
2. **Production deployment**: All components self-hosted, air-gapped compatible

### Hardware Requirements

**Fine-Tuning (Unsloth optimized):**
- GPU: 1x NVIDIA A100 40GB or 1x RTX 4090 24GB
- RAM: 32GB system RAM
- Storage: 500GB SSD (model checkpoints, datasets)
- Training time: ~8-12 hours for 5K examples, 3 epochs

**Inference (RAG + Fine-tuned):**
- GPU: 1x RTX 4090 24GB or 1x A100 40GB (quantized model)
- RAM: 64GB (vector DB + model in memory)
- Storage: 100GB SSD (vector DB, model weights)
- Latency: <2s per query (target)

---

## Version Compatibility Matrix

| Component | Python | CUDA | PyTorch |
|-----------|--------|------|---------|
| Unsloth | 3.10-3.13 | 11.8+ | 2.5.0+ |
| ChromaDB | 3.10+ | N/A | N/A |
| sentence-transformers | 3.10-3.13 | 11.8+ | 2.5.0+ |
| Docling | 3.10+ | N/A | N/A |
| Axolotl | 3.10-3.11 | 11.8+ | 2.5.0+ |

**Current Project:** Python 3.10+ (per pyproject.toml)
**Recommendation:** Python 3.11 for stability, 3.13 for latest features (all libraries compatible)

---

## Migration Path from Current State

### Phase 1: RAG Layer (Parallel to existing work)
1. Install Docling, ChromaDB, BM25, ColBERT
2. Parse 8 CCoP PDFs with Docling
3. Generate embeddings with vstackai-law-1
4. Index in ChromaDB with metadata
5. Implement hybrid search + ColBERT reranking
6. Integrate with existing evaluation framework (benchmarks B1-B5)

### Phase 2: Fine-Tuning Enhancement
1. Install Unsloth, Axolotl
2. Generate synthetic dataset (118 → 1000+ examples) using GPT-4o
3. Expert validation pipeline
4. Fine-tune Llama-Primus with QLoRA
5. Evaluate against benchmarks B1-B19

### Phase 3: Hybrid Integration
1. Install LlamaIndex
2. Implement query router
3. Integrate RAG context with fine-tuned model
4. Add citation extraction
5. Deploy hallucination detection (SelfCheckGPT + RAGAS)
6. Final validation against 85% accuracy target

---

## Confidence Assessment

| Stack Component | Confidence | Source |
|----------------|------------|--------|
| **Document Processing** (Docling) | HIGH | Official docs, 2025-2026 benchmarks, verified performance |
| **Embeddings** (vstackai-law-1) | HIGH | MTEB leaderboard, VectorStack official sources, legal specialization validated |
| **Vector Storage** (ChromaDB) | HIGH | Official docs, Rust rewrite verified, production adoption confirmed |
| **Retrieval** (Hybrid + ColBERT) | HIGH | Multiple 2026 production sources, industry standard |
| **Fine-Tuning** (Unsloth + Axolotl) | HIGH | Official docs, 2026 framework comparisons, performance verified |
| **Dataset Generation** (GPT-4o) | MEDIUM | AutoLaw research (Singapore regs), but CCoP-specific generation unverified |
| **Orchestration** (LlamaIndex) | HIGH | 2026 framework comparisons, production adoption, official docs |
| **Evaluation** (SelfCheckGPT, RAGAS) | HIGH | 2025-2026 research papers, industry standard |

**Overall Stack Confidence: HIGH**

---

## Open Questions / Future Validation

1. **vstackai-law-1 licensing**: Verify commercial use terms for CII deployment
2. **CCoP-specific dataset quality**: Validate GPT-4o generation accuracy on Singapore regulations (requires expert review)
3. **ColBERT latency at scale**: Benchmark on full 8-document corpus (220 clauses)
4. **Hybrid router accuracy**: Test query classification on CCoP-specific queries
5. **Air-gapped model downloads**: Confirm Hugging Face model caching for offline deployment

---

## Sources

### Document Processing & PDF Parsing
- [RAG for Legal Documents - ReadyTensor](https://app.readytensor.ai/publications/rag-for-legal-documents-an-open-source-system-for-legal-document-intelligence-HaYlApIv7Mkt)
- [Legal Document RAG: Multi-Graph Multi-Agent - Medium](https://medium.com/enterprise-rag/legal-document-rag-multi-graph-multi-agent-recursive-retrieval-through-legal-clauses-c90e073e0052)
- [5 Best Document Parsers 2026 - F22Labs](https://www.f22labs.com/blogs/5-best-document-parsers-in-2025-tested/)
- [Best Python PDF to Text Parser Libraries 2026 - Unstract](https://unstract.com/blog/evaluating-python-pdf-to-text-libraries/)

### Embeddings
- [Legal Embedding Models - Milvus](https://milvus.io/ai-quick-reference/what-types-of-embedding-models-are-best-for-legal-documents)
- [voyage-law-2 - Voyage AI](https://blog.voyageai.com/2024/04/15/domain-specific-embeddings-and-retrieval-legal-edition-voyage-law-2/)
- [vstackai-law-1 - VectorStack](https://www.vectorstack.ai/blog/best-in-class-legal-domain-embeddings-vstackai-law-1)
- [Top Embedding Models 2026 - ArtSmart](https://artsmart.ai/blog/top-embedding-models-in-2025/)

### Vector Storage
- [ChromaDB Official](https://www.trychroma.com/)
- [ChromaDB Vector Embeddings - Airbyte](https://airbyte.com/data-engineering-resources/chroma-db-vector-embeddings)
- [Metadata Filtering Vector Databases - Dataquest](https://www.dataquest.io/blog/metadata-filtering-and-hybrid-search-for-vector-databases/)

### Retrieval & Re-ranking
- [Advanced RAG: Hybrid Search and Re-ranking - DEV](https://dev.to/kuldeep_paul/advanced-rag-from-naive-retrieval-to-hybrid-search-and-re-ranking-4km3)
- [Advanced RAG Techniques - Neo4j](https://neo4j.com/blog/genai/advanced-rag-techniques/)
- [Optimizing RAG with Hybrid Search - Superlinked](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking)
- [Top 7 Rerankers for RAG - Analytics Vidhya](https://www.analyticsvidhya.com/blog/2025/06/top-rerankers-for-rag/)
- [ColBERT and Friends - Medium](https://medium.com/@2nick2patel2/colbert-and-friends-re-ranking-that-feels-instant-6c09102b7526)

### Fine-Tuning
- [Comparing LLM Fine-Tuning Frameworks - Spheron](https://blog.spheron.network/comparing-llm-fine-tuning-frameworks-axolotl-unsloth-and-torchtune-in-2025)
- [Best Frameworks for Fine-Tuning LLMs 2025 - Modal](https://modal.com/blog/fine-tuning-llms)
- [Unsloth Documentation](https://docs.unsloth.ai/get-started/fine-tuning-llms-guide)

### Dataset Generation
- [AutoLaw: Singapore Regulations - arXiv](https://arxiv.org/html/2505.14015)
- [Enhancing Legal QA with Data Generation - Springer](https://link.springer.com/article/10.1007/s10506-025-09463-9)
- [SynLexLM: Legal LLMs with Synthetic Data - arXiv](https://arxiv.org/html/2504.18762)

### Hybrid Orchestration
- [15 Best RAG Frameworks 2026 - Firecrawl](https://www.firecrawl.dev/blog/best-open-source-rag-frameworks)
- [Hybrid RAG Architecture - TechAhead](https://www.techaheadcorp.com/blog/hybrid-rag-architecture-definition-benefits-use-cases/)
- [RAG vs Fine-Tuning - AWS ML Blog](https://aws.amazon.com/blogs/machine-learning/tailoring-foundation-models-for-your-business-needs-a-comprehensive-guide-to-rag-fine-tuning-and-hybrid-approaches/)

### Chunking Strategies
- [Semantic Chunking - RAG About It](https://ragaboutit.com/the-chunking-strategy-shift-why-semantic-boundaries-cut-your-rag-errors-by-60/)
- [Legal Chunking: Evaluating Methods - ResearchGate](https://www.researchgate.net/publication/386472016_Legal_Chunking_Evaluating_Methods_for_Effective_Legal_Text_Retrieval)
- [Mastering Document Chunking - Medium](https://medium.com/@sahin.samia/mastering-document-chunking-strategies-for-retrieval-augmented-generation-rag-c9c16785efc7)

### Evaluation & Hallucination Detection
- [Hallucination Detection and Mitigation - arXiv](https://arxiv.org/pdf/2601.09929)
- [LLM Hallucinations 2025 - Lakera](https://www.lakera.ai/blog/guide-to-hallucinations-in-large-language-models)
- [Detecting Hallucinations with LLM-as-a-Judge - Datadog](https://www.datadoghq.com/blog/ai/llm-hallucination-detection/)
