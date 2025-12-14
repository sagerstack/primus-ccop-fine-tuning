# Ground Truth Establishment Process

## Overview

The ground truth for this CCoP 2.0 evaluation benchmark was established through a multi-stage process combining AI-assisted generation with human validation. The process began with Claude (Anthropic's large language model) generating 118 test cases across 21 benchmarks (B1-B21), covering all 11 sections of Singapore's Cybersecurity Code of Practice 2.0. Each test case includes comprehensive fields: question, expected response, key facts (3-8 atomic, verifiable statements), expected labels for classification/safety benchmarks, reasoning dimensions for reasoning benchmarks, and safety checks for hallucination detection. Following generation, a human researcher (the project investigator) conducted systematic review and validation, including: (1) verification of clause references against the official CCoP 2.0 Second Edition Revision One PDF, (2) schema alignment with the updated three-tier scoring methodology (classification, reasoning, safety), (3) automated validation using custom Python scripts to ensure all required fields are present and properly formatted, and (4) consolidation of test cases into a standardized JSONL format with backup preservation. The test cases were then prepared for domain expert validation through creation of a structured Excel spreadsheet (CCoP_Test_Cases_Expert_Review.xlsx) containing all 118 test cases with dedicated columns for expert approval (Y/N) and remarks. This spreadsheet has been sent to a CCoP 2.0 compliance practitioner with deep expertise in Singapore's critical infrastructure cybersecurity requirements for final validation. The ground truth is currently in the "Pending Expert Approval" stage, with the expert review expected to identify any technical inaccuracies, missing key facts, incorrect clause references, or misinterpretations of CCoP requirements before the ground truth is finalized for baseline model evaluation.

---

## Visual Flow Diagram

For an interactive visual representation of the ground truth establishment process, see:
- **[Ground Truth Establishment Flow (HTML)](./ground_truth_establishment_flow.html)** - Interactive black & white flowchart with Mermaid.js diagrams

---

## Current Status Summary

| Stage | Status | Completion Date |
|-------|--------|----------------|
| 1. LLM Generation | ✅ Completed | Dec 13-14, 2024 |
| 2. Human Researcher Review | ✅ Completed | Dec 14, 2024 |
| 3. Expert Review Preparation | ✅ Completed | Dec 14, 2024 |
| 4. Domain Expert Review | ⏳ In Progress | Pending |
| 5. Approval & Finalization | ⏸ Pending | Pending |

**Ground Truth Maturity Level:** 6/10 (Pending Expert Validation)

**Production Readiness:** Ready for internal baseline evaluation; awaiting expert validation for publication-grade quality.

---

## Detailed Process Stages

### Stage 1: LLM Generation (Claude Sonnet 4.5) ✅
- **Output:** 118 test cases in JSONL format
- **Coverage:** 21 benchmarks (B1-B21): 29 classification, 79 reasoning, 10 safety
- **Scope:** All 11 CCoP 2.0 sections + Cybersecurity Act 2018
- **Fields:** test_id, question, expected_response, clause_reference, difficulty, metadata

### Stage 2: Human Researcher Review & Validation ✅
- **Schema Enhancement:** Added benchmark_category, key_facts (3-8 per case), expected_label, reasoning_dimensions, safety_checks
- **Automated Validation:** validate_schema.py - all 118 cases passed
- **Quality Control:** Directory consolidation, standardized naming (b01-b21), backup preservation
- **Clause Verification:** Spot-checked references against CCoP 2.0 PDF
- **Fact Extraction:** Multi-strategy automated extraction (update_test_schema_v2.py)

### Stage 3: Expert Review Preparation ✅
- **Excel File:** CCoP_Test_Cases_Expert_Review.xlsx (98 KB)
- **Structure:** 17 columns (identification, references, content, schema fields, validation)
- **Review Columns:** Approved (Y/N) dropdown + Remarks (free text)
- **Features:** Frozen panes, data validation, color-coded headers, optimized layout
- **Expert Profile:** CCoP 2.0 compliance practitioner with CII cybersecurity expertise

### Stage 4: Domain Expert Review ⏳
**Review Criteria:**
- ✓ Clause references accurate against CCoP 2.0 official document
- ✓ Expected responses technically accurate and complete
- ✓ Key facts are atomic, verifiable, and correctly extracted
- ✓ Singapore-specific terminology used correctly (CIIO, CSA, Commissioner)
- ✓ Questions clear and unambiguous for evaluation purposes
- ✓ Scenarios realistic and applicable to CII operations

### Stage 5: Approval & Ground Truth Finalization ⏸
**Next Steps:**
- Process expert approvals and remarks
- Update test cases based on expert feedback
- Re-run automated validation on corrected cases
- Document approval rate, changes made, expert insights
- Finalize ground truth version 1.0 for baseline evaluation
- Prepare ground truth for potential research publication

---

## Quality Metrics

- **Test Cases:** 118
- **Benchmarks:** 21 (B1-B21)
- **Schema Validation:** 100% (118/118 passed)
- **CCoP Coverage:** 11/11 sections
- **Key Facts:** 3-8 per test case
- **Expert Review:** Pending
