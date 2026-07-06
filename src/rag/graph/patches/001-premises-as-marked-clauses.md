# Patch 001 — premises become marked clauses (paper alignment)

**Decision:** align the graph with GraphCompliance Algorithm 1 — a *premise* is a
**mark on its clause node**, not a separate node. Obligations (`actor-CU`/`meta-CU`)
stay as derived CU nodes (they already match the paper's `DERIVES` model).

**Why:** our model gave every premise a separate `ComplianceUnit{cu_type:'premise'}`
node over the `Clause` layer — an indirection the paper avoids. Phase 11's goal is
"align graphrag to graphcompliance architecture," so we adopt the paper's node model.

## Operation

For each of the 423 `premise` CUs (verified 1:1 with a clause, 0 clauses shared with
an obligation CU): stamp the clause with a `:Premise` label + `premise_kind` (+ the old
`cu_id` for provenance), then delete the premise CU node and its `FROM_CLAUSE` edge.

## Before → After manifest

| | Before | After |
|---|---|---|
| ComplianceUnit nodes | 804 (423 premise / 365 actor / 16 meta) | **381** (365 actor / 16 meta) |
| `:Premise`-labelled clauses | 0 | **423** |
| Clause nodes | 883 | 883 (unchanged) |
| `FROM_CLAUSE` edges | 804 | **381** (−423) |
| `HAS_CHILD` | 765 | 765 (unchanged) |
| `REFERS_TO` | 172 | **143 (−29)** |

Deleted: 423 premise CU nodes + 423 FROM_CLAUSE edges + **29 REFERS_TO edges**.
Added: `:Premise` + `premise_kind` + `premise_cu_id` on 423 clauses.

**REFERS_TO −29 (not in the original estimate — caught by the post-patch diff):** all 29
were `obligation → premise` references (premise as *target*), removed with the premise CU.
This is **consistent with the paper** — REFERS_TO is CU→CU and premises aren't CUs, so these
edges don't exist in the paper's model. ~23 pointed at duplicate-blob premises (removed
later anyway); the rest at mis-tagged premises (e.g. `Act-19`) that should be obligations —
those re-materialize as legitimate CU→CU refs once retyped. Accepted, not preserved.

## Paired consumer-code change (required, same change-set)

`rag/retrieval/nodes/anchor_hypernym_mapping.py::_FETCH_FRAGMENT_POOL_QUERY` currently
fetches `ComplianceUnit` with `cu_type IN ['premise','actor-CU','meta-CU']`. After this
patch, premises are `:Premise` clauses, not CUs — so the fragment pool + the STRONG
`is_premise` predicate must read `:Premise`-labelled clauses (definitional carriers)
alongside actor/meta CU subjects. Without this, hypernym mapping loses all premises.

## Post-conditions (self-check, in the .cypher)

- 0 `ComplianceUnit {cu_type:'premise'}` remain
- 423 `:Premise` clauses, each with `premise_kind`
- ComplianceUnit total = 381
