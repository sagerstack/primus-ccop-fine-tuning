"""
Unit tests for the anchor extraction + hypernym mapping node (Phase 11, plan
11-06 Task 3, D-09/D-10).

Mirrors `test_function_type_routing.py`'s mocked-node testing shape, but
injects a fake `fragment_retriever` (constructor-injection seam) instead of
mocking an LLM client — this node's external dependency is Neo4j-backed
fragment retrieval, not an LLM call. Covers:
- Gating: only derives anchors/mappings for mode=="graph-compliance"; the
  fragment retriever is never invoked for other modes.
- Anchor derivation from Context Graph triples (actor/data/system only).
- The B01-001 scenario: a hospital-admin-system anchor produces a STRONG
  mapping supported by a CII-definition premise fragment.
- hypernym_mappings entries carry {label, strong_weak, supporting_premise, score}.
- Graceful degradation: a raising fragment_retriever never crashes the node.
"""

from unittest.mock import MagicMock, patch

import pytest

from rag.retrieval.nodes.anchor_hypernym_mapping import map_anchors_to_hypernyms


def _settings(**overrides):
    settings = MagicMock()
    settings.hypernym_top_m = 10
    for key, value in overrides.items():
        setattr(settings, key, value)
    return settings


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


class TestGating:
    """Node only derives anchors/mappings (and only calls the retriever) for graph-compliance mode."""

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_non_graph_compliance_mode_is_a_no_op(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_retriever = MagicMock()

        state = map_anchors_to_hypernyms(
            {"context_graph_triples": B01_001_TRIPLES, "mode": "hybrid"},
            fragment_retriever=mock_retriever,
        )

        mock_retriever.assert_not_called()
        assert state["anchors"] == []
        assert state["hypernym_mappings"] == []

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_missing_mode_key_defaults_to_no_op(self, mock_get_settings):
        mock_get_settings.return_value = _settings()
        mock_retriever = MagicMock()

        state = map_anchors_to_hypernyms(
            {"context_graph_triples": B01_001_TRIPLES},
            fragment_retriever=mock_retriever,
        )

        mock_retriever.assert_not_called()
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


class TestB01001HypernymMapping:
    """
    The worked example (11-CONTEXT.md): hospital admin system anchor should
    resolve STRONG via a CII-*definition* premise fragment (D-09), NOT a
    meta-CU designation rule.
    """

    def _b01_001_fragment_retriever(self, anchor_label, top_m, settings):
        # Every anchor sees the same small candidate pool for this test —
        # mirrors what a real top-M retrieval call would surface.
        return [
            {
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
            },
            {
                "cu_id": "metacu-act-7",
                "cu_type": "meta-CU",
                "citation_id": "Act-7",
                "text": "The Commissioner may designate a computer system as CII.",
                "subject": "computer system designated by the Commissioner",
                "is_premise": False,
                "score": 0.71,
            },
        ]

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_hospital_admin_system_anchor_produces_strong_mapping(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        state = map_anchors_to_hypernyms(
            {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
            fragment_retriever=self._b01_001_fragment_retriever,
        )

        anchor_labels = {a["label"] for a in state["anchors"]}
        assert "Hospital administration system" in anchor_labels

        strong_mappings = [m for m in state["hypernym_mappings"] if m["strong_weak"] == "STRONG"]
        assert len(strong_mappings) > 0
        strong = strong_mappings[0]
        assert "CII means" in strong["supporting_premise"]
        assert strong["score"] > 0

    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_mapping_entries_carry_the_d17_2_trace_shape(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        state = map_anchors_to_hypernyms(
            {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
            fragment_retriever=self._b01_001_fragment_retriever,
        )

        assert len(state["hypernym_mappings"]) > 0
        for mapping in state["hypernym_mappings"]:
            assert set(mapping.keys()) >= {"label", "strong_weak", "supporting_premise", "score"}
            assert mapping["strong_weak"] in ("STRONG", "WEAK")


class TestGracefulDegradation:
    @patch("rag.retrieval.nodes.anchor_hypernym_mapping.get_settings")
    def test_raising_fragment_retriever_never_crashes_the_node(self, mock_get_settings):
        mock_get_settings.return_value = _settings()

        def _raising_retriever(anchor_label, top_m, settings):
            raise RuntimeError("Neo4j unreachable")

        state = map_anchors_to_hypernyms(
            {"context_graph_triples": B01_001_TRIPLES, "mode": "graph-compliance"},
            fragment_retriever=_raising_retriever,
        )

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
