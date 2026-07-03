"""
SHACL validation backstop tests (Phase 10, D-13).

Pure, in-memory rdflib tests — NO Neo4j required. They exercise the structural
constraints authored in `src/rag/graph/ontology/shapes.ttl` (the D-07 anti-
pattern fixes) through the `SHACLValidator` pure functions:

  * a node missing its canonical `name` -> conforms=False (D-07 name required),
  * a node with a junk name ("N.A.", "A", empty) -> conforms=False (junk rejected),
  * a fully valid fixture graph -> conforms=True,
  * violations are QUARANTINED into a report (focusNode/resultPath/severity),
    never deleted from the data graph (D-13 reject + log separately).

The LPG->RDF export mapping is exercised as a pure function too (Neo4j record
dicts in, rdflib.Graph out) so no live driver is touched.
"""

from rdflib import Graph, Literal, Namespace, RDF

from rag.graph.ontology.shacl_validator import (
    CCOP,
    SHACLValidator,
    ValidationReport,
    lpg_to_rdf,
)

NS = Namespace("http://ccop.example/kg#")


def _validator() -> SHACLValidator:
    # driver=None: we only exercise the pure validate_rdf / export helpers here.
    return SHACLValidator(driver=None)


def _data_graph_with(node_id: str, label: str, props: dict[str, str]) -> Graph:
    """Build a minimal LPG->RDF data graph for one node."""
    g = Graph()
    uri = NS[node_id]
    g.add((uri, RDF.type, NS[label]))
    for k, v in props.items():
        g.add((uri, NS[k], Literal(v)))
    return g


class TestCanonicalNameConstraint:
    """D-07: extracted entities require a canonical, non-junk `name`."""

    def test_node_missing_name_does_not_conform(self):
        # A CriticalInformationInfrastructure node with NO name property.
        g = _data_graph_with("n1", "CriticalInformationInfrastructure", {})
        report = _validator().validate_rdf(g)

        assert report.conforms is False
        assert len(report.violations) >= 1
        focus_nodes = {v.focus_node for v in report.violations}
        assert str(NS["n1"]) in focus_nodes

    def test_junk_name_na_does_not_conform(self):
        # The canonical Phase 9 junk value.
        g = _data_graph_with(
            "n2", "CriticalInformationInfrastructure", {"name": "N.A."}
        )
        report = _validator().validate_rdf(g)

        assert report.conforms is False
        assert any(str(NS["n2"]) == v.focus_node for v in report.violations)

    def test_single_letter_name_does_not_conform(self):
        g = _data_graph_with("n3", "AccessControl", {"name": "A"})
        report = _validator().validate_rdf(g)

        assert report.conforms is False

    def test_empty_name_does_not_conform(self):
        g = _data_graph_with("n4", "Waiver", {"name": ""})
        report = _validator().validate_rdf(g)

        assert report.conforms is False

    def test_placeholder_person_name_does_not_conform(self):
        g = _data_graph_with("n5", "ThirdParty", {"name": "John Doe"})
        report = _validator().validate_rdf(g)

        assert report.conforms is False

    def test_valid_named_entity_conforms(self):
        g = _data_graph_with(
            "n6",
            "CriticalInformationInfrastructure",
            {"name": "National Power Grid SCADA"},
        )
        report = _validator().validate_rdf(g)

        assert report.conforms is True
        assert report.violations == []


class TestSeededClauseConstraint:
    """D-10: seeded clause-backbone nodes are keyed on clause_id, not name."""

    def test_seeded_clause_with_clause_id_conforms(self):
        # A seeded Clause has clause_id but NO name — must NOT be flagged.
        g = _data_graph_with(
            "c1",
            "Clause",
            {"clause_id": "1.2.1", "source_doc": "CCoP", "chapter": "1"},
        )
        report = _validator().validate_rdf(g)

        assert report.conforms is True

    def test_clause_missing_clause_id_does_not_conform(self):
        g = _data_graph_with("c2", "Clause", {"source_doc": "CCoP"})
        report = _validator().validate_rdf(g)

        assert report.conforms is False

    def test_function_tagged_clause_conforms(self):
        # ScopeClause is a function-type tag on a Clause; keyed on clause_id.
        g = Graph()
        uri = NS["c3"]
        g.add((uri, RDF.type, NS["Clause"]))
        g.add((uri, RDF.type, NS["ScopeClause"]))
        g.add((uri, NS["clause_id"], Literal("1.2.1")))
        report = _validator().validate_rdf(g)

        assert report.conforms is True


class TestQuarantineNotDelete:
    """D-13: violations are quarantined + logged, NEVER silently deleted."""

    def test_violations_collected_with_focus_path_severity(self):
        g = _data_graph_with(
            "n7", "CriticalInformationInfrastructure", {"name": "N.A."}
        )
        report = _validator().validate_rdf(g)

        assert report.conforms is False
        assert len(report.violations) >= 1
        v = report.violations[0]
        # Quarantine record carries the fields curation needs (D-13).
        assert v.focus_node
        assert v.severity  # e.g. sh:Violation
        assert v.message

    def test_data_graph_not_mutated_by_validation(self):
        g = _data_graph_with(
            "n8", "CriticalInformationInfrastructure", {"name": "N.A."}
        )
        triples_before = len(g)
        report = _validator().validate_rdf(g)

        # Reject + log separately: the offending triple is STILL in the graph
        # (quarantined, not deleted).
        assert len(g) == triples_before
        assert (NS["n8"], NS["name"], Literal("N.A.")) in g
        assert report.conforms is False

    def test_quarantine_report_serializable(self):
        g = _data_graph_with("n9", "AccessControl", {"name": "A"})
        report = _validator().validate_rdf(g)

        payload = report.to_dict()
        assert payload["conforms"] is False
        assert isinstance(payload["violations"], list)
        assert payload["violation_count"] == len(report.violations)


class TestLpgToRdfExport:
    """The LPG->RDF export is a pure function (Neo4j records in, Graph out)."""

    def test_export_maps_labels_and_properties(self):
        node_records = [
            {
                "id": "4:abc:1",
                "labels": ["__Entity__", "CriticalInformationInfrastructure"],
                "props": {"name": "ACME Grid"},
            }
        ]
        g = lpg_to_rdf(node_records, [])

        uri = CCOP["4:abc:1"]
        assert (uri, RDF.type, CCOP["CriticalInformationInfrastructure"]) in g
        assert (uri, CCOP["name"], Literal("ACME Grid")) in g

    def test_export_maps_relationships(self):
        node_records = [
            {"id": "a", "labels": ["Clause"], "props": {"clause_id": "1.2.1"}},
            {"id": "b", "labels": ["Control"], "props": {"name": "Access Logging"}},
        ]
        rel_records = [{"source": "a", "target": "b", "rel_type": "GOVERNS"}]
        g = lpg_to_rdf(node_records, rel_records)

        assert (CCOP["a"], CCOP["GOVERNS"], CCOP["b"]) in g

    def test_exported_valid_graph_conforms(self):
        node_records = [
            {
                "id": "n10",
                "labels": ["__Entity__", "OperationalTechnology"],
                "props": {"name": "PLC Controller"},
            },
            {
                "id": "n11",
                "labels": ["Clause"],
                "props": {"clause_id": "5.3.1", "source_doc": "CCoP"},
            },
        ]
        g = lpg_to_rdf(node_records, [])
        report = _validator().validate_rdf(g)

        assert report.conforms is True

    def test_exported_junk_graph_quarantined(self):
        node_records = [
            {
                "id": "n12",
                "labels": ["__Entity__", "OperationalTechnology"],
                "props": {"name": "N.A."},
            }
        ]
        g = lpg_to_rdf(node_records, [])
        report = _validator().validate_rdf(g)

        assert report.conforms is False
        assert any(v.focus_node == str(CCOP["n12"]) for v in report.violations)


class TestStructuralNodesIgnored:
    """neo4j-graphrag scaffolding labels have no shape -> not flagged."""

    def test_chunk_and_document_nodes_not_validated(self):
        node_records = [
            {"id": "ch1", "labels": ["Chunk"], "props": {"text": "some prose"}},
            {"id": "doc1", "labels": ["Document"], "props": {"path": "x.md"}},
        ]
        g = lpg_to_rdf(node_records, [])
        report = _validator().validate_rdf(g)

        # No targetClass matches Chunk/Document -> conforms.
        assert report.conforms is True
