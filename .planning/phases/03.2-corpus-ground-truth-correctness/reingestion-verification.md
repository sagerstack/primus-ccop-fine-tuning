# Re-ingestion Verification Log

**Date:** 2026-04-21
**Branch:** feature/phase2-eval
**Plan:** 03.2-03

---

## Run Log

### Pre-conditions

- Qdrant was not running at start. Docker Desktop launched automatically. Qdrant started via `docker compose up -d qdrant`.
- Existing collection `ccop_clauses_hybrid` had **303 points** (stale index from pre-fix chunker). Collection was dropped before re-ingestion.

### Drop Command

```
cd src && poetry run python -c "
  from qdrant_client import QdrantClient
  from infrastructure.config.settings import get_settings
  s = get_settings()
  c = QdrantClient(url=s.qdrant_url)
  c.delete_collection(s.qdrant_collection_name)
  print('dropped')
"
```

Result: `Drop result: True`

---

### Ingestion Run (2026-04-21T13:38:24Z → 13:42:51Z)

Command:
```
cd src && poetry run python -m rag.ingestion.run_ingestion --ccop-dir ../ccop-official
```

**Exit code: 0**

#### Per-document chunk counts (Step 2/5)

| Document | Chunks | Chunker |
|---|---|---|
| CCoP 2.0 | 256 | clause_aware |
| CCoP Response to Feedback | 22 | clause_aware |
| Auditing Guidelines | 11 | section_based |
| Threat Modelling Guide | 22 | section_based |
| Risk Assessment Guide | 19 | section_based |
| Security By Design | 110 | clause_aware |
| Cybersecurity Act 2018 | 50 | section_based |
| **Total** | **490** | |

Note: Docling ran diagram captioning (Step 1.5) — ZhipuAI API returned 429 (insufficient balance) for all 21 Security By Design diagrams. Diagrams were captioned with placeholder text rather than vision descriptions. This is pre-existing behaviour unrelated to the chunker fix.

#### Chunk size distribution

| Metric | Value |
|---|---|
| Min | 2 tokens |
| Max | 2835 tokens |
| Avg | 175 tokens |
| Median | 81 tokens |

| Bucket | Count | % |
|---|---|---|
| < 300 tokens | 413 | 84.3% |
| 300–500 tokens | 40 | 8.2% |
| 500–700 tokens | 15 | 3.1% |
| 700–900 tokens | 11 | 2.2% |
| 900+ tokens | 11 | 2.2% |

#### TOC Sanity Gate (Step 2.5/5)

```
TOC sanity gate — observed sections: ['1', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7',
  '10', '10.1', '10.2', '10.3', '10.4', '11', '11.1', '11.2', '2', '2.1', '3', '3.1', '3.2',
  '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '4', '4.1', '5', '5.1', '5.10', '5.11', '5.12',
  '5.13', '5.14', '5.15', '5.16', '5.17', '5.2', '5.3', '5.4', '5.5', '5.6', '5.7', '5.8',
  '5.9', '6', '6.1', '6.2', '6.3', '6.4', '7', '7.1', '7.2', '7.3', '8', '8.1', '8.2',
  '9', '9.1', '9.2']
TOC sanity gate PASSED — all 12 expected sections present
```

**RESULT: PASS**

#### Upload (Step 4/5)

- 490 chunks embedded (BGE-large-en-v1.5 dense + BM25 sparse)
- Uploaded in 5 batches to `ccop_clauses_hybrid`
- Verification query "access control requirements for CII" returned 5 results

#### Points in Collection Post-Ingest

477 points (490 chunks - 13 deduplicated by deterministic uuid5 IDs from re-used citation_ids across preamble sub-chunks).

| Document | Points |
|---|---|
| CCoP 2.0 | 250 |
| Security By Design | 110 |
| Cybersecurity Act 2018 | 48 |
| Threat Modelling Guide | 20 |
| Risk Assessment Guide | 19 |
| CCoP Response to Feedback | 19 |
| Auditing Guidelines | 11 |
| **Total** | **477** |

---

## SC #7 — Section Presence Verification

Filter: `document_source == "CCoP 2.0" AND section == <X.Y>`.

| Section | Points | Example citation_id | Result |
|---|---|---|---|
| 5.1 | 4 | CCoP 2.0::5.1.1 | **PASS** |
| 5.2 | 2 | CCoP 2.0::5.2.1 | **PASS** |
| 5.3 | 1 | CCoP 2.0::5.3.1 | **PASS** |
| 5.4 | 1 | CCoP 2.0::5.4.1 | **PASS** |
| 5.5 | 3 | CCoP 2.0::5.5.1 | **PASS** |
| 5.6 | 3 | CCoP 2.0::5.6.1 | **PASS** |
| 5.7 | 2 | CCoP 2.0::5.7.1 | **PASS** |
| 5.8 | 1 | CCoP 2.0::5.8.1 | **PASS** |
| 5.9 | 4 | CCoP 2.0::5.9.1 | **PASS** |
| 5.10 | 2 | CCoP 2.0::5.10.1 | **PASS** |
| 5.11 | 4 | CCoP 2.0::5.11.1 | **PASS** |
| 5.12 | 7 | CCoP 2.0::5.12.1 | **PASS** |

**All 12 sections present. SC #7: PASS.**

Previously missing sections (5.3, 5.4) are now indexed:
- `CCoP 2.0::5.3.1` — Privileged Access Management (grants, inventory, privilege separation)
- `CCoP 2.0::5.4.1` — Trust Relationship Management (domain trust monitoring + anomaly alerting)

---

## SC #8 — Phrase Scan

The plan's SC #8 specifies: "full-text scan for 'individual accountability' returns >=1 hit" and "full-text scan for 'individual authentication' returns >=1 hit".

### Finding: Phrases not present in source document

A full scroll of all 250 CCoP 2.0 points and a raw search of the parsed Docling markdown (151,269 chars) confirmed:

- `"individual accountability"` — **0 hits in PDF, 0 hits in index**
- `"individual authentication"` — **0 hits in PDF, 0 hits in index**

These compound phrases do not appear literally in the CCoP 2.0 source document (CCoP---Second-Edition_Revision-One.pdf). The plan's SC #8 referenced them as "previously-missing content" from sections 5.3/5.4, but inspection of sections 5.3 and 5.4 shows they contain:

- **5.3 (Privileged Access Management):** Privileged access grants, inventory, separation
- **5.4 (Trust Relationship Management):** Domain trust monitoring and anomaly alerting

Neither section uses the phrases "individual accountability" or "individual authentication".

### What IS present in the index for these concepts

Related terms that ARE present:
- `"accountability"` — 1 hit: `CCoP 2.0::7.1` (Incident Management context, "lines of accountability")
- `"authentication"` — 11 hits: `CCoP 2.0::5.1`, `5.7.2`, `5.13`, `7.1.3`, `10.2.3`, etc.

**SC #8 as written: CANNOT PASS — phrases do not exist in source document.**

The real success criterion for the chunker fix is SC #7 (sections 5.3 and 5.4 present), which PASSES. The previously-missing content was the clause text for Privileged Access Management and Trust Relationship Management, now both indexed.

---

## Summary

| SC | Description | Result |
|---|---|---|
| SC #6 | Collection dropped and re-ingested with fixed chunker | **PASS** |
| SC #7 | Sections 5.1..5.12 all present as discrete points | **PASS** |
| SC #8 | Phrase scan "individual accountability" / "individual authentication" | **CANNOT PASS** — phrases absent from source PDF |

**Critical fix confirmed:** Sections 5.3 and 5.4, which were previously absent from the index due to the `##`-prefix heading bug (Plan 03.2-01), are now correctly ingested as `CCoP 2.0::5.3.1` and `CCoP 2.0::5.4.1`.
