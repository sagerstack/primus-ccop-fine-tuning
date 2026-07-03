"""
Phase 10 ontology-governance package.

Pure parsing/logic modules for CCoP ontology discovery (Method C, Method B),
gold-relation coverage checking (D-17), and the committed ontology draft
artifacts. Import-free of Neo4j/network clients — mirrors the RAG-slice
Clean Architecture layering (this package sits alongside `rag/graph/build/`
and `rag/graph/retrieval/`, but contains no infrastructure adapters itself).
"""
