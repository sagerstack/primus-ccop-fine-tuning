"""
Retrieval Precision Benchmark

Validates Phase 1 Success Criterion 3: Retrieval precision >80% on ground truth CCoP queries.
"""

import os
import pytest
from typing import List, Tuple

from infrastructure.config.settings import get_settings
from rag.retrieval.graph import build_rag_graph
from rag.retrieval.state.graph_state import GraphState


# Ground truth query-answer pairs with expected retrieval sources
GROUND_TRUTH_QUERIES = [
    {
        "query": "What are the access control requirements for Critical Information Infrastructure?",
        "expected_sections": ["Section 5", "Access Control"],
        "expected_documents": ["CCoP 2.0", "CCoP"],
    },
    {
        "query": "What are the incident reporting timelines under CCoP?",
        "expected_sections": ["Section 7", "Incident", "Response"],
        "expected_documents": ["CCoP 2.0", "CCoP"],
    },
    {
        "query": "How should CII owners conduct cybersecurity risk assessment?",
        "expected_sections": ["Risk", "Assessment"],
        "expected_documents": ["Risk Assessment", "Guide"],
    },
    {
        "query": "What are the requirements for cybersecurity audit of Critical Information Infrastructure?",
        "expected_sections": ["Audit", "Auditing"],
        "expected_documents": ["Audit", "Guidelines"],
    },
    {
        "query": "What does CCoP say about threat modelling for CII?",
        "expected_sections": ["Threat", "Model"],
        "expected_documents": ["Threat", "Modelling", "Guide"],
    },
    {
        "query": "What are the physical security requirements for Critical Information Infrastructure?",
        "expected_sections": ["Section 4", "Physical", "Security"],
        "expected_documents": ["CCoP 2.0", "CCoP"],
    },
    {
        "query": "How should CII owners implement security monitoring and logging?",
        "expected_sections": ["Section 6", "Monitor", "Logging", "Security Monitoring"],
        "expected_documents": ["CCoP 2.0", "CCoP"],
    },
    {
        "query": "What are the network security requirements under CCoP 2.0?",
        "expected_sections": ["Section 5", "Network", "Security"],
        "expected_documents": ["CCoP 2.0", "CCoP"],
    },
    {
        "query": "What does security by design mean for Critical Information Infrastructure?",
        "expected_sections": ["Security", "Design"],
        "expected_documents": ["Security By Design", "Framework"],
    },
    {
        "query": "What are the supply chain security requirements for CII?",
        "expected_sections": ["Section 8", "Supply Chain", "Third Party"],
        "expected_documents": ["CCoP 2.0", "CCoP"],
    },
]


def check_databricks_configured() -> bool:
    """Check if Databricks credentials are configured."""
    settings = get_settings()
    return all([
        settings.databricks_host,
        settings.databricks_token,
        settings.databricks_vector_search_endpoint,
    ])


def matches_expected(text: str, expected_terms: List[str]) -> bool:
    """
    Check if text contains at least one of the expected terms (case-insensitive).

    Args:
        text: Text to search in
        expected_terms: List of terms (at least one must match)

    Returns:
        True if any term is found
    """
    text_lower = text.lower()
    return any(term.lower() in text_lower for term in expected_terms)


def calculate_precision(
    query: str,
    expected_sections: List[str],
    expected_documents: List[str],
    retrieved_documents: List,
) -> Tuple[float, List[str], List[str]]:
    """
    Calculate precision for a single query.

    Precision = (relevant retrieved) / (total retrieved)

    A document is relevant if its metadata matches expected sections OR expected documents.

    Args:
        query: Query string
        expected_sections: Expected section keywords
        expected_documents: Expected document keywords
        retrieved_documents: List of Document objects from retrieval pipeline

    Returns:
        Tuple of (precision, matched_sources, all_sources)
    """
    if not retrieved_documents:
        return 0.0, [], []

    relevant_count = 0
    matched_sources = []
    all_sources = []

    for doc in retrieved_documents:
        metadata = doc.metadata
        document_source = metadata.get("document_source", "")
        section = metadata.get("section", "")
        citation_id = metadata.get("citation_id", "")

        # Build source description for reporting
        source_desc = f"{document_source} - {section}" if section else document_source
        all_sources.append(source_desc)

        # Check if document matches expected sections or documents
        is_relevant = (
            matches_expected(section, expected_sections) or
            matches_expected(document_source, expected_documents)
        )

        if is_relevant:
            relevant_count += 1
            matched_sources.append(source_desc)

    precision = relevant_count / len(retrieved_documents)
    return precision, matched_sources, all_sources


@pytest.mark.integration
@pytest.mark.skipif(
    not check_databricks_configured(),
    reason="Databricks credentials not configured (set CCOP_DATABRICKS_* env vars)"
)
class TestRetrievalPrecision:
    """
    Benchmark retrieval precision against ground truth CCoP compliance queries.

    Target: >=80% average precision (Phase 1 Success Criterion 3).
    """

    def test_retrieval_precision_benchmark(self):
        """
        Run retrieval pipeline on 10 ground truth queries and measure precision.

        For each query:
        1. Initialize state with query
        2. Run query_analysis node
        3. Run retrieval node
        4. Run grade_documents node
        5. Extract filtered_documents (relevant docs after grading)
        6. Calculate precision against expected sections/documents

        Assert: average precision >= 80%
        """
        settings = get_settings()
        graph = build_rag_graph(settings)

        precisions = []
        results = []

        print("\n" + "=" * 80)
        print("RETRIEVAL PRECISION BENCHMARK")
        print("=" * 80)

        for i, test_case in enumerate(GROUND_TRUTH_QUERIES, start=1):
            query = test_case["query"]
            expected_sections = test_case["expected_sections"]
            expected_documents = test_case["expected_documents"]

            # Initialize state
            initial_state: GraphState = {
                "query": query,
                "rewritten_query": "",
                "needs_retrieval": False,
                "documents": [],
                "filtered_documents": [],
                "grading_scores": [],
                "retrieval_succeeded": False,
                "retrieval_attempts": 0,
                "generation": "",
                "is_rag_augmented": False,
                "citations": [],
                "error": "",
            }

            # Run the graph (full pipeline)
            try:
                final_state = graph.invoke(initial_state)

                # Extract filtered documents (post-grading)
                filtered_docs = final_state.get("filtered_documents", [])
                retrieval_succeeded = final_state.get("retrieval_succeeded", False)

                # Calculate precision
                precision, matched_sources, all_sources = calculate_precision(
                    query, expected_sections, expected_documents, filtered_docs
                )

                precisions.append(precision)

                # Store result for reporting
                result = {
                    "query": query,
                    "precision": precision,
                    "retrieval_succeeded": retrieval_succeeded,
                    "matched_sources": matched_sources,
                    "all_sources": all_sources,
                    "passed": precision >= 0.80,
                }
                results.append(result)

                # Print per-query result
                status = "✓ PASS" if result["passed"] else "✗ FAIL"
                print(f"\nQuery {i}: {status}")
                print(f"  Question: {query[:80]}...")
                print(f"  Precision: {precision:.2%}")
                print(f"  Retrieved: {len(filtered_docs)} documents")
                print(f"  Matched sources: {', '.join(matched_sources[:3]) if matched_sources else 'None'}")
                if not result["passed"]:
                    print(f"  Expected: sections={expected_sections}, documents={expected_documents}")
                    print(f"  Actual sources: {', '.join(all_sources[:3])}")

            except Exception as e:
                print(f"\nQuery {i}: ✗ ERROR")
                print(f"  Question: {query[:80]}...")
                print(f"  Error: {e}")
                # Treat errors as 0 precision
                precisions.append(0.0)
                results.append({
                    "query": query,
                    "precision": 0.0,
                    "retrieval_succeeded": False,
                    "matched_sources": [],
                    "all_sources": [],
                    "passed": False,
                })

        # Calculate average precision
        avg_precision = sum(precisions) / len(precisions) if precisions else 0.0
        passed_count = sum(1 for r in results if r["passed"])

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total queries: {len(GROUND_TRUTH_QUERIES)}")
        print(f"Passed (>=80%): {passed_count}/{len(GROUND_TRUTH_QUERIES)}")
        print(f"Average precision: {avg_precision:.2%}")
        print(f"Target: >=80%")
        print(f"Status: {'✓ PASS' if avg_precision >= 0.80 else '✗ FAIL'}")
        print("=" * 80)

        # Assert average precision meets threshold
        assert avg_precision >= 0.80, (
            f"Average retrieval precision {avg_precision:.2%} below 80% threshold. "
            f"Only {passed_count}/{len(GROUND_TRUTH_QUERIES)} queries passed."
        )

    def test_ground_truth_query_sample(self):
        """
        Smoke test: Run a single ground truth query to verify pipeline works.
        """
        settings = get_settings()
        graph = build_rag_graph(settings)

        query = "What are the access control requirements for Critical Information Infrastructure?"

        initial_state: GraphState = {
            "query": query,
            "rewritten_query": "",
            "needs_retrieval": False,
            "documents": [],
            "filtered_documents": [],
            "grading_scores": [],
            "retrieval_succeeded": False,
            "retrieval_attempts": 0,
            "generation": "",
            "is_rag_augmented": False,
            "citations": [],
            "error": "",
        }

        final_state = graph.invoke(initial_state)

        # Basic assertions
        assert final_state["retrieval_succeeded"] is True, "Retrieval should succeed for compliance query"
        assert len(final_state["filtered_documents"]) > 0, "Should retrieve at least one relevant document"
        assert final_state["generation"], "Should generate a response"
        assert final_state["is_rag_augmented"] is True, "Response should be RAG-augmented"
