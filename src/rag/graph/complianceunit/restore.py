"""Restore the Phase-11 Compliance-Unit graph from cu_graph_backup.json into Neo4j.

Recreates the exact nodes (labels + props) and relationships (type + props) that were
exported before the OMD-GraphRAG layer replaced them. Idempotent-ish: it CREATEs, so run
only against a graph that does NOT already contain these CU nodes (i.e. after a teardown).

    poetry run python -m rag.graph.complianceunit.restore
"""
import json
from pathlib import Path
from rag.graph.ontology_v2._neo import session

_DUMP = Path(__file__).parent / "cu_graph_backup.json"


def main() -> None:
    d = json.loads(_DUMP.read_text())
    nodes, rels = d["nodes"], d["rels"]
    with session() as s:
        # nodes grouped by exact label-set (labels must be static in Cypher)
        from collections import defaultdict
        by_labels = defaultdict(list)
        for n in nodes:
            by_labels[tuple(sorted(n["labels"]))].append(n)
        for labels, group in by_labels.items():
            lbl = "".join(f":`{l}`" for l in labels)
            s.run(
                f"UNWIND $rows AS row CREATE (n{lbl}) SET n = row.props SET n._eid = row.eid",
                rows=[{"eid": n["eid"], "props": n["props"]} for n in group],
            )
        # relationships grouped by type
        by_type = defaultdict(list)
        for r in rels:
            by_type[r["type"]].append(r)
        for rtype, group in by_type.items():
            s.run(
                f"UNWIND $rows AS row MATCH (a {{_eid: row.start}}), (b {{_eid: row.end}}) "
                f"CREATE (a)-[x:`{rtype}`]->(b) SET x = row.props",
                rows=[{"start": r["start"], "end": r["end"], "props": r["props"]} for r in group],
            )
        s.run("MATCH (n) WHERE n._eid IS NOT NULL REMOVE n._eid")
        nc = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rc = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    print(f"restored — graph now has {nc} nodes, {rc} rels "
          f"(backup had {d['counts']['nodes']} nodes, {d['counts']['rels']} rels)")


if __name__ == "__main__":
    main()
