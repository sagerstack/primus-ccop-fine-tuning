"""Phase 2 addendum — leaf-concept specialization (Fork 2).

For the umbrella control types whose one type-name node collapses many distinct concepts,
give the node a SPECIFIC canonical name (keeping the type) so distinct concepts form distinct
nodes / cross-clause bridges (POC mechanism). Only clauses that already invoke the umbrella
type are touched; the leaf is chosen by scanning the clause text. A clause that names several
leaves of one type expands its single generic triple into one triple per leaf.

Leaf names are chosen collision-safe: none is a type name and none CONTAINS an alias substring
(canon() substring-matches aliases like 'encryption'/'hash'/'control'), so they never collapse.

    poetry run python -m rag.graph.ontology_v2.specialize_leaves          # dry-run
    poetry run python -m rag.graph.ontology_v2.specialize_leaves --apply  # write
"""
import argparse
import json
import re
from pathlib import Path

_ROOT = Path(__file__).parent
_ONT = json.loads((_ROOT / "corpus_ontology.json").read_text())
_REEXTRACT = _ROOT / "reextract"
_RUNS = _ROOT / "runs" / "extract"
_ETYPE_LOWER = {e["name"].lower() for e in _ONT["entity_types"]}
_ALIASES = [a.lower() for e in _ONT["entity_types"] for a in e.get("aliases", [])]

# umbrella type -> ordered [(text regex, leaf canonical name)]
MAPS = {
    "DesignPrinciple": [
        (r"defen[cs]e[- ]in[- ]depth", "defence-in-depth"),
        (r"least[- ]privilege|minimum (extent of )?access|least extent", "least-privilege"),
        (r"segregat\w+ of dut|separation of dut", "segregation-of-duties"),
        (r"defen[cs]e[- ]by[- ]diversity|diversity", "defence-by-diversity"),
        (r"zero[- ]trust", "zero-trust"),
    ],
    "AccessControlMechanism": [
        (r"multi[- ]?factor|two[- ]?factor|\bmfa\b|\b2fa\b", "multi-factor-authentication"),
        (r"privileged access|privileged account|administrative access", "privileged-access-management"),
        (r"authoris|authoriz", "authorisation"),
        (r"authenticat", "authentication"),
        (r"session|logon|log[- ]on", "session-management"),
    ],
    "NetworkControl": [
        (r"web application firewall|\bwaf\b", "web-application-firewall"),
        (r"firewall", "firewall"),
        (r"segment", "network-segmentation"),
        (r"intrusion (detection|prevention)|\bnids\b|\bnips\b|ids/ips", "intrusion-detection"),
        (r"data[- ]diode|unidirectional|one[- ]way", "unidirectional-gateway"),
    ],
    "Cryptography": [
        (r"dnssec", "DNSSEC"),
    ],
}


def _collapses(name):
    low = name.lower()
    if low in _ETYPE_LOWER:
        return True
    return any(a in low for a in _ALIASES)


# safety: no leaf name may collapse
for _t, _pairs in MAPS.items():
    for _rx, _leaf in _pairs:
        assert not _collapses(_leaf), f"leaf '{_leaf}' collapses via canon()"


def _leaves(typ, text):
    out = []
    for rx, leaf in MAPS[typ]:
        if re.search(rx, text):
            out.append(leaf)
    return out


def _clause_text(cid):
    for d in _REEXTRACT.iterdir():
        f = d / "clauses.clean.json"
        if f.exists():
            for r in json.loads(f.read_text()):
                if r["citation_id"] == cid:
                    return r["text"].lower()
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    per_leaf = {}
    clauses_touched = 0
    samples = []
    for cf in sorted(_RUNS.glob("*.json")):
        d = json.loads(cf.read_text())
        if d.get("extractor") != "claude-opus":
            continue
        text = _clause_text(d["citation_id"])
        new_triples = []
        changed = False
        for t in d["triples"]:
            variants = [t]
            for end, etype in (("s", "s_type"), ("o", "o_type")):
                typ = t[etype]
                # only specialize an endpoint still carrying the bare type name
                if typ in MAPS and t[end] == typ:
                    leaves = _leaves(typ, text)
                    if leaves:
                        expanded = []
                        for v in variants:
                            for leaf in leaves:
                                nv = dict(v); nv[end] = leaf
                                expanded.append(nv)
                                per_leaf[leaf] = per_leaf.get(leaf, 0) + 1
                        variants = expanded
                        changed = True
            new_triples.extend(variants)
        if changed:
            # dedup on (s, rel, o)
            seen, dedup = set(), []
            for t in new_triples:
                k = (t["s"], t["rel"], t["o"])
                if k not in seen:
                    seen.add(k); dedup.append(t)
            d["triples"] = dedup
            d["concepts"] = sorted({t["s"] for t in dedup} | {t["o"] for t in dedup})
            clauses_touched += 1
            if len(samples) < 20:
                samples.append(f"  [{d['citation_id']}] -> " +
                               ", ".join(sorted({t[e] for t in dedup for e in ('s','o')
                                                 if t[e] in per_leaf})))
            if a.apply:
                cf.write_text(json.dumps(d, indent=2))
    print(f"{'APPLIED' if a.apply else 'DRY-RUN'}: {clauses_touched} clauses specialized")
    print("leaf node -> #triples:")
    for leaf, n in sorted(per_leaf.items(), key=lambda x: -x[1]):
        print(f"  {leaf}: {n}")
    print("samples:")
    print("\n".join(samples))


if __name__ == "__main__":
    main()
