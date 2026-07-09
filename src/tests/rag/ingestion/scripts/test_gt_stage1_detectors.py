"""Unit tests for the GT Stage-1 deterministic defect detectors."""

from __future__ import annotations

from rag.ingestion.scripts.gt_stage1_detectors import (
    detect_cite_kf,
    detect_family,
    detect_forbidden,
    detect_leak,
    extract_ccop_citations_from_source,
    extract_ccop_clause_tokens,
    looks_like_required_element,
    question_answer_overlap,
)

# A small inventory stand-in: real CCoP clauses, deliberately excluding the
# hallucinated ones (5.1.5, 8.3, 5.9.7) confirmed absent in step (b).
CCOP_IDS = {"5.1.2", "5.2.2", "5.3.1", "5.3.1(c)", "4.1.1", "5.7.2(b)", "1.6.1", "3.2.2"}


# --- extractor -------------------------------------------------------------

def test_extract_dotted_clause_tokens():
    toks = extract_ccop_clause_tokens("see Clause 5.1.5 and 8.3; CCoP 2.0 5.7.2(b)")
    assert "5.1.5" in toks and "8.3" in toks and "5.7.2" in toks


def test_extract_rejects_out_of_range_sections():
    # 99.9 / version-like tokens are not plausible CCoP sections (max 11)
    assert extract_ccop_clause_tokens("version 99.9 and 2026.04") == set()


def test_extract_rejects_version_tokens():
    # "CCoP 2.0" must not yield "2.0" (version string, never a clause)
    assert "2.0" not in extract_ccop_clause_tokens("CCoP 2.0 Clause 5.1.2")
    # direct Q-prefixed question number is dropped by the naive extractor
    assert "2.3" not in extract_ccop_clause_tokens("see Q2.3")
    # NOTE: ranges like "Q2.2-2.3" and full doc-attribution are the source-extractor's
    # job (test_source_extraction_skips_rtf_and_act_segments), not the naive extractor.


# --- attribution-aware source extraction (FP guards) -----------------------

def test_source_extraction_skips_rtf_and_act_segments():
    src = "CCoP 2.0 Scope section, RESPONSE-TO-FEEDBACK Q2.2-2.3"
    toks = extract_ccop_citations_from_source(src)
    assert "2.3" not in toks  # the RtF Q-number must not be treated as a CCoP clause
    src2 = "Cybersecurity Act 2018 Section 11, CCoP 2.0 Clause 5.1.2"
    assert extract_ccop_citations_from_source(src2) == {"5.1.2"}  # only the CCoP segment


def test_source_extraction_keeps_ccop_clause():
    assert extract_ccop_citations_from_source("CCoP 2.0 Clause 5.1.5 requires MFA") == {"5.1.5"}


# --- D-CITE-KF -------------------------------------------------------------

def test_cite_kf_flags_nonexistent_clause_in_key_facts():
    rec = {
        "test_id": "B02-001", "benchmark_id": "B02",
        "ground_truth": {"key_facts": [{"source": "CCoP 2.0 Clause 5.1.5 requires MFA"}]},
    }
    defects = detect_cite_kf(rec, CCOP_IDS)
    assert any(d.offending_value == "5.1.5" and d.detector == "D-CITE-KF" for d in defects)


def test_cite_kf_passes_real_clause():
    rec = {
        "test_id": "B05-001", "benchmark_id": "B05",
        "ground_truth": {"key_facts": [{"source": "CCoP 2.0 5.2.2 account review"}]},
    }
    assert detect_cite_kf(rec, CCOP_IDS) == []


def test_cite_kf_checks_support_citations():
    # explicit CCoP attribution => flagged (matches real B24 source 'CCoP 2.0 Section 8.3')
    rec = {
        "test_id": "B24-001", "benchmark_id": "B24",
        "ground_truth": {},
        "metadata": {"support_citations": ["CCoP 2.0 Section 8.3 reporting"]},
    }
    defects = detect_cite_kf(rec, CCOP_IDS)
    assert any(d.offending_value == "8.3" for d in defects)


def test_cite_kf_ignores_unattributed_section_ref():
    # bare "section 8.3" with no doc marker must NOT be assumed CCoP (high precision)
    rec = {
        "test_id": "X", "benchmark_id": "X",
        "ground_truth": {},
        "metadata": {"support_citations": ["section 8.3 reporting"]},
    }
    assert detect_cite_kf(rec, CCOP_IDS) == []


# --- D-FAMILY --------------------------------------------------------------

def test_family_flags_disjoint():
    rec = {
        "test_id": "B01-001", "benchmark_id": "B01",
        "metadata": {"clause_reference": ["1.2.1", "1.4.1"]},
        "ground_truth": {"key_facts": [{"source": "CCoP 2.0 Clause 5.1.2"}]},
    }
    defects = detect_family(rec)
    assert len(defects) == 1 and defects[0].detector == "D-FAMILY"


def test_family_no_flag_when_overlap():
    rec = {
        "test_id": "X", "benchmark_id": "X",
        "metadata": {"clause_reference": ["5.3.1"]},
        "ground_truth": {"key_facts": [{"source": "CCoP 2.0 Clause 5.3.1(c)"}]},
    }
    assert detect_family(rec) == []


# --- D-FORBIDDEN -----------------------------------------------------------

def test_forbidden_flags_required_element():
    assert looks_like_required_element("Reference to applicable CCoP clause")
    assert looks_like_required_element("Missing: Specific remediation actions")
    assert looks_like_required_element("Evidence quality considerations")


def test_forbidden_passes_genuine_prohibition():
    assert not looks_like_required_element("SMS-based MFA does not satisfy CCoP 2.0 MFA requirements")
    assert not looks_like_required_element("Board members are personally liable")
    assert not looks_like_required_element("Stating one regulator completely replaces another")


def test_forbidden_passes_prohibitions_ending_in_requirements():
    # the FP class found in the first real scan: real prohibitions that end in "requirements"
    assert not looks_like_required_element("IM8 compliance fully satisfies CCoP 2.0 requirements")
    assert not looks_like_required_element(
        "Systems outside the digital boundary are never subject to CCoP network requirements"
    )
    assert not looks_like_required_element(
        "ISO 27001 certification satisfies CCoP 2.0 compliance requirements"
    )


def test_forbidden_detector_on_record():
    rec = {
        "test_id": "B07-006", "benchmark_id": "B07",
        "fail_conditions": {"forbidden_claims": [
            "Stating no gap exists when control requirement is not met",  # legit
            "Reference to applicable CCoP clause",                        # contamination
        ]},
    }
    defects = detect_forbidden(rec)
    assert len(defects) == 1
    assert defects[0].offending_value == "Reference to applicable CCoP clause"
    assert defects[0].confidence == "heuristic"


# --- D-LEAK ----------------------------------------------------------------

def test_leak_flags_verbatim_copy():
    q = "What CCoP 2.0 Section 8 actions are required for classification and reporting?"
    rec = {
        "test_id": "B09-001", "benchmark_id": "B09",
        "input": {"question": q},
        "ground_truth": {"expected_response": q + "\n\nIdentified Risks: ..."},
    }
    defects = detect_leak(rec)
    assert len(defects) == 1 and defects[0].detector == "D-LEAK"


def test_leak_no_flag_for_distinct_answer():
    rec = {
        "test_id": "X", "benchmark_id": "X",
        "input": {"question": "Does CCoP mandate MFA?"},
        "ground_truth": {"expected_response": "Yes, privileged access requires multi-factor authentication under the privileged access management section."},
    }
    assert detect_leak(rec) == []


def test_overlap_metric_bounds():
    assert question_answer_overlap("", "x") == 0.0
    assert question_answer_overlap("same text here", "same text here") == 1.0
