# Patch 007a — de-duplicate blob premises (keep one per group)

**Depends on:** patch 001. Interim de-dup of the section-blob premises that the
chunking bug copied across sub-clauses. For each group of byte-identical `:Premise`
clauses, keep ONE representative (smallest citation_id) and **de-premise** the
redundant copies (remove `:Premise` label only — text/nodes kept, reversible).

## Classification (checked — NOT junk)

All 15 groups are **substantive** content that was mis-chunked + duplicated:
Response-to-Feedback Q&A (RtF-*), the Risk Assessment guide, the Threat Modelling
"Table of Attack", the audit-guide cover/TOC. (An earlier "junk footer" call on
`RtF-10.4` was wrong — the full 975-char blob carries a real Feedback item after a
URL prefix.) So we keep one copy of each; nothing substantive leaves the pool.

## Plan — 15 kept, 203 de-premised

| Representative kept `:Premise` | size | copies dropped |
|---|---|---|
| RtF-11.10 | 19099 | 50 |
| RtF-15.10 | 14063 | 35 |
| RtF-13.10 | 12001 | 28 |
| RtF-12.10 | 7491 | 18 |
| RtF-8.1 | 4800 | 14 |
| RtF-7.10 | 7979 | 12 |
| RiskGuide-1.1 | 9261 | 11 |
| RtF-14.1 | 3317 | 9 |
| ThreatGuide-1.1 | 7861 | 8 |
| RtF-2 | 3055 | 5 |
| AuditGuide-6.3 | 6821 | 3 |
| RtF-10.4 | 975 | 3 |
| RtF-5.1 | 3515 | 3 |
| RtF-9.1 | 3102 | 3 |
| RtF-4.5 | 1955 | 1 |

## Before → After

| | Before | After |
|---|---|---|
| `:Premise` clauses | 393 | **190** (−203 redundant copies) |
| duplicate `:Premise` text groups | 15 | **0** |
| fragment pool | 775 | **572** |
| clause nodes / text | unchanged | unchanged (label-only) |

## Not done here (separate re-chunk effort, B)

The 15 kept representatives are still whole-section blobs. Splitting them into proper
sub-items — and recovering the real per-sub-clause text the chunking bug overwrote —
requires re-parsing the source PDFs (RESPONSE-TO-FEEDBACK / RiskGuide / ThreatGuide).
That is the remaining `#1` re-chunk, scoped as its own re-ingestion pass.
