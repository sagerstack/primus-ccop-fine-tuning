"""
Compliance Gate — grounded judgment + answer (GraphCompliance §3.3, eqs. 5-6).
Mode-gated on `graphcpl`.

Assembles the grounding context the model reasons over:
  - PREMISES (definitions/interpretations) — the STRONG-supporting premises the
    hypernym mapping (11-06b) already surfaced per anchor.
  - OBLIGATIONS (the CU Plan actor-CU/meta-CU 4-tuples) from the Gate retrieval.
  - VERBATIM CLAUSE TEXT for both (citation grounding).
  - REFERENCE NEIGHBOURS — the REFERS_TO targets of the CU-Plan CUs (evidence for
    the paper's exception-override, eq. 6).

One listwise LLM judgment call (eq. 5): meta-CU applicability gating FIRST, forbid
inference from silence (ambiguous/out-of-scope → not-applicable/insufficient),
consider reference exceptions, and produce a reasoned answer + verdict + citations.
Writes `state["generation"]`, `state["citations"]`, and token/latency trace.

Mirrors `context_graph_extraction.py`'s LLM-call shape (OpenRouter, temp 0,
fix_invalid_json, degrade-to-empty). Degrade-safe: never raises.
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

_MODE = "graphcpl"

_FETCH_REFS_QUERY = """
UNWIND $cu_ids AS cid
MATCH (s:ComplianceUnit {cu_id: cid})-[:REFERS_TO]->(t:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)
RETURN DISTINCT t.cu_id AS cu_id, t.subject AS subject, t.constraint AS constraint,
       c.citation_id AS citation_id, c.text AS clause_text
""".strip()

JUDGE_PROMPT = """You are a Singapore CCoP 2.0 (Cybersecurity Code of Practice for CII) compliance analyst. Answer the SCENARIO using ONLY the policy content provided below.

SCENARIO:
{question}

CONTEXT GRAPH (entity-relation triples extracted from the scenario):
{triples}

SCENARIO ENTITIES (from the context graph) and how each maps to policy vocabulary:
{anchors}

DEFINITIONS / PREMISES (authoritative meanings — use these to decide what things ARE):
{premises}

OBLIGATIONS retrieved for this scenario (the CU Plan — subject | modality | constraint | conditions | [citation]):
{obligations}

REFERENCED OBLIGATIONS (cross-referenced by the above — may contain exceptions/qualifications):
{references}

INSTRUCTIONS:
- First decide APPLICABILITY (meta/scope rules and definitions): does the code apply to the entity in question? A system is only a CII if it meets the definition (designation under s.7(1) of the Act). Do NOT treat a system as in-scope merely because it shares a network with a CII.
- Judge against the retrieved obligations; consider any exception/qualification in the referenced obligations.
- Forbid inference from silence: if the provided content does not support a conclusion, answer not-applicable or insufficient rather than guessing.
- Ground every claim in a cited [citation_id].

Return ONLY a JSON object:
{{"verdict": "<applicable|not-applicable|compliant|non-compliant|insufficient>", "answer": "<concise reasoned answer citing [citation_id]s>", "citations": ["<citation_id>", ...]}}

JSON:"""


def _fetch_references(settings, cu_ids: List[str]) -> List[Dict[str, Any]]:
    if not cu_ids:
        return []
    import neo4j
    drv = neo4j.GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        with drv.session(database=settings.neo4j_database) as s:
            return [dict(r) for r in s.run(_FETCH_REFS_QUERY, cu_ids=cu_ids)]
    finally:
        drv.close()


def _render_triples(state) -> str:
    lines = []
    for t in state.get("context_graph_triples", []):
        lines.append(f"- ({t.get('subject','')}) --[{t.get('predicate','')}]--> ({t.get('object','')})")
    return "\n".join(lines) or "(none)"


def _render_anchors(state) -> str:
    lines = []
    hm = state.get("hypernym_mappings", [])
    for a in state.get("anchors", []):
        hyps = [f"{m['label']}({m['strong_weak']})" for m in hm if m.get("anchor") == a["label"]]
        lines.append(f"- {a['label']} [{a['type']}] -> {', '.join(hyps) or '(no mapping)'}")
    return "\n".join(lines) or "(none)"


def _render_premises(state) -> str:
    seen, lines = set(), []
    for m in state.get("hypernym_mappings", []):
        prem = (m.get("supporting_premise") or "").strip()
        if prem and prem not in seen:
            seen.add(prem)
            src = m.get("score", "")
            lines.append(f"- [{m.get('label','')}] {prem}")
    return "\n".join(lines) or "(none)"


def _render_obligations(cu_plan) -> str:
    lines = []
    for c in cu_plan:
        lines.append(f"- {c.get('subject','')} | {c.get('modality','')} | {str(c.get('constraint',''))[:180]} | "
                     f"cond={str(c.get('conditions',''))[:80]} | [{c.get('citation_id','')}]")
    return "\n".join(lines) or "(none)"


def _render_references(refs) -> str:
    return "\n".join(f"- {r.get('subject','')} | {str(r.get('constraint',''))[:150]} | [{r.get('citation_id','')}]"
                     for r in refs) or "(none)"


def _judge_llm(settings, prompt: str):
    """One OpenRouter judgment call. Returns (parsed_dict_or_None, sys, user, ptoks, ctoks, latency_ms)."""
    if not settings.openrouter_api_key:
        return None, "", prompt, 0, 0, 0
    t0 = time.monotonic()
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url)
        resp = client.chat.completions.create(
            model=settings.ontology_discovery_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        latency = int((time.monotonic() - t0) * 1000)
        raw = resp.choices[0].message.content or ""
        usage = getattr(resp, "usage", None)
        ptoks = getattr(usage, "prompt_tokens", 0) or 0
        ctoks = getattr(usage, "completion_tokens", 0) or 0
        try:
            from neo4j_graphrag.experimental.components.pdf_loader import fix_invalid_json  # noqa
        except Exception:
            pass
        try:
            parsed = json.loads(raw)
        except Exception:
            try:
                from neo4j_graphrag.exceptions import InvalidJSONError  # noqa
                from neo4j_graphrag.experimental.pipeline.exceptions import fix_invalid_json  # type: ignore
                parsed = json.loads(fix_invalid_json(raw))
            except Exception:
                start, end = raw.find("{"), raw.rfind("}")
                parsed = json.loads(raw[start:end + 1]) if start >= 0 and end > start else None
        return parsed, "", prompt, ptoks, ctoks, latency
    except Exception as e:
        logger.warning(f"Compliance judgment LLM call failed: {e}")
        return None, "", prompt, 0, 0, int((time.monotonic() - t0) * 1000)


def compliance_judgment(state: GraphState) -> GraphState:
    """Grounded compliance judgment + answer over the CU Plan + premises. Mode-gated, degrade-safe."""
    if state.get("mode") != _MODE:
        return state

    settings = get_settings()
    cu_plan = state.get("cu_plan", [])
    try:
        refs = _fetch_references(settings, [c["cu_id"] for c in cu_plan if c.get("cu_id")])
    except Exception as e:
        logger.warning(f"Reference fetch failed: {e}")
        refs = []

    prompt = JUDGE_PROMPT.format(
        question=state.get("query", ""),
        triples=_render_triples(state),
        anchors=_render_anchors(state),
        premises=_render_premises(state),
        obligations=_render_obligations(cu_plan),
        references=_render_references(refs),
    )
    parsed, sys_p, user_p, ptoks, ctoks, latency = _judge_llm(settings, prompt)

    if parsed and isinstance(parsed, dict):
        verdict = str(parsed.get("verdict", "")).strip()
        answer = str(parsed.get("answer", "")).strip()
        cites = parsed.get("citations", []) or []
        generation = f"[verdict: {verdict}] {answer}" if verdict else answer
    else:
        verdict, generation, cites = "", "", []

    state["generation"] = generation
    state["raw_generation"] = generation
    state["citations"] = [{"citation_id": c} for c in cites]
    state["is_rag_augmented"] = True
    state["system_prompt"] = sys_p
    state["user_prompt"] = user_p
    state["prompt_tokens"] = ptoks
    state["completion_tokens"] = ctoks
    state["total_tokens"] = ptoks + ctoks
    state["latency_ms"] = latency
    state["retrieval_succeeded"] = bool(cu_plan)
    logger.info(f"Compliance judgment: verdict={verdict!r}, {len(cites)} citation(s)")
    return state


__all__ = ["compliance_judgment"]
