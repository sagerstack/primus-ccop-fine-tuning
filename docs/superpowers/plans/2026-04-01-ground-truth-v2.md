# Ground Truth V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the v1 ground truth (118 test cases, inconsistent schema, 21 benchmarks) with a research-informed v2 ground truth (~435 test cases, unified schema, ~18 benchmarks) targeting Risk Managers in CII organizations.

**Architecture:** Two parallel streams (schema design + benchmark audit) merge into test case generation. V2 uses nested JSON format with tiered key_facts, reasoning chains, and fail conditions. The JSONL repository parser and TestCase entity are updated to handle v2 format while remaining backward-compatible with v1 during transition.

**Tech Stack:** Python 3.13, Poetry, jsonschema, openpyxl, pytest

**Spec:** `docs/superpowers/specs/2026-04-01-ground-truth-v2-design.md`
**Research:** `artifacts/research/2026-04-01-llm-eval-ground-truth-quality-deep-dive.md`, `artifacts/research/2026-04-01-singapore-ciio-ccop-practices-deep-dive.md`

---

## Task 1: Archive V1 Ground Truth and Set Up V2 Directory Structure

**Files:**
- Move: `ground-truth/phase-2/test-suite/*` → `ground-truth/archive/phase-2/test-suite/`
- Move: `ground-truth/phase-2/expert-validation/*` → `ground-truth/archive/phase-2/expert-validation/`
- Create: `ground-truth/test-suite/` (empty, will hold v2 JSONL files)
- Create: `ground-truth/schema/` (will hold JSON schema + validator)
- Create: `ground-truth/expert-validation/` (will hold v2 expert review)

- [ ] **Step 1: Create v2 directory structure**

```bash
mkdir -p ground-truth/archive/phase-2/test-suite
mkdir -p ground-truth/archive/phase-2/expert-validation
mkdir -p ground-truth/test-suite
mkdir -p ground-truth/schema
mkdir -p ground-truth/expert-validation
```

- [ ] **Step 2: Move v1 test suite files to archive**

```bash
mv ground-truth/phase-2/test-suite/*.jsonl ground-truth/archive/phase-2/test-suite/
```

- [ ] **Step 3: Move v1 expert validation files to archive**

```bash
mv ground-truth/phase-2/expert-validation/expert_validation_review.md ground-truth/archive/phase-2/expert-validation/
mv ground-truth/phase-2/expert-validation/generate_expert_review_excel.py ground-truth/archive/phase-2/expert-validation/
mv ground-truth/phase-2/expert-validation/CCoP_Test_Cases_Expert_Review.xlsx ground-truth/archive/phase-2/expert-validation/
```

Note: Skip any `~$` temp files (Excel lock files).

- [ ] **Step 4: Remove empty v1 directories**

```bash
rmdir ground-truth/phase-2/test-suite 2>/dev/null || true
rmdir ground-truth/phase-2/expert-validation 2>/dev/null || true
rmdir ground-truth/phase-2 2>/dev/null || true
```

- [ ] **Step 5: Verify structure**

```bash
find ground-truth -type f | head -30
```

Expected: All JSONL files under `ground-truth/archive/phase-2/test-suite/`, empty `ground-truth/test-suite/`, `ground-truth/schema/`, `ground-truth/expert-validation/`.

- [ ] **Step 6: Commit**

```bash
git add ground-truth/
git commit -m "chore: archive v1 ground truth, set up v2 directory structure

Move 21 JSONL test suite files and expert validation artifacts
to ground-truth/archive/phase-2/. Create empty v2 directories
for test-suite, schema, and expert-validation."
```

---

## Task 2: Create V2 JSON Schema Definition

**Files:**
- Create: `ground-truth/schema/test-case-v2.schema.json`
- Test: `tests/ground_truth/test_schema_validation.py`

- [ ] **Step 1: Write the v2 JSON schema**

Create `ground-truth/schema/test-case-v2.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CCoP Ground Truth Test Case V2",
  "description": "Schema for CCoP 2.0 evaluation ground truth test cases (v2)",
  "type": "object",
  "required": ["test_id", "version", "benchmark_id", "input", "ground_truth", "fail_conditions", "metadata"],
  "additionalProperties": false,
  "properties": {
    "test_id": {
      "type": "string",
      "pattern": "^B\\d{1,2}-\\d{3}$",
      "description": "Unique test case identifier (e.g., B3-015)"
    },
    "version": {
      "type": "string",
      "const": "2.0"
    },
    "benchmark_id": {
      "type": "string",
      "pattern": "^B\\d{1,2}$",
      "description": "Benchmark identifier (e.g., B3)"
    },
    "input": {
      "type": "object",
      "required": ["question", "scenario_sector", "scenario_role"],
      "additionalProperties": false,
      "properties": {
        "question": {
          "type": "string",
          "minLength": 50,
          "description": "Scenario-grounded compliance question"
        },
        "scenario_sector": {
          "type": "string",
          "enum": ["energy", "water", "banking", "healthcare", "aviation", "transport", "maritime", "telecoms", "government", "media", "security", "cross-sector"],
          "description": "CII sector context"
        },
        "scenario_role": {
          "type": "string",
          "enum": ["risk_manager", "employee"],
          "description": "Question perspective"
        }
      }
    },
    "ground_truth": {
      "type": "object",
      "required": ["expected_response", "key_facts"],
      "additionalProperties": false,
      "properties": {
        "expected_label": {
          "type": ["string", "null"],
          "description": "Classification label (required for rule-based benchmarks, optional for LLM-judge)"
        },
        "expected_response": {
          "type": "string",
          "minLength": 50,
          "description": "Reference answer (100-250 words recommended)"
        },
        "key_facts": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "required": ["fact", "source", "tier"],
            "additionalProperties": false,
            "properties": {
              "fact": {
                "type": "string",
                "minLength": 10,
                "description": "Atomic, independently verifiable claim"
              },
              "source": {
                "type": "string",
                "description": "CCoP clause, Act section, or 'Regulatory interpretation'"
              },
              "tier": {
                "type": "string",
                "enum": ["critical", "important", "supporting"]
              }
            }
          }
        },
        "reasoning_chain": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Ordered reasoning steps (required for LLM-judge benchmarks)"
        },
        "acceptable_variations": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Valid alternative framings"
        }
      }
    },
    "fail_conditions": {
      "type": "object",
      "required": ["forbidden_claims", "hallucination_patterns"],
      "additionalProperties": false,
      "properties": {
        "forbidden_claims": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Claims that indicate hallucination or dangerous advice"
        },
        "hallucination_patterns": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Categories of fabrication to detect"
        }
      }
    },
    "metadata": {
      "type": "object",
      "required": ["section", "clause_reference", "domain", "difficulty", "test_category", "created_date"],
      "additionalProperties": true,
      "properties": {
        "section": {
          "type": "string",
          "description": "CCoP 2.0 section reference"
        },
        "clause_reference": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Specific clause numbers"
        },
        "domain": {
          "type": "string",
          "enum": ["IT", "OT", "IT/OT"]
        },
        "difficulty": {
          "type": "string",
          "enum": ["low", "medium", "high"]
        },
        "scenario_type": {
          "type": "string",
          "description": "Taxonomy of scenario pattern"
        },
        "related_sections": {
          "type": "array",
          "items": { "type": "string" }
        },
        "test_category": {
          "type": "string",
          "enum": ["positive", "negative", "edge_case", "adversarial"]
        },
        "created_date": {
          "type": "string",
          "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
        },
        "reviewer": {
          "type": ["string", "null"]
        }
      }
    }
  }
}
```

- [ ] **Step 2: Verify schema is valid JSON**

```bash
cd src && poetry run python -c "import json; json.load(open('../ground-truth/schema/test-case-v2.schema.json')); print('Valid JSON')"
```

Expected: `Valid JSON`

- [ ] **Step 3: Commit**

```bash
git add ground-truth/schema/test-case-v2.schema.json
git commit -m "feat: add v2 ground truth JSON schema definition

Defines nested schema with separated concerns: input, ground_truth
(tiered key_facts, reasoning_chain, acceptable_variations),
fail_conditions, and metadata. Supports both rule-based and
LLM-judge scoring paths."
```

---

## Task 3: Create Schema Validator Script

**Files:**
- Create: `ground-truth/schema/validate.py`
- Test: Run against a sample test case

- [ ] **Step 1: Write the validator script**

Create `ground-truth/schema/validate.py`:

```python
#!/usr/bin/env python3
"""
V2 Ground Truth Schema Validator

Validates JSONL test case files against test-case-v2.schema.json.
Runs both JSON Schema validation and business rule checks.

Usage:
    python validate.py                          # Validate all files in ../test-suite/
    python validate.py --file ../test-suite/b03_conditional_compliance_reasoning.jsonl
    python validate.py --strict                 # Fail on warnings too
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError


def load_schema() -> dict:
    schema_path = Path(__file__).parent / "test-case-v2.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_business_rules(test_case: dict, warnings: list[str], errors: list[str]) -> None:
    """Business rules beyond what JSON Schema can enforce."""
    test_id = test_case.get("test_id", "UNKNOWN")
    benchmark_id = test_case.get("benchmark_id", "")

    # Rule: test_id prefix must match benchmark_id
    if not test_id.startswith(f"{benchmark_id}-"):
        errors.append(f"{test_id}: test_id prefix does not match benchmark_id '{benchmark_id}'")

    # Rule: reasoning benchmarks need reasoning_chain
    rule_based_benchmarks = {"B1", "B2", "B4", "B21"}
    ground_truth = test_case.get("ground_truth", {})
    if benchmark_id not in rule_based_benchmarks:
        if not ground_truth.get("reasoning_chain"):
            warnings.append(f"{test_id}: LLM-judge benchmark missing reasoning_chain")
        if not ground_truth.get("acceptable_variations"):
            warnings.append(f"{test_id}: LLM-judge benchmark missing acceptable_variations")

    # Rule: rule-based benchmarks need expected_label
    if benchmark_id in rule_based_benchmarks:
        if not ground_truth.get("expected_label"):
            errors.append(f"{test_id}: rule-based benchmark missing expected_label")

    # Rule: minimum 2 critical-tier key_facts for reasoning benchmarks
    key_facts = ground_truth.get("key_facts", [])
    critical_count = sum(1 for kf in key_facts if kf.get("tier") == "critical")
    if benchmark_id not in rule_based_benchmarks and critical_count < 2:
        warnings.append(
            f"{test_id}: reasoning benchmark has {critical_count} critical key_facts (recommend >= 2)"
        )

    # Rule: forbidden_claims should not be empty
    fail_conditions = test_case.get("fail_conditions", {})
    if not fail_conditions.get("forbidden_claims"):
        warnings.append(f"{test_id}: no forbidden_claims defined")


def validate_file(filepath: Path, schema: dict, strict: bool = False) -> tuple[int, int, int]:
    """Validate a single JSONL file. Returns (valid_count, warning_count, error_count)."""
    validator = Draft202012Validator(schema)
    valid_count = 0
    warning_count = 0
    error_count = 0
    seen_ids: set[str] = set()

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                test_case = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  ERROR line {line_num}: Invalid JSON — {e}")
                error_count += 1
                continue

            test_id = test_case.get("test_id", f"line-{line_num}")

            # Duplicate ID check
            if test_id in seen_ids:
                print(f"  ERROR {test_id}: Duplicate test_id")
                error_count += 1
            seen_ids.add(test_id)

            # JSON Schema validation
            schema_errors = list(validator.iter_errors(test_case))
            if schema_errors:
                for err in schema_errors:
                    path = ".".join(str(p) for p in err.absolute_path) or "(root)"
                    print(f"  ERROR {test_id} [{path}]: {err.message}")
                error_count += len(schema_errors)
                continue

            # Business rule validation
            warnings: list[str] = []
            biz_errors: list[str] = []
            validate_business_rules(test_case, warnings, biz_errors)

            for w in warnings:
                print(f"  WARN  {w}")
                warning_count += 1

            for e in biz_errors:
                print(f"  ERROR {e}")
                error_count += 1

            if not schema_errors and not biz_errors:
                valid_count += 1

    return valid_count, warning_count, error_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate v2 ground truth test cases")
    parser.add_argument("--file", type=Path, help="Validate a single JSONL file")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    schema = load_schema()
    test_suite_dir = Path(__file__).parent.parent / "test-suite"

    if args.file:
        files = [args.file]
    else:
        files = sorted(test_suite_dir.glob("b*.jsonl"))
        if not files:
            print(f"No JSONL files found in {test_suite_dir}")
            sys.exit(1)

    total_valid = 0
    total_warnings = 0
    total_errors = 0

    for filepath in files:
        print(f"\n--- {filepath.name} ---")
        valid, warnings, errors = validate_file(filepath, schema, args.strict)
        total_valid += valid
        total_warnings += warnings
        total_errors += errors
        print(f"  Result: {valid} valid, {warnings} warnings, {errors} errors")

    print(f"\n=== TOTAL: {total_valid} valid, {total_warnings} warnings, {total_errors} errors ===")

    if total_errors > 0 or (args.strict and total_warnings > 0):
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create a sample v2 test case to validate against**

Create `ground-truth/test-suite/b03_conditional_compliance_reasoning.jsonl` with one test case:

```jsonl
{"test_id":"B3-001","version":"2.0","benchmark_id":"B3","input":{"question":"Your organization uses shared admin accounts with session logging for CII SCADA systems because the legacy HMIs don't support individual authentication. The CISO argues this satisfies CCoP access control requirements through compensating controls. Does this approach comply with CCoP 2.0?","scenario_sector":"energy","scenario_role":"risk_manager"},"ground_truth":{"expected_label":"non-compliant","expected_response":"Shared admin accounts on CII SCADA systems do not comply with CCoP 2.0 access control requirements, even with session logging as a compensating control. Clause 5.3.1(c) mandates individual accountability for privileged access to CII systems. Shared accounts fundamentally prevent attribution of actions to specific individuals, which is the core requirement. Session logging is a detective control — it records what happened but cannot prevent unauthorized actions or establish who performed them. Detective controls cannot substitute for the preventive requirement of individual authentication. The appropriate path is to pursue a waiver under Section 11(7) of the Cybersecurity Act, documenting that the legacy HMIs genuinely cannot support individual accounts, proposing compensating controls (session logging, physical access restrictions, dual-operator procedures), and setting a timeline for system upgrade or replacement. The existing monitoring controls should be retained as defense-in-depth alongside any future MFA implementation.","key_facts":[{"fact":"Clause 5.3.1(c) requires individual accountability for privileged access to CII systems","source":"CCoP 2.0 Section 5.3.1(c)","tier":"critical"},{"fact":"Shared admin accounts prevent individual attribution of actions, violating accountability requirements","source":"Regulatory interpretation","tier":"critical"},{"fact":"Session logging is a detective control that cannot replace the preventive requirement of individual authentication","source":"CCoP 2.0 defense-in-depth principle","tier":"important"},{"fact":"A waiver under Section 11(7) should be pursued if legacy HMIs genuinely cannot support individual accounts","source":"Cybersecurity Act Section 11(7)","tier":"supporting"}],"reasoning_chain":["Identify that shared admin accounts on CII systems involve privileged access","Recall that CCoP 2.0 requires individual accountability for privileged access","Evaluate whether compensating controls (session logging) satisfy the accountability mandate","Conclude that detective controls cannot substitute for the preventive requirement","Recommend the waiver mechanism for genuinely infeasible requirements"],"acceptable_variations":["May recommend PAM tooling as an alternative to individual HMI accounts","May reference the OT addendum for legacy system considerations","May suggest jumpbox architecture as a compensating control pathway"]},"fail_conditions":{"forbidden_claims":["Shared admin accounts with logging satisfy CCoP access control requirements","Compensating controls can always replace mandated controls"],"hallucination_patterns":["Citing non-existent CCoP clauses","Attributing requirements from other frameworks as CCoP mandates"]},"metadata":{"section":"Section 5: Protection","clause_reference":["5.3.1"],"domain":"OT","difficulty":"high","scenario_type":"compensating_controls_insufficient","related_sections":["5.2.1","OT Addendum"],"test_category":"negative","created_date":"2026-04-01","reviewer":null}}
```

- [ ] **Step 3: Install jsonschema dependency**

```bash
cd src && poetry add jsonschema
```

- [ ] **Step 4: Run validator on the sample file**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b03_conditional_compliance_reasoning.jsonl
```

Expected:
```
--- b03_conditional_compliance_reasoning.jsonl ---
  Result: 1 valid, 0 warnings, 0 errors

=== TOTAL: 1 valid, 0 warnings, 0 errors ===
```

- [ ] **Step 5: Commit**

```bash
git add ground-truth/schema/validate.py ground-truth/test-suite/b03_conditional_compliance_reasoning.jsonl
git commit -m "feat: add v2 schema validator and first sample test case

Validator runs JSON Schema + business rules (test_id prefix match,
reasoning_chain for LLM-judge benchmarks, critical key_facts count,
expected_label for rule-based benchmarks). Includes B3-001 sample."
```

---

## Task 4: Benchmark Audit and Registry

**Files:**
- Create: `docs/phase-2/benchmark-registry.md`
- Read: All 21 archived v1 JSONL files for audit
- Read: `artifacts/research/2026-04-01-singapore-ciio-ccop-practices-deep-dive.md`

This task produces the benchmark registry document. It requires critical analysis, not code. The executor should:

- [ ] **Step 1: Read all 21 archived v1 test suite files**

Read each file in `ground-truth/archive/phase-2/test-suite/` and note: test case count, question quality, key_facts quality, and coverage gaps.

- [ ] **Step 2: Read the CIIO research**

Read `artifacts/research/2026-04-01-singapore-ciio-ccop-practices-deep-dive.md` for sector-specific scenarios and Risk Manager questions that should inform benchmark relevance.

- [ ] **Step 3: Apply audit criteria to each benchmark**

For each of the 21 v1 benchmarks, evaluate against:
- **CIIO Relevance**: Does this test something a Risk Manager needs?
- **Distinctiveness**: Does this measure something unique?
- **Scorer Alignment**: Does current scoring infrastructure evaluate this effectively?
- **Question Feasibility**: Can 20+ scenario-grounded questions be written?
- **Evaluation Clarity**: Clear distinction between good and bad responses?

- [ ] **Step 4: Write the benchmark registry**

Create `docs/phase-2/benchmark-registry.md` with the final benchmark set. Use the decisions from the spec (Section 2: Benchmark Audit) as the starting point, but adjust based on audit findings:

```markdown
# CCoP 2.0 Evaluation Benchmark Registry (V2)

## Overview

18 benchmarks organized by compliance reasoning capability.
Reduced from 21 v1 benchmarks through merging, removal, and addition
based on CIIO research and benchmark audit.

## Changes from V1

### Merges
| V1 Benchmarks | V2 Benchmark | Rationale |
|---------------|-------------|-----------|
| B8 + B11 | B8 Risk-Based Prioritization | ... |
| B14 + B15 | B14 Remediation Quality & Feasibility | ... |
| B9 + B16 | B9 Risk Identification & Residual Risk | ... |

### Removed / Absorbed
| V1 Benchmark | Absorbed Into | Rationale |
|-------------|---------------|-----------|
| B17 | B7 | ... |
| B19 | Cross-benchmark quality check | ... |
| B20 | B21 | ... |

### New
| Benchmark | Rationale |
|-----------|-----------|
| B22 Waiver & Exception Reasoning | ... |
| B23 Multi-Regulator Coordination | ... |
| B24 Incident Response Guidance | ... |

## Benchmark Definitions

### B1 — CCoP Applicability & Scope
- **Scoring path:** Rule-based
- **Description:** ...
- **V2 changes:** Added CCoP 1.0 evolution, IM8 context, ESCI/STCC/FDI awareness
- **Target count:** 25
- **Key CCoP sections:** Preamble, Cybersecurity Act

[Repeat for all 18 benchmarks]
```

- [ ] **Step 5: Commit**

```bash
git add docs/phase-2/benchmark-registry.md
git commit -m "docs: add v2 benchmark registry from audit

18 benchmarks: 8 kept, 6 refocused, 3 merged pairs, 3 removed,
3 new (waiver reasoning, multi-regulator, incident response).
Based on CIIO research and 5-criteria audit."
```

---

## Task 5: Triage Existing 118 Test Cases

**Files:**
- Read: All 21 files in `ground-truth/archive/phase-2/test-suite/`
- Create: `ground-truth/archive/phase-2/triage-report.md`

This task produces a triage report classifying each existing test case as keep/revise/discard, and mapping kept cases to v2 benchmark IDs.

- [ ] **Step 1: Read all v1 test cases**

Load every test case from the 21 archived JSONL files. For each, assess:
- **Question quality**: Is it scenario-grounded and practitioner-relevant?
- **Ground truth quality**: Is expected_response accurate and detailed enough?
- **Key facts quality**: Are key_facts present, atomic, and sourced? Or placeholder?
- **Benchmark mapping**: Does this test case map to a v2 benchmark? If the v1 benchmark was merged/removed, which v2 benchmark absorbs it?

- [ ] **Step 2: Classify each test case**

| Classification | Criteria | Action |
|----------------|----------|--------|
| **Keep** | Good question, decent ground truth, maps to v2 benchmark | Migrate to v2 schema: enrich key_facts with source/tier, add fail_conditions, add reasoning_chain |
| **Revise** | Good concept but question needs rewriting for practitioner grounding | Rewrite question, reconstruct ground truth in v2 format |
| **Discard** | Too abstract, definitional, placeholder key_facts, or benchmark removed without absorption | Do not migrate |

- [ ] **Step 3: Write triage report**

Create `ground-truth/archive/phase-2/triage-report.md`:

```markdown
# V1 Test Case Triage Report

## Summary
- Total v1 test cases: 118
- Keep: XX (XX%)
- Revise: XX (XX%)
- Discard: XX (XX%)

## Per-Benchmark Triage

### B1 — CCoP Applicability & Scope (8 cases)
| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|-------------|-------|
| B1-001 | Keep | B1 | Good scenario, needs key_facts enrichment |
| B1-002 | Revise | B1 | Too definitional, needs practitioner framing |
| ... | ... | ... | ... |

[Repeat for all 21 v1 benchmarks]
```

- [ ] **Step 4: Commit**

```bash
git add ground-truth/archive/phase-2/triage-report.md
git commit -m "docs: triage 118 v1 test cases for v2 migration

Classify each test case as keep/revise/discard with v2 benchmark
mapping and migration notes."
```

---

## Task 6: Generate V2 Test Cases — Rule-Based Benchmarks (B1, B2, B4, B21)

**Files:**
- Create/Modify: `ground-truth/test-suite/b01_ccop_applicability_scope.jsonl`
- Create: `ground-truth/test-suite/b02_compliance_classification.jsonl`
- Create: `ground-truth/test-suite/b04_it_ot_classification_boundary.jsonl`
- Create: `ground-truth/test-suite/b21_hallucination_over_specification.jsonl`

Targets: B1 (25), B2 (25), B4 (25), B21 (25) = **100 test cases**

These benchmarks use rule-based scoring. Every test case MUST have `expected_label`. Key_facts use `tier` for weighted scoring. `forbidden_claims` are checked via regex/pattern matching.

- [ ] **Step 1: Generate B1 test cases (25)**

Source questions from:
- Triage report (kept/revised v1 cases mapped to B1)
- CIIO research: CCoP 1.0→2.0 evolution, IM8 context, ESCI/STCC/FDI awareness, digital boundary definition
- CCoP 2.0 Preamble and Cybersecurity Act sections

Question design requirements:
- Mix of `scenario_role`: risk_manager and employee
- Cover all 11 sectors (minimum 3 represented)
- Include CCoP 1.0 context questions (e.g., "What changed between CCoP 1.0 and 2.0 for access control?")
- Include IM8 overlap questions (e.g., "Our government agency has both IM8 and CCoP requirements...")
- Include ESCI/FDI questions (e.g., "Could our cloud service be classified under the new FDI provisions?")
- Difficulty distribution: ~6 low, ~11 medium, ~8 high
- Test categories: mix of positive, negative, edge_case, adversarial

Every test case must pass the v2 schema validator.

- [ ] **Step 2: Validate B1 test cases**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b01_ccop_applicability_scope.jsonl
```

Expected: 25 valid, 0 errors

- [ ] **Step 3: Generate B2 test cases (25)**

Source: compliance classification scenarios across sectors. Focus on sector-specific IT/OT nuance.

- [ ] **Step 4: Validate B2**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b02_compliance_classification.jsonl
```

- [ ] **Step 5: Generate B4 test cases (25)**

Source: IT/OT boundary reasoning. Focus on hybrid sectors (healthcare, aviation, transport) where the boundary is ambiguous. Include smart grid, medical device, and rail signalling scenarios from CIIO research.

- [ ] **Step 6: Validate B4**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b04_it_ot_classification_boundary.jsonl
```

- [ ] **Step 7: Generate B21 test cases (25)**

Source: adversarial questions designed to elicit hallucination or over-specification. Include:
- Non-existent clause references
- Requirements from other frameworks framed as CCoP
- Leading questions suggesting non-existent obligations
- Over-specification traps (adding requirements beyond CCoP text)
- Questions about repealed/outdated requirements

- [ ] **Step 8: Validate B21**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b21_hallucination_over_specification.jsonl
```

- [ ] **Step 9: Run full validation**

```bash
cd ground-truth/schema && python validate.py
```

Expected: 101 valid (100 new + 1 B3 sample from Task 3), 0 errors

- [ ] **Step 10: Commit**

```bash
git add ground-truth/test-suite/b01_*.jsonl ground-truth/test-suite/b02_*.jsonl ground-truth/test-suite/b04_*.jsonl ground-truth/test-suite/b21_*.jsonl
git commit -m "feat: generate v2 rule-based benchmark test cases (B1, B2, B4, B21)

100 test cases across 4 rule-based benchmarks.
B1: 25 (includes CCoP 1.0, IM8, ESCI/FDI context)
B2: 25 (sector-specific compliance classification)
B4: 25 (IT/OT boundary reasoning across sectors)
B21: 25 (hallucination + over-specification detection)"
```

---

## Task 7: Generate V2 Test Cases — Core Reasoning Benchmarks (B3, B5, B6, B7, B10)

**Files:**
- Modify: `ground-truth/test-suite/b03_conditional_compliance_reasoning.jsonl` (expand from 1 to 30)
- Create: `ground-truth/test-suite/b05_control_requirement_comprehension.jsonl`
- Create: `ground-truth/test-suite/b06_control_intent_understanding.jsonl`
- Create: `ground-truth/test-suite/b07_gap_identification_quality.jsonl`
- Create: `ground-truth/test-suite/b10_risk_justification_coherence.jsonl`

Targets: B3 (30), B5 (25), B6 (20), B7 (30), B10 (20) = **125 test cases**

These benchmarks use LLM-judge scoring. Every test case MUST have `reasoning_chain` and `acceptable_variations`. Minimum 2 critical-tier key_facts.

- [ ] **Step 1: Generate B3 test cases (30 total, 29 new)**

Source: conditional compliance scenarios. Focus on compensating controls, partial compliance, waiver-worthy situations. Use CIIO research scenarios: SCADA patching, cloud migration, vendor remote access.

- [ ] **Step 2: Validate B3**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b03_conditional_compliance_reasoning.jsonl
```

- [ ] **Step 3: Generate B5 test cases (25)**

Source: "what does this clause actually mean for my org?" questions. Practical comprehension, not abstract paraphrasing. Cover all 7 auditable CCoP domains.

- [ ] **Step 4: Validate B5**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b05_control_requirement_comprehension.jsonl
```

- [ ] **Step 5: Generate B6 test cases (20)**

Source: intent behind CCoP controls applied to real scenarios. E.g., "Why does CCoP require on-site vendor access rather than monitored VPN?"

- [ ] **Step 6: Validate B6**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b06_control_intent_understanding.jsonl
```

- [ ] **Step 7: Generate B7 test cases (30)**

Source: gap analysis scenarios. Include B17 (policy vs practice) as a scenario type within gap identification. Use common audit findings from CIIO research: incomplete asset inventories, weak privileged access management, insufficient logging.

- [ ] **Step 8: Validate B7**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b07_gap_identification_quality.jsonl
```

- [ ] **Step 9: Generate B10 test cases (20)**

Source: risk justification for board reporting. Risk Manager must articulate why a specific compliance gap poses risk, calibrated to the organization's sector and context.

- [ ] **Step 10: Validate B10**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b10_risk_justification_coherence.jsonl
```

- [ ] **Step 11: Run full validation**

```bash
cd ground-truth/schema && python validate.py
```

Expected: 226 valid (101 + 125), 0 errors

- [ ] **Step 12: Commit**

```bash
git add ground-truth/test-suite/b03_*.jsonl ground-truth/test-suite/b05_*.jsonl ground-truth/test-suite/b06_*.jsonl ground-truth/test-suite/b07_*.jsonl ground-truth/test-suite/b10_*.jsonl
git commit -m "feat: generate v2 core reasoning benchmark test cases (B3, B5, B6, B7, B10)

125 test cases across 5 core reasoning benchmarks.
B3: 30 (conditional compliance, compensating controls)
B5: 25 (practical control requirement comprehension)
B6: 20 (control intent applied to CIIO scenarios)
B7: 30 (gap identification, absorbs B17 policy-vs-practice)
B10: 20 (risk justification for board reporting)"
```

---

## Task 8: Generate V2 Test Cases — Risk & Remediation Benchmarks (B8, B9, B14)

**Files:**
- Create: `ground-truth/test-suite/b08_risk_based_prioritization.jsonl`
- Create: `ground-truth/test-suite/b09_risk_identification_residual_risk.jsonl`
- Create: `ground-truth/test-suite/b14_remediation_quality_feasibility.jsonl`

Targets: B8 (25), B9 (25), B14 (30) = **80 test cases**

- [ ] **Step 1: Generate B8 test cases (25)**

Source: merged B8 (gap prioritization) + B11 (risk severity). Scenarios where Risk Manager must prioritize multiple compliance gaps based on risk severity, operational impact, and remediation cost. Include OT vs IT prioritization differences.

- [ ] **Step 2: Validate B8**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b08_risk_based_prioritization.jsonl
```

- [ ] **Step 3: Generate B9 test cases (25)**

Source: merged B9 (risk identification) + B16 (residual risk). Scenarios covering: identifying compliance-specific risks, and understanding what risks remain AFTER remediation. Include sector-specific risk profiles.

- [ ] **Step 4: Validate B9**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b09_risk_identification_residual_risk.jsonl
```

- [ ] **Step 5: Generate B14 test cases (30)**

Source: merged B14 (remediation quality) + B15 (remediation feasibility). Practical, proportionate remediation recommendations that account for operational constraints. Include OT patching dilemmas, resource-constrained scenarios, phased remediation plans.

- [ ] **Step 6: Validate B14**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b14_remediation_quality_feasibility.jsonl
```

- [ ] **Step 7: Run full validation**

```bash
cd ground-truth/schema && python validate.py
```

Expected: 306 valid (226 + 80), 0 errors

- [ ] **Step 8: Commit**

```bash
git add ground-truth/test-suite/b08_*.jsonl ground-truth/test-suite/b09_*.jsonl ground-truth/test-suite/b14_*.jsonl
git commit -m "feat: generate v2 risk and remediation benchmark test cases (B8, B9, B14)

80 test cases across 3 merged benchmarks.
B8: 25 (risk-based prioritization, merged B8+B11)
B9: 25 (risk identification + residual risk, merged B9+B16)
B14: 30 (remediation quality + feasibility, merged B14+B15)"
```

---

## Task 9: Generate V2 Test Cases — Audit & Governance Benchmarks (B12, B13, B18)

**Files:**
- Create: `ground-truth/test-suite/b12_audit_perspective_alignment.jsonl`
- Create: `ground-truth/test-suite/b13_evidence_expectation_awareness.jsonl`
- Create: `ground-truth/test-suite/b18_responsibility_attribution_sg.jsonl`

Targets: B12 (20), B13 (20), B18 (25) = **65 test cases**

- [ ] **Step 1: Generate B12 test cases (20)**

Source: dual perspective — CSA auditor viewpoint AND Risk Manager audit prep. Use CIIO research: audit process (Forms A1/A2, 30-day submission, compliance-based + risk-based methodology), common non-compliance areas.

- [ ] **Step 2: Validate B12**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b12_audit_perspective_alignment.jsonl
```

- [ ] **Step 3: Generate B13 test cases (20)**

Source: evidence preparation for CCoP audits. What documentation, logs, records, and artifacts should a Risk Manager prepare? Cover all 7 auditable domains.

- [ ] **Step 4: Validate B13**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b13_evidence_expectation_awareness.jsonl
```

- [ ] **Step 5: Generate B18 test cases (25)**

Source: extended responsibility hierarchy — BoD, CIIO, CISO, Risk Manager, vendor. Include scenarios from CIIO research: outsourced CII management (SingHealth-IHiS model), vendor accountability, board cybersecurity training obligations.

- [ ] **Step 6: Validate B18**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b18_responsibility_attribution_sg.jsonl
```

- [ ] **Step 7: Run full validation**

```bash
cd ground-truth/schema && python validate.py
```

Expected: 371 valid (306 + 65), 0 errors

- [ ] **Step 8: Commit**

```bash
git add ground-truth/test-suite/b12_*.jsonl ground-truth/test-suite/b13_*.jsonl ground-truth/test-suite/b18_*.jsonl
git commit -m "feat: generate v2 audit and governance benchmark test cases (B12, B13, B18)

65 test cases across 3 benchmarks.
B12: 20 (audit perspective, dual CSA-auditor + RM-prep)
B13: 20 (evidence expectation across 7 auditable domains)
B18: 25 (responsibility attribution, extended role hierarchy)"
```

---

## Task 10: Generate V2 Test Cases — New Benchmarks (B22, B23, B24)

**Files:**
- Create: `ground-truth/test-suite/b22_waiver_exception_reasoning.jsonl`
- Create: `ground-truth/test-suite/b23_multi_regulator_coordination.jsonl`
- Create: `ground-truth/test-suite/b24_incident_response_guidance.jsonl`

Targets: B22 (20), B23 (20), B24 (25) = **65 test cases**

- [ ] **Step 1: Generate B22 test cases (20)**

Source: CIIO research on waiver process (Section 11(7)). Scenarios:
- When to apply for a waiver vs when to implement the control
- Compensating controls that satisfy vs don't satisfy waiver requirements
- Waiver duration and renewal
- OT-specific waiver scenarios (legacy SCADA, PLCs without security features)
- Time-bound waivers and transition planning

- [ ] **Step 2: Validate B22**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b22_waiver_exception_reasoning.jsonl
```

- [ ] **Step 3: Generate B23 test cases (20)**

Source: CIIO research on regulatory overlap. Scenarios:
- CCoP + MAS-TRM dual compliance (banking sector)
- CCoP + IM8 dual compliance (government sector)
- CCoP + PDPC data protection overlap
- Cross-regulator incident reporting (CSA + MAS + PDPC)
- Harmonized vs conflicting requirements
- Mutually recognized audits

- [ ] **Step 4: Validate B23**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b23_multi_regulator_coordination.jsonl
```

- [ ] **Step 5: Generate B24 test cases (25)**

Source: CIIO research on incident response. Scenarios:
- 2-hour CSA notification process and triggers
- 14-day supplementary report requirements
- Multi-regulator reporting (CSA + MAS + PDPC) with different timelines
- APT vs ransomware vs data breach response differences
- Crisis communication obligations
- Post-incident remediation and audit implications
- Exercise Cyber Star participation

- [ ] **Step 6: Validate B24**

```bash
cd ground-truth/schema && python validate.py --file ../test-suite/b24_incident_response_guidance.jsonl
```

- [ ] **Step 7: Run full validation**

```bash
cd ground-truth/schema && python validate.py
```

Expected: 436 valid (371 + 65), 0 errors

- [ ] **Step 8: Commit**

```bash
git add ground-truth/test-suite/b22_*.jsonl ground-truth/test-suite/b23_*.jsonl ground-truth/test-suite/b24_*.jsonl
git commit -m "feat: generate v2 new benchmark test cases (B22, B23, B24)

65 test cases across 3 new benchmarks.
B22: 20 (waiver and exception reasoning)
B23: 20 (multi-regulator coordination)
B24: 25 (incident response guidance)"
```

---

## Task 11: Generate Coverage Matrix

**Files:**
- Create: `ground-truth/coverage-matrix.md`

- [ ] **Step 1: Analyze coverage across all v2 test cases**

Read all JSONL files in `ground-truth/test-suite/` and build a matrix:
- Rows: 18 benchmarks
- Columns: 11 CCoP sections, 12 sectors, 3 difficulty levels, 4 test categories, 3 domains (IT/OT/IT+OT)

- [ ] **Step 2: Write the coverage matrix**

Create `ground-truth/coverage-matrix.md`:

```markdown
# Ground Truth V2 Coverage Matrix

## Summary
- Total test cases: XXX
- Benchmarks: 18
- CCoP sections covered: XX/11
- Sectors represented: XX/12

## Benchmark × CCoP Section

| Benchmark | Governance | Identification | Protection | Detection | Response | Resilience | Training | OT Addendum | Preamble | Act | Other |
|-----------|-----------|---------------|-----------|-----------|----------|-----------|----------|------------|---------|-----|-------|
| B1 | X | X | ... | ... | ... | ... | ... | ... | X | X | |
| ... | | | | | | | | | | | |

## Benchmark × Sector

| Benchmark | Energy | Water | Banking | Healthcare | Aviation | Transport | Maritime | Telecoms | Gov | Media | Security | Cross |
|-----------|--------|-------|---------|-----------|---------|-----------|---------|---------|-----|-------|----------|-------|
| B1 | 3 | 2 | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| ... | | | | | | | | | | | | |

## Benchmark × Difficulty

| Benchmark | Low | Medium | High | Total |
|-----------|-----|--------|------|-------|
| B1 | 6 | 11 | 8 | 25 |
| ... | | | | |

## Benchmark × Test Category

| Benchmark | Positive | Negative | Edge Case | Adversarial | Total |
|-----------|----------|----------|-----------|-------------|-------|
| B1 | X | X | X | X | 25 |
| ... | | | | | |

## Coverage Gaps
- [List any CCoP sections with < 3 test cases]
- [List any sectors with < 3 total test cases]
- [List any benchmarks with < 20 test cases]
```

- [ ] **Step 3: Commit**

```bash
git add ground-truth/coverage-matrix.md
git commit -m "docs: add v2 ground truth coverage matrix

Coverage across 18 benchmarks x 11 CCoP sections x 12 sectors
x 3 difficulty levels x 4 test categories."
```

---

## Task 12: Generate Expert Validation Spreadsheet

**Files:**
- Create: `ground-truth/expert-validation/generate_v2_expert_review.py`
- Create: `ground-truth/expert-validation/CCoP_V2_Test_Cases_Expert_Review.xlsx`

- [ ] **Step 1: Write the Excel generator script**

Create `ground-truth/expert-validation/generate_v2_expert_review.py`:

```python
#!/usr/bin/env python3
"""
Generate Excel spreadsheet for expert validation of v2 test cases.

Reads all v2 JSONL files from ground-truth/test-suite/ and creates
a structured Excel workbook for domain expert review.
"""

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


def load_all_test_cases(test_suite_dir: Path) -> list[dict]:
    """Load all v2 test cases from JSONL files."""
    cases = []
    for filepath in sorted(test_suite_dir.glob("b*.jsonl")):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    cases.append(json.loads(line))
    return cases


def create_workbook(cases: list[dict], output_path: Path) -> None:
    """Create expert review Excel workbook."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Expert Review"

    # Headers
    headers = [
        "Test ID", "Benchmark", "Sector", "Domain", "Difficulty",
        "Category", "CCoP Section", "Clause Refs",
        "Question", "Expected Label", "Expected Response",
        "Key Facts (Critical)", "Key Facts (Important/Supporting)",
        "Reasoning Chain", "Forbidden Claims",
        # Expert review columns
        "Approved (Y/N)", "Accuracy", "Completeness", "Remarks"
    ]

    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    review_fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    review_font = Font(bold=True, color="000000", size=11)

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        if col_idx >= 16:  # Review columns
            cell.fill = review_fill
            cell.font = review_font
        else:
            cell.fill = header_fill
            cell.font = header_font
        cell.alignment = Alignment(horizontal="center", wrap_text=True)

    # Data rows
    for row_idx, case in enumerate(cases, 2):
        gt = case.get("ground_truth", {})
        fc = case.get("fail_conditions", {})
        meta = case.get("metadata", {})
        inp = case.get("input", {})
        key_facts = gt.get("key_facts", [])

        critical_facts = "\n".join(
            f"- {kf['fact']} [{kf['source']}]"
            for kf in key_facts if kf.get("tier") == "critical"
        )
        other_facts = "\n".join(
            f"- [{kf['tier']}] {kf['fact']} [{kf['source']}]"
            for kf in key_facts if kf.get("tier") != "critical"
        )
        reasoning = "\n".join(
            f"{i+1}. {step}"
            for i, step in enumerate(gt.get("reasoning_chain", []))
        )
        forbidden = "\n".join(f"- {c}" for c in fc.get("forbidden_claims", []))

        row_data = [
            case.get("test_id", ""),
            case.get("benchmark_id", ""),
            inp.get("scenario_sector", ""),
            meta.get("domain", ""),
            meta.get("difficulty", ""),
            meta.get("test_category", ""),
            meta.get("section", ""),
            ", ".join(meta.get("clause_reference", [])),
            inp.get("question", ""),
            gt.get("expected_label", ""),
            gt.get("expected_response", ""),
            critical_facts,
            other_facts,
            reasoning,
            forbidden,
        ]

        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # Data validation for Approved column
    approval_dv = DataValidation(type="list", formula1='"Y,N"', allow_blank=True)
    approval_dv.error = "Please enter Y or N"
    approval_dv.errorTitle = "Invalid Input"
    ws.add_data_validation(approval_dv)
    approval_dv.add(f"P2:P{len(cases) + 1}")

    # Accuracy validation (1-5 scale)
    accuracy_dv = DataValidation(type="list", formula1='"1,2,3,4,5"', allow_blank=True)
    ws.add_data_validation(accuracy_dv)
    accuracy_dv.add(f"Q2:Q{len(cases) + 1}")

    # Completeness validation (1-5 scale)
    completeness_dv = DataValidation(type="list", formula1='"1,2,3,4,5"', allow_blank=True)
    ws.add_data_validation(completeness_dv)
    completeness_dv.add(f"R2:R{len(cases) + 1}")

    # Column widths
    widths = [10, 8, 12, 8, 10, 12, 20, 15, 60, 15, 60, 40, 40, 40, 30, 12, 10, 12, 40]
    for col_idx, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Freeze panes (freeze header row and first column)
    ws.freeze_panes = "B2"

    wb.save(output_path)
    print(f"Saved {len(cases)} test cases to {output_path}")


def main() -> None:
    test_suite_dir = Path(__file__).parent.parent / "test-suite"
    output_path = Path(__file__).parent / "CCoP_V2_Test_Cases_Expert_Review.xlsx"

    cases = load_all_test_cases(test_suite_dir)
    if not cases:
        print(f"No test cases found in {test_suite_dir}")
        return

    create_workbook(cases, output_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the generator**

```bash
cd ground-truth/expert-validation && python generate_v2_expert_review.py
```

Expected: `Saved ~436 test cases to .../CCoP_V2_Test_Cases_Expert_Review.xlsx`

- [ ] **Step 3: Commit**

```bash
git add ground-truth/expert-validation/generate_v2_expert_review.py ground-truth/expert-validation/CCoP_V2_Test_Cases_Expert_Review.xlsx
git commit -m "feat: generate v2 expert validation spreadsheet

Excel workbook with all ~436 v2 test cases for domain expert review.
Includes approval (Y/N), accuracy (1-5), completeness (1-5), and
remarks columns with data validation."
```

---

## Task 13: Write Migration Report

**Files:**
- Create: `docs/phase-2/ground-truth-v2-migration.md`

- [ ] **Step 1: Write the migration report**

Create `docs/phase-2/ground-truth-v2-migration.md`:

```markdown
# Ground Truth V2 Migration Report

## Overview
- V1: 118 test cases across 21 benchmarks
- V2: ~436 test cases across 18 benchmarks
- Schema: Flat → nested with tiered key_facts, reasoning chains, fail conditions

## Schema Changes
[Document the v1→v2 field mapping from the spec]

## Benchmark Changes
[Document merges, removals, additions from benchmark registry]

## Test Case Triage Results
[Summary from triage report — how many kept, revised, discarded]

## Quality Improvements
- All key_facts now have source and tier (no more "Unable to extract")
- All test cases have fail_conditions
- All LLM-judge benchmarks have reasoning_chain and acceptable_variations
- All questions are scenario-grounded and sector-aware
- Target audience: Risk Managers in CII organizations

## Known Limitations
- Expert validation pending
- Difficulty calibration not empirically validated (requires baseline model run)
- Coverage gaps identified in coverage matrix (if any)

## Next Steps
- Expert validation of v2 test cases
- Update JSONL repository parser to handle v2 nested format
- Update TestCase entity with v2 fields
- Run baseline evaluation against v2 ground truth
```

- [ ] **Step 2: Commit**

```bash
git add docs/phase-2/ground-truth-v2-migration.md
git commit -m "docs: add ground truth v2 migration report

Documents schema changes, benchmark restructuring, triage results,
quality improvements, and next steps."
```

---

## Task 14: Update Repository Parser for V2 Format

**Files:**
- Modify: `src/infrastructure/adapters/repositories/jsonl_test_case_repository.py:141-157`
- Modify: `src/domain/entities/test_case.py:31-46`
- Test: `src/tests/infrastructure/test_jsonl_v2_parsing.py`

This task updates the infrastructure to load v2 nested JSONL format while remaining backward-compatible with v1 flat format during transition.

- [ ] **Step 1: Write the failing test for v2 parsing**

Create `src/tests/infrastructure/test_jsonl_v2_parsing.py`:

```python
"""Tests for v2 JSONL test case parsing."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from domain.entities.test_case import TestCase
from infrastructure.adapters.repositories.jsonl_test_case_repository import (
    JSONLTestCaseRepository,
)


V2_TEST_CASE = {
    "test_id": "B3-001",
    "version": "2.0",
    "benchmark_id": "B3",
    "input": {
        "question": "Your organization uses shared admin accounts with session logging for CII SCADA systems. Does this comply with CCoP 2.0?",
        "scenario_sector": "energy",
        "scenario_role": "risk_manager",
    },
    "ground_truth": {
        "expected_label": "non-compliant",
        "expected_response": "Shared admin accounts do not comply with CCoP 2.0 access control requirements. Clause 5.3.1(c) mandates individual accountability for privileged access to CII systems.",
        "key_facts": [
            {
                "fact": "Clause 5.3.1(c) requires individual accountability",
                "source": "CCoP 2.0 Section 5.3.1(c)",
                "tier": "critical",
            },
            {
                "fact": "Shared accounts prevent attribution of actions",
                "source": "Regulatory interpretation",
                "tier": "critical",
            },
        ],
        "reasoning_chain": [
            "Identify privileged access scenario",
            "Recall individual accountability requirement",
            "Conclude non-compliance",
        ],
        "acceptable_variations": [
            "May recommend PAM tooling",
        ],
    },
    "fail_conditions": {
        "forbidden_claims": ["Shared accounts satisfy CCoP requirements"],
        "hallucination_patterns": ["Citing non-existent clauses"],
    },
    "metadata": {
        "section": "Section 5: Protection",
        "clause_reference": ["5.3.1"],
        "domain": "OT",
        "difficulty": "high",
        "test_category": "negative",
        "created_date": "2026-04-01",
        "reviewer": None,
    },
}


@pytest.fixture
def v2_jsonl_dir(tmp_path: Path) -> Path:
    """Create a temp dir with a v2 JSONL file."""
    filepath = tmp_path / "b03_conditional_compliance_reasoning.jsonl"
    filepath.write_text(json.dumps(V2_TEST_CASE) + "\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def mock_logger() -> MagicMock:
    return MagicMock()


class TestV2Parsing:
    """Test that the repository correctly parses v2 nested format."""

    @pytest.mark.asyncio
    async def test_parses_v2_test_case(
        self, v2_jsonl_dir: Path, mock_logger: MagicMock
    ) -> None:
        repo = JSONLTestCaseRepository(v2_jsonl_dir, mock_logger)
        cases = await repo.load_all()

        assert len(cases) == 1
        case = cases[0]
        assert case.test_id == "B3-001"
        assert case.question == V2_TEST_CASE["input"]["question"]
        assert case.expected_response == V2_TEST_CASE["ground_truth"]["expected_response"]
        assert case.expected_label == "non-compliant"

    @pytest.mark.asyncio
    async def test_parses_v2_key_facts_as_strings(
        self, v2_jsonl_dir: Path, mock_logger: MagicMock
    ) -> None:
        """key_facts property returns list[str] for backward compatibility with scorers."""
        repo = JSONLTestCaseRepository(v2_jsonl_dir, mock_logger)
        cases = await repo.load_all()
        case = cases[0]

        # Scorers expect list[str], not list[dict]
        assert isinstance(case.key_facts[0], str)
        assert "Clause 5.3.1(c) requires individual accountability" in case.key_facts[0]

    @pytest.mark.asyncio
    async def test_parses_v2_forbidden_claims(
        self, v2_jsonl_dir: Path, mock_logger: MagicMock
    ) -> None:
        repo = JSONLTestCaseRepository(v2_jsonl_dir, mock_logger)
        cases = await repo.load_all()
        case = cases[0]

        assert "Shared accounts satisfy CCoP requirements" in case.forbidden_claims

    @pytest.mark.asyncio
    async def test_parses_v2_metadata(
        self, v2_jsonl_dir: Path, mock_logger: MagicMock
    ) -> None:
        repo = JSONLTestCaseRepository(v2_jsonl_dir, mock_logger)
        cases = await repo.load_all()
        case = cases[0]

        assert case.domain == "OT"
        assert case.metadata.get("scenario_sector") == "energy"
        assert case.metadata.get("test_category") == "negative"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src && poetry run pytest tests/infrastructure/test_jsonl_v2_parsing.py -v
```

Expected: FAIL — parser doesn't handle nested format yet.

- [ ] **Step 3: Update the repository parser to detect and handle v2 format**

Modify `src/infrastructure/adapters/repositories/jsonl_test_case_repository.py`. Replace the `_parse_test_case` method:

```python
def _parse_test_case(self, data: dict) -> TestCase:
    """Parse JSON data to TestCase entity. Handles both v1 flat and v2 nested formats."""
    is_v2 = data.get("version") == "2.0"

    if is_v2:
        return self._parse_v2_test_case(data)
    return self._parse_v1_test_case(data)

def _parse_v1_test_case(self, data: dict) -> TestCase:
    """Parse v1 flat format (backward compatibility)."""
    return TestCase(
        test_id=data["test_id"],
        benchmark_type=BenchmarkType.from_string(data["benchmark_type"]),
        section=CCoPSection.from_string(data["section"]),
        clause_reference=data["clause_reference"],
        difficulty=DifficultyLevel.from_string(data["difficulty"]),
        question=data["question"],
        expected_response=data["expected_response"],
        evaluation_criteria=data.get("evaluation_criteria", {}),
        metadata=data.get("metadata", {}),
        key_facts=data.get("key_facts", []),
        expected_label=data.get("expected_label"),
        forbidden_claims=data.get("forbidden_claims", []),
    )

def _parse_v2_test_case(self, data: dict) -> TestCase:
    """Parse v2 nested format."""
    inp = data.get("input", {})
    gt = data.get("ground_truth", {})
    fc = data.get("fail_conditions", {})
    meta = data.get("metadata", {})

    # Extract key_facts as list[str] for scorer compatibility
    raw_key_facts = gt.get("key_facts", [])
    key_facts_strings = [kf["fact"] for kf in raw_key_facts if isinstance(kf, dict)]

    # Merge v2-specific fields into metadata for downstream access
    enriched_metadata = {
        **meta,
        "scenario_sector": inp.get("scenario_sector"),
        "scenario_role": inp.get("scenario_role"),
        "test_category": meta.get("test_category"),
        "reasoning_chain": gt.get("reasoning_chain", []),
        "acceptable_variations": gt.get("acceptable_variations", []),
        "key_facts_structured": raw_key_facts,
        "hallucination_patterns": fc.get("hallucination_patterns", []),
    }

    # Build clause_reference as string (v1 format expects string, not list)
    clause_refs = meta.get("clause_reference", [])
    clause_ref_str = ", ".join(clause_refs) if isinstance(clause_refs, list) else clause_refs

    return TestCase(
        test_id=data["test_id"],
        benchmark_type=BenchmarkType.from_string(data["benchmark_id"]),
        section=CCoPSection.from_string(meta.get("section", "N/A")),
        clause_reference=clause_ref_str,
        difficulty=DifficultyLevel.from_string(meta.get("difficulty", "Medium")),
        question=inp["question"],
        expected_response=gt["expected_response"],
        evaluation_criteria={},  # v2 uses universal judge, no per-test criteria
        metadata=enriched_metadata,
        key_facts=key_facts_strings,
        expected_label=gt.get("expected_label"),
        forbidden_claims=fc.get("forbidden_claims", []),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src && poetry run pytest tests/infrastructure/test_jsonl_v2_parsing.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Run existing tests to verify no regressions**

```bash
cd src && poetry run pytest tests/ -v --timeout=30
```

Expected: All existing tests still pass (v1 parsing unchanged).

- [ ] **Step 6: Commit**

```bash
git add src/infrastructure/adapters/repositories/jsonl_test_case_repository.py src/tests/infrastructure/test_jsonl_v2_parsing.py
git commit -m "feat: add v2 nested JSONL parsing to test case repository

Repository auto-detects v2 format via version field and parses
nested structure (input, ground_truth, fail_conditions, metadata).
Extracts key_facts as strings for scorer backward compatibility.
V1 flat format still supported for archived test cases."
```

---

## Task 15: Update Test Case Repository Config to Point to V2 Directory

**Files:**
- Modify: config file or environment variable that sets the test cases directory path
- Test: Run `poetry run ccop-eval evaluate run --model primus-reasoning --benchmarks B3 --no-save` (should load from v2 directory)

- [ ] **Step 1: Find where the test cases directory is configured**

```bash
cd src && grep -r "test.case" --include="*.py" --include="*.env*" --include="*.toml" -l
```

Check `.env.test`, `.env.local`, `pyproject.toml`, or any config file for the test cases path.

- [ ] **Step 2: Update the path to point to v2 directory**

Change the test cases directory from `ground-truth/phase-2/test-suite/` to `ground-truth/test-suite/`.

The exact file and key depends on what Step 1 finds. Update accordingly.

- [ ] **Step 3: Verify the path change works**

```bash
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --benchmarks B3 --no-save 2>&1 | head -20
```

Expected: Should discover and attempt to load `b03_conditional_compliance_reasoning.jsonl` from the v2 directory. (The evaluation itself may fail if the model isn't running — that's fine; we just need to see it finding the v2 files.)

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: update test cases directory to v2 ground-truth/test-suite/"
```

---

## Task 16: Final Validation and Summary Commit

**Files:**
- Run: Full schema validation
- Run: Test suite
- Verify: All deliverables present

- [ ] **Step 1: Run full schema validation**

```bash
cd ground-truth/schema && python validate.py --strict
```

Expected: ~436 valid, 0 warnings, 0 errors

- [ ] **Step 2: Run all tests**

```bash
cd src && poetry run pytest tests/ -v --timeout=30
```

Expected: All tests pass including v2 parsing tests.

- [ ] **Step 3: Verify all deliverables exist**

```bash
echo "=== V2 Test Suite ===" && ls ground-truth/test-suite/*.jsonl | wc -l
echo "=== Schema ===" && ls ground-truth/schema/
echo "=== Expert Validation ===" && ls ground-truth/expert-validation/
echo "=== Archive ===" && ls ground-truth/archive/phase-2/test-suite/*.jsonl | wc -l
echo "=== Docs ===" && ls docs/phase-2/benchmark-registry.md docs/phase-2/ground-truth-v2-migration.md ground-truth/coverage-matrix.md
```

Expected:
- 18 JSONL files in v2 test-suite
- Schema + validator in schema/
- Excel in expert-validation/
- 21 JSONL files in archive
- All 3 doc files present

- [ ] **Step 4: Verify difficulty and sector distribution**

```bash
cd ground-truth/schema && python -c "
import json
from pathlib import Path
from collections import Counter

difficulties = Counter()
sectors = Counter()
for f in sorted(Path('../test-suite').glob('b*.jsonl')):
    for line in open(f):
        tc = json.loads(line.strip())
        difficulties[tc['metadata']['difficulty']] += 1
        sectors[tc['input']['scenario_sector']] += 1

total = sum(difficulties.values())
print('=== Difficulty Distribution ===')
for d in ['low', 'medium', 'high']:
    print(f'  {d}: {difficulties[d]} ({difficulties[d]/total*100:.0f}%)')
print(f'  Target: ~25% low, ~45% medium, ~30% high')
print()
print('=== Sector Distribution ===')
for s, c in sectors.most_common():
    print(f'  {s}: {c}')
print(f'  Sectors represented: {len(sectors)}')
"
```

Expected: Difficulty roughly matches 25/45/30 targets. At least 8 sectors represented.

- [ ] **Step 5: Count total test cases**

```bash
wc -l ground-truth/test-suite/*.jsonl
```

Expected: ~436 total lines (one test case per line)

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: ground truth v2 complete — ~436 test cases across 18 benchmarks

Final validation: all test cases pass v2 schema, all tests pass,
all deliverables present. Expert validation pending."
```
