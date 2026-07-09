"""Phase 7 — dense index over the :Clause layer (the paper's Traditional-RAG *Semantic* channel).

Our Channel-II stopgap was BM25 (lexical) only; abstract clauses that are semantically-but-not-
lexically similar to a query (B01-001: §1.4.1 scope determination, Act §7) never surfaced. The OMD
paper's traditional channel is dense semantic + keyword; this adds the dense half.

Embeds all 863 :Clause texts ONCE with the project's dense encoder (BAAI/bge-large-en-v1.5, the same
model + asymmetric prompt convention hybrid mode uses — settings.graph_embedding_model — so graphont
stays comparable to hybrid/graphcpl). Documents embedded WITHOUT the query prompt; both normalised
(cosine == dot). Cached to runs/dense/clauses_<build_id>.npz (droppable with the rest of the layer).

    poetry run python -m rag.graph.ontology_v2.build_dense_index            # dry-run counts
    poetry run python -m rag.graph.ontology_v2.build_dense_index --apply
"""
import argparse
from pathlib import Path

import numpy as np

from rag.graph.ontology_v2._neo import query as _q
from infrastructure.config.settings import get_settings

BUILD_ID = "omd-v1-20260709"
_OUT = Path(__file__).parent / "runs" / "dense"
QUERY_PROMPT = "Represent this sentence for searching relevant passages: "  # bge asymmetric (query side)


def _passages():
    """Clauses + definitions (id, text). Definitions indexed as 'term: definition' so the 40 glossary
    terms with no DEFINES edge (otherwise unreachable) become retrievable by content."""
    ids, texts = [], []
    for r in _q("MATCH (c:Clause {build_id:$b}) WHERE c.text IS NOT NULL "
                "RETURN c.citation_id AS id, c.text AS text ORDER BY c.citation_id", b=BUILD_ID):
        ids.append(r["id"]); texts.append(r["text"])
    for r in _q("MATCH (d:Definition {build_id:$b}) "
                "RETURN d.def_id AS id, d.term AS term, d.definition AS def ORDER BY d.def_id", b=BUILD_ID):
        ids.append(r["id"]); texts.append(f"{r['term']}: {r['def']}")
    return ids, texts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    cids, texts = _passages()
    s = get_settings()
    print(f"to embed: {len(cids)} passages (clauses + definitions) | model={s.graph_embedding_model} "
          f"dim={s.graph_embedding_dimensions} (build_id={BUILD_ID})")
    if not a.apply:
        print("dry-run — pass --apply to load the model and write the .npz")
        return
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(s.graph_embedding_model)
    emb = model.encode(texts, batch_size=32, normalize_embeddings=True,
                       show_progress_bar=True, convert_to_numpy=True).astype(np.float32)
    _OUT.mkdir(parents=True, exist_ok=True)
    out = _OUT / f"clauses_{BUILD_ID}.npz"
    np.savez(out, cids=np.array(cids), emb=emb, model=s.graph_embedding_model)
    print(f"WROTE {out}  shape={emb.shape}")


if __name__ == "__main__":
    main()
