# Phase 10: Ontology-grounded GraphRAG (Neo4j, governed KG) - Context

**Gathered:** 2026-07-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Layer **ontology governance** onto the Phase 9 Neo4j GraphRAG stack **additively** — construct a
CCoP ontology (entity/relation types), deterministically seed the 691 clause nodes, constrain KG
extraction to the ontology (schema-guided) with entity resolution + gleaning, validate with SHACL,
and expose `--mode graphrag-ontology` behind the same pluggable retrieval provider. A/B on the
18-case fixed GT vs Phase 9 basic (emergent) GraphRAG and the hybrid baseline, isolating the effect
of ontology grounding on the identical engine / input / harness (P9→P10 differs by exactly one
variable: extraction governance).

**In scope:** ontology construction (discover→curate→lock), clause seeding, schema-constrained
extraction, entity resolution, SHACL validation, clause-anchored retrieval + relevance routing,
`--mode graphrag-ontology`, deterministic clause-hit@3 eval harness, A/B report.

**Out of scope:** re-chunking the corpus to clause units (violates P9 D-05); fine-tuning; changing
the generator (primus held constant per P9 D-06); the Microsoft `graphrag` package (P9 D-01).
</domain>

<decisions>
## Implementation Decisions

### Ontology construction method (Method C → curate → Method B)
- **D-01:** Construct the ontology by **discovery, not hand-authoring** — the user oversees /
  verifies / amends but does not author. Sequence: **Method C (grounded synthesis) first → user
  curation gate → Method B (clustering) cross-verify → reconcile → lock.** (Ref: the five-methods
  article — "schema-free discovers → schema-based formalizes.")
- **D-02:** **Do NOT reuse Phase 9's emergent entities/graph** as discovery input (explicit user
  decision). Discovery runs fresh from the corpus + structured taxonomy.
- **D-03:** The roadmap title's "Text Ontology Learning (paper §3.2.2)" is treated as **inspiration,
  not a prescription** — proceed with the C→B approach without the paper. (User confirmed.)
- **D-04:** **Method C mechanism** = grounded synthesis anchored on *structured sources*, NOT open
  per-chunk NER (that was the Phase 9 failure). Sources: CCoP section/clause **headers** (control
  taxonomy — from the Docling corpus / Qdrant `section` fields, since `clause_inventory.json` has
  IDs but no titles), the **18 benchmark definitions** (reasoning/relation concepts), and sampled
  corpus prose (domain entities). Each proposed type carries **provenance** + flagged ambiguities.
- **D-05:** **Method B mechanism** = clustering pipeline (extract corpus terms → embed → cluster →
  LLM-name clusters) as an **independent coverage cross-check** against C. B-only clusters =
  candidate missing types → user decides keep/drop. (Embedding model + clustering algo = planner's
  discretion; article suggests Affinity Propagation.)

### Anti-patterns to avoid (from the Phase 9 emergent-KG audit)
- **D-06:** The Phase 9 emergent NER produced: fragmented duplicate types (CII / CIIAsset /
  CriticalInformationInfrastructure / CIIOrganization), hallucinated junk instances ("N.A.", "A",
  "John Doe"), mis-typing ("Penetration Testing" as System), and — critically — **modelled the
  scenario narrative, not the regulation** (no Clause/Control/Obligation types; no GOVERNS/REQUIRES/
  APPLIES_TO relations). Phase 10 MUST NOT repeat these. Root cause = **unconstrained extraction
  with no schema**.
- **D-07:** Fixes, structurally: **schema-constrained extraction (Method D)** with a **controlled,
  non-overlapping type vocabulary**; **entity resolution / dedup** to canonical nodes; **filter**
  junk (empties, placeholders); **instruct extraction to ignore illustrative/example passages**
  (the "John Doe" source); require a canonical name (SHACL-enforced).

### Ontology content (types + relations)
- **D-08:** The ontology MUST include the **regulatory-structure layer** the emergent graph lacked:
  entity types `Clause`, `Control`, `Obligation`, `Definition`; relation types `GOVERNS`, `REQUIRES`,
  `APPLIES_TO`, `RESPONSIBLE_FOR`, `MITIGATES`. This layer is **hand-added / seeded**, not discovered
  (discovery can only cluster what's in the prose, which is scenario-centric).
- **D-09:** Include **clause-function tags** (`ScopeClause` / `ControlClause` / `DefinitionClause`) —
  required to enable function-type relevance routing (D-12).
- **D-10:** **Clause backbone = deterministic seeding** — MERGE 691 clause nodes from
  `clause_inventory.json` (Title→Chapter→Article→Item, parent-child edges). No LLM → no hallucinated/
  unnamed clauses. Extracted entities LINK to these seeded clause nodes.

### Chunking (extraction unit vs retrieval unit — the decouple)
- **D-11:** Decouple the two units (P9's chunk was double-duty). **Extraction chunk:** move from
  P9's arbitrary 4000-char `FixedSizeSplitter` to **section-aligned** boundaries + **gleaning
  (multi-pass)** — NOT "bigger" (4000-char ≈ 1000 tok is already large; bigger without gleaning
  loses entity recall per the 600-vs-2400 finding). neo4j-graphrag lacks native gleaning → user-added.
  **Retrieval unit:** the **seeded clause node** (fine, real-ID), NOT the coarse extraction chunk.
  (Permitted: P9 D-08 says "all alignment/tuning belongs to Phase 10.") See ADR-007 / research report.

### Retrieval relevance-routing (the citation-retrieval fix)
- **D-12:** **Function-type routing** (CONFIRMED by user) — classify question intent → prefer
  clauses tagged with the matching function-type (D-09). This is the mechanism that makes §1.2.1
  out-rank §5.6 for a scope question. Grounding + clause nodes fix *citation correctness/granularity*;
  routing is the SEPARATE lever that fixes *ranking*. If function-type alone doesn't clear the
  clause-hit@3 gate, escalate to "Both, layered" (function-type + entity-anchored traversal).

### Validation & human gates
- **D-13:** **SHACL validation** (locked, D-16 from P9) — reject non-conforming facts, log
  separately ("validation is the line between toy and production"). **OWL reasoner = stretch goal**
  (logical-consistency check; "SHACL minimum, OWL ideal").
- **D-14:** **Two human curation gates in Wave 1:** (a) after the Method-C draft, (b) after the
  Method-B reconcile. Build does not proceed until the ontology has user approval + passes a
  **benchmark coverage check** (every one of the 18 benchmarks maps to a type).

### Evaluation & A/B scope
- **D-15:** **Acceptance gate = deterministic clause-hit@3 harness** — for each GT case, assert the
  expected clause SET appears in the top-3 that reaches the LLM. Requires: **exact vector search +
  stable tie-break** (P9 retrieval was non-deterministic — top-3 flapped across runs on clustered
  scores), and scoring against a clause **SET** (not a single ID; B01-001 spans §1.2.1 + §1.4.1 +
  Act §7/§11 + RtF Q2.2–2.3). Metrics: clause hit@3 / recall@3 / recall@pool(50).
- **D-16:** **A/B = graphrag-ontology vs basic graphrag vs hybrid** on the 18-case fixed GT
  (`bdc4927d`). ⚠️ **Hard dependency:** the basic-GraphRAG baseline is the **deferred Phase 9
  Wave 6** (only B01-001 run so far, n=1, within-noise). No "ontology improved X" claim is
  trustworthy until that 18-case Phase 9 baseline exists. Deciding signals: clause-hit@3 + LLM-judge
  citation/grounding dims + RAGAs context metrics.

### Ontology coverage validation against gold relations (user-added)
- **D-17:** After ontology construction (C→B→curate, D-01), **cross-check the ontology's entity
  types + relation types against the `graph_relation` column (col 22) of
  `src/results/evaluations/eval-report-hybrid-suite-20260630-0907.xlsx`, sheet `eval-18`** — a
  **hand-authored gold-standard** of the relationship triples each of the 18 cases requires, with
  clause citations. Parse the triples → extract their entity types + relation types → **any type
  present in the gold triples but MISSING from the ontology is a gap → ADD it.** This is a stronger,
  concrete coverage check than the benchmark-name mapping (D-14) — it's per-case gold relations.
- **D-18:** The gold triples reveal relation families the emergent extraction (and the naïve starter
  set) **missed** and that the ontology MUST cover — especially **negation/modal relations** central
  to compliance reasoning: `NOT_DESIGNATED_AS`, `CANNOT_SATISFY`, `DOES_NOT_WAIVE`, `DEFINES_NO`,
  `DOES_NOT_SPECIFY`, `PERMITS…where_necessary`, `TECHNOLOGY_NEUTRAL_ON`, `RECOMMENDS_AGAINST`,
  `DEFERS_TO`, plus `IS_A`/`DEFINED_AS`/`CLASSIFIED_AS`/`DESIGNATES`/`DETERMINED_BY`. Extend the
  starter relation set (D-08) accordingly during curation.

### Claude's Discretion
- Method B embedding model + clustering algorithm (AP suggested), corpus term-extraction strategy.
- Concrete SHACL shape authoring; entity-resolution algorithm (exact-match vs LLM-based).
- Exact `--mode` naming / provider wiring (mirror P9's pluggable seam).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 9 forward-guidance (the additive seam — read first)
- `.planning/phases/09-basic-graphrag-reference-baseline-microsoft-graphrag-package/09-CONTEXT.md` — D-01 (Neo4j both phases; one-variable ablation), D-04/D-05/D-08 (input constant; don't clause-fragment extraction; P9 pure-defaults, tuning belongs to P10), D-06/06a/07 (generator = primus held constant; extraction LLM = gpt-4o-mini; embeddings = bge-large-en-v1.5), **D-16 / D-16a** (Phase-10 ontology + clause seeding + SHACL; three-part chunking decouple).
- `.planning/phases/09-.../deferred-items.md` — chunk-granularity → Phase 10 carry-forward; the P9 18-case deferral.

### Chunking / ontology research
- `docs/project_notes/research/2026-07-02-graphrag-chunking-regulatory.md` — deep-research report (extract-large/retrieve-fine decouple, gleaning, clause-hierarchy backbone; 22/25 claims adversarially verified).
- `docs/project_notes/decisions.md` — **ADR-007** (coarse chunking as intrinsic OOTB limitation; clause granularity is P10's job).
- https://zerofuturetech.substack.com/p/building-ontology-with-llms-five — the five ontology-construction methods (A pipeline, B clustering, C two-phase, D schema-guided, E end-to-end). Basis for D-01/D-04/D-05/D-13.

### Data / fixtures
- `src/rag/ingestion/fixtures/clause_inventory.json` — 691 clause IDs for deterministic seeding (D-10). NOTE: IDs + source_doc only, no titles.
- `ground-truth/test-suite/*.jsonl` — the 18 benchmarks; their definitions seed the reasoning/relation concepts (D-04) and the coverage check (D-14). GT clause references (e.g. B01-001 → §1.2.1/§1.4.1) feed the clause-hit@3 gate (D-15).
- Canonical hybrid baseline: `src/results/evaluations/2026-04/eval-run-hybrid-tests-18-bdc4927d-20260430-0232` (rubric judge — the parity mode; NOT universal).
- **`src/results/evaluations/eval-report-hybrid-suite-20260630-0907.xlsx`, sheet `eval-18`, col 22 `graph_relation`** — hand-authored GOLD-STANDARD relationship triples per case (with clause citations). The ontology coverage check (D-17) validates against this; D-18 relation families come from it. MUST read during ontology curation.

### Bugs / lessons carried in
- `docs/project_notes/bugs.md` — 2026-07-02 provenance-collapse bug (all docs → "document.txt"); P9 NER emergent-entity audit (the D-06 anti-patterns).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/rag/graph/build/kg_builder.py` (`EmergentKGBuilder`, `SimpleKGPipeline`) — Phase 10 provides the `schema`/entities/relations kwargs P9 deliberately left empty (D-03/D-08). Provenance fix + fulltext index already landed.
- `src/rag/graph/retrieval/neo4j_graph_retrieval_adapter.py` — `HybridCypherRetriever` (dense+sparse) + shared reranker funnel; Phase 10 registers a *second* provider (`graphrag-ontology`) behind the same pluggable seam (P9 D-11) without touching P9's.
- `src/rag/retrieval/nodes/reranking.py` — shared cross-encoder + RRF funnel the graph path already routes through (Wave-6 parity fix).
- `src/application/use_cases/evaluate_model.py` — `_RETRIEVAL_EVAL_MODES` (P3 fix); add `graphrag-ontology` here AND `run_id._VALID_MODES` AND `VALID_EVAL_MODES` (the multi-allowlist lesson).

### Established Patterns
- Pluggable graph-retrieval provider (DI container `graph_retrieval_provider`) — the additivity seam.
- Deterministic eval harness needed: exact vector search + stable tie-break for reproducible clause-hit@3 (D-15).

### Integration Points
- `--mode graphrag-ontology` on `evaluate run` + `query ask` (mirror P9 D-10 mode wiring).
- Neo4j (same instance), n10s for SHACL (or rdflib/pyshacl export).

</code_context>

<specifics>
## Specific Ideas

- Concrete worked example that anchors the whole phase: **B01-001** (healthcare admin system on shared CII network). Correct answer grounds on **CCoP §1.2.1 + §1.4.1** (+ Act §7/§11, RtF Q2.2–2.3); §5.6 (Network Security) is a *distractor* the P9/hybrid ranking wrongly favours. Phase 10 success = clause-anchored retrieval + function-type routing surfaces §1.2.1/§1.4.1 in top-3.
- The user's role is **oversight/curation** (verify, amend, advise) — not authoring. Present the draft ontology as a markup table (type | definition | example terms | provenance | flagged ambiguities) + a benchmark coverage check.

</specifics>

<deferred>
## Deferred Ideas

- **Phase 9 Wave 6** (18-case graphrag-vs-hybrid comparison + report + B01/B03/B04 deep-dive) — deferred by user, but is a HARD dependency for Phase 10's A/B (D-16). Must run before Phase 10 conclusions are trusted.
- **"Both, layered" routing** (function-type + entity-anchored traversal) — richer than D-12; revisit if function-type routing alone doesn't clear the clause-hit@3 gate.
- **OWL reasoner** — stretch beyond SHACL (D-13).
- **GT over-strictness** — some GT cases cite a single clause for multi-clause reasoning questions; the clause-hit@3 gate accepts a clause SET, but the GT itself may warrant a review pass (own effort, not Phase 10).
- **ADR-006 not implemented** — judge still reads `forbidden_claims`; unrelated to Phase 10 but tracked.

</deferred>

---

*Phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2*
*Context gathered: 2026-07-02*
