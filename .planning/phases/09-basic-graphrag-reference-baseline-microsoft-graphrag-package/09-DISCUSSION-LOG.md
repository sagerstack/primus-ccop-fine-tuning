# Phase 9: Basic GraphRAG baseline (Neo4j, emergent KG) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-01
**Phase:** 09-basic-graphrag-baseline-neo4j-emergent-kg
**Areas discussed:** Engine/framework reframe, Indexing input, Backend parity, Config fidelity, Search mode, Eval integration & --mode, Storage (Neo4j vs Microsoft graphrag), Phase-9→10 additivity, Comparison scope

---

## Cross-cutting constraints (set by user up front)
- Phase 10 must be **additive** — tech/SDK choices aligned & compatible, nothing Phase 10 rips out.
- **Each phase gets a `--mode` toggle** (consistent with existing `--mode hybrid`/`--mode llm-only`).

---

## Indexing input

| Option | Description | Selected |
|--------|-------------|----------|
| Same Docling-parsed text, graphrag's own chunking | Input held constant vs hybrid; isolates graph-vs-vector retrieval | ✓ |
| Raw CCoP PDFs → parse from scratch | Most literal OOTB; but graphrag/neo4j-graphrag has no PDF parser, and naive extraction is known-worse (dec [01.3-01]) | |
| Pre-chunked clause units | Starves prose-based entity extraction | |

**User's choice:** Docling text, engine does its own chunking + extraction.
**Notes:** User challenged "why not raw PDFs" — clarified graphrag can't parse PDFs; the honest form of that option uses a parser we already measured as inferior, which would *handicap* graphrag. User accepted Docling-constant input as fairer.

## Backend parity

| Option | Description | Selected |
|--------|-------------|----------|
| Same local stack (primus + BGE via Ollama) | Compute parity; isolates graph-structure variable | ✓ |
| graphrag shipped defaults (GPT-4o-class + text-embedding-3) | "True OOTB" but different compute class | |
| Both (parity primary + default upper-bound) | Most informative; ~2x cost | |

**User's choice:** Same local stack.
**Notes:** Small-model risk on extraction quality flagged as a research watch-item.

## Config fidelity

| Option | Description | Selected |
|--------|-------------|----------|
| Pure defaults (models + required workflow + local search) | Honest emergent baseline | ✓ |
| Minimal alignment tuning | Nudge chunk/community toward hybrid granularity | |

**User's choice:** Pure defaults.
**Notes:** User asked what "local search" and "defaults" mean — explained the graphrag pipeline (emergent entity extraction, community detection, local vs global search) before deciding.

## Comparison scope & deliverable

| Option | Description | Selected |
|--------|-------------|----------|
| All 18 cases, deep-dive B01/B03/B04, report artifact | Full picture; decide by composite + per-group + hallucination | ✓ |
| Only B01/B03/B04 cases | Faster; loses cross-benchmark signal | |

**User's choice:** All 18, deep-dive the three, comparison report vs canonical hybrid baseline.

## Engine/framework reframe (the pivotal decision)

| Option | Description | Selected |
|--------|-------------|----------|
| Neo4j GraphRAG both phases (emergent P9, ontology P10) | Cleanest additive ablation; one engine | ✓ |
| Neo4j + keep Microsoft graphrag as optional secondary | Retain published-method citation | |
| Keep Microsoft graphrag for Phase 9 | Original plan; decide P10 engine later | |

**User's choice:** Neo4j GraphRAG for both phases; drop Microsoft `graphrag` as primary.
**Notes:** User drove this by asking (a) "why not Neo4j?", (b) for a full Microsoft-graphrag-vs-Neo4j comparison and Neo4j's advantages, then (c) proposed "make Phase 9 GraphRAG, not Microsoft GraphRAG." Comparison surfaced Neo4j's advantages: schema-guided extraction (native fit for Phase-10 ontology), one-`MERGE` clause seeding, Cypher/Text2Cypher retrieval, browsable KG for dissertation, n10s SHACL. Reframe judged the stronger research design because it isolates the ontology-grounding contribution on an identical engine (no engine-swap confound). Tradeoff accepted: forgoes the "Microsoft GraphRAG named baseline" citation.

## Storage (Neo4j vs Microsoft graphrag native)

| Option | Description | Selected |
|--------|-------------|----------|
| Neo4j (local Docker) | Queryable/visualizable; alongside Qdrant; local-first | ✓ |
| Microsoft graphrag parquet + LanceDB | File-based, no server, but not queryable; ties to Microsoft package | |
| Neo4j via bolt-on to Microsoft graphrag | Extra infra Phase 9 would never query | |

**User's choice:** Neo4j (implied by the engine reframe).
**Notes:** Clarified SHACL is RDF-native; Neo4j supports it via n10s (`n10s.validation.shacl`) or an rdflib/pyshacl export — both viable for Phase 10. No Neo4j needed *only* for SHACL, but Neo4j chosen as the shared graph engine for both phases.

## Roadmap update

**User's choice:** Update ROADMAP Phase 9/10 titles + goals + Phase 9 dependency to match the Neo4j reframe (done before writing CONTEXT).

---

## Claude's Discretion
- Concrete `neo4j-graphrag` pipeline/retriever classes, Neo4j Docker version, vector index config, repo layout for graph artifacts.
- Exact BGE embedding model served via Ollama (research to resolve).

## Deferred Ideas
- Ontology-grounded KG + schema-constrained extraction + clause seeding + SHACL → Phase 10.
- Global/corpus-wide sensemaking retrieval → only if a global-search comparison is later wanted.
- Optional Microsoft `graphrag` reference run → possible secondary baseline for the published-method citation.
