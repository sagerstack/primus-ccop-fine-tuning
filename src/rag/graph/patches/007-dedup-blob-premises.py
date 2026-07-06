"""
Patch 007a — de-duplicate blob premises. For every group of byte-identical
:Premise clauses (the RtF/RiskGuide/ThreatGuide/AuditGuide section blobs that the
chunking bug copied across sub-clauses), keep ONE :Premise representative (the
lexicographically-smallest citation_id) and de-premise the redundant copies.

Removes the DUPLICATION noise from the retrieval pool only — text/nodes are kept,
only the :Premise label is removed from the redundant copies (reversible). Content
recovery (proper sub-item chunking) remains the separate re-chunk effort (B).

Idempotent: after running, no duplicate :Premise text groups remain, so a re-run
finds nothing to drop.

Usage:
  cd src && poetry run python rag/graph/patches/007-dedup-blob-premises.py          # DRY RUN (prints plan)
  cd src && poetry run python rag/graph/patches/007-dedup-blob-premises.py apply    # apply
"""
import os, sys, hashlib, neo4j
from collections import defaultdict

def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    pw = os.environ.get("CCOP_NEO4J_PASSWORD", "test12345")
    drv = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", pw))
    with drv.session() as s:
        rows = list(s.run("MATCH (c:Clause:Premise) RETURN c.citation_id AS cit, c.text AS t"))
        groups = defaultdict(list)
        for r in rows:
            groups[hashlib.md5((r["t"] or "").encode()).hexdigest()].append((r["cit"], r["t"]))
        drop_ids, plan = [], []
        for h, members in groups.items():
            if len(members) <= 1:
                continue
            ids = sorted(c for c, _ in members)
            keep, drops = ids[0], ids[1:]
            drop_ids += drops
            plan.append((keep, len(drops), len(members[0][1]), drops))

        print(f"{'APPLY' if apply else 'DRY RUN'} — {len(plan)} dup groups, keep {len(plan)}, de-premise {len(drop_ids)} redundant copies")
        print(f"{'':4}{'KEEP (stays :Premise)':28}{'size':>7}{'  drop':>7}")
        for keep, ndrop, size, drops in sorted(plan, key=lambda x: -x[1]):
            print(f"    {keep:28}{size:>7}{ndrop:>7}   e.g. {drops[:3]}")

        if apply:
            r = s.run("MATCH (c:Clause:Premise) WHERE c.citation_id IN $ids "
                      "REMOVE c:Premise, c.premise_kind, c.premise_cu_id RETURN count(c) AS n",
                      ids=drop_ids).single()
            total = s.run("MATCH (c:Clause:Premise) RETURN count(c) AS n").single()["n"]
            remaining_dupes = sum(1 for h, m in defaultdict(list, {}).items())  # recompute below
            after = list(s.run("MATCH (c:Clause:Premise) RETURN c.text AS t"))
            g2 = defaultdict(int)
            for x in after: g2[hashlib.md5((x["t"] or "").encode()).hexdigest()] += 1
            dup_left = sum(1 for v in g2.values() if v > 1)
            print(f"\nde-premised: {r['n']} | :Premise total now: {total} | duplicate groups left: {dup_left}")
            drv.close()
            sys.exit(0 if (r["n"] == len(drop_ids) and dup_left == 0) else 1)
    drv.close()

if __name__ == "__main__":
    main()
