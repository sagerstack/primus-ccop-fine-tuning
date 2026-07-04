# Phase 11: Align GraphRAG to GraphCompliance - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-04
**Phase:** 11-align-graphrag-to-graphcompliance-architecture-scenario-anch
**Areas discussed:** Scenario-anchoring approach (OMAGR vs GraphCompliance), Policy Graph
construction, premise/CU model, Context Graph, retrieval mechanism, judgment prompt, retrieval-recall
risk, mode + verbose-io trace

---

## Scenario anchoring approach (Lever 1)

| Option | Description | Selected |
|--------|-------------|----------|
| Full Context-Graph extraction (GraphCompliance) | Per-query scenario → entity triples → actor/data/system anchors | ✓ |
| Ontology-aligned multi-anchor decomposition (OMAGR) | Decompose query into legal dimensions; per-dimension Cypher | |
| Light query-entity extraction | Pull named entities from question, anchor to nodes | |

**User's choice:** GraphCompliance. *"focus on aligning with graphcompliance, not OMAGR."*
**Notes:** Corrected the initial either/or framing — Context-Graph extraction and multi-anchor
decomposition are different axes that can compose; user chose to follow the paper faithfully.
Also flagged: eval will eventually run on all 435 cases (18 is only the validation fixture) — this
reshapes cost constraints (mandatory F8 fix, temp 0, caching, benchmark-family generalization).

## Gating fork — pure GraphCompliance vs hybrid with Phase-10 ontology

| Option | Description | Selected |
|--------|-------------|----------|
| Pure GraphCompliance | CU/premise + REFERS_TO Policy Graph; 24-type ontology steps out of the loop | ✓ |
| Hybrid | CU layer primary, but keep 24-type relations (GOVERNS/REQUIRES/APPLIES_TO) as auxiliary edges | |

**User's choice:** Pure GraphCompliance (implied by "follow the paper step by step" + "align with
GraphCompliance"). **Notes:** Accepted consequence — consciously benches part of the Phase-10
ontology investment, justified by the paper's ablation (entity-ontology-in-retrieval adds nothing).

## Policy Graph construction sequence

**Established from paper §3.1 (verified against the PDF the user saved):** 3 stages —
(1) text classification (premise vs CU, three-way with meta-CU/actor-CU sub-typing),
(2) rule formalization (4-tuple ⟨subject, constraint, context, conditions⟩),
(3) relational linking (REFERS_TO via regex + small LLM).
Warm-start from Phase-10 function-type tags (Definition→premise, Scope→meta-CU, Control→actor-CU).

**Clause-count reconciliation (user challenged "691"):** file actually has 883 entries / 7 docs;
CCoP 2.0 = 415 (11 chapters + 51 sections + 353 leaves, 175 lettered sub-items). Operative-clause
count ≈ user's ~220 once structural headers are stripped. Structural headers → CONTAIN skeleton,
not CUs.

## Premise / CU model + where premises are used

**Established from paper §3.1/§3.2:** premise = non-deontic, never judged; CU = judged (4-tuple),
sub-typed actor-CU (judged) / meta-CU (applicability gate, evaluated first). Premises are a **build
artifact consumed at query time in hypernym mapping** (STRONG/WEAK, β=0.3 bonus) — not in CU
retrieval, not judged. Correction logged: STRONG bonus flows from the *definitional* premise
("CII means…"), not the Act §7 designation rule (a meta-CU).

## Retrieval mechanism (how the "top-3" is produced)

**Established:** GraphCompliance retrieves atomic **CUs**, not chunks — per-anchor bi-encoder over
CU `subject` (eq. 3) → cross-encoder rerank (eq. 4) → CU Plan. Kills Finding 8 by construction;
makes clause-hit@3 native. Judgment prompt = evidence window + CU Plan (4-tuple + verbatim text).

## Retrieval-recall risk (user's key challenge)

**User challenge:** *"i am not confident if the retrieved context sent to LLM will contain the
relevant text from the corpus… are you confident of achieving this?"*
**Resolution:** split into (A) recall and (B) payload; do NOT claim confidence-by-design. Mechanisms:
always-attach verbatim text; two-channel retrieval (anchor→subject + hybrid over verbatim clause
text — a deliberate divergence from pure GraphCompliance); deterministic pulls; fallback floor.
Confidence is **earned by measurement** via three gates (verbatim-text-in-prompt assertion,
clause-hit@3/recall@pool, B01-001 E2E slice first).

## Mode + verbose-io trace (user-requested)

**User request:** define a `--mode` for this setup; under `--verbose-io` show the query→clause
matching trace like the B01-001 walkthrough — Context Graph, anchors (from the query), matching
premises/meta-CUs/actor-CUs, then the embedded clauses.
**Resolution:** new `--mode graph-compliance` (additive; NOT `graphrag-*`); D-17 trace spec with the
exact four-part order. Wire into all three allowlists (multi-allowlist lesson).

---

## Claude's Discretion

- CU-node schema on Neo4j (new `:ComplianceUnit` layer vs upgrading `:Clause`) — leaning new layer.
- Embedding/cross-encoder models + K1/K/M/N/β hyperparameters (paper defaults as starting points).
- Cross-document deference edge modeling (REFERS_TO vs statutory-hierarchy type).
- ER-triple/anchor extraction prompt design + caching.

## Deferred Ideas

- Full 435-case A/B run + gold clause SETs for all 435.
- Phase-9 basic-graphrag 18-case baseline (fair-A/B dependency).
- OMAGR multi-anchor decomposition (not chosen; revisit if scenario anchoring under-recalls).
- MS GraphRAG global search (aggregation questions).
- Cross-document entity canonicalization (open, needs corpus validation).
- OWL reasoner / GT over-strictness review (carried from P10).
