# Phase 11: Align GraphRAG to GraphCompliance - Pattern Map

**Mapped:** 2026-07-04
**Files analyzed:** 24 (new/modified, across Wave 0-5)
**Analogs found:** 22 / 24

## File Classification

| New/Modified File (anticipated) | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/rag/ingestion/chunkers/clause_aware_chunker.py` (FIX, not new) | utility/transform | file-I/O -> CRUD (chunk emission) | itself (existing, bug fix to 5.2->5.3 boundary regex) | exact (same file) |
| `src/rag/ingestion/scripts/build_clause_inventory.py` (extend/verify) | utility | batch | itself | exact (same file) |
| Wave-0 completeness-gate script (new, e.g. `verify_clause_completeness.py`) | utility/validator | batch | `src/rag/graph/ontology/shacl_validator.py` (validate + quarantine-report pattern) | role-match |
| `src/rag/graph/ontology/cu_classifier.py` (new — premise/meta-CU/actor-CU stage 1) | service (LLM classification) | batch / transform | `src/rag/retrieval/nodes/function_type_routing.py` (settings-gated LLM classify, enum-validated output) | strong role-match |
| `src/rag/graph/ontology/cu_extractor.py` (new — stage 2, 4-tuple extraction) | service (schema-constrained LLM extraction) | batch / transform | `src/rag/graph/build/gleaning_extractor.py` + `ontology_kg_builder.py` (`ONTOLOGY_EXTRACTION_PROMPT`, JSON-repair/validate path) | strong role-match |
| `src/rag/graph/ontology/refers_to_linker.py` (new — stage 3, REFERS_TO linking) | service (regex + LLM linking) | batch / transform | `src/rag/graph/ontology/clause_linker.py` (deterministic post-hoc MERGE-linking pass, boundary-aware match reuse) | strong role-match |
| `src/rag/graph/ontology/cu_seeder.py` or extend `clause_seeder.py` (CU nodes, namespaced ids) | service (deterministic MERGE seeding) | CRUD (graph write) | `src/rag/graph/ontology/clause_seeder.py` (MERGE-seed pattern, composite uniqueness constraint, `SeedStats` dataclass) | exact |
| `src/rag/graph/build/policy_graph_builder.py` (new — orchestrates stage 1-3 build) | service (build orchestrator) | batch | `src/rag/graph/build/ontology_kg_builder.py` (`OntologyKGBuilder`, `BuildStats`, factory-injection, idempotent index bootstrap) | exact |
| `src/rag/retrieval/nodes/context_graph_extraction.py` (new — per-query ER/SAO triple extraction) | hook/node (LangGraph node) | request-response | `src/rag/retrieval/nodes/query_analysis.py` (`analyze_query`, settings-gated OpenRouter call, graceful degradation) | strong role-match |
| `src/rag/retrieval/nodes/anchor_hypernym_mapping.py` (new — anchor extraction + hypernym mapping) | hook/node | request-response | `src/rag/retrieval/nodes/function_type_routing.py` (classify -> validate against locked enum -> store in state) | strong role-match |
| `src/rag/graph/retrieval/neo4j_compliance_gate_adapter.py` (new — anchor->CU retrieval provider) | service/adapter (graph retrieval provider) | request-response | `src/rag/graph/retrieval/neo4j_ontology_graph_retrieval_adapter.py` (`IGraphRetrievalProvider` impl, Lucene escaping, static parameterized Cypher, dual dense+BM25 channels) | exact |
| CU Plan reranking step (extend `reranking.py` or new node) | hook/node | request-response | `src/rag/retrieval/nodes/reranking.py` (cross-encoder rerank, RRF ensemble, top-N funnel) | role-match |
| Compliance-Gate judgment node (new, e.g. `compliance_judgment.py`) | hook/node (LLM judge + generation) | request-response | `src/rag/retrieval/nodes/generation.py` (`generate_response` — prompt assembly, token/latency capture, structured citation build) | strong role-match |
| REFERS_TO exception-closure node (new) | hook/node | request-response | `src/rag/graph/ontology/clause_linker.py` (graph traversal query pattern) + `generation.py` (2nd LLM call shape) | partial match |
| `src/rag/graph/retrieval/graph_retrieval_node.py` (extend — 3rd mode branch) | hook/node (LangGraph node, mode dispatch) | request-response | itself (existing `graph_retrieve_documents`, mode-aware provider selection) | exact (extend in place) |
| `src/rag/retrieval/edges/routing.py` (extend — `graph-compliance` routing key) | route/edge fn | request-response | itself (existing `route_by_mode`) | exact (extend in place) |
| `src/rag/retrieval/graph.py` (extend — wire new nodes into StateGraph) | config/wiring | request-response | itself (existing `build_rag_graph`) | exact (extend in place) |
| `src/rag/retrieval/state/graph_state.py` (extend — CU Plan / anchors / trace fields) | model (TypedDict state) | request-response | itself (existing `GraphState`, e.g. `function_type` field precedent) | exact (extend in place) |
| `src/infrastructure/config/container.py` (extend — new provider singleton) | config/DI | request-response | itself (existing `_create_ontology_graph_retrieval_provider` / `graph_retrieval_provider_ontology`) | exact (extend in place) |
| `src/domain/value_objects/run_id.py` (extend `_VALID_MODES`) | model (value object) | validation | itself | exact (extend in place) |
| `src/presentation/cli/commands/evaluate.py` (extend `VALID_EVAL_MODES`) | controller (CLI command) | request-response | itself | exact (extend in place) |
| `src/application/use_cases/evaluate_model.py` (extend `_RETRIEVAL_EVAL_MODES`) | service (use case) | CRUD | itself | exact (extend in place) |
| `src/rag/presentation/cli/query.py` (extend mode choices) | controller (CLI command) | request-response | itself | exact (extend in place) |
| `src/rag/graph/cli/graph.py` (extend — `graph build-compliance` command) | controller (CLI command) | batch | itself (existing `build` / `build-ontology` commands) | exact (extend in place) |
| `src/application/use_cases/clause_hit_harness.py` (reuse/extend for graph-compliance mode) | service (eval harness) | batch | itself | exact (reuse, extend provider param) |

## Pattern Assignments

### Wave 0 — Clause-aware chunker fix + completeness gate

**Analog:** `src/rag/ingestion/chunkers/clause_aware_chunker.py` (the file itself — this is a bug fix, not a new file)

**Bug location** (the 5.2→5.3 boundary regex, lines 42-45):
```python
CLAUSE_PATTERN = re.compile(
    r"^(?:##\s+|-\s+(?=\d+\.))?(\d+(?:\.\d+)*(?:\([a-z]\))?)\s+(.+?)$",
    re.MULTILINE,
)
```
The docstring (lines 22-33) already documents the known list-item absorption failure mode (clauses 6.1.1, 8.2.5) — the same failure class applies to 5.2→5.3. Fix must extend the pattern or its list-item branch without breaking the documented cases; write a regression test per clause id that was previously glued to a neighbor.

**Clause emission loop** (no-merge discipline, lines 109-135): every clause match emits its own chunk (`i += 3` per group, no merging) — the same discipline must hold once the boundary bug is fixed (do not reintroduce clause-body-merging as a "solution").

**Completeness-gate analog:** `src/rag/graph/ontology/shacl_validator.py` — the **validate + quarantine-report, never silently mutate** shape (lines 1-25 docstring; `ValidationReport`/`Violation` dataclasses at lines 65-90) is the pattern to copy for D-19's "assert every clause_id in `clause_inventory.json` resolves to retrievable verbatim text; fail loudly at build" gate: produce a `CompletenessReport` dataclass, write it to a committed JSON artifact, and raise/exit non-zero on any missing clause rather than logging-and-continuing.

**Provenance-integrity analog (D-20):** `src/rag/graph/build/ontology_kg_builder.py` lines 362-374 — the `file_path=doc_name` fix (bugs.md 2026-07-02) that prevents `document.txt` collapse:
```python
await self.runner.run(
    {"text": text, "file_path": doc_name, "document_metadata": None}
)
```
Any new Wave-0 re-ingestion path MUST pass a real per-doc `file_path`/provenance field the same way — copy this call shape verbatim, do not reintroduce a shared default.

---

### Policy Graph construction — Stage 1 (premise/meta-CU/actor-CU classification)

**Analog:** `src/rag/retrieval/nodes/function_type_routing.py`

**Settings-gated LLM classification pattern** (lines 53-93):
```python
def _classify_function_type(question: str, settings) -> str:
    if not settings.openrouter_api_key:
        logger.warning("... OPENROUTER_API_KEY not set; skipping")
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openrouter_api_key,
                         base_url=settings.openrouter_base_url, timeout=60)
        resp = client.chat.completions.create(
            model=settings.ontology_discovery_model,
            messages=[{"role": "user", "content": FUNCTION_TYPE_PROMPT.format(q=question)}],
            temperature=0.0, max_tokens=10,
        )
        raw = (resp.choices[0].message.content or "").strip()
        normalized = raw.strip("\"'. \n\t")
        if normalized not in VALID_FUNCTION_TYPES:
            logger.warning(f"... unrecognized label ({raw!r}); defaulting to no boost")
            return ""
        return normalized
    except Exception as e:
        logger.warning(f"Function-type classification failed: {e}")
        return ""
```
Copy this exact shape for the CU premise/meta-CU/actor-CU classifier: locked 3-value enum (`VALID_FUNCTION_TYPES` -> `VALID_CU_TYPES = {"premise", "meta-CU", "actor-CU"}`), defensive quote/punctuation stripping before validating, never raise on bad LLM output — degrade to a safe default and log. D-03's warm-start mapping (`DefinitionClause -> premise`, `ScopeClause -> meta-CU`, `ControlClause -> actor-CU`) should be encoded as a static dict exactly like `clause_seeder.py`'s `_CCOP_2_0_SECTION_FUNCTION_TYPE` (lines 86-97) — a verified, documented mapping with an explicit `DEFAULT_*` fallback constant (line 81), not silent guessing.

---

### Policy Graph construction — Stage 2 (4-tuple extraction)

**Analog:** `src/rag/graph/build/ontology_kg_builder.py` (extraction prompt discipline) + `src/rag/graph/build/gleaning_extractor.py` (JSON-repair/validate reuse)

**Schema-constrained prompt pattern** (`ontology_kg_builder.py` lines 92-131, `ONTOLOGY_EXTRACTION_PROMPT`): locked vocabulary injected via `{schema}` placeholder, explicit "do not invent" instruction, strict JSON-only output contract, canonical-name enforcement. Copy this template shape for the CU 4-tuple extraction prompt (`⟨subject, constraint, context, conditions⟩`), swapping the node/relationship schema block for the CU tuple schema.

**JSON-repair/validate reuse pattern** (`gleaning_extractor.py` lines 152-192, `_parse_graph_response`):
```python
try:
    repaired_json = fix_invalid_json(raw_content)
    result = json.loads(repaired_json)
except (json.JSONDecodeError, InvalidJSONError) as e:
    if self.on_error == OnError.RAISE:
        raise LLMGenerationError(...) from e
    logger.error(...)
    return Neo4jGraph()  # empty, never crashes the batch
```
Do not hand-roll a new JSON repair function — reuse `neo4j_graphrag`'s `fix_invalid_json` the same way, or if the CU extractor is not built on `neo4j_graphrag`'s pipeline, mirror this exact try/except/degrade shape with a Pydantic model for the CU 4-tuple.

---

### Policy Graph construction — Stage 3 (REFERS_TO linking)

**Analog:** `src/rag/graph/ontology/clause_linker.py`

**Deterministic post-hoc MERGE-linking pattern** (whole file, especially lines 39-54, 110-133):
```python
_LINK_CHUNKS_TO_CLAUSES_QUERY = """
UNWIND $pairs AS pair
MATCH (chunk) WHERE elementId(chunk) = pair.chunk_id
MATCH (clause:Clause) WHERE elementId(clause) = pair.clause_element_id
MERGE (chunk)-[:LINKED_TO]->(clause)
""".strip()

@staticmethod
def _compute_pairs(chunks, clauses) -> list[dict[str, Any]]:
    pairs = []
    for chunk in chunks:
        haystack_lower = chunk["text"].lower()
        for clause in clauses:
            if KGInspector._clause_id_appears(clause["clause_id"], haystack_lower):
                pairs.append({...})
    return pairs
```
This is the template for the regex-explicit-reference half of D-05's REFERS_TO linker: static parameterized Cypher (`$pairs`, never string-interpolated — T-09-12 discipline appears throughout this codebase and MUST be followed), a `LinkStats`-shaped dataclass reporting authoritative post-link counts read back from Neo4j (lines 165-173, `_accumulate_stats`), and reuse of `KGInspector._clause_id_appears`'s boundary-aware regex (`src/rag/graph/inspect/metrics.py:184-193`) rather than reimplementing substring matching — this exact boundary-aware matcher is what prevents `"5.3"` from spuriously matching inside `"5.3.10"` and should be reused a third time for REFERS_TO candidate detection, not reimplemented.

For the LLM half (implicit/relative references), reuse the Stage-1 classifier pattern (settings-gated call, try/except degrade, enum-or-empty output) rather than inventing a new LLM-call shape.

---

### CU node seeding (namespaced ids, D-06/D-07/D-08)

**Analog:** `src/rag/graph/ontology/clause_seeder.py`

**MERGE-seed + composite-key + idempotent-constraint pattern** (lines 165-260):
```python
def _ensure_constraint(self) -> None:
    try:
        session.run(
            "CREATE CONSTRAINT clause_id_source_doc_unique IF NOT EXISTS "
            "FOR (c:Clause) REQUIRE (c.clause_id, c.source_doc) IS UNIQUE"
        )
    except Exception as e:
        if "already exists" in str(e).lower():
            logger.info("... already exists — skipping creation.")
        else:
            logger.warning(f"Could not create ... constraint (non-fatal): {e}")
```
The composite `(clause_id, source_doc)` MERGE key (module docstring lines 10-14) is exactly the D-08 namespacing fix (`CCoP-5.7.2(b)` vs `Act-7`) the planner needs for CU nodes: MERGE key should be `(cu_id, source_doc)` or `(citation_id)` where `citation_id` is already namespaced. `SeedStats` (lines 155-162) is the dataclass shape to copy for a `CUSeedStats` (never trust in-process counters — always re-query Neo4j for authoritative counts, `_accumulate_stats` lines 262-282).

**D-07 CU-candidacy filter (headers are not CUs):** `_derive_parent`/`_derive_chapter` (lines 108-137) already implement the dot/paren clause-hierarchy parsing that distinguishes a leaf clause from its parent section — reuse this to decide which `clause_id`s become CU candidates (leaves + lettered sub-items only, per D-07) vs. which remain pure `CONTAIN`-hierarchy skeleton nodes (chapter/section headers, never a CU).

---

### Policy Graph build orchestrator

**Analog:** `src/rag/graph/build/ontology_kg_builder.py`

**Factory-injection + idempotent-index-bootstrap + BuildStats pattern** (whole class `OntologyKGBuilder`, lines 257-399):
```python
def __init__(self, settings, driver=None, llm_factory=_default_llm_factory,
             embedder_factory=_default_embedder_factory,
             runner_factory=_default_runner_factory, ...) -> None:
    ...
    self._ensure_vector_index()
    self._ensure_fulltext_index()
    ...

async def build(self, texts: dict[str, str]) -> BuildStats:
    stats = BuildStats()
    for doc_name, text in texts.items():
        try:
            await self.runner.run({"text": text, "file_path": doc_name, ...})
            stats.docs_processed += 1
        except Exception as e:
            logger.error(f"... failed for document '{doc_name}': {e}")
            stats.failures.append(f"{doc_name}: {e}")
    self._accumulate_graph_stats(stats)
    return stats
```
This is the template for a `PolicyGraphBuilder` that drives Stage 1 -> 2 -> 3 in sequence per document: injectable factories (unit-testable without hitting a live driver/LLM), failures collected in a list (never swallowed — T-09-08 discipline), and stats always re-queried from Neo4j after the build rather than trusted from in-process counters.

---

### Context Graph extraction (per-query ER/SAO triples) + anchor/hypernym mapping

**Analog:** `src/rag/retrieval/nodes/query_analysis.py` (`analyze_query`) for the node shape; `src/rag/retrieval/nodes/function_type_routing.py` (`classify_function_type`) for the mode-gated, state-writing pattern.

**Mode-gated LangGraph node pattern** (`function_type_routing.py` lines 96-119):
```python
def classify_function_type(state: GraphState) -> GraphState:
    settings = get_settings()
    query = state.get("query", "")
    if state.get("mode") != "graphrag-ontology":
        state["function_type"] = state.get("function_type", "")
        return state
    function_type = _classify_function_type(query, settings)
    state["function_type"] = function_type
    return state
```
Copy this exact no-op-unless-mode-matches shape for `extract_context_graph` (ER/SAO triples) and `map_anchors_to_hypernyms` — gated on `state.get("mode") == "graph-compliance"` (or the chosen mode name), a no-op for every other mode, writing into new `GraphState` fields (`context_graph_triples`, `anchors`, `hypernym_mappings`) the same way `function_type` was reserved on the state contract before its consuming node existed (see `graph_state.py` lines 39-43 comment — that is the precedent for "this plan reserves the field, a later plan consumes it").

**Graceful degradation pattern** (`query_analysis.py` lines 27-48, `_generate_hyde`): settings-gated `if not settings.openrouter_api_key: ... return ""`, try/except around the OpenAI call, log-and-return-empty on failure — never raise, never break the pipeline on an LLM hiccup. This applies to every new per-query LLM call in Phase 11 (Context Graph extraction, anchor hypernym mapping, listwise judgment, exception-closure check).

---

### Compliance Gate — anchor->CU retrieval (bi-encoder + cross-encoder, two-channel recall)

**Analog:** `src/rag/graph/retrieval/neo4j_ontology_graph_retrieval_adapter.py`

**`IGraphRetrievalProvider` implementation shape** (whole class, lines 83-227) — this is the strongest, most directly reusable analog in the codebase:
```python
class Neo4jOntologyGraphRetrievalAdapter(IGraphRetrievalProvider):
    RETRIEVAL_QUERY = """
WITH node AS chunk, score
OPTIONAL MATCH (chunk)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (chunk)-[:LINKED_TO]->(c:Clause)
WITH chunk, score, doc, c,
     coalesce(c.clause_id, elementId(chunk)) AS resolved_citation_id,
     CASE WHEN c.function_type = $function_type THEN score * $boost ELSE score END AS boosted_score
RETURN chunk.text AS original_text, resolved_citation_id AS citation_id, ...
ORDER BY boosted_score DESC, resolved_citation_id ASC
""".strip()

    def __init__(self, settings, driver=None, embedder=None, retriever=None, logger_=None):
        ...
        self._retriever = retriever or HybridCypherRetriever(
            driver=self._driver, vector_index_name=..., fulltext_index_name=...,
            retrieval_query=self.RETRIEVAL_QUERY, embedder=self._embedder,
            result_formatter=self._format_record, neo4j_database=settings.neo4j_database,
        )

    def retrieve(self, query: str, top_k: int, function_type: str = "") -> list[Document]:
        query_vector = self._embedder.embed_query(query)
        escaped_query_text = _escape_lucene_query_text(query)
        result = self._retriever.search(
            query_text=escaped_query_text, query_vector=query_vector, top_k=top_k,
            query_params={"function_type": function_type or "", "boost": self.settings.function_type_boost},
        )
        return [Document(page_content=item.content, metadata=dict(item.metadata or {})) for item in result.items]
```
Build `Neo4jComplianceGateAdapter` (or similarly named) on this exact template:
- Same `IGraphRetrievalProvider` interface + additive-signature-extension convention (the port's abstract `retrieve(query, top_k)` is left untouched; the concrete class adds extra kwargs — `function_type` here, `anchors`/`hypernyms` for the new adapter).
- The dual-channel D-13 recall requirement (paper anchor->CU-subject match + hybrid dense/BM25 over verbatim clause text) maps directly onto this file's existing dense (`embed_query`) + Lucene fulltext (`HybridCypherRetriever`) duality — extend `RETRIEVAL_QUERY` to `MATCH`/`OPTIONAL MATCH` onto `:ComplianceUnit` nodes the same way it currently expands `:Chunk -[:LINKED_TO]-> :Clause`.
- **Lucene escaping (D-23) is MANDATORY reuse, not reinvention:** `_escape_lucene_query_text` (lines 65-80) and `_LUCENE_SPECIAL_CHARS_RE` (line 62) must be imported/reused verbatim for the new adapter's fulltext/BM25 channel over verbatim clause text — this is the exact regression D-23 flags.
- **Provable routing marker convention:** every returned `Document.metadata["provider"]` carries a literal string tag (`"graphrag-ontology"`, line 171) distinguishing this provider's output — the new adapter must set its own distinct tag (e.g. `"graph-compliance"`), never reuse an existing one (this is also the mechanism the D-17 verbose-io trace and eval harness rely on to prove which path actually ran).
- **Deterministic tie-break (D-15 lineage):** `ORDER BY boosted_score DESC, resolved_citation_id ASC` — carry the same secondary sort key discipline into the CU-scoring query so clause-hit@3 stays reproducible.

**Cross-encoder reranking funnel reuse:** `src/rag/retrieval/nodes/reranking.py` (`rerank_documents`, whole file) — the RRF ensemble (`rrf = rrf_w_d / (K + r_d) + rrf_w_c / (K + r_c)`, lines 105-117) and top-N funnel (`top_docs = scored_for_topn[:top_n]`, lines 264-266) is the pattern for the CU Plan's bi-encoder-K1 -> cross-encoder-rerank funnel (D-11, eq. 3-4). The listwise-CE-scoring shape (`model.predict(pairs)` over `(query, doc.page_content)` tuples, lines 85-91) generalizes directly to `(q(a), d(c))` tuples built from `[predicate; actor_type; object_type]` vs `[subject; constraint; condition]` — build the pair strings, call the same cross-encoder, reuse the RRF combine.

---

### Compliance Gate — structured listwise judgment + reference-closure exception handling

**Analog:** `src/rag/retrieval/nodes/generation.py` (`generate_response`)

**Prompt-assembly + token/latency capture pattern** (whole file, especially lines 163-248):
```python
_start = perf_counter()
try:
    formatted_messages = generation_prompt.format_messages(context=context, query=query)
    _system_msg = next((m for m in formatted_messages if m.type == "system"), None)
    _human_msg = next((m for m in formatted_messages if m.type == "human"), None)
    state["system_prompt"] = _system_msg.content if _system_msg else ""
    state["user_prompt"] = _human_msg.content if _human_msg else ""

    chain = generation_prompt | llm
    response = chain.invoke({"context": context, "query": query})
    state["latency_ms"] = int((perf_counter() - _start) * 1000)

    response_metadata = getattr(response, "response_metadata", {}) or {}
    usage_metadata = getattr(response, "usage_metadata", {}) or {}
    prompt_tokens = response_metadata.get("prompt_eval_count", usage_metadata.get("input_tokens", 0))
    completion_tokens = response_metadata.get("eval_count", usage_metadata.get("output_tokens", 0))
    total_tokens = usage_metadata.get("total_tokens") or (prompt_tokens + completion_tokens)
    state["prompt_tokens"] = prompt_tokens
    state["completion_tokens"] = completion_tokens
    state["total_tokens"] = total_tokens
except Exception as e:
    state["latency_ms"] = int((perf_counter() - _start) * 1000)
    state["prompt_tokens"] = 0
    state["completion_tokens"] = 0
    state["total_tokens"] = 0
    logger.error(f"Generation failed: {e}")
    state["error"] = f"Generation error: {str(e)}"
```
This IS the D-21 fix template — copy this exact capture-before-and-after-the-call shape for the new Compliance-Gate judgment node so `system_prompt`/`user_prompt`/`prompt_tokens`/`completion_tokens`/`total_tokens`/`latency_ms` are populated for `--mode graph-compliance` exactly as they already are for `hybrid`/`graphrag`/`graphrag-ontology` (contrast with `src/rag/retrieval/nodes/rag_response.py` lines 44-50, which intentionally hardcodes zeros because there is NO LLM call in that retrieval-only path — the new judgment node DOES call an LLM, so it must follow `generate_response`'s pattern, not `rag_only_response`'s).

**Structured-output discipline:** the judgment prompt (per-CU `{label, confidence, rationale, evidence}`, D-12) should follow the same "strict JSON-only, locked vocabulary" discipline as `ONTOLOGY_EXTRACTION_PROMPT` (`ontology_kg_builder.py` lines 92-131) rather than free text + regex parsing — Pydantic-validate the judge's JSON output the same way `gleaning_extractor.py` validates `Neo4jGraph.model_validate(result)` (lines 179-191), degrading to a safe default (e.g. `INSUFFICIENT`) on parse failure, never crashing the case.

**Reference-closure exception handling (2nd LLM call):** reuse the same prompt-assembly + degrade-on-failure shape as the judgment call itself; for the `REFERS_TO` graph traversal half, reuse `clause_linker.py`'s static-parameterized-Cypher `MATCH ... -[:REFERS_TO]-> ...` traversal pattern (never string-interpolate a clause id into Cypher).

---

### New `--mode graph-compliance` — the multi-allowlist wiring (D-16)

**This is a cross-cutting shared pattern, not a single-file analog** — the exact same 5 locations were touched for `graphrag-ontology` in Phase 10 and MUST be touched identically for the new mode name (NOT `graphrag-*`, per D-16):

1. **`src/domain/value_objects/run_id.py`** lines 24-31:
```python
_VALID_MODES = {
    "hybrid", "llm-only", "rag-only", "graphrag", "graphrag-retrieval",
    "graphrag-ontology",  # Phase 10 (D-16 additivity) — ontology-grounded graph retrieval
}
```
Add the new mode name to this set with the same one-line comment convention (`# Phase 11 (D-16) — ...`).

2. **`src/presentation/cli/commands/evaluate.py`** line 30:
```python
VALID_EVAL_MODES = ["hybrid", "llm-only", "graphrag", "graphrag-ontology"]
```
Append the new mode; also extend the `--mode` help string (lines 58-63) and re-check the "no retrieval-only mode on evaluate" comment still applies or needs its own carve-out.

3. **`src/application/use_cases/evaluate_model.py`** lines 32-40:
```python
# MAINTENANCE: keep in sync with the retrieval members of
# presentation.cli.commands.evaluate.VALID_EVAL_MODES — Phase 10 adds
# "graphrag-ontology". (This mirrors the run_id._VALID_MODES lesson: a new
# retrieval mode added in one place but missed here silently N/As its
# retrieval metrics in the summary/report.)
_RETRIEVAL_EVAL_MODES = {"hybrid", "graphrag", "graphrag-ontology"}
```
Add the new mode; this set gates whether RAG-only quality groups (Retrieval Quality, Model-RAG Grounding) apply (used at lines 632, 710) — missing this silently N/As the new mode's retrieval metrics, exactly the bug this comment warns about.

4. **`src/rag/presentation/cli/query.py`** lines 38-41, 117-119, 144: same 3-place pattern (choice list, help-text dispatch dict, elif branch) as `graphrag-ontology`'s additions — add the 4th mode alongside.

5. **`src/infrastructure/config/container.py`** lines 282-345 — sibling-singleton pattern to copy verbatim:
```python
@staticmethod
def _create_ontology_graph_retrieval_provider(settings, logger):
    if getattr(settings, "neo4j_uri", None) and getattr(settings, "graphrag_ontology_enabled", True):
        from rag.graph.retrieval.neo4j_ontology_graph_retrieval_adapter import Neo4jOntologyGraphRetrievalAdapter
        logger.info("Initialized Neo4jOntologyGraphRetrievalAdapter (mode=graphrag-ontology)")
        return Neo4jOntologyGraphRetrievalAdapter(settings=settings, logger_=logger)
    else:
        logger.warning("No ontology graph retrieval provider configured (...)")
        return None

graph_retrieval_provider_ontology = providers.Singleton(
    _create_ontology_graph_retrieval_provider, settings=config, logger=logger,
)
```
Add a THIRD sibling singleton (`graph_retrieval_provider_compliance` or similar) — D-16 additivity means this is a new `_create_*` staticmethod + a new `providers.Singleton(...)` line, never a modification of the existing two.

**Graph-wiring analogs (also part of the multi-location lesson):**
- `src/rag/retrieval/edges/routing.py` `route_by_mode` (lines 14-62) — add a new `if mode == "graph-compliance": return "<new_route_key>"` branch, following the `graphrag-ontology` branch's comment style (explains WHY the route key differs from the mode name when an intermediate node must run first, lines 42-59).
- `src/rag/retrieval/graph.py` `build_rag_graph` (lines 76-141) — add new node(s) + wire into `add_conditional_edges("query_analysis", route_by_mode, {...})` map, following the `"graph_retrieval_ontology": "function_type_routing"` precedent (line 106) for "route key targets a prerequisite node, not the terminal node directly."
- `src/rag/graph/retrieval/graph_retrieval_node.py` `graph_retrieve_documents` (lines 36-137) — extend the `is_ontology_mode` branch pattern (lines 67-72, 86-97) with a third `is_compliance_mode` branch selecting `container.graph_retrieval_provider_compliance()`.
- `src/rag/graph/cli/graph.py` — add `graph build-compliance` command mirroring `build` / `build-ontology`'s `_run_build`-shaped async orchestration (drop flag, corpus load, builder construction, stats table).

---

### Verbose-io reasoning trace (D-17) + data-model propagation (D-21)

**Analog:** `src/rag/retrieval/state/graph_state.py` (state contract) + `src/rag/retrieval/nodes/generation.py` (population) + `src/rag/application/ports/i_rag_pipeline.py` (`RagResponse` DTO) + `src/rag/infrastructure/adapters/langgraph_rag_adapter.py` (`GraphState -> RagResponse` mapping).

**State-field-reservation precedent** (`graph_state.py` lines 39-43):
```python
# Ontology-grounded retrieval (Phase 10, D-12): inferred function-type tag
# used to boost retrieval scoring in the ontology-grounded graph provider.
# Populated by function-type classification landing in plan 10-09; this
# plan (10-02) only reserves the field on the state contract.
function_type: str
```
Reserve new `GraphState` fields the same way for D-17's trace: `context_graph_triples`, `anchors`, `hypernym_mappings`, `cu_plan` (matched CUs by type with scores), `verbatim_clause_texts` — each with a short docstring-comment naming which later task populates it.

**Propagation chain to verify/extend (D-21's "known-unwired" bug):** `langgraph_rag_adapter.py` maps `final_state["latency_ms"]`/etc into `RagResponse(...)` (lines 69-94) which then flows into `EvaluationResultDTO` via `evaluate_model.py` (`tokens_used=result.model_response.tokens_used`, lines 1040-1041; `prompt_tokens=result.model_response.prompt_tokens`, lines 1059-1061). This full chain already works correctly for `hybrid`/`graphrag`/`graphrag-ontology` (confirmed live — NOT actually hardcoded to 0 in the current `generate_response` path; only `rag_response.py`'s intentionally-no-LLM retrieval-only path hardcodes zeros, lines 44-50). **Verify at plan time** whether the D-21 bug still reproduces on the CURRENT codebase or was already fixed by a prior plan — either way, the new Compliance-Gate judgment node MUST follow `generate_response`'s capture pattern (see above), and the new trace fields need the SAME `RagResponse` DTO extension (`i_rag_pipeline.py` lines 14-66) plus `EvaluationResultDTO` extension (`evaluation_result_dto.py` lines 30-70) to reach the CLI's `--verbose-io` printer.

---

### Eval gates (clause-hit@3 reuse, D-15/D-22)

**Analog:** `src/application/use_cases/clause_hit_harness.py` (whole file)

**Deterministic per-case harness pattern** (lines 45-100+): `FIXED_18_TEST_IDS` tuple (the `bdc4927d` fixture), `CaseClauseHitResult`/`ClauseHitHarnessResult` dataclasses, gold-set union-with-disagreement-flagging (`gold_disagreement`, lines 76-97). Reuse this harness directly for the new mode — parameterize its retrieval-provider injection to accept the new Compliance-Gate provider instead of writing a parallel harness. D-22's gold-validation guard should extend this harness's existing disagreement-detection mechanism (`disagreement_test_ids` property, lines 94-97) rather than building a separate validator.

## Shared Patterns

### Settings-gated LLM call with graceful degradation
**Source:** `src/rag/retrieval/nodes/query_analysis.py` (`_generate_hyde`) and `src/rag/retrieval/nodes/function_type_routing.py` (`_classify_function_type`)
**Apply to:** every new per-query LLM call (Context Graph extraction, hypernym mapping, CU listwise judgment, exception-closure check) and every offline classification/extraction call (Stage 1 premise/CU classifier, Stage 2 4-tuple extractor, Stage 3 implicit-reference linker).
```python
if not settings.openrouter_api_key:
    logger.warning("... not set; skipping")
    return <safe_default>
try:
    ...
except Exception as e:
    logger.warning(f"... failed: {e}")
    return <safe_default>
```

### Static, parameterized Cypher (T-09-12 discipline)
**Source:** `src/rag/graph/ontology/clause_linker.py`, `src/rag/graph/ontology/clause_seeder.py`, `src/rag/graph/ontology/shacl_validator.py`, `src/rag/graph/retrieval/neo4j_ontology_graph_retrieval_adapter.py`
**Apply to:** every new Cypher query (CU seeding, REFERS_TO linking, anchor->CU retrieval, exception-closure traversal). Every query is a module-level string; every variable input is bound via `session.run(query, **params)` / `HybridCypherRetriever.search(query_params=...)` — never f-string/`.format()`-spliced into the query body.

### Idempotent index/constraint bootstrap (swallow "already exists", raise everything else)
**Source:** `src/rag/graph/build/ontology_kg_builder.py` `_ensure_vector_index`/`_ensure_fulltext_index`; `src/rag/graph/ontology/clause_seeder.py` `_ensure_constraint`
**Apply to:** any new Neo4j index/constraint the Policy Graph or Compliance Gate needs (e.g. a CU vector index, a `(cu_id, source_doc)` uniqueness constraint).
```python
try:
    create_vector_index(...)
except Exception as e:
    if "already exists" in str(e).lower():
        logger.info("... already exists — skipping creation.")
    else:
        raise
```

### Authoritative stats re-query (never trust in-process counters)
**Source:** `src/rag/graph/build/ontology_kg_builder.py` `_accumulate_graph_stats`; `src/rag/graph/ontology/clause_seeder.py` `_accumulate_stats`; `src/rag/graph/ontology/clause_linker.py` `_accumulate_stats`
**Apply to:** every new `*Stats`/`*Result` dataclass (Policy Graph build stats, CU seeding stats, REFERS_TO linking stats) — query Neo4j directly for post-write counts inside a `try/except` that logs-and-continues on query failure (never fails the whole build over a stats query).

### Multi-allowlist mode wiring (D-16 lesson, hard constraint)
**Source:** `src/domain/value_objects/run_id.py`, `src/presentation/cli/commands/evaluate.py`, `src/application/use_cases/evaluate_model.py`, `src/rag/presentation/cli/query.py`, `src/infrastructure/config/container.py`, `src/rag/retrieval/edges/routing.py`, `src/rag/retrieval/graph.py`, `src/rag/graph/retrieval/graph_retrieval_node.py`
**Apply to:** the new `--mode graph-compliance` (D-16) — ALL 8 locations above must be touched additively (new branch/entry), never by modifying an existing mode's branch. The planner should encode "grep for every one of these 8 locations, confirm each was touched" as an explicit acceptance criterion, not just "add the new mode" — this is the exact regression class D-16/D-19/D-20 memory notes warn about (a mode/value added to one allowlist but not a sibling one).

### Boundary-aware clause-id text matching (don't-hand-roll)
**Source:** `src/rag/graph/inspect/metrics.py` `KGInspector._clause_id_appears` (static method, reused by `clause_linker.py` and eligible for reuse a third time)
**Apply to:** REFERS_TO regex-explicit-reference detection (Stage 3), and the Wave-0 completeness gate's "does this clause_id's verbatim text exist" check — always this same lookbehind/lookahead-bounded regex, never a naive `in` substring check (which would let `"5.3"` match inside `"5.3.10"`).

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Hypernym mapping scorer (eqs. 1-2: max-pool + top-N=5, STRONG/WEAK + β=0.3 bonus) | domain service (scoring) | transform | No existing codebase component does confidence-weighted max-pool aggregation over premise fragments; closest conceptual analog is `reranking.py`'s RRF combine (different formula, same "combine multiple scored signals" shape) — build fresh, following `domain/services/*_scoring_service.py` naming/placement convention (see `ClauseHitScoringService` for the module-placement precedent) |
| Meta-CU applicability gating (evaluated first, gates before actor-CU judgment) | domain service (business rule) | transform | No existing gating/precedence logic in the retrieval or judgment path; this is new domain logic — place under `domain/services/` per the project's existing `ScoringService`/`ClauseHitScoringService` convention, not inside a LangGraph node (keep business rule out of infrastructure) |
| Violation-first aggregation (final verdict combining per-CU judgments) | domain service | transform | Same as above — new pure-domain logic, no existing analog; write as a standalone testable function/class, called from the judgment node, not embedded in it |

## Metadata

**Analog search scope:** `src/rag/ingestion/`, `src/rag/graph/build/`, `src/rag/graph/ontology/`, `src/rag/graph/retrieval/`, `src/rag/graph/cli/`, `src/rag/retrieval/nodes/`, `src/rag/retrieval/edges/`, `src/rag/retrieval/state/`, `src/rag/application/ports/`, `src/rag/infrastructure/adapters/`, `src/rag/presentation/cli/`, `src/application/use_cases/`, `src/application/dtos/`, `src/domain/value_objects/`, `src/presentation/cli/commands/`, `src/infrastructure/config/`
**Files scanned:** ~40 read/grepped, 22 read in full or targeted excerpt
**Pattern extraction date:** 2026-07-04
