---
status: complete
phase: 01-rag-infrastructure
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md]
started: 2026-02-09T12:00:00Z
updated: 2026-02-12T11:30:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: complete
name: All tests executed
awaiting: none

## Tests

### 1. Dry-run ingestion pipeline
expected: Run `cd src && poetry run python -m rag.ingestion.run_ingestion --dry-run --ccop-dir ../ccop-official/` — Shows 8 documents parsed, 87 chunks created, per-document chunk counts, and size distribution. No Databricks upload attempted.
result: pass

### 2. Unit tests pass
expected: Run `cd src && poetry run pytest tests/ -v -m "not integration"` — All tests pass (56+ tests), including citation resolver, graph state, section chunker, and all existing evaluation tests.
result: pass

### 3. CLI help shows query command
expected: Run `cd src && poetry run ccop-eval --help` — Output shows evaluate, setup, report, AND query commands listed.
result: pass

### 4. Factual compliance query (RAG-augmented)
expected: Run `cd src && poetry run ccop-eval query ask "What are the access control requirements for CII under CCoP 2.0?" --mode hybrid` — Response cites specific CCoP 2.0 sections, content grounded in retrieved context.
result: pass
notes: Response covered 6 real CCoP access control requirements (network access, restricted connections, internet restrictions, remote access/MFA, wireless security, system hardening). References generic ("CCoP 2.0: CSA") rather than specific clause numbers — expected since base model doesn't produce citation anchors.

### 5. Cross-document query
expected: Run `cd src && poetry run ccop-eval query ask "How should a CII owner conduct a cybersecurity risk assessment?" --mode hybrid` — Response references supplementary documents (Risk Assessment Guide), not just the main CCoP 2.0 document.
result: issue
severity: medium
notes: Response was generic risk assessment guidance without CCoP-specific methodology. Did not reference supplementary Risk Assessment Guide document. Retrieval likely pulled main CCoP chunks ranked above supplementary documents, or supplementary chunks scored below threshold. Root cause: ingestion quality (ToC/title pages indexed, supplementary docs not ranking high enough for domain queries).

### 6. General question fallback (model-only)
expected: Run `cd src && poetry run ccop-eval query ask "What is cybersecurity?" --mode hybrid` — Pipeline falls through to fallback node (LLM-only response). No CCoP-specific citations.
result: pass
notes: All 10 retrieved chunks scored 0.53-0.56 (below threshold). Routing correctly hit fallback node. Response was generic cybersecurity knowledge. is_rag_augmented=False confirmed fallback path.

### 7. Retrieval precision benchmark
expected: Run `cd src && poetry run pytest tests/rag/retrieval/test_retrieval_precision.py -v -m integration --tb=short` — 10 ground truth queries tested, average precision >= 80%.
result: issue
severity: medium
notes: Average precision 66.33%, below 80% threshold. 5/10 queries passed. Failures: Q1 access control (50%, Cybersecurity Act mixed in), Q2 incident reporting (0%, all below threshold), Q3 risk assessment (30%, main CCoP ranked above Risk Assessment Guide), Q4 audit (30%, only 3/10 from Auditing Guidelines), Q5 threat modelling (70%, close). Root causes: ingestion quality (ToCs, title pages, boilerplate indexed), supplementary documents not ranking high enough, hybrid search rewards keyword-dense structural content.

### 8. Citation accuracy (manual spot check)
expected: Verify 2-3 claims from Test 4 response against actual CCoP PDF to confirm cited sections exist and are relevant.
result: pass
notes: Verified 6 claims against CCoP ground truth. 5/6 directly traceable to specific clauses (5.4.1, 5.1.5, 10.2.3, 5.6.4). Claim 6 (system hardening) weakest — more inferred than sourced. No pure hallucinations. Some wording oversimplified vs actual CCoP language.

## Summary

total: 8
passed: 6
issues: 2
pending: 0
skipped: 0

## Gaps

### GAP-01: Supplementary document retrieval ranking
- **Severity**: Medium
- **Tests**: 5, 7
- **Description**: Supplementary CCoP documents (Risk Assessment Guide, Auditing Guidelines, Threat Modelling Guide) not ranking high enough for their domain queries. Main CCoP document chunks and structural content (ToCs, title pages) outrank relevant supplementary chunks.
- **Root Cause**: Ingestion quality — no content filtering at parse time (ToCs, title pages, boilerplate all indexed). Hybrid search (BM25 + dense) rewards keyword-dense structural content. Section chunker splits on markdown headers without distinguishing structural vs substantive content.
- **Impact**: Retrieval precision at 66.33% vs 80% target. Cross-document queries return generic responses instead of document-specific guidance.
- **Fix Scope**: Ingestion pipeline improvements — content filtering during parsing, chunk quality scoring, metadata enrichment. Belongs in RAG optimization phase (post Phase 1).
