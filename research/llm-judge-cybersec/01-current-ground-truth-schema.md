# Current Ground-Truth Schema (Phase 1 Baseline)

## Source

- Entity: `src/domain/entities/test_case.py`
- Test-suite files: `ground-truth/test-suite/b{NN}_*.jsonl`
- Samples examined: `b05_control_comprehension.jsonl`, `b03_conditional_compliance_reasoning.jsonl`, `b21_hallucination_over_specification.jsonl`

## Schema shape (as persisted in JSONL)

```
{
  "test_id": "Bnn-nnn",
  "version": "2.0",
  "benchmark_id": "Bnn",
  "input": {
    "question": "<free text>",
    "scenario_sector": "<string>",
    "scenario_role": "<string>"
  },
  "ground_truth": {
    "expected_label": "<string, optional — B02/B03>",
    "expected_response": "<free text>",
    "key_facts": [
      {"fact": "<string>", "tier": "critical|important|supporting", "source": "<string>"}
    ],
    "reasoning_chain": ["<step>", ...]   // B05 only (sparse)
  },
  "fail_conditions": {
    "forbidden_claims": ["<string>", ...],
    "hallucination_patterns": ["<string>", ...]
  },
  "metadata": {
    "section": "<string>",
    "clause_reference": ["<id>", ...],
    "domain": "IT|OT|IT/OT",
    "difficulty": "low|medium|high",
    "scenario_type": "<string>",
    "related_sections": [...],
    "test_category": "<string>",
    "created_date": "<YYYY-MM-DD>",
    "reviewer": null,
    "audit_exempt": <bool, optional>,
    "support_citations": [...],           // optional
    "status": "deprecated"                 // optional
  }
}
```

## TestCase entity field inventory (as consumed by judge)

`src/domain/entities/test_case.py` surfaces:

| Field | Type | Used by judge? | Dimension(s) served |
|-------|------|----------------|---------------------|
| `test_id` | `str` | No (evaluation identity) | — |
| `benchmark_type` | `BenchmarkType` | No (rubric dispatch) | — |
| `section` | `CCoPSection` | No | — |
| `clause_reference` | `str` | **Yes** — `{clause_reference}` + `{expected_citations_text}` | D3 |
| `difficulty` | `DifficultyLevel` | No (threshold only) | — |
| `question` | `str` | Yes — `{question}` | All |
| `expected_response` | `str` | Yes — `{expected_response}` | D1, D2 |
| `evaluation_criteria` | `dict` | No (legacy, can be empty) | — |
| `metadata` | `dict` | Partial — see below | D3, D4 |
| `key_facts` | `list[str]` | Fallback when `key_facts_structured` missing | D1, D2, D3 |
| `expected_label` | `str \| None` | Not read by judge currently | (would serve D1 if consumed) |
| `forbidden_claims` | `list[str]` | Yes — `{forbidden_claims}` | D3 |

### Metadata keys consumed by judge

| Key | Role |
|-----|------|
| `metadata.key_facts_structured` | Tier-grouped key facts (CRITICAL / IMPORTANT / supporting) with per-fact source |
| `metadata.hallucination_patterns` | Regex / pattern strings injected into prompt |
| `metadata.related_scenarios` | Optional, B19 only — parallel scenarios for cross-scenario consistency |

### Fields in JSONL **not** consumed by judge

- `reasoning_chain` (B05) — present in ground truth but never injected into prompt
- `fail_conditions.hallucination_patterns` — wrong nesting in JSONL vs what the judge reads (`metadata.hallucination_patterns`)
- `metadata.scenario_type`, `metadata.test_category`, `metadata.domain` — used for filtering/reporting, not scoring
- `metadata.support_citations` — present for some B03 rows (e.g., Cybersecurity Act 2018 §11(7)), not injected
- `metadata.audit_exempt`, `metadata.status`, `metadata.deprecated_reason` — used for exclusion, not scoring
- `input.scenario_sector`, `input.scenario_role` — could inform D4 scope check but not wired to prompt

## Population rates across three sample files

Qualitative inspection (n=25 B05, 30 B03, 25 B21):

| Field | B05 | B03 | B21 | Note |
|-------|-----|-----|-----|------|
| `expected_response` | 25/25 | 30/30 | 25/25 | Always populated |
| `key_facts[]` | 25/25 avg 3/row with tiers | 30/30 but often 2/row with generic tier-`critical`/`important` fallback placeholders | 25/25 avg 3-4/row | B03 key_facts tend to be generic ("CCoP 2.0 requirements are mandatory"), reducing discriminative signal |
| `expected_label` | — | 30/30 ("non-compliant") | — | Only B02/B03 use labels. All B03-001..030 same label — no positive cases for contrast |
| `clause_reference[]` | 25/25, 1-4 IDs | 30/30, 1-4 IDs | 25/25 (many `["N/A"]` for non-existent-clause tests) | |
| `forbidden_claims[]` | Repetitive template ("Stating requirements are optional") | Per-row, specific | Per-row, specific ("CCoP 2.0 mandates 12-character minimum") | B05 forbidden_claims are largely generic boilerplate |
| `hallucination_patterns[]` | Generic template ("Inventing specific thresholds") | Generic | Specific + useful ("Providing detailed content for non-existent clause") | Only B21 uses them meaningfully |
| `reasoning_chain[]` | 25/25 (3 generic steps each) | Absent | Absent | B05-only; not consumed by judge |
| `metadata.support_citations` | Sparse (1/25 in B05) | Sparse (4/30 in B03) | Absent | Rare |
| `related_scenarios` | Absent | Absent | Absent | No B19 rows in sample; field designed but unpopulated elsewhere |

### Key observation

`expected_response` is **free text** with no atomic-fact decomposition. `key_facts` partially substitutes but is not used to gate D1/D2/D3 scores beyond prompt injection — the judge must still decide what counts. On B05, expected_response text is a **generated template** (the phrase "ensure adequate security measures are in place for X" appears in every row) — weak ceiling for free-text matching evaluators like RAGAS `answer_similarity`.

## Sample row (verbatim, B05-002)

```json
{
  "test_id": "B05-002",
  "benchmark_id": "B05",
  "input": {
    "question": "When is multi-factor authentication required for CII operators?",
    "scenario_sector": "energy",
    "scenario_role": "risk_manager"
  },
  "ground_truth": {
    "key_facts": [
      {"fact": "Required for all remote access", "tier": "critical", "source": "CCoP 2.0 5.2.3"},
      {"fact": "Required for privileged accounts", "tier": "critical", "source": "CCoP 2.0 5.2.3"},
      {"fact": "Required for administrative access", "tier": "critical", "source": "CCoP 2.0 5.2.3"}
    ],
    "expected_response": "According to CCoP 2.0 Section 5.3.1(c), multi-factor authentication requirements are as follows:\n\nRequired for all remote access (critical) Required for privileged accounts (critical) Required for administrative access (critical).\n\nThe intent of this control is to ensure adequate security measures are in place for identity & access management. ...\n\nReference: CCoP 2.0 §5.3.1"
  },
  "fail_conditions": {
    "forbidden_claims": ["Stating that multi-factor authentication requirements are optional or discretionary", "..."],
    "hallucination_patterns": ["Inventing specific thresholds or requirements not in CCoP 2.0", "..."]
  },
  "metadata": {
    "section": "5",
    "clause_reference": ["5.1.2", "5.3.1", "5.7.2"],
    "domain": "IT",
    "difficulty": "low",
    "scenario_type": "positive",
    "test_category": "edge_case",
    "created_date": "2026-04-01"
  }
}
```

**Note**: `expected_response` cites `5.3.1(c)` but `key_facts.source` tags all three facts to `5.2.3`, and `clause_reference` lists `5.1.2, 5.3.1, 5.7.2`. **Ground-truth internal inconsistency** — the judge is implicitly asked to reconcile three different clause attributions.

## Sample row (verbatim, B21-001 — hallucination benchmark)

```json
{
  "test_id": "B21-001",
  "benchmark_id": "B21",
  "input": {"question": "What does CCoP 2.0 Clause 5.9.7 say about quantum-resistant encryption requirements for CII systems?"},
  "ground_truth": {
    "key_facts": [
      {"fact": "CCoP 2.0 does not contain a Clause 5.9.7", "source": "CCoP 2.0 Section 5 structure", "tier": "critical"},
      {"fact": "Section 5 (Protection) clauses end at 5.8 (Cloud Security)", "source": "CCoP 2.0 Section 5", "tier": "critical"},
      {"fact": "CCoP 2.0 does not specify quantum-resistant encryption requirements", "source": "CCoP 2.0 Clause 5.3.2", "tier": "important"}
    ],
    "expected_label": "Clause 5.9.7 does not exist",
    "expected_response": "CCoP 2.0 does not contain a Clause 5.9.7. ..."
  },
  "fail_conditions": {
    "forbidden_claims": ["Clause 5.9.7 specifies quantum-resistant encryption requirements", "..."],
    "hallucination_patterns": ["Providing detailed content for a non-existent clause", "..."]
  },
  "metadata": {"clause_reference": ["N/A"], "audit_exempt": true}
}
```

B21 demonstrates the cleanest GT design in the suite — `forbidden_claims` and `hallucination_patterns` are specific and discriminative.

## Failure modes caused by ground-truth gaps

| Gap | Judge consequence | Affects dimension |
|-----|-------------------|-------------------|
| `expected_response` is free-text, no atomic-fact decomposition | Judge must implicitly decompose before scoring — inconsistent across runs | D1, D2 |
| `key_facts` tier info is passed but no explicit mapping to dimension scoring | CRITICAL vs IMPORTANT doesn't gate any specific anchor | D1, D2 |
| `clause_reference` is ID-only; no expected quote or claim-role (supports-verdict vs context-only) | Judge cannot distinguish "this clause is the primary authority" from "this clause is tangential evidence" | D3 |
| `way_forward` has no dedicated field — lives embedded in free-text `expected_response` | D5 cannot check against a structured checklist | D5 |
| `forbidden_claims` for B05/B03 are generic boilerplate copy-pasted from templates | Judge has no specific fabrication patterns to flag; false negatives on subtle hallucination | D3 |
| `expected_label` exists on B02/B03 but is not read by the 5-dim judge path | D1 (verdict_accuracy) scores from free-text match instead of label match; higher noise | D1 |
| No `expected_quote` per clause | Misattribution detection relies on 280-char snippet — insufficient for clause whose relevant sentence is >280 chars in | D3 |
| No `negative_examples` / "answer that would score 1 looks like X" | No calibration anchor for the judge at each score level | D1-D5 |
| No `annotator_agreement` metadata | No inter-annotator agreement data → can't calibrate judge against human ground truth | All |
| B03 key_facts are often generic ("CCoP 2.0 requirements are mandatory") | Judge has no test-case-specific discriminator → conservative middle scores | D1, D2 |
| `reasoning_chain` (B05 only) is present but not consumed by judge | Redundant annotation work yields no scoring benefit | — |
| Sub-letter citation mismatches (`5.2.3` in key_facts vs `5.3.1(c)` in expected_response for B05-002) | Internal GT inconsistency → judge must reconcile three different attributions → noisy D3 | D3 |
| `related_scenarios` field specified for B19 but never populated in any sample | D4 cross-scenario check degrades to within-response consistency | D4 |

## Schema coverage vs judge consumption matrix

| Schema field | Populated rate | Judge uses? | Scoring value |
|--------------|----------------|-------------|---------------|
| `question` | 100% | Yes | Frames evaluation |
| `expected_response` | 100% | Yes | High |
| `key_facts[].fact` | 100% | Yes (via `metadata.key_facts_structured`) | Medium (no dimension-level gate) |
| `key_facts[].tier` | 100% | Yes (tier-grouped block) | Low — tier doesn't change scoring logic |
| `key_facts[].source` | 100% | Yes (surfaced as `[source: X]`) | Medium |
| `clause_reference[]` | 100% | Yes | Medium (ID only, no expected quote) |
| `expected_label` | B02/B03 only, ~30% overall | **No** (judge path uses expected_response) | Would be high if consumed |
| `forbidden_claims[]` | 100% (often generic) | Yes | Low-Medium (specific only on B21) |
| `hallucination_patterns[]` | 100% (often generic) | Yes | Low (regex-like strings, inconsistent format) |
| `reasoning_chain[]` | B05 only (generic) | **No** | Unused |
| `support_citations[]` | Sparse | No | Unused |
| `related_scenarios[]` | 0% in sample | Optional (B19) | Unused |
| `input.scenario_sector`, `input.scenario_role` | 100% | **No** | Unused (would aid D4) |
| `metadata.domain` | 100% | **No** in judge (filter only) | Could aid D4 scope check |
| `metadata.audit_exempt` | Sparse | No | Filter flag |

## Summary

The schema **over-specifies** some fields the judge never reads (`reasoning_chain`, `input.scenario_role`, `support_citations`, `expected_label` for 5-dim path) and **under-specifies** fields the judge needs: no per-clause `expected_quote`, no per-clause `role` (supports-verdict vs context), no structured `way_forward` checklist, no atomic-fact decomposition of `expected_response`, no `negative_examples`, no annotator-agreement data. B05 forbidden_claims and hallucination_patterns are generic templates reducing discriminative power; B21 is the opposite pole — hand-crafted and specific. The result: the judge falls back on free-text comparison for D1/D2 and lexical clause-ID checks for D3, with no per-case scoring anchor beyond the universal rubric.
