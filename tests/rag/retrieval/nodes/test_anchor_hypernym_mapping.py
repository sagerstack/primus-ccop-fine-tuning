"""
Unit tests for the anchor extraction + hypernym mapping node (Phase 11, plan
11-06 Task 3 + 11-06b addendum, D-09/D-10).

11-06b closes the §3.2 fidelity gap the D-26 checkpoint surfaced: the paper's
hypernym mapping is THREE steps (retrieve -> `ctx.hypernym` LLM elicitation ->
aggregate), and 11-06 Task 3 collapsed the middle step (raw fragment text
used directly as the hypernym label, cosine similarity used directly as the
confidence). These tests mock the LLM elicitation call the same way
`test_context_graph_extraction.py` mocks Context Graph extraction (patch
`openai.OpenAI`), and inject a fake `fragment_retriever` for step 1 (this
node's OTHER external dependency is Neo4j-backed fragment retrieval).

Covers:
- Gating: only derives anchors/mappings for mode=="graph-compliance"; neither
  the fragment retriever nor the LLM elicitation is ever invoked otherwise.
- Anchor derivation from Context Graph triples (actor/data/system only),
  now carrying triple `context` (11-06b).
- Triple-context-enriched retrieval query text (11-06b step-1 fix).
- `elicit_hypernyms` (the pure ctx.hypernym elicitation function): proposal
  parsing, degrade-to-empty on missing api key / LLM error / malformed JSON,
  and per-(entity, context, fragment-set) caching.
- The full node wiring: LLM-proposed (label, confidence, is_premise) feeds
  `score_candidates`, NOT raw fragments/cosine — a premise-supported proposal
  is STRONG with the beta bonus, a non-premise proposal is WEAK, labels are
  the normalized LLM terms (not raw fragment text), top-N=5 still enforced.
- Graceful degradation: a raising fragment_retriever or LLM call never
  crashes the node.
"""

from unittest.mock import MagicMock, patch

import pytest

from rag.retrieval.nodes.anchor_hypernym_mapping import (
    _hypernym_cache,
    elicit_hypernyms,
    map_anchors_to_hypernyms,
)


@pytest.fixture(autouse=True)
def _clear_hypernym_cache():
    _hypernym_cache.clear()
    yield
    _hypernym_cache.clear()


def _settings(**overrides):
    settings = MagicMock()
    settings.hypernym_top_m = 10
    settings.openrouter_api_key = "test-key"
    settings.openrouter_base_url = "https://openrouter.ai/api/v1"
    settings.ontology_discovery_model = "openai/gpt-4o-mini"
    for key, value in overrides.items():
        setattr(settings, key, value)
    return settings


def _mock_openai_response(content: str):
    resp = MagicMock()
    resp.choices = [MagicMock(message=MagicMock(content=content))]
    return resp


B01_001_TRIPLES = [
    {
        "subject": "Hospital administration system",
        "subject_type": "system",
        "predicate": "shares network with",
        "object": "enterprise network",
        "object_type": "system",
    },
    {
        "subject": "Patient monitoring systems",
        "subject_type": "system",
        "predicate": "designated as",
        "object": "CII",
        "object_type": "system",
    },
]

# The candidate pool a "designated as CII"-context-enriched retrieval would
# surface: a CII-*definition* premise plus a non-premise meta-CU designation
# rule (mirrors the worked example in 11-CONTEXT.md).
_CII_DEFINITION_FRAGMENT = {
    "cu_id": "premise-cii-def-1",
    "cu_type": "premise",
    "citation_id": "CCoP-1.2.1",
    "text": (
        "CII means a computer system that is necessary for the continuous "
        "delivery of an essential service, the loss or compromise of which "
        "will lead to a debilitating impact on national security."
    ),
    "is_premise": True,
    "score": 0.82,
}

_CII_DESIGNATION_FRAGMENT = {
    "cu_id": "metacu-act-7",
    "cu_type": "meta-CU",
    "citation_id": "Act-7",
    "text": "The Commissioner may designate a computer system as CII.",
    "subject": "computer system designated by the Commissioner",
    "is_premise": False,
    "score": 0.71,
}


def _default_fragment_pool(anchor_label, top_m, settings):
    return [_CII_DEFINITION_FRAGMENT, _CII_DESIGNATION_FRAGMENT]


class TestGating:
    """Node only derives anchors/mappings (and only calls the retriever/LLM) for graph-compliance mode."""

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_non_graph_compliance_mode_is_a_no_op(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_retriever = MagicMock()

        with patch("openai.OpenAI") as mock_openai_cls:
            state = map_anchors_to_hypernyms(
                {"context_graph_triples": B01_001_TRIPLES, "mode": "hybrid"},
                fragment_retriever=mock_retriever,
            )

        mock_retriever.assert_not_called()
        mock_openai_cls.assert_not_called()
        assert state["anchors"] == []
        assert state["hypernym_mappings"] == []

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_missing_mode_key_defaults_to_no_op(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_retriever = MagicMock()

        with patch("openai.OpenAI") as mock_openai_cls:
            state = map_anchors_to_hypernyms(
                {"context_graph_triples": B01_001_TRIPLES},
                fragment_retriever=mock_retriever,
            )

        mock_retriever.assert_not_called()
        mock_openai_cls.assert_not_called()
        assert state["anchors"] == []
        assert state["hypernym_mappings"] == []


class TestAnchorDerivation:
    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_derives_unique_actor_data_system_anchors(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        state = map_anchors_to_hypernyms(
            {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
            fragment_retriever=lambda label, top_m, settings: [],
        )

        labels = {a["label"] for a in state["anchors"]}
        assert "Hospital administration system" in labels
        assert "enterprise network" in labels
        assert "Patient monitoring systems" in labels
        assert "CII" in labels
        assert all(a["type"] == "system" for a in state["anchors"])

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_anchors_carry_triple_context(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        state = map_anchors_to_hypernyms(
            {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
            fragment_retriever=lambda label, top_m, settings: [],
        )

        by_label = {a["label"]: a for a in state["anchors"]}
        assert ("designated as", "CII") in by_label["Patient monitoring systems"]["context"]
        assert ("designated as", "Patient monitoring systems") in by_label["CII"]["context"]

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_other_type_triples_never_become_anchors(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        triples = [
            {
                "subject": "some concept",
                "subject_type": "other",
                "predicate": "relates to",
                "object": "another concept",
                "object_type": "other",
            }
        ]

        state = map_anchors_to_hypernyms(
            {"context_graph_triples": triples, "mode": "graph-compliance"},
            fragment_retriever=lambda label, top_m, settings: [],
        )

        assert state["anchors"] == []

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_empty_triples_produce_no_anchors(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        state = map_anchors_to_hypernyms(
            {"context_graph_triples": [], "mode": "graph-compliance"},
            fragment_retriever=lambda label, top_m, settings: [],
        )

        assert state["anchors"] == []
        assert state["hypernym_mappings"] == []


class TestQueryEnrichment:
    """Step-1 fix (11-06b): retrieval query text is label + rendered triple context."""

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_retrieval_query_includes_triple_context(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        seen_queries = []

        def _capturing_retriever(query_text, top_m, settings):
            seen_queries.append(query_text)
            return []

        map_anchors_to_hypernyms(
            {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
            fragment_retriever=_capturing_retriever,
        )

        patient_monitoring_query = next(
            q for q in seen_queries if q.startswith("Patient monitoring systems")
        )
        assert "designated as" in patient_monitoring_query
        assert "CII" in patient_monitoring_query
        assert patient_monitoring_query != "Patient monitoring systems"

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_anchor_with_no_context_falls_back_to_bare_label(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        seen_queries = []

        def _capturing_retriever(query_text, top_m, settings):
            seen_queries.append(query_text)
            return []

        triples = [
            {
                "subject": "Standalone system",
                "subject_type": "system",
                "predicate": "",
                "object": "",
                "object_type": "other",
            }
        ]

        map_anchors_to_hypernyms(
            {"context_graph_triples": triples, "mode": "graph-compliance"},
            fragment_retriever=_capturing_retriever,
        )

        assert seen_queries == ["Standalone system"]


class TestElicitHypernyms:
    """The pure `ctx.hypernym` elicitation function (11-06b step 2, Alg. 2 line 3)."""

    def test_no_fragments_never_calls_the_llm(self):
        settings = _settings()

        with patch("openai.OpenAI") as mock_openai_cls:
            proposals = elicit_hypernyms("Patient monitoring systems", "designated as CII", [], settings)

        mock_openai_cls.assert_not_called()
        assert proposals == []

    def test_missing_api_key_degrades_to_empty(self):
        settings = _settings(openrouter_api_key=None)

        with patch("openai.OpenAI") as mock_openai_cls:
            proposals = elicit_hypernyms(
                "Patient monitoring systems",
                "designated as CII",
                [_CII_DEFINITION_FRAGMENT],
                settings,
            )

        mock_openai_cls.assert_not_called()
        assert proposals == []

    def test_llm_error_degrades_to_empty(self):
        settings = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("OpenRouter timeout")

        with patch("openai.OpenAI", return_value=mock_client):
            proposals = elicit_hypernyms(
                "Patient monitoring systems",
                "designated as CII",
                [_CII_DEFINITION_FRAGMENT],
                settings,
            )

        assert proposals == []

    def test_malformed_json_degrades_to_empty(self):
        settings = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response("not json {{")

        with patch("openai.OpenAI", return_value=mock_client):
            proposals = elicit_hypernyms(
                "Patient monitoring systems",
                "designated as CII",
                [_CII_DEFINITION_FRAGMENT],
                settings,
            )

        assert proposals == []

    def test_parses_valid_proposal_shape(self):
        settings = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '[{"hypernym": "critical information infrastructure", "confidence": 0.92, '
            '"supporting_frag_id": "CCoP-1.2.1"}]'
        )

        with patch("openai.OpenAI", return_value=mock_client):
            proposals = elicit_hypernyms(
                "Patient monitoring systems",
                "designated as CII",
                [_CII_DEFINITION_FRAGMENT],
                settings,
            )

        assert proposals == [
            {
                "hypernym": "critical information infrastructure",
                "confidence": 0.92,
                "supporting_frag_id": "CCoP-1.2.1",
            }
        ]

    def test_confidence_clamped_to_unit_interval(self):
        settings = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '[{"hypernym": "x", "confidence": 3.0, "supporting_frag_id": ""}, '
            '{"hypernym": "y", "confidence": -1.0, "supporting_frag_id": ""}]'
        )

        with patch("openai.OpenAI", return_value=mock_client):
            proposals = elicit_hypernyms("entity", "", [_CII_DEFINITION_FRAGMENT], settings)

        confidences = {p["hypernym"]: p["confidence"] for p in proposals}
        assert confidences["x"] == 1.0
        assert confidences["y"] == 0.0

    def test_repeated_identical_call_hits_cache(self):
        settings = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '[{"hypernym": "critical information infrastructure", "confidence": 0.9, '
            '"supporting_frag_id": "CCoP-1.2.1"}]'
        )

        with patch("openai.OpenAI", return_value=mock_client) as mock_openai_cls:
            elicit_hypernyms(
                "Patient monitoring systems", "designated as CII", [_CII_DEFINITION_FRAGMENT], settings
            )
            elicit_hypernyms(
                "Patient monitoring systems", "designated as CII", [_CII_DEFINITION_FRAGMENT], settings
            )

        mock_openai_cls.assert_called_once()

    def test_different_entities_each_call_the_llm(self):
        settings = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '[{"hypernym": "critical information infrastructure", "confidence": 0.9, '
            '"supporting_frag_id": "CCoP-1.2.1"}]'
        )

        with patch("openai.OpenAI", return_value=mock_client) as mock_openai_cls:
            elicit_hypernyms("Entity A", "ctx", [_CII_DEFINITION_FRAGMENT], settings)
            elicit_hypernyms("Entity B", "ctx", [_CII_DEFINITION_FRAGMENT], settings)

        assert mock_openai_cls.call_count == 2


class TestB01001HypernymMapping:
    """
    The corrected worked example (11-06b, per the D-26 checkpoint + the
    B01-001 ground truth): the "Patient monitoring systems" anchor (a
    "designated as CII" system) should resolve STRONG via the CII
    *definition* premise (D-09), with a NORMALIZED hypernym label — not the
    hospital-admin-system anchor (11-06 Task 3's original, now-corrected,
    worked example tied the STRONG CII mapping to the wrong anchor).
    """

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_premise_supported_proposal_is_strong_with_normalized_label(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '[{"hypernym": "critical information infrastructure", "confidence": 0.9, '
            '"supporting_frag_id": "CCoP-1.2.1"}]'
        )

        with patch("openai.OpenAI", return_value=mock_client):
            state = map_anchors_to_hypernyms(
                {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
                fragment_retriever=_default_fragment_pool,
            )

        patient_monitoring_mappings = [
            m for m in state["hypernym_mappings"] if m["anchor"] == "Patient monitoring systems"
        ]
        assert len(patient_monitoring_mappings) == 1
        mapping = patient_monitoring_mappings[0]

        # Normalized LLM label, NOT raw fragment/enumeration text.
        assert mapping["label"] == "critical information infrastructure"
        assert mapping["strong_weak"] == "STRONG"
        assert "CII means" in mapping["supporting_premise"]
        # STRONG score = LLM confidence (0.9) + beta (0.3) = 1.2, NOT cosine (0.82).
        assert mapping["score"] == pytest.approx(1.2)

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_non_premise_supported_proposal_is_weak(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '[{"hypernym": "designated computer system", "confidence": 0.6, '
            '"supporting_frag_id": "Act-7"}]'
        )

        with patch("openai.OpenAI", return_value=mock_client):
            state = map_anchors_to_hypernyms(
                {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
                fragment_retriever=_default_fragment_pool,
            )

        mappings = [m for m in state["hypernym_mappings"] if m["anchor"] == "Patient monitoring systems"]
        assert len(mappings) == 1
        mapping = mappings[0]
        assert mapping["label"] == "designated computer system"
        assert mapping["strong_weak"] == "WEAK"
        # WEAK score = LLM confidence alone (0.6), no beta bonus.
        assert mapping["score"] == pytest.approx(0.6)

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_top_n_5_still_enforced_by_scorer(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        proposals_json = (
            "["
            + ", ".join(
                f'{{"hypernym": "label-{i}", "confidence": 0.{i}, "supporting_frag_id": ""}}'
                for i in range(1, 7)
            )
            + "]"
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(proposals_json)

        with patch("openai.OpenAI", return_value=mock_client):
            state = map_anchors_to_hypernyms(
                {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
                fragment_retriever=_default_fragment_pool,
            )

        mappings = [m for m in state["hypernym_mappings"] if m["anchor"] == "Patient monitoring systems"]
        assert len(mappings) <= 5

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_mapping_entries_carry_the_d17_2_trace_shape(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            '[{"hypernym": "critical information infrastructure", "confidence": 0.9, '
            '"supporting_frag_id": "CCoP-1.2.1"}]'
        )

        with patch("openai.OpenAI", return_value=mock_client):
            state = map_anchors_to_hypernyms(
                {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
                fragment_retriever=_default_fragment_pool,
            )

        assert len(state["hypernym_mappings"]) > 0
        for mapping in state["hypernym_mappings"]:
            assert set(mapping.keys()) >= {"anchor", "label", "strong_weak", "supporting_premise", "score"}
            assert mapping["strong_weak"] in ("STRONG", "WEAK")


class TestGracefulDegradation:
    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_raising_fragment_retriever_never_crashes_the_node(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        def _raising_retriever(query_text, top_m, settings):
            raise RuntimeError("Neo4j unreachable")

        with patch("openai.OpenAI") as mock_openai_cls:
            state = map_anchors_to_hypernyms(
                {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
                fragment_retriever=_raising_retriever,
            )

        # No fragments retrieved -> elicit_hypernyms is never invoked (no
        # grounding to elicit from) -> no mappings, never raises.
        mock_openai_cls.assert_not_called()
        assert state["hypernym_mappings"] == []
        assert "error" not in state

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_llm_failure_degrades_that_anchor_to_no_mappings(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("OpenRouter timeout")

        with patch("openai.OpenAI", return_value=mock_client):
            state = map_anchors_to_hypernyms(
                {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
                fragment_retriever=_default_fragment_pool,
            )

        assert state["hypernym_mappings"] == []
        assert "error" not in state

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_missing_api_key_degrades_that_anchor_to_no_mappings(self, mock_get_settings):
        mock_get_settings.return_value = _settings(openrouter_api_key=None)

        with patch("openai.OpenAI") as mock_openai_cls:
            state = map_anchors_to_hypernyms(
                {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
                fragment_retriever=_default_fragment_pool,
            )

        mock_openai_cls.assert_not_called()
        assert state["hypernym_mappings"] == []
        assert "error" not in state


class TestStateShape:
    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_original_state_keys_untouched(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        state = map_anchors_to_hypernyms(
            {
                "query": "Does the hospital admin system fall in scope?",
                "context_graph_triples": B01_001_TRIPLES,
                "mode": "graph-compliance",
            },
            fragment_retriever=lambda label, top_m, settings: [],
        )

        assert state["query"] == "Does the hospital admin system fall in scope?"
        assert state["mode"] == "graph-compliance"
        assert "anchors" in state
        assert "hypernym_mappings" in state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
