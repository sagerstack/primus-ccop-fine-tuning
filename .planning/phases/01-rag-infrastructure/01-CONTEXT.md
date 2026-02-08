# Phase 1: RAG Infrastructure - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Build document ingestion, vector storage, and retrieval pipeline for CCoP 2.0 documents using LangChain + LangGraph + Databricks. Returns relevant clauses with citations for compliance queries. End-to-end adaptive RAG with self-correcting retrieval loops.

This is the learning-priority phase -- RAG implementation is the primary skill acquisition goal.

Evaluation against the existing 118 test cases (49.2% baseline) happens in Phase 2. Dataset expansion happens later in Phase 3, informed by RAG evaluation gaps.

</domain>

<decisions>
## Implementation Decisions

### Roadmap Reorder
- Original order: Dataset Expansion -> Baseline -> RAG -> RAG Eval
- New order: RAG Infrastructure -> RAG Evaluation (118 cases) -> Dataset Expansion -> Re-baseline + Re-evaluate
- Motivation: Learning RAG implementation is the priority
- Existing 49.2% baseline (from Phase 1 paper) serves as comparison point -- no need to re-run base model before RAG eval
- First two phases are about completing and validating the setup

### Document Ingestion
- All 8 CCoP documents ingested (main CCoP + 7 supplementary documents)
- Structure preservation is critical: clause numbers, section hierarchy, and table content must be captured as metadata
- Section-level chunking -- each numbered section is a chunk
- Tables converted to natural language for semantic searchability
- RESPONSE-TO-FEEDBACK.pdf parsed as Q&A pairs, each linked to the CCoP clause it clarifies
- One-time batch ingestion (no incremental/re-runnable pipeline needed)
- PDF parsing via LangChain document loaders

### Retrieval Pipeline (LangGraph Adaptive RAG)
- End-to-end LangGraph graph: query analysis -> retrieval -> grading -> response generation -> grounding verification
- LangChain provides building blocks (retrievers, embeddings, prompt templates, LLM integrations)
- LangGraph provides orchestration (stateful graph with loops, branches, self-correction)
- Query classification approach: determined by research (investigate latest papers on query routing for RAG in regulatory/compliance domains)
- Failed retrieval handling: when no relevant context is found, query goes to model without RAG augmentation
- Failed retrievals are logged with query, attempted retrievals, and grading scores -- this log feeds Phase 4 (RAG Eval) and Phase 5 (Fine-Tuning) to identify which query types need fine-tuning vs retrieval
- Retrieval failure fallback strategy: research best practice for adaptive RAG (reformulate, expand, or graceful degradation)
- LLM for response generation: Llama-Primus-Reasoning (hosting approach TBD pending research on Databricks Model Serving feasibility)
- Always transparent: every response indicates whether it was RAG-augmented or model-only

### Citation & Output Format
- End-of-response references (clean response text, sources listed at bottom)
- Citation detail level: Document + Section + Clause (e.g., "CCoP 2.0, Section 5: Access Control, Clause 5.2.1")
- Confidence scoring: research best practice before deciding (investigate how production RAG systems handle confidence scoring)

### Framework & Tooling
- LangChain + LangGraph (LangGraph orchestrates, LangChain provides components)
- Databricks as vector store (Mosaic AI Vector Search) -- paid workspace available
- Databricks BGE embedding endpoint for text-to-vector conversion
- Develop locally, deploy to Databricks for evaluation runs (both environments)
- Databricks connectivity via .env.local (DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_CATALOG, DATABRICKS_SCHEMA)
- No LangSmith -- standard Python logging for observability

### Claude's Discretion
- Specific LangGraph graph node/edge design
- Re-ranking strategy (dense, hybrid, sparse)
- Text splitter configuration details
- Error handling and retry logic within graph nodes
- Local development setup specifics

</decisions>

<specifics>
## Specific Ideas

- "I want to learn how to implement RAG as a priority" -- this phase is as much about skill acquisition as deliverable
- After RAG eval on 118 cases, the gap analysis informs which benchmarks need more test cases during dataset expansion
- Both base model AND RAG-augmented model get re-evaluated after dataset expansion for statistically valid comparison
- Failed retrievals are a feature, not a bug -- they identify fine-tuning needs

</specifics>

<deferred>
## Deferred Ideas

- Quality validation strategy for generated data -- discuss when dataset expansion (Phase 3) becomes active
- Benchmark distribution strategy (1000+ cases across 21 benchmarks) -- Phase 3 discussion
- Output format decisions (JSONL schema, instruction-tuning format) -- Phase 3 discussion
- External dataset research (NIST, ISO 27001, CCoP datasets) -- Phase 3 research task
- Dataset generation approach: no LangGraph, plain Python with tier-specific prompt templates -- Phase 3

</deferred>

## Research Items for Downstream Researcher

1. Query classification approach for RAG in regulatory/compliance domains (latest papers)
2. Best practice for handling retrieval failures in adaptive RAG systems
3. Databricks Model Serving feasibility and cost for hosting Llama-Primus-Reasoning
4. Confidence scoring in production RAG systems

---

*Phase: 01-rag-infrastructure*
*Context gathered: 2026-02-07*
