# Neo4j Browser Visual-Inspection Workflow (Phase 9, D-18/D-19)

The emergent CCoP knowledge graph (Phase 9 — un-governed, no ontology/schema
constraint, D-03/D-08) must be **seen and measured** before it is ever scored
against the hybrid baseline. This is D-18's interactive/visual layer.
Its quantitative complement is `ccop-eval graph inspect|stats` (Plan 09-03,
`src/rag/graph/inspect/metrics.py`) — run both; they surface different
signal (visual density/clusters/garbage vs. numeric metrics).

## Opening the Browser

1. Ensure the local Neo4j service is running:
   ```bash
   docker compose up -d neo4j
   ```
2. Open **http://localhost:7474** in a browser.
3. Connect using:
   - **Connect URL:** `bolt://localhost:7687`
   - **Username:** `neo4j` (or `CCOP_NEO4J_USER` if overridden)
   - **Password:** the value of `CCOP_NEO4J_PASSWORD` in `src/config/.env.local`
     (must match the `docker-compose.yml` `NEO4J_AUTH` value — never a
     committed literal, T-09-10).

Neo4j Browser ships with the Docker image; Bloom (graphical exploration) is
also available from the same login if the Community/Enterprise image
includes it — Browser + the Cypher snippets below are sufficient for the
D-18 visual-inspection requirement regardless.

## Cypher Inspection Snippets

Paste these directly into the Browser query bar. Each targets a different
"garbage or functional?" question from D-18/D-19.

### 1. Sample entities and relationships (get oriented)

```cypher
MATCH (n:__Entity__)-[r]->(m:__Entity__)
RETURN n, r, m
LIMIT 75
```

Renders as an interactive graph. Look for: relationships that make semantic
sense given CCoP subject matter (e.g. `MANAGES`, `OVERSEES`, `RESPONDS_TO`
between plausible entity types), vs. nonsensical pairings.

### 2. Densest nodes (potential hubs or entity-resolution collisions)

```cypher
MATCH (n:__Entity__)
RETURN labels(n) AS labels, properties(n) AS props, COUNT { (n)--() } AS degree
ORDER BY degree DESC
LIMIT 20
```

A very high degree can mean a legitimately central concept (e.g. "Cyber
Security Agency of Singapore") — or a genericized entity that collapsed many
distinct mentions into one node (see snippet 4).

### 3. Orphan / isolated nodes (extraction that went nowhere)

```cypher
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n) AS labels, properties(n) AS props
LIMIT 50
```

Isolated nodes contribute to node_count but nothing to graph-retrieval
context — they are candidates for "garbage" review under D-19.

### 4. Entity-type counts (does the emergent taxonomy look sane?)

```cypher
MATCH (n)
UNWIND labels(n) AS label
WITH label, count(*) AS count
WHERE NOT label IN ['__KGBuilder__', '__Entity__', 'Chunk', 'Document']
RETURN label, count
ORDER BY count DESC
```

Compare against `ccop-eval graph inspect`'s entity-type-distribution table —
this is the same metric, browsable and clickable per label.

### 5. Duplicate / near-duplicate entity candidates

```cypher
MATCH (n:__Entity__)
WITH n, coalesce(n.name, n.identifier, toString(n.user_id),
                  toString(n.asset_id), toString(n.incident_id)) AS display_name
WHERE display_name IS NOT NULL
WITH toLower(display_name) AS normalized, collect(n) AS nodes
WHERE size(nodes) > 1
RETURN normalized, size(nodes) AS group_size, nodes
ORDER BY group_size DESC
LIMIT 20
```

Emergent (schema-free) extraction commonly collapses many distinct mentions
onto generic identifier conventions (e.g. `user123`, `CII-001`) — this is
the visual counterpart to `KGInspector.duplicate_entities()`.

### 6. A single document's chunk chain (does chunking look coherent?)

```cypher
MATCH (d:Document)<-[:FROM_DOCUMENT]-(c:Chunk)
WHERE d.path CONTAINS 'CCoP'
RETURN d, c
ORDER BY c.index
LIMIT 50
```

## Honesty Guardrail (D-19)

**Iteration is for making the emergent extraction *functional* — not for
tuning toward benchmark scores.**

- **In scope for iteration:** fixing extraction that is obviously broken
  (isolated garbage nodes with no relationships, malformed/empty properties,
  entity types that are clearly parser artifacts rather than domain
  concepts). If a fix is applied, rebuild and re-inspect (see below), and
  **report the change and why it was made** — this is a principled,
  documented decision, never silent tuning.
- **Out of scope for iteration:** adjusting chunk size, extraction prompt
  wording, or entity-resolution thresholds specifically because a
  B01/B03/B04 answer scored poorly. That would blur the Phase 9 emergent
  baseline against the Phase 10 ontology-grounded comparison (D-16) — the
  whole point of the two-phase design is that the *only* variable that
  changes between them is extraction governance (emergent vs
  ontology-grounded), not chunking or prompting.
- Any change beyond "make it work" must be called out explicitly in the
  plan/run notes, not folded in quietly alongside an unrelated fix.

If in doubt whether a change is "fixing broken" vs. "tuning toward a score":
it is tuning if the change was motivated by looking at eval results rather
than by looking at the graph itself.

## The Iterate-and-Improve Loop (D-19)

```
inspect (Browser + `ccop-eval graph inspect`)
   -> adjust (only "make it work" fixes, per the guardrail above)
   -> rebuild
   -> re-inspect
   -> (repeat until the graph is structurally sound)
   -> only then: run retrieval/eval (Plan 09-05/09-06)
```

Rebuild command (clears the existing graph first — irreversible, confirm
before running against a graph you want to keep):

```bash
cd src && poetry run ccop-eval graph build --drop
```

Quantitative re-check after any rebuild:

```bash
cd src && poetry run ccop-eval graph inspect
# or, machine-readable for the comparison report (D-15):
cd src && poetry run ccop-eval graph stats --output kg-stats.json
```

A degenerate graph (near-zero clause coverage, near-total orphan nodes, or a
handful of duplicate-collapsed mega-entities dominating the degree
distribution) should be caught and addressed here — **before** Plan 09-05/06
ever score a response generated against it.
