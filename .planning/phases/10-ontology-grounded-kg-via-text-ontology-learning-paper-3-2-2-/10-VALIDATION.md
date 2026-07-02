---
phase: 10
slug: ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-02
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from the `## Validation Architecture` section of `10-RESEARCH.md`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (poetry-managed; run from `src/`) |
| **Config file** | `src/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `cd src/ && poetry run pytest -m "not integration" -q` |
| **Full suite command** | `cd src/ && poetry run pytest` |
| **Estimated runtime** | ~TBD (planner to fill per plan) |

---

## Sampling Rate

- **After every task commit:** Run `cd src/ && poetry run pytest -m "not integration" -q` (scoped to touched module where possible)
- **After every plan wave:** Run `cd src/ && poetry run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green + smallest-slice E2E for the wave's vertical seam
- **Max feedback latency:** TBD (planner to fill)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| _(planner + gsd-nyquist-auditor to populate per task)_ | | | | | | | | | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] _(planner to enumerate stub test files + fixtures per REQ)_

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Ontology curation gates (D-14) — user approval of Method-C draft + Method-B reconcile | REQ (ontology-lock) | Requires human judgement / oversight-not-authoring role | Present markup table (type \| definition \| example terms \| provenance \| flagged ambiguities) + benchmark coverage check; capture approval |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < TBDs
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
