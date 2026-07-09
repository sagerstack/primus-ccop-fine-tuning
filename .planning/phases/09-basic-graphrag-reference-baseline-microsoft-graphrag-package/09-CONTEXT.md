# Phase 9: Basic GraphRAG baseline (Neo4j, emergent KG) - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning

> **Note on naming:** the phase directory slug still reads
> `...microsoft-graphrag-package` for legacy reasons. During discussion the phase
> was **reframed** away from the Microsoft `graphrag` package to a **Neo4j-based
> GraphRAG** stack (see D-01). The ROADMAP Phase 9/10 titles + goals were updated
> to match; the directory slug was left as-is (GSD tracks by phase number).

<domain>
## Phase Boundary

Stand up a **basic, emergent-KG GraphRAG baseline on Neo4j** over the CCoP corpus and
evaluate it against the current hybrid baseline on the 18-case fixed ground truth.

"Basic / emergent" means: the knowledge graph is built by **LLM free-extraction with
NO ontology/schema constraint** — whatever entities and relationships the LLM discovers.
This is deliberately the *un-governed* reference point. Ontology grounding
(schema-constrained extraction, deterministic clause seeding, SHACL validation) is
**Phase 10** and is explicitly OUT of scope here.

**In scope:**
- Neo4j GraphRAG stack (KG construction from Docling-parsed CCoP text; graph retrieval feeding primus)
- **KG quality inspection + visualization** capability so the graph can be iterated/improved before
  and alongside eval (Neo4j Browser/Bloom + a `ccop-eval graph` CLI) — see D-17/18/19
- Correct model roles (D-06/06a/07): extraction = `gpt-4o-mini` (OpenRouter); embeddings =
  `bge-large-en-v1.5` (in-process); answer generation = `primus-reasoning` (local, graph-as-retriever)
- `--mode graphrag` toggle behind a **pluggable graph-retrieval provider**
- Evaluation on all 18 fixed-GT cases through the existing judge + RAGAs harness
- graphrag-vs-hybrid comparison report, deep-diving B01/B03/B04

**Out of scope (→ Phase 10):** CCoP ontology, schema-constrained extraction, clause
seeding from `clause_inventory.json`, SHACL validation. Also out: fine-tuning, safety
guardrails, any change to the hybrid stack itself.
</domain>

<decisions>
## Implementation Decisions

### Engine & framework (the central reframe)
- **D-01: Neo4j GraphRAG for BOTH Phase 9 and Phase 10 — not the Microsoft `graphrag` package.**
  Rationale: makes Phase 10 *truly additive* — Phase 9→10 differs by exactly one variable
  (extraction governance: emergent → ontology-grounded) on an identical engine, storage,
  retrieval, input, and harness. This isolates the ontology-grounding contribution cleanly
  (a proper ablation) instead of confounding it with an engine swap. Use the official
  `neo4j-graphrag-python` package.
- **D-02: Tradeoff accepted** — we forgo the "Microsoft GraphRAG published-method named
  baseline" citation. If desired later, a Microsoft `graphrag` reference run may be added as
  an *optional secondary* data point, but Neo4j is the primary track for both phases.
- **D-03: Basic = emergent KG.** Phase 9 uses `neo4j-graphrag` KG construction (e.g.
  `SimpleKGPipeline`) with **no schema constraint** — the un-governed baseline.

### Indexing input
- **D-04: Feed the same Docling-parsed CCoP text the hybrid stack uses**; let the Neo4j KG
  pipeline do its own chunking + LLM entity/relationship extraction. Input text is held
  **constant** across both systems so the comparison isolates graph-vs-vector retrieval, not
  parsing quality. (We already proved naive PDF parsing is inferior — decision [01.3-01],
  Docling replaced PyMuPDF4LLM.)
- **D-05: Reuse the existing corpus prep** (`src/rag/ingestion/` Docling parser output) rather
  than re-parsing. Do NOT pre-chunk to clause units — isolated clauses starve prose-based
  entity extraction.

### Model roles (three distinct models — only ONE is the subject under test)
GraphRAG uses a chat LLM in TWO places (extraction at index time, generation at query time)
plus an embedder. These MUST be kept separate — conflating any of them with the subject model
(`primus-reasoning`) confounds the comparison.
- **D-06 (CORRECTED — supersedes the original "primus for graph-build/query"): Answer
  generation = `primus-reasoning`, used OUTSIDE the graph.** The Neo4j graph is used as a
  **retriever only** (returns context / subgraph); `primus` generates the scored answer via the
  SAME generation path hybrid uses (retriever → primus). This holds the generator constant so
  the comparison isolates *retrieval* (graph vs vector), not the model. `primus` is NEVER used
  inside GraphRAG's own extraction or internal answer synthesis. `--mode graphrag` swaps only
  the LangGraph *retrieval* node; the primus generation node is unchanged.
- **D-06a: KG-extraction LLM = `openai/gpt-4o-mini` via OpenRouter — NOT primus.** Entity/
  relationship extraction at index time is retrieval *infrastructure* (like the embedder), not
  the subject. `gpt-4o-mini` is already the configured OpenRouter model for RAG-infra LLM tasks
  (`rag_contextualization_model`, `rag_hyde_model` in settings.py), so this is consistent
  precedent — and better/cheaper than a small local model for structured JSON extraction.
  **Held constant across Phase 9 and Phase 10** so the P9↔P10 ablation isolates the ontology,
  not the extraction model. (A capable local instruct model via Ollama remains a fallback if a
  fully-local KG build is later required.)
- **D-07 (RESOLVED): Embeddings = `BAAI/bge-large-en-v1.5` (1024-dim), exact parity with
  hybrid**, via neo4j-graphrag's `SentenceTransformerEmbeddings` (in-process — same model as
  `CCOP_QDRANT_EMBEDDING_MODEL`). No Ollama embedding endpoint needed. Vector index
  `dimensions=1024`, cosine similarity.

### Config fidelity
- **D-08: Pure defaults** — set only what's required (LLM + embedder config, vector index,
  retriever), leave chunking / extraction prompts / retrieval params at sensible defaults.
  Honest emergent baseline. All alignment/tuning belongs to Phase 10.

### Retrieval mode
- **D-09: Entity-anchored ("local") retrieval** — Neo4j VectorRetriever / VectorCypherRetriever
  (find query-relevant entities → pull their neighborhood → answer). Fits B01/B03/B04's
  clause-level questions. Global/corpus-wide sensemaking is not required here.

### Eval integration & `--mode`
- **D-10: `--mode graphrag` ships on both CLIs (mirroring hybrid/llm-only), but the mode set
  differs per command — exactly as `rag-only` already differs today:**
  - **`evaluate run`** (`VALID_EVAL_MODES`): add **`graphrag`** only — graph retrieval → primus
    generation → scored. **NO retrieval-only mode** (unscoreable without an answer; consistent
    with `rag-only` being excluded from eval, decision [02-01]). Becomes: `hybrid`, `llm-only`,
    `graphrag`.
  - **`query ask`** (`VALID_MODES`): add **`graphrag`** (graph retrieval → primus) **AND a
    graph-retrieval-only inspection mode** — the `rag-only` analog: returns the retrieved
    subgraph/context with **no generation**, for per-question retrieval inspection during KG
    iteration (D-18/19). Becomes: `hybrid`, `llm-only`, `rag-only`, `graphrag`, + graph-retrieval-only.
  - Exact naming (`graphrag-only` vs generalizing retrieval-source × generation-toggle) is an
    implementation detail for the planner.
- **D-11: Pluggable graph *retrieval* provider.** The Neo4j graph sits behind a
  retrieval-provider abstraction selected by the mode flag; it returns **retrieved contexts**
  (graph neighborhood) into the existing `primus` generation node — NOT a finished answer (see
  D-06). Output shape matches hybrid's retriever so the universal judge + RAGAs harness runs
  unchanged. Phase 10 registers a *second* provider (`--mode graphrag-ontology`) without
  touching Phase 9's — the additivity seam.

### Storage
- **D-12: Neo4j (local Docker)** — run alongside the existing Qdrant container. Persistent,
  queryable (Cypher), visualizable (Browser/Bloom) — a browsable KG is a dissertation asset.
  Local-first preserved (no cloud). Replaces Microsoft graphrag's parquet+LanceDB.

### Comparison scope & deliverable
- **D-13: Run ALL 18 fixed-GT cases** (`bdc4927d`), analyze **B01/B03/B04** deeply.
- **D-14: Deciding metrics** — composite score + per-group (retrieval quality vs response
  quality) + hallucination, compared against the canonical hybrid baseline run
  `eval-run-hybrid-tests-18-bdc4927d-20260430-0232`.
- **D-15: Deliverable** — a graphrag-vs-hybrid **comparison report** artifact (include a KG-quality section, see D-18).

### KG quality visualization & iteration
- **D-17: Graph building is a formal Phase 9 deliverable** — a first-class ingestion/build step
  (e.g. `ccop-eval graph build`), part of the graphrag pipeline. NOT a throwaway `.lab/` spike.
- **D-18: KG-quality inspection + visualization is a first-class Phase 9 capability** so the
  emergent graph can be *seen* and *measured*, not taken on faith. Two layers:
  - **Interactive (visual):** Neo4j Browser / Bloom (ships with the Neo4j service) — explore
    entities/relationships via Cypher, eyeball density/clusters/garbage.
  - **Quantitative (measurable):** a `ccop-eval graph inspect|stats` command reporting KG-quality
    metrics — node/edge counts, entity-type distribution, degree + orphan/isolated-node analysis,
    **clause coverage** (how many of `clause_inventory.json`'s 691 clauses surface as/among nodes),
    duplicate/near-duplicate entities, and extraction failure rate. This is what makes iteration
    measurable.
  - **Per-question (retrieval):** `query ask` graph-retrieval-only mode (D-10) — inspect the
    subgraph/context the graph returns for a specific question, no generation. Complements the
    global KG view above with case-level retrieval signal.
- **D-19: Iteration loop before scoring** — inspect → adjust → rebuild → re-inspect, so we never
  score a degenerate graph. **Honesty guardrail:** iteration is for making the *emergent* extraction
  *functional* (fix malformed/failed extractions, obvious garbage nodes), NOT for tuning
  chunk/prompt to chase B01/B03/B04 scores — that would blur the baseline. Any change beyond
  "make it work" is a reported, principled decision, not silent tuning (ties to the Specifics note).

### Chunking / retrieval-granularity decision (research-backed, 2026-07-02)
- **D-20: Phase 9 keeps neo4j-graphrag's default `FixedSizeSplitter` (4000 char / 200 overlap,
  single pass, NO gleaning); the coarse chunk granularity is REPORTED as an intrinsic OOTB
  limitation of the emergent baseline — NOT patched by re-chunking.** Rationale (holds D-04/D-05/
  D-08 intact and settles the Wave-6 confound question):
  - Re-chunking to clause units would (a) violate D-05 — verified: clause-level fragmentation
    *starves relationship extraction* because both endpoints of a relation must co-occur in one
    chunk (arXiv 2605.28004, "Beyond Chunk-Local Extraction"; 3-0 adversarial); and (b) add a
    second variable to the P9→P10 ablation, violating D-01.
  - "Bigger is simply better" is ALSO false: smaller chunks recover ~2× more entity references
    (600 vs 2400 tokens, Microsoft GraphRAG paper arXiv 2404.16130v2, direct ablation, 3-0). The
    field reconciles this with **gleaning** (repeated extraction passes) — Microsoft defaults to
    1200 tokens + `max_gleanings`. **neo4j-graphrag ships neither gleaning nor a structure-aware
    splitter**, so its 4000-char single-pass default is a *generic library default*, not a
    quality-tuned choice (Neo4j KG-builder docs, 3-0). Reporting it as an honest OOTB
    characteristic is therefore correct and defensible.
  - The retrieval-return-unit confound (a 4000-char chunk = ~10–40 clauses handed to primus) is a
    SEPARATE axis from the extraction unit. D-05 justifies large *extraction* chunks; it does NOT
    justify returning coarse chunks at query time. The evidence-backed fix is architectural
    (clause-node seeding + clause-anchored fine retrieval) → **Phase 10**, see D-16.
  - Wave-6 harness parity work (rerank + sparse + top_n funnel) is orthogonal to chunking and
    stays in scope for Phase 9 (a harness concern, per D-19 framing) — chunk granularity is the
    one confound axis deliberately left as a reported limitation.

### Phase-10 forward guidance (additive, do not implement here)
- **D-16:** Phase 10 layers onto this same Neo4j stack: define a CCoP ontology; deterministically
  seed clause nodes from `clause_inventory.json` (691 entries) via Cypher `MERGE`; constrain
  extraction to the ontology (schema-guided KG build); validate with SHACL (n10s in-DB OR
  rdflib/pyshacl export). Phase 9 must keep the extraction + provider stages **interceptable**
  so Phase 10 is purely additive.
- **D-16a (research-backed chunking/retrieval architecture, 2026-07-02 — informs but does not
  pre-decide Phase 10):** the evidence-backed way to get clause granularity WITHOUT re-splitting
  extraction chunks is a three-part decouple:
  1. **Extraction unit:** section-level chunks + overlap (multiple clauses per chunk) so
     relationships have co-occurrence context; ideally add a **gleaning / multi-pass** extraction
     step (neo4j-graphrag lacks it natively — must be user-added) to recover entity recall lost
     at larger chunk sizes. Do NOT clause-fragment the extraction input (D-05, D-20).
  2. **Graph backbone:** make the document's own **clause hierarchy** the primary structure
     (Title→Chapter→Article→Item nodes, parent-child edges) via the D-16 clause seeding — NOT NER
     co-occurrence. Entity-centric GraphRAG is "structurally blind" to hierarchy, a known failure
     mode for legal/regulatory text (SAT-Graph, arXiv 2505.00039v5, 3-0).
  3. **Retrieval unit:** re-anchor retrieval on the seeded **clause nodes** to return fine,
     clause-level snippets — legal RAG favors minimal precise clause segments over coarse chunks
     (LegalBench-RAG, arXiv 2408.10343, 3-0).
  - **CRITICAL for the P9→P10 comparison:** clause-node seeding alone is NOT sufficient — if
    Phase 10 retrieval still returns the coarse 4000-char chunk, the D-20 return-unit confound
    **rides into Phase 10**. The seeding MUST be paired with clause-anchored retrieval (step 3),
    else the "graph vs vector" comparison stays confounded on chunk granularity in both phases.
  - **Evidence base (all survived 3-vote adversarial verification unless noted):** section-based
    beats naive fixed-size chunking on structured statutes (NitiBench, arXiv 2502.10868 — a real
    ablation); small fixed chunks cause "concept fragmentation" on structured text (arXiv
    2502.20364). Caveat: no source ran the exact extract-large/retrieve-fine decouple ablation on
    a cybersecurity-CoP corpus — this is a synthesis, so Phase 10 should treat it as a strong
    hypothesis to *measure* (RAGAs context_precision/recall/faithfulness), not a settled result.
    Full research report: `docs/project_notes/research/2026-07-02-graphrag-chunking-regulatory.md`.

### Claude's Discretion
- Concrete `neo4j-graphrag` pipeline/retriever class selection, Neo4j Docker version, vector
  index config, and repo layout for graph artifacts — planner/executor decide within CA
  conventions.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase & project planning
- `.planning/ROADMAP.md` §"Phase 9" / §"Phase 10" — reframed titles/goals/dependencies
- `.planning/phases/03.2-corpus-ground-truth-correctness/03.2-VERIFICATION.md` — clean corpus + GT state this phase builds on
- `CLAUDE.md` §"Benchmarks (Active Set)", §"Build, Run, Test" — 18 benchmarks, `ccop-eval` CLI

### GraphRAG framework (external)
- Library: `neo4j-graphrag-python` (Context7 id `/neo4j/neo4j-graphrag-python`) — `SimpleKGPipeline`
  (schema optional), retrievers (Vector, VectorCypher, Text2Cypher, Hybrid, Tools), Ollama LLM/embedder
- Reference (secondary, if a Microsoft run is added): `/microsoft/graphrag`
- Neo4j `neosemantics` (n10s) — RDF import + `n10s.validation.shacl` (relevant to Phase 10)

### Eval bed & baseline
- `ground-truth/test-suite/` — 18 active benchmark JSONL files (fixed-GT subset hash `bdc4927d`)
- `src/results/evaluations/2026-04/eval-run-hybrid-tests-18-bdc4927d-20260430-0232-primus-reasoning.json`
  — **canonical hybrid baseline** (comparison target); `-contexts.json` sidecar for retrieval audit

### Reusable corpus / graph seed (Phase 10)
- `src/rag/ingestion/` — Docling parser + clause chunker (produces the input text for D-04)
- `src/rag/ingestion/fixtures/clause_inventory.json` — 691-entry clause inventory (Phase 10 seeding)
- `src/rag/ingestion/scripts/build_clause_inventory.py` — how the inventory is built
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/rag/ingestion/` (Docling parser, clause chunker, `run_ingestion.py`): source of the
  Docling-parsed CCoP text fed to the Neo4j KG pipeline (D-04/D-05).
- `src/rag/retrieval/` LangGraph pipeline + `IModelGateway`/graph state: the shape graphrag
  answers must conform to so judge + RAGAs run unchanged (D-11).
- `ccop-eval` CLI (`presentation/cli/`) + `evaluate run --mode ...`: where `--mode graphrag` plugs in (D-10).
- `docker-compose.yml` (Qdrant): pattern for adding a local Neo4j service (D-12).
- `clause_inventory.json` fixture: Phase-10 clause seeding source (D-16).

### Established Patterns
- Clean Architecture / ports & adapters — the graph-retrieval provider must be a port with a
  Neo4j adapter, selected via DI container by mode (mirrors the Qdrant/Databricks vector-store
  adapter selection, decision [01.2-04]).
- `--mode hybrid | llm-only` toggle in `evaluate run` — `graphrag` is an additional mode value.
- Universal LLM judge (reasoning depth + hallucination) via OpenRouter + RAGAs groups — reused as-is.

### Integration Points
- New: Neo4j **retrieval** adapter behind a `GraphRetrievalProvider` port (returns contexts, not
  answers); DI wiring; `--mode graphrag` swaps the retrieval node only; Neo4j service in
  docker-compose; graph-build ingestion (extraction = `gpt-4o-mini` via OpenRouter; embeddings =
  `bge-large-en-v1.5` in-process) consuming Docling text.
- New: `ccop-eval graph` CLI namespace — `build` (construct KG) + `inspect`/`stats` (KG-quality
  metrics, D-18), following the existing Typer subcommand pattern (`setup`/`evaluate`/`report`).
  Interactive visualization via Neo4j Browser (`http://localhost:7474`) / Bloom — no build needed.
- Unchanged: **primus generation node**, judge + RAGAs scoring, 18-case GT loading, result JSON
  schema, comparison report path.
</code_context>

<specifics>
## Specific Ideas

- The Phase-9-vs-Phase-10 experiment is the point: identical Neo4j engine/input/harness, delta =
  ontology governance only. Keep that ablation clean.
- ⚠️ Carry the known blocker: `B04/B4` test_id casing inconsistency surfaces in eval logs —
  handle during eval integration so graphrag results align with GT ids.
- Extraction quality (D-06a): the KG is built by `gpt-4o-mini`, not primus — so extraction is
  capable. What's measured is primus's *response* quality on graph-retrieved context (parity with
  hybrid). If the emergent graph is too sparse/noisy to retrieve over, that's a *finding to
  report*, not something to silently tune away — that would blur the baseline.
</specifics>

<deferred>
## Deferred Ideas

- **Ontology-grounded KG (schema-constrained extraction, clause seeding, SHACL)** — Phase 10 (D-16).
- **Global/corpus-wide sensemaking retrieval** (community summarization) — not needed for the
  entity-anchored B01/B03/B04 focus; revisit only if a global-search comparison is wanted.
- **Optional Microsoft `graphrag` reference run** — possible secondary baseline for the
  published-method citation (D-02); not in Phase 9 scope.

### Reviewed Todos (not folded)
None — no pending todos matched this phase.
</deferred>

---

*Phase: 9-basic-graphrag-baseline-neo4j-emergent-kg (dir slug: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package)*
*Context gathered: 2026-07-01*
