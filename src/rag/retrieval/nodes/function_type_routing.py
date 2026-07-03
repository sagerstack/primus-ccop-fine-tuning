"""
Function-Type Routing Node (Phase 10, plan 10-09, D-12)

Classifies a compliance question's PRIMARY intent as exactly one of the three
D-09 clause-function tags (`ScopeClause` / `ControlClause` / `DefinitionClause`,
locked in `ontology_config.json`'s `function_type_tags`) via a lightweight
OpenRouter gpt-4o-mini call, mirroring
`rag/retrieval/nodes/query_analysis.py::_generate_hyde`'s settings-gated LLM
call + graceful-degradation shape exactly.

The classified `function_type` is stored in `state["function_type"]` (the
GraphState field reserved by plan 10-02) and threaded by the mode-aware
`graph_retrieve_documents` node (`rag/graph/retrieval/graph_retrieval_node.py`)
into `Neo4jOntologyGraphRetrievalAdapter.retrieve(..., function_type=...)`,
which passes it as a bound `$function_type` Cypher parameter (T-09-12) to
boost matching clauses (D-12).

Gated on `state.get("mode") == "graphrag-ontology"` — this node is a no-op for
every other mode, never fails the whole request on an LLM error (mirrors
HyDE's try/except-log-return degradation pattern), and defaults to an empty
`function_type` (no boost applied — RETRIEVAL_QUERY's
`CASE WHEN c.function_type = $function_type` simply never matches) on any
classification failure.

Escalation hook (D-12, not implemented here): if function-type routing alone
does not clear the clause-hit@3 gate (D-15, plan 10-10), CONTEXT.md
pre-authorizes escalating to "Both, layered" — adding entity-anchored
traversal (Phase 9's existing `FROM_CHUNK` one-hop expansion) as an
ADDITIONAL signal alongside this function-type boost, not a replacement. That
escalation is intentionally deferred to a future plan.
"""

import logging

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


# D-09 locked function-type tags (src/rag/graph/ontology/ontology_config.json
# "function_type_tags") — the only three valid classification outputs.
VALID_FUNCTION_TYPES = frozenset({"ScopeClause", "ControlClause", "DefinitionClause"})

FUNCTION_TYPE_PROMPT = """Classify this compliance question's PRIMARY intent as exactly one of:
ScopeClause (is X in/out of mandatory scope/applicability?), ControlClause (what must be done/implemented?), DefinitionClause (what does term X mean?).

Question: {q}

Answer with ONLY the label — exactly one of: ScopeClause, ControlClause, DefinitionClause."""


def _classify_function_type(question: str, settings) -> str:
    """
    Call OpenRouter to classify the question's function-type intent (D-12).

    Mirrors `query_analysis.py::_generate_hyde`'s settings-gated call +
    try/except-log-return degradation pattern exactly: returns "" (no boost)
    on any missing-key or LLM-call failure, never raises.
    """
    if not settings.openrouter_api_key:
        logger.warning("Function-type routing enabled but OPENROUTER_API_KEY not set; skipping")
        return ""
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=60,
        )
        resp = client.chat.completions.create(
            model=settings.ontology_discovery_model,
            messages=[{"role": "user", "content": FUNCTION_TYPE_PROMPT.format(q=question)}],
            temperature=0.0,
            max_tokens=10,
        )
        raw = (resp.choices[0].message.content or "").strip()
        # Defensive normalization: strip quotes/punctuation the LLM might add,
        # then validate against the LOCKED D-09 tag set before trusting it as
        # a Cypher-bound value (constrains classifier output to a 3-value enum
        # per T-10-09-01's mitigation, before it ever reaches $function_type).
        normalized = raw.strip("\"'. \n\t")
        if normalized not in VALID_FUNCTION_TYPES:
            logger.warning(
                f"Function-type classification returned an unrecognized label "
                f"({raw!r}); defaulting to no boost (empty function_type)"
            )
            return ""
        return normalized
    except Exception as e:
        logger.warning(f"Function-type classification failed: {e}")
        return ""


def classify_function_type(state: GraphState) -> GraphState:
    """
    Classify question intent into a D-09 function-type tag (D-12).

    Gated on `mode == "graphrag-ontology"` (mirrors `analyze_query`'s
    HyDE mode-gating) — a no-op for every other mode, so `hybrid`/`llm-only`/
    `graphrag` requests are entirely unaffected. Runs BEFORE the ontology
    retrieval node so `state["function_type"]` is set before the boosted
    Cypher query executes (wired in `rag/retrieval/graph.py`).
    """
    settings = get_settings()
    query = state.get("query", "")

    if state.get("mode") != "graphrag-ontology":
        state["function_type"] = state.get("function_type", "")
        return state

    logger.info(f"Classifying function-type intent (model={settings.ontology_discovery_model})")
    function_type = _classify_function_type(query, settings)
    state["function_type"] = function_type
    if function_type:
        logger.debug(f"Function-type: {function_type}")

    return state


__all__: list[str] = [
    "VALID_FUNCTION_TYPES",
    "FUNCTION_TYPE_PROMPT",
    "classify_function_type",
]
