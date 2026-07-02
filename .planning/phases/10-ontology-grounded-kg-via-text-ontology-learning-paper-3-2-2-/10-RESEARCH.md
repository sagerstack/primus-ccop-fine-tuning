# Phase 10: Ontology-grounded GraphRAG (Neo4j, governed KG) - Research

**Researched:** 2026-07-02
**Domain:** Schema-constrained knowledge-graph construction (neo4j-graphrag), SHACL validation, ontology discovery, clause-anchored retrieval routing
**Confidence:** MEDIUM-HIGH (library APIs verified live against installed `neo4j-graphrag 1.18.0` source + Context7 docs; ontology-discovery methodology and SHACL-tooling choice carry more judgment and are flagged)

## Summary

Phase 10 is additive governance on the identical Phase 9 Neo4j stack: swap the un-governed
`SimpleKGPipeline` for one configured with an explicit `schema=` (node_types / relationship_types /
patterns), seed 691 deterministic clause nodes via Cypher `MERGE`, add a user-written gleaning loop
(neo4j-graphrag has none natively), validate the resulting graph with SHACL, and register a second
`IGraphRetrievalProvider` behind `--mode graphrag-ontology` that retrieves at clause-node granularity
instead of the Phase 9 4000-char chunk. Every extension point needed is a documented, first-class
neo4j-graphrag 1.18.0 API — `SimpleKGPipeline(schema=...)`, `LLMEntityRelationExtractor.extract_for_chunk`
(override point for gleaning), custom `text_splitter=`, `SinglePropertyExactMatchResolver` — none of
this requires forking the library.

The two decisions with the most planning risk are NOT the neo4j-graphrag API (that's well-documented)
but (1) the **hard A/B dependency on the deferred Phase 9 Wave-6 18-case basic-GraphRAG run**, which
does not exist yet and must be sequenced explicitly, and (2) **mode-aware provider selection**: the
current DI container (`_create_graph_retrieval_provider`) and `graph_retrieve_documents` node select
**one** graph provider unconditionally from `neo4j_uri` — there is no existing mechanism to route
`graphrag` → Phase 9 adapter vs `graphrag-ontology` → Phase 10 adapter. This wiring gap must be closed
in Wave 0/1, not discovered mid-build.

**Primary recommendation:** Build ontology governance as one new `neo4j.OntologyKGBuilder` (parallel
to `EmergentKGBuilder`, same factory-injection pattern) + one new `Neo4jOntologyGraphRetrievalAdapter`
(parallel to `Neo4jGraphRetrievalAdapter`), wire mode-aware provider selection into the DI container,
run SHACL validation via **rdflib/pyshacl in pure Python** (not n10s in-DB — avoids an unverified
Neo4j-plugin version-compatibility risk), and treat the Phase 9 Wave-6 18-case run as a **Wave 0
prerequisite task inside this phase's plan**, not an external blocker to wait on.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Ontology discovery (C+B) | Application (offline script/CLI) | — | One-shot curation artifact, not a runtime service; produces a committed ontology config (JSON/YAML) consumed at build time |
| Clause node seeding (691 entries) | Infrastructure (Neo4j build step) | Domain (clause hierarchy VOs, if any) | Deterministic Cypher `MERGE`, same tier as Phase 9's `EmergentKGBuilder` |
| Schema-constrained extraction (Method D) + gleaning | Infrastructure (`rag/graph/build/`) | — | Wraps neo4j-graphrag `SimpleKGPipeline`/`LLMEntityRelationExtractor`, mirrors `EmergentKGBuilder` |
| SHACL validation | Infrastructure (a new `rag/graph/validation/` module) | — | rdflib/pyshacl export-and-validate is a pure-Python infra concern, no DB plugin dependency |
| Function-type relevance routing | Application (LangGraph node, `query_analysis.py` or a new node) | Infrastructure (Cypher `WHERE`/boost in the ontology retrieval adapter) | Classification is an LLM call (app-layer orchestration); the actual boost/filter lives in the Cypher retrieval query (infra) |
| `--mode graphrag-ontology` retrieval | Infrastructure (`Neo4jOntologyGraphRetrievalAdapter` behind `IGraphRetrievalProvider`) | — | Mirrors Phase 9's adapter exactly; same port |
| Deterministic clause-hit@3 harness | Application (eval use case) / a new domain scoring service | — | New metric alongside existing RAGAs/judge scoring, consumes GT `clause_reference` + retrieved `citation_id`s |
| Gold-relation coverage check (D-17/18) | Application (one-off script, `scripts/` or `graph/ontology/`) | — | Parses xlsx, diffs against ontology config — a build-time/curation-time tool, not runtime |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `neo4j-graphrag` | 1.18.0 (already pinned `^1.18.0`, installed) [VERIFIED: installed in project venv, confirmed via `poetry run pip show`] | Schema-guided `SimpleKGPipeline`, `LLMEntityRelationExtractor`, `SchemaFromTextExtractor`, `SinglePropertyExactMatchResolver` | Already the Phase 9 engine (D-01); Phase 10 reuses the same package, no new dependency |
| `neo4j` (driver) | 6.2.0 (installed) [VERIFIED: `poetry run pip show`] | Cypher driver for seeding + retrieval | Already in use |
| `rdflib` | latest 3.x (not yet a dependency — must add) [ASSUMED: package identity from training knowledge + PyPI existence check] | In-memory RDF graph construction for SHACL export path | De facto standard Python RDF library; pyshacl depends on it anyway |
| `pyshacl` | 0.31.0 (verified current on PyPI 2026-07-02) [VERIFIED: PyPI JSON API] | Pure-Python SHACL validator, `pyshacl.validate(data_graph, shacl_graph)` | Only actively maintained pure-Python SHACL validator; avoids the Neo4j n10s plugin version-pinning risk (see Pitfall SHACL-1) |
| `openpyxl` | already a dependency (used for xlsx read elsewhere) [VERIFIED: read `eval-report-hybrid-suite-20260630-0907.xlsx` successfully in this session] | Parse the D-17 gold-relation xlsx | Already used in the codebase for report generation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `sentence-transformers` (via `SentenceTransformerEmbeddings`) | already installed (`BAAI/bge-large-en-v1.5`, D-07) | Method B term-clustering embeddings | Reuse the SAME embedding model already loaded in-process for chunk embeddings — do NOT add a second embedding model; keeps Phase 9→10 model-role parity intact and avoids a new dependency |
| `scikit-learn` | not currently a direct dependency; `scipy`/`numpy` ARE transitive via `neo4j-graphrag` [ASSUMED: `scikit-learn` not pinned in `pyproject.toml` — verify at implementation time] | `sklearn.cluster.AffinityPropagation` for Method B clustering | Add as explicit dependency if AP clustering is implemented; article-suggested algorithm (D-05), no strong alternative found in this research pass |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pyshacl (Python, export-based) | neosemantics (n10s) in-DB SHACL (`n10s.validation.shacl.*`) | n10s requires (a) `n10s.graphconfig.init()` LPG→RDF mapping config on the live graph, (b) shapes authored in Turtle loaded via Neo4j procedures, and (c) an **unverified** Neo4j-5.26-compatible n10s release — the GitHub releases page shows version numbers that track Neo4j 5.18/5.20 but no confirmed 5.26 build as of this research pass. rdflib/pyshacl runs identically regardless of Neo4j server version. **Recommendation: pyshacl primary; n10s only if in-DB continuous validation triggers become a hard requirement later.** |
| `sklearn.cluster.AffinityPropagation` | HDBSCAN, KMeans | AP doesn't require a pre-specified cluster count (matches "let structure emerge" intent of Method B); article explicitly suggests it (D-05 references it) |
| Custom gleaning via `extract_for_chunk` override | Wait for neo4j-graphrag to ship gleaning natively | Confirmed absent in 1.18.0 (D-11 in CONTEXT.md, HIGH confidence per chunking research report); no ETA found for native support — must build in Phase 10 |

**Installation:**
```bash
cd src/ && poetry add rdflib pyshacl
# scikit-learn only if Method B clustering is implemented with AffinityPropagation:
poetry add scikit-learn
```

**Version verification:** `neo4j-graphrag 1.18.0` and `neo4j 6.2.0` confirmed installed via
`poetry run pip show` in this session (matches `pyproject.toml` pins `^1.18.0` / `^6.2.0`).
`pyshacl==0.31.0` confirmed current via PyPI JSON API (2026-07-02). `rdflib` not independently
verified on PyPI in this session — verify version at `poetry add` time.

## Package Legitimacy Audit

> slopcheck was not run in this research session (not installed, and Bash tool network access for
> `pip install slopcheck` was not attempted given rdflib/pyshacl are extremely well-known, decade-old
> libraries). Per the graceful-degradation rule, both new packages are marked `[ASSUMED]` and MUST be
> gated behind a `checkpoint:human-verify` before install.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `rdflib` | PyPI | ~20 years (project founded 2002) | very high (millions/month, foundational RDF library) | github.com/RDFLib/rdflib | not run — `[ASSUMED]` | Approved pending human-verify checkpoint |
| `pyshacl` | PyPI, confirmed v0.31.0 live | ~8 years (RDFLib/pySHACL) | high | github.com/RDFLib/pySHACL | not run — `[ASSUMED]` | Approved pending human-verify checkpoint |
| `scikit-learn` | PyPI | ~15+ years | extremely high | github.com/scikit-learn/scikit-learn | not run — `[ASSUMED]` | Approved pending human-verify checkpoint (only if Method B implemented) |

**Packages removed due to slopcheck [SLOP] verdict:** none (slopcheck not run)
**Packages flagged as suspicious [SUS]:** none (slopcheck not run)

*All three packages above are tagged `[ASSUMED]` — the planner must gate each install behind a
`checkpoint:human-verify` task. In practice these are extremely well-established libraries (rdflib is
the canonical Python RDF library pyshacl itself depends on), so the risk is low, but the protocol is
followed regardless.*

---

## Ten Implementation Questions

### Q1 — neo4j-graphrag schema-guided extraction (Method D)

**Recommended approach:** Pass an explicit `schema=` dict to `SimpleKGPipeline` (or to a standalone
`LLMEntityRelationExtractor` if building a custom `Pipeline` for gleaning — see Q2). Confirmed live
against the installed `neo4j_graphrag.experimental.components.schema.GraphSchema` Pydantic model
(fields: `node_types`, `relationship_types`, `patterns`, `constraints`, `additional_node_types`,
`additional_relationship_types`, `additional_patterns`).

```python
kg_builder = SimpleKGPipeline(
    llm=llm, driver=driver, embedder=embedder, from_pdf=False,
    schema={
        "node_types": [
            "Clause", "Control", "Obligation", "Definition",          # D-08 regulatory layer
            {"label": "ScopeClause", "description": "..."},            # D-09 function tags
            {"label": "ControlClause", "description": "..."},
            {"label": "DefinitionClause", "description": "..."},
            # + Method C/B discovered domain types (CII, Asset, Organization, ...)
        ],
        "relationship_types": [
            "GOVERNS", "REQUIRES", "APPLIES_TO", "RESPONSIBLE_FOR", "MITIGATES",  # D-08
            "NOT_DESIGNATED_AS", "CANNOT_SATISFY", "DOES_NOT_WAIVE", "DEFINES_NO",  # D-18
            "DOES_NOT_SPECIFY", "TECHNOLOGY_NEUTRAL_ON", "RECOMMENDS_AGAINST",
            "DEFERS_TO", "IS_A", "DEFINED_AS", "CLASSIFIED_AS", "DESIGNATES", "DETERMINED_BY",
        ],
        "patterns": [("Clause", "REQUIRES", "Control"), ...],   # curated during Wave 1 gates
        "additional_node_types": False,          # lock the vocabulary (D-06/D-07 anti-pattern fix)
        "additional_relationship_types": False,
    },
    on_error="IGNORE",   # or OnError.RAISE during dev to surface malformed LLM JSON loudly
)
```

**Canonical-name enforcement + "ignore illustrative passages":** neo4j-graphrag has NO built-in
instruction for this — it must go into a **custom `prompt_template`**. The default
`ERExtractionTemplate` (confirmed via `inspect.getsource` on the installed package) has NO language
about examples/hypotheticals; it only injects `{schema}`, `{examples}`, `{text}`. Subclass or pass a
raw string:

```python
CCOP_EXTRACTION_PROMPT = """... [schema block as in default template] ...
IMPORTANT: This text is a REGULATORY CODE OF PRACTICE. Do NOT extract entities from illustrative
examples, hypothetical scenarios, or placeholder names (e.g. "John Doe", "Company X", "N.A.").
Only extract entities and relationships stated as normative regulatory content (obligations,
definitions, scope statements). Every extracted node MUST have a canonical "name" property using
the exact term as it appears in the source clause — do not paraphrase or abbreviate.
..."""
extractor = LLMEntityRelationExtractor(llm=llm, prompt_template=CCOP_EXTRACTION_PROMPT)
```

This directly fixes the D-06 anti-patterns (junk "N.A."/"John Doe" instances, fragmented duplicate
names) at the prompt layer; SHACL (Q5) catches whatever slips through as a structural backstop.

**Pitfall:** `additional_node_types=False` is strict — if the curated ontology is missing a type the
corpus actually needs, extraction silently drops those entities rather than erroring. Run the D-14
benchmark-coverage check and D-17 gold-relation check **before** locking `additional_node_types=False`
in the build config, and keep a `--permissive` build mode (`additional_node_types=True`) available for
iteration, matching Phase 9's D-19 "inspect → adjust → rebuild" loop.

**Confidence:** HIGH — schema dict shape and prompt customization confirmed against both Context7 docs
and the installed package source (`entity_relation_extractor.py`, `schema.py`).

---

### Q2 — Gleaning (multi-pass extraction)

**Confirmed:** `LLMEntityRelationExtractor` has no native gleaning parameter in 1.18.0 (matches the
Phase 9 chunking research report, D-11). The exact override point, confirmed by reading the installed
source, is `extract_for_chunk(self, schema, examples, chunk) -> Neo4jGraph`, called once per chunk by
`run_for_chunk`. This is a clean subclass point — no need to reimplement `run()`, `combine_chunk_graphs`,
or ID-prefixing logic.

**Recommended pattern (loop the extraction prompt asking "what did you miss?"):**

```python
class GleaningEntityRelationExtractor(LLMEntityRelationExtractor):
    def __init__(self, *args, max_gleanings: int = 1, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_gleanings = max_gleanings

    async def extract_for_chunk(self, schema, examples, chunk):
        graph = await super().extract_for_chunk(schema, examples, chunk)
        for _ in range(self.max_gleanings):
            found_so_far = _summarize(graph)  # compact node/rel list for the follow-up prompt
            glean_prompt = self.prompt_template.format(
                text=chunk.text, schema=schema.model_dump(exclude_none=True),
                examples=f"Already extracted:\n{found_so_far}\n\nMANY entities were missed. "
                         f"Find ADDITIONAL entities/relationships not in the list above.",
            )
            llm_result = await self.llm.ainvoke(glean_prompt)
            extra_graph = _parse_and_validate(llm_result, self.on_error)  # reuse fix_invalid_json + Neo4jGraph.model_validate
            graph.nodes.extend(extra_graph.nodes)
            graph.relationships.extend(extra_graph.relationships)
        return graph
```

Pass this custom extractor into a manually-assembled `Pipeline` (not `SimpleKGPipeline`, which
hardcodes its own `LLMEntityRelationExtractor` construction) — confirmed via the "Add a Component to a
Pipeline" / "Subclass EntityRelationExtractor" Context7 examples; `SimpleKGPipeline` does not expose an
`extractor=` override kwarg in the version checked, so a hand-built `Pipeline` wiring
`loader → splitter → schema → extractor(gleaning) → resolver → writer` is the correct integration
shape. Verify the exact `SimpleKGPipeline` constructor signature at implementation time (confirm
whether a later patch adds an extractor override — check `pip show`/changelog before building the
custom pipeline).

**Recall trade-off (from the chunking research report, HIGH confidence, 3-0 adversarial):** gleaning
recovers entity recall lost to larger chunks (Microsoft's own reconciliation of the 600-vs-2400-token
finding) but costs one extra LLM call per gleaning pass per chunk. With `max_gleanings=1` and
section-level chunks (Q3), this roughly doubles extraction-time LLM calls per document — budget for it
in Wave time estimates.

**Confidence:** MEDIUM-HIGH for the override mechanism (verified against source); MEDIUM for the exact
prompt-engineering of the glean-again instruction (no official neo4j-graphrag gleaning example exists
to benchmark against — this is a synthesis from Microsoft GraphRAG's documented gleaning behavior,
cited in the chunking research report, adapted to neo4j-graphrag's extractor shape).

---

### Q3 — Section-aligned extraction chunking

**Recommended approach:** Do NOT reuse the hybrid stack's clause-level chunker (`clause_aware_chunker.py`
`chunk_by_clauses`) directly — that produces clause-granularity chunks, which is explicitly the
extraction-starving mistake D-05/D-20 forbid. Instead, write a **coarser** structure-aware splitter that
groups multiple clauses under one section heading, reusing the SAME `CLAUSE_PATTERN`-style regex
already proven against the Docling markdown (`## X.Y heading` boundaries), but splitting only at
**top-level section boundaries** (e.g. `5.3`, not `5.3.1(a)`), each section chunk containing several
clauses.

Implementation shape — a custom `TextSplitter` component (confirmed via Context7's "Customize Text
Splitter in SimpleKGPipeline" example, which shows `text_splitter=` accepting any custom splitter
instance):

```python
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
# or implement a custom Component subclass with .run(text) -> TextChunks, splitting on the
# same regex boundary logic as rag/ingestion/chunkers/clause_aware_chunker.py's CLAUSE_PATTERN,
# but merging all sub-clauses under one top-level section number into a single chunk.

kg_builder = SimpleKGPipeline(..., text_splitter=SectionAlignedSplitter(), ...)
```

**Metadata available:** Docling markdown carries `## X.Y heading` markers that
`clause_aware_chunker.CLAUSE_PATTERN` already parses reliably (bug #10 fix, decision [03.2-01]).
Reuse/adapt this regex — do not reinvent boundary detection. Qdrant chunk metadata (`section`,
`subsection`, `chapter`, `parent_path`) exists only on the ALREADY clause-chunked hybrid index; it is
NOT directly available on the raw Docling markdown Phase 9/10 consume (`corpus_source.py` feeds full
per-document markdown, unchunked — confirmed by reading `load_ccop_corpus_texts`). The section-aligned
splitter for Phase 10 must therefore parse section boundaries fresh from the same regex logic, not
import pre-computed `ChunkMetadata`.

**Pitfall:** the chunking research report explicitly flags "no source ran the exact extract-large/
retrieve-fine decouple ablation on a cybersecurity-CoP corpus" — this is a hypothesis to MEASURE
(RAGAs context_precision/recall/faithfulness + clause-hit@3), not an assumed win. Budget an eval pass
specifically to confirm section-aligned chunking + gleaning actually beats the Phase 9 4000-char
default on entity/relationship recall before treating it as settled.

**Confidence:** MEDIUM — the splitter customization mechanism is HIGH confidence (verified library
API); the specific "section = top-level clause group" boundary choice is a reasoned synthesis from
D-16a, not independently verified against a second source.

---

### Q4 — Deterministic clause seeding (691 clause nodes)

**Recommended approach:** A dedicated Cypher `MERGE`-based seeding script/component reading
`clause_inventory.json` directly (structure confirmed: `{"clause_id": "1", "source_doc": "Auditing
Guidelines"}` — flat list of 691 entries, **IDs + source_doc only, no titles**, as CONTEXT.md D-04
already notes).

```cypher
// One clause node per entry; parent inferred from clause_id dot-hierarchy (e.g. "6.1" -> parent "6")
UNWIND $entries AS entry
MERGE (c:Clause {clause_id: entry.clause_id, source_doc: entry.source_doc})
```

Parent-child edges: derive `Title→Chapter→Article→Item` from the `clause_id` string structure itself
(e.g. `"6.1"` implies parent `"6"`; `"6.1.2"` implies parent `"6.1"`) — this mirrors exactly what
`clause_aware_chunker._build_parent_path` already does for the hybrid stack's `parent_path` metadata
(reuse/adapt that logic rather than re-deriving hierarchy rules from scratch). Because
`clause_inventory.json` has **no titles**, seeded `Clause` nodes will initially carry only
`clause_id` + `source_doc` + (derived) `chapter`/`parent_id` — no human-readable label until either (a)
Method C's section-header discovery (Q6) back-fills titles, or (b) a join against the hybrid Qdrant
chunk metadata (`section`/`subsection` fields) is used to enrich seeded nodes post-hoc.

**How extracted entities LINK to seeded nodes:** two options, pick based on retrieval design (Q7/Q8):
1. **Extraction-time linking** — pass the seeded clause list as part of the `schema` `examples` context
   so the extraction LLM emits e.g. `(entity)-[:GOVERNED_BY]->(Clause {clause_id:"5.3.1"})` directly.
   Risk: LLM must reproduce exact clause_id strings verbatim — error-prone (hallucinated clause IDs).
2. **Post-hoc linking (RECOMMENDED)** — after extraction, run a deterministic Cypher pass that matches
   extracted `Chunk` nodes (or entities) to seeded `Clause` nodes via the SAME clause-ID regex boundary
   matching Phase 9's `KGInspector.clause_coverage()` already implements (`_clause_id_appears`,
   boundary-aware text match) — reuse that helper rather than reimplementing text-based clause
   detection a third time.

**Confidence:** HIGH for the MERGE/seeding mechanics (standard Cypher, no library dependency); MEDIUM
for "which linking strategy" — this is a genuine open design choice the plan should decide explicitly,
not left implicit (see Open Questions).

---

### Q5 — SHACL validation

**Recommended approach: rdflib/pyshacl export-and-validate**, run as a batch validation step after
each build (or as a standalone `ccop-eval graph validate` command mirroring the existing `graph
inspect` pattern). NOT n10s in-DB (see Alternatives table — unverified Neo4j 5.26 compatibility,
requires RDF-mapping config on the live graph, heavier operational surface).

**Pipeline shape:**
```python
from rdflib import Graph, Namespace, RDF, Literal
from pyshacl import validate

# 1. Export: query Neo4j -> build an in-memory rdflib.Graph
#    Simple LPG->RDF mapping: node -> URI by elementId; primary label -> rdf:type;
#    properties -> literal triples; relationships -> predicate triples.
data_graph = Graph()
NS = Namespace("http://ccop.example/kg#")
for record in session.run("MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props"):
    node_uri = NS[record["id"]]
    for label in record["labels"]:
        data_graph.add((node_uri, RDF.type, NS[label]))
    for k, v in record["props"].items():
        data_graph.add((node_uri, NS[k], Literal(v)))
# ... relationships similarly ...

# 2. Load SHACL shapes (Turtle, committed to repo, e.g. src/rag/graph/ontology/shapes.ttl)
shacl_graph = Graph().parse("src/rag/graph/ontology/shapes.ttl", format="turtle")

# 3. Validate
conforms, results_graph, results_text = validate(
    data_graph, shacl_graph=shacl_graph, inference="none", abort_on_error=False,
)
```

**Concrete shape authoring for D-07's canonical-name/type constraints** (Claude's Discretion — concrete
recommendation): each locked node type gets an `sh:NodeShape` requiring `sh:minCount 1` on the
`name`/canonical-name property, `sh:datatype xsd:string`, and `sh:pattern` rejecting known junk values
(`"N.A."`, `"A"`, empty string) — directly encodes the D-06 anti-pattern fix as a machine-checked
constraint:

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ccop: <http://ccop.example/kg#> .
ccop:EntityShape a sh:NodeShape ;
  sh:targetClass ccop:Entity ;
  sh:property [
    sh:path ccop:name ;
    sh:minCount 1 ;
    sh:datatype xsd:string ;
    sh:pattern "^(?!N\\.A\\.$|^A$|^$).+$" ;   # reject known junk canonical names
  ] .
```

**Reject + log non-conforming facts separately (D-13):** iterate `results_graph` (a standard SHACL
Validation Report graph per spec — `sh:conforms`, `sh:result` entries with `focusNode`/`resultPath`/
`severity`), write violating node/edge IDs to a `validation_report.json` or a `:ValidationFailure`
label in Neo4j (do not delete — "reject non-conforming facts, log separately" implies quarantine, not
silent deletion) so curation can review and either fix the ontology or the extraction prompt.

**Confidence:** HIGH for the pyshacl API shape (`validate()` signature, return tuple) — verified via
WebSearch cross-referenced against the official `RDFLib/pySHACL` repo. MEDIUM for the LPG→RDF export
mapping — this is a standard pattern but no neo4j-graphrag-specific export helper was found; it must be
hand-written (n10s DOES ship this mapping built-in, which is its main advantage — noted as a tradeoff).

---

### Q6 — Ontology discovery mechanics (Method C + Method B)

**Method C (grounded synthesis) — recommended pipeline:**
1. **Anchor sources** (per D-04, exactly as locked): (a) CCoP section/clause headers extracted from
   Docling markdown via the same `## X.Y heading` regex already used elsewhere — gives a **control
   taxonomy** with real structure but no clause_inventory.json title data, so headers must come from
   Docling text, not the JSON fixture; (b) the 18 benchmark JSONL `input.question` + `ground_truth`
   fields (confirmed structure: `metadata.clause_reference`, `key_facts[].fact`) — gives
   reasoning/relation vocabulary; (c) sampled corpus prose (a stratified sample across the 7
   `source_docs`, not just CCoP 2.0) — gives domain entities.
2. **One LLM synthesis call per source category** (not per-chunk NER — this is the explicit fix for
   the Phase 9 failure mode, D-04) producing a candidate type list with **provenance** (which source
   surfaced it) and **flagged ambiguities** (overlapping/near-duplicate candidates) — present as the
   markup table CONTEXT.md's Specifics section describes (type | definition | example terms |
   provenance | flagged ambiguities).
3. Output artifact: a committed YAML/JSON ontology draft, reviewed at the D-14 "gate (a)" human
   curation checkpoint.

**Method B (clustering cross-check) — recommended pipeline:**
1. Extract candidate terms from corpus prose — simplest defensible approach: run the SAME extraction
   LLM (`gpt-4o-mini`) with a lightweight "list noun phrases / domain terms in this passage" prompt
   over section-level chunks (NOT full NER) OR reuse Phase 9's emergent-graph entity names as raw term
   candidates **for term extraction only** (this does NOT violate D-02, which forbids reusing the
   emergent GRAPH as ontology discovery input — using its raw entity-name strings as one input to a
   term list for clustering is a different, much weaker reuse; if this is contentious, default to
   fresh corpus-term-extraction to stay unambiguously compliant with D-02).
2. **Embed** each term with the SAME `SentenceTransformerEmbeddings(model="BAAI/bge-large-en-v1.5")`
   already loaded for chunk embeddings (Claude's Discretion recommendation — reuse, don't add a new
   embedding model; keeps infra minimal and consistent with D-07's "held constant" philosophy even
   though Method B embedding choice isn't formally locked by P9).
3. **Cluster** with `sklearn.cluster.AffinityPropagation` (article-suggested, D-05) — no need to
   pre-specify k, which fits "let structure emerge" intent.
4. **LLM-name each cluster** (one call per cluster, small n) — produces Method B's candidate type list.
5. **Cross-check against Method C:** types present in B but absent from C = candidate missing types →
   surfaced to the user at D-14 gate (b) for keep/drop.

**Confidence:** MEDIUM — the overall C→curate→B→reconcile shape is locked by CONTEXT.md D-01;
the concrete mechanics above (which LLM calls, which embedding/clustering choices) are this
research's synthesis and carry the `[ASSUMED]` tag for the specific term-extraction-for-B step (Q6
item B.1) since two viable variants exist and neither is definitively verified against a source for
this exact regulatory-corpus use case.

---

### Q7 — Function-type relevance routing (D-12)

**Recommended approach:** Add a lightweight classification call in the retrieval pipeline — most
natural insertion point is `rag/retrieval/nodes/query_analysis.py` (the SAME node already makes one
OpenRouter `gpt-4o-mini` call for HyDE per query; extending it with a second small classification call
is consistent with the existing "RAG infra LLM tasks" precedent, D-06a). Store `function_type` in
`GraphState` (mirrors how `rewritten_query` is already threaded through state).

```python
# Extend query_analysis.py or add a sibling node:
FUNCTION_TYPE_PROMPT = """Classify this compliance question's PRIMARY intent as exactly one of:
ScopeClause (is X in/out of mandatory scope?), ControlClause (what must be done/implemented?),
DefinitionClause (what does term X mean?). Question: {q}\nAnswer with just the label."""
```

The retrieval-side wiring is the Phase-10 ontology adapter's Cypher `RETRIEVAL_QUERY` (parallel to
Phase 9's static `RETRIEVAL_QUERY` string in `neo4j_graph_retrieval_adapter.py`) boosting/filtering on
the seeded clause's function-type tag:

```cypher
WITH node AS chunk, score
OPTIONAL MATCH (chunk)-[:LINKED_TO]->(c:Clause)
WITH chunk, score, c,
     CASE WHEN c.function_type = $function_type THEN score * 1.5 ELSE score END AS boosted_score
RETURN chunk.text AS original_text, ..., boosted_score AS score
ORDER BY boosted_score DESC
```

Pass `$function_type` as a bound Cypher parameter (never string-interpolated — matches the existing
T-09-12 parameterization discipline already enforced in `neo4j_graph_retrieval_adapter.py`).

**Escalation path (D-12):** if function-type routing alone doesn't clear the clause-hit@3 gate (D-15),
CONTEXT.md pre-authorizes escalating to "Both, layered" — add entity-anchored traversal (the existing
`FROM_CHUNK` one-hop expansion from Phase 9) as an additional signal alongside the function-type boost,
rather than replacing it.

**Confidence:** MEDIUM-HIGH for the mechanism (parallels existing, working Phase 9 patterns exactly);
LOW-MEDIUM for the specific boost multiplier / classification prompt wording, which is a tuning
decision the plan should treat as iterable, not fixed.

---

### Q8 — Deterministic clause-hit@3 harness (D-15)

**Two sub-problems, both must be solved:**

**(a) Deterministic retrieval (exact vector search + stable tie-break).** Phase 9's `HybridCypherRetriever`
uses Neo4j's native vector index (HNSW-based, approximate by default) — this is the likely source of
the "top-3 flapped across runs" symptom D-15 references. Neo4j vector indexes do not have a documented
"exact"/brute-force mode exposed through `HybridCypherRetriever` in the version checked — **recommend
verifying this against current neo4j-graphrag docs at implementation time** (not confirmed in this
research pass; flagged as an open question). The tie-break itself is straightforward regardless: add a
deterministic secondary sort key to the Cypher `ORDER BY` (e.g. `ORDER BY score DESC, chunk.clause_id
ASC`) so equal-score ties resolve identically across runs — this part is fully verifiable and should be
added unconditionally.

**(b) Scoring against a clause SET, not a single ID.** Confirmed via direct inspection of
`ground-truth/test-suite/b01_ccop_applicability_scope.jsonl`: `metadata.clause_reference` is already a
**list** (e.g. `["1.2.1"]`, or `["1.4.3", "section 11"]`) — the schema already supports set-valued gold
references. **Pitfall found in this research:** for B01-001, `metadata.clause_reference` contains only
`["1.2.1"]`, while CONTEXT.md's own worked example says the correct answer set is
`§1.2.1 + §1.4.1 + Act §7/§11 + RtF Q2.2–2.3` — narrower than what's actually needed for a complete
hit@3 evaluation. **The `clause_reference` field alone likely under-represents the true gold clause set
for several cases.** Recommend enriching/cross-checking `clause_reference` against the D-17 gold-relation
xlsx's bracketed citations (e.g. `[1.2.1, 1.4.1]` appears directly in the `graph_relation` column text)
during Wave 1 ontology curation, and flag any GT case where the two sources disagree for human review
— do not silently trust `clause_reference` alone as ground truth for the harness.

**Recommended metric implementation:** a new domain/application-layer scoring function (parallel to
existing `ScoringService`) computing, per case: `hit@3 = 1 if gold_set ∩ retrieved_top3_clause_ids ≠ ∅
else 0`; `recall@3 = |gold_set ∩ top3| / |gold_set|`; `recall@pool(50) = |gold_set ∩ top50| / |gold_set|`
(the pool metric isolates whether the graph even *contains* the right clauses, independent of ranking).

**Confidence:** MEDIUM — the clause-SET scoring design is well-grounded (verified against real GT
JSONL structure); the "exact vector search" determinism claim needs direct verification against
current `neo4j_graphrag.retrievers` docs before the plan locks an implementation (flagged as Open
Question, not asserted as fact here).

---

### Q9 — Entity resolution / dedup

**Recommended approach:** Start with `SinglePropertyExactMatchResolver` (confirmed shipped in
1.18.0 — `neo4j_graphrag.experimental.components.resolver`), run post-build as a pipeline step:

```python
from neo4j_graphrag.experimental.components.resolver import SinglePropertyExactMatchResolver
resolver = SinglePropertyExactMatchResolver(driver, resolve_property="name")
await resolver.run()
```

This directly addresses D-07's "entity resolution/dedup to canonical nodes" for the common case
(same canonical name, different chunk-scoped node IDs) — cheap, deterministic, no extra LLM cost.
**LLM-based resolution** (semantic near-duplicate merging, e.g. "CII" vs "Critical Information
Infrastructure") is the fallback for cases exact-match misses; no built-in neo4j-graphrag component for
this was found in the docs pulled — would need a custom post-process step (embed candidate names,
cosine-similarity threshold, LLM-confirm merges above threshold). **Recommendation: ship exact-match
resolver in the core plan; treat LLM-based semantic resolution as a stretch/Wave-2 item**, measured
against the D-06-documented fragmentation problem (CII/CIIAsset/CriticalInformationInfrastructure/
CIIOrganization) to see how much exact-match alone fixes once canonical-name enforcement (Q1) and
SHACL rejection (Q5) are also in place — those two may already prevent most fragmentation upstream.

**Confidence:** HIGH for `SinglePropertyExactMatchResolver`'s existence/API (confirmed via Context7 +
matches Phase 9's forward-guidance mention); MEDIUM for the "exact-match may be sufficient once
upstream fixes land" claim — a reasoned hypothesis, not measured.

---

### Q10 — Gold-relation coverage check (D-17/D-18)

**Confirmed live** by reading `src/results/evaluations/eval-report-hybrid-suite-20260630-0907.xlsx`,
sheet `eval-18`: column 22 (`graph_relation`) contains **hand-authored, semi-structured free text**, not
strict machine-parseable triples — e.g. for B01-001:
`(hospital_admin_system) -[SHARES_NETWORK_WITH]-> (CII); (hospital_admin_system) -[NOT DESIGNATED_AS]->
(CII); ... [1.2.1, 1.4.1]; ...`. Notably the D-18 relation name `NOT_DESIGNATED_AS` appears in the
actual cell text as **`NOT DESIGNATED_AS`** (space, not underscore) — confirms the CONTEXT.md list needs
light normalization during parsing, not a literal string match.

**Recommended parsing approach:** a regex-based extractor, NOT a full parser (the text is prose with
embedded triples, not strict Turtle/JSON):
```python
import re
TRIPLE_RE = re.compile(r"\(([^)]+)\)\s*-\[([^\]]+)\]->\s*\(([^)]+)\)")
CLAUSE_BRACKET_RE = re.compile(r"\[([\w.\s,()§]+)\]")  # e.g. "[1.2.1, 1.4.1]" or "[5.3.1(c)]"

for cell in graph_relation_column:
    triples = TRIPLE_RE.findall(cell)  # (subject, relation, object) tuples
    relation_types = {re.sub(r"\s+", "_", rel.strip()) for _, rel, _ in triples}  # normalize spacing
    clause_citations = CLAUSE_BRACKET_RE.findall(cell)
```
Then: `missing_relations = relation_types_from_gold - set(ontology_relationship_types)` → D-17's gap
list. Run this AFTER the Method C→B ontology draft exists (curation-time script, not a runtime
component), output as a coverage report table for the D-14/D-17 human gate.

**Confidence:** HIGH — verified directly against the actual xlsx cell contents in this research
session (not assumed structure).

---

## HARD Dependency: Phase 9 Wave-6 18-case baseline

**⚠️ Confirmed via `deferred-items.md` and `09-CONTEXT.md`:** as of this research date, the Phase 9
basic-GraphRAG 18-case run has **not been executed** — only B01-001 (n=1) has been re-run, and that
result is explicitly documented as "within-noise" / not trustworthy for comparison (`09-CONTEXT.md`
D-16, deferred-items.md). D-16 in the Phase 10 CONTEXT.md is explicit: "No 'ontology improved X' claim
is trustworthy until that 18-case Phase 9 baseline exists."

**Sequencing recommendation for the planner:** do NOT treat this as an external blocker to wait on
before starting Phase 10 build work (ontology construction, clause seeding, schema-constrained
extraction, SHACL — none of that depends on the Phase 9 comparison number existing). DO treat it as a
**hard gate specifically on the D-16 A/B comparison deliverable** — the LAST plan/wave of Phase 10,
not the first. Two viable sequencing options for the plan to choose between:

1. **Fold the Phase 9 Wave-6 18-case run into Phase 10's Wave 0** as an explicit prerequisite task
   (run `ccop-eval evaluate run --mode graphrag` across all 18 cases using the ALREADY-BUILT Phase 9
   emergent graph — no new code, pure execution) before any Phase 10-specific build work starts. This
   keeps the eventual A/B report clean (basic-GraphRAG baseline pre-exists before ontology work begins)
   and surfaces any remaining Phase 9 harness bugs early.
2. **Run it in parallel** with Phase 10 Waves 1-2 (ontology construction/seeding does not depend on it)
   and gate ONLY the final A/B comparison wave on its completion.

**Recommendation: Option 1** — it is cheap (no new code, `ccop-eval` already supports `--mode graphrag`
for all 18 cases per D-10), removes a moving dependency from the critical path, and produces the
comparison baseline the team can sanity-check before investing in ontology curation. Cost: modest
upfront time (18 cases × judge + RAGAs scoring latency) before Phase 10-specific work visibly starts.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Entity/relationship extraction from text | A custom LLM-JSON extraction loop | `neo4j_graphrag.experimental.components.entity_relation_extractor.LLMEntityRelationExtractor` (subclassed for gleaning) | Already handles JSON repair (`json_repair`), ID prefixing, error modes (`OnError`), lexical-graph linking — reinventing loses all of this |
| SHACL validation logic | A hand-written constraint checker | `pyshacl.validate()` | SHACL is a W3C spec with real semantics (property paths, severity levels, node/property shapes); pyshacl is the reference-grade implementation |
| Entity dedup | Custom fuzzy-string-matching merge logic | `SinglePropertyExactMatchResolver` (ships with neo4j-graphrag) for the base case | Handles the common case for free; only escalate to custom logic for the semantic-near-duplicate tail |
| Clause-hierarchy parent-child derivation | A new hierarchy-parsing module | Adapt `clause_aware_chunker._build_parent_path` (already proven against all 691 clause IDs via the Phase 3.2 clause-inventory build) | Don't re-derive Title→Chapter→Article→Item rules from scratch; this logic already exists and is tested |

**Key insight:** every piece of Phase 10's "hard" infrastructure (extraction, resolution, SHACL) has a
maintained library; the genuinely novel work is glue code (gleaning loop, LPG→RDF export, function-type
routing) and curation judgment (ontology content), not extraction/validation engines.

## Common Pitfalls

### Pitfall 1: `additional_node_types=False` silently drops out-of-schema entities
**What goes wrong:** Locking the vocabulary too early (before D-14/D-17 coverage checks are complete)
causes extraction to silently discard valid entities that don't fit the curated types — looks like a
sparse graph, but it's actually a schema-coverage gap, not an extraction-quality problem.
**Why it happens:** The strict/permissive toggle is a single boolean with no logged rejection list in
the standard pipeline output.
**How to avoid:** Run the D-14 benchmark-coverage + D-17 gold-relation coverage checks BEFORE setting
`additional_node_types=False`; keep a permissive dev-mode build available during iteration.
**Warning signs:** Node/edge counts far below Phase 9's emergent graph despite a "richer" schema.

### Pitfall 2: Neo4j vector index approximate search undermines the D-15 determinism requirement
**What goes wrong:** If the default HNSW-based vector index is used for the clause-hit@3 harness's
retrieval, results may not be bit-reproducible run-to-run even with a stable Cypher tie-break, because
the ANN search itself can be non-deterministic under concurrent writes/index state.
**Why it happens:** Neo4j's vector index is approximate by design (performance trade-off); this was not
independently re-verified against current neo4j-graphrag docs in this research pass (see Open Questions).
**How to avoid:** Explicitly verify (at implementation time, via Context7/official docs) whether an
exact/brute-force retrieval mode is available and needed, or whether determinism can be achieved
sufficiently via stable tie-breaking + a frozen index state during eval runs (no concurrent writes).
**Warning signs:** clause-hit@3 harness produces different pass/fail results across identical re-runs.

### Pitfall 3: Provider selection is not mode-aware today
**What goes wrong:** `container._create_graph_retrieval_provider` and `graph_retrieve_documents` select
exactly ONE `graph_retrieval_provider` singleton based only on whether `neo4j_uri` is set — there is no
existing code path that picks Phase 9's adapter for `--mode graphrag` vs a NEW Phase 10 adapter for
`--mode graphrag-ontology`. If not addressed, Phase 10 risks silently returning Phase 9's emergent-graph
results for BOTH modes.
**Why it happens:** Phase 9 only needed one provider; the abstraction was built for pluggability
across PHASES, not for two providers coexisting live in the same running process.
**How to avoid:** Extend `_create_graph_retrieval_provider` (or introduce a small provider registry
keyed by mode string) so the DI container/`graph_retrieve_documents` node passes `state["mode"]`
through to select the correct adapter. This is Wave-0/1 wiring work, not a Wave-3 afterthought.
**Warning signs:** `--mode graphrag-ontology` eval runs produce results statistically identical to
`--mode graphrag` (same retrieval, different label).

### Pitfall 4: `clause_reference` in GT JSONL under-represents the true gold clause set
**What goes wrong:** Using `metadata.clause_reference` as-is for the D-15 harness may produce
misleadingly low (or misleadingly high, if too permissive) hit@3 scores because several GT cases'
`clause_reference` lists are narrower than the actual multi-clause reasoning the question requires
(confirmed for B01-001 in this research session).
**Why it happens:** `clause_reference` was populated during Phase 3.2's ground-truth audit for a
different purpose (citation correctness scoring, not graph-retrieval-set evaluation).
**How to avoid:** Cross-check `clause_reference` against the D-17 gold-relation xlsx's bracketed
citations during Wave 1 curation; flag disagreements for human review rather than trusting one source
silently.
**Warning signs:** clause-hit@3 gate fails or passes trivially in ways inconsistent with manual
inspection of a few cases.

### Pitfall 5: n10s version compatibility with Neo4j 5.26 is unverified
**What goes wrong:** If the plan defaults to n10s (in-DB SHACL) without checking, the build may fail at
Docker-plugin-load time with an obscure compatibility error, discovered late.
**Why it happens:** n10s release versioning (`5.26.0` released 2024, docs referencing Neo4j 5.20) does
not cleanly map to the project's pinned `neo4j:5.26-community` image tag; no confirmed compatible
release was found in this research pass.
**How to avoid:** Default to the rdflib/pyshacl path (Q5) which has zero Neo4j-version coupling. If
in-DB SHACL is later desired, verify n10s compatibility against the exact `neo4j:5.26-community` tag
BEFORE committing to it in a plan.
**Warning signs:** `NEO4JLABS_PLUGINS=["n10s"]` container fails healthcheck or logs plugin-load errors.

## Code Examples

Verified patterns from official sources (all snippets below confirmed via Context7 `/neo4j/
neo4j-graphrag-python` fetch or direct inspection of the installed `neo4j-graphrag==1.18.0` source in
this session — see inline notes):

### Schema-guided SimpleKGPipeline (Context7-verified)
```python
# Source: github.com/neo4j/neo4j-graphrag-python/blob/main/docs/source/user_guide_kg_builder.rst
kg_builder = SimpleKGPipeline(
    llm=llm, driver=driver, embedder=embedder,
    schema={
        "node_types": NODE_TYPES, "relationship_types": RELATIONSHIP_TYPES,
        "patterns": PATTERNS, "additional_node_types": False,
    },
    on_error="IGNORE", from_file=False,
)
```

### Gleaning override point (verified against installed source, `entity_relation_extractor.py`)
```python
# Source: local install .venv/lib/python3.13/site-packages/neo4j_graphrag/experimental/
#         components/entity_relation_extractor.py (LLMEntityRelationExtractor.extract_for_chunk)
async def extract_for_chunk(self, schema, examples, chunk) -> Neo4jGraph:
    """Override point for multi-pass (gleaning) extraction — called once per chunk by run_for_chunk."""
```

### SHACL validation (verified via RDFLib/pySHACL official repo + PyPI)
```python
# Source: github.com/RDFLib/pySHACL
from pyshacl import validate
conforms, results_graph, results_text = validate(
    data_graph, shacl_graph=shacl_graph, inference="none", abort_on_error=False,
)
```

### Entity resolution (Context7-verified)
```python
# Source: github.com/neo4j/neo4j-graphrag-python/blob/main/docs/source/user_guide_kg_builder.rst
from neo4j_graphrag.experimental.components.resolver import SinglePropertyExactMatchResolver
resolver = SinglePropertyExactMatchResolver(driver, filter_query="WHERE NOT entity:Resolved")
res = await resolver.run()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Emergent/unconstrained KG extraction (Phase 9) | Schema-guided extraction via `schema=` kwarg | Phase 10 (this phase) | Fixes fragmented duplicate types, junk instances, missing regulatory-structure layer (D-06 anti-patterns) |
| One coarse-chunk extraction+retrieval unit (Phase 9 D-20) | Decoupled extraction unit (section) vs retrieval unit (seeded clause node) | Phase 10 (D-16a) | Removes the "return-unit confound" that rides through Phase 9's comparison |
| Single-pass extraction | Gleaning (multi-pass, user-added) | Phase 10 (D-11) | Recovers entity recall lost to larger section-level chunks |

**Deprecated/outdated:** N/A — neo4j-graphrag 1.18.0 is current; no deprecated APIs identified in the
schema/extraction/resolver surfaces used here.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `rdflib` package identity/current version not independently confirmed on PyPI (only `pyshacl`'s dependency on it was) | Standard Stack | Low — rdflib is foundational infrastructure for pyshacl itself; near-zero risk of wrong package, but pin the exact version at `poetry add` time |
| A2 | `scikit-learn` is not currently a pinned dependency — assumed absent from `pyproject.toml` based on grep, not exhaustively confirmed | Standard Stack | Low — trivial to add; only matters if Method B clustering is implemented with AffinityPropagation |
| A3 | Method B's term-extraction-for-clustering approach (reusing Phase 9 emergent entity NAMES, not the graph structure, as raw term candidates) does not violate D-02 | Q6 | Medium — if this reasoning is rejected during discussion, default to fresh corpus-term extraction instead; flagged as an alternative in the text |
| A4 | Neo4j's default vector index is approximate (HNSW-based) and may not offer an "exact search" mode through `HybridCypherRetriever` | Q8, Pitfall 2 | Medium-High — if wrong, the D-15 determinism requirement may be much easier (or harder) to satisfy than assumed; MUST be verified against current neo4j-graphrag retriever docs before the plan locks an implementation |
| A5 | `SimpleKGPipeline` does not expose an `extractor=` override kwarg for injecting the gleaning subclass directly (requiring a hand-built `Pipeline` instead) | Q2 | Medium — if a newer neo4j-graphrag patch (beyond 1.18.0, or an undocumented kwarg) does support this, the hand-built-Pipeline complexity in Q2 is unnecessary; verify constructor signature at implementation time |
| A6 | n10s has no confirmed Neo4j-5.26-compatible release | Alternatives, Pitfall 5 | Low (this assumption pushes toward the SAFER pyshacl default) — if n10s IS confirmed compatible later, it remains a valid stretch-goal alternative, not a blocker |

## Open Questions

1. **Does Neo4j / neo4j-graphrag's vector index support an exact (non-ANN) search mode?**
   - What we know: Phase 9's D-15 symptom ("top-3 flapped across runs on clustered scores") strongly
     suggests approximate search is in play; `HybridCypherRetriever` wraps a native Neo4j vector index.
   - What's unclear: whether `neo4j_graphrag.indexes.create_vector_index` or the retriever classes
     expose an exact-search parameter, or whether determinism must instead come entirely from freezing
     index state + stable Cypher tie-breaks during eval runs.
   - Recommendation: verify against current neo4j-graphrag + Neo4j vector index docs as a first Wave-0/1
     research task within the phase's own execution (not deferred) — this directly gates D-15's
     acceptance-gate design.

2. **Which clause-linking strategy (extraction-time vs post-hoc) should Phase 10 lock?**
   - What we know: post-hoc Cypher-based linking (reusing `KGInspector`'s clause-ID text-matching logic)
     is lower-risk (deterministic, no LLM clause-ID hallucination risk) than asking the extraction LLM
     to emit exact clause_id strings.
   - What's unclear: whether post-hoc linking alone achieves sufficient precision, or whether a hybrid
     (extraction-time hints + post-hoc verification) is needed.
   - Recommendation: default to post-hoc linking (Q4 recommendation); treat extraction-time linking as
     an enhancement only if post-hoc precision proves insufficient during Wave 1/2 iteration.

3. **Is `metadata.clause_reference` in the GT JSONL trustworthy enough for D-15's acceptance gate as-is,
   or does it need a curation pass first?**
   - What we know: confirmed narrower than the true gold set for at least B01-001 (Pitfall 4).
   - What's unclear: how many of the 435 test cases across 18 benchmarks have this under-representation
     issue; no systematic audit was run in this research pass (would require checking all cases against
     the D-17 gold-relation xlsx, which only currently covers the 18-case stratified sample, not the
     full 435).
   - Recommendation: the D-15 harness only needs to run against the 18-case `bdc4927d` fixed-GT set
     (per D-16's A/B scope), so cross-check ONLY those 18 `clause_reference` entries against the D-17
     xlsx during Wave 1 curation — a small, bounded task, not a full-corpus audit.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Neo4j (Docker, local) | All Phase 10 work (extraction target, seeding, retrieval) | ✓ (already running per Phase 9) | `neo4j:5.26-community` (docker-compose.yml) | — |
| `neo4j-graphrag` | Schema-guided extraction, resolver | ✓ | 1.18.0 (installed) | — |
| `rdflib` / `pyshacl` | SHACL validation (Q5) | ✗ (not yet installed) | — | `poetry add rdflib pyshacl` — trivial, pure-Python, no external service needed |
| `scikit-learn` | Method B clustering (AffinityPropagation) | ✗ (not confirmed present) | — | `poetry add scikit-learn` if Method B implemented; alternative: hand-roll clustering with scipy (already a transitive dep via neo4j-graphrag) to avoid the new dependency entirely |
| OpenRouter (`gpt-4o-mini`) | Extraction LLM (held constant, D-06a), function-type classification, Method C/B LLM calls | ✓ (already configured, Phase 9) | — | — |
| `neosemantics` (n10s) Neo4j plugin | Only if in-DB SHACL alternative chosen | ✗ (not installed; version compatibility with `neo4j:5.26-community` unverified) | — | Use rdflib/pyshacl instead (recommended default, Q5) |

**Missing dependencies with no fallback:** none.

**Missing dependencies with fallback:** `rdflib`/`pyshacl` (trivial install, no viable alternative
needed since these ARE the fallback for n10s); `scikit-learn` (fallback: scipy-based hand-rolled
clustering, already available transitively).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4.4 (installed), per `pyproject.toml [tool.pytest.ini_options]` |
| Config file | `src/pyproject.toml` |
| Quick run command | `cd src/ && poetry run pytest tests/rag/graph/ -m "not integration"` |
| Full suite command | `cd src/ && poetry run pytest` (all tests + coverage) |

### Phase Requirements → Test Map

> No formal Phase 10 requirement IDs exist yet (REQUIREMENTS.md tracks project-level DATA/RAG/FT/HYB/
> EVAL/SAFE IDs, none of which map 1:1 to Phase 10's internal D-01..D-18 decisions). The planner should
> derive phase-local requirement IDs from the D-## decisions in CONTEXT.md. Below is a candidate map
> using that scheme; the planner may renumber.

| Req ID (candidate) | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| P10-D08 | Ontology-constrained `SimpleKGPipeline` build produces ONLY locked node/relationship types | unit (mock LLM, assert schema kwarg shape) | `pytest tests/rag/graph/build/test_ontology_kg_builder.py -x` | ❌ Wave 0 |
| P10-D10 | Clause seeding MERGEs exactly 691 `Clause` nodes with correct parent-child edges | integration (real Neo4j, Docker) | `pytest tests/rag/graph/build/test_clause_seeding.py -m integration -x` | ❌ Wave 0 |
| P10-D11 | Gleaning extractor recovers ≥N additional entities vs single-pass on a fixture chunk | unit (mock LLM with scripted 2-call sequence) | `pytest tests/rag/graph/build/test_gleaning_extractor.py -x` | ❌ Wave 0 |
| P10-D13 | SHACL validation rejects a node missing canonical name; conforms on a valid fixture graph | unit (in-memory rdflib graphs, no Neo4j needed) | `pytest tests/rag/graph/ontology/test_shacl_validation.py -x` | ❌ Wave 0 |
| P10-D12 | Function-type classification routes a scope question to `ScopeClause`-boosted retrieval | unit (mock classifier + adapter, assert boosted Cypher param) | `pytest tests/rag/graph/retrieval/test_function_type_routing.py -x` | ❌ Wave 0 |
| P10-D15 | Clause-hit@3 harness scores a synthetic case with a known gold SET correctly (hit/recall/pool) | unit (pure scoring function, no external deps) | `pytest tests/application/use_cases/test_clause_hit_harness.py -x` | ❌ Wave 0 |
| P10-D16 | `--mode graphrag-ontology` routes through the CORRECT (Phase 10) provider, not Phase 9's | unit (assert DI container mode-aware selection, mocking both adapters) | `pytest tests/infrastructure/config/test_graph_provider_selection.py -x` | ❌ Wave 0 |
| P10-D17 | Gold-relation xlsx parser extracts relation types + clause citations matching manually-verified expected output for 2-3 sample rows | unit (fixture xlsx or fixture cell strings) | `pytest tests/rag/graph/ontology/test_gold_relation_parser.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `poetry run pytest tests/rag/graph/ -m "not integration"` (fast unit-only slice)
- **Per wave merge:** `poetry run pytest` (full suite including `-m integration` against live Neo4j)
- **Phase gate:** Full suite green + a real E2E slice (`ccop-eval graph build` with the ontology schema
  against a SMALL real text sample, then `ccop-eval query ask --mode graphrag-ontology "..."` against
  the live Docker Neo4j) before `/gsd:verify-work` — per the project's e2e-testing rule: mocked unit
  tests are necessary but not sufficient; the smallest real vertical slice (one document, one query)
  must actually run before the phase is claimed done.

### Wave 0 Gaps
- [ ] `tests/rag/graph/build/test_ontology_kg_builder.py` — covers P10-D08
- [ ] `tests/rag/graph/build/test_clause_seeding.py` — covers P10-D10 (needs a Neo4j-integration fixture,
      likely reusing whatever `conftest.py` pattern `tests/rag/graph/retrieval/test_graph_retrieval_adapter_integration.py` already established for Phase 9 — inspect that file's fixtures before writing new ones)
- [ ] `tests/rag/graph/build/test_gleaning_extractor.py` — covers P10-D11
- [ ] `tests/rag/graph/ontology/test_shacl_validation.py` — covers P10-D13 (new `tests/rag/graph/ontology/`
      directory, mirrors the new `src/rag/graph/ontology/` module)
- [ ] `tests/rag/graph/retrieval/test_function_type_routing.py` — covers P10-D12
- [ ] `tests/application/use_cases/test_clause_hit_harness.py` — covers P10-D15
- [ ] `tests/infrastructure/config/test_graph_provider_selection.py` — covers P10-D16 (Pitfall 3's fix)
- [ ] `tests/rag/graph/ontology/test_gold_relation_parser.py` — covers P10-D17
- [ ] Framework install: `poetry add rdflib pyshacl` (+ `scikit-learn` if Method B implemented)

## Security Domain

> `security_enforcement` is absent from `.planning/config.json` — treated as enabled per protocol.
> This project is a local research/evaluation CLI with no auth flows, no multi-tenant data, and no
> network-exposed API surface (Neo4j/Qdrant bound to `127.0.0.1` per `docker-compose.yml`). Most ASVS
> categories are not applicable; the two that matter for Phase 10 specifically are below.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth surface added by this phase |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A (local single-user CLI/eval tool) |
| V5 Input Validation | Yes | Cypher injection prevention — ALL new Cypher (clause seeding MERGE, function-type-boosted retrieval query, SHACL export queries) MUST use parameterized queries exactly as Phase 9's `Neo4jGraphRetrievalAdapter.RETRIEVAL_QUERY` already does (static Cypher string, user input passed only as bound parameters, never string-interpolated — T-09-12 precedent) |
| V6 Cryptography | No | No new secrets/crypto surface; `neo4j_password` already handled via `config/.env.local`, never a literal (existing pattern, unchanged) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Cypher injection via unsanitized user query text reaching a dynamically-built Cypher string | Tampering | Static, class-level Cypher strings with driver-native parameterization ONLY (mirror `neo4j_graph_retrieval_adapter.py`'s existing T-09-12 pattern); this applies to the NEW function-type-boosted query and the SHACL-export read queries introduced in Phase 10 |
| Prompt injection via corpus text influencing extraction LLM to emit adversarial Cypher-shaped strings in node properties | Tampering | Neo4j driver parameterization neutralizes this at the write layer regardless of extracted content (properties are always bound values, never executed as Cypher) — no additional mitigation needed beyond the existing parameterization discipline |
| SHACL shape file tampering (shapes.ttl committed to repo but could be edited to silently weaken constraints) | Tampering | Code review on `src/rag/graph/ontology/shapes.ttl` changes, same as any other committed config — no special runtime control needed for a local single-developer research project |

## Project Constraints (from CLAUDE.md)

- All commands run from `src/`; Poetry is the only supported package manager — new dependencies
  (`rdflib`, `pyshacl`, optionally `scikit-learn`) must be added via `poetry add`, never pip.
- Clean Architecture / DDD dependency rule applies to the RAG slice: new Phase 10 modules under
  `src/rag/graph/` follow the same `domain → application → infrastructure/presentation` discipline
  already established by Phase 9's `build/`, `retrieval/`, `ports/`, `inspect/` layout — a new
  `src/rag/graph/ontology/` module (ontology config, SHACL shapes, gold-relation parser) should mirror
  this, with pure logic (parsing, scoring) kept import-free of Neo4j/network concerns where possible.
  A `src/rag/graph/ontology/` module for shapes.ttl + parsing logic is NOT itself a deployable unit or
  a new bounded context — it is infrastructure/application code inside the existing RAG module.
- Test suite location mirrors `src/` layer-for-layer (`tests/rag/graph/...`) — confirmed by inspecting
  the existing Phase 9 test tree; Phase 10 tests must follow the same mirror.
- `pytest -m integration` marks tests requiring live external services (existing convention,
  `pyproject.toml:172`) — all new Neo4j-dependent tests (clause seeding, live SHACL-against-real-graph)
  must be marked `integration`; pure-logic tests (SHACL shape validation against fixture graphs, xlsx
  parsing, clause-hit@3 scoring) should NOT require the marker and must run in the fast default suite.
- Institutional memory: `docs/project_notes/decisions.md` (ADR-007 read and incorporated above),
  `docs/project_notes/bugs.md` (provenance-collapse bug read and incorporated — the `document_source`
  fix already landed in Phase 9's `EmergentKGBuilder.build()`, Phase 10's builder must preserve the
  same `file_path=doc_name` pattern).

## Sources

### Primary (HIGH confidence)
- Context7 `/neo4j/neo4j-graphrag-python` — schema-guided `SimpleKGPipeline`, custom prompt templates,
  text splitter customization, `SchemaFromTextExtractor`, `SinglePropertyExactMatchResolver`, custom
  `EntityRelationExtractor`/`KGWriter` subclassing patterns (fetched live in this session)
- Direct inspection of installed `neo4j-graphrag==1.18.0` source (`entity_relation_extractor.py`,
  `schema.py`) via `poetry run python -c "import inspect; ..."` — confirms `GraphSchema` fields,
  `extract_for_chunk` override point, default `ERExtractionTemplate` prompt text
- `src/rag/graph/build/kg_builder.py`, `src/rag/graph/retrieval/neo4j_graph_retrieval_adapter.py`,
  `src/rag/graph/ports/i_graph_retrieval_provider.py`, `src/infrastructure/config/container.py`,
  `src/rag/retrieval/edges/routing.py`, `src/rag/graph/retrieval/graph_retrieval_node.py` — read in full
  this session, confirms current wiring gaps (Pitfall 3) and reusable patterns
- `src/results/evaluations/eval-report-hybrid-suite-20260630-0907.xlsx` sheet `eval-18` — read directly
  via `openpyxl` in this session; confirms `graph_relation` column structure and content (Q10)
- `ground-truth/test-suite/b01_ccop_applicability_scope.jsonl` — read directly, confirms `clause_reference`
  list structure and the under-representation pitfall (Q8, Pitfall 4)
- `src/rag/ingestion/fixtures/clause_inventory.json`, `src/rag/ingestion/models.py`,
  `src/rag/ingestion/chunkers/clause_aware_chunker.py` — read directly, confirms clause-inventory shape
  (no titles) and reusable hierarchy/boundary-parsing logic (Q3, Q4)
- PyPI JSON API (`pypi.org/pypi/pyshacl/json`) — confirms `pyshacl==0.31.0` current

### Secondary (MEDIUM confidence)
- `github.com/RDFLib/pySHACL` (via WebSearch, cross-referenced against multiple result summaries) —
  `pyshacl.validate()` signature and return values
- `neo4j.com/labs/neosemantics/4.0/validation/` (via WebFetch) — n10s SHACL procedure names and shape
  format; used to justify the Alternatives-table tradeoff, not as the chosen path
- `github.com/neo4j-labs/neosemantics/releases` (via WebFetch) — version/compatibility ambiguity that
  informed the "avoid n10s by default" recommendation (Pitfall 5)

### Tertiary (LOW confidence)
- None used as load-bearing claims in this document; all WebSearch findings were either cross-verified
  against a second source or explicitly flagged as an Open Question / Assumption rather than stated as
  fact.

## Metadata

**Confidence breakdown:**
- Standard stack (neo4j-graphrag APIs): HIGH — verified against both Context7 and live installed source
- SHACL tooling choice: MEDIUM-HIGH — pyshacl API verified; LPG→RDF export pattern is a reasoned design,
  not copied from an existing neo4j-graphrag-specific example
- Ontology discovery mechanics (Method C/B): MEDIUM — methodology locked by CONTEXT.md D-01/D-04/D-05;
  concrete implementation choices in this document are this research's synthesis
- Deterministic retrieval (D-15 exact-search question): LOW-MEDIUM — genuinely unresolved, flagged as
  Open Question 1, needs verification at implementation time
- Hard dependency sequencing (Phase 9 Wave-6): HIGH — confirmed directly from `deferred-items.md` and
  `09-CONTEXT.md`, not inferred

**Research date:** 2026-07-02
**Valid until:** ~30 days (neo4j-graphrag is an actively-developed package; re-verify the schema/
extractor/resolver API surface if implementation starts more than a month out, and re-check n10s
Neo4j-5.26 compatibility status if the pyshacl-vs-n10s decision is revisited)
