# Phase 10: Ontology-grounded GraphRAG - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-02
**Phase:** 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2
**Areas discussed:** Ontology method & §3.2.2 paper, Retrieval relevance-routing, Validation depth & curation gates, A/B scope & Phase 9 baseline, Ontology construction next-steps

> Note: most Phase 10 gray areas were deep-dived in the preceding working session (chunking research,
> the five-methods article, the Phase 9 emergent-entity audit). Those decisions are carried into
> CONTEXT.md directly (D-01…D-11). This log records the four open areas selected for lock-down.

---

## Ontology method & §3.2.2 paper

| Option | Description | Selected |
|--------|-------------|----------|
| Use our C→B approach | Grounded synthesis (C) + clustering cross-check (B) + user curation; treat §3.2.2 as inspiration; proceed now | ✓ |
| I'll provide the §3.2.2 paper | Follow a specific Text Ontology Learning method once supplied | |
| Hybrid — C→B now, reconcile with paper later | Start C→B, fold paper method in at curation gate if surfaced | |

**User's choice:** Use our C→B approach.
**Notes:** §3.2.2 paper not available; treated as inspiration, not a prescription (CONTEXT D-03).

---

## Retrieval relevance-routing

| Option | Description | Selected |
|--------|-------------|----------|
| Function-type routing | Classify question intent → prefer clauses tagged with matching function-type | ✓ (best-judgment, pending confirmation) |
| Entity-anchored traversal | Extract entities → traverse to governing clauses | |
| Both, layered | Function-type + entity traversal combined | (noted as richer future option) |
| Start minimal, let the gate drive | Clause-node dense retrieval first; add routing only if clause-hit@3 shows need | |

**User's choice:** No response within 60s — proceeded with best judgment (Function-type routing).
**Notes:** Marked pending user confirmation in CONTEXT D-12. This is the lever that fixes ranking
(§1.2.1 over §5.6); grounding/clause-nodes alone do not.

---

## Validation depth & curation gates

**Resolved by best judgment from prior discussion (no separate question asked):**
- SHACL now (locked, P9 D-16); OWL reasoner as a stretch goal ("SHACL minimum, OWL ideal").
- Two human curation gates: after the Method-C draft, and after the Method-B reconcile.
- Build gated on user approval + benchmark coverage check. (CONTEXT D-13, D-14.)

---

## A/B scope & Phase 9 baseline

**Resolved by best judgment from prior discussion (no separate question asked):**
- A/B = graphrag-ontology vs basic graphrag vs hybrid on the 18-case GT.
- Hard dependency: the basic-GraphRAG baseline is the deferred Phase 9 Wave 6 (only B01-001 run,
  n=1). Flagged; no ontology-effect claim trustworthy until it exists.
- Deciding signals: clause-hit@3 + LLM-judge citation/grounding dims + RAGAs context metrics.
  (CONTEXT D-15, D-16.)

---

## Ontology construction next-steps (user freeform question)

User asked what happens after C→B. Documented as the Wave-1 pipeline in CONTEXT (D-01…D-14):
reconcile C vs B → lock → SHACL shapes → seed 691 clauses → schema-constrained extraction + gleaning
→ entity resolution/filter → link to clauses → SHACL/OWL validate → clause-anchored retrieval +
routing → clause-hit@3 gate + A/B.

---

## Claude's Discretion

- Method B embedding model + clustering algorithm (AP suggested); corpus term-extraction strategy.
- SHACL shape authoring; entity-resolution algorithm.
- `--mode graphrag-ontology` naming / provider wiring.
- D-12 (function-type routing) — best-judgment pending user confirmation.

## Deferred Ideas

- Phase 9 Wave 6 (18-case comparison) — deferred but a hard dependency for the A/B.
- "Both, layered" routing (function-type + entity traversal) — richer future option.
- OWL reasoner — stretch beyond SHACL.
- GT over-strictness review (single-clause GT for multi-clause reasoning questions).
- ADR-006 not implemented (judge still reads forbidden_claims) — unrelated, tracked.
