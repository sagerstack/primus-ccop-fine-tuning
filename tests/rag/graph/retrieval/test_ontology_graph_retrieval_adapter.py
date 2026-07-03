"""
Unit tests for Neo4jOntologyGraphRetrievalAdapter (Phase 10, plan 10-09).

All tests mock the neo4j-graphrag retriever / driver / embedder — no live
Neo4j connection is made here. The actual Cypher CASE-WHEN boost arithmetic
and ORDER BY execution can only be proven against a live Neo4j instance
(see the `@pytest.mark.integration` class at the bottom, mirroring
test_graph_retrieval_adapter_integration.py's precedent) — these unit tests
instead assert (a) the RETRIEVAL_QUERY static Cypher string contains the
correct boost/tie-break/clause-anchoring shape, (b) `retrieve()` passes
`$function_type`/`$boost` as BOUND query_params (never interpolated), and
(c) the adapter faithfully preserves whatever order/citation_id Neo4j's
result stream returns (i.e. the adapter is a correct passthrough of an
already-boosted-and-ordered Neo4j result — the "mocked retriever records"
the plan's Task 1 behavior spec refers to).
"""

from unittest.mock import MagicMock, call, patch

import pytest
from langchain_core.documents import Document

from rag.graph.retrieval.neo4j_ontology_graph_retrieval_adapter import (
    Neo4jOntologyGraphRetrievalAdapter,
    _escape_lucene_query_text,
)


def _make_settings(**overrides):
    settings = MagicMock()
    settings.neo4j_uri = "bolt://localhost:7687"
    settings.neo4j_user = "neo4j"
    settings.neo4j_password = "test-password"
    settings.neo4j_database = "neo4j"
    settings.graph_vector_index_name = "ccop_chunk_embeddings"
    settings.graph_fulltext_index_name = "ccop_chunk_fulltext"
    settings.graph_embedding_model = "BAAI/bge-large-en-v1.5"
    settings.graph_embedding_dimensions = 1024
    settings.function_type_boost = 1.5
    for key, value in overrides.items():
        setattr(settings, key, value)
    return settings


def _mock_item(citation_id, score, provider="graphrag-ontology"):
    return MagicMock(
        content=f"Clause text for {citation_id}.",
        metadata={
            "citation_id": citation_id,
            "section": citation_id,
            "document_source": "ccop.pdf",
            "similarity_score": score,
            "original_text": f"Clause text for {citation_id}.",
            "provider": provider,
        },
    )


class TestNeo4jOntologyGraphRetrievalAdapterRetrieve:
    """retrieve() maps neo4j-graphrag search results to hybrid-shaped Documents."""

    def test_retrieve_returns_documents_with_required_metadata_keys(self):
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.items = [_mock_item("1.2.1", 1.35)]
        mock_retriever.search.return_value = mock_result
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

        adapter = Neo4jOntologyGraphRetrievalAdapter(
            settings=_make_settings(),
            driver=MagicMock(),
            embedder=mock_embedder,
            retriever=mock_retriever,
        )

        docs = adapter.retrieve("Is X in scope?", top_k=3, function_type="ScopeClause")

        assert len(docs) == 1
        doc = docs[0]
        assert isinstance(doc, Document)
        for key in (
            "citation_id",
            "section",
            "document_source",
            "similarity_score",
            "original_text",
            "provider",
        ):
            assert key in doc.metadata
        assert doc.metadata["provider"] == "graphrag-ontology"

    def test_retrieve_returns_empty_list_when_no_results(self):
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.items = []
        mock_retriever.search.return_value = mock_result
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

        adapter = Neo4jOntologyGraphRetrievalAdapter(
            settings=_make_settings(),
            driver=MagicMock(),
            embedder=mock_embedder,
            retriever=mock_retriever,
        )

        docs = adapter.retrieve("irrelevant query", top_k=5)

        assert docs == []

    def test_retrieve_defaults_function_type_to_empty_string(self):
        """No function_type passed (e.g. classification failed/degraded) -> bound param is ''."""
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.items = []
        mock_retriever.search.return_value = mock_result
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1]

        adapter = Neo4jOntologyGraphRetrievalAdapter(
            settings=_make_settings(),
            driver=MagicMock(),
            embedder=mock_embedder,
            retriever=mock_retriever,
        )

        adapter.retrieve("query with no classified intent", top_k=3)

        _, kwargs = mock_retriever.search.call_args
        assert kwargs["query_params"]["function_type"] == ""


class TestFunctionTypeBoundParameters:
    """
    T-10-09-01: $function_type / $boost MUST be bound Cypher params (never
    string-interpolated) — asserted at the retrieve() call boundary.
    """

    def test_function_type_and_boost_passed_as_bound_query_params(self):
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.items = []
        mock_retriever.search.return_value = mock_result
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.42]

        settings = _make_settings(function_type_boost=2.0)
        adapter = Neo4jOntologyGraphRetrievalAdapter(
            settings=settings,
            driver=MagicMock(),
            embedder=mock_embedder,
            retriever=mock_retriever,
        )

        adapter.retrieve("What must be implemented?", top_k=3, function_type="ControlClause")

        mock_retriever.search.assert_called_once()
        _, kwargs = mock_retriever.search.call_args
        assert kwargs["query_params"] == {"function_type": "ControlClause", "boost": 2.0}
        assert kwargs["top_k"] == 3
        assert kwargs["query_vector"] == [0.42]

    def test_boost_value_sourced_from_settings_function_type_boost(self):
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.items = []
        mock_retriever.search.return_value = mock_result
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1]

        settings = _make_settings(function_type_boost=3.25)
        adapter = Neo4jOntologyGraphRetrievalAdapter(
            settings=settings,
            driver=MagicMock(),
            embedder=mock_embedder,
            retriever=mock_retriever,
        )
        adapter.retrieve("q", top_k=1, function_type="DefinitionClause")

        _, kwargs = mock_retriever.search.call_args
        assert kwargs["query_params"]["boost"] == 3.25


class TestFunctionTypeBoostOrdering:
    """
    Task 1 behavior: 'RETRIEVAL_QUERY boosts a clause whose function_type ==
    $function_type above an equal-base-score clause that doesn't match
    (asserted on mocked retriever records)'.

    The CASE-WHEN arithmetic itself executes in Neo4j (unit-testable only via
    live integration, see TestNeo4jOntologyGraphRetrievalAdapterLiveBoost
    below in the integration test module) — these tests assert the adapter
    faithfully preserves the order Neo4j's `ORDER BY boosted_score DESC,
    resolved_citation_id ASC` produces, i.e. it never re-sorts or drops the
    boost-driven ordering already applied by the query.
    """

    def test_boosted_matching_clause_ranks_above_equal_base_score_non_match(self):
        # Simulates Neo4j's own boosted+ordered output: two clauses share an
        # identical BASE score (1.0), but "1.2.1" is function_type-matched
        # (ScopeClause) so its boosted_score (1.0 * 1.5 = 1.5) ranks first;
        # "5.6" is unmatched so it stays at base score 1.0.
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.items = [
            _mock_item("1.2.1", 1.5),  # boosted: matched ScopeClause
            _mock_item("5.6", 1.0),  # unboosted: unmatched
        ]
        mock_retriever.search.return_value = mock_result
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1]

        adapter = Neo4jOntologyGraphRetrievalAdapter(
            settings=_make_settings(),
            driver=MagicMock(),
            embedder=mock_embedder,
            retriever=mock_retriever,
        )

        docs = adapter.retrieve(
            "Is a connected-but-not-designated system in scope?",
            top_k=5,
            function_type="ScopeClause",
        )

        assert [d.metadata["citation_id"] for d in docs] == ["1.2.1", "5.6"]
        assert docs[0].metadata["similarity_score"] > docs[1].metadata["similarity_score"]

    def test_tie_break_ordering_is_identical_across_repeated_calls(self):
        """D-15: stable secondary sort key -> identical ordering, run to run."""
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        # Two records tied at score 1.0 — Neo4j's `..., resolved_citation_id
        # ASC` tie-break resolves this deterministically to "1.2.1" first.
        mock_result.items = [_mock_item("1.2.1", 1.0), _mock_item("1.4.1", 1.0)]
        mock_retriever.search.return_value = mock_result
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1]

        adapter = Neo4jOntologyGraphRetrievalAdapter(
            settings=_make_settings(),
            driver=MagicMock(),
            embedder=mock_embedder,
            retriever=mock_retriever,
        )

        first_run = [d.metadata["citation_id"] for d in adapter.retrieve("q", top_k=5)]
        second_run = [d.metadata["citation_id"] for d in adapter.retrieve("q", top_k=5)]

        assert first_run == second_run == ["1.2.1", "1.4.1"]


class TestRealClauseIdCitations:
    """citation_id/section carry the REAL seeded clause_id, not elementId(chunk)."""

    def test_citation_id_is_the_real_seeded_clause_id(self):
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.items = [_mock_item("3.7.1", 0.91)]
        mock_retriever.search.return_value = mock_result
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1]

        adapter = Neo4jOntologyGraphRetrievalAdapter(
            settings=_make_settings(),
            driver=MagicMock(),
            embedder=mock_embedder,
            retriever=mock_retriever,
        )

        docs = adapter.retrieve("q", top_k=1)

        assert docs[0].metadata["citation_id"] == "3.7.1"
        assert docs[0].metadata["section"] == "3.7.1"
        # Not a Neo4j internal element id shape (e.g. "4:uuid:123").
        assert not docs[0].metadata["citation_id"].startswith("4:")

    def test_format_record_maps_citation_id_and_section_from_cypher_record(self):
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1]
        adapter = Neo4jOntologyGraphRetrievalAdapter(
            settings=_make_settings(),
            driver=MagicMock(),
            embedder=mock_embedder,
            retriever=mock_retriever,
        )

        raw_record = {
            "original_text": "The CIIO shall implement access controls.",
            "citation_id": "5.3.1",
            "section": "5.3.1",
            "document_source": "ccop.pdf",
            "score": 1.5,
        }
        item = adapter._format_record(raw_record)

        assert item.metadata["citation_id"] == "5.3.1"
        assert item.metadata["section"] == "5.3.1"
        assert item.metadata["similarity_score"] == 1.5
        assert item.metadata["provider"] == "graphrag-ontology"


class TestNeo4jOntologyGraphRetrievalAdapterCypherSafety:
    """T-09-12/T-10-09-01: RETRIEVAL_QUERY is static/parameterized — never
    string-interpolated with user text or the classifier's output."""

    def test_retrieval_query_is_a_plain_static_string(self):
        assert isinstance(Neo4jOntologyGraphRetrievalAdapter.RETRIEVAL_QUERY, str)
        query = Neo4jOntologyGraphRetrievalAdapter.RETRIEVAL_QUERY
        assert "{query" not in query
        assert "{function_type" not in query
        assert "%s" not in query

    def test_retrieval_query_uses_bound_function_type_and_boost_params(self):
        query = Neo4jOntologyGraphRetrievalAdapter.RETRIEVAL_QUERY
        assert "$function_type" in query
        assert "$boost" in query

    def test_retrieval_query_anchors_to_seeded_clause_via_linked_to(self):
        query = Neo4jOntologyGraphRetrievalAdapter.RETRIEVAL_QUERY
        assert "LINKED_TO" in query
        assert "Clause" in query

    def test_retrieval_query_produces_boosted_score(self):
        query = Neo4jOntologyGraphRetrievalAdapter.RETRIEVAL_QUERY
        assert "boosted_score" in query

    def test_retrieval_query_has_deterministic_tie_break_order_by(self):
        # D-15 LOCKED decision: ORDER BY <score> DESC, <stable id> ASC.
        query = Neo4jOntologyGraphRetrievalAdapter.RETRIEVAL_QUERY
        assert "ORDER BY boosted_score DESC" in query
        assert "ASC" in query


class TestLuceneEscaping:
    """
    Fixes the B02-001-class TokenMgrError (deferred-items.md, plan 10-01):
    '/' and "'" in question text must be escaped for the Lucene fulltext
    leg, WITHOUT corrupting the dense-vector embedding input.
    """

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("username/password", r"username\/password"),
            ("what is the user's obligation?", r"what is the user\'s obligation\?"),
            ("plain text no specials", "plain text no specials"),
            ("", ""),
        ],
    )
    def test_escape_lucene_query_text(self, raw, expected):
        assert _escape_lucene_query_text(raw) == expected

    def test_retrieve_sends_escaped_text_to_lucene_leg_but_unescaped_to_embedder(self):
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.items = []
        mock_retriever.search.return_value = mock_result
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1, 0.2]

        adapter = Neo4jOntologyGraphRetrievalAdapter(
            settings=_make_settings(),
            driver=MagicMock(),
            embedder=mock_embedder,
            retriever=mock_retriever,
        )

        question = "What about username/password plus the user's SMS OTP?"
        adapter.retrieve(question, top_k=3)

        # Dense leg: embedder receives the ORIGINAL, un-escaped query text.
        mock_embedder.embed_query.assert_called_once_with(question)

        # Sparse/Lucene leg: retriever receives the ESCAPED query_text.
        _, kwargs = mock_retriever.search.call_args
        assert kwargs["query_text"] == _escape_lucene_query_text(question)
        assert "/" not in kwargs["query_text"] or r"\/" in kwargs["query_text"]


class TestNeo4jOntologyGraphRetrievalAdapterConstruction:
    """Construction wires bge embeddings + the configured dense + sparse indexes."""

    @patch("rag.graph.retrieval.neo4j_ontology_graph_retrieval_adapter.HybridCypherRetriever")
    @patch(
        "rag.graph.retrieval.neo4j_ontology_graph_retrieval_adapter.SentenceTransformerEmbeddings"
    )
    def test_uses_configured_embedding_model_and_hybrid_indexes(
        self, mock_embedder_cls, mock_retriever_cls
    ):
        settings = _make_settings()

        Neo4jOntologyGraphRetrievalAdapter(settings=settings, driver=MagicMock())

        mock_embedder_cls.assert_called_once_with(model=settings.graph_embedding_model)
        _, kwargs = mock_retriever_cls.call_args
        assert kwargs["vector_index_name"] == settings.graph_vector_index_name
        assert kwargs["fulltext_index_name"] == settings.graph_fulltext_index_name
        assert kwargs["neo4j_database"] == settings.neo4j_database
        assert kwargs["retrieval_query"] == Neo4jOntologyGraphRetrievalAdapter.RETRIEVAL_QUERY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
