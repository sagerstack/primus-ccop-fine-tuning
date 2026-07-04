# Phase 11: Align GraphRAG to GraphCompliance (scenario-anchored, reasoning-first) - Context

**Gathered:** 2026-07-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Re-architect the ontology graph-RAG retrieval+reasoning to match the **GraphCompliance**
reference (arXiv 2510.26309, WWW'26). Phase-10 triage proved `--mode graphrag-ontology` does
no real graph reasoning — it is hybrid chunk retrieval + a decorative clause label (Finding 0),
the exact "retrieval-only-graph" config GraphCompliance's ablations show adds nothing over
vanilla RAG. This phase builds the two-graph, reasoning-first architecture:

1. **Policy Graph** (offline, from the corpus) — the regulation formalized into **Compliance
   Units (CUs)**, with `premise` / `meta-CU` / `actor-CU` typing and `REFERS_TO` edges.
2. **Context Graph** (per-query, from the scenario) — the question's scenario extracted to
   entity anchors, hypernym-mapped to policy vocabulary.
3. **Compliance Gate** — anchor→CU retrieval → meta-CU applicability gating → structured LLM
   judgment over a CU Plan + verbatim clause text → `REFERS_TO` exception closure → aggregation.

**Success:** a new eval mode that actually reasons over the ontology and beats the hybrid
baseline on **clause-hit@3 + citation grounding** on the 18-case fixed GT (`bdc4927d`), with a
verbatim-text-in-prompt guarantee that is *measured*, not assumed.

**In scope:** Policy Graph construction (premise/CU classification → 4-tuple extraction →
`REFERS_TO` linking); step-0 clause-text alignment (fixes Finding 1); Context Graph + anchor +
hypernym-mapping pipeline; anchor→CU retrieval (CU Plan) with two-channel recall + fallback;
meta-CU gating; structured judgment prompt (CU 4-tuple + verbatim clause text); reference-closure
exception handling; new `--mode graph-compliance`; the `--verbose-io` reasoning trace; F8 fan-out
elimination (native to atomic CUs); F4/F5 eval-ruler reliability (temp 0, RAGAs demotion).

**Out of scope:** re-chunking the corpus to clause units for *extraction* (violates P9 D-05 —
extraction stays coarse, retrieval/citation is clause-grained); fine-tuning; changing the
generator (primus held constant, P9 D-06); the Microsoft `graphrag` package (P9 D-01); the full
435-case run (this phase validates on 18; see D-14 for the 435 constraint that shapes the design).
</domain>

<decisions>
## Implementation Decisions

### Reframing (supersedes the Phase-10 "ontology-guided graph retrieval" framing)
- **D-01:** GraphCompliance is **NOT graph-RAG** in the retrieval sense — it is ontology-schema-
  structured compliance **reasoning**. The graph earns its keep in reasoning (anchor alignment,
  meta-CU gating, `REFERS_TO` closure done *outside* the LLM), NOT as a retrieval index; retrieval
  is plain embedding over CU subjects. Phase 11 stops trying to "make retrieval traverse the
  ontology" (the config the paper shows adds nothing) and instead **structures obligations as CUs
  + does deterministic reasoning over them**. (Paper §2.1/§3; their GraphRAG baseline underperformed
  vanilla RAG 47.5 vs 49.5 micro-F1.)

### Two-graph architecture (follow the paper step by step)
- **D-02:** Build **two graphs**: a **Policy Graph** (offline, reused across all cases = the rules)
  and a **Context Graph** (per-query = the facts of the scenario). The Compliance Gate aligns
  Context→Policy. The Context Graph is GraphCompliance's biggest lever (their S2 ablation, removing
  it = −10.2pp) — it is exactly the scenario anchoring our current system throws away (Finding 0,
  query embedded as a bare string).

### Policy Graph construction — 3 stages (paper §3.1)
- **D-03:** **Stage 1 = text classification** (the first build step): segment the corpus into
  semantic units (clauses) and classify each **three ways** — `premise` (non-deontic definitional/
  interpretive; never judged), `meta-CU` (applicability/scope gate; evaluated first, never a
  standalone violation), `actor-CU` (obligation on a role-bearing actor; the unit actually judged).
  Run once, offline, by an LLM. **Warm-start from Phase-10 function-type tags:** `DefinitionClause
  → premise`, `ScopeClause → meta-CU`, `ControlClause → actor-CU`.
- **D-04:** **Stage 2 = rule formalization**: formalize each CU into the 4-tuple
  **⟨subject, constraint, context, conditions⟩** via schema-constrained LLM extraction (same
  discipline as P10, target = the obligation tuple, not loose entities).
- **D-05:** **Stage 3 = relational linking**: create `REFERS_TO` edges via regex (explicit refs,
  e.g. "Clause 5.7.2") + a small LLM (implicit/relative refs). These are traversed at query time
  for exception closure.

### Corpus scope + clause-count reconciliation
- **D-06:** The clause inventory (`clause_inventory.json`) has **883 entries across 7 docs**, NOT
  the "691" stated in P10 CONTEXT D-10 (stale — correct it). CCoP 2.0 alone = **415 entries** =
  11 chapter headers + 51 section headers + 353 leaves (175 of which are lettered sub-items
  `(a)(b)(c)`). The user's "~220 clauses" ≈ the operative leaves once structural headers are
  stripped. Verify what `clause_seeder.py` actually MERGEs during planning.
- **D-07:** **CU candidates = operative provisions only.** The 62 chapter/section headers (`1`,
  `5.7`) are NOT CUs — they are the `CONTAIN` hierarchy skeleton (they are also the Finding-3
  "content-empty chapter anchors" that flooded linking). Lettered sub-items `(a)(b)(c)` become
  their own CUs where they carry a distinct obligation.
- **D-08:** **Corpus-scope split (proposed, confirm at plan):** CCoP 2.0 + Cybersecurity Act =
  binding → yield judged `actor-CU`/`meta-CU`s; the 4 guides + Response-to-Feedback =
  `premise`/guidance (context, not judged). Namespace citation ids by source doc
  (`CCoP-5.7.2(b)` vs `Act-7`) → fixes Finding 2 (clause_id collides across all 6 docs).

### Premises — build artifact, consumed at query time
- **D-09:** Premises are **classified offline** but **used at query time in hypernym mapping**
  (§3.2), NOT in CU retrieval and NOT judged. A hypernym proposal is marked **STRONG** iff its
  supporting fragment is a `premise` (else WEAK), earning a β=0.3 confidence bonus (eq. 1). So the
  premise/CU classification is not just a filter — the label is a **runtime confidence signal**, so
  premise **text must be attached + embedded/retrievable**, and the classification must be correct.
  (Note: STRONG comes from the *definitional* premise, e.g. "CII means…", NOT from the Act §7
  *designation* rule which is a meta-CU.)

### Query-time pipeline (Compliance Gate, §3.3)
- **D-10:** **Context Graph** = LLM extracts ER/SAO triples from the scenario → **anchors**
  (actor/data/system) → **hypernym mapping** normalizes anchors to policy vocabulary (top-M
  fragment retrieval, STRONG/WEAK, max-pool + top-N=5 per entity, eqs. 1–2). Hypernym mapping
  normalizes *entities*, not relations (correction to the B01-001 draft).
- **D-11:** **CU retrieval → CU Plan:** per anchor, bi-encoder scores anchor vs each CU's
  **`subject`** (+ hypernym overlap bonus, eq. 3) → top-K1; cross-encoder reranks
  `q(a)=[predicate; actor_type; object_type]` vs `d(c)=[subject; constraint; condition]` (eq. 4)
  → the CU Plan. Retrieval unit = the **atomic CU**, never a chunk.
- **D-12:** **Structured judgment prompt** = evidence window (scenario subgraph around the anchor)
  + the CU Plan as **structured 4-tuples PLUS the verbatim clause text** (see D-16). Listwise judge
  (eq. 5): per-CU `{label, confidence, rationale, evidence}`; "forbid inference from silence"
  (ambiguous/out-of-scope → INSUFFICIENT/NOT_APPLICABLE) — this is also the fix for Finding 6
  (hedge-instead-of-decide). meta-CUs gate applicability first. Then **reference-closure exception
  handling**: for NON_COMPLIANT CUs traverse `REFERS_TO`, a 2nd LLM call checks for a valid
  overriding exception (eq. 6). Finally **violation-first aggregation**.

### Retrieval recall guarantee (the "is the relevant text in the prompt?" risk)
- **D-13:** Two independent failure modes must both be defeated: **(A) recall** (is the gold
  clause's CU in the CU Plan?) and **(B) payload** (does the prompt carry the *verbatim* text?).
  Mechanisms:
  - **Payload:** every CU node hard-links to its source clause id + verbatim provision text
    (deterministic, from step-0 alignment); the prompt **always** carries the verbatim text
    alongside the 4-tuple (tuple = reasoning representation, text = citation payload) — extraction
    loss can't remove the real text.
  - **Recall (deliberate divergence from pure GraphCompliance):** retrieve over **two channels** —
    (i) the paper's anchor→CU-`subject` match, PLUS (ii) hybrid dense+BM25 over the **verbatim
    clause text** — so a clause surfaces by its actual wording even if its extracted `subject` is
    weak. Plus deterministic pulls (meta-CU scope gating, `REFERS_TO` closure) and a **fallback
    floor**: if CU-path recall lags, fall back to existing hybrid text retrieval → never worse than
    today's hybrid.
  - **This is NOT confidence-by-design — it is confidence-by-measurement.** Gates in D-15.

### Eval scope + ruler reliability
- **D-14:** **Eval target = all 435 cases eventually; 18-case `bdc4927d` is the validation
  fixture.** This constraint shapes the design: (a) the F8 fan-out fix is **mandatory** (~20 min/
  case × 435 ≈ 6 days is untenable) — and is **native** to atomic-CU retrieval (no chunk×clause
  cross-product); (b) **temp 0** over multi-seed for score stability (F5) — multi-seed × 435 too
  costly; (c) cache per-query extractions/anchors; (d) the anchor set + CU model must generalize
  across all 18 benchmark *families*, not just scope questions → benchmark-family coverage check
  (like P10 D-14/D-17).
- **D-15:** **Acceptance gates (measured, before any A/B is reported):**
  1. **Verbatim-text-in-prompt assertion** (deterministic substring check, per case): the gold
     clause text is literally present in the prompt sent to the LLM.
  2. **clause-hit@3 / recall@pool** on the 18-case gold (reuse P10 D-15 harness): CU Plan contains
     the gold clause SET.
  3. **B01-001 E2E slice FIRST** (e2e-testing rule): run the real pipeline on one case, dump the
     actual prompt, confirm §1.2.1/§1.4.1 text present — before scaling to 18/435.
  - **RAGAs demoted to secondary** (F4 rate-limit corruption); primary ruler = clause-hit@3 +
    citation grounding. Add backoff but don't gate on RAGAs.
  - **D-16 dependency (P10):** the 3-way A/B (graph-compliance vs graphrag-ontology vs hybrid) is
    only *fair* once the deferred Phase-9 18-case basic-graphrag baseline exists — flag before
    reporting conclusions.

### New mode + verbose-io trace (user-requested)
- **D-16:** **New `--mode graph-compliance`** (additive — preserves `graphrag-ontology` for the
  ablation; do NOT re-architect in place). Wire into ALL allowlists (the multi-allowlist lesson):
  `evaluate_model._RETRIEVAL_EVAL_MODES`, `run_id._VALID_MODES`, `VALID_EVAL_MODES`, and `query
  ask`. Name is adjustable at plan time but must NOT be `graphrag-*` (perpetuates the graph-RAG
  mislabel per D-01). Prove wiring with the E2E slice (D-15.3).
- **D-17:** **Under `--verbose-io`, emit a per-case reasoning trace** mirroring the B01-001
  walkthrough, in this order:
  1. **Context Graph** — the ER/SAO triples extracted from the query.
  2. **Anchors** — actor/data/system, each with its hypernym mapping (label + STRONG/WEAK +
     supporting premise + score).
  3. **Matched CUs by type** — `premise` (STRONG bridges) / `meta-CU` (applicability gates) /
     `actor-CU` (judged), i.e. the CU Plan with retrieval scores.
  4. **The embedded/retrieved clauses** — the verbatim clause text actually sent to the LLM
     (the citation payload), with namespaced clause ids.
  This trace IS the human-facing proof of D-13 (relevant text in prompt) and the debugging surface
  for recall failures.

### Gating design fork (RESOLVED by user)
- **D-18:** Follow **pure GraphCompliance**, not a hybrid that also keeps the Phase-10 24-type
  entity ontology in the retrieval/reasoning loop. Consequence (accepted): the 24-type / 48-relation
  ontology largely **steps out of the loop** — at most a vocabulary source for CU `subject`/`context`
  — since the paper's ablations show entity-ontology-in-retrieval adds nothing. This consciously
  benches part of the Phase-10 ontology investment. (User: "focus on aligning with GraphCompliance,
  not OMAGR.")

### Claude's Discretion
- Exact CU-node schema on Neo4j (new `:ComplianceUnit` layer vs upgrading `:Clause`); leaning new
  additive layer (a clause can spawn multiple CUs) — confirm at plan.
- Embedding/cross-encoder models for anchor→CU retrieval (reuse bge-large + bge-reranker unless a
  reason to change); K1, K, M, N, β values (paper defaults β=0.3, N=5 as starting points).
- Cross-document deference modeling (Code→Act, Code→guide) — `REFERS_TO` vs a distinct
  statutory-hierarchy edge type (research doc flags this as open).
- ER-triple / anchor extraction prompt design and caching strategy.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The reference architecture (READ FIRST — this whole phase implements it)
- `research/graphcompliance/2510.26309v1.pdf` — **GraphCompliance (arXiv 2510.26309, WWW'26).**
  §3.1 Policy Graph construction (premise/CU classification, 4-tuple, REFERS_TO); §3.2 Context
  Graph + hypernym mapping (eqs. 1–2, STRONG/WEAK premise bonus); §3.3 Compliance Gate (eqs. 3–6:
  anchor→CU retrieval, listwise judgment, reference closure, violation-first aggregation);
  Figure 2 = end-to-end pipeline; Table 1 = ablations (S2 −10.2pp, GraphRAG < vanilla RAG).
- `docs/project_notes/research/2026-07-04-ontology-graph-retrieval-design.md` — design study (16
  sources, 22 verified claims); the meta-finding (retrieval-only graph RAG adds nothing; reasoning
  is the win) grounding D-01; the GraphCompliance head-to-head and 4 levers.

### Phase-10 findings this phase fixes (the "why")
- `.planning/phases/10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2-/deferred-items.md`
  — **Findings 0–8** (F0 retrieval never traverses ontology; F1 clause carries no text; F2 clause_id
  collision; F3 short-id over-linking; F4 RAGAs rate-limit corruption; F5 score instability; F6
  hedge-instead-of-decide; F8 1,880-row fan-out) + the GraphCompliance reference-architecture
  comparison section.
- `.planning/phases/10-.../10-CONTEXT.md` — locked ontology (24 types, 48 relations), clause
  backbone (D-10, count stale per our D-06), function-type tags (D-09, warm-start for D-03),
  clause-hit@3 harness (D-15), A/B scope (D-16), gold-relation coverage check (D-17/D-18).

### Data / fixtures
- `src/rag/ingestion/fixtures/clause_inventory.json` — **883 entries / 7 source docs** (415 CCoP);
  the CU-candidate source (D-06/D-07). IDs + source_doc only, no titles/text (Finding 1).
- `ground-truth/test-suite/b01_ccop_applicability_scope.jsonl` — B01-001 (the worked example /
  first E2E slice, D-15.3): scope question, GT `not-applicable`, cites §1.2.1/§1.4.1/Act §7/RtF
  Q2.2–2.3; §5.6 is the distractor.
- `ground-truth/test-suite/*.jsonl` — the 18 benchmarks (validation fixture `bdc4927d`) and the
  eventual 435-case target (D-14).
- Canonical hybrid baseline: `src/results/evaluations/2026-04/eval-run-hybrid-tests-18-bdc4927d-20260430-0232`
  (rubric judge — the parity comparison leg).
- `src/results/evaluations/eval-report-hybrid-suite-20260630-0907.xlsx`, sheet `eval-18`, col 22
  `graph_relation` — hand-authored gold relationship triples per case (P10 D-17); use for the
  benchmark-family coverage check (D-14).

### CCoP source documents (for CU extraction + clause text)
- `ccop-official/CCoP---Second-Edition_Revision-One.pdf` — main Code (CU source).
- `ccop-official/RESPONSE-TO-FEEDBACK.pdf`, `ccop-official/references/Ensign*.pdf`,
  `ccop-official/supplementary/` — Act + guides (premises/context per D-08).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/rag/graph/ontology/clause_seeder.py`, `clause_linker.py` — the clause backbone + linking;
  D-06/D-07 need the seeder to skip structural headers as CUs and namespace ids (F2/F3 fixes).
- `src/rag/graph/retrieval/neo4j_ontology_graph_retrieval_adapter.py` — P10 adapter; a NEW provider
  is registered for `graph-compliance` behind the pluggable seam (do NOT touch P9/P10 adapters).
- `src/rag/retrieval/nodes/reranking.py`, `function_type_routing.py`, `query_analysis.py` — reranker
  funnel + routing; anchor→CU retrieval reuses the cross-encoder; F8 dedup becomes moot (atomic CUs).
- `src/application/use_cases/evaluate_model.py` `_RETRIEVAL_EVAL_MODES` + `run_id._VALID_MODES` +
  `VALID_EVAL_MODES` — the three allowlists a new mode must be added to (D-16, multi-allowlist lesson).
- `--verbose-io` capture path (system/user prompts + retrieved contexts per case) — extend for the
  D-17 reasoning trace (Context Graph → anchors → matched CUs → embedded clauses).

### Established Patterns
- Pluggable graph-retrieval provider (DI container `graph_retrieval_provider`) — the additivity seam.
- Deterministic clause-hit@3 harness (exact vector search + stable tie-break) — reuse for D-15.
- Schema-constrained LLM extraction (P10) — reuse discipline for CU 4-tuple extraction (D-04).

### Integration Points
- `--mode graph-compliance` on `evaluate run` + `query ask` (mirror P9/P10 mode wiring).
- Neo4j (same instance) — new `:ComplianceUnit` layer / CU properties + `REFERS_TO` edges.
</code_context>

<specifics>
## Specific Ideas

- **Anchor worked example (B01-001)** drives the whole design and is the first E2E slice: scenario
  → Context Graph (`HospitalAdminSys sharesNetwork EnterpriseNetwork`, CII systems designated) →
  anchor `HospitalAdminSys ⇒ non-designated system` (STRONG via CII-*definition* premise) → scope
  anchor matches meta-CUs §1.2.1/§1.4.1/Act §7 (NOT §5.6, whose subject is a control) → judge 3
  atomic rules → `REFERS_TO` closure surfaces the §1.4.1 dependency caveat → verdict `not-applicable`
  + cites {§1.2.1, §1.4.1, Act §7}. Full trace in `11-DISCUSSION-LOG.md`.
- **The `--verbose-io` trace (D-17) must look like that walkthrough** — the user explicitly wants to
  *see* Context Graph → anchors → matching premises/meta-CUs/actor-CUs → embedded clause text.
- Honesty note carried from discussion: the B01-001 tuples were hand-simulated, not executed; the
  first plan task is to make this real and dump the actual prompt (D-15.3).
</specifics>

<deferred>
## Deferred Ideas

- **Full 435-case A/B run** — this phase validates on the 18-case fixture; the 435-case run and its
  gold clause SETs (clause-hit@3 needs gold for all 435) are a follow-on effort (D-14).
- **Phase-9 basic-graphrag 18-case baseline** — a hard dependency for a *fair* 3-way A/B (P10 D-16);
  deferred by user but must precede reported conclusions.
- **OMAGR multi-anchor decomposition** (legal-dimension routing) — the alternative anchoring
  mechanism; explicitly NOT chosen (user chose GraphCompliance). Revisit only if scenario-entity
  anchoring under-recalls on non-scope benchmark families.
- **MS GraphRAG global search** (community-summary map-reduce for "across the whole Code"
  aggregation questions) — keep as a possible second retrieval mode; not this phase.
- **Cross-document entity canonicalization** across Code/Act/guides — flagged open (research doc,
  2-1 split); needs validation on the 7-PDF corpus.
- **OWL reasoner / GT over-strictness review** — carried from P10 deferred.

### Reviewed Todos (not folded)
None — no matching todos surfaced for this phase.
</deferred>

---

*Phase: 11-align-graphrag-to-graphcompliance-architecture-scenario-anch*
*Context gathered: 2026-07-04*
