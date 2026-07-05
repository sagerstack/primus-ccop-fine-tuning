"""
Source-layer annotation tests (Phase 11 -- D-06/D-07/D-08, corrected).

`TestClauseSourceAnnotatorUnit` covers the pure helpers (`source_doc_prefix`,
`doc_class_for`, `_citation_token`, `_compute_structural_header_ids`,
`SourceAnnotationStats.conforms`) against synthetic fixtures -- no Neo4j
required, runs under `pytest -m "not integration"`.

`TestClauseSourceAnnotatorIntegration` requires a live local Neo4j (mirrors
`tests/rag/graph/ontology/test_clause_seeding.py`'s precedent). Runs the REAL
`ClauseSourceAnnotator` against the seeded 883-clause backbone -- the
mandatory E2E slice for this task, not a mock. Asserts zero
`:ComplianceUnit` nodes throughout (this plan mints none, D-07 corrected).
"""

import json

import neo4j
import pytest

from infrastructure.config.settings import get_settings
from rag.graph.ontology.clause_seeder import DEFAULT_CLAUSE_INVENTORY_PATH, ClauseSeeder
from rag.graph.ontology.clause_source_annotator import (
    BINDING_SOURCE_DOCS,
    DOC_CLASS_BINDING,
    DOC_CLASS_GUIDANCE,
    ClauseSourceAnnotator,
    SourceAnnotationStats,
    _citation_token,
    doc_class_for,
    source_doc_prefix,
)


class TestSourceDocPrefixAndDocClassUnit:
    def test_known_docs_resolve_to_documented_prefixes(self):
        assert source_doc_prefix("CCoP 2.0") == "CCoP"
        assert source_doc_prefix("Cybersecurity Act 2018") == "Act"

    def test_unknown_source_doc_fails_loud(self):
        with pytest.raises(ValueError):
            source_doc_prefix("Some Undocumented Doc")

    def test_all_seven_corpus_docs_have_a_registered_prefix(self):
        payload = json.loads(DEFAULT_CLAUSE_INVENTORY_PATH.read_text())
        docs = {entry["source_doc"] for entry in payload["entries"]}
        assert len(docs) == 7
        for doc in docs:
            assert source_doc_prefix(doc)  # must not raise

    def test_ccop_and_act_are_binding(self):
        assert doc_class_for("CCoP 2.0") == DOC_CLASS_BINDING
        assert doc_class_for("Cybersecurity Act 2018") == DOC_CLASS_BINDING
        assert BINDING_SOURCE_DOCS == {"CCoP 2.0", "Cybersecurity Act 2018"}

    def test_guides_and_response_to_feedback_are_guidance(self):
        for doc in (
            "CCoP Response to Feedback",
            "Auditing Guidelines",
            "Threat Modelling Guide",
            "Risk Assessment Guide",
            "Security By Design",
        ):
            assert doc_class_for(doc) == DOC_CLASS_GUIDANCE


class TestCitationTokenUnit:
    def test_strips_section_prefix_matching_d08_example(self):
        assert _citation_token("section 7") == "7"

    def test_passthrough_for_dotted_and_part_ids(self):
        assert _citation_token("5.7.2(b)") == "5.7.2(b)"
        assert _citation_token("Part 1") == "Part 1"

    def test_full_citation_id_matches_d08_worked_examples(self):
        assert f"{source_doc_prefix('CCoP 2.0')}-{_citation_token('5.7.2(b)')}" == "CCoP-5.7.2(b)"
        assert f"{source_doc_prefix('Cybersecurity Act 2018')}-{_citation_token('section 7')}" == "Act-7"


class TestStructuralHeaderComputationUnit:
    def test_chapter_and_section_are_structural(self):
        entries = [
            {"clause_id": "5", "source_doc": "CCoP 2.0"},
            {"clause_id": "5.3", "source_doc": "CCoP 2.0"},
            {"clause_id": "5.3.1", "source_doc": "CCoP 2.0"},
        ]
        structural = ClauseSourceAnnotator._compute_structural_header_ids(entries)
        assert ("5", "CCoP 2.0") in structural
        assert ("5.3", "CCoP 2.0") in structural
        assert ("5.3.1", "CCoP 2.0") not in structural

    def test_leaf_clause_with_only_item_letter_children_is_not_structural(self):
        entries = [
            {"clause_id": "5.3.1", "source_doc": "CCoP 2.0"},
            {"clause_id": "5.3.1(a)", "source_doc": "CCoP 2.0"},
            {"clause_id": "5.3.1(b)", "source_doc": "CCoP 2.0"},
        ]
        structural = ClauseSourceAnnotator._compute_structural_header_ids(entries)
        # "5.3.1" has ONLY lettered sub-item children -- it is itself an
        # operative leaf clause (a CU candidate in 11-04), not a
        # chapter/section skeleton node.
        assert ("5.3.1", "CCoP 2.0") not in structural
        assert ("5.3.1(a)", "CCoP 2.0") not in structural

    def test_structural_flag_is_scoped_per_source_doc(self):
        entries = [
            {"clause_id": "1", "source_doc": "CCoP 2.0"},
            {"clause_id": "1.1", "source_doc": "CCoP 2.0"},
            {"clause_id": "1", "source_doc": "Auditing Guidelines"},
        ]
        structural = ClauseSourceAnnotator._compute_structural_header_ids(entries)
        assert ("1", "CCoP 2.0") in structural
        assert ("1", "Auditing Guidelines") not in structural


class TestSourceAnnotationStatsUnit:
    def test_conforms_true_when_zero_cu_and_all_annotated(self):
        stats = SourceAnnotationStats(
            entries_total=10,
            annotated=10,
            compliance_unit_count=0,
            missing_citation_id_count=0,
            invalid_doc_class_count=0,
        )
        assert stats.conforms is True

    def test_conforms_false_when_compliance_unit_exists(self):
        stats = SourceAnnotationStats(
            entries_total=10,
            annotated=10,
            compliance_unit_count=1,
            missing_citation_id_count=0,
            invalid_doc_class_count=0,
        )
        assert stats.conforms is False

    def test_conforms_false_when_citation_id_missing(self):
        stats = SourceAnnotationStats(
            entries_total=10,
            annotated=9,
            compliance_unit_count=0,
            missing_citation_id_count=1,
            invalid_doc_class_count=0,
        )
        assert stats.conforms is False


@pytest.mark.integration
class TestClauseSourceAnnotatorIntegration:
    """Requires a live local Neo4j (docker compose up -d neo4j)."""

    def _driver(self) -> neo4j.Driver:
        settings = get_settings()
        return neo4j.GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def _ensure_backbone_seeded(self, driver: neo4j.Driver) -> None:
        settings = get_settings()
        ClauseSeeder(settings=settings, driver=driver).seed()

    def test_annotate_sets_namespaced_citation_id_and_valid_doc_class(self):
        settings = get_settings()
        driver = self._driver()
        try:
            self._ensure_backbone_seeded(driver)
            annotator = ClauseSourceAnnotator(settings=settings, driver=driver)
            stats = annotator.annotate()

            assert stats.entries_total == 883
            assert stats.annotated == 883
            assert stats.missing_citation_id_count == 0
            assert stats.invalid_doc_class_count == 0
            assert stats.compliance_unit_count == 0
            assert stats.conforms is True

            with driver.session(database=settings.neo4j_database) as session:
                bare_ids = session.run(
                    "MATCH (c:Clause) WHERE NOT c.citation_id CONTAINS '-' "
                    "RETURN count(c) AS c"
                ).single()["c"]
            assert bare_ids == 0
        finally:
            driver.close()

    def test_zero_compliance_unit_nodes_after_annotate(self):
        settings = get_settings()
        driver = self._driver()
        try:
            self._ensure_backbone_seeded(driver)
            annotator = ClauseSourceAnnotator(settings=settings, driver=driver)
            annotator.annotate()

            with driver.session(database=settings.neo4j_database) as session:
                cu_count = session.run(
                    "MATCH (cu:ComplianceUnit) RETURN count(cu) AS c"
                ).single()["c"]
            assert cu_count == 0
        finally:
            driver.close()

    def test_ccop_2_0_clause_is_binding_and_guide_clause_is_guidance(self):
        settings = get_settings()
        driver = self._driver()
        try:
            self._ensure_backbone_seeded(driver)
            annotator = ClauseSourceAnnotator(settings=settings, driver=driver)
            annotator.annotate()

            with driver.session(database=settings.neo4j_database) as session:
                ccop_record = session.run(
                    "MATCH (c:Clause {clause_id: '5.3.1', source_doc: 'CCoP 2.0'}) "
                    "RETURN c.doc_class AS doc_class, c.citation_id AS citation_id, "
                    "c.is_structural_header AS is_structural_header"
                ).single()
                act_record = session.run(
                    "MATCH (c:Clause {source_doc: 'Cybersecurity Act 2018'}) "
                    "RETURN c.doc_class AS doc_class LIMIT 1"
                ).single()

            assert ccop_record["doc_class"] == "binding"
            assert ccop_record["citation_id"] == "CCoP-5.3.1"
            assert ccop_record["is_structural_header"] is False
            assert act_record["doc_class"] == "binding"
        finally:
            driver.close()

    def test_chapter_and_section_headers_flagged_structural(self):
        settings = get_settings()
        driver = self._driver()
        try:
            self._ensure_backbone_seeded(driver)
            annotator = ClauseSourceAnnotator(settings=settings, driver=driver)
            annotator.annotate()

            with driver.session(database=settings.neo4j_database) as session:
                chapter = session.run(
                    "MATCH (c:Clause {clause_id: '5', source_doc: 'CCoP 2.0'}) "
                    "RETURN c.is_structural_header AS flag"
                ).single()
                section = session.run(
                    "MATCH (c:Clause {clause_id: '5.3', source_doc: 'CCoP 2.0'}) "
                    "RETURN c.is_structural_header AS flag"
                ).single()

            assert chapter["flag"] is True
            assert section["flag"] is True
        finally:
            driver.close()

    def test_annotation_is_idempotent(self):
        settings = get_settings()
        driver = self._driver()
        try:
            self._ensure_backbone_seeded(driver)
            annotator = ClauseSourceAnnotator(settings=settings, driver=driver)
            first_stats = annotator.annotate()
            second_stats = annotator.annotate()

            assert first_stats.annotated == second_stats.annotated == 883
            assert second_stats.compliance_unit_count == 0

            with driver.session(database=settings.neo4j_database) as session:
                total_clauses = session.run(
                    "MATCH (c:Clause) RETURN count(c) AS c"
                ).single()["c"]
            assert total_clauses == 883
        finally:
            driver.close()
