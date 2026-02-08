# Phase 1: RAG Infrastructure - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Build document ingestion, vector storage, and retrieval pipeline for CCoP 2.0 documents. Returns relevant clauses with citations for compliance queries. This is the learning-priority phase — RAG implementation is the primary skill acquisition goal.

Evaluation against the existing 118 test cases (49.2% baseline) happens in Phase 2. Dataset expansion happens later in Phase 3, informed by RAG evaluation gaps.

</domain>

<decisions>
## Implementation Decisions

### Roadmap Reorder
- Original order: Dataset Expansion → Baseline → RAG → RAG Eval
- New order: RAG Infrastructure → RAG Evaluation (118 cases) → Dataset Expansion → Re-baseline + Re-evaluate
- Motivation: Learning RAG implementation is the priority
- Existing 49.2% baseline (from Phase 1 paper) serves as comparison point — no need to re-run base model before RAG eval
- First two phases are about completing and validating the setup

### Dataset Generation (deferred to Phase 3)
- No LangGraph — plain Python script with structured prompting
- Tier-specific prompt templates for factual, reasoning, safety tiers
- Multi-source questions: CIIO practitioner scenarios + audit/assessment questions + existing cybersecurity compliance datasets (NIST, ISO 27001, etc.) adapted to CCoP + any existing CCoP-specific datasets
- Research needed: publicly available cybersecurity compliance datasets and existing CCoP question datasets

### Claude's Discretion
- RAG architecture choices (vector DB, embedding model, chunking strategy)
- Retrieval pipeline design (dense, hybrid, re-ranking)
- Integration approach with existing codebase
- Citation extraction method

</decisions>

<specifics>
## Specific Ideas

- "I want to learn how to implement RAG as a priority" — this phase is as much about skill acquisition as deliverable
- After RAG eval on 118 cases, the gap analysis informs which benchmarks need more test cases during dataset expansion
- Both base model AND RAG-augmented model get re-evaluated after dataset expansion for statistically valid comparison

</specifics>

<deferred>
## Deferred Ideas

- Quality validation strategy for generated data (deterministic checks, expert review, circularity problem) — discuss when dataset expansion becomes active phase
- Benchmark distribution strategy (how to balance 1000+ cases across 21 benchmarks) — discuss when dataset expansion becomes active phase
- Output format decisions (JSONL schema, instruction-tuning format) — discuss when dataset expansion becomes active phase
- External dataset research (NIST, ISO 27001, CCoP datasets) — research task during dataset expansion phase

</deferred>

---

*Phase: 01-rag-infrastructure*
*Context gathered: 2026-02-07*
