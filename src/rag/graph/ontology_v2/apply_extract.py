"""Phase 2 — apply HAND-AUTHORED (Opus) triples through Φ-validation + cache.

The clause->triples reasoning is done by hand (Claude Opus reading each clause);
this script does NOT call any LLM. It only Φ-validates the authored triples via
extract.type_ok/canon and writes the per-clause cache tagged extractor=claude-opus.

Batch file format (JSON list):
    [
      {"citation_id": "CCoP 2.0::1.2.5",
       "triples": [
         {"subject": "...", "subject_type": "...", "relation": "...",
          "object": "...", "object_type": "...", "proposed": false}
       ]},
      ...
    ]

    poetry run python -m rag.graph.ontology_v2.apply_extract --file batch.json
"""
import argparse
import json
from pathlib import Path

from rag.graph.ontology_v2.extract import apply_authored


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="batch JSON of authored triples")
    ap.add_argument("--no-force", action="store_true", help="skip clauses already cached")
    a = ap.parse_args()
    batch = json.loads(Path(a.file).read_text())
    if isinstance(batch, dict):                       # {cid: [triples]} also accepted
        batch = [{"citation_id": k, "triples": v} for k, v in batch.items()]

    tot_kept = tot_prop = 0
    fails = []
    for rec in batch:
        cid = rec["citation_id"]
        res = apply_authored(cid, rec["triples"], force=not a.no_force)
        nk, npr = len(res["triples"]), len(res["proposed"])
        tot_kept += nk; tot_prop += npr
        flag = "  <-- PROPOSED/DROPPED" if npr else ""
        print(f"[{cid}]  kept={nk}  proposed={npr}{flag}")
        for t in res["proposed"]:
            reason = t.get("reason", "out-of-schema")
            print(f"    PROPOSED ({t.get('s')}:{t.get('s_type')}) -[{t.get('rel')}]-> "
                  f"({t.get('o')}:{t.get('o_type')})   {reason}")
            fails.append((cid, reason))
    print(f"\n=== {len(batch)} clauses | kept={tot_kept} | proposed/dropped={tot_prop} ===")
    if fails:
        print("Review the PROPOSED lines above: fix authored types/relations if they "
              "were meant to be in-schema, or leave as intended coverage signal.")


if __name__ == "__main__":
    main()
