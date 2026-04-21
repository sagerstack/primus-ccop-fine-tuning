# Pre-Chunker Docling Audit — Sections 5.3 and 5.4

**Date:** 2026-04-21
**Phase:** 03.2-corpus-ground-truth-correctness
**Plan:** 03.2-01
**Purpose:** Verify that `ccop-official/CCoP---Second-Edition_Revision-One.pdf`, as parsed by Docling, contains sections 5.3 and 5.4 text verbatim before any chunker intervention. This audit establishes that the root cause of bug #10 (context_recall=0 for B3-001) lies in the clause-aware chunker, not in the Docling parser.

---

## Audit Configuration

- **PDF parsed:** `ccop-official/CCoP---Second-Edition_Revision-One.pdf`
- **Parser:** `rag.ingestion.parsers.docling_parser.parse_ccop_pdf_with_docling` (Classic pipeline)
- **Markdown output length:** 151,269 characters
- **Method:** Direct Python invocation against the parser; no chunker involved

---

## PASS/FAIL Gate Results

| Check | Result | Evidence |
|-------|--------|----------|
| Section 5.3 heading present | **PASS** | `## 5.3 Privileged Access Management` found at pos 80,418 |
| Section 5.4 heading present | **PASS** | `## 5.4 Domain Controller` found at pos 81,883 |
| 5.3.1 clause heading present | **PASS** | `## 5.3.1 With respect to privileged accounts, the CIIO shall:` found at pos 80,918 |
| 5.4.1 clause heading present | **PASS** | `## 5.4.1 The CIIO shall implement mechanisms and processes to:` found at pos 82,098 |
| 'Privileged Access Management' found | **PASS** | 2 occurrences (1 in TOC, 1 in section body) |
| 'individual accountability' found | **NOT FOUND** | Phrase absent from this document; not a bug — this phrase is from a different CCoP section |
| 'individual authentication' found | **NOT FOUND** | Phrase absent from this document; not a bug — see note below |
| 'multi-factor authentication' found | **PASS** | 1 occurrence in 5.3.1(c) body |
| CLAUSE_PATTERN matches 5.3/5.4 | **FAIL** | 0 hits — root cause of bug #10 (see root cause analysis) |

**Overall gate: PASS** — Sections 5.3 and 5.4 are present in Docling output. Root cause is the chunker, not the parser.

Note on absent phrases: "individual accountability" and "individual authentication" do not appear in CCoP---Second-Edition_Revision-One.pdf. These phrases may exist in supplementary CCoP documents (auditing guidelines, security-by-design framework). Their absence does not affect the audit gate — the bug #10 root cause is confirmed independently via CLAUSE_PATTERN analysis below.

---

## Section 5.3 — First 500 Characters

```
## 5.3 Privileged Access Management

Privileged accounts on a network are prime targets for malicious exploitation because they
usually have more authority and access to resources.  An attacker who has access to these
accounts could potentially move about in the network and access privileged resources to gain
unauthorised and persistent access to the entire system. Therefore, privileged access must be
subject to tighter access control and greater monitoring.

## 5.3.1 With respect to privileged accounts, the CIIO shall:

- (a) Ensure that privileged access (i.e., administrative access) is granted only to selected
      accounts authorised to have such access;
- (b) Maintain an updated inventory of privileged accounts including details of the permissions
      and privileges assigned to each account;
- (c) Implement multi-factor authentication where privileged accounts are used to access the CII...
- (d) Ensure that privileged access is initiated from a cybersecurity hardened environment...
```

---

## Section 5.4 — First 500 Characters

```
## 5.4 Domain Controller

Domain controllers are servers that are responsible for authenticating user access to a network.
During a cybersecurity incident, the domain controller is one of the primary targets as it
contains data that a cyber threat actor could use to cause massive damage. Therefore, it is
important to have mechanisms in place to monitor for anomalies.

## 5.4.1 The CIIO shall implement mechanisms and processes to:

- (a) Monitor for changes to the trust relationships established between domains; and
- (b) Identify anomalies in the trust relationships and trigger an alert for investigation
      when any anomaly is detected.
```

---

## Root Cause Analysis: Why Sections 5.3 and 5.4 Are Missing From Qdrant

### Heading Format Discrepancy

Docling's Classic pipeline emits CCoP headings in two formats depending on the structural level:

| Format | Example | Count in Document |
|--------|---------|-------------------|
| Bare digit (no prefix) | `5.2.2 The CIIO shall perform a review...` | 171 occurrences |
| Markdown `##` heading | `## 5.3 Privileged Access Management` | 56 occurrences |

The current `CLAUSE_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+?)$", re.MULTILINE)` matches only the bare-digit format (171 hits). It produces **0 matches** against `##`-prefixed headings.

Sections 5.3, 5.3.1, 5.4, 5.4.1 — and 51 other section headings — are all emitted with `##` prefix by Docling. The chunker loop never finds a clause boundary at these lines, so the text continues to accumulate as part of the preceding chunk (the 5.2.2 bare-digit chunk). This is the exact failure described in bug #10: "5.3 header + the opening line of 5.3.1 got glued onto the tail of the 5.2.2 chunk."

Affected headings include: all X.Y section headings (51 entries) and 5 X.Y.Z clause headings (5.3.1, 5.4.1, 5.5.3, 5.7.2, 10.1.2).

### Item-Letter Sub-Items

Items `(a)`, `(b)`, `(c)`, `(d)` appear as markdown list items (`- (a) Ensure...`) within the clause body, not as standalone headings. The plan's reference to `5.3.1(c)` notation as a potential regex boundary reflects bug #10 analysis text, but in practice the actual document uses `- (a)` list syntax. The chunker fix targets the `##` prefix gap; item-letter sub-items stay embedded in parent clause text per the CONTEXT.md decision.

### Required Fix

Extend `CLAUSE_PATTERN` to match both heading formats:
```
^(?:##\s+)?(\d+(?:\.\d+)*(?:\([a-z]\))?)\s+(.+?)$
```

This captures:
- `## 5.3 Privileged Access Management` → clause number `5.3`
- `## 5.3.1 With respect to...` → clause number `5.3.1`
- `5.2.2 The CIIO shall perform...` → clause number `5.2.2` (existing behavior preserved)

---

## Summary

The Docling parser correctly extracts all sections including 5.3 and 5.4. The bug is entirely within `clause_aware_chunker.py`: the `CLAUSE_PATTERN` regex does not match `##`-prefixed markdown headings that Docling emits for section-level and some clause-level entries. Extending the regex to handle the `##` prefix will restore 56 missing clause boundaries and fix bug #10.
