# Neo4j exact vector-search / determinism spike (2026-07-02)

**Plan:** 10-01, Task 2 — resolves RESEARCH Open Question 1 / Pitfall 2 (Phase 10
`10-RESEARCH.md`). Gates the D-15 clause-hit@3 harness design (plans 10-09/10-10).

**Stack under test:** `neo4j-graphrag-python` 1.18.0, `neo4j` Python driver 6.2.0,
`neo4j:5.26-community` (Docker, local, `neo4j-local` container). Vector index
`ccop_chunk_embeddings` over `Chunk.embedding` (1024-dim, `bge-large-en-v1.5`,
cosine similarity, created with library defaults — no explicit `vector.hnsw.m` /
`vector.hnsw.ef_construction` / quantization overrides in
`src/rag/graph/build/kg_builder.py::_ensure_vector_index`). Fulltext index
`ccop_chunk_fulltext` (Lucene) over `Chunk.text`. Both indexes queried via
`neo4j_graphrag.retrievers.HybridCypherRetriever` — the exact retriever class
`src/rag/graph/retrieval/neo4j_graph_retrieval_adapter.py` uses.

## (a) Does an exact / brute-force (non-ANN) search mode exist?

**No exact mode is exposed at the retriever layer.** Confirmed via the official
`neo4j-graphrag-python` docs (fetched with `ctx7 docs /neo4j/neo4j-graphrag-python`):

> "When performing a similarity search on a Neo4j vector index, approximate
> nearest neighbor search is used, which may not always yield exact results."
> — README, "Performing a Similarity Search"

> "The query over the vector index is an approximate nearest neighbor search
> and may not give exact results." — `docs/source/index.rst`, Limitations

> "Vector indexes use an approximate nearest neighbor algorithm, which has
> limitations detailed in the Neo4j Documentation." — `user_guide_rag.rst`,
> Vector Retriever

Every retriever in the package (`VectorRetriever`, `VectorCypherRetriever`,
`HybridRetriever`, `HybridCypherRetriever` — the one Phase 9/10 use) routes
through the underlying Neo4j **vector index**, which is HNSW-based ANN. There is
no `exact=True` flag, no brute-force retriever class, and no documented escape
hatch in the retriever API.

**A genuine exact-search path DOES exist, but one level down, in raw Cypher —
not through the retriever.** Neo4j 5.x/2026.x ship a scalar function
`vector.similarity.cosine(a, b)` (confirmed via `ctx7 docs
/websites/neo4j_cypher-manual_current`, "Calculate cosine similarity between two
vectors") that computes exact cosine similarity between two vectors using
`float32` arithmetic, no index involved. This can be used for a genuine
brute-force scan:

```cypher
MATCH (c:Chunk)
WHERE c.embedding IS NOT NULL
RETURN elementId(c) AS citation_id,
       vector.similarity.cosine(c.embedding, $qvec) AS score
ORDER BY score DESC, citation_id ASC
LIMIT $k
```

This is viable at the current graph scale (684 nodes / ~250 `Chunk` nodes) but
**changes retrieval semantics**: it scores the dense leg only, whereas
`HybridCypherRetriever` fuses dense (vector index) + sparse (Lucene fulltext)
signals. Swapping production `graphrag` / `graphrag-ontology` retrieval to
brute-force cosine would silently drop the sparse/hybrid signal — not a like-for-
like substitution, and out of scope for this plan (D-16: "Do NOT change
generator, embedder, or retrieval config").

## (b) Observed run-to-run stability of the ANN path

Empirical probe: same query text/vector against the live, static (no concurrent
writes) Phase 9 index, `top_k=5`, N=5 repeats via `HybridCypherRetriever`, plus
N=3 repeats of the exact brute-force Cypher above for comparison. Script:
scratch probe using the adapter's own settings (`graph_vector_index_name`,
`graph_fulltext_index_name`, `graph_embedding_model`).

**Result: bit-stable.** All 5 `HybridCypherRetriever` runs returned the
identical top-5 `(citation_id, score)` sequence, in the identical order. All 3
exact brute-force runs likewise returned an identical top-5 sequence. Sample
(query: *"What are the access control requirements for critical information
infrastructure?"*):

```
ANN  (HybridCypherRetriever, x5 identical):
  (...236, 1.0), (...452, 1.0), (...322, 0.9979), (...2, 0.9967), (...225, 0.9963)
EXACT (vector.similarity.cosine, x3 identical):
  (...236, 0.8488), (...225, 0.8466), (...322, 0.8463), (...2, 0.8405), (...583, 0.8334)
```

Overlap between ANN top-5 and EXACT top-5: 4/5 (expected — ANN score is the
dense+sparse hybrid-fused score, EXACT is dense-only cosine; different signal,
not a bug).

**Caveat — a latent non-determinism risk was found in the ANN result, not yet
manifested but real:** the top-2 ANN scores tied exactly at `1.0` (two distinct
chunks, `...236` and `...452`). The adapter's current `RETRIEVAL_QUERY`
(`neo4j_graph_retrieval_adapter.py`) does `ORDER BY score DESC` **with no
secondary sort key**. Cypher does not guarantee a stable sort for tied primary
keys — under a tie, ordering is an artifact of internal traversal/heap order,
which is not documented as stable across Neo4j versions, query replans, or
even repeated executions in principle (this run happened to be stable because
the index was frozen and the driver/server were unchanged between calls — that
is necessary but not sufficient for a determinism *guarantee*). At this
corpus scale exact 1.0 ties surfaced organically on the very first probe query,
so this is not a rare edge case for the 691-clause-node scale of Phase 10.

## (c) LOCKED determinism strategy for the D-15 harness

**Decision: ANN + deterministic secondary Cypher tie-break + frozen index.**
No exact-search API exists in the retriever layer that preserves the
production hybrid (dense+sparse) retrieval semantics; a true brute-force exact
alternative exists only via `vector.similarity.cosine()` in raw Cypher and
would require abandoning the sparse leg, which is out of scope (D-16
additivity: Phase 10 must not silently change what "graphrag" retrieval means
relative to Phase 9). The empirical probe confirms ANN is stable run-to-run
*when the index is frozen and there are no true ties* — but ties were observed
on the very first test query, so the missing secondary sort key is a live risk,
not a theoretical one.

**Concrete requirements for plans 10-09 (adapter tie-break) and 10-10
(harness):**

1. **Secondary sort key on every retrieval Cypher query used by the eval
   harness:** `ORDER BY score DESC, citation_id ASC` (or the ontology-graph
   equivalent stable identifier — e.g. the seeded clause node's deterministic
   `clause_id`, which is a stronger, human-meaningful tie-break than
   `elementId()` once Phase 10's clause backbone (D-10) lands). This is a
   required change to `RETRIEVAL_QUERY` wherever score-ordered results feed
   the deterministic clause-hit@3 gate.
2. **Frozen index during eval runs:** no concurrent `graph build`/ingestion
   writes while the D-15 harness runs. Not currently enforced by tooling —
   plans 10-09/10-10 should document this as an operational precondition (e.g.
   a pre-flight check or a documented run-order constraint), not assume it is
   self-evident.
3. **Do not rely on ANN score equality as a proxy for "same chunk" across
   repeated runs** — the observed 1.0/1.0 tie between two *different* chunks
   shows scores alone are an insufficient sort key even before considering
   cross-run stability.

This resolves RESEARCH Open Question 1 / Pitfall 2 as **Option B** from the
plan's action spec ("ANN + deterministic secondary Cypher tie-break + frozen
index"), not Option A ("exact-search API") — no such API exists at the
retriever layer without discarding the hybrid dense+sparse signal.

## Appendix: probe methodology

- Query embedded once via `SentenceTransformerEmbeddings(model=settings.graph_embedding_model)`
  (`BAAI/bge-large-en-v1.5`), reused as the fixed `query_vector` for the exact
  leg; `HybridCypherRetriever.search(query_text=...)` re-embeds internally per
  call (by design — it is not given a raw vector), so the ANN repeats also
  exercise embedding-call determinism, not just index-query determinism. No
  drift was observed there either.
- `top_k=5`, single representative query (`"What are the access control
  requirements for critical information infrastructure?"`), 5 ANN runs / 3
  exact runs, no writes to the graph between runs (index frozen for the
  duration of the probe).
- Environment: `neo4j-graphrag` 1.18.0, `neo4j` driver 6.2.0, `neo4j:5.26-community`,
  vector index created with library defaults (no explicit HNSW
  `ef_construction`/`m`/quantization tuning).
