# Graph patches

**Working model (2026-07-06):** the graph is no longer rebuilt from code. The
construction pipeline (`CUClassifier`, `CUExtractor`, `PolicyGraphBuilder`) is
**frozen/legacy**. The live Neo4j graph is the artifact of record, and all fixes
are applied as **ordered, idempotent, reviewed patches** here.

## Reproducibility

    graph state  =  snapshots/000-baseline-20260706.json  +  001-*.cypher, 002-*.cypher, … (in order)

- `snapshots/000-baseline-*.json` — complete export (all nodes+props, all edges).
  Restore anchor. Never edit.
- `NNN-<slug>.cypher` — one patch per fix. **Idempotent** (safe to re-run),
  numbered, applied in order.
- `NNN-<slug>.md` — the patch's rationale + before/after manifest (what changed).

## Rules

1. Every patch is reviewed (before/after manifest shown) **before** it is applied.
2. Every patch is idempotent — re-running it is a no-op.
3. Consumer code (retrieval / hypernym nodes) is updated in lockstep when a patch
   changes the shape it reads. Build code is NOT touched.
4. Nothing is applied to the graph without an entry here.

## Apply

    cd src && CCOP_NEO4J_PASSWORD=… \
      docker exec -i neo4j-local cypher-shell -u neo4j -p "$CCOP_NEO4J_PASSWORD" -f - < rag/graph/patches/NNN-<slug>.cypher
