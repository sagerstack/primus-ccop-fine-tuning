"""OMD-GraphRAG context assembly for primus (--mode graphont).

The `graphont` analog of compliance_context_assembly (graphcpl option (a)): calls the OMD-GraphRAG
tri-channel retriever (rag.graph.ontology_v2.omd_retrieval) and packs its output into
`state["filtered_documents"]` — the format the `generate` node feeds primus — so graphont measures
**primus + OMD-GraphRAG retrieval**, comparable to hybrid/graphcpl.

Retriever = IDF-weighted graph Channel-I ⊕ BM25 ⊕ bge dense, weighted-RRF fused, then a
cross-encoder reranked with confidence-adaptive CE⊕RRF (rag/graph/ontology_v2/omd_retrieval.py).
It reranks internally, so this branch routes straight to `generate` (bypasses the shared reranking
node), mirroring graphcpl. Two document kinds are assembled:
  1. RETRIEVED CLAUSES — top-K reranked clauses (verbatim text, citation_id)
  2. DEFINITIONS — glossary definitions of the query concepts (injected grounding, bypass ranking)

Mode-gated on `graphont`; degrade-safe (empty context on failure). Downstream `generate` reasons/cites.
"""
import logging
from typing import List

from langchain_core.documents import Document

from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

_MODE = "graphont"
_TOP_K = 8  # paper §retrieval top-k = 8


def _doc(text: str, citation_id: str, section: str, score: float) -> Document:
    return Document(
        page_content=text,
        metadata={
            "citation_id": citation_id,
            "document_source": "OMD-GraphRAG",
            "section": section,
            "similarity_score": score,
        },
    )


def omd_context_assembly(state: GraphState) -> GraphState:
    """Retrieve via OMD-GraphRAG and pack reranked clauses + injected definitions into
    filtered_documents for primus."""
    if state.get("mode") != _MODE:
        return state

    question = state.get("query", "") or ""
    docs: List[Document] = []
    try:
        from rag.graph.ontology_v2 import omd_retrieval

        out = omd_retrieval.retrieve(question, k=_TOP_K)

        # Definitions (injected + retrieved) lead the text with a clean "<doc> <ref>" so primus cites
        # correctly — the model builds its Sources footer from the section (doc name) + leading text (ref).
        def _def_doc(cid, term, definition, score):
            doc_name, _, ref = (cid or "").partition("::")
            return _doc(f"{doc_name} {ref} — Definition of '{term}': {definition}", cid,
                        f"Definition ({doc_name})", score)

        seen_defs = set()
        # 1. Injected definitions (concept-anchored grounding, bypass ranking)
        for d in out.get("definitions", []):
            docs.append(_def_doc(d.get("citation_id", ""), d.get("term", ""), d["definition"], 1.0))
            seen_defs.add((d.get("citation_id"), d.get("term")))

        # 2. Ranked results — clauses AND retrieved definitions (dedup retrieved defs vs injected)
        for r in out.get("results", []):
            if r.get("kind") == "definition":
                key = (r.get("citation_id"), r.get("term"))
                if key in seen_defs:
                    continue
                seen_defs.add(key)
                docs.append(_def_doc(r.get("citation_id", ""), r.get("term", ""),
                                     r.get("definition", ""), float(r.get("score", 0.0))))
            else:
                docs.append(_doc(r.get("text", ""), r.get("citation_id", ""),
                                 f"Clause ({r.get('doc', '')})", float(r.get("score", 0.0))))

        logger.info(
            "OMD-GraphRAG context assembled for primus: %d document(s) "
            "(%d clauses + %d definitions, ranked_by=%s, D_cand=%d)",
            len(docs), len(out.get("results", [])), len(out.get("definitions", [])),
            out.get("ranked_by"), out.get("d_cand", 0))
    except Exception as e:  # degrade-safe: empty context, primus answers without grounding
        logger.warning("OMD-GraphRAG retrieval failed (%s) — empty graphont context", e)

    state["filtered_documents"] = docs
    state["documents"] = docs
    state["is_rag_augmented"] = True
    state["retrieval_succeeded"] = bool(docs)
    return state


__all__ = ["omd_context_assembly"]
