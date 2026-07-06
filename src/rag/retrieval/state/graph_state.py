"""
LangGraph State Schema

Defines the TypedDict state schema for RAG graph.
State persists across all graph nodes and edges.
"""

from typing import Dict, List, TypedDict

from langchain_core.documents import Document


class GraphState(TypedDict):
    """
    State schema for LangGraph RAG graph.

    Fields are updated by graph nodes as the query flows through
    the retrieval pipeline.
    """

    # Pipeline mode: "hybrid" (default), "llm-only", "rag-only"
    mode: str

    # Query fields
    query: str
    rewritten_query: str
    needs_retrieval: bool

    # Retrieval fields
    documents: List[Document]
    filtered_documents: List[Document]
    grading_scores: List[float]
    retrieval_succeeded: bool
    retrieval_attempts: int

    # Reranker fields (Phase 1.3)
    reranker_scores: List[float]  # Cross-encoder scores for all retrieved docs (before top-N selection)

    # Ontology-grounded retrieval (Phase 10, D-12): inferred function-type tag
    # used to boost retrieval scoring in the ontology-grounded graph provider.
    # Populated by function-type classification landing in plan 10-09; this
    # plan (10-02) only reserves the field on the state contract.
    function_type: str

    # Lab Exp #41 production-promoted fields:
    hyde_query: str  # gpt-4o-mini-generated hypothetical clause (used for retrieval embedding)
    dense_ranks: List[int]  # Original dense-retrieval rank for each retrieved doc
    rrf_scores: List[float]  # Reciprocal Rank Fusion combined score
    merged_groups: List[Dict]  # Parent-child merged sibling groups, if any

    # Generation fields
    generation: str          # post-processor output (citation block parsed, References footer appended if applicable)
    raw_generation: str      # pre-processor model output (still contains the literal <Sources> block, no formatter changes)
    is_rag_augmented: bool
    citations: List[dict]
    llm_context: str

    # I/O capture fields (Phase 3.1 — traceability)
    system_prompt: str
    user_prompt: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    retrieved_contexts_detailed: List[Dict]  # One entry per filtered doc with full metadata

    # Context Graph (Phase 11, D-10): per-query ER/SAO triples extracted from
    # the scenario. Each entry: {subject, subject_type, predicate, object,
    # object_type} where *_type in {actor, data, system, other}. Populated by
    # `extract_context_graph` (plan 11-06 Task 1); consumed by anchor
    # derivation (`map_anchors_to_hypernyms`, plan 11-06 Task 3).
    context_graph_triples: List[Dict]

    # Context Graph (Phase 11, D-10): actor/data/system anchors derived from
    # `context_graph_triples`. Each entry: {label, type}. Populated by
    # `map_anchors_to_hypernyms` (plan 11-06 Task 3); consumed by anchor->CU
    # retrieval (D-11, a future plan).
    anchors: List[Dict]

    # Context Graph (Phase 11, D-09/D-10): hypernym mappings normalizing each
    # anchor to policy vocabulary. Each entry: {anchor, label, strong_weak,
    # supporting_premise, score} — the D-17.2 verbose-io trace payload.
    # Populated by `map_anchors_to_hypernyms` (plan 11-06 Task 3).
    hypernym_mappings: List[Dict]

    # Compliance Gate (Phase 11, D-11): the CU Plan — matched CUs by type
    # (premise / meta-CU / actor-CU) with retrieval scores. Reserved here;
    # populated by a future plan's anchor->CU retrieval node.
    cu_plan: List[Dict]

    # Compliance Gate (Phase 11, D-13/D-17.4): verbatim clause texts actually
    # embedded in the judgment prompt (the citation payload), namespaced by
    # clause id. Reserved here; populated by a future plan's structured
    # judgment prompt-assembly node.
    verbatim_clause_texts: List[Dict]

    # Error handling
    error: str
