"""Pack persisted OMD-GraphRAG candidates into generation documents."""
from typing import List

from langchain_core.documents import Document

from rag.retrieval.state.graph_state import GraphState

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


def cap_primary_candidates(candidates: List[dict], top_k: int) -> List[dict]:
    """Preserve ranking order; retain all definition candidates plus at most top_k primary clauses."""
    selected = []
    primary_count = 0
    for candidate in candidates:
        if candidate.get("kind") == "definition":
            selected.append(candidate)
        elif primary_count < top_k:
            selected.append(candidate)
            primary_count += 1
    return selected


def omd_pack(state: GraphState) -> GraphState:
    """Transform the persisted retrieval trace into primus context documents."""
    trace = state.get("retrieval_trace", {})
    candidates = trace.get("candidates", [])
    definitions = trace.get("definitions", [])
    docs: List[Document] = []

    def _def_doc(cid, term, definition, score):
        doc_name, _, ref = (cid or "").partition("::")
        return _doc(f"{doc_name} {ref} — Definition of '{term}': {definition}", cid,
                    f"Definition ({doc_name})", score)

    seen_defs = set()
    # Definitions bypass ranking and lead the context for citation grounding.
    for d in definitions:
        docs.append(_def_doc(d.get("citation_id", ""), d.get("term", ""),
                             d["definition"], 1.0))
        seen_defs.add((d.get("citation_id"), d.get("term")))

    # Ranked clauses and retrieved definitions follow, with definition deduplication.
    for r in candidates:
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

    state["filtered_documents"] = docs
    state["documents"] = docs
    state["is_rag_augmented"] = True
    state["retrieval_succeeded"] = bool(docs)
    return state


__all__ = ["cap_primary_candidates", "omd_pack"]
