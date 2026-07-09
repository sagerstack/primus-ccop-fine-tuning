# GT Audit — Clause Inventory Validation (step zero)

**Date:** 2026-06-29
**Goal:** Before re-auditing the ground truth, validate the authority everything should be
checked against — `src/rag/ingestion/fixtures/clause_inventory.json` — for completeness and
accuracy against the CCoP 2.0 source PDF. Motivated by `04_judge_ragas_scoring_critique.md`:
wholesale LLM audits don't converge because nothing binds to a single trusted clause registry.

## Method (deterministic, code-only — no LLM judgment)

- Inventory: `clause_inventory.json` (`generated_at` 2026-04-30; regenerated during the
  agent-team corrections). 883 entries across 7 source docs; **415 are CCoP 2.0**.
- Source: `ccop-official/CCoP---Second-Edition_Revision-One.pdf` → `pdftotext -layout`.
- Parsed PDF body clause headings (excluding TOC dotted-leader lines), set-diffed against the
  inventory in both directions; spot-verified contested clauses and sub-letter completeness.

## Verdict: inventory is accurate, complete, and trustworthy

| Check | Result |
|---|---|
| CCoP 2.0 entries | 415 (229 numeric + 175 sub-letter + section-level) |
| Deep numeric clauses (≥3-level) present in PDF | **178 / 178** |
| Numeric clauses in PDF missing from inventory | **0** (`1.0`/`2.0` are parse artifacts) |
| Inventory sub-letters with no PDF bullet | **0 / 175** |
| Sub-letter spot-check | `4.1.1(a–j)`, `5.7.2(a–f)`, `5.3.1(a–d)`, `10.4.1(a–e)` — all match |
| Hallucinated-in-GT clauses correctly excluded | `5.1.5`, `5.2.3`, `5.3.2`, `5.3.3`, `8.3`, `5.9.7`, `11.3` → all absent |

**The inventory correctly excludes every fabricated clause the ground truth cites — it is more
correct than the GT itself.** It can serve as the deterministic validation authority immediately.

## Re-diagnosis: the inventory is not the defect; two consumers diverge from it

1. **Ground truth** cites clauses absent from the inventory (`5.1.5`, `8.3`, `5.9.7`, `5.2.3`…)
   → the GT-hallucination defect class (`bugs.md` D5; doc 04 S-2/B02/B21/B24).
2. **Qdrant RAG corpus** is missing the §5.3/§5.4 sub-clause *bodies* (`bugs.md` 2026-04-21).
   The clause `5.3.1(c)` is **real and in the inventory**, but its body was never chunked, so the
   retriever cannot surface it → `context_recall = 0` for any GT grounded on §5.3/§5.4.

Clarification of a prior note: §5.3 (Privileged Access Management) and §5.4 (Domain Controller)
**exist** in the PDF and inventory. `bugs.md`'s "5.3/5.4 missing" referred to the **vector index**,
not the document or the registry.

## Implications

- **Step zero is done.** No registry to build — bind the GT-fix pipeline and the judge's citation
  verifier to `clause_inventory.json` directly.
- **Two concrete, now-unblocked fixes:**
  1. Validate every GT clause citation (`clause_reference`, `expected_response`, `key_facts.source`)
     against the inventory → deterministically catches the entire hallucinated-clause class.
  2. Re-index Qdrant so §5.3/§5.4 sub-clause bodies are emitted as their own points → fixes
     `context_recall=0` on B03/B07/B12-family cases.

## Residual / not-yet-done

- Validated **CCoP 2.0 only.** The other 6 inventory source docs (Response to Feedback,
  Cybersecurity Act 2018, Auditing Guidelines, Risk Assessment Guide, Threat Modelling, Security
  By Design) are not yet cross-checked against their PDFs. The GT also cites these → bounded follow-up.
- Sub-letter parent-attribution was checked leniently (the `(x)` bullet exists somewhere, not
  provably under the right parent). No evidence of misattribution, but not exhaustively proven.
