"""
Method B: Clustering Ontology Cross-Check (D-01/D-02/D-05)

The SECOND leg of D-01's ontology-construction sequence
`C (grounded synthesis) -> curate (gate a) -> B (clustering) -> reconcile
(gate b) -> lock`.

Method B is a structurally DIFFERENT discovery lens run as an INDEPENDENT
COVERAGE CROSS-CHECK against the human-approved Method-C draft
(`ontology_draft.json`) -- NOT a replacement for it. Its job is to catch
candidate types Method C missed, which the human curation gate (b) then
decides keep/drop on.

Pipeline (RESEARCH.md Q6, "Method B", D-05):

  1. Extract candidate domain terms from corpus PROSE via a lightweight
     "list the domain terms / noun phrases" gpt-4o-mini prompt over
     section-level passages -- a FRESH corpus extraction. This module reads
     ONLY the Docling-parsed CCoP markdown (via
     `rag.graph.build.corpus_source.load_ccop_corpus_texts`, the identical
     text the KG builders consume). It does NOT read the Phase 9 emergent
     knowledge graph or any other built graph artifact -- discovery runs
     fresh from the corpus, per D-02.
  2. Embed each term with the SAME
     `SentenceTransformerEmbeddings(model=settings.graph_embedding_model)`
     already used for chunk embeddings (D-05/D-07 -- reuse the one embedding
     model, do not add a second).
  3. Cluster the term embeddings with `sklearn.cluster.AffinityPropagation`
     (article-suggested, D-05) -- no pre-set k, so structure emerges.
  4. LLM-name each cluster (one small gpt-4o-mini call per cluster) into a
     candidate PascalCase type label.
  5. Cross-check against Method C: a named cluster whose type is ABSENT from
     the Method-C draft (matched by label OR any member term) is a
     `b_only` candidate -> surfaced to the human gate (b) for keep/drop.

Output: a reconcile report `{c_types, b_types, b_only, overlap,
c_not_corroborated}` written to `method_b_reconcile.json` for the gate. This
module NEVER locks the ontology -- locking (`additional_*_types=false`) is a
separate, post-gate step (plan 10-04 Task 3), only after the D-14/D-17
coverage checks pass on the reconciled type set.

The two LLM seams (term extraction, cluster naming) and the embedder are
INJECTABLE so the unit suite runs deterministically offline; the default
factories follow the project's OpenRouter graceful-degradation convention
(see `rag.retrieval.nodes.query_analysis._generate_hyde`).

Usage:
    cd src && poetry run python -m rag.graph.ontology.discovery.method_b_clustering \\
        --method-c rag/graph/ontology/ontology_draft.json \\
        --ccop-dir ../ccop-official \\
        --output rag/graph/ontology/method_b_reconcile.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from infrastructure.config.settings import Settings, get_settings
from rag.graph.build.corpus_source import DEFAULT_CCOP_DIR, load_ccop_corpus_texts

logger = logging.getLogger(__name__)

# Injectable LLM seams (defaults call OpenRouter gpt-4o-mini).
TermExtractor = Callable[[str], list[str]]  # (passage prose) -> candidate terms
ClusterNamer = Callable[[list[str]], str]  # (cluster member terms) -> PascalCase type label

DEFAULT_METHOD_C_PATH = "rag/graph/ontology/ontology_draft.json"
DEFAULT_OUTPUT_PATH = "rag/graph/ontology/method_b_reconcile.json"

# Passage windowing for term extraction (bounded so the real run stays a
# reasonable number of LLM calls; stratified per document).
DEFAULT_WORDS_PER_PASSAGE = 400
DEFAULT_MAX_PASSAGES_PER_DOC = 6


@dataclass
class NamedCluster:
    """One AffinityPropagation cluster after LLM naming."""

    name: str
    members: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Embedding + clustering (pure, offline-testable)
# ---------------------------------------------------------------------------


def embed_terms(terms: list[str], embedder: Any) -> Any:
    """Embed each term via the injected embedder's `embed_query` (the same
    interface `SentenceTransformerEmbeddings` exposes). Returns an (n, d)
    float ndarray."""
    import numpy as np

    vectors = [embedder.embed_query(term) for term in terms]
    return np.asarray(vectors, dtype=float)


def cluster_terms(embeddings: Any, *, random_state: int = 0) -> list[int]:
    """Cluster term embeddings with AffinityPropagation (no pre-set k, D-05).

    Degrades safely: empty -> []; single term -> [0]; non-convergence (all
    -1 labels) -> each term its own cluster.
    """
    import numpy as np

    arr = np.asarray(embeddings, dtype=float)
    n = arr.shape[0] if arr.ndim else 0
    if n == 0:
        return []
    if n == 1:
        return [0]

    from sklearn.cluster import AffinityPropagation

    ap = AffinityPropagation(random_state=random_state)
    labels = ap.fit_predict(arr)
    labels_list = [int(lbl) for lbl in labels]
    if not labels_list or all(lbl == -1 for lbl in labels_list):
        logger.warning("AffinityPropagation did not converge; falling back to singleton clusters")
        return list(range(n))
    return labels_list


def group_terms_by_cluster(terms: list[str], labels: list[int]) -> list[list[str]]:
    """Group terms by cluster label, preserving first-appearance order."""
    labels = list(labels)
    order: list[int] = []
    groups: dict[int, list[str]] = {}
    for term, label in zip(terms, labels, strict=False):
        if label not in groups:
            groups[label] = []
            order.append(label)
        groups[label].append(term)
    return [groups[label] for label in order]


# ---------------------------------------------------------------------------
# Cross-check against Method C (pure, offline-testable)
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _method_c_labels(method_c_draft: dict) -> list[str]:
    labels: list[str] = []
    for nt in method_c_draft.get("node_types", []):
        label = nt["label"] if isinstance(nt, dict) else nt
        if label:
            labels.append(str(label))
    return labels


def _c_covered_index(method_c_draft: dict) -> dict[str, str]:
    """Map every normalized C concept (label + example terms + real
    flagged-ambiguity synonyms) to its canonical C label, so a B cluster can
    be matched to C via its NAME or any MEMBER TERM."""
    index: dict[str, str] = {}
    for nt in method_c_draft.get("node_types", []):
        if isinstance(nt, dict):
            label = str(nt.get("label", ""))
        else:
            label = str(nt)
        if not label:
            continue
        index.setdefault(_normalize(label), label)
        if isinstance(nt, dict):
            for term in nt.get("example_terms", []) or []:
                index.setdefault(_normalize(str(term)), label)
            for amb in nt.get("flagged_ambiguities", []) or []:
                amb = str(amb)
                # Skip curation notes like "motivated by B01, B02" -- they are
                # provenance breadcrumbs, not concept synonyms.
                if amb.lower().startswith("motivated by"):
                    continue
                norm = _normalize(amb)
                if norm:
                    index.setdefault(norm, label)
    return index


def _match_cluster_to_c(cluster: NamedCluster, c_index: dict[str, str]) -> str | None:
    """Return the matched C label if the cluster's name or any member term is
    already covered by Method C, else None."""
    matched = c_index.get(_normalize(cluster.name))
    if matched:
        return matched
    for term in cluster.members:
        matched = c_index.get(_normalize(term))
        if matched:
            return matched
    return None


def build_reconcile_report(named_clusters: list[NamedCluster], method_c_draft: dict) -> dict[str, Any]:
    """Diff Method-B named clusters against the Method-C draft.

    Returns the human-gate (b) reconcile report:
      - c_types            : all Method-C node-type labels.
      - b_types            : all Method-B named cluster labels.
      - b_only             : clusters NOT covered by C (candidate missing types).
      - overlap            : clusters covered by C (independent corroboration).
      - c_not_corroborated : C types no B cluster matched (possible over-inclusions).
    """
    c_index = _c_covered_index(method_c_draft)
    c_types = sorted(set(_method_c_labels(method_c_draft)))
    b_types = sorted({c.name for c in named_clusters if c.name})

    b_only: list[dict[str, Any]] = []
    overlap: list[dict[str, Any]] = []
    corroborated_c: set[str] = set()

    for cluster in named_clusters:
        matched = _match_cluster_to_c(cluster, c_index)
        if matched:
            overlap.append(
                {"name": cluster.name, "members": cluster.members, "matched_c_type": matched}
            )
            corroborated_c.add(matched)
        else:
            b_only.append({"name": cluster.name, "members": cluster.members})

    c_not_corroborated = sorted(set(c_types) - corroborated_c)

    return {
        "c_types": c_types,
        "b_types": b_types,
        "b_only": b_only,
        "overlap": overlap,
        "c_not_corroborated": c_not_corroborated,
    }


# ---------------------------------------------------------------------------
# Corpus term extraction (fresh from prose -- D-02)
# ---------------------------------------------------------------------------


def iter_corpus_passages(
    corpus_texts: dict[str, str],
    *,
    words_per_passage: int = DEFAULT_WORDS_PER_PASSAGE,
    max_passages_per_doc: int = DEFAULT_MAX_PASSAGES_PER_DOC,
) -> list[str]:
    """Stratified section-level prose passages across all source documents.

    Reads ONLY the corpus markdown (headings stripped) -- never the emergent
    graph (D-02). Bounded per document so the term-extraction LLM-call count
    stays reasonable for the cross-check.
    """
    passages: list[str] = []
    for _doc_name, text in corpus_texts.items():
        body_lines = [ln for ln in text.splitlines() if not ln.strip().startswith("#")]
        words = " ".join(body_lines).split()
        made = 0
        for start in range(0, len(words), words_per_passage):
            if made >= max_passages_per_doc:
                break
            chunk = " ".join(words[start : start + words_per_passage]).strip()
            if chunk:
                passages.append(chunk)
                made += 1
    return passages


def extract_corpus_terms(
    corpus_texts: dict[str, str],
    term_extractor: TermExtractor,
    *,
    words_per_passage: int = DEFAULT_WORDS_PER_PASSAGE,
    max_passages_per_doc: int = DEFAULT_MAX_PASSAGES_PER_DOC,
) -> list[str]:
    """Run the injected term extractor over every corpus passage, deduping
    terms case-insensitively while preserving first-seen surface form."""
    seen: dict[str, str] = {}
    for passage in iter_corpus_passages(
        corpus_texts,
        words_per_passage=words_per_passage,
        max_passages_per_doc=max_passages_per_doc,
    ):
        for term in term_extractor(passage) or []:
            term = str(term).strip()
            if not term:
                continue
            key = term.lower()
            if key not in seen:
                seen[key] = term
    return list(seen.values())


# ---------------------------------------------------------------------------
# Default LLM seams (OpenRouter gpt-4o-mini, graceful degradation)
# ---------------------------------------------------------------------------

_TERM_EXTRACTION_PROMPT = """You are assisting with ontology discovery for a knowledge graph over \
Singapore's CCoP 2.0 Cybersecurity Code of Practice. From the regulatory passage below, list the \
DOMAIN TERMS and noun phrases that name a TYPE of thing (entities, roles, asset/system categories, \
process or governance concepts).

Rules:
- Output STRICT JSON only: {{"terms": ["...", "..."]}}
- Terms only -- no verbs, no full sentences, no clause numbers, no placeholder/example names.
- Prefer canonical noun phrases as they appear in the text (e.g. "critical information \
infrastructure", "incident response plan", "privileged access").
- If the passage names no domain terms, return {{"terms": []}}.

PASSAGE:
{passage}
"""

_CLUSTER_NAMING_PROMPT = """You are naming a cluster of related domain terms discovered from \
Singapore's CCoP 2.0 Cybersecurity Code of Practice. Given the member terms below (which an \
embedding-based clustering grouped as near-synonyms/one concept), propose ONE canonical \
PascalCase entity-TYPE label that best names the shared concept.

Rules:
- Output STRICT JSON only: {{"label": "PascalCaseLabel"}}
- One label, canonical and reusable (e.g. "CriticalInformationInfrastructure", "AccessControl").
- Name the TYPE, not an instance.

MEMBER TERMS:
{members}
"""


def _default_term_extractor(settings: Settings) -> TermExtractor:
    def extract(passage: str) -> list[str]:
        if not settings.openrouter_api_key:
            logger.warning("Method B term extraction skipped -- CCOP_OPENROUTER_API_KEY not set")
            return []
        if not passage.strip():
            return []
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                timeout=120,
            )
            resp = client.chat.completions.create(
                model=settings.ontology_discovery_model,
                messages=[{"role": "user", "content": _TERM_EXTRACTION_PROMPT.format(passage=passage)}],
                temperature=0.2,
                max_tokens=800,
                response_format={"type": "json_object"},
            )
            raw = (resp.choices[0].message.content or "").strip()
            terms = json.loads(raw).get("terms", [])
            return [str(t) for t in terms] if isinstance(terms, list) else []
        except Exception as e:  # graceful degradation (project convention)
            logger.warning(f"Method B term extraction failed for a passage: {e}")
            return []

    return extract


def _default_cluster_namer(settings: Settings) -> ClusterNamer:
    def name(members: list[str]) -> str:
        fallback = "".join(w.capitalize() for w in re.split(r"\W+", members[0]) if w) if members else "Cluster"
        if not settings.openrouter_api_key or not members:
            return fallback
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                timeout=60,
            )
            resp = client.chat.completions.create(
                model=settings.ontology_discovery_model,
                messages=[
                    {"role": "user", "content": _CLUSTER_NAMING_PROMPT.format(members=", ".join(members))}
                ],
                temperature=0.2,
                max_tokens=60,
                response_format={"type": "json_object"},
            )
            raw = (resp.choices[0].message.content or "").strip()
            label = str(json.loads(raw).get("label", "")).strip()
            return label or fallback
        except Exception as e:  # graceful degradation
            logger.warning(f"Method B cluster naming failed: {e}")
            return fallback

    return name


def _default_embedder(settings: Settings) -> Any:
    """Reuse the SAME embedding model as chunk embeddings (D-05/D-07)."""
    from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings

    return SentenceTransformerEmbeddings(model=settings.graph_embedding_model)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_method_b(
    corpus_texts: dict[str, str],
    method_c_draft: dict,
    embedder: Any,
    *,
    term_extractor: TermExtractor,
    cluster_namer: ClusterNamer,
    words_per_passage: int = DEFAULT_WORDS_PER_PASSAGE,
    max_passages_per_doc: int = DEFAULT_MAX_PASSAGES_PER_DOC,
) -> dict[str, Any]:
    """Full Method-B pipeline: extract terms -> embed -> cluster -> name ->
    cross-check against Method C. Returns the reconcile report augmented with
    `terms` and `clusters` provenance for the human gate."""
    terms = extract_corpus_terms(
        corpus_texts,
        term_extractor,
        words_per_passage=words_per_passage,
        max_passages_per_doc=max_passages_per_doc,
    )
    logger.info(f"Method B extracted {len(terms)} unique candidate terms from corpus prose")

    if not terms:
        report = build_reconcile_report([], method_c_draft)
        report["terms"] = []
        report["clusters"] = []
        return report

    embeddings = embed_terms(terms, embedder)
    labels = cluster_terms(embeddings)
    clusters = group_terms_by_cluster(terms, labels)
    logger.info(f"Method B AffinityPropagation produced {len(clusters)} clusters")

    named_clusters = [NamedCluster(name=cluster_namer(members), members=members) for members in clusters]

    report = build_reconcile_report(named_clusters, method_c_draft)
    report["terms"] = terms
    report["clusters"] = [{"name": c.name, "members": c.members} for c in named_clusters]
    return report


def build_cross_check(
    settings: Settings,
    method_c_draft: dict,
    ccop_dir: str = DEFAULT_CCOP_DIR,
) -> dict[str, Any]:
    """Wire the default OpenRouter + SentenceTransformer seams and run Method B
    against the live corpus + the approved Method-C draft."""
    logger.info("Loading CCoP corpus (Docling markdown, same text the KG builders consume)...")
    corpus_texts = load_ccop_corpus_texts(settings, ccop_dir)

    return run_method_b(
        corpus_texts,
        method_c_draft,
        _default_embedder(settings),
        term_extractor=_default_term_extractor(settings),
        cluster_namer=_default_cluster_namer(settings),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Method B: clustering ontology cross-check (D-01/D-05). One-shot "
            "curation-time script -- produces a reconcile report for gate (b), "
            "NEVER locks the ontology."
        )
    )
    parser.add_argument("--method-c", default=DEFAULT_METHOD_C_PATH, help="Approved Method-C draft JSON")
    parser.add_argument("--ccop-dir", default=DEFAULT_CCOP_DIR, help="CCoP PDFs base directory")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH, help="Output reconcile-report path")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s -- %(message)s",
        datefmt="%H:%M:%S",
    )

    method_c_draft = json.loads(Path(args.method_c).read_text(encoding="utf-8"))
    settings = get_settings()

    report = build_cross_check(settings, method_c_draft, ccop_dir=args.ccop_dir)
    report = {
        "method": "B (AffinityPropagation clustering cross-check)",
        "generated_at": datetime.now(UTC).isoformat(),
        "method_c_source": args.method_c,
        **report,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("\n" + "=" * 60)
    print("METHOD-B CLUSTERING CROSS-CHECK COMPLETE")
    print("=" * 60)
    print(f"Candidate terms extracted: {len(report.get('terms', []))}")
    print(f"Clusters (candidate B types): {len(report.get('b_types', []))}")
    print(f"B-only candidate types: {[c['name'] for c in report['b_only']]}")
    print(f"C types not corroborated by B: {report['c_not_corroborated']}")
    print(f"Output: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
