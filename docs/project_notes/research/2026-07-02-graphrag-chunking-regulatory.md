# Research: Best chunking strategy for GraphRAG over clause-heavy regulatory text

**Date:** 2026-07-02
**Trigger:** Phase 9 Wave-6 confound — `--mode graphrag` scored judge 0.06 vs hybrid 0.44 on
B01-001. Root cause hypothesized as retrieval-primitive asymmetry (untuned graph retrieval vs
tuned hybrid), one axis of which is chunk granularity (neo4j-graphrag default 4000-char coarse
chunks vs hybrid's clause-level Docling chunks). Question: is coarse chunking a fixable confound
or an intrinsic characteristic to report?
**Method:** deep-research harness — 6 search angles, 24 sources fetched, 99 claims extracted, top
25 verified with 3-vote adversarial verification (need 2/3 refutes to kill). 22 confirmed, 3
refuted.
**Decisions informed:** D-20 (Phase 9 reports coarse chunking as intrinsic OOTB limitation),
D-16a (Phase 10 chunking/retrieval architecture).

## Bottom line

For a clause-heavy compliance/regulatory corpus, the evidence-backed strategy is to **decouple
the extraction unit from the retrieval unit** and make the graph backbone the document's own
**clause hierarchy** rather than co-occurrence-extracted entities:

- **Extract on larger section-level chunks** (+ overlap, ideally + gleaning/multi-pass) so
  relationships have co-occurrence context and entity recall is preserved.
- **Seed the graph with explicit clause-hierarchy nodes** (Title→Chapter→Article→Item).
- **Retrieve at fine clause granularity** via clause/entity-anchored retrieval — clause precision
  without re-splitting the extraction chunks.

## Verified findings (confidence + adversarial vote)

1. **Chunk double-duty is real and is the root tension.** In GraphRAG the same TextUnit is both
   the LLM extraction unit and a retrieval unit. HIGH, 3-0.
   — Microsoft GraphRAG docs (index/default_dataflow, config/yaml).

2. **Smaller extraction chunks ≈ 2× entity recall.** GPT-4 extracted almost twice as many entity
   references at 600 vs 2400 tokens; longer chunks trade recall (esp. early-in-chunk info) for
   fewer/cheaper LLM calls. HIGH, 3-0. — Microsoft GraphRAG paper, arXiv 2404.16130v2 App. A.2
   (direct ablation; primary experiments used 600-token chunks / 100 overlap).

3. **Relationship extraction is chunk-local → small chunks starve it.** Relations whose evidence
   spans passages are "systematically absent" because both endpoints must co-occur in one chunk;
   naive stitching is "fragile for long texts." HIGH, 3-0. — arXiv 2605.28004 (Beyond Chunk-Local
   Extraction). **This validates Phase 9's D-05, but scoped to *relationships*, not entities.**

4. **Gleaning is the field's reconciliation, not "just go bigger."** Microsoft defaults to 1200
   tokens + `max_gleanings` (repeated extraction passes) to recover entities missed in larger
   chunks. HIGH, 3-0. — GraphRAG config/yaml + default_dataflow + paper.

5. **neo4j-graphrag has neither gleaning nor structure-aware splitting.** Default
   `FixedSizeSplitter(chunk_size=4000, chunk_overlap=200)`, character-based, single-pass
   (one `llm.ainvoke` per chunk; only post-hoc EntityResolver merging). Multi-pass "like the
   GraphRAG authors do" must be user-added. HIGH, 3-0. — Neo4j KG-builder docs.
   **So the project's 4000-char graph chunking is a generic library default, not a quality-tuned
   choice.**

6. **Structure-aware/section-based chunking wins on structured legal text.** Section-based
   significantly improves retrieval + end-to-end QA vs naive line chunking (NitiBench, Thai
   statutes — a real ablation); small fixed chunks cause "concept fragmentation" degrading
   structured-text performance; statutes should be split into sections/clauses with chapter/
   section metadata. HIGH, 3-0. — arXiv 2502.10868, 2502.20364, 2503.04338.

7. **Make the graph backbone the clause hierarchy, not NER co-occurrence.** Titles/Chapters/
   Articles/Items as nodes with parent-child edges; entity-centric GraphRAG is "structurally
   blind" to hierarchy — a critical failure for legal text where position defines scope. HIGH,
   3-0. — SAT-Graph, arXiv 2505.00039v5 (corroborated by BifrostRAG 2507.13625, GraphCompliance
   2510.26309). **Independent validation of Phase 10's clause-node seeding (D-16).**

8. **Decouple structural nodes from retrievable text.** Text chunks link only to the most-specific
   text-version node (fine retrieval unit), not the timeless structural node. HIGH, 3-0. —
   SAT-Graph arXiv 2505.00039v5.

9. **Retrieval side favors minimal precise clause snippets.** Large imprecise chunks raise cost,
   latency, and hallucination risk; precise snippets enable citation + human verification. HIGH,
   3-0. — LegalBench-RAG, arXiv 2408.10343.

10. **Clause-relationship graph beats chunk-based RAG on ISO 27000 (best 90.54% MCQ).** MEDIUM,
    2-1 — single corpus, MCQ-only, one config, no chunk-size ablation, and LightRAG still chunks
    (~1200 tokens) upstream so it does not isolate chunk size. — MDPI Information 17(4):389 (2026).

## Refuted (did NOT survive verification — do not cite as support)

- "Conventional fixed-size RAG is *empirically inadequate* on ISO 27000, motivating graph over
  chunk retrieval" — 1-2 (overreach; the corpus result doesn't establish inadequacy of chunk RAG
  in general). — MDPI 17(4):389.
- "Hierarchical NMFk indexing + chunking beats flat chunking across all legal doc types" — 0-3. —
  arXiv 2502.20364.
- "Expert/semantic-annotator chunks beat token chunks on clause-heavy corpora" — 0-3 (evidence
  came from general-knowledge QA sets, not clause corpora). — arXiv 2503.04338.
  **Takeaway: treat "structure-aware always wins on retrieval" with caution.**

## Caveats / open questions

- The 600-vs-2400 entity-recall figure is a single ablation on one dataset used to motivate
  gleaning; the relationship-recall side is argued structurally, not quantified with a matching
  ablation.
- SAT-Graph / ontology-driven "structure-aware wins" are mostly method-design preprints, not
  head-to-head ablations. The genuine regulatory-clause ablations are NitiBench (2502.10868) and
  2502.20364.
- **No source ran the exact extract-large / retrieve-fine DECOUPLE ablation on a cybersecurity
  code-of-practice corpus.** The recommendation is a synthesis → Phase 10 should *measure* it
  (RAGAs context_precision/recall/faithfulness + downstream answer quality), not assume it.
- Framework defaults change — re-verify Microsoft (1200 tok + gleaning) and neo4j-graphrag
  (4000 char / 200, single-pass) against live docs before implementing.

## Key sources

- Microsoft GraphRAG paper — arXiv 2404.16130v2 (chunk-size vs entity-recall ablation, gleaning)
- Beyond Chunk-Local Extraction — arXiv 2605.28004 (cross-chunk relation loss)
- SAT-Graph / ontology-driven legal RAG — arXiv 2505.00039v5 (clause-hierarchy backbone)
- NitiBench — arXiv 2502.10868 (section vs line chunking ablation, Thai statutes)
- arXiv 2502.20364 (concept fragmentation on structured text)
- LegalBench-RAG — arXiv 2408.10343 (minimal precise clause retrieval)
- MDPI Information 17(4):389 (LightRAG on ISO 27000; medium confidence)
- Microsoft GraphRAG docs — microsoft.github.io/graphrag (config/yaml, index/default_dataflow)
- neo4j-graphrag-python KG-builder docs — neo4j.com/docs/neo4j-graphrag-python/current
