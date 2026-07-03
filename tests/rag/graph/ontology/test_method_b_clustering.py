"""
Tests for Method B clustering cross-check (plan 10-04, Task 2, D-05).

Method B is an INDEPENDENT coverage cross-check against the approved Method-C
draft (`ontology_draft.json`): extract corpus terms -> embed -> cluster
(AffinityPropagation) -> LLM-name each cluster -> compute the B-only clusters
(named types absent from Method C) that the human curation gate (b) decides
keep/drop on.

All tests inject fakes for the two LLM seams (term extraction + cluster
naming) and the embedder, so the suite is deterministic and offline.
"""

from __future__ import annotations

import inspect

from rag.graph.ontology.discovery import method_b_clustering as mb
from rag.graph.ontology.discovery.method_b_clustering import (
    NamedCluster,
    build_reconcile_report,
    cluster_terms,
    embed_terms,
    group_terms_by_cluster,
    run_method_b,
)


class FakeEmbedder:
    """Stand-in for SentenceTransformerEmbeddings — deterministic 2-D vectors.

    Exposes `embed_query` exactly like neo4j_graphrag's embedder so the
    production code path (reusing the SAME embedding model as chunk
    embeddings, per D-05/D-07) is exercised unchanged.
    """

    def __init__(self, vectors: dict[str, list[float]]):
        self._vectors = vectors

    def embed_query(self, text: str) -> list[float]:
        return self._vectors[text]


# A Method-C draft slice: CriticalInformationInfrastructure is covered (with
# CII as an example term); PenetrationTesting is deliberately absent so a
# B cluster naming it must surface as B-only.
FIXTURE_METHOD_C = {
    "node_types": [
        {
            "label": "CriticalInformationInfrastructure",
            "description": "Designated critical systems.",
            "example_terms": ["CII", "Critical Infrastructure"],
            "flagged_ambiguities": ["CII Asset", "motivated by B01, B02"],
        },
        {
            "label": "RiskAssessment",
            "description": "Risk identification and evaluation.",
            "example_terms": ["Risk Assessment"],
            "flagged_ambiguities": [],
        },
    ],
    "relationship_types": ["GOVERNS", "REQUIRES"],
}

# Two tight, well-separated groups: the CII synonyms cluster together and the
# penetration-testing synonyms cluster together.
FIXTURE_VECTORS = {
    "CII": [0.0, 0.0],
    "Critical Infrastructure": [0.0, 0.0],
    "Penetration Testing": [10.0, 10.0],
    "Pen Test": [10.0, 10.0],
}


class TestClustering:
    def test_clustering_groups_synonymous_terms(self):
        terms = ["CII", "Critical Infrastructure", "Penetration Testing", "Pen Test"]
        embeddings = embed_terms(terms, FakeEmbedder(FIXTURE_VECTORS))
        labels = cluster_terms(embeddings)
        clusters = group_terms_by_cluster(terms, labels)

        assert len(clusters) == 2
        member_sets = sorted((sorted(c) for c in clusters), key=lambda c: c[0])
        assert ["CII", "Critical Infrastructure"] in [sorted(c) for c in clusters]
        assert ["Pen Test", "Penetration Testing"] in [sorted(c) for c in clusters]

    def test_empty_and_singleton_are_safe(self):
        assert cluster_terms([]) == []
        assert list(cluster_terms([[1.0, 2.0]])) == [0]


class TestReconcileReport:
    def test_b_only_excludes_clusters_covered_by_method_c(self):
        named = [
            NamedCluster(name="CriticalInformationInfrastructure", members=["CII", "Critical Infrastructure"]),
            NamedCluster(name="PenetrationTesting", members=["Penetration Testing", "Pen Test"]),
        ]
        report = build_reconcile_report(named, FIXTURE_METHOD_C)

        b_only_names = {c["name"] for c in report["b_only"]}
        overlap_names = {c["name"] for c in report["overlap"]}

        # The CII cluster overlaps C (via label AND example term) -> NOT b-only.
        assert "CriticalInformationInfrastructure" not in b_only_names
        assert "CriticalInformationInfrastructure" in overlap_names
        # The penetration-testing cluster is absent from C -> IS b-only.
        assert "PenetrationTesting" in b_only_names
        assert "PenetrationTesting" not in overlap_names

    def test_overlap_match_can_be_via_member_term_only(self):
        # Cluster named differently from any C label, but a member term ("CII")
        # matches a C example term -> still counts as overlap, not b-only.
        named = [NamedCluster(name="InfraSystems", members=["CII", "backbone"])]
        report = build_reconcile_report(named, FIXTURE_METHOD_C)
        assert report["b_only"] == []
        assert report["overlap"][0]["matched_c_type"] == "CriticalInformationInfrastructure"

    def test_report_surfaces_c_types_not_corroborated_by_b(self):
        # Only the CII cluster is present; RiskAssessment (a C type) is not
        # independently corroborated by any B cluster -> flagged for gate (b).
        named = [NamedCluster(name="CriticalInformationInfrastructure", members=["CII"])]
        report = build_reconcile_report(named, FIXTURE_METHOD_C)
        assert "RiskAssessment" in report["c_not_corroborated"]
        assert "CriticalInformationInfrastructure" not in report["c_not_corroborated"]

    def test_report_shape(self):
        named = [NamedCluster(name="PenetrationTesting", members=["Pen Test"])]
        report = build_reconcile_report(named, FIXTURE_METHOD_C)
        assert set(report) >= {"c_types", "b_types", "b_only", "overlap", "c_not_corroborated"}
        assert "CriticalInformationInfrastructure" in report["c_types"]
        assert report["b_types"] == ["PenetrationTesting"]


class TestRunMethodB:
    def test_run_uses_injected_llm_seams_and_returns_membership(self):
        corpus = {"doc": "Some regulatory prose about critical infrastructure and testing."}

        def term_extractor(passage: str) -> list[str]:
            return ["CII", "Critical Infrastructure", "Penetration Testing", "Pen Test"]

        def cluster_namer(members: list[str]) -> str:
            return "CriticalInformationInfrastructure" if "CII" in members else "PenetrationTesting"

        report = run_method_b(
            corpus,
            FIXTURE_METHOD_C,
            FakeEmbedder(FIXTURE_VECTORS),
            term_extractor=term_extractor,
            cluster_namer=cluster_namer,
        )

        assert "PenetrationTesting" in {c["name"] for c in report["b_only"]}
        # membership is carried through so the human gate can inspect terms
        pen = next(c for c in report["b_only"] if c["name"] == "PenetrationTesting")
        assert set(pen["members"]) == {"Penetration Testing", "Pen Test"}


class TestD02Compliance:
    def test_term_extraction_reads_corpus_prose_not_emergent_graph(self):
        """D-02: Method B discovers fresh from corpus prose, never from the
        Phase 9 emergent knowledge graph."""
        src = inspect.getsource(mb)
        # No reads of the emergent graph / Neo4j.
        assert "KGInspector" not in src
        assert "MATCH (" not in src
        assert "neo4j" not in src.lower()
        # Term source is the Docling corpus loader (same text the KG builders use).
        assert "load_ccop_corpus_texts" in src
