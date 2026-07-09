# Phase 10: Ontology-grounded GraphRAG (Neo4j, governed KG) - Pattern Map

**Mapped:** 2026-07-02
**Files analyzed:** 24 (new + modified)
**Analogs found:** 19 exact/role-match / 24 total (5 genuinely novel — see "No Analog Found")

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/rag/graph/build/ontology_kg_builder.py` (NEW) | service (KG builder) | batch / event-driven (async pipeline run) | `src/rag/graph/build/kg_builder.py` (`EmergentKGBuilder`) | exact |
| `src/rag/graph/build/gleaning_extractor.py` (NEW) | service (extractor subclass) | transform (LLM extraction, multi-pass) | `neo4j_graphrag.experimental.components.entity_relation_extractor.LLMEntityRelationExtractor` (library, not project code) + `kg_builder.py`'s factory-injection style | role-match (library subclass point, project injection style borrowed) |
| `src/rag/graph/build/section_aligned_splitter.py` (NEW) | utility (text splitter component) | transform | `src/rag/ingestion/chunkers/clause_aware_chunker.py` (`CLAUSE_PATTERN`, `_extract_section`) | role-match |
| `src/rag/graph/ontology/schema.py` or `ontology_config.py` (NEW) | config | transform (load committed ontology draft) | `src/rag/ingestion/fixtures/clause_inventory.json` (committed JSON config fixture) + `infrastructure/config/settings.py` (typed config loading) | role-match |
| `src/rag/graph/ontology/shapes.ttl` (NEW) | config (SHACL shapes, Turtle) | — | none in this codebase (new file format) | no analog |
| `src/rag/graph/ontology/shacl_validator.py` (NEW) | service (validation) | transform (LPG→RDF export + validate) | `src/rag/graph/inspect/metrics.py` (`KGInspector`, Neo4j session query pattern) | partial match |
| `src/rag/graph/ontology/clause_seeder.py` (NEW) | infrastructure (Cypher MERGE seeding) | batch / CRUD (idempotent write) | `src/rag/ingestion/scripts/build_clause_inventory.py` (script CLI shape) + `clause_aware_chunker.py::_build_parent_path` (hierarchy derivation) + `kg_builder.py::_ensure_vector_index` (idempotent Neo4j write pattern) | role-match |
| `src/rag/graph/ontology/gold_relation_parser.py` (NEW) | utility (xlsx/regex parser) | transform / batch | `src/rag/ingestion/scripts/audit_ground_truth_citations.py` (openpyxl read + regex extraction + report script) | exact |
| `src/rag/graph/ontology/discovery/method_c_synthesis.py` (NEW) | service (one-shot curation script) | batch (LLM synthesis calls) | `src/rag/ingestion/scripts/audit_ground_truth_citations.py` (script CLI structure) + `src/rag/retrieval/nodes/query_analysis.py::_generate_hyde` (OpenRouter LLM call pattern) | role-match |
| `src/rag/graph/ontology/discovery/method_b_clustering.py` (NEW) | service (clustering script) | batch | same as Method C above; clustering itself has no project analog (new `sklearn` dependency) | role-match (script shape only) |
| `src/rag/graph/retrieval/neo4j_ontology_graph_retrieval_adapter.py` (NEW) | infrastructure (retrieval adapter) | request-response | `src/rag/graph/retrieval/neo4j_graph_retrieval_adapter.py` (`Neo4jGraphRetrievalAdapter`) | exact |
| `src/rag/graph/ports/i_graph_retrieval_provider.py` (UNCHANGED — reused) | port/interface | — | itself (no modification needed; both adapters implement it) | exact |
| `src/rag/retrieval/nodes/function_type_routing.py` (NEW, or extend `query_analysis.py`) | provider/hook (LangGraph node) | request-response (LLM classification) | `src/rag/retrieval/nodes/query_analysis.py` (`analyze_query`, `_generate_hyde`) | exact |
| `src/rag/retrieval/edges/routing.py` (MODIFIED) | route/controller | event-driven (conditional edge) | itself (`route_by_mode`, `decide_after_grading`) | exact |
| `src/rag/graph/retrieval/graph_retrieval_node.py` (MODIFIED or new sibling `graph_retrieval_ontology_node.py`) | provider/hook (LangGraph node) | request-response | `src/rag/graph/retrieval/graph_retrieval_node.py` (`graph_retrieve_documents`) | exact |
| `src/infrastructure/config/container.py` (MODIFIED — `_create_graph_retrieval_provider`) | config/DI wiring | request-response (mode-aware selection) | itself, plus `_create_vector_store_adapter` (if/elif provider-selection precedent already in same file) | exact |
| `src/infrastructure/config/settings.py` (MODIFIED — new ontology/SHACL/mode settings) | config | — | itself ("Neo4j GraphRAG Configuration" block, lines 410-473) | exact |
| `src/domain/value_objects/run_id.py` (MODIFIED — `_VALID_MODES`) | model/value object | — | itself | exact |
| `src/application/use_cases/evaluate_model.py` (MODIFIED — `_RETRIEVAL_EVAL_MODES`) | service (use case) | — | itself (already forward-patched, verify only) | exact |
| `src/presentation/cli/commands/evaluate.py` (MODIFIED — `VALID_EVAL_MODES`) | controller (CLI command) | — | itself | exact |
| `src/rag/presentation/cli/query.py` (MODIFIED — `VALID_MODES`, spinner_label, error help) | controller (CLI command) | — | itself | exact |
| `src/rag/graph/cli/graph.py` (MODIFIED — add `build-ontology`/`validate` subcommands) | controller (CLI command) | batch | itself (`build_command`, `graph_app` Typer structure) | exact |
| `src/domain/services/clause_hit_scoring_service.py` (NEW — D-15 harness) | service (domain scoring) | transform (pure function scoring) | `src/domain/services/scoring_service.py` (`ScoringService`, stateless static-method pattern) | exact |
| `src/rag/graph/inspect/metrics.py` (MODIFIED — extend `KGInspector` or add ontology-aware coverage check) | service (metrics) | transform | itself (`clause_coverage`, `_clause_id_appears`) | exact |
| `tests/rag/graph/ontology/*.py` (NEW test dir) | test | — | `tests/rag/graph/test_kg_builder.py`, `tests/rag/graph/retrieval/test_graph_retrieval_adapter.py`, `tests/rag/graph/retrieval/test_graph_retrieval_adapter_integration.py`, `tests/rag/graph/retrieval/test_graphrag_routing.py` | exact |
| `tests/infrastructure/config/test_graph_provider_selection.py` (NEW) | test | — | existing container tests (mock settings, assert branch selection) — see `_create_vector_store_adapter`/`_create_indexer_adapter` branching pattern for the shape to test | role-match |

## Pattern Assignments

### `src/rag/graph/build/ontology_kg_builder.py` (service, batch)

**Analog:** `src/rag/graph/build/kg_builder.py` (`EmergentKGBuilder`)

**Imports pattern** (lines 21-33):
```python
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Optional

import neo4j
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index
from neo4j_graphrag.llm import LLMInterface, OpenAILLM

from infrastructure.config.settings import Settings
```
Reuse identically — Phase 10 adds `schema=` to the `SimpleKGPipeline` construction and swaps in the custom `text_splitter=`/gleaning-wrapped extractor (see RESEARCH.md Q1/Q2), but the LLM/embedder/index bootstrap is otherwise unchanged.

**Injectable-factory pattern** (lines 37-77) — MUST copy exactly, this is the seam unit tests mock against:
```python
LLMFactory = Callable[[Settings], LLMInterface]
EmbedderFactory = Callable[[Settings], Embedder]
PipelineFactory = Callable[[LLMInterface, "neo4j.Driver", Embedder], SimpleKGPipeline]

def _default_llm_factory(settings: Settings) -> LLMInterface:
    return OpenAILLM(
        model_name=settings.graph_extraction_model,   # held constant, D-06a
        model_params={"temperature": 0},
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
    )

def _default_embedder_factory(settings: Settings) -> Embedder:
    return SentenceTransformerEmbeddings(model=settings.graph_embedding_model)  # D-07 held constant

def _default_pipeline_factory(llm, driver, embedder) -> SimpleKGPipeline:
    return SimpleKGPipeline(llm=llm, driver=driver, embedder=embedder, from_pdf=False)
    # Phase 10: ADD schema=..., text_splitter=SectionAlignedSplitter() here (RESEARCH.md Q1/Q3)
```

**Idempotent index creation pattern** (lines 109-148) — reuse verbatim for any new index Phase 10 needs:
```python
try:
    create_vector_index(self.driver, self.settings.graph_vector_index_name, label="Chunk", ...)
except Exception as e:
    if "already exists" in str(e).lower():
        logger.info(...)
    else:
        raise
```

**Build-loop + provenance-preservation pattern** (lines 150-181) — the `file_path=doc_name` fix (bugs.md 2026-07-02 provenance-collapse bug) MUST be preserved verbatim in the ontology builder:
```python
await self.pipeline.run_async(text=text, file_path=doc_name)
```

**Error handling** (`BuildStats`, lines 42-50, 164-181): failures recorded in `stats.failures`, never swallowed (T-09-08) — copy this dataclass + try/except-per-document loop shape unchanged.

**Divergence point (Phase 10-specific):** pass `schema={...}` (node_types/relationship_types/patterns/`additional_node_types=False`) into `_default_pipeline_factory`, and use a custom `prompt_template=` on the extractor to enforce canonical-name + ignore-illustrative-passages rules (RESEARCH.md Q1). This is the ONE meaningful code delta from the analog — everything else (LLM/embedder factories, index bootstrap, build loop, stats) copies unchanged.

---

### `src/rag/graph/build/gleaning_extractor.py` (service, transform)

**Analog:** no project analog (new pattern) — subclass point confirmed against installed `neo4j_graphrag.experimental.components.entity_relation_extractor.LLMEntityRelationExtractor.extract_for_chunk`. Borrow the **factory-injection discipline** from `kg_builder.py` (constructor takes `max_gleanings: int` as an explicit, testable parameter, mirroring how `EmergentKGBuilder.__init__` takes factories) so unit tests can script a fixed 2-call LLM sequence without a live model (per RESEARCH.md's test map, `test_gleaning_extractor.py` is a mocked unit test).

**Core pattern** (from RESEARCH.md Q2, verified against installed source):
```python
class GleaningEntityRelationExtractor(LLMEntityRelationExtractor):
    def __init__(self, *args, max_gleanings: int = 1, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_gleanings = max_gleanings

    async def extract_for_chunk(self, schema, examples, chunk):
        graph = await super().extract_for_chunk(schema, examples, chunk)
        for _ in range(self.max_gleanings):
            # ... follow-up "what was missed" prompt, extend graph.nodes/relationships
            ...
        return graph
```
**Error handling to mirror:** reuse the base class's own JSON-repair/`OnError` handling (`fix_invalid_json`, `Neo4jGraph.model_validate`) rather than hand-rolling new JSON parsing — Don't-Hand-Roll table in RESEARCH.md.

---

### `src/rag/graph/build/section_aligned_splitter.py` (utility, transform)

**Analog:** `src/rag/ingestion/chunkers/clause_aware_chunker.py`

**Boundary-regex pattern to adapt** (lines 42-74, `CLAUSE_PATTERN`) and **hierarchy derivation** (lines 278-322, `_extract_section` / `_build_parent_path`):
```python
def _extract_section(clause_number: str) -> str:
    if "." in clause_number:
        return clause_number.rsplit(".", 1)[0]
    return clause_number

def _build_parent_path(clause_number: str) -> str:
    parts = clause_number.split(".")
    if len(parts) == 1:
        return f"Chapter {parts[0]}"
    elif len(parts) == 2:
        return f"Chapter {parts[0]} > Section {clause_number}"
    else:
        section = ".".join(parts[:2])
        return f"Chapter {parts[0]} > Section {section} > {clause_number}"
```
**Divergence (Phase 10):** DO NOT reuse `chunk_by_clauses` output directly (produces clause-granularity chunks — the extraction-starving anti-pattern D-05/D-20 forbid). Instead write a coarser splitter that groups multiple clauses under one **top-level** section boundary (e.g. split only at `5.3`, not `5.3.1(a)`), reusing the SAME regex boundary-detection logic but merging sub-clauses into one chunk. Implements neo4j-graphrag's `text_splitter=` custom `Component` contract (confirmed via Context7 "Customize Text Splitter" example) — not a project-code contract, so there's no exact base-class analog in this codebase; treat `clause_aware_chunker.py` as the regex/hierarchy source, not the chunking-granularity target.

---

### `src/rag/graph/ontology/clause_seeder.py` (infrastructure, batch/CRUD)

**Analogs (three, combined):**
1. `src/rag/ingestion/scripts/build_clause_inventory.py` — CLI script shape (argparse, `if __name__ == "__main__"`, logging setup, default output path co-located with fixtures).
2. `src/rag/ingestion/chunkers/clause_aware_chunker.py::_build_parent_path` (lines 298-322, shown above) — reuse for parent-child edge derivation from `clause_id` string structure (D-10).
3. `src/rag/graph/inspect/metrics.py::KGInspector._clause_id_appears` (lines 183-193) — boundary-aware clause-ID matching, reusable for the post-hoc entity→clause linking pass (RESEARCH.md Q4, recommended strategy):
```python
@staticmethod
def _clause_id_appears(clause_id: str, haystack_lower: str) -> bool:
    pattern = re.compile(
        r"(?<![A-Za-z0-9])" + re.escape(clause_id.lower()) + r"(?![A-Za-z0-9])"
    )
    return bool(pattern.search(haystack_lower))
```

**Cypher MERGE pattern** (idempotent, from RESEARCH.md Q4, style matches `kg_builder.py`'s direct `session.run(...)` calls in `_accumulate_graph_stats`, lines 191-199):
```python
with self.driver.session(database=self.settings.neo4j_database) as session:
    session.run(
        "UNWIND $entries AS entry "
        "MERGE (c:Clause {clause_id: entry.clause_id, source_doc: entry.source_doc})",
        entries=entries,
    )
```
**Data source:** `src/rag/ingestion/fixtures/clause_inventory.json` — flat `{"clause_id": ..., "source_doc": ...}` list, 691 entries, NO titles (verify against `generated_at`/`source_docs`/`entries` top-level shape at file lines 1-15).

**Error handling:** static, parameterized Cypher only (never string-interpolated) — T-09-12 discipline, identical to `neo4j_graph_retrieval_adapter.py`'s `RETRIEVAL_QUERY` precedent (see Shared Patterns below).

---

### `src/rag/graph/ontology/gold_relation_parser.py` (utility, transform/batch)

**Analog:** `src/rag/ingestion/scripts/audit_ground_truth_citations.py`

**Docstring/report-script shape to copy** (lines 1-40): READ-ONLY input, produces a machine-readable diff/report artifact for human review — mirror this framing exactly for D-17's coverage-gap report (human curation gate, D-14).

**Regex extraction pattern** (from RESEARCH.md Q10, confirmed against live xlsx cell content this session):
```python
import re
TRIPLE_RE = re.compile(r"\(([^)]+)\)\s*-\[([^\]]+)\]->\s*\(([^)]+)\)")
CLAUSE_BRACKET_RE = re.compile(r"\[([\w.\s,()§]+)\]")  # e.g. "[1.2.1, 1.4.1]"

for cell in graph_relation_column:
    triples = TRIPLE_RE.findall(cell)
    relation_types = {re.sub(r"\s+", "_", rel.strip()) for _, rel, _ in triples}
    clause_citations = CLAUSE_BRACKET_RE.findall(cell)
```
**Input:** `src/results/evaluations/eval-report-hybrid-suite-20260630-0907.xlsx`, sheet `eval-18`, column 22 `graph_relation` — read via `openpyxl` (already a project dependency, used elsewhere for report generation per RESEARCH.md Standard Stack table).
**Normalization pitfall confirmed live:** cell text uses `NOT DESIGNATED_AS` (space) not `NOT_DESIGNATED_AS` (underscore) — the parser MUST normalize whitespace→underscore before diffing against the ontology's locked relation-type vocabulary.

---

### `src/rag/graph/ontology/discovery/method_c_synthesis.py` and `method_b_clustering.py` (service, batch)

**Analog for script shape:** `src/rag/ingestion/scripts/audit_ground_truth_citations.py` / `build_clause_inventory.py` (argparse CLI, one-shot curation-time artifact, NOT a runtime service — confirmed by RESEARCH.md's Architectural Responsibility Map: "Application (offline script/CLI)").

**Analog for the LLM call itself:** `src/rag/retrieval/nodes/query_analysis.py::_generate_hyde` (lines 27-48) — the established pattern for a lightweight OpenRouter `gpt-4o-mini` call in this codebase:
```python
from openai import OpenAI
client = OpenAI(
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url,
    timeout=60,
)
resp = client.chat.completions.create(
    model=settings.rag_hyde_model,   # Phase 10: a new settings field, e.g. ontology_discovery_model
    messages=[{"role": "user", "content": PROMPT.format(...)}],
    temperature=0.2,
    max_tokens=200,
)
return (resp.choices[0].message.content or "").strip()
```
**Error handling:** the try/except-log-and-return-empty pattern in `_generate_hyde` (lines 46-48) is the project convention for "LLM call may fail, degrade gracefully, log a warning" — reuse for both Method C and Method B LLM calls.

**Divergence:** Method B's `sklearn.cluster.AffinityPropagation` step has no project analog (new dependency, `poetry add scikit-learn`) — pure new code, not a pattern-copy target.

---

### `src/rag/graph/ontology/shacl_validator.py` (service, transform)

**Analog:** `src/rag/graph/inspect/metrics.py` (`KGInspector`) — for the Neo4j session-query style (`self._session()` context manager, direct Cypher `session.run(...)`, aggregation into a plain dict return value):
```python
def clause_coverage(self, inventory_path=DEFAULT_CLAUSE_INVENTORY_PATH) -> dict[str, Any]:
    entries = json.loads(Path(inventory_path).read_text())["entries"]
    ...
    with self._session() as session:
        result = session.run("MATCH (c:Chunk) RETURN c.text AS text")
        ...
    return {"covered": covered, "total": total, "coverage_ratio": ...}
```
Use this exact "query Neo4j → aggregate → return typed dict" shape for the LPG→RDF export step (`MATCH (n) RETURN elementId(n), labels(n), properties(n)`) before handing the resulting `rdflib.Graph` to `pyshacl.validate()`.

**pyshacl API (external library, verified in RESEARCH.md Q5):**
```python
from pyshacl import validate
conforms, results_graph, results_text = validate(
    data_graph, shacl_graph=shacl_graph, inference="none", abort_on_error=False,
)
```
**Reject + log (D-13):** do NOT delete non-conforming facts — quarantine (write `validation_report.json` or a `:ValidationFailure` label), mirroring `BuildStats.failures` in `kg_builder.py` ("failures reported, never silently swallowed", T-09-08) as the project's general convention for degrade-with-visibility.

---

### `src/rag/graph/retrieval/neo4j_ontology_graph_retrieval_adapter.py` (infrastructure, request-response)

**Analog:** `src/rag/graph/retrieval/neo4j_graph_retrieval_adapter.py` (`Neo4jGraphRetrievalAdapter`) — THIS IS AN EXACT STRUCTURAL MATCH; implement the identical `IGraphRetrievalProvider` port.

**Imports pattern** (lines 27-38):
```python
import logging
from typing import Optional

import neo4j
from langchain_core.documents import Document
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.retrievers import HybridCypherRetriever
from neo4j_graphrag.types import RetrieverResultItem

from infrastructure.config.settings import Settings
from rag.graph.ports.i_graph_retrieval_provider import IGraphRetrievalProvider
```

**Static parameterized Cypher pattern (T-09-12, MUST preserve)** (lines 55-72) — a class-level string constant, `node`/`score` bound by neo4j-graphrag itself, never string-interpolated:
```python
RETRIEVAL_QUERY = """
WITH node AS chunk, score
OPTIONAL MATCH (chunk)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (entity)-[:FROM_CHUNK]->(chunk)
WITH chunk, score, doc, collect(DISTINCT labels(entity)) AS neighbor_label_lists
RETURN
    chunk.text AS original_text,
    elementId(chunk) AS citation_id,
    coalesce(doc.path, 'unknown') AS document_source,
    score AS score,
    neighbor_label_lists AS neighbor_label_lists
ORDER BY score DESC
""".strip()
```
**Phase 10 divergence:** rewrite this query to retrieve at CLAUSE-NODE granularity (not raw Chunk text) and add the function-type boost (RESEARCH.md Q7):
```cypher
WITH node AS chunk, score
OPTIONAL MATCH (chunk)-[:LINKED_TO]->(c:Clause)
WITH chunk, score, c,
     CASE WHEN c.function_type = $function_type THEN score * 1.5 ELSE score END AS boosted_score
RETURN chunk.text AS original_text, ..., boosted_score AS score
ORDER BY boosted_score DESC, chunk.clause_id ASC   -- stable tie-break, D-15
```
Note the added deterministic secondary sort key (`chunk.clause_id ASC`) — REQUIRED for the D-15 clause-hit@3 harness (RESEARCH.md Q8/Pitfall 2); the Phase 9 analog does not need this because it has no determinism acceptance gate.

**Constructor pattern** (lines 76-101) — copy the `Optional[...]` injectable-dependency shape (driver/embedder/retriever all overridable for unit testing) verbatim.

**`_format_record` pattern** (lines 103-131) — same shape, but Phase 10's metadata MUST populate `section`/`citation_id` with the REAL seeded clause_id (not `elementId(chunk)` as Phase 9's honesty-note explains at lines 19-24) — this is the concrete fix for the "Honesty note" limitation documented in the Phase 9 analog's own docstring.

**`retrieve()` method** (lines 133-151): identical signature/shape; no changes needed beyond what the rewritten `RETRIEVAL_QUERY` requires (e.g. passing `function_type` as an additional bound Cypher parameter via `HybridCypherRetriever`'s `retrieval_query` mechanism — verify the exact param-passing API at implementation time per RESEARCH.md Q7).

---

### `src/rag/retrieval/nodes/function_type_routing.py` (provider/hook, request-response)

**Analog:** `src/rag/retrieval/nodes/query_analysis.py` (`analyze_query`, `_generate_hyde`)

**Full pattern to mirror** (lines 27-76) — settings-gated LLM call, state field set on the SAME `GraphState` object, never fails the whole request on LLM error:
```python
def _generate_hyde(question: str, settings) -> str:
    if not settings.openrouter_api_key:
        logger.warning(...)
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url, timeout=60)
        resp = client.chat.completions.create(model=..., messages=[...], temperature=0.2, max_tokens=200)
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning(f"HyDE generation failed: {e}")
        return ""

def analyze_query(state: GraphState) -> GraphState:
    settings = get_settings()
    query = state.get("query", "")
    ...
    state["rewritten_query"] = query  # or hyde
    return state
```
**Phase 10 shape:** a sibling node classifying `state["query"]` into `ScopeClause`/`ControlClause`/`DefinitionClause`, storing result in `state["function_type"]` (a NEW `GraphState` field — extend `src/rag/retrieval/state/graph_state.py`'s TypedDict the same way `rewritten_query`/`hyde_query` were added). Gate this node with `mode == "graphrag-ontology"` only (mirrors `analyze_query`'s `settings.rag_hyde_enabled and state.get("mode") in (...)` gating at line 62).

---

### `src/rag/retrieval/edges/routing.py` (route/controller, event-driven) — MODIFIED

**Analog:** itself. Extend `route_by_mode` (lines 14-43) with a new branch:
```python
def route_by_mode(state: GraphState) -> str:
    mode = state.get("mode", "hybrid")
    if mode == "llm-only":
        return "fallback"
    if mode in ("graphrag", "graphrag-retrieval"):
        return "graph_retrieval"
    if mode == "graphrag-ontology":            # Phase 10 addition
        return "graph_retrieval_ontology"       # or route to the SAME node, mode-branching inside it
    return "retrieval"
```
`decide_after_grading` (lines 46-74) likely needs no change (falls through to the existing `retrieval_succeeded` branch) UNLESS a `graphrag-ontology-retrieval` (retrieval-only) variant mirroring `graphrag-retrieval` is added per D-15's harness needs — verify against the harness design before locking.

**Test analog:** `tests/rag/graph/retrieval/test_graphrag_routing.py` (full file read) — direct, dependency-free unit tests against `route_by_mode({"mode": ...})`, plus one integration-style test asserting the compiled `build_rag_graph` LangGraph contains the new node name. Copy this file's structure exactly for `test_graphrag_ontology_routing.py`.

---

### `src/infrastructure/config/container.py` (config/DI wiring) — MODIFIED, Pitfall 3 fix

**Analog:** itself (`_create_graph_retrieval_provider`, lines 258-280) PLUS the existing if/elif multi-provider-selection precedent already in the same file (`_create_vector_store_adapter`, lines 177-215; `_create_indexer_adapter`, lines 218-256).

**Current (Phase 9) single-provider pattern — the wiring gap RESEARCH.md Pitfall 3 flags:**
```python
@staticmethod
def _create_graph_retrieval_provider(settings, logger):
    if getattr(settings, "neo4j_uri", None):
        from rag.graph.retrieval.neo4j_graph_retrieval_adapter import Neo4jGraphRetrievalAdapter
        return Neo4jGraphRetrievalAdapter(settings=settings, logger_=logger)
    else:
        return None

graph_retrieval_provider = providers.Singleton(
    _create_graph_retrieval_provider, settings=config, logger=logger,
)
```
**Recommended fix (RESEARCH.md's explicit recommendation):** register a SECOND singleton (`graph_retrieval_provider_ontology`) alongside the first, following the SAME if/elif-on-settings shape as `_create_vector_store_adapter`'s Qdrant/Databricks branching:
```python
@staticmethod
def _create_ontology_graph_retrieval_provider(settings, logger):
    if getattr(settings, "neo4j_uri", None):
        from rag.graph.retrieval.neo4j_ontology_graph_retrieval_adapter import (
            Neo4jOntologyGraphRetrievalAdapter,
        )
        return Neo4jOntologyGraphRetrievalAdapter(settings=settings, logger_=logger)
    return None

graph_retrieval_provider_ontology = providers.Singleton(
    _create_ontology_graph_retrieval_provider, settings=config, logger=logger,
)
```
Then `graph_retrieve_documents` (or a new `graph_retrieve_documents_ontology` sibling node, see below) selects `container.graph_retrieval_provider()` vs `container.graph_retrieval_provider_ontology()` based on `state["mode"]` — this is the mode-aware routing RESEARCH.md's Pitfall 3 explicitly calls out as "Wave-0/1 wiring work, not a Wave-3 afterthought."

---

### `src/rag/graph/retrieval/graph_retrieval_node.py` (provider/hook, request-response) — MODIFIED or new sibling

**Analog:** itself (`graph_retrieve_documents`, full file read, lines 1-112).

**Pattern to mirror exactly** (provider lookup, error handling, state population):
```python
def graph_retrieve_documents(state: GraphState) -> GraphState:
    settings = get_settings()
    query = state.get("rewritten_query", "") or state.get("query", "")
    top_k = settings.rag_retrieval_top_k
    try:
        container = get_container()
        provider = container.graph_retrieval_provider()   # Phase 10: mode-aware pick
        if provider is None:
            logger.error("No graph retrieval provider configured. Set CCOP_NEO4J_URI ...")
            state["documents"] = []
            state["filtered_documents"] = []
            state["retrieval_succeeded"] = False
            state["retrieval_attempts"] = retrieval_attempts + 1
            state["error"] = "No graph retrieval provider configured"
            return state
        documents = provider.retrieve(query=query, top_k=top_k)
        for rank, doc in enumerate(documents, 1):
            doc.metadata.setdefault("similarity_score", doc.metadata.get("similarity_score", 0.0))
            doc.metadata["dense_rank"] = rank
        state["documents"] = documents
        state["retrieval_succeeded"] = bool(documents)
        state["retrieval_attempts"] = retrieval_attempts + 1
    except Exception as e:
        logger.error(f"Graph retrieval failed: {e}")
        state["documents"] = []
        state["filtered_documents"] = []
        state["retrieval_succeeded"] = False
        state["retrieval_attempts"] = retrieval_attempts + 1
        state["error"] = f"Graph retrieval error: {str(e)}"
    return state
```
**Wave-6 parity note (MUST preserve):** does NOT pre-set `filtered_documents` — the graph path flows through the SAME shared cross-encoder reranker (`src/rag/retrieval/nodes/reranking.py`) as hybrid mode, which owns the final top-N funnel via `dense_rank`/`ce_rank` RRF ensemble (`reranking.py` lines 100-121). Any new Phase 10 node MUST attach `dense_rank` identically so it doesn't bypass the shared reranker.

---

### `src/domain/value_objects/run_id.py` (model/value object) — MODIFIED

**Analog:** itself, line 24:
```python
_VALID_MODES = {"hybrid", "llm-only", "rag-only", "graphrag", "graphrag-retrieval"}
```
**Fix:** add `"graphrag-ontology"` to this set. This is ONE of (at least) four independent allowlists that must all be updated together — see Shared Patterns → "Multi-Allowlist Mode Wiring" below. Confirmed this file does NOT yet include `graphrag-ontology` (checked live).

---

### `src/application/use_cases/evaluate_model.py` (service, use case) — VERIFY ONLY

**Analog:** itself, lines 32-40 — ALREADY includes `"graphrag-ontology"` in `_RETRIEVAL_EVAL_MODES`:
```python
_RETRIEVAL_EVAL_MODES = {"hybrid", "graphrag", "graphrag-ontology"}
```
This was pre-patched during the P3 fix (commit `7658505`) with an explicit forward-looking comment: "Phase 10 adds 'graphrag-ontology'... MAINTENANCE: keep in sync with... run_id._VALID_MODES." **Action for Phase 10: verify this stays correct; the remaining allowlists (below) are NOT yet patched and must be.**

---

### `src/presentation/cli/commands/evaluate.py` (controller, CLI) — MODIFIED

**Analog:** itself, line 30:
```python
VALID_EVAL_MODES = ["hybrid", "llm-only", "graphrag"]
```
**Fix:** add `"graphrag-ontology"`. Confirmed this does NOT yet include it (checked live) — this is allowlist #3 of 4.

---

### `src/rag/presentation/cli/query.py` (controller, CLI) — MODIFIED

**Analog:** itself, line 35:
```python
VALID_MODES = ["hybrid", "llm-only", "rag-only", "graphrag", "graphrag-retrieval"]
```
Confirmed this does NOT yet include `"graphrag-ontology"` — allowlist #4 of 4. Also update:
- `spinner_label` dict (lines 106-112) — add `"graphrag-ontology": "Querying ontology-grounded graph pipeline..."`
- Error-help branch (lines 128-141) — the `elif mode in ("graphrag", "graphrag-retrieval"):` branch (line 136) should extend to include `"graphrag-ontology"` (same Neo4j config help text applies).

---

### `src/domain/services/clause_hit_scoring_service.py` (service, domain scoring) — NEW, D-15 harness

**Analog:** `src/domain/services/scoring_service.py` (`ScoringService`) — stateless, `@staticmethod`-based domain service pattern, no external dependencies:
```python
class ScoringService:
    """
    Domain service for scoring model responses against test cases.
    Stateless service containing domain logic operating on entities.
    """
    @staticmethod
    def score_response(test_case, response, judge_mode="rubric", retrieved_contexts=None) -> List[EvaluationMetric]:
        ...
```
**Phase 10 shape:** a new `ClauseHitScoringService` (or a method added to `ScoringService`) with pure functions computing, per RESEARCH.md Q8:
```python
hit@3 = 1 if gold_set ∩ retrieved_top3_clause_ids else 0
recall@3 = |gold_set ∩ top3| / |gold_set|
recall@pool(50) = |gold_set ∩ top50| / |gold_set|
```
No live-service dependency — pure scoring function, matches RESEARCH.md's Phase Requirements → Test Map row `P10-D15` ("unit — pure scoring function, no external deps"). Gold set comes from GT `metadata.clause_reference` CROSS-CHECKED against the D-17 gold-relation xlsx bracketed citations (Pitfall 4) — do not trust `clause_reference` alone.

---

## Shared Patterns

### Multi-Allowlist Mode Wiring (the P3 lesson — CRITICAL, applies to ALL Phase 10 files touching `--mode`)
**Source:** `docs/project_notes/bugs.md` 2026-07-02 entry + the e2e-testing global rule (`~/.claude/rules/e2e-testing.md`) which cites this EXACT bug as its motivating example.
**Apply to:** every plan/task that adds `--mode graphrag-ontology`.
**The four allowlists, confirmed live in this session (state as of today):**
| Allowlist | File:Line | Currently includes `graphrag-ontology`? |
|---|---|---|
| `_VALID_MODES` | `src/domain/value_objects/run_id.py:24` | NO — must add |
| `_RETRIEVAL_EVAL_MODES` | `src/application/use_cases/evaluate_model.py:40` | YES — already patched |
| `VALID_EVAL_MODES` | `src/presentation/cli/commands/evaluate.py:30` | NO — must add |
| `VALID_MODES` | `src/rag/presentation/cli/query.py:35` | NO — must add |
Also: `route_by_mode`/`decide_after_grading` in `src/rag/retrieval/edges/routing.py` need a new branch (this is routing logic, not an allowlist, but the same "grep for ALL the places" discipline applies). **A grep for `graphrag` across `src/` before considering the mode wiring done is mandatory** — do not trust this table alone at implementation time; re-grep, since new commits may have landed.

### Static Parameterized Cypher (T-09-12, security-critical)
**Source:** `src/rag/graph/retrieval/neo4j_graph_retrieval_adapter.py` lines 55-72 (`RETRIEVAL_QUERY` class-level string constant).
**Apply to:** ALL new Cypher in Phase 10 — `clause_seeder.py`'s MERGE statements, the ontology adapter's boosted `RETRIEVAL_QUERY`, the SHACL LPG→RDF export read queries.
**Rule:** Cypher is always a static, class-level (or module-level) string; user/LLM-derived values are passed ONLY as bound parameters (`session.run(query, entries=entries)` or the retriever's own `query_vector`/fulltext-query parameterization) — NEVER f-string/`.format()`-interpolated into the Cypher body. This is RESEARCH.md's explicit V5 Input Validation control (Cypher injection prevention).

### Idempotent Neo4j Writes ("already exists" swallow, everything else propagates)
**Source:** `src/rag/graph/build/kg_builder.py::_ensure_vector_index` (lines 109-132) and `_ensure_fulltext_index` (lines 134-148, `fail_if_exists=False`).
**Apply to:** `clause_seeder.py` (MERGE is naturally idempotent, but any accompanying index/constraint creation should follow this exact try/except-on-"already exists" shape).

### Failures Reported, Never Swallowed (T-09-08)
**Source:** `src/rag/graph/build/kg_builder.py`'s `BuildStats.failures` list (lines 42-50) + per-document try/except in `build()` (lines 164-181).
**Apply to:** the ontology builder's per-document loop, the SHACL validator's non-conforming-fact quarantine (D-13: "reject + log separately", not silent deletion), and the gleaning extractor's per-pass error handling.

### Shared Cross-Encoder Reranker Funnel (Wave-6 parity — MUST NOT bypass)
**Source:** `src/rag/retrieval/nodes/reranking.py` (`rerank_documents`, full file) — RRF ensemble of `dense_rank` ⊕ `ce_rank` (lines 105-121), `rerank_top_n` funnel (line 265-266).
**Apply to:** any new Phase 10 retrieval node — it MUST populate `documents` (the wide candidate pool, NOT `filtered_documents`) with `dense_rank` attached, exactly as `graph_retrieve_documents` does (lines 74-76), so retrieval flows through the SAME shared reranker rather than a parallel/duplicated ranking path. This directly supports D-15's "same engine, one variable" ablation design.

### Settings/Config Field Pattern
**Source:** `src/infrastructure/config/settings.py` lines 410-473 ("Neo4j GraphRAG Configuration" block) — `Field(default=..., description="...", alias="CCOP_...")` for env-prefixed, documented, typed config.
**Apply to:** any new Phase 10 settings (ontology config path, SHACL shapes path, `ontology_discovery_model`, function-type-routing boost multiplier, gleaning `max_gleanings` default) — follow the SAME `Field(...)` + docstring-comment-block-with-decision-ref style (note how existing fields cite `D-06a`/`D-07` inline).

### DI Container Multi-Provider Selection (if/elif on settings)
**Source:** `src/infrastructure/config/container.py::_create_vector_store_adapter` (lines 177-215) — the established precedent for "branch on which config is present, log which adapter was chosen, return None with a warning if neither."
**Apply to:** the new `_create_ontology_graph_retrieval_provider` static method and, more importantly, whatever mode-aware SELECTION mechanism the planner chooses for routing between `graph_retrieval_provider` (P9) and `graph_retrieval_provider_ontology` (P10) at the LangGraph-node call site.

---

## No Analog Found

Files with no close structural match in the codebase — planner should rely on RESEARCH.md's verified library-API patterns (Context7-sourced) instead of a project-code analog:

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `src/rag/graph/ontology/shapes.ttl` | config | — | First SHACL/Turtle file in the repo; no RDF-format precedent. Author from RESEARCH.md Q5's `sh:NodeShape` example directly. |
| `src/rag/graph/ontology/schema.py` (ontology type/relation definitions) | config | — | First ontology-config artifact. Nearest structural pattern: `clause_inventory.json`'s "committed JSON fixture, versioned in repo" convention, but the CONTENT (node_types/relationship_types/patterns dict matching `neo4j_graphrag.experimental.components.schema.GraphSchema`) is new — copy the dict shape from RESEARCH.md Q1's verified `schema={...}` example, not from any project file. |
| Method B clustering logic (`sklearn.cluster.AffinityPropagation` usage) | transform | — | No clustering code exists anywhere in this codebase; new `scikit-learn` dependency, genuinely novel algorithm usage. |
| `src/rag/graph/ontology/discovery/` module as a whole (Method C/B orchestration) | service | batch | The individual LLM-call and script-CLI parts have analogs (see above), but the overall "two-phase discover→curate→cross-check→reconcile" orchestration flow has no precedent — treat CONTEXT.md D-01/D-04/D-05 and RESEARCH.md Q6 as the spec, not a code analog. |
| Function-type classification PROMPT content (the specific `ScopeClause`/`ControlClause`/`DefinitionClause` taxonomy prompt) | — | — | The MECHANISM (LLM classification call in a LangGraph node) has an exact analog (`query_analysis.py`'s HyDE call); the PROMPT CONTENT is new domain content specific to D-09/D-12 — write from RESEARCH.md Q7's draft prompt, not copied from an existing prompt file. |

## Metadata

**Analog search scope:** `src/rag/graph/`, `src/rag/retrieval/`, `src/rag/ingestion/`, `src/rag/graph/inspect/`, `src/infrastructure/config/`, `src/domain/value_objects/`, `src/domain/services/`, `src/application/use_cases/`, `src/presentation/cli/`, `src/rag/presentation/cli/`, `tests/rag/graph/`
**Files scanned:** ~40 (read in full or targeted-range) across the above directories, plus live inspection of `src/results/evaluations/eval-report-hybrid-suite-20260630-0907.xlsx` and `src/rag/ingestion/fixtures/clause_inventory.json` structure (both already verified in RESEARCH.md; re-confirmed against this session's own reads where noted).
**Pattern extraction date:** 2026-07-02

---

*Phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2*
