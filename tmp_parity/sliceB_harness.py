"""Slice-B PARITY HARNESS — graphont (omd_context_assembly) byte-identity guard.

Two-phase design so PRE/POST comparison is deterministic despite retrieve()'s
live gpt-4o-mini + Neo4j non-determinism:

  RECORD phase (--record): call the REAL omd_retrieval.retrieve(question) once per
    test_id and freeze the raw payload to fixtures/<test_id>.retrieve.json. This is
    the *input* to the node's packing logic and is frozen so it never varies again.

  GOLDEN phase (default): replay each frozen payload THROUGH the node by
    monkeypatching omd_retrieval.retrieve to return the frozen payload, then snapshot
    the FULL state delta the node writes + the exact emitted log line. Because the
    input payload is identical PRE and POST, any diff in the golden is caused solely
    by the refactored packing/state-writing code — which is exactly what parity guards.

Usage:
  poetry run python tmp_parity/sliceB_harness.py --record          # once, before builder
  poetry run python tmp_parity/sliceB_harness.py --out DIR         # capture goldens
"""
import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
sys.path.insert(0, str(SRC))

FIXDIR = Path(__file__).resolve().parent / "fixtures"
TESTS = {
    "B01-001": "b01_ccop_applicability_scope",
    "B02-001": "b02_compliance_classification",
    "B05-001": "b05_control_comprehension",
    "B12-001": "b12_audit_perspective_alignment",
    "B24-001": "b24_incident_response_guidance",
}


def _question(test_id: str) -> str:
    f = REPO / "ground-truth" / "test-suite" / f"{TESTS[test_id]}.jsonl"
    with f.open() as fh:
        for line in fh:
            d = json.loads(line)
            if d["test_id"] == test_id:
                return d["input"]["question"]
    raise KeyError(test_id)


def _canon(obj):
    """Deterministic JSON string: sorted keys, stable float repr."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
                      default=lambda o: f"<<{type(o).__name__}>>")


def _serialize_doc(d):
    """langchain Document -> stable dict (page_content + sorted metadata w/ repr'd floats)."""
    meta = {}
    for k in sorted(d.metadata):
        v = d.metadata[k]
        meta[k] = repr(v) if isinstance(v, float) else v
    return {"page_content": d.page_content, "metadata": meta}


def record():
    FIXDIR.mkdir(parents=True, exist_ok=True)
    from rag.graph.ontology_v2 import omd_retrieval
    for tid in TESTS:
        q = _question(tid)
        out = omd_retrieval.retrieve(q, k=8)
        (FIXDIR / f"{tid}.retrieve.json").write_text(
            json.dumps({"question": q, "payload": out}, indent=1, default=str))
        print(f"recorded {tid}: results={len(out.get('results',[]))} "
              f"defs={len(out.get('definitions',[]))} ranked_by={out.get('ranked_by')}")


# --- Synthetic payloads: exercise the omd_pack branches the real test_ids miss ---------
# real B01/B02/B05/B12/B24 all return defs=0 -> only the CLAUSE branch is covered.
# These craft payloads that hit: injected-definition packing, retrieved-def dedup vs
# injected, and the empty/degrade paths. "__RAISE__" makes retrieve() raise -> except branch.
SYNTH = {
    # WITH channel keys (ch1/bm25/dense/rrf) as the REAL retrieve() always emits -> exercises
    # omd_pack's injected-def + retrieved-def-DEDUP + clause branches (real cases have defs=0).
    "SYNTH-DEFS-CH": {
        "question": "synthetic: definitions + dedup + clause (channel keys present)",
        "payload": {
            "definitions": [
                {"citation_id": "CCoP::1.2.1", "term": "CII", "definition": "critical information infrastructure def"},
            ],
            "results": [
                {"kind": "definition", "citation_id": "CCoP::1.2.1", "term": "CII",
                 "definition": "dup should be skipped", "score": 0.9,
                 "ch1": 0.0, "bm25": 0.0, "dense": 0.0, "rrf": 0.01},
                {"kind": "definition", "citation_id": "CCoP::2.1", "term": "CIIO",
                 "definition": "owner def", "score": 0.8,
                 "ch1": 0.0, "bm25": 1.2, "dense": 0.0, "rrf": 0.02},
                {"kind": "clause", "citation_id": "CCoP::4.5.1", "doc": "CCoP",
                 "text": "passwords shall be at least 12 characters", "score": 0.7,
                 "ch1": 3.1, "bm25": 2.0, "dense": 0.5, "rrf": 0.03},
            ],
            "ranked_by": "ce+rrf(conf=0.50)", "d_cand": 42,
        },
    },
    # WITHOUT channel keys -> documents the NEW hard-subscript fragility (omd_retrieve reads
    # r["ch1"]). Original packed 3 docs; new code KeyErrors -> degrades whole context to empty.
    "SYNTH-DEFS-NOCH": {
        "question": "synthetic: definitions + dedup + clause (NO channel keys)",
        "payload": {
            "definitions": [
                {"citation_id": "CCoP::1.2.1", "term": "CII", "definition": "critical information infrastructure def"},
            ],
            "results": [
                {"kind": "definition", "citation_id": "CCoP::1.2.1", "term": "CII",
                 "definition": "dup should be skipped", "score": 0.9},
                {"kind": "definition", "citation_id": "CCoP::2.1", "term": "CIIO",
                 "definition": "owner def", "score": 0.8},
                {"kind": "clause", "citation_id": "CCoP::4.5.1", "doc": "CCoP",
                 "text": "passwords shall be at least 12 characters", "score": 0.7},
            ],
            "ranked_by": "ce+rrf(conf=0.50)", "d_cand": 42,
        },
    },
    "SYNTH-EMPTY": {
        "question": "synthetic: empty retrieval",
        "payload": {"definitions": [], "results": [], "ranked_by": "none", "d_cand": 0},
    },
    "SYNTH-RAISE": {"question": "synthetic: retrieve raises -> degrade-safe warning",
                    "payload": "__RAISE__"},
}


def _load_node(node_file):
    """Load the omd_context_assembly module from an arbitrary file path (e.g. a HEAD
    blob dumped to /tmp) so PRE-goldens bind to the pristine baseline even if the
    working copy has been edited in parallel. Default = the installed package module."""
    if not node_file:
        import rag.retrieval.nodes.omd_context_assembly as node_mod
        return node_mod
    import importlib.util
    spec = importlib.util.spec_from_file_location("_omd_node_under_test", node_file)
    node_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(node_mod)
    return node_mod


def capture(outdir: Path, node_file=None):
    outdir.mkdir(parents=True, exist_ok=True)
    node_mod = _load_node(node_file)
    from rag.graph.ontology_v2 import omd_retrieval

    md5_table = {}
    cases = {tid: json.loads((FIXDIR / f"{tid}.retrieve.json").read_text()) for tid in TESTS}
    cases.update(SYNTH)
    for tid in cases:
        payload, question = cases[tid]["payload"], cases[tid]["question"]

        # Freeze retrieve() to the recorded/synthetic payload -> deterministic node input.
        if payload == "__RAISE__":
            def _boom(*a, **k):
                raise RuntimeError("synthetic retrieval failure")
            omd_retrieval.retrieve = _boom
        else:
            omd_retrieval.retrieve = lambda *a, _p=payload, **k: _p

        # Capture emitted log line(s) from ANY logger (the refactor may emit from a
        # different module logger) — attach to ROOT so we compare the MESSAGE fairly.
        # We record message text (parity-relevant) and logger name (surfaced separately).
        logs = []
        lognames = []

        class _Cap(logging.Handler):
            def emit(self, r):
                msg = r.getMessage()
                if "OMD-GraphRAG" in msg:
                    logs.append(f"{r.levelname}:{msg}")
                    lognames.append(r.name)

        root = logging.getLogger()
        h = _Cap()
        root.addHandler(h)
        prev_level = root.level
        root.setLevel(logging.DEBUG)
        try:
            state = {"mode": "graphont", "query": question}
            before = set(state)
            result = node_mod.omd_context_assembly(state)
            written = {k: result[k] for k in result if k not in before or k in
                       ("filtered_documents", "documents", "is_rag_augmented",
                        "retrieval_succeeded")}
        finally:
            root.removeHandler(h)
            root.setLevel(prev_level)

        # docs-only hash lets us separate a genuine content regression from a
        # log-emission/logger-name change.
        docs_blob = _canon([_serialize_doc(d) for d in written.get("filtered_documents", [])])
        # PARITY SCOPE (coordinator's definition): the 4 ORIGINAL keys + the success/failure
        # log MESSAGE text must be byte-identical. The additive `retrieval_trace` key and the
        # emitting logger NAME are EXCLUDED from the assertion (design Q5 / cosmetic).
        parity_obj = {
            "filtered_documents": [_serialize_doc(d) for d in written.get("filtered_documents", [])],
            "documents": [_serialize_doc(d) for d in written.get("documents", [])],
            "is_rag_augmented": written.get("is_rag_augmented"),
            "retrieval_succeeded": written.get("retrieval_succeeded"),
            "log_lines": logs,
        }
        parity_md5 = hashlib.md5(_canon(parity_obj).encode()).hexdigest()
        golden = {
            "test_id": tid,
            "written_keys": sorted(written),
            "parity_md5": parity_md5,           # <-- the assertion hash (4 keys + log msg)
            **parity_obj,
            "log_logger_names": lognames,       # informational only (excluded from parity)
            "has_retrieval_trace": "retrieval_trace" in written,  # informational (additive)
            "docs_md5": hashlib.md5(docs_blob.encode()).hexdigest(),
        }
        blob = _canon(golden)
        (outdir / f"{tid}.json").write_text(blob)
        md5 = hashlib.md5(blob.encode()).hexdigest()
        md5_table[tid] = md5
        print(f"{tid}  md5={md5}  docs={len(golden['filtered_documents'])}  logs={logs}")

    (outdir / "_md5.json").write_text(json.dumps(md5_table, indent=1, sort_keys=True))
    print("\nMD5 TABLE:")
    for tid, m in sorted(md5_table.items()):
        print(f"  {tid}  {m}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--out", default="/tmp/sliceB_pre_goldens")
    ap.add_argument("--node-file", default=None,
                    help="path to omd_context_assembly.py to test (default: installed pkg)")
    a = ap.parse_args()
    if a.record:
        record()
    else:
        capture(Path(a.out), a.node_file)
