# 09-04 SUMMARY — Graph retrieval provider + `--mode graphrag` wiring

**Plan:** 09-04 · **Wave:** 4 · **Status:** complete
**Decisions:** D-06, D-09, D-11

> Execution note: two spawned executors stalled on the slow `make verify` pre-commit
> hook (600s stream-watchdog), after committing the port (`76091a5`) + RED adapter
> tests (`1af5d02`). The coordinator finished the plan inline.

## What was built
- **`src/rag/graph/ports/i_graph_retrieval_provider.py`** — `IGraphRetrievalProvider` port; `retrieve(query, top_k) -> list[Document]` returning contexts (not an answer, D-06). Phase-10 registers a 2nd provider against this (D-11).
- **`src/rag/graph/retrieval/neo4j_graph_retrieval_adapter.py`** — `Neo4jGraphRetrievalAdapter` (entity-anchored/"local" retrieval, D-09) via neo4j-graphrag `VectorCypherRetriever`: bge-large-en-v1.5 query embedding → vector-match `Chunk` → static one-hop `FROM_CHUNK` expansion. STATIC parameterized Cypher (T-09-12: query never string-formatted in). Returns hybrid-shaped Documents (D-11).
- **`src/rag/graph/retrieval/graph_retrieval_node.py`** — `graph_retrieve_documents(state)` LangGraph node: pulls the provider from DI, populates `documents` + `filtered_documents` (bypasses reranking → attaches `dense_rank`/`similarity_score` for parity), sets `retrieval_succeeded`; degrades cleanly when no provider / on exceptions.
- **`src/rag/retrieval/edges/routing.py`** — `route_by_mode` returns `graph_retrieval` for `mode=="graphrag"`; hybrid/llm-only/rag-only unchanged.
- **`src/rag/retrieval/graph.py`** — added `graph_retrieval` node + edge-map entry; `graph_retrieval → grade_documents → generate`. The primus `generate` node is **untouched** (D-06).
- **`src/infrastructure/config/container.py`** — `_create_graph_retrieval_provider` + `graph_retrieval_provider` Singleton (selects Neo4j adapter iff `neo4j_uri` set), mirroring the Qdrant/Databricks pattern (D-11 seam).

## Honesty note (emergent baseline, D-08/D-19)
The un-governed KG has no clause-level metadata on `Chunk` nodes, so the adapter sets `citation_id` = chunk `elementId` and `section` = None. Reported, not patched — clause grounding is Phase 10.

## Verification
- `poetry run pytest ../tests/rag/graph/retrieval/{test_graph_retrieval_adapter,test_graph_retrieval_node,test_graphrag_routing}.py -m "not integration"` → **15 passed (4.23s)**.
- Topology test confirms the compiled graph has `graph_retrieval` and the unchanged `generate` node.
- `generate.py` NOT in files_modified (D-06 asserted).
- Live 625-node graph preserved (retrieval is read-only).
- 9 pre-existing `test_llm_judge_service.py` failures remain (unrelated, documented in 09-01/02 summaries) — no new regressions.

## Model roles held
extraction = gpt-4o-mini (build only) · embeddings = bge-large-en-v1.5 · **graph = retriever only** · generation = primus (unchanged). No ontology/SHACL/seeding (Phase 10).
