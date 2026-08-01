"""Regression tests for omd_agentic_context_assembly error resilience.

Prevents re-occurrence of KeyError 'retrieval_trace' bug (fixed 2026-07-24).
"""
from unittest.mock import patch

from rag.retrieval.nodes.omd_agentic_context_assembly import omd_agentic_context_assembly


def test_omd_agentic_context_assembly_creates_trace_before_retrieve():
    """Regression test for KeyError 'retrieval_trace' bug.
    
    Verifies retrieval_trace exists even if retrieve() throws.
    
    Context: In Slice 3, omd_pack was moved to graph routing. If retrieve()
    failed before trace creation, pack_contexts would KeyError on
    state["retrieval_trace"]. The fix moved trace creation to line 1.
    """
    from unittest.mock import patch
    from rag.retrieval.nodes.omd_agentic_context_assembly import omd_agentic_context_assembly
    
    state = {"query": "test", "mode": "graphont-agentic"}
    
    # Mock retrieve() to throw (simulates Neo4j down, timeout, OOM, etc.)
    with patch("rag.retrieval.nodes.omd_agentic_context_assembly.omd_retrieval.retrieve",
               side_effect=Exception("Simulated retrieve failure")):
        try:
            omd_agentic_context_assembly(state)
        except Exception:
            pass  # Expected to propagate
        
        # Critical assertion: trace should exist even after failure
        assert "retrieval_trace" in state, \
            "retrieval_trace must be created at line 1 (before retrieve)"
        assert isinstance(state["retrieval_trace"], dict), \
            "retrieval_trace must be a dict (even if empty)"


def test_omd_pack_handles_missing_trace_gracefully():
    """Regression test for omd_pack KeyError when retrieval_trace missing.
    
    Verifies omd_pack uses .get() with safe defaults so it doesn't KeyError
    on missing or empty trace.
    """
    from rag.retrieval.nodes.omd_pack import omd_pack
    
    # Test 1: completely empty state
    state1 = {}
    result1 = omd_pack(state1)
    assert result1.get("retrieval_succeeded") == False
    assert len(result1.get("documents", [])) == 0
    
    # Test 2: trace exists but empty
    state2 = {"retrieval_trace": {}}
    result2 = omd_pack(state2)
    assert result2.get("retrieval_succeeded") == False
    assert len(result2.get("documents", [])) == 0
    
    # Test 3: trace with candidates
    state3 = {
        "retrieval_trace": {
            "candidates": [
                {"citation_id": "test::1.1", "text": "test", "score": 0.9, "kind": "clause"}
            ],
            "definitions": []
        }
    }
    result3 = omd_pack(state3)
    assert result3.get("retrieval_succeeded") == True
    assert len(result3.get("documents", [])) == 1
