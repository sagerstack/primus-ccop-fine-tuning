"""Phase 2 addendum — encode shall/should modality (B02) as a Provision MANDATES/RECOMMENDS
edge on obligation clauses. Deterministic lexical modality (shall/must -> MANDATES;
should -> RECOMMENDS) projected onto the control/process the clause already invokes
(from the hand-authored triples). Adds at most ONE modality edge per clause; skips
clauses that already carry MANDATES/RECOMMENDS or have no mandatable object.

    poetry run python -m rag.graph.ontology_v2.modality_pass          # dry-run report
    poetry run python -m rag.graph.ontology_v2.modality_pass --apply  # write
"""
import argparse
import json
import re
from pathlib import Path

_ROOT = Path(__file__).parent
_ONT = json.loads((_ROOT / "corpus_ontology.json").read_text())
_REEXTRACT = _ROOT / "reextract"
_RUNS = _ROOT / "runs" / "extract"
_REL = {r["name"]: r for r in _ONT["relations"]}
_PARENT = {e["name"]: e.get("subtype_of") for e in _ONT["entity_types"]}


def _anc(t):
    out, cur = {t}, _PARENT.get(t)
    while cur:
        out.add(cur); cur = _PARENT.get(cur)
    return out


def _mandatable(t):
    return bool(_anc(t) & set(_REL["MANDATES"]["range"]))


def _key(cid):
    return _RUNS / (re.sub(r"[^A-Za-z0-9]", "_", cid) + ".json")


# object-selection priority: what the clause requires
_SUBJ_RELS = ["PROTECTS", "MITIGATES", "ADDRESSES", "APPLIES_BASELINE", "DISABLES",
              "REDUCES", "RECOVERS", "RESPONDS_TO", "VALIDATES", "DETECTS", "CONDUCTS", "IDENTIFIES"]
_OBJ_RELS = ["IMPLEMENTS", "CONDUCTS", "MANDATES", "RECOMMENDS"]


def _pick_object(triples):
    # 1: object of IMPLEMENTS/CONDUCTS (what the CIIO does)
    for rel in ("IMPLEMENTS", "CONDUCTS"):
        for t in triples:
            if t["rel"] == rel and _mandatable(t["o_type"]):
                return t["o"], t["o_type"]
    # 2: subject of a control/process/plan relation (the mechanism itself)
    for t in triples:
        if t["rel"] in _SUBJ_RELS and _mandatable(t["s_type"]):
            return t["s"], t["s_type"]
    return None


def _clause_text(cid):
    for d in _REEXTRACT.iterdir():
        f = d / "clauses.clean.json"
        if f.exists():
            for r in json.loads(f.read_text()):
                if r["citation_id"] == cid:
                    return r["text"]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    added = {"MANDATES": 0, "RECOMMENDS": 0}
    skipped_has_modality = skipped_no_obj = skipped_no_signal = 0
    samples = []
    for cf in sorted(_RUNS.glob("*.json")):
        d = json.loads(cf.read_text())
        if d.get("extractor") != "claude-opus":
            continue
        triples = d["triples"]
        if any(t["rel"] in ("MANDATES", "RECOMMENDS") for t in triples):
            skipped_has_modality += 1
            continue
        text = _clause_text(d["citation_id"]).lower()
        if re.search(r"\bshall\b|\bmust\b", text):
            mod = "MANDATES"
        elif re.search(r"\bshould\b", text):
            mod = "RECOMMENDS"
        else:
            skipped_no_signal += 1
            continue
        picked = _pick_object(triples)
        if not picked:
            skipped_no_obj += 1
            continue
        obj, otype = picked
        triples.append({"s": "Provision", "s_type": "Provision", "rel": mod, "o": obj, "o_type": otype})
        d["concepts"] = sorted(set(d["concepts"]) | {obj})
        added[mod] += 1
        if len(samples) < 24:
            samples.append(f"  [{d['citation_id']}] {mod} -> {obj}")
        if a.apply:
            cf.write_text(json.dumps(d, indent=2))
    print(f"{'APPLIED' if a.apply else 'DRY-RUN'}: +MANDATES={added['MANDATES']}  +RECOMMENDS={added['RECOMMENDS']}")
    print(f"skipped: already-has-modality={skipped_has_modality}  no-shall/should={skipped_no_signal}  no-mandatable-object={skipped_no_obj}")
    print("samples:")
    print("\n".join(samples))


if __name__ == "__main__":
    main()
