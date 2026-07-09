"""Phase 6 — concept-IDF: precompute inverse document frequency and store it on each :Concept.

Channel-I's equal-weight concept overlap lets hub concepts (CII df=296, CIIO df=382, Provision
df=328) dominate scoring, so a hub-heavy clause outranks the focused decisive one (B01-001: RtF
§2.2 buried under OT-architecture §10.2). IDF fixes this: rare concepts that actually discriminate
(EnterpriseNetwork, DigitalBoundary, Obligation ≈ 4-5) outweigh hubs (≈ 0.8-1.1).

    idf(c) = log(N / df(c))      N = #:Clause, df(c) = #clauses that INVOKE c

Stored additively as :Concept.idf (property write only — no new nodes/edges). Concepts with no
INVOKES edge get idf = log(N) (max), so a query concept that no clause invokes never silently
scores 0 by a missing property.

    poetry run python -m rag.graph.ontology_v2.compute_idf            # dry-run distribution
    poetry run python -m rag.graph.ontology_v2.compute_idf --apply
"""
import argparse
import math

from rag.graph.ontology_v2._neo import session, query as _q

BUILD_ID = "omd-v1-20260709"


def compute() -> dict:
    N = _q("MATCH (c:Clause {build_id:$b}) RETURN count(c) AS n", b=BUILD_ID)[0]["n"]
    df = {r["n"]: r["df"] for r in _q(
        "MATCH (cl:Clause {build_id:$b})-[:INVOKES]->(c:Concept {build_id:$b}) "
        "RETURN c.name AS n, count(DISTINCT cl) AS df", b=BUILD_ID)}
    default = math.log(N)  # concept invoked by nothing → maximally specific
    names = [r["n"] for r in _q("MATCH (c:Concept {build_id:$b}) RETURN c.name AS n", b=BUILD_ID)]
    return {n: math.log(N / df[n]) if n in df else default for n in names}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    idf = compute()
    srt = sorted(idf.items(), key=lambda x: x[1])
    print(f"idf over {len(idf)} concepts  (idf = log(N/df))")
    print("  lowest (hubs) :", ", ".join(f"{n}={v:.2f}" for n, v in srt[:5]))
    print("  highest (rare):", ", ".join(f"{n}={v:.2f}" for n, v in srt[-5:]))
    if not a.apply:
        print("dry-run — pass --apply to write :Concept.idf")
        return
    with session() as s:
        s.run("UNWIND $rows AS r MATCH (c:Concept {name:r.name, build_id:$b}) SET c.idf=r.idf",
              rows=[{"name": n, "idf": v} for n, v in idf.items()], b=BUILD_ID)
        got = s.run("MATCH (c:Concept {build_id:$b}) WHERE c.idf IS NOT NULL RETURN count(c) AS n",
                    b=BUILD_ID).single()["n"]
    print(f"SET :Concept.idf on {got} nodes")


if __name__ == "__main__":
    main()
