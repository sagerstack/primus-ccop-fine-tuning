# Compliance Gate — in-session build plan (resumable)

**Goal:** implement the GraphCompliance Compliance Gate (paper §3.3) end-to-end so
`poetry run ccop-eval evaluate run --mode graphcpl --test-ids B01-001` runs
and produces a scored result. **Paper is the gold standard**; the old 11-07/08/09/10
plans are reference only (pre-patch, may have drifted). No GSD subagents — built in-session.

## Locked decisions (2026-07-06)
- **Retrieval = pure paper** (eq.3 subject-similarity + hypernym bonus → top-K1; eq.4 cross-encoder rerank → CU Plan). NO hybrid-text second channel / fallback floor (that was a plan hedge, not in the paper).
- **Output / grounding (D4b, confirmed):** the mode's core job is to **forward the right graph content as context** for the query's anchors — **relevant premises (definitions/interpretations) + obligations (CU Plan actor/meta-CU) + verbatim clause text** — to the model. Premises come from the 11-06b hypernym STRONG-support (already computed per anchor) + any retrieved for the CUs; obligations from the Gate retrieval (eq.3-4). For B01-001, the paper's verdict+rationale is the answer; generalising to the non-verdict benchmarks (answer-gen over this grounding) is deferred but the context assembly is built for it now.
- **Foundation** = current patched graph (premises are `:Clause:Premise`; obligations are `:ComplianceUnit` actor-CU/meta-CU, 381). Hyperparams = paper defaults (β=0.3, N=5, K1≈20, K≈8) + reuse `bge-large` embedder + `bge-reranker` cross-encoder.
- **Retrieval unit = atomic CU** (actor-CU/meta-CU subjects). Premises are NOT retrieved by the Gate (they're the STRONG-support source in 11-06b hypernym mapping, already done).

## Paper methodology → nodes (§3.3, Alg. 3, eqs. 3-6)
1. Anchors A ← from Context Graph (state["anchors"] + state["hypernym_mappings"]) — DONE (11-06b).
2. Preselect (eq.3): per anchor, score vs each CU `subject` → top-K1.
3. Rerank (eq.4): cross-encoder q(a)=[predicate;actor_type;object_type] vs d(c)=[subject;constraint;condition] → CU Plan {P_i}.
4. meta-CU gating: meta-CUs judged first (applicability); gate whether actor-CUs apply.
5. Judgment (eq.5): listwise LLM over evidence window W(a) + CU Plan → per-CU {label∈{COMPLIANT,NON_COMPLIANT,NOT_APPLICABLE,INSUFFICIENT}, confidence, why, evidence}. Forbid inference from silence.
6. Reference closure + exception (eq.6): for NON_COMPLIANT c, closure over REFERS_TO (+DERIVES=FROM_CLAUSE) → 2nd LLM call → override to COMPLIANT if a valid exception.
7. Aggregate (violation-first): → final verdict + rationale + citations.

## Current-code anchors (from survey)
- Graph build: `rag/retrieval/graph.py::build_rag_graph` (add nodes + route). Pipeline: query_analysis → route_by_mode → … → reranking → grade_documents → decide_after_grading → {generate|fallback|rag_response} → END.
- Routing: `rag/retrieval/edges/routing.py::route_by_mode` + `decide_after_grading`.
- State: `rag/retrieval/state/graph_state.py` (has context_graph_triples/anchors/hypernym_mappings/cu_plan/verbatim_clause_texts reserved).
- Mode allowlists (register graph-compliance in ALL):
  1. `domain/value_objects/run_id.py` `_VALID_MODES`
  2. `application/use_cases/evaluate_model.py` `_RETRIEVAL_EVAL_MODES`
  3. `presentation/cli/commands/evaluate.py` `VALID_EVAL_MODES` + `--mode` help
  4. `rag/retrieval/edges/routing.py` `route_by_mode` (+ decide_after_grading if needed)
  5. `rag/retrieval/graph.py` (nodes + conditional edge target)
  6. DI container `infrastructure/config/container.py` (if a provider singleton is needed)
  7. RagResponse/DTO mapping (`rag/infrastructure/adapters/langgraph_rag_adapter.py`, `application/dtos/evaluation_result_dto.py`) — trace + generation propagate
  8. `rag/application/use_cases/query_compliance.py` docstring/mode plumbing (verify)
- Reuse: embedder `SentenceTransformerEmbeddings(settings.graph_embedding_model)` + cross-encoder from `reranking.py::_get_cross_encoder`; LLM call shape from `context_graph_extraction.py` (OpenRouter, temp 0, fix_invalid_json, degrade-to-empty).
- Neo4j: actor-CU/meta-CU via `(cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)`; REFERS_TO `(:ComplianceUnit)-[:REFERS_TO]->(:ComplianceUnit)`.

## Build steps (implementation order; check off as done)
- [ ] S1. New node `compliance_gate_retrieval` (eqs. 3-4): fetch actor/meta CU pool (subject+4-tuple+verbatim clause text, cache); per anchor eq.3 → top-K1 → cross-encoder rerank → `state["cu_plan"]` (+ `verbatim_clause_texts`). Mode-gated, degrade-safe. Unit test (mock pool).
- [ ] S2. New node `compliance_judgment` (eqs. 5-6 + gating + aggregation): build evidence window; listwise judge LLM call; meta-CU gating; REFERS_TO closure + exception LLM call for NON_COMPLIANT; violation-first aggregate; assemble `state["generation"]` + citations + tokens/latency. Mode-gated, degrade-safe. Unit test (mock LLM).
- [ ] S3. Wire into `graph.py`: add extract_context_graph, map_anchors_to_hypernyms, compliance_gate_retrieval, compliance_judgment nodes; route graphcpl: query_analysis → extract_context_graph → map_anchors_to_hypernyms → compliance_gate_retrieval → compliance_judgment → END.
- [ ] S4. Register `graphcpl` in all mode allowlists (1-8 above).
- [ ] S5. Trace/response propagation: generation + citations + tokens/latency + trace fields flow GraphState → RagResponse → EvaluationResult/CLI.
- [ ] S6. E2E: `poetry run ccop-eval evaluate run --model primus-reasoning --mode graphcpl --test-ids B01-001` runs; inspect verdict + score. Fix wiring issues (multi-allowlist class of bug).

## Acceptance
`evaluate run --mode graphcpl --test-ids B01-001` completes end-to-end, produces a
response with a verdict (expect not-applicable), retrieved CU Plan + verbatim clauses in the
prompt, and a judge score. Then review.
