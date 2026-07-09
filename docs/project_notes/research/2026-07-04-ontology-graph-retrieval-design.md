# Ontology-Grounded Graph Retrieval — Design Research (2026-07-04)

Deep-research synthesis (16 sources, 22 adversarially-verified claims) on how
ontology/KG-RAG retrieval *should* work for a multi-document regulatory corpus,
commissioned after Phase-10 triage found the `graphrag-ontology` leg does no real
graph traversal (see `deferred-items.md` Findings 0–8). Grounded in the CCoP 2.0
stack (Neo4j + `neo4j-graphrag`, hybrid vector+BM25, bge-reranker, clause-hit@3).

## The one meta-finding that reframes everything

**Retrieval-only graph RAG gives no meaningful uplift over plain RAG.** In the
GraphCompliance study (arXiv 2510.26309, GDPR), GraphRAG-style graph-flavoured
*retrieval* did not beat vanilla RAG; the gains (+up to 12.8 pp macro-F1, +19.6 pp
F2) came from **typed-graph REASONING** — deterministic traversal of typed edges
(cross-references, actor/scope checks) done *outside* the LLM, with the LLM
reserved for final judgment over pre-structured evidence.

Implication for us: **fixing retrieval to "use the graph" is necessary but not
sufficient to beat our hybrid baseline.** Our Finding 0 (retrieval = hybrid +
decorative clause label) means the ontology leg is essentially retrieval-only
graph — exactly the configuration shown to add nothing. The win requires using
the graph for *structural reasoning*, not just graph-shaped retrieval.

## (a) Retrieval unit + chunking

1. **Retrieval/citation unit = the leaf clause/provision as a text-carrying
   node** with a stable id and typed edges (parent-child hierarchy, cross-refs,
   ontology-dimension). Flat section chunks are "blind to the hierarchical and
   cross-referential structure of law." [OMAGR 2606.11910; SAT-Graph RAG
   2505.00039 — the latter peer-reviewed, on legal norms] → fixes our F1.
2. **Coarse text is for EXTRACTION only, not the retrieval unit.** Build an
   entity/clause's relationship network by aggregating ALL text segments where it
   appears (multi-context), then retrieve/cite at leaf grain. [RAKG 2504.09823;
   MS GraphRAG entity-description aggregation] → resolves the coarse-vs-fine
   tension and our F3 over-linking (extraction aggregates; citation is the leaf).
3. **Chunking granularity is document-type-dependent, not uniform.** Fine
   chunking helps narrative text but *fragments* structured/hierarchical legal
   text. Minimise chunking for the structured Code/Act; chunk the 4 narrative
   guides. [Barron et al. 2502.20364, ICAIL-linked]

## (b) Ontology-graph retrieval pipeline (the core)

Standard shape the sources converge on:

1. **Two parallel channels** — the query is BOTH embedded for semantic retrieval
   AND used to traverse the graph. Not vector search with a decorative label.
   [Barron et al.] → fixes F0.
2. **Decompose the query into ontology-aligned anchors — one per legal
   dimension** (scope, applicability-condition, responsible-party,
   control-requirement, evidence-expectation, cross-reference). Each anchor
   anchors to graph nodes and **issues its own typed Cypher traversal** for that
   dimension, so a scope question routes to `APPLIES_TO`/`IN_SCOPE_ONLY_IF` and the
   dominant semantic signal can't crowd out other legally-relevant dimensions.
   Planner-guided with explicit policies, not similarity-only; structure-aware
   filtering restricts vector search to a pre-filtered relevant subgraph.
   [OMAGR; SAT-Graph]
3. **Two-hop cross-reference expansion** from the top anchors to recover
   co-applicable provisions unreachable via the primary ontology edge.
4. **Fuse + rerank + dedup:** Reciprocal Rank Fusion (k=60, uniform weights),
   cross-encoder rerank to top-k, MMR (λ≈0.7) to drop near-duplicates. [OMAGR]
   (MMR directly addresses our F8 duplicate top-3.)
5. **Citation-grounded generation:** constrain every answer claim to a verbatim
   source in the retrieved set R; prohibit citing any provision outside R.
   [OMAGR]
6. **Split structural lookups from LLM judgment:** deterministic graph traversal
   for cross-refs / actor / scope / responsibility checks; LLM only for final
   semantic judgment over the pre-analyzed structured input. [GraphCompliance]

**Local vs global:** anchored/local traversal answers specific clause-hit
questions; **Microsoft GraphRAG global search** (map-reduce over LLM-generated
community-report summaries) answers "across the whole Code" aggregation
questions. Keep both. [MS GraphRAG docs]

## (c) Multi-document handling

- **Canonicalise shared concepts** across Code / guides / Act (RAKG "pre-entity"
  intermediate representations reduce cross-doc disambiguation; **split 2-1 vote
  — treat as open**).
- **Namespace citations by source document** (`CCoP-5.7.2(b)` vs `Act-7`) → fixes
  our F2 collision.
- **Model inter-document deference** (Code → Act, Code → guide) as **explicit
  typed cross-reference / statutory-hierarchy edges** resolved at ingestion, then
  traversed. [OMAGR statutory-hierarchy edge type]

## (d) Evaluation

- Measure **structural-logic + citation grounding**, not just RAGAs. Tie every
  answer claim to a verbatim source in R and check the SPECIFIC gold leaf clause
  was retrieved+cited (not a topically-adjacent chapter anchor). [OMAGR;
  GraphCompliance] — validates our clause-hit@3 direction; RAGAs alone is
  insufficient (and, per our triage, was rate-limit-corrupted anyway).

## What `neo4j-graphrag` gives vs what we must build

- **Provides the retrieve-then-traverse primitive:** `VectorCypherRetriever` /
  `HybridCypherRetriever` find seed nodes via vector/full-text then run a
  user-supplied `retrieval_query` that MATCHes typed edges; `Text2CypherRetriever`
  uses an LLM to generate Cypher for exact lookups (no embedder). [Neo4j docs +
  eng blog] — this is the seam to actually traverse `GOVERNS`/`REQUIRES`/
  `APPLIES_TO` instead of only chunk→clause.
- **Does NOT provide** (build on top or borrow from MS GraphRAG): the
  query-planner / multi-anchor decomposition, per-dimension Cypher templates,
  community-report generation (global search), and the RRF/rerank/MMR fusion
  layer.

## Caveats (source honesty)

- OMAGR (2606.11910, Chinese traffic law) and GraphCompliance (2510.26309, GDPR)
  are **recent non-peer-reviewed preprints in adjacent domains**; the pipeline
  *patterns* transfer but the specific numbers (12.8 pp, RRF k=60, top-8) are
  single-study, domain-specific, and GraphCompliance's GraphRAG baseline is
  author-implemented.
- SAT-Graph RAG (2505.00039) is peer-reviewed and on-domain, but its
  Work/Expression *versioning* payoff is only partly relevant to a static CCoP
  corpus.
- **Refuted claims (do not over-index):** "reference-edge traversal is the single
  most important component (9.6 pp)" — refuted 0-3; "hierarchical NMFk retrieval
  beats flat across all doc types" — refuted 1-2; "KG-RAG must be bidirectional
  (text+graph always)" — refuted 1-2.
- Cross-document entity canonicalisation is an **open design area needing
  validation** on the 7-PDF corpus.

## Open questions to resolve before building

1. Leaf-clause node schema on Neo4j: each clause carries its own text + a stable
   namespaced citation id AND typed edges; replace the loose substring
   chunk→clause links (avg 46, max 217) with precise clause↔text alignment at
   ingestion.
2. The concrete CCoP anchor set (scope / applicability / responsible-party /
   control / evidence / cross-ref) and the typed-Cypher template per anchor — the
   per-domain planner `neo4j-graphrag` doesn't provide.
3. How to model + traverse cross-document deference (Code→Act, Code→guide) and
   validate cross-doc entity canonicalisation.
4. The labeled gold set + metric protocol for clause-hit@3 / citation-grounding,
   and how to avoid LLM-judge pitfalls (scoring the specific gold leaf clause, not
   a topically-adjacent anchor).

## Primary sources

- OMAGR — Ontology-Multi-Anchor Graph Retrieval (arXiv 2606.11910)
- SAT-Graph RAG — Ontology-Driven Graph RAG for Legal Norms (arXiv 2505.00039, peer-reviewed)
- GraphCompliance (arXiv 2510.26309)
- RAKG — retrospective-retrieval KG construction (arXiv 2504.09823)
- Barron et al. — legal-RAG chunking + dual vector/graph channel (arXiv 2502.20364)
- Microsoft GraphRAG global search docs (microsoft.github.io/graphrag)
- neo4j-graphrag user guide + hybrid-retrieval blog (neo4j.com/docs)
