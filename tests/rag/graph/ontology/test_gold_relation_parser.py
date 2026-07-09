"""
Tests for the D-17 gold-relation parser (plan 10-03, Task 1).

RED-phase fixture cell mirrors the actual live content of B01-001's
`graph_relation` cell (confirmed via direct xlsx read during RESEARCH.md
Q10 and re-confirmed live in this session) — including the
`NOT DESIGNATED_AS` (space, not underscore) normalization pitfall.
"""

from pathlib import Path

import pytest

from rag.graph.ontology.gold_relation_parser import (
    CLAUSE_BRACKET_RE,
    TRIPLE_RE,
    normalize_relation,
    parse_gold_relations,
    parse_graph_relation_cell,
)

FIXTURE_CELL = (
    "(hospital_admin_system) -[SHARES_NETWORK_WITH]-> (CII); "
    "(hospital_admin_system) -[NOT DESIGNATED_AS]-> (CII); "
    "(Commissioner) -[DESIGNATES]-> (CII) [Cybersecurity_Act_2018 s7]; "
    "(CCoP_2.0) -[APPLIES_TO]-> (designated_CII + cyber_operating_environment) "
    "[1.2.1, 1.4.1]; "
    "(digital_boundary) -[DETERMINED_BY]-> (CSA + CIIO + Sector_Lead) [RTF 2.2]"
)

REAL_XLSX_PATH = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "results"
    / "evaluations"
    / "eval-report-hybrid-suite-20260630-0907.xlsx"
)


class TestNormalizeRelation:
    def test_normalizes_space_separated_relation_to_underscore(self):
        assert normalize_relation("NOT DESIGNATED_AS") == "NOT_DESIGNATED_AS"

    def test_leaves_already_normalized_relation_unchanged(self):
        assert normalize_relation("SHARES_NETWORK_WITH") == "SHARES_NETWORK_WITH"

    def test_strips_surrounding_whitespace(self):
        assert normalize_relation("  DESIGNATES  ") == "DESIGNATES"


class TestParseGraphRelationCell:
    def test_extracts_all_triples_from_fixture_cell(self):
        triples, _, _, _ = parse_graph_relation_cell(FIXTURE_CELL)
        assert len(triples) == 5
        assert ("hospital_admin_system", "SHARES_NETWORK_WITH", "CII") in triples

    def test_normalizes_not_designated_as_triple(self):
        """The parser MUST normalize 'NOT DESIGNATED_AS' -> 'NOT_DESIGNATED_AS'."""
        triples, relation_types, _, _ = parse_graph_relation_cell(FIXTURE_CELL)
        normalized_relations = {rel for _, rel, _ in triples}
        assert "NOT_DESIGNATED_AS" in normalized_relations
        assert "NOT DESIGNATED_AS" not in normalized_relations
        assert "NOT_DESIGNATED_AS" in relation_types

    def test_extracts_bracketed_clause_citations(self):
        _, _, _, clause_citations = parse_graph_relation_cell(FIXTURE_CELL)
        assert "1.2.1" in clause_citations
        assert "1.4.1" in clause_citations

    def test_extracts_item_letter_clause_citation(self):
        _, _, _, clause_citations = parse_graph_relation_cell(
            "(x) -[APPLIES_TO]-> (y) [5.3.1(c)]"
        )
        assert clause_citations == ["5.3.1(c)"]

    def test_relation_name_brackets_are_not_treated_as_citations(self):
        """
        CLAUSE_BRACKET_RE's character class also matches bare relation-name
        brackets like "[SHARES_NETWORK_WITH]" (no digits). These must be
        filtered out — only digit-bearing bracket groups are real citations.
        """
        _, _, _, clause_citations = parse_graph_relation_cell(FIXTURE_CELL)
        assert "SHARES_NETWORK_WITH" not in clause_citations
        assert "NOT_DESIGNATED_AS" not in clause_citations
        assert "NOT DESIGNATED_AS" not in clause_citations

    def test_extracts_entity_terms(self):
        _, _, entity_terms, _ = parse_graph_relation_cell(FIXTURE_CELL)
        assert "hospital_admin_system" in entity_terms
        assert "CII" in entity_terms

    def test_empty_cell_returns_empty_results(self):
        triples, relation_types, entity_terms, clause_citations = parse_graph_relation_cell("")
        assert triples == []
        assert relation_types == set()
        assert entity_terms == set()
        assert clause_citations == []


class TestRegexSymbols:
    """Assert the module-level regex constants exist and match the documented shape."""

    def test_triple_re_matches_basic_shape(self):
        assert TRIPLE_RE.search("(a) -[REL]-> (b)")

    def test_clause_bracket_re_matches_multi_citation(self):
        assert CLAUSE_BRACKET_RE.search("[1.2.1, 1.4.1]")


@pytest.mark.skipif(not REAL_XLSX_PATH.exists(), reason="Gold-relation xlsx not present in this checkout")
class TestParseGoldRelationsRealFile:
    """
    Smallest real E2E slice (~e2e-testing.md): exercises the actual xlsx
    file-reading path (sheet lookup, column indexing, row iteration) against
    the real committed gold-standard workbook — not a mock. Mocked unit
    tests above cover `parse_graph_relation_cell`'s regex logic in isolation;
    this proves the openpyxl wiring around it actually works.
    """

    def test_parses_b01_001_from_real_workbook(self):
        cases = parse_gold_relations(REAL_XLSX_PATH, sheet_name="eval-18")
        assert len(cases) > 0

        by_id = {c.test_id: c for c in cases}
        assert "B01-001" in by_id

        b01 = by_id["B01-001"]
        assert "SHARES_NETWORK_WITH" in b01.relation_types
        assert "NOT_DESIGNATED_AS" in b01.relation_types
        assert "1.2.1" in b01.clause_citations
        assert "1.4.1" in b01.clause_citations
