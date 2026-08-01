#!/usr/bin/env python3
"""
Retrieval Quality Evaluator — Phase A measurement tool.

Independent of LLM generation and judge. For each test case:
  1. Load expected clause_reference from ground truth.
  2. Run retrieval pipeline (Qdrant hybrid via DI container) directly.
  3. Optionally pass through reranker (per current setting CCOP_RAG_RERANK_ENABLED).
  4. Compare retrieved citation_ids vs expected clauses.
  5. Compute precision/recall/F1 at multiple k values + MRR.

USAGE:
  cd src && poetry run python ../.lab/workspace/retrieval_eval.py \\
      --test-ids B01-007 B08-001 ...                     # specific cases
      --sample-file ../research/human-kappa-seed/00-sample-selection.json   # all 30
      --top-k 20                                          # candidate set size
      --top-n 3                                           # final top-N (if reranker on)
      --output ../.lab/workspace/exp-N-retrieval.json     # output path

Runtime: ~30-60 sec for 30 cases (no LLM, no Primus).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Add src to path
SRC = Path("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/src")
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def normalise_clause(s: str) -> str:
    """Normalise a clause reference to a canonical form for matching.

    Strips whitespace, collapses spaces, removes 'CCoP 2.0::' prefix.
    """
    if s is None:
        return ""
    s = str(s).strip()
    # Strip CCoP 2.0:: prefix to get bare clause
    if s.startswith("CCoP 2.0::"):
        s = s[len("CCoP 2.0::"):]
    return s


def is_subletter_of(child: str, parent: str) -> bool:
    """True when child clause is a sub-letter or sub-section of parent.

    Examples:
      is_subletter_of('5.3.1(c)', '5.3.1') == True
      is_subletter_of('5.3.1(c)', '5.3.1(c)') == False  (same clause; that's exact)
      is_subletter_of('5.3.1.2', '5.3.1') == True
      is_subletter_of('5.3', '5') == True
    """
    if child == parent:
        return False
    if not child.startswith(parent):
        return False
    rest = child[len(parent):]
    # Must continue with '.' or '(' to be a true sub
    return rest.startswith(".") or rest.startswith("(")


def match_score(retrieved: str, expected: str) -> Tuple[float, str]:
    """Return (score 0..1, kind) for how well a retrieved id matches an expected clause.

    - exact: 1.0
    - retrieved is parent of expected (e.g., retrieved 5.3.1, expected 5.3.1(c)): 0.7
    - retrieved is child of expected: 0.7
    - same top-level section (5.3.x retrieved, 5.3.x expected): 0.3
    - same chapter (5.x retrieved, 5.x expected): 0.1
    - else: 0.0
    """
    r, e = normalise_clause(retrieved), normalise_clause(expected)
    if not r or not e:
        return 0.0, "empty"
    if r == e:
        return 1.0, "exact"
    if is_subletter_of(e, r):  # retrieved is parent
        return 0.7, "parent_of_expected"
    if is_subletter_of(r, e):  # retrieved is child
        return 0.7, "child_of_expected"
    # Same section (split by dots, first 2 parts equal — 5.3.x and 5.3.y)
    r_parts = r.split(".")
    e_parts = e.split(".")
    if len(r_parts) >= 2 and len(e_parts) >= 2 and r_parts[:2] == e_parts[:2]:
        return 0.3, "same_section"
    if len(r_parts) >= 1 and len(e_parts) >= 1 and r_parts[0] == e_parts[0]:
        return 0.1, "same_chapter"
    return 0.0, "no_match"


def get_parent_path(clause: str) -> str:
    """Return the parent path of a normalized clause id.

    "1.6.1(c)" → "1.6.1" (strip sub-letter parenthetical first)
    "1.6.1"    → "1.6"   (drop last dotted segment)
    "1.6"      → "1"
    "1"        → "1"
    """
    if "(" in clause:
        # Strip sub-letter: "1.6.1(c)" → "1.6.1"
        return clause.rsplit("(", 1)[0]
    parts = clause.split(".")
    if len(parts) > 1:
        return ".".join(parts[:-1])
    return clause


def merge_by_parent(reranked_clauses: List[str], window: int = 10, min_siblings: int = 2):
    """Auto-merge sibling clauses in the reranked head.

    Returns a list of "entries" where each entry is either a single clause str
    or a list of clause strs (merged section group). Entries are ordered by
    earliest occurrence in the original reranked list.

    Args:
        reranked_clauses: ordered list of clause IDs (e.g. from cross-encoder rank)
        window: only consider merging within first `window` items
        min_siblings: minimum sibling count to trigger merge
    """
    head = reranked_clauses[:window]
    tail = reranked_clauses[window:]

    # Group head by parent_path
    parent_groups: Dict[str, List[str]] = {}
    for c in head:
        if not c:
            continue
        p = get_parent_path(c)
        parent_groups.setdefault(p, []).append(c)

    # Walk head in order; first occurrence of each parent triggers entry creation
    merged: List = []
    seen_parents = set()
    for c in head:
        p = get_parent_path(c) if c else ""
        if p in seen_parents:
            continue
        seen_parents.add(p)
        siblings = parent_groups.get(p, [c])
        if len(siblings) >= min_siblings:
            merged.append(siblings)  # list = merged group
        else:
            merged.append(c)  # single clause

    # Tail (beyond window) stays unmerged
    for c in tail:
        merged.append(c)

    return merged


_M3_ENCODER = None


def _retrieve_single_mode(vector_store, query: str, k: int, mode: str, dense_encoder_override=None):
    """Call Qdrant directly for dense-only or sparse-only retrieval. Returns list of (Document, score) tuples like the hybrid adapter."""
    from langchain_core.documents import Document
    from qdrant_client.models import SparseVector
    client = vector_store.client
    collection = vector_store.collection_name
    embed = vector_store.embedding_service
    if mode == "dense":
        if dense_encoder_override is not None:
            dv = dense_encoder_override.encode(
                query, normalize_embeddings=True
            ).tolist()
        else:
            dv = embed.embed_query(query)
        results = client.query_points(
            collection_name=collection, query=dv, using="dense", limit=k,
            with_payload=True, with_vectors=False,
        )
    elif mode == "sparse":
        sd = embed.embed_sparse(query)
        sv = SparseVector(indices=sd["indices"], values=sd["values"])
        results = client.query_points(
            collection_name=collection, query=sv, using="sparse", limit=k,
            with_payload=True, with_vectors=False,
        )
    else:
        raise ValueError(f"Unknown retrieval_mode: {mode}")
    pairs = []
    for p in results.points:
        payload = p.payload or {}
        doc = Document(page_content=payload.get("text", ""), metadata={**payload, "similarity_score": float(p.score)})
        pairs.append((doc, float(p.score)))
    return pairs


@dataclass
class CaseResult:
    test_id: str
    benchmark: str
    expected: List[str]
    retrieved_topk: List[Dict[str, Any]]      # full top-K with scores
    retrieved_topn: List[Dict[str, Any]]      # final top-N delivered to LLM
    # Aggregate match metrics for top-N (what model actually sees)
    matched_topn_max_scores: Dict[str, float] = field(default_factory=dict)
    precision_topn: float = 0.0
    recall_topn: float = 0.0
    f1_topn: float = 0.0
    # Aggregate match metrics for top-K (candidate set quality)
    matched_topk_max_scores: Dict[str, float] = field(default_factory=dict)
    recall_topk: float = 0.0
    # MRR: rank of first chunk that exact-matches any expected
    mrr_topk: float = 0.0
    # Multi-N recall (after rerank, computed at multiple cutoffs incl. dynamic N=C)
    cardinality: int = 0  # |expected|
    recall_at_n: Dict[str, float] = field(default_factory=dict)  # keys: "3","5","8","10","C","K"
    precision_at_n: Dict[str, float] = field(default_factory=dict)
    f1_at_n: Dict[str, float] = field(default_factory=dict)


def evaluate_case(
    test_case: dict,
    vector_store,
    rerank_enabled: bool,
    rerank_top_n: int,
    top_k: int,
    cross_encoder_model: str,
    query_prefix: str = "",
    query_suffix: str = "",
    retrieval_mode: str = "hybrid",
    expected_override: list = None,
    merge_parents: bool = False,
    merge_window: int = 10,
    merge_min_siblings: int = 2,
    hyde_query: str = None,
    multi_query: bool = False,
    reranker_text: str = "original",  # "original" or "augmented"
    rrf_dense_weight: float = 1.0,
    rrf_ce_weight: float = 1.0,
    dense_encoder=None,  # Optional sentence-transformer override for query encoding
) -> CaseResult:
    """Run retrieval for one case and compute all match metrics."""
    test_id = test_case["test_id"]
    benchmark = test_case.get("benchmark_id") or test_case.get("metadata", {}).get("benchmark") or "?"
    if expected_override is not None:
        expected = expected_override
    else:
        expected = test_case.get("metadata", {}).get("clause_reference", []) or []
    expected = [normalise_clause(x) for x in expected if x]

    question = test_case["input"]["question"]
    # Apply query rewriting (suffix/prefix augmentation)
    augmented_query = (query_prefix + " " if query_prefix else "") + question + (" " + query_suffix if query_suffix else "")

    # HyDE: use hypothetical-clause text as the EMBEDDING query (retrieval only).
    # The original `augmented_query` is preserved for reranker scoring.
    # Multi-query mode: retrieve with BOTH original and HyDE, RRF-merge.
    use_multi = bool(hyde_query) and multi_query

    def _retrieve(q: str):
        if retrieval_mode == "hybrid":
            return vector_store.similarity_search_with_scores(query=q, k=top_k)
        return _retrieve_single_mode(vector_store, q, top_k, retrieval_mode, dense_encoder_override=dense_encoder)

    if use_multi:
        a = _retrieve(augmented_query)
        b = _retrieve(hyde_query)
        # RRF merge by citation_id
        K_RRF = 60
        scores: dict = {}
        kept: dict = {}
        for rank, (doc, score) in enumerate(a, 1):
            cid = doc.metadata.get("citation_id", "")
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (K_RRF + rank)
            kept[cid] = (doc, score)
        for rank, (doc, score) in enumerate(b, 1):
            cid = doc.metadata.get("citation_id", "")
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (K_RRF + rank)
            if cid not in kept:
                kept[cid] = (doc, score)
        sorted_cids = sorted(scores.keys(), key=lambda c: -scores[c])[:top_k]
        pairs = [kept[c] for c in sorted_cids]
    else:
        embed_query = hyde_query if hyde_query else augmented_query
        pairs = _retrieve(embed_query)
    topk_docs = [
        {
            "rank": i,
            "score": float(score),
            "citation_id": doc.metadata.get("citation_id", ""),
            "clause": normalise_clause(doc.metadata.get("citation_id", "")),
            "snippet": (doc.page_content or "")[:120].replace("\n", " "),
        }
        for i, (doc, score) in enumerate(pairs, 1)
    ]

    # 2. Optional reranking → keep FULL reranked order
    # If reranker_text == "rrf_dense_ce", combine dense rank + cross-encoder rank via RRF
    if reranker_text == "rrf_dense_ce" and rerank_enabled and len(pairs) > 0:
        from sentence_transformers import CrossEncoder
        if "_CE_CACHE" not in globals():
            globals()["_CE_CACHE"] = {}
        cache = globals()["_CE_CACHE"]
        if cross_encoder_model not in cache:
            cache[cross_encoder_model] = CrossEncoder(cross_encoder_model, max_length=512)
        ce = cache[cross_encoder_model]
        # Cross-encoder uses original_text (avoid breadcrumb distraction)
        ce_pairs = [
            (augmented_query, doc.metadata.get("original_text") or doc.page_content)
            for doc, _ in pairs
        ]
        ce_scores = ce.predict(ce_pairs, batch_size=8)
        # Build ranks: dense order is the input order; CE order is sorted by ce_scores desc
        dense_rank = {id(p[0]): i for i, p in enumerate(pairs, 1)}
        ce_sorted = sorted(zip(pairs, ce_scores), key=lambda x: -x[1])
        ce_rank = {id(p[0][0]): i for i, p in enumerate(ce_sorted, 1)}
        K_RRF = 60
        rrf_scored = []
        for doc, score in pairs:
            r_d = dense_rank[id(doc)]
            r_c = ce_rank[id(doc)]
            rrf = rrf_dense_weight / (K_RRF + r_d) + rrf_ce_weight / (K_RRF + r_c)
            rrf_scored.append((doc, rrf))
        full_reranked = sorted(rrf_scored, key=lambda x: -x[1])
    elif rerank_enabled and len(pairs) > 0:
        from sentence_transformers import CrossEncoder
        global _CE_CACHE
        if "_CE_CACHE" not in globals():
            _CE_CACHE = {}
        if cross_encoder_model not in _CE_CACHE:
            _CE_CACHE[cross_encoder_model] = CrossEncoder(cross_encoder_model, max_length=512)
        ce = _CE_CACHE[cross_encoder_model]
        # Reranker text source — controllable via reranker_text param.
        # "original": score against bare clause text (default; safer)
        # "augmented": score against augmented text (breadcrumb + context + questions + original)
        # "ensemble": score against BOTH and average — smooths polarization
        if reranker_text == "ensemble":
            orig_pairs = [
                (augmented_query, doc.metadata.get("original_text") or doc.page_content)
                for doc, _ in pairs
            ]
            aug_pairs = [(augmented_query, doc.page_content) for doc, _ in pairs]
            scores_orig = ce.predict(orig_pairs, batch_size=8)
            scores_aug = ce.predict(aug_pairs, batch_size=8)
            ce_scores = [(o + a) / 2.0 for o, a in zip(scores_orig, scores_aug)]
        elif reranker_text == "augmented":
            scored_pairs = [
                (augmented_query, doc.page_content)
                for doc, _ in pairs
            ]
            ce_scores = ce.predict(scored_pairs, batch_size=8)
        else:
            scored_pairs = [
                (
                    augmented_query,
                    doc.metadata.get("original_text") or doc.page_content,
                )
                for doc, _ in pairs
            ]
            ce_scores = ce.predict(scored_pairs, batch_size=8)
        rerank_sorted = sorted(
            zip(pairs, ce_scores),
            key=lambda x: x[1],
            reverse=True,
        )
        full_reranked = [(doc, sc) for ((doc, _), sc) in rerank_sorted]
    else:
        full_reranked = list(pairs)

    topn_pairs = full_reranked[:rerank_top_n]
    topn_docs = [
        {
            "score": float(score),
            "citation_id": doc.metadata.get("citation_id", ""),
            "clause": normalise_clause(doc.metadata.get("citation_id", "")),
            "snippet": (doc.page_content or "")[:120].replace("\n", " "),
        }
        for (doc, score) in topn_pairs
    ]
    # Save full reranked clause order so we can compute recall@any-N afterwards
    full_reranked_clauses = [
        normalise_clause(doc.metadata.get("citation_id", ""))
        for (doc, _) in full_reranked
    ]

    cr = CaseResult(
        test_id=test_id,
        benchmark=benchmark,
        expected=expected,
        retrieved_topk=topk_docs,
        retrieved_topn=topn_docs,
    )

    # 3. Match expected vs top-N (precision/recall/F1)
    # STRICT match threshold: only exact (1.0) or parent/child (0.7) counts
    # toward recall/precision. Same-section (0.3) and same-chapter (0.1) are
    # tracked but excluded — different sub-section is a different clause.
    STRICT_THRESH = 0.7

    if expected and topn_docs:
        # For each expected clause, find best match in top-N
        topn_max = {}
        for e in expected:
            best = 0.0
            for r in topn_docs:
                score, _ = match_score(r["clause"], e)
                if score > best:
                    best = score
            topn_max[e] = best
        cr.matched_topn_max_scores = topn_max
        # STRICT recall: fraction of expected clauses matched at >= 0.7 in top-N
        cr.recall_topn = sum(1 for s in topn_max.values() if s >= STRICT_THRESH) / len(expected)
        # STRICT precision: fraction of top-N entries that match any expected at >= 0.7
        n_matches = 0
        for r in topn_docs:
            for e in expected:
                s, _ = match_score(r["clause"], e)
                if s >= STRICT_THRESH:
                    n_matches += 1
                    break
        cr.precision_topn = n_matches / len(topn_docs) if topn_docs else 0.0
        cr.f1_topn = (
            2 * cr.precision_topn * cr.recall_topn / (cr.precision_topn + cr.recall_topn)
            if (cr.precision_topn + cr.recall_topn) > 0
            else 0.0
        )
    elif not expected:
        # No expected clauses (e.g., B21 hallucination test). Skip but record.
        cr.recall_topn = float("nan")
        cr.precision_topn = float("nan")
        cr.f1_topn = float("nan")

    # 4. Recall@K (candidate set quality) — STRICT
    if expected and topk_docs:
        topk_max = {}
        for e in expected:
            best = 0.0
            for r in topk_docs:
                score, _ = match_score(r["clause"], e)
                if score > best:
                    best = score
            topk_max[e] = best
        cr.matched_topk_max_scores = topk_max
        cr.recall_topk = sum(1 for s in topk_max.values() if s >= STRICT_THRESH) / len(expected)
    elif not expected:
        cr.recall_topk = float("nan")

    # 4b. Multi-N recall metrics (after rerank): N=3, 5, 8, 10, K=full pool, C=cardinality
    cr.cardinality = len(expected)
    # Optionally apply parent-child auto-merging
    if merge_parents:
        merged_entries = merge_by_parent(
            full_reranked_clauses,
            window=merge_window,
            min_siblings=merge_min_siblings,
        )
    else:
        merged_entries = list(full_reranked_clauses)

    def expand_entries(entries: list) -> list:
        """Flatten merged entries (lists) into clause id list for recall counting."""
        out = []
        for e in entries:
            if isinstance(e, list):
                out.extend(e)
            elif e:
                out.append(e)
        return out

    if expected and full_reranked_clauses:
        cutoffs = {"3": 3, "5": 5, "8": 8, "10": 10, "K": len(merged_entries), "C": cr.cardinality}
        for label, n in cutoffs.items():
            cutoff_entries = merged_entries[:n] if n > 0 else []
            top_n_clauses = expand_entries(cutoff_entries)
            # recall@n
            num_recalled = 0
            for e in expected:
                best = 0.0
                for r in top_n_clauses:
                    s, _ = match_score(r, e)
                    if s > best:
                        best = s
                if best >= STRICT_THRESH:
                    num_recalled += 1
            cr.recall_at_n[label] = num_recalled / len(expected) if expected else 0.0
            # precision@n
            num_pmatches = 0
            for r in top_n_clauses:
                for e in expected:
                    s, _ = match_score(r, e)
                    if s >= STRICT_THRESH:
                        num_pmatches += 1
                        break
            cr.precision_at_n[label] = num_pmatches / len(top_n_clauses) if top_n_clauses else 0.0
            # f1@n
            r_, p_ = cr.recall_at_n[label], cr.precision_at_n[label]
            cr.f1_at_n[label] = (2 * r_ * p_ / (r_ + p_)) if (r_ + p_) > 0 else 0.0
    elif not expected:
        for label in ["3", "5", "8", "10", "K", "C"]:
            cr.recall_at_n[label] = float("nan")
            cr.precision_at_n[label] = float("nan")
            cr.f1_at_n[label] = float("nan")

    # 5. MRR: rank of first exact-match clause
    if expected and topk_docs:
        for i, r in enumerate(topk_docs, 1):
            for e in expected:
                if r["clause"] == e:
                    cr.mrr_topk = 1.0 / i
                    break
            if cr.mrr_topk:
                break

    return cr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-ids", nargs="+", help="Specific test_ids to evaluate")
    ap.add_argument("--sample-file", help="Path to sample-selection.json")
    ap.add_argument("--top-k", type=int, default=None, help="Override CCOP_RAG_RETRIEVAL_TOP_K")
    ap.add_argument("--top-n", type=int, default=None, help="Override CCOP_RERANK_TOP_N")
    ap.add_argument("--rerank-enabled", choices=["true", "false", "auto"], default="auto")
    ap.add_argument("--ce-model", default=None, help="Override cross-encoder model (HF ID)")
    ap.add_argument("--query-prefix", default="", help="Text prepended to every query before retrieval")
    ap.add_argument("--query-suffix", default="", help="Text appended to every query before retrieval")
    ap.add_argument("--retrieval-mode", choices=["hybrid", "dense", "sparse"], default="hybrid", help="Retrieval mode for candidate set")
    ap.add_argument("--corrected-gt", default=None, help="Path to corrected-gt.json (overrides test_case.metadata.clause_reference)")
    ap.add_argument("--corrected-gt-field", default="recommended_ccop_only", choices=["recommended_full", "recommended_ccop_only", "recommended_external"], help="Which field of the corrected GT entry to use as expected clauses")
    ap.add_argument("--collection", default=None, help="Override Qdrant collection name (e.g. ccop_clauses_contextual)")
    ap.add_argument("--merge-parents", action="store_true", help="Apply parent-child auto-merging to reranked list")
    ap.add_argument("--merge-window", type=int, default=10, help="Top-K reranked window to consider for merging (default 10)")
    ap.add_argument("--merge-min-siblings", type=int, default=2, help="Minimum sibling clauses required to trigger merge (default 2)")
    ap.add_argument("--hyde", action="store_true", help="Generate HyDE hypothetical answer per query and use as retrieval query")
    ap.add_argument("--hyde-model", default="openai/gpt-4o-mini", help="OpenRouter model id for HyDE generation")
    ap.add_argument("--multi-query", action="store_true", help="Multi-query: retrieve with both original and HyDE, RRF-merge")
    ap.add_argument("--reranker-text", choices=["original", "augmented", "ensemble", "rrf_dense_ce"], default="original", help="Text source for reranker scoring or ranking strategy. 'rrf_dense_ce' = RRF ensemble of dense rank + CE rank.")
    ap.add_argument("--rrf-dense-weight", type=float, default=1.0, help="RRF weight on dense rank (only when --reranker-text=rrf_dense_ce)")
    ap.add_argument("--rrf-ce-weight", type=float, default=1.0, help="RRF weight on cross-encoder rank (only when --reranker-text=rrf_dense_ce)")
    ap.add_argument("--query-encoder", default=None, help="Override sentence-transformer model for query encoding (e.g. BAAI/bge-m3 to match a custom collection)")
    ap.add_argument("--output", required=True, help="Output JSON path")
    ap.add_argument("--label", default="", help="Label for this evaluation")
    args = ap.parse_args()

    # Load test cases
    if args.test_ids:
        test_ids = args.test_ids
    elif args.sample_file:
        with open(args.sample_file) as f:
            sample = json.load(f)
        test_ids = [c["test_id"] for c in sample]
    else:
        ap.error("--test-ids or --sample-file required")

    # Load full test cases from JSONL
    from infrastructure.config.container import get_container
    from infrastructure.config.settings import get_settings

    container = get_container()
    test_repo = container.test_case_repository()

    # Need raw dicts (with metadata.clause_reference). The repository returns TestCase entities,
    # so load directly from JSONL for raw access.
    import glob
    raw_cases = {}
    for f in glob.glob("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/ground-truth/test-suite/*.jsonl"):
        if ".bak" in f:
            continue
        with open(f) as fh:
            for line in fh:
                if not line.strip():
                    continue
                d = json.loads(line)
                raw_cases[d["test_id"]] = d

    cases = [raw_cases[tid] for tid in test_ids if tid in raw_cases]
    missing = [tid for tid in test_ids if tid not in raw_cases]
    if missing:
        print(f"WARN: missing test_ids: {missing}", file=sys.stderr)

    settings = get_settings()
    if args.rerank_enabled == "true":
        rerank_enabled = True
    elif args.rerank_enabled == "false":
        rerank_enabled = False
    else:
        rerank_enabled = settings.rag_rerank_enabled
    top_k = args.top_k if args.top_k else settings.rag_retrieval_top_k
    top_n = args.top_n if args.top_n else settings.rerank_top_n
    ce_model = args.ce_model if args.ce_model else settings.cross_encoder_model

    # Load corrected GT mapping if provided
    corrected_gt = None
    if args.corrected_gt:
        with open(args.corrected_gt) as f:
            corrected_gt = json.load(f)
        print(f"Loaded corrected GT from {args.corrected_gt} (field={args.corrected_gt_field})", file=sys.stderr)

    print(
        f"Config: top_k={top_k}, top_n={top_n}, rerank_enabled={rerank_enabled}, "
        f"cross_encoder={ce_model}, "
        f"query_prefix={args.query_prefix!r}, query_suffix={args.query_suffix!r}, "
        f"retrieval_mode={args.retrieval_mode}, corrected_gt={'YES' if corrected_gt else 'NO'}",
        file=sys.stderr,
    )

    vs = container.vector_store()
    if args.collection:
        # Override the adapter's collection name (so retrieval queries the new index)
        vs.collection_name = args.collection
        print(f"Using collection: {args.collection}", file=sys.stderr)

    dense_encoder = None
    if args.query_encoder:
        from sentence_transformers import SentenceTransformer
        print(f"Loading query encoder: {args.query_encoder}", file=sys.stderr)
        dense_encoder = SentenceTransformer(args.query_encoder)
        print("  loaded", file=sys.stderr)

    # Optionally pre-generate HyDE hypothetical clauses for all cases (parallel)
    hyde_map: Dict[str, str] = {}
    if args.hyde:
        from openai import OpenAI
        from concurrent.futures import ThreadPoolExecutor, as_completed
        if not settings.openrouter_api_key:
            raise SystemExit("CCOP_OPENROUTER_API_KEY not set; required for --hyde")
        oc = OpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url, timeout=60)
        HYDE_PROMPT = """You are simulating a CCoP 2.0 (Cybersecurity Code of Practice for Critical Information Infrastructure, Singapore) regulatory clause that would be cited as the answer to the question below. Write 2-3 sentences in formal regulatory style using the vocabulary of CCoP 2.0 ("the CIIO shall...", "the Commissioner may...", "waiver", "compliance", clause-style language). Do not include preamble — output only the hypothetical clause text.

QUESTION:
{q}

HYPOTHETICAL CLAUSE:"""
        print(f"Generating HyDE for {len(cases)} queries via {args.hyde_model}...", file=sys.stderr)
        def hyde_one(tc):
            q = tc["input"]["question"]
            try:
                resp = oc.chat.completions.create(
                    model=args.hyde_model,
                    messages=[{"role": "user", "content": HYDE_PROMPT.format(q=q)}],
                    temperature=0.2,
                    max_tokens=200,
                )
                return tc["test_id"], (resp.choices[0].message.content or "").strip()
            except Exception as e:
                print(f"  HyDE failed for {tc['test_id']}: {e}", file=sys.stderr)
                return tc["test_id"], ""
        t_hyde = time.time()
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(hyde_one, tc) for tc in cases]
            for fut in as_completed(futures):
                tid, ht = fut.result()
                hyde_map[tid] = ht
        print(f"  HyDE done in {time.time()-t_hyde:.1f}s", file=sys.stderr)

    t0 = time.time()
    results = []
    for tc in cases:
        expected_override = None
        if corrected_gt is not None:
            entry = corrected_gt.get(tc["test_id"])
            if entry:
                expected_override = entry.get(args.corrected_gt_field, [])
        cr = evaluate_case(
            test_case=tc,
            vector_store=vs,
            rerank_enabled=rerank_enabled,
            rerank_top_n=top_n,
            top_k=top_k,
            cross_encoder_model=ce_model,
            query_prefix=args.query_prefix,
            query_suffix=args.query_suffix,
            retrieval_mode=args.retrieval_mode,
            expected_override=expected_override,
            merge_parents=args.merge_parents,
            merge_window=args.merge_window,
            merge_min_siblings=args.merge_min_siblings,
            hyde_query=hyde_map.get(tc["test_id"]) if args.hyde else None,
            multi_query=args.multi_query,
            reranker_text=args.reranker_text,
            rrf_dense_weight=args.rrf_dense_weight,
            rrf_ce_weight=args.rrf_ce_weight,
            dense_encoder=dense_encoder,
        )
        results.append(cr)
        rcl = "nan" if cr.recall_topn != cr.recall_topn else f"{cr.recall_topn:.2f}"
        prc = "nan" if cr.precision_topn != cr.precision_topn else f"{cr.precision_topn:.2f}"
        rk = "nan" if cr.recall_topk != cr.recall_topk else f"{cr.recall_topk:.2f}"
        print(
            f"  {tc['test_id']}: expected={cr.expected[:3]}{'...' if len(cr.expected)>3 else ''} "
            f"R@N={rcl} P@N={prc} R@K={rk} MRR={cr.mrr_topk:.3f}",
            file=sys.stderr,
        )
    dur = time.time() - t0

    # Aggregate (skipping NaN cases)
    def safe_mean(values):
        clean = [v for v in values if v == v]  # filter NaN
        return sum(clean) / len(clean) if clean else float("nan")

    agg = {
        "label": args.label,
        "config": {
            "top_k": top_k,
            "top_n": top_n,
            "rerank_enabled": rerank_enabled,
            "cross_encoder_model": ce_model,
            "query_prefix": args.query_prefix,
            "query_suffix": args.query_suffix,
            "retrieval_mode": args.retrieval_mode,
            "merge_parents": args.merge_parents,
            "merge_window": args.merge_window,
            "merge_min_siblings": args.merge_min_siblings,
            "hyde": args.hyde,
            "hyde_model": args.hyde_model if args.hyde else None,
            "multi_query": args.multi_query,
        },
        "n_cases": len(results),
        "n_with_expected": sum(1 for r in results if r.expected),
        "duration_sec": round(dur, 1),
        "metrics": {
            "mean_recall_topn": safe_mean(r.recall_topn for r in results),
            "mean_precision_topn": safe_mean(r.precision_topn for r in results),
            "mean_f1_topn": safe_mean(r.f1_topn for r in results),
            "mean_recall_topk": safe_mean(r.recall_topk for r in results),
            "mean_mrr_topk": safe_mean(r.mrr_topk for r in results),
            **{
                f"mean_recall_at_{label}": safe_mean(r.recall_at_n.get(label, float('nan')) for r in results)
                for label in ["3", "5", "8", "10", "K", "C"]
            },
            **{
                f"mean_precision_at_{label}": safe_mean(r.precision_at_n.get(label, float('nan')) for r in results)
                for label in ["3", "5", "8", "10", "K", "C"]
            },
            **{
                f"mean_f1_at_{label}": safe_mean(r.f1_at_n.get(label, float('nan')) for r in results)
                for label in ["3", "5", "8", "10", "K", "C"]
            },
        },
        "per_case": [asdict(r) for r in results],
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(agg, f, indent=2)

    print(file=sys.stderr)
    print(f"=== AGGREGATE ({len(results)} cases, {dur:.1f}s) ===", file=sys.stderr)
    for k, v in agg["metrics"].items():
        v_str = "nan" if v != v else f"{v:.4f}"
        print(f"  {k}: {v_str}", file=sys.stderr)
    print(f"Wrote: {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
