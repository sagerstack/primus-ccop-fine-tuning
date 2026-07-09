---
phase: 11-align-graphrag-to-graphcompliance-architecture-scenario-anch
plan: 06b
type: execute
wave: 5
depends_on: ["11-06"]
addendum_to: "11-06"
files_modified:
  - src/rag/retrieval/nodes/anchor_hypernym_mapping.py
  - tests/rag/retrieval/nodes/test_anchor_hypernym_mapping.py
autonomous: false
requirements: [R11-5, R11-4]
must_haves:
  truths:
    - "GraphCompliance §3.2 hypernym mapping is THREE steps: (1) retrieve top-M policy fragments (dense, grounding only), (2) LLM ELICITATION `ctx.hypernym` proposing NORMALIZED policy-vocabulary hypernym labels + confidence s(r) in [0,1] + supporting frag_id, (3) aggregate via eqs. 1-2 (Alg. 2 line 3)"
    - "The 11-06 Task 3 implementation SKIPPED step 2 -- it used the raw retrieved fragment AS the hypernym label and cosine similarity AS s(r). This addendum adds the missing LLM elicitation so hypernyms are normalized terms (e.g. 'critical information infrastructure') not raw enumeration fragments ('(a) Operating systems;')"
    - "STRONG iff the proposal's supporting fragment is a Premise (D-09, beta=0.3); the paper's s(r) is LLM-generated confidence, NOT cosine"
    - "HypernymScoringService (11-06 Task 2, eqs. 1-2) is CORRECT and MUST NOT be modified -- it only needs correct inputs (LLM confidence as score, is_premise from the supporting fragment)"
    - "Retrieval (step 1) is grounding, not the answer -- enrich the query with the entity's triple context (predicate + object) so the right definitions land in the LLM window; the CII-definition premise for a 'designated as CII' system must be retrievable"
    - "New behavior is no-op unless mode == graph-compliance; the node NEVER raises (degrade-to-empty on any LLM/retrieval failure, mirroring context_graph_extraction.py)"
  artifacts:
    - path: "src/rag/retrieval/nodes/anchor_hypernym_mapping.py"
      provides: "ctx.hypernym LLM elicitation step + triple-context-enriched retrieval query"
      contains: "elicit_hypernyms"
  key_links:
    - from: "src/rag/retrieval/nodes/anchor_hypernym_mapping.py"
      to: "src/domain/services/hypernym_scoring_service.py"
      via: "feed LLM-proposed (label, confidence, is_premise) proposals -- NOT raw fragments -- into score_candidates"
      pattern: "HypernymScoringService"
---

<objective>
Close the §3.2 fidelity gap the D-26 checkpoint surfaced: 11-06 Task 3 built hypernym
mapping as 2 steps (retrieve -> aggregate), collapsing the paper's middle step -- the
`ctx.hypernym` LLM elicitation that turns a scenario entity + retrieved policy fragments
into NORMALIZED policy-vocabulary hypernym labels with LLM confidence s(r) and premise
support (GraphCompliance Alg. 2 line 3; §3.2 eqs. 1-2). Without it, hypernyms come out as
raw enumeration fragments and s(r) is cosine, not confidence -- violating the "normalizes
entities" must-have and making retrieval fragile.

This addendum adds step 2 and enriches step 1's query. Step 3 (HypernymScoringService)
is correct and untouched.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/11-align-graphrag-to-graphcompliance-architecture-scenario-anch/11-06-PLAN.md
@research/graphcompliance/2510.26309v1.pdf
@src/rag/retrieval/nodes/anchor_hypernym_mapping.py
@src/rag/retrieval/nodes/context_graph_extraction.py
@src/domain/services/hypernym_scoring_service.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add ctx.hypernym LLM elicitation + triple-context-enriched retrieval</name>
  <read_first>
    - src/rag/retrieval/nodes/context_graph_extraction.py — MIRROR its LLM-call shape EXACTLY: `openai` client with api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url, model=settings.ontology_discovery_model, client.chat.completions.create(...); parse via neo4j_graphrag `fix_invalid_json`; degrade-to-empty when api key unset or on any exception; per-query cache with a threading.Lock. REUSE these, do not invent a new gateway or settings key.
    - src/rag/retrieval/nodes/anchor_hypernym_mapping.py — the current node: `_derive_anchors` (returns {label,type}), `_default_fragment_retriever`, and the `map_anchors_to_hypernyms` body that builds `candidates: Dict[label, List[ScoredFragment]]` and calls `scorer.score_candidates`.
    - src/domain/services/hypernym_scoring_service.py — `ScoredFragment` fields (text, score, is_premise, source_id) and `score_candidates(Dict[label, List[ScoredFragment]])`. DO NOT MODIFY this file.
    - research/graphcompliance/2510.26309v1.pdf §3.2 (steps: retrieve top-M -> elicit proposals r=(e,h(r),frag_id,src) with LLM confidence s(r), STRONG iff supporting fragment is a Premise -> eqs. 1-2) and Appendix C.2 Algorithm 2 line 3 `H <- LLM.Call("ctx.hypernym", ER.entity, G_P.premise)` + Listing 2 (hypernym is a clean policy term: "IT operations manager"->"controller").
  </read_first>
  <action>
    Modify `anchor_hypernym_mapping.py`:

    1. **Enrich anchors with triple context (step 1 fix).** Change `_derive_anchors` (or add a companion) so each anchor carries its relations from the triples that mention it — e.g. `{"label","type","context": [(predicate,object), ...]}`. Build the retrieval query from label + rendered triple context (e.g. `"patient monitoring systems | designated as CII"`) instead of the bare label, so `_default_fragment_retriever` surfaces the definitional premise for a "designated as CII" system. Keep the retriever's dense mechanism; only the query text changes.

    2. **Add the ctx.hypernym elicitation step (step 2 — the core addition).** New `elicit_hypernyms(entity, entity_context, fragments, settings) -> List[proposal]` mirroring `context_graph_extraction.py`'s LLM-call+parse+degrade shape. Prompt: given the entity (+ its triple context) and the top-M retrieved policy fragments (each with its citation_id, cu_type, and text), propose up to a few NORMALIZED policy-vocabulary hypernym labels, each as `{"hypernym": <normalized term>, "confidence": <0..1>, "supporting_frag_id": <citation_id of the fragment that justifies it>}`. Resolve `supporting_frag_id` back to the retrieved fragment to set `is_premise = (that fragment.cu_type == "premise")` and `source_id`. Degrade-safe: no api key or any exception -> that entity yields `[]`. Cache per (query-id, entity-label) with a lock (Claude's discretion, mirror the Task-1 cache).

    3. **Rewire the scorer feed (step 3 inputs — no scorer change).** Replace the current "raw-fragment-as-label / cosine-as-score" candidate construction with proposals from `elicit_hypernyms`: build `candidates` keyed by the NORMALIZED `hypernym` label, each a `ScoredFragment(text=hypernym, score=confidence, is_premise=<from supporting frag>, source_id=<citation_id>)`. Then call the UNMODIFIED `scorer.score_candidates`. The retriever still runs first (grounding for the LLM); the scorer still applies eqs. 1-2 (max-pool + beta=0.3 + top-N=5).

    Keep the whole node mode-gated (`mode == "graph-compliance"`, else no-op) and degrade-safe (never raises). Do NOT add settings.py keys. Do NOT modify hypernym_scoring_service.py or context_graph_extraction.py.
  </action>
  <acceptance_criteria>
    - `grep -n "elicit_hypernyms" src/rag/retrieval/nodes/anchor_hypernym_mapping.py` present; the node feeds LLM proposals (normalized label + confidence + is_premise) into `score_candidates`, NOT raw fragments/cosine.
    - `git diff --name-only` shows NO change to `src/domain/services/hypernym_scoring_service.py`.
    - Unit tests (mocked LLM, no live infra) assert: (a) mode != graph-compliance is a no-op; (b) a proposal whose supporting fragment is a premise is STRONG with the beta bonus, a non-premise proposal is WEAK; (c) LLM confidence (not cosine) is the score fed to the scorer; (d) hypernym labels are the normalized LLM terms, not raw fragment text; (e) LLM failure / unset api key degrades that entity to no mappings and never raises; (f) top-N=5 still enforced by the scorer.
    - All existing 11-06 unit tests still pass (37 pre-existing + new).
  </acceptance_criteria>
  <verify>
    <automated>cd src && poetry run pytest ../tests/rag/retrieval/nodes/test_anchor_hypernym_mapping.py ../tests/domain/services/test_hypernym_scoring_service.py ../tests/rag/retrieval/nodes/test_context_graph_extraction.py -x</automated>
  </verify>
  <done>ctx.hypernym elicitation added; retrieval query enriched with triple context; scorer fed correct inputs; scorer untouched; all tests green.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>The §3.2-faithful 3-step hypernym mapping: triple-context-enriched retrieval (grounding) -> ctx.hypernym LLM elicitation (normalized labels + confidence + premise support) -> unchanged eqs. 1-2 scorer.</what-built>
  <how-to-verify>
    Run the REAL live E2E slice on B01-001 (live OpenRouter + live Neo4j graph, NOT mocks; e2e-testing rule). Report, as checkpoint evidence:
    1. The hypernym mappings for EACH anchor — especially `patient monitoring systems` and `MRI machines` (the "designated as CII" systems): do they map to a NORMALIZED CII label (e.g. "critical information infrastructure") marked STRONG, supported by the CII-definition premise CCoP-1.2.1?
    2. The `hospital administration system` anchor: it should NOT be STRONG-mapped to CII (B01-001 ground truth = not-applicable; it is not itself CII). Report what it maps to.
    3. Confirm hypernym LABELS are normalized policy terms, not raw enumeration fragments.
    Note: the 11-06 Task 3 acceptance criterion tied the STRONG CII mapping to the hospital-admin anchor; per the B01-001 ground truth that is the wrong anchor — the STRONG CII mapping belongs on the patient-monitoring/MRI anchors. Flag this correction, do not force the admin system to map STRONG to CII.
  </how-to-verify>
  <resume-signal>Type "approved" to advance to Wave 6 (11-07), or list what needs rework.</resume-signal>
</task>
</tasks>

<verification>
- 3-step §3.2 hypernym mapping faithful; scorer unmodified; normalized hypernyms; live B01-001 shows CII-systems -> CII STRONG via CCoP-1.2.1, admin system not STRONG-CII.
</verification>

<success_criteria>
- D-10/D-09 satisfied faithfully: hypernym mapping normalizes entities to policy vocabulary via LLM elicitation, premise-supported proposals STRONG with beta bonus, eqs. 1-2 aggregation intact.
</success_criteria>

<output>
Append to / create `.planning/phases/11-align-graphrag-to-graphcompliance-architecture-scenario-anch/11-06-SUMMARY.md` (note the addendum) when done.
</output>
