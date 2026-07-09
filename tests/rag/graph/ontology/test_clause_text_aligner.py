"""
Step-0 clause-text alignment tests (Phase 11 -- D-13/D-19).

`TestClauseTextAlignerResolutionUnit` covers the pure resolution helpers
(`_resolve_text`, `_heading_starts_with`, `_body_starts_with_number`) against
synthetic chunk fixtures modeled directly on the real re-ingested corpus --
no Neo4j/Qdrant required, runs under `pytest -m "not integration"`.

`TestClauseTextAlignerIntegration` requires the LIVE local Neo4j + Qdrant
services (`docker compose up -d qdrant`; Neo4j per docker-compose) and the
`ccop_clauses_hybrid` collection already populated by the Wave-0 re-ingest --
mirrors `tests/rag/graph/ontology/test_clause_seeding.py`'s live-integration
precedent. This is the mandatory E2E slice for this task (D-15.3 discipline):
it runs the REAL `ClauseTextAligner` against the 883-clause backbone, not a
mock.
"""

import neo4j
import pytest

from infrastructure.config.settings import get_settings
from rag.graph.ontology.clause_seeder import ClauseSeeder
from rag.graph.ontology.clause_text_aligner import (
    AlignStats,
    ClauseTextAligner,
    _body_starts_with_number,
    _heading_starts_with,
    _resolve_act_text,
    _slice_act_sections,
)


class TestActSectionSlicingUnit:
    """
    11-04b fix: the Act's section bodies live on/after their `##` heading line,
    so the old heading-stripping resolver collided them onto a shared TOC blob.
    These verify the section-slicer + Act resolver on synthetic chunks modeled
    on the real corpus (subsectioned, no-subsection, and mid-chunk sections).
    """

    def _chunks(self):
        return [
            {"text": "## Designation of critical information infrastructure   7. -(1)  The Commissioner may designate ..."},
            # a chunk with a preceding section's tail then a mid-chunk section 13
            {"text": "... appointed under section 4.\n\n## Change in ownership of critical information infrastructure  \n13. -(1)  Where there is any change ..."},
            # the shared TOC blob the old resolver wrongly assigned everywhere
            {"text": "## Cybersecurity Act 2018\nTable of Contents\n- 7 Designation\n- 13 Change in ownership\n- 25 Licensing officer"},
        ]

    def test_slices_subsectioned_and_midchunk_sections(self):
        sections = _slice_act_sections(self._chunks())
        assert "7" in sections and sections["7"].startswith("## Designation")
        assert "13" in sections and "Where there is any change" in sections["13"]

    def test_section_never_gets_the_toc_blob(self):
        sections = _slice_act_sections(self._chunks())
        assert "Table of Contents" not in sections.get("7", "")
        assert "Table of Contents" not in sections.get("13", "")

    def test_resolver_returns_none_over_wrong_blob(self):
        sections = _slice_act_sections(self._chunks())
        # an unknown section resolves to None (textless), never a shared blob
        assert _resolve_act_text("section 99", sections, self._chunks()) is None

    def test_resolver_resolves_known_section(self):
        sections = _slice_act_sections(self._chunks())
        assert _resolve_act_text("section 13", sections, self._chunks()).count("Table of Contents") == 0
        assert "change" in _resolve_act_text("section 13", sections, self._chunks()).lower()

    def test_part_heading_resolves_not_toc(self):
        chunks = [{"text": "## PART 4  ## RESPONSES TO CYBERSECURITY THREATS AND INCIDENTS"},
                  {"text": "## Cybersecurity Act 2018\nTable of Contents\n- Part 4 ..."}]
        assert _resolve_act_text("Part 4", {}, chunks) == chunks[0]["text"]


class TestClauseTextAlignerResolutionUnit:
    """Pure resolution-helper tests -- no external services required."""

    # ------------------------------------------------------------------
    # Tier 1: exact `clause` metadata match
    # ------------------------------------------------------------------

    def test_exact_metadata_match_wins_over_substring_scan(self):
        doc_chunks = [
            {"text": "5.3 Privileged Access Management\n\nPrivileged accounts...", "clause": "5.3"},
            {"text": "5.3.1 With respect to privileged accounts, the CIIO shall...", "clause": "5.3.1"},
        ]
        assert ClauseTextAligner._resolve_text("5.3.1", doc_chunks).startswith("5.3.1 With respect")

    def test_exact_metadata_match_prefers_shortest_on_duplicate(self):
        doc_chunks = [
            {"text": "5.3 Section body, longer duplicate text here", "clause": "5.3"},
            {"text": "5.3 short", "clause": "5.3"},
        ]
        assert ClauseTextAligner._resolve_text("5.3", doc_chunks) == "5.3 short"

    # ------------------------------------------------------------------
    # Tier 2: item-letter decomposition
    # ------------------------------------------------------------------

    def test_item_letter_same_chunk_match(self):
        doc_chunks = [
            {"text": "10.2.5 The CIIO shall ensure that (a) items are logged.", "clause": "10.2.5"},
        ]
        result = ClauseTextAligner._resolve_text("10.2.5(a)", doc_chunks)
        assert result is not None and "(a)" in result

    def test_item_letter_falls_back_to_letter_only_chunk_when_no_same_chunk_match(self):
        doc_chunks = [
            {"text": "Some unrelated chunk mentioning 4.2 in passing.", "clause": ""},
            {"text": "## Task A: Determine Likelihood\n(i) historical occurrence data.", "clause": ""},
        ]
        result = ClauseTextAligner._resolve_text("4.2(i)", doc_chunks)
        assert result is not None and "(i)" in result

    def test_item_letter_unresolvable_returns_none(self):
        doc_chunks = [{"text": "Nothing relevant here at all.", "clause": ""}]
        assert ClauseTextAligner._resolve_text("9.9(z)", doc_chunks) is None

    # ------------------------------------------------------------------
    # Tier 3: "section N" convention (Cybersecurity Act 2018)
    # ------------------------------------------------------------------

    def test_section_n_precise_body_start_match(self):
        doc_chunks = [
            {
                "text": (
                    "## Designation of critical information infrastructure  \n"
                    "7. -(1)  The Commissioner may, by written notice..."
                ),
                "clause": "",
            },
            {
                "text": "## Some other clause referencing subsection (7) in passing.",
                "clause": "",
            },
        ]
        result = ClauseTextAligner._resolve_text("section 7", doc_chunks)
        assert result is not None
        assert "Designation of critical information infrastructure" in result

    def test_section_n_falls_back_to_longest_generic_match_when_no_precise_hit(self):
        doc_chunks = [
            {"text": "A short chunk mentioning 7 in an unrelated sentence.", "clause": ""},
            {
                "text": (
                    "## Cybersecurity Act 2018 (No. 9 of 2018)\nTable of Contents\n"
                    "- 7 Designation of critical information infrastructure\n"
                    "extra padding to make this the longest candidate chunk by far"
                ),
                "clause": "",
            },
        ]
        result = ClauseTextAligner._resolve_text("section 7", doc_chunks)
        assert result is not None and "Table of Contents" in result

    # ------------------------------------------------------------------
    # Tier 4: heading-token match (section-based guides)
    # ------------------------------------------------------------------

    def test_heading_token_match_bare_chapter_id(self):
        doc_chunks = [
            {"text": "## 7 COI AUDIT\n\n## 7.1 Background\nFollowing the cyber-attack...", "clause": ""},
        ]
        result = ClauseTextAligner._resolve_text("7", doc_chunks)
        assert result is not None and result.startswith("## 7 COI AUDIT")

    # ------------------------------------------------------------------
    # Tier 5: generic boundary-aware substring fallback ("Part N" ids)
    # ------------------------------------------------------------------

    def test_generic_substring_fallback_for_part_n(self):
        doc_chunks = [
            {
                "text": (
                    "## Cybersecurity Act 2018 (No. 9 of 2018)\n"
                    "## Part 1 PRELIMINARY\n- 1 Short title and commencement"
                ),
                "clause": "",
            },
        ]
        result = ClauseTextAligner._resolve_text("Part 1", doc_chunks)
        assert result is not None and "Part 1 PRELIMINARY" in result

    def test_unresolvable_clause_returns_none(self):
        doc_chunks = [{"text": "Completely unrelated content.", "clause": ""}]
        assert ClauseTextAligner._resolve_text("99.99", doc_chunks) is None

    # ------------------------------------------------------------------
    # Boundary-safety regression: short numeric ids must not spuriously
    # match inside a longer one (reuses KGInspector._clause_id_appears).
    # ------------------------------------------------------------------

    def test_short_clause_id_does_not_spuriously_match_longer_one(self):
        doc_chunks = [{"text": "15.37 Some unrelated clause body.", "clause": "15.37"}]
        # "1" must not match inside "15.37" via the generic substring tier.
        assert ClauseTextAligner._resolve_text("1", doc_chunks) is None


class TestHeadingAndBodyHelpersUnit:
    """Direct unit coverage for the small precision-matching helpers."""

    def test_heading_starts_with_matches_bare_number(self):
        assert _heading_starts_with("## 8 TERMS AND DEFINITIONS\nBody...", "8")

    def test_heading_starts_with_rejects_number_prefix_collision(self):
        # "8" must not match inside "80" (boundary-aware).
        assert not _heading_starts_with("## 80 SOMETHING ELSE\nBody...", "8")

    def test_body_starts_with_number_matches_act_clause_convention(self):
        text = "## Some Heading\n7. -(1) The Commissioner may..."
        assert _body_starts_with_number(text, "7")

    def test_body_starts_with_number_rejects_cross_reference_only(self):
        text = "## Some Heading\nSubject to subsection (7), the licensing officer..."
        assert not _body_starts_with_number(text, "7")


@pytest.mark.integration
class TestClauseTextAlignerIntegration:
    """
    Requires live local Neo4j + Qdrant with the re-ingested corpus already
    indexed into `ccop_clauses_hybrid` (Wave 0). Runs the REAL aligner --
    the mandatory E2E slice for this task, not a mock.
    """

    def _driver(self) -> neo4j.Driver:
        settings = get_settings()
        return neo4j.GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def _ensure_backbone_seeded(self, driver: neo4j.Driver) -> None:
        settings = get_settings()
        seeder = ClauseSeeder(settings=settings, driver=driver)
        seeder.seed()

    def test_backbone_precondition_seeded_before_alignment(self):
        settings = get_settings()
        driver = self._driver()
        try:
            self._ensure_backbone_seeded(driver)
            with driver.session(database=settings.neo4j_database) as session:
                count = session.run("MATCH (c:Clause) RETURN count(c) AS c").single()["c"]
            assert count == 883
        finally:
            driver.close()

    def test_align_produces_zero_textless_clause_nodes(self):
        settings = get_settings()
        driver = self._driver()
        try:
            self._ensure_backbone_seeded(driver)
            aligner = ClauseTextAligner(settings=settings, driver=driver)
            try:
                stats: AlignStats = aligner.align()
            finally:
                aligner.close()

            assert stats.entries_total == 883
            assert stats.textless_nodes == 0
            assert len(stats.unaligned) == 0
        finally:
            driver.close()

    def test_5_3_and_5_4_carry_real_verbatim_bodies(self):
        settings = get_settings()
        driver = self._driver()
        try:
            self._ensure_backbone_seeded(driver)
            aligner = ClauseTextAligner(settings=settings, driver=driver)
            try:
                aligner.align()
            finally:
                aligner.close()

            with driver.session(database=settings.neo4j_database) as session:
                record_5_3 = session.run(
                    "MATCH (c:Clause {clause_id: '5.3', source_doc: 'CCoP 2.0'}) "
                    "RETURN c.text AS text"
                ).single()
                record_5_4 = session.run(
                    "MATCH (c:Clause {clause_id: '5.4', source_doc: 'CCoP 2.0'}) "
                    "RETURN c.text AS text"
                ).single()

            assert record_5_3 is not None and record_5_3["text"]
            assert record_5_4 is not None and record_5_4["text"]
            assert "Privileged Access Management" in record_5_3["text"]
            assert "Domain Controller" in record_5_4["text"]
        finally:
            driver.close()

    def test_alignment_is_idempotent(self):
        settings = get_settings()
        driver = self._driver()
        try:
            self._ensure_backbone_seeded(driver)
            aligner = ClauseTextAligner(settings=settings, driver=driver)
            try:
                first_stats = aligner.align()
                second_stats = aligner.align()
            finally:
                aligner.close()

            assert first_stats.aligned == second_stats.aligned
            assert second_stats.textless_nodes == 0
        finally:
            driver.close()
