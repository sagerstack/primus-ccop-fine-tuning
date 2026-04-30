# Ground-Truth Remap Proposal — Evidence-Backed from Authoritative PDFs

**Scope:** 179 actionable flags (excluding 13 B21 by-design hallucination flags)

**Source of truth:** `ccop-official/*.pdf` parsed via Docling to `/tmp/ccop-markdown/`

**Method:** For each cluster of flagged test cases, we consulted the authoritative CCoP 2.0 regulation PDF and supporting CSA guidance PDFs to identify the correct primary clause and, where the question inherently requires methodology or process detail beyond the regulation, the relevant supporting-document clause.

**Decision scheme:**
- **REMAP-ALL** — all test cases in cluster map to one correct clause
- **REMAP-PER-CASE** — clause varies per test case (row-by-row proposal table)
- **DEPRECATE** — no authoritative support exists; remove from benchmark

---

## Cluster 1 — B08_RISK_BASED_PRIORITIZATION (50 flags, 25 test cases)

**Current (wrong) citations:** col 7 = `4`, col 8 = `4.2.1` (or in-text `4.2`)
**Reason wrong:** CCoP 2.0 Chapter 4 is "Identification" with subsections 4.1 (CII Identification) and 4.2 (Asset Management). There is no clause 4.2.1. Moreover, the subject of all 25 test cases is **risk prioritization by likelihood × impact** — this is explicitly covered in CCoP 2.0 **§3.2 Risk Management**, not Chapter 4.

**Evidence from CCoP 2.0 (`ccop-2.0.md`, lines 287–305):**

> **3.2.2** The CIIO shall include the following steps in the cybersecurity risk assessment methodology:
> - (a) Risk identification - identification of CII assets and cybersecurity threats, including threats identified from threat modelling, threat hunting, post-incident reviews of cybersecurity incidents, and the construction of risk scenarios;
> - (b) Risk analysis - **analysis of each risk scenario to determine the likelihood of occurrence and potential impact**;
> - (c) Risk evaluation - **determining, documenting and prioritising risks**; and
> - (d) Risk response - treatment and monitoring of each risk to keep the risk level within the organisation's risk tolerance level.

**Evidence from Risk Assessment Guide (`risk-assessment-guide.md`, lines 257–379):**

> **§4.2 Step 2: Risk Analysis** → Task A (Determine Likelihood — 5-point scale 'Rare' to 'Highly Likely' via Discoverability / Exploitability / Reproducibility); Task B (Determine Impact — 5-point scale 'Negligible' to 'Very Severe').
>
> **§4.3 Step 3: Risk Evaluation** → Task A (Determine and Prioritise Risk using **5-by-5 Risk Matrix** = Likelihood × Impact).

### Proposal: **REMAP-ALL**

| Field | Current | Proposed |
|-------|---------|----------|
| col 7 (CCoP Section) | `4` | `3` |
| col 8 (Clause Refs) | `4.2.1` | `3.2.2(b), 3.2.2(c)` |
| Supporting citation (col 8 appendix) | — | `Risk Assessment Guide §4.2, §4.3` |
| In-text `4.2` references | `4.2` | `3.2.2` |

**Apply to:** B08-001 through B08-025 (all 25 cases)

---

## Cluster 2 — B09_RISK_IDENTIFICATION_RESIDUAL_RISK (25 flags, 25 test cases)

**Current (wrong) citation:** col 8 = `4.2.1`
**Reason wrong:** Same structural error as B08 — clause 4.2.1 does not exist. The test case topic is **risk identification from misconfiguration / residual risk tracking**, which is explicitly §3.2.

**Evidence from CCoP 2.0 (`ccop-2.0.md`, lines 278–311):**

> **3.2.1** The CIIO shall establish and implement a cybersecurity risk management framework … including (c) Cybersecurity risk assessment methodology …
>
> **3.2.2(a)** Risk identification - identification of CII assets and cybersecurity threats, including threats identified from threat modelling, threat hunting, post-incident reviews …
>
> **3.2.4** The CIIO shall maintain and keep updated a **risk register** for each CII. The risk register shall record … (g) **Residual risk ratings**; and (h) Risk owner.
>
> **3.2.5** The CIIO shall ensure that all cybersecurity risks listed in the risk register are reviewed and monitored regularly to ensure that the thresholds or limits for **residual risk** identified in accordance with clause 3.2.1(e) are not breached.

**Evidence from Risk Assessment Guide (`risk-assessment-guide.md`, lines 185–255):**

> **§4.1 Step 1: Risk Identification** → Task A (Identify Assets — crown jewels, stepping stones); Task B (Threat Modelling); Task C (Construct Risk Scenarios — asset, threat event, vulnerability, consequence).

### Proposal: **REMAP-ALL**

| Field | Current | Proposed |
|-------|---------|----------|
| col 7 (CCoP Section) | `4` | `3` |
| col 8 (Clause Refs) | `4.2.1` | `3.2.2(a), 3.2.4, 3.2.5` |
| Supporting citation | — | `Risk Assessment Guide §4.1` |

**Apply to:** B09-001 through B09-025 (all 25 cases)

---

## Cluster 3 — B22_WAIVER_EXCEPTION_REASONING (20 flags, 20 test cases)

**Current (wrong) citation:** col 7 = `11`, col 8 = `11.7`
**Reason wrong:** CCoP 2.0 Chapter 11 does not exist. "11.7" is a confusion with **Cybersecurity Act 2018 §11(7)**, which is the statutory basis for waivers. The CCoP clause that operationalises this is **§1.6 Waiver**.

**Evidence from CCoP 2.0 (`ccop-2.0.md`, lines 222–229):**

> **1.6 Waiver**
>
> **1.6.1** The Commissioner may waive the application of any specific provisions of this Code to a CIIO under **section 11(7) of the Act**.
>
> **1.6.2** A CIIO can request for waiver from specific provisions of this Code under **section 11(7) of the Act** by submitting a written request to the Commissioner with the justifications supporting the request.
>
> **1.6.3** Any waiver, if granted by the Commissioner, shall be subject to such terms and conditions as the Commissioner may specify and may, without limitation, be for a fixed period or effective until the occurrence of a specific event.

### Proposal: **REMAP-ALL**

| Field | Current | Proposed |
|-------|---------|----------|
| col 7 (CCoP Section) | `11` | `1` |
| col 8 (Clause Refs) | `11.7` | `1.6.1, 1.6.2, 1.6.3` |
| Supporting citation | — | `Cybersecurity Act 2018 §11(7)` |

**Apply to:** B22-001 through B22-020 (all 20 cases)

**Also applies to:** B3-004, B3-011 (B03 cluster, same `11.7` citation — see medium clusters section)

---

## Cluster 4 — B24_INCIDENT_RESPONSE_GUIDANCE (38 flags, 24 test cases)

**Current (wrong) citations:** col 7 = `CCoP 2.0 Section 8`, col 8 = combinations of `8.2`, `8.3`, `8.4`, `8.5`, `8.6`, `8.7`, `9.4`, `9.5`

**Reason wrong:** Chapter 8 is **Cyber Resiliency** (§8.1 Backup and Restoration Plan; §8.2 Business Continuity Plan / Disaster Recovery Plan). Clauses 8.3–8.7 **do not exist**. Incident response is Chapter **7**, specifically **§7.1 Incident Management**.

**Evidence from CCoP 2.0 (`ccop-2.0.md`, lines 771–804):**

> **7.1 Incident Management**
>
> **7.1.1** The CIIO shall establish a Cybersecurity Incident Response Plan … The Plan establishes:
> - **(a)** A Cybersecurity Incident Response Team ('CIRT') structure, including clearly defined roles and responsibilities …
> - **(b)** An incident reporting structure which sets out how the CIIO will comply with its reporting obligations under the Act …
> - **(c)** Communication and coordination structures to ensure the timely escalation of cybersecurity incidents to the CIRT and to the senior management of the CIIO;
> - **(d)** Thresholds and procedures to activate the incident response and CIRT;
> - **(e)** Engagement protocols with relevant external parties, including vendors for forensic or recovery services and law enforcement agencies …
> - **(f)** A communication plan to communicate information relating to a cybersecurity incident to internal and external stakeholders;
> - **(g)** Processes and procedures to **contain** a cybersecurity incident, investigate the cause and impact …, and to **restore** the CII's operations;
> - **(h)** Processes and procedures to **collect and preserve digital forensic evidence** before initiating the recovery process, in order to support investigations;
> - **(i)** A **post-incident review** process to identify and implement corrective measures to prevent a recurrence.
>
> **7.1.2** The CIIO shall ensure that the CIRT is trained and equipped …
>
> **7.1.3** The CIIO shall establish procedures to reset the Kerberos Ticket Granting Ticket account …
>
> **7.1.4** The CIIO shall establish and implement processes to identify, investigate and address the **root causes** that contributed to each cybersecurity incident …
>
> **7.1.5** The CIIO shall communicate the Cybersecurity Incident Response Plan to all persons who use, operate and manage the CII …
>
> **7.1.6** The CIIO shall review the Cybersecurity Incident Response Plan … at least once every 12 months.
>
> **7.1.7** The CIIO shall also review the Cybersecurity Incident Response Plan when there are material changes to the CII cyber operating environment or incident response requirements.

### Proposal: **REMAP-PER-CASE**

The question topics vary, so mapping is per-row. Proposed primary clauses are the relevant 7.1.x sub-clauses; where a question also touches on BCP/DRP recovery or crisis communication, secondary citations from 7.2 or 8.2 are included.

| Test ID | Current col 8 | Question topic | Proposed col 8 (primary) | Secondary / supporting |
|---------|---------------|----------------|--------------------------|------------------------|
| B24-001 | 8.2, 8.4 | Ransomware on patient records — IR actions | `7.1.1(b), 7.1.1(g), 7.1.1(h)` | `8.2.1` (BCP) |
| B24-002 | 8.2, 8.4 | Ransomware on SCADA + water distribution | `7.1.1(b), 7.1.1(g), 7.1.1(h)` | `8.2.1` (DRP) |
| B24-003 | 8.3, 8.4, 8.7 | Payment-processing ransomware after failover | `7.1.1(b), 7.1.1(g), 7.1.1(i), 7.1.4` | `8.2.1` |
| B24-004 | 8.2, 8.4 | Ransomware on admin only (OT safe) | `7.1.1(d), 7.1.1(g)` | `8.2.1` |
| B24-005 | 8.2, 8.3 | Weekend ransomware / pay-ransom decision | `7.1.1(c), 7.1.1(d), 7.1.1(e)` | — |
| B24-006 | 8.3, 8.4, 8.6 | Data exfiltration (telecom) | `7.1.1(b), 7.1.1(f), 7.1.1(h)` | — |
| B24-007 | 8.2, 8.3, 8.4 | Unauthorized access (govt employee directory) | `7.1.1(b), 7.1.1(g), 7.1.1(h)` | — |
| B24-008 | 8.4 | SCADA config files accessed remotely | `7.1.1(b), 7.1.1(g), 7.1.4` | — |
| B24-009 | 8.4, 8.6, 8.7 | Exposed DB backup containing health records | `7.1.1(b), 7.1.1(h), 7.1.1(i), 7.1.4` | — |
| B24-010 | 8.4, 8.6 | Breach with unclear exfil scope | `7.1.1(g), 7.1.1(h)` | — |
| B24-011 | 9.5 | (see medium cluster B24 `9.5`) | `7.1.1(i), 7.1.4` | — |
| B24-012 | 8.3, 8.4 | Air traffic intermittent disruptions | `7.1.1(d), 7.1.1(g)` | `8.2.1` |
| B24-013 | 9.5 | (see medium cluster B24 `9.5`) | `7.1.1(i), 7.1.4` | — |
| B24-014 | 8.4, 8.6 | SCADA visibility loss (substations) | `7.1.1(d), 7.1.1(g)` | `8.2.1` |
| B24-015 | 8.2, 8.4 | Telemetry outage (pumping stations) | `7.1.1(d), 7.1.1(g)` | `8.2.1` |
| B24-016 | 8.3, 8.6 | Insider data exfiltration (designs) | `7.1.1(g), 7.1.1(h)` | — |
| B24-017 | 7.2, 8.3, 8.6 | Third-party vendor breach → pivot | `7.1.1(e), 7.1.1(g)` | `7.2.2` (crisis comms) |
| B24-018 | 7.3, 8.3, 8.6 | Stale contractor credentials abused | `7.1.1(g), 7.1.4` | — |
| B24-019 | 8.4, 8.6 | Phishing targeting internal IT | `7.1.1(d), 7.1.1(f)` | — |
| B24-020 | 8.4, 9.4 | Accidental DB deletion, no backup | `7.1.1(g)` | `8.1.1, 8.1.2` (backup failure) |
| B24-021 | 7.2, 8.3 | Fake-vendor social engineering (6 months) | `7.1.1(g), 7.1.4` | `7.2.2` |
| B24-023 | 8.5 | (singleton) | `7.1.1(g)` | — |
| B24-024 | 8.2, 8.3, 8.4 | Simultaneous DDoS + ransomware + … | `7.1.1(c), 7.1.1(d), 7.1.1(g)` | `8.2.1` |
| B24-025 | 5.2, 8.3, 8.6, 8.7 | 6-month-old undetected incident | `7.1.1(b), 7.1.1(h), 7.1.1(i), 7.1.4` | — |

**Note:** Wherever `col 7 = "CCoP 2.0 Section 8"` appears for a B24 row, update to `"CCoP 2.0 Section 7"`.

### BONUS finding — B24-022 (unflagged by Pass-1, semantically wrong)

**Not currently in patcher.** Pass-1 regex gate accepted col 8 = `8.1,8.2` because both clauses exist in CCoP. But Pass-2 semantic inspection reveals the topic is **threat intelligence pre-incident**, which §8.1 (Backup and Restoration) and §8.2 (BCP/DRP) do not cover.

**ER text (current):**
> Section 8.1 requires incident management policy include threat intelligence consumption … Pre-incident preparation is Section 8.2 (IR plan) and Section 5.1 (threat intelligence).

**All three citations are wrong:**
- §8.1 is Backup/Restoration, not IR policy
- §8.2 is BCP/DRP, not IR plan — §7.1.1 is the IR plan clause
- §5.1 is Security Policies / authentication, not threat intelligence — §6.4 is threat intel

**Proposed (if user approves scope expansion):**
- col 7: `CCoP 2.0 Section 8` → `7`
- col 8: `8.1,8.2` → `6.4.1, 6.4.3, 7.1.1(a), 7.1.1(d) [support: 7.3.3(a)]`
- col 11 in-text patches:
  - `Section 8.1 requires incident management policy` → `Section 6.4 requires the CIIO to establish mechanisms to obtain and act on threat intelligence; Section 7.1.1(a) establishes the IR plan`
  - `Section 8.2 (IR plan)` → `Section 7.1.1 (IR plan)`
  - `Section 5.1 (threat intelligence)` → `Section 6.4 (Cyber Threat Intelligence)`

**Defer to user:** This is an unflagged finding (outside the Pass-1 audit scope that drives this proposal). Option to either: (A) include in Phase C patcher, (B) leave for a future Pass-2 semantic audit phase, or (C) mark as separate follow-up issue.

---

## Cluster 5 — B07_GAP_IDENTIFICATION_QUALITY — `4.2.2` × 4

**Current (wrong) citation:** `4.2.2` — does not exist in CCoP 2.0. Topic of B07-001, -002, -003, -005 inspection: gap-severity determination, which is **§3.2.2** (risk assessment methodology).

### Proposal: **REMAP-ALL**

| Field | Current | Proposed |
|-------|---------|----------|
| col 8 (Clause Refs) | `4.2.2` | `3.2.2(b), 3.2.2(c)` |
| Supporting | — | `Risk Assessment Guide §4.2, §4.3` |

**Apply to:** B07-001, B07-002, B07-003, B07-005

---

## Cluster 6 — B02_COMPLIANCE_CLASSIFICATION — `5.6.4` × 4

**Current citation:** `5.6.4` — **confirmed non-existent**. CCoP 2.0 §5.6 Network Security contains only `5.6.1`, `5.6.2`, `5.6.3`.

**Topic correction after inspecting ER text:** All four cases (B2-003, B2-010, B2-014, B2-024) are about **patch management**, not Network Security. NN's `5.6.1` suggestion is wrong-chapter. The correct clause is **§5.10.1(e)** — *"Applying security patches in a timely manner"* under the Patch Management process.

### ⚠ CONCERN — fabricated timelines in ER text

The expected_response strings in these four B2 rows embed specific timelines (`"within 14 days"`, `"within 30 days"`) that are **NOT present in CCoP 2.0 §5.10.1 or any supporting document**. §5.10.1(e) says only *"timely manner"* with no day-count. The 14/30-day figures appear to be fabricated or imported from a different standard (possibly NIST SP 800-40 or a generic industry norm) and then attributed to CCoP.

**Options for user decision:**
1. **Accept §5.10.1(e) citation, leave ER timelines as-is** — citation is now correct, but ER claims "CCoP requires X within 14/30 days" which is not actually what the Code says. Downstream evaluation will continue scoring against the fabricated claim.
2. **Deprecate all 4 cases** — mark as out-of-scope (CCoP does not mandate specific patch timelines).
3. **Rewrite ER to match actual text** — replace day-counts with "timely manner" language per §5.10.1(e), preserving the test case but grounding it in actual CCoP text.

**Recommendation:** Option 3 preserves test coverage while restoring correctness. Option 1 is the minimum structural fix (citation only) and is what the current patcher encodes (`_b02_564_rule` → §5.10.1(e)). Option 3 requires manual ER edits not yet in the patcher.

### Proposal: **REMAP-ALL to §5.10.1(e)** (citation only — ER timeline resolution pending user decision on Options 1/2/3)

---

## Cluster 7 — B03_CONDITIONAL_COMPLIANCE_REASONING — `11.7` × 2

Same root cause as Cluster 3 (B22). The term "11.7" is an erroneous rendering of Cybersecurity Act §11(7).

### Proposal: **REMAP-ALL**

| Field | Current | Proposed |
|-------|---------|----------|
| col 8 | `11.7` | `1.6.1, 1.6.2, 1.6.3` |
| Supporting | — | `Cybersecurity Act 2018 §11(7)` |

**Apply to:** B3-004, B3-011

---

## Cluster 8 — B03 `4.2` × 2

**Rows:** B3-006, B3-021.

**Topic correction after inspecting ER text:** Both cases are **templated Section 11(7) waiver** cases — their expected_response strings are identical to B3-005/019/024 ("A Section 11(7) waiver may be applicable if genuine technical constraints exist"). The `4.2` citation in col 8 is simply a different symptom of the same B03 template bug.

### Proposal: **REMAP-ALL → same target as Cluster 7 / B22**

| Field | Current | Proposed |
|-------|---------|----------|
| col 7 | `4` | `1` |
| col 8 | `4.2` | `1.6.1, 1.6.2, 1.6.3 [support: Cybersecurity Act 2018 §11(7)]` |

**Apply to:** B3-006, B3-021 (encoded in SINGLETONS cluster — matches B3-005/019/024 pattern).

### Latent broader issue — B03 templating

Inspection of `b03_conditional_compliance_reasoning.jsonl` shows **28 of 29 B3 cases** have `clause_reference: ["Section 2"]` in their JSONL `metadata` (only B3-001 differs). The audit flagged only 7 B3 rows because the rest have a numeric `col 8` (e.g., `5.3.2`, `8.5`, `9.4`) that happens to pass the regex gate even though they're all variants of the same template. The `["Section 2"]` placeholder in the JSONL is itself invalid (CCoP §2 = "Audit", not general compliance).

**Scope question for user:**
- **A (current plan):** Fix only the 7 rows flagged by audit (B3-004, B3-005, B3-006, B3-011, B3-019, B3-021, B3-024).
- **B (scope expansion):** Fix all 29 B3 cases by retiring the `["Section 2"]` placeholder and mapping each to its actual topical clause.

Option B requires 22 additional row-level remaps (one per remaining B3 case). Defer to user — not included in current patcher.

---

## Cluster 9 — B05_CONTROL_COMPREHENSION — `5.2.3` × 2

**Rows:** B05-002, B05-019. **Confirmed non-existent**: CCoP §5.2 Account Management contains only `5.2.1`, `5.2.2`.

**Topic correction after inspecting ER text:** Both cases are about **MFA** (Multi-Factor Authentication), not generic Account Management. §5.2 has no MFA clause — MFA is defined in:
- `§5.3.1(c)` — MFA for privileged accounts (PAM)
- `§5.7.2(b)` — MFA for remote connections
- `§5.1.2` — generic authentication requirement that implicitly covers MFA

### Proposal: **REMAP-ALL → `5.1.2, 5.3.1, 5.7.2`** (matches MFA singleton bundle used elsewhere, e.g. B1-017, B2-001, B06-002, B07-027, B12-001)

| Field | Current | Proposed |
|-------|---------|----------|
| col 8 | `5.2.3` | `5.1.2, 5.3.1, 5.7.2` |
| col 11 | "Section 5.2.3" | "Section 5.3.1(c)" |

---

## Cluster 10 — B07 chapter-5 clauses (`5.2.3, 5.2.4, 5.2.5, 5.2.6`) & others (`5.4.2, 5.4.4, 6.3.4`)

**Verified non-existent in CCoP 2.0:** `5.2.3`, `5.2.4`, `5.2.5`, `5.2.6` (§5.2 has only 5.2.1, 5.2.2). Other Ch-5 citations (`5.4.2`, `5.4.4`, `6.3.4`) to be verified per-row. NN suggestions (e.g. 7.1.4 for `5.2.3`, `5.2.4`, `5.2.6`, pointing to root-cause analysis / gap identification) suggest several of these B07 questions are actually about IR/post-incident gaps, not access control.

### Proposal: **REMAP-PER-CASE** after inspecting each question. Candidates: `5.2.1, 5.2.2` (if access-control in scope), `7.1.4` (if root-cause / IR in scope), `3.2.2` (if risk in scope).

---

## Cluster 11 — B24 `9.5` × 2 (B24-011, B24-013)

Not incident response but BCP/DRP recovery-related (NN suggests `8.2.1`). If questions are about recovery timing, REMAP to `8.2.1`; if about post-incident lessons, REMAP to `7.1.4` + `7.1.1(i)`.

---

## Singletons (29 non-B21 rows) — Verified Per-Row Remap Table

**Verification method:** For each row, read the question + expected_response from the source JSONL, cross-reference against CCoP 2.0 PDF chapter/clause boundaries (see §5.1.1-4, §5.2.1-2, §5.3.1, §5.4.1, §5.5.1-2, §5.7.1-2, §8.2.1-4, §10.2.1-7 — `/tmp/ccop-markdown/ccop-2.0.md`). Key facts verified from the regulation text:
- **§5.1** has only 5.1.1–5.1.4 (no 5.1.5, no standalone MFA clause at §5.1)
- **§5.2** has only 5.2.1, 5.2.2 (account mgmt + review)
- **§5.3** has only 5.3.1 (privileged access; sub-item (c) is MFA for privileged accounts)
- **§5.4** has only 5.4.1 (domain controller)
- **§5.7** has 5.7.1 and 5.7.2 — **§5.7.2(b) explicitly mandates MFA for remote connections**
- **§8** has only 8.1 and 8.2 (no 8.5)
- **§9** has only 9.1 and 9.2 (no 9.3, 9.4, 9.5)
- **§10.2** is OT-specific (segmentation, authentication, fail-safe)

### Per-Row Proposals

| Test ID | Current clause | Proposed primary | Supporting | Rationale (from ER/question) |
|---------|---------------|------------------|------------|------------------------------|
| B1-001 | Section 11 Cybersecurity Act, RESPONSE-TO-FEEDBACK Q2.2-2.3 | `1.2.1, 1.4.1` | keep `Cybersecurity Act 2018 §7`, keep `RESPONSE-TO-FEEDBACK Q2.2-2.3` | CII digital-boundary scope — §1.2 defines CII; §1.4 legal effect/application |
| B1-017 | `5.1.5, 5.3` | `5.1.2, 5.3.1, 5.7.2` | — | CCoP 1→2 access control gaps: auth controls + PAM + remote MFA |
| B2-001 | `5.1.5` | `5.1.2, 5.7.2` | — | VPN SMS-OTP compliance — **§5.7.2(b) explicitly requires MFA for remote connection**. In-text `5.1.5` in ER also replaced → `5.7.2`. |
| B3-005 | `Section 2` (JSONL) / `5.3.2` (Excel) | `1.6.1, 1.6.2, 1.6.3` | `Cybersecurity Act 2018 §11(7)` | ER explicitly mentions "Section 11(7) waiver may be applicable" |
| B3-006 | `Section 2` (JSONL) / `4.2` (Excel) | `1.6.1, 1.6.2, 1.6.3` | `Cybersecurity Act 2018 §11(7)` | Templated waiver case — identical ER to B3-005 (see Cluster 8) |
| B3-019 | `Section 2` (JSONL) / `8.5` (Excel) | `1.6.1, 1.6.2, 1.6.3` | `Cybersecurity Act 2018 §11(7)` | Same template as B3-005 |
| B3-021 | `Section 2` (JSONL) / `4.2` (Excel) | `1.6.1, 1.6.2, 1.6.3` | `Cybersecurity Act 2018 §11(7)` | Templated waiver case — identical ER to B3-005 (see Cluster 8) |
| B3-024 | `Section 2` (JSONL) / `9.4` (Excel) | `1.6.1, 1.6.2, 1.6.3` | `Cybersecurity Act 2018 §11(7)` | Same template as B3-005 |
| B05-013 | `4.3` | `1.6.1, 1.6.2, 1.6.3, 3.2.1` | `Cybersecurity Act 2018 §11(7)` | Legacy system exemption — waiver mechanism + risk mgmt framework for compensating controls |
| B05-015 | `9.3.1` | `3.8.1, 3.8.2, 3.8.3` | — | Hardware/software supply chain → §3.8 Outsourcing & Vendor Mgmt |
| B05-016 | `5.3.4` | `5.11.1, 5.11.2, 5.11.3, 5.11.4` | — | BYOD/mobile devices → §5.11 Portable Computing Devices |
| B05-018 | `5.5.5` | **DEPRECATE** | — | Cross-border data transfer — not an explicit CCoP 2.0 requirement (handled by PDPA, not CSA). ER admits "CSA notification may be required" → out of scope. |
| B06-002 | `5.2.3` | `5.1.2, 5.3.1, 5.7.2` | — | MFA objective — generic auth + PAM (5.3.1(c)) + remote (5.7.2(b)) |
| B06-013 | `5.2.5` | `5.2.1, 5.2.2` | — | Periodic access review/privilege creep — §5.2.1(d)(e) monitoring/deletion, §5.2.2 mandatory 12-month review |
| B06-018 | `7.4.1` | `8.2.1, 8.2.2` | — | BCP/cyber resilience → §8.2 BCP/DRP |
| B06-019 | `4.2.1` | `3.2.1, 3.2.2` | `Risk Assessment Guide §3` | Risk assessment purpose → §3.2 Risk Management framework |
| B07-006 | `5.2.4` | `5.2.1, 5.3.1` | — | Shared admin accounts → §5.2.1(c) *"Ensure that shared user accounts are not created unless necessary"* + §5.3.1 (PAM) |
| B07-007 | `5.2.5` | `5.2.2, 5.3.1` | — | 3-year review lapse on admin accounts → §5.2.2 (≥12-month review) + §5.3.1 (privileged accounts) |
| B07-008 | `5.2.4` | `5.2.1, 5.3.1` | — | Service accounts with excessive permissions → §5.2.1(a) *"Grant to each account only the minimum privileges necessary"* + §5.3.1 (PAM) |
| B07-010 | `5.2.6` | `5.3.1` | — | Break-glass/emergency access → §5.3.1 PAM scope |
| B07-015 | `6.3.4` | `6.2.1, 6.2.2, 6.2.3` | — | Alert threshold tuning/monitoring → §6.2 Monitoring & Detection |
| B07-017 | `5.4.2` | `5.5.1, 5.5.2, 10.2.1` | — | OT flat network — §5.5 segmentation + §10.2.1 OT CII separation |
| B07-018 | `5.4.4` | `5.7.1, 5.7.2, 10.2.3` | — | Vendor direct OT connections → §5.7 remote access + §10.2.3 OT-vs-enterprise auth separation |
| B07-027 | `5.2.3` | `5.1.2, 5.7.2` | — | MFA exemption policy — generic auth + remote (5.7.2(b)) |
| B12-001 | `5.2.3` | `5.1.2, 5.3.1, 5.7.2` | `Auditing Guidelines for CII` | MFA audit perspective — triple-clause coverage |
| B12-005 | `4.2.2` | `4.1.1, 4.1.2` | `Auditing Guidelines for CII` | CII asset inventory → §4.1 Asset Management |
| B12-008 | `7.4.1` | `8.2.1, 8.2.2, 8.2.3, 8.2.4` | `Auditing Guidelines for CII` | BCP audit → §8.2 |
| B12-014 | `5.2.5` | `5.2.1, 5.2.2` | `Auditing Guidelines for CII` | Access control review audit |
| B12-016 | `9.3.1` | `3.8.1, 3.8.2, 3.8.3, 3.8.4, 3.8.5` | `Auditing Guidelines for CII` | Supply chain audit → §3.8 Outsourcing & Vendor Mgmt |
| B12-020 | `4.2.1` | `3.2.1, 3.2.2` | `Auditing Guidelines for CII`, `Risk Assessment Guide §3` | Risk-based methodology audit → §3.2 |

### Section (col 7) Corrections

The `CCoP Section` column (col 7) for all singleton rows above shall be updated to match the chapter of the first listed primary clause (e.g. B05-013 → `1`; B05-015 → `3`; B05-016 → `5`; B07-015 → `6`; etc.).

### Deprecation (1 row)

- **B05-018** — cross-border data transfer is not a CCoP 2.0 requirement. Mark `status: "deprecated"`, `deprecated_reason: "Cross-border data transfer scoped to PDPA, not CCoP 2.0"`. Retained per CONTEXT.md locked decision (no deletion).

### In-Text Citation Patches (Pass 2 fix-ups)

Several singletons have the old invalid citation embedded in `expected_response` text, not just in `metadata.clause_reference`. The patcher must also perform a textual substitution:

| Test ID | Old substring in ER | New substring |
|---------|--------------------|--------------|
| B2-001 | `Clause 5.1.5` / `Section 5.1.5` | `Clause 5.7.2(b)` / `Section 5.7.2` |
| B05-013 | `Section 4.3` | `Section 1.6 (Waiver)` |
| B05-015 | `Section 9.3.1` | `Section 3.8` |
| B05-016 | `Section 5.3.4` | `Section 5.11` |
| B06-002 | `Section 5.2.3` | `Section 5.3.1(c)` |
| B06-013 | `Section 5.2.5` | `Section 5.2.2` |
| B06-018 | `Section 7.4.1` | `Section 8.2` |
| B06-019 | `Section 4.2.1` | `Section 3.2` |
| B07-006 | `Section 5.2.4` | `Section 5.2.1(c)` |
| B07-007 | `Section 5.2.5` | `Section 5.2.2` |
| B07-008 | `Section 5.2.4` | `Section 5.2.1(a)` |
| B07-010 | `Section 5.2.6` | `Section 5.3.1` |
| B07-015 | `Section 6.3.4` | `Section 6.2` |
| B07-017 | `Section 5.4.2` | `Section 5.5` |
| B07-018 | `Section 5.4.4` | `Section 5.7` |
| B07-027 | `Section 5.2.3` | `Section 5.7.2` |
| B12-001 | `CCoP 2.0 5.2.3` | `CCoP 2.0 §5.3.1(c)` |
| B12-005 | `CCoP 2.0 4.2.2` | `CCoP 2.0 §4.1` |
| B12-008 | `CCoP 2.0 7.4.1` | `CCoP 2.0 §8.2` |
| B12-014 | `CCoP 2.0 5.2.5` | `CCoP 2.0 §5.2.2` |
| B12-016 | `CCoP 2.0 9.3.1` | `CCoP 2.0 §3.8` |
| B12-020 | `CCoP 2.0 4.2.1` | `CCoP 2.0 §3.2` |

---

## B21 — Audit-Exempt Tag (13 rows)

Action independent of remapping: add a column (e.g., `audit_exempt: true`) or sheet-level marker so future audit runs skip these rows. These intentionally cite non-existent clauses to test hallucination refusal.

**Rows:** B21-001, B21-004, B21-005, B21-008, B21-009, B21-010, B21-012, B21-016, B21-018, B21-019, B21-021 (+ Pass-2 dupes of -001, -010, -012)

---

## Summary of Proposed Edits

| Cluster | Scope | Action | Rows affected |
|---------|-------|--------|---------------|
| B08 | 25 | REMAP-ALL → `3.2.2(b), 3.2.2(c)` + RA Guide §4.2/§4.3 | B08-001..B08-025 |
| B09 | 25 | REMAP-ALL → `3.2.2(a), 3.2.4, 3.2.5` + RA Guide §4.1 | B09-001..B09-025 |
| B22 | 20 | REMAP-ALL → `1.6.1, 1.6.2, 1.6.3` + Act §11(7) | B22-001..B22-020 |
| B24 | 24 | REMAP-PER-CASE → 7.1.x variants (table above) | B24-001..B24-025 (exc. B24-022) |
| B07 `4.2.2` | 4 | REMAP-ALL → `3.2.2` | B07-001..005 |
| B03 `11.7` | 2 | REMAP-ALL → `1.6.x` | B3-004, B3-011 |
| B02 `5.6.4` | 4 | REMAP-ALL → `5.10.1(e)` (citation only; ER timeline claims flagged — see Cluster 6 CONCERN) | B2-003, B2-010, B2-014, B2-024 |
| B05 `5.2.3` | 2 | REMAP-ALL → MFA bundle `5.1.2, 5.3.1, 5.7.2` | B05-002, B05-019 |
| B24 `9.5` | 2 | REMAP-PER-CASE → `7.1.1(i), 7.1.4` | B24-011, B24-013 |
| B03 `4.2` | 2 | REMAP-ALL → Waiver `1.6.1, 1.6.2, 1.6.3` (in SINGLETONS) | B3-006, B3-021 |
| Singletons verified | 29 | REMAP-PER-CASE (table above) | B1, B2, B3, B05, B06, B07, B12 singletons |
| Singleton deprecations | 1 | DEPRECATE | B05-018 |
| B21 (all) | 13 | AUDIT-EXEMPT, no correction | B21-001..B21-021 (subset) |

**Net structural remaps:** 129 rows (~100 from major clusters + 29 verified singletons)
**Pass-1 audit flag coverage:** 100% — all 71 non-B08/B09/B22 Pass-1 flagged test IDs now have an encoded rule in the patcher (B24 per-row, B21 exempt, cluster rules, singletons, deprecate).
**Deprecations:** 1 row (B05-018)
**No-op (B21 exempt):** 13 rows
**Flagged for user decision (Cluster 6 CONCERN):** B02 `5.6.4` cluster — citation corrected to §5.10.1(e), but ER timeline claims (`14 days`, `30 days`) are fabricated and remain in the data pending user choice of Options 1/2/3.

---

## Next Steps (Phase B — User Approval)

For each cluster above, the user must confirm:
1. Whether to apply the REMAP-ALL proposals as-stated (yes / adjust / deprecate).
2. For REMAP-PER-CASE (B24 table), approve row-by-row or en bloc.
3. For B21, approve the audit-exempt tag approach.
4. For singletons & medium clusters needing verification, approve the verify-then-remap approach (I'll walk each row).

Once approved, **Phase C** applies the edits directly to `ground-truth/expert-validation/CCoP_V2_Test_Cases_Expert_Review.xlsx` (transactional edit, backup file first). Then the JSONL regeneration script (pending plan item) runs to rebuild all 18 benchmark files from the corrected Excel.
