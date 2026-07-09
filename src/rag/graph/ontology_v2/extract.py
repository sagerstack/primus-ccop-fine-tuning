"""Phase 2 — blind, ontology-guided extraction (OMD-GraphRAG §3.1 + POC extract()).

Per clause: inject the locked schema S=(E,R,Φ) into the prompt, call the LLM, resolve
entities to canonical types (canon/aliases), then post-hoc Φ type-check every triple
(type_ok, subtype-aware). In-schema+valid triples are kept; out-of-schema emissions are
held aside as `proposed` (open schema). Per-clause JSON cache → resumable. Blind: the
extractor never sees benchmark/answer labels.

    poetry run python -m rag.graph.ontology_v2.extract --ids "CCoP 2.0::1.2.5" ...
    poetry run python -m rag.graph.ontology_v2.extract --doc 1            # whole doc
"""
import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from infrastructure.config.settings import get_settings

_ROOT = Path(__file__).parent
_ONT = json.loads((_ROOT / "corpus_ontology.json").read_text())
_REEXTRACT = _ROOT / "reextract"
_RUNS = _ROOT / "runs" / "extract"

# ---- schema indexes -------------------------------------------------------
_ETYPES = {e["name"]: e for e in _ONT["entity_types"]}
_PARENT = {e["name"]: e.get("subtype_of") for e in _ONT["entity_types"]}
_REL = {r["name"]: r for r in _ONT["relations"]}
_ETYPE_LOWER = {n.lower(): n for n in _ETYPES}
_ALIAS = {}
for e in _ONT["entity_types"]:
    for a in e.get("aliases", []):
        _ALIAS[a.lower()] = e["name"]


def _ancestors(t: str) -> set:
    out, cur = {t}, _PARENT.get(t)
    while cur:
        out.add(cur); cur = _PARENT.get(cur)
    return out


def _is_a(t: str, required: str) -> bool:
    return required in _ancestors(t)


def canon(name: str, typ: str) -> Tuple[str, str]:
    """Resolve to (canonical_name, canonical_type). Aliases + type snapping."""
    n = (name or "").strip().strip('"').strip()
    low = n.lower()
    if low in _ALIAS:
        ct = _ALIAS[low]; return ct, ct
    if low in _ETYPE_LOWER:                   # name IS an entity type -> snap (fixes mis-typing)
        ct = _ETYPE_LOWER[low]; return ct, ct
    if typ in _ETYPES:                       # LLM gave a valid type
        return (typ if len(n) < 3 else n), typ
    for k, v in _ALIAS.items():              # substring alias
        if k in low:
            return v, v
    return n, typ                            # unresolved -> keep raw (proposed)


def type_ok(rel: str, stype: str, otype: str) -> bool:
    r = _REL.get(rel)
    if not r:
        return False
    dom_ok = any(_is_a(stype, d) for d in r["domain"])
    if "__literal__" in r["range"] or "__any_entity__" in r["range"]:
        rng_ok = True if "__any_entity__" in r["range"] else True  # literal object allowed
    else:
        rng_ok = any(_is_a(otype, rr) for rr in r["range"])
    return dom_ok and rng_ok


# ---- prompt ---------------------------------------------------------------
def _schema_block() -> str:
    ent = "\n".join(f"- {e['name']}: {e.get('desc','')}" for e in _ONT["entity_types"] if not e.get("abstract"))
    rel = "\n".join(f"- {r['name']}: {'|'.join(r['domain'])} -> {'|'.join(r['range'])}" for r in _ONT["relations"])
    return ent, rel


_PROMPT = """Extract typed relation triples from this regulatory clause, guided by the ontology.

ENTITY TYPES (use ONLY these for subject_type/object_type; normalize to the canonical type):
{ent}

RELATIONS (use ONLY these; the types must satisfy the shown domain -> range):
{rel}

Rules:
- subject and object MUST each be a CANONICAL ENTITY - a short noun/name that maps to one entity type. NEVER put a clause sentence, verb phrase, or requirement text as a subject/object.
- Normalize to the canonical type: "the CII"/"CII systems" -> CII; "CSA"/"Sector Lead" -> Regulator; "digital boundary"/"cyber operating environment" -> DigitalBoundary; "default password" -> DefaultCredential; "hash form" -> HashStorage.
- For a REQUIREMENT clause (e.g. "the CIIO shall maintain a risk register"), extract the concrete triple: (Provision, MANDATES, RiskRegister) and/or (CIIO, IMPLEMENTS, RiskRegister). Do NOT emit (CIIO, HAS_OBLIGATION, "<the whole sentence>"). Only use HAS_OBLIGATION with a short named Obligation, never a sentence.
- For hardening/credential clauses, extract the specific security objects: Password, DefaultCredential, HashStorage, Account, PrivilegedAccount, Port, Service (e.g. "default passwords shall be changed" -> (SecurityConfigurationBaseline, MUST_CHANGE, DefaultCredential); "stored in hash forms" -> (Password, STORED_AS, HashStorage)).
- DEFERRAL / SILENCE (important): when a clause defers a specification to an external standard (e.g. "the CIIO may take reference from NIST to determine the appropriate password length"), emit BOTH (CIIO, DEFERS_TO, ExternalStandard) AND (CodeOfPractice, DOES_NOT_SPECIFY, <the thing not specified, e.g. PasswordLength>). Also invoke the underlying object AND link a specific attribute to its general concept, e.g. (PasswordLength, ATTRIBUTE_OF, Password), so length-related clauses link to password clauses.
- If a clause asserts something the ontology genuinely cannot express, you MAY emit a triple with a type/relation NOT in the lists and set "proposed": true.
- Return ONLY a JSON array of objects {{"subject","subject_type","relation","object","object_type"}} (add "proposed": true if out-of-schema). No prose.

CLAUSE:
{clause}

JSON:"""


def _call_llm(clause_text: str) -> str:
    from openai import OpenAI
    s = get_settings()
    ent, rel = _schema_block()
    cli = OpenAI(api_key=s.openrouter_api_key, base_url=s.openrouter_base_url, timeout=90)
    r = cli.chat.completions.create(
        model=s.ontology_discovery_model,
        messages=[{"role": "user", "content": _PROMPT.format(ent=ent, rel=rel, clause=clause_text)}],
        temperature=0.0, max_tokens=900,
    )
    return (r.choices[0].message.content or "").strip()


def _parse(raw: str) -> List[Dict[str, Any]]:
    try:
        from neo4j_graphrag.experimental.components.entity_relation_extractor import fix_invalid_json
        data = json.loads(fix_invalid_json(raw))
    except Exception:
        try:
            data = json.loads(raw[raw.find("["): raw.rfind("]") + 1])
        except Exception:
            data = []
    return data if isinstance(data, list) else []


def _cache_path(citation_id: str) -> Path:
    return _RUNS / (re.sub(r"[^A-Za-z0-9]", "_", citation_id) + ".json")


def _validate_and_cache(citation_id: str, raw_triples: List[Dict[str, Any]],
                        extractor: str | None = None) -> Dict[str, Any]:
    """Shared Φ-validation + cache loop. `raw_triples` is a list of
    {subject, subject_type, relation, object, object_type, [proposed]} — from
    either _call_llm (gpt-4o-mini) or hand-authored (Opus). No LLM call here.
    """
    _RUNS.mkdir(parents=True, exist_ok=True)
    kept, proposed = [], []
    concepts = set()
    for t in raw_triples:
        rel = str(t.get("relation", "")).strip()
        se, st = canon(t.get("subject"), t.get("subject_type", ""))
        oe, ot = canon(t.get("object"), t.get("object_type", ""))
        # free-text guard: a concept is a short name, never a clause sentence
        free_text = len(str(se).split()) > 4 or len(str(oe).split()) > 4
        is_proposed = bool(t.get("proposed")) or rel not in _REL or st not in _ETYPES or (ot not in _ETYPES and "__" not in "".join(_REL.get(rel, {}).get("range", [])))
        triple = {"s": se, "s_type": st, "rel": rel, "o": oe, "o_type": ot}
        if free_text:
            proposed.append({**triple, "reason": "free_text_not_concept"})
        elif is_proposed:
            proposed.append(triple)
        elif type_ok(rel, st, ot):
            kept.append(triple); concepts.update([se, oe])
        else:
            proposed.append({**triple, "reason": "phi_type_mismatch"})
    # dedup kept triples on (s, rel, o)
    seen, deduped = set(), []
    for t in kept:
        k = (t["s"], t["rel"], t["o"])
        if k not in seen:
            seen.add(k); deduped.append(t)
    kept = deduped
    result = {"citation_id": citation_id, "concepts": sorted(concepts),
              "triples": kept, "proposed": proposed, "n_raw": len(raw_triples)}
    if extractor:
        result["extractor"] = extractor
    _cache_path(citation_id).write_text(json.dumps(result, indent=2))
    return result


def apply_authored(citation_id: str, triples: List[Dict[str, Any]],
                   force: bool = True) -> Dict[str, Any]:
    """Persist Opus-authored triples: Φ-validate + cache, tagged claude-opus.
    The reasoning (clause -> triples) is done by hand; this only validates."""
    cache = _cache_path(citation_id)
    if cache.exists() and not force:
        return json.loads(cache.read_text())
    return _validate_and_cache(citation_id, triples, extractor="claude-opus")


def extract(citation_id: str, text: str, force: bool = False) -> Dict[str, Any]:
    cache = _cache_path(citation_id)
    if cache.exists() and not force:
        return json.loads(cache.read_text())
    return _validate_and_cache(citation_id, _parse(_call_llm(text)))


def _clauses_for_doc(idx: int) -> List[Dict[str, Any]]:
    slug = sorted(p.name for p in _REEXTRACT.iterdir())[idx - 1]
    return json.loads((_REEXTRACT / slug / "clauses.clean.json").read_text())


def _find_clause(cid: str) -> str:
    for d in _REEXTRACT.iterdir():
        f = d / "clauses.clean.json"
        if f.exists():
            for r in json.loads(f.read_text()):
                if r["citation_id"] == cid:
                    return r["text"]
    raise SystemExit(f"clause not found: {cid}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--doc", type=int)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    targets = [(cid, _find_clause(cid)) for cid in (a.ids or [])] if a.ids \
        else [(r["citation_id"], r["text"]) for r in _clauses_for_doc(a.doc)]
    for cid, text in targets:
        res = extract(cid, text, force=a.force)
        print(f"\n[{cid}]  concepts={res['concepts']}")
        for t in res["triples"]:
            print(f"    KEPT     ({t['s']}:{t['s_type']}) -[{t['rel']}]-> ({t['o']}:{t['o_type']})")
        for t in res["proposed"]:
            print(f"    PROPOSED ({t.get('s')}:{t.get('s_type')}) -[{t.get('rel')}]-> ({t.get('o')}:{t.get('o_type')})  {t.get('reason','out-of-schema')}")
