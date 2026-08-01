#!/usr/bin/env python3
"""
Re-encode the contextualized corpus with BGE-M3 (instead of bge-large-en-v1.5).

Source: ccop_clauses_contextual (already has augmented_text in payload)
Target: ccop_clauses_bge_m3 (same payload, new dense vectors)
Sparse vectors: re-use Qdrant/bm25 from EmbeddingService (unchanged).

Cost: ~5 min embedding 495 chunks with BGE-M3.
"""
from __future__ import annotations
import logging
import sys
import time
from pathlib import Path

SRC = Path("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/src")
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

NEW_COLLECTION = "ccop_clauses_bge_m3"
SOURCE_COLLECTION = "ccop_clauses_contextual"
M3_MODEL = "BAAI/bge-m3"


def main():
    from infrastructure.config.container import get_container
    from sentence_transformers import SentenceTransformer
    from qdrant_client.models import (
        Distance, VectorParams, SparseVectorParams, SparseVector, PointStruct, Modifier
    )

    container = get_container()
    vs = container.vector_store()
    client = vs.client
    embed = vs.embedding_service  # for sparse only

    logger.info(f"Loading BGE-M3 ({M3_MODEL}) on CPU (avoid MPS OOM)...")
    m3 = SentenceTransformer(M3_MODEL, device="cpu")
    logger.info("  loaded")

    logger.info(f"Scrolling source: {SOURCE_COLLECTION}")
    chunks = []
    offset = None
    while True:
        pts, next_off = client.scroll(
            SOURCE_COLLECTION, limit=300, offset=offset,
            with_payload=True, with_vectors=False,
        )
        chunks.extend(pts)
        if next_off is None:
            break
        offset = next_off
    logger.info(f"  → {len(chunks)} chunks")

    # Use the same augmented text from payload "text" (which was the contextualized text)
    texts = [(p.payload or {}).get("text", "") for p in chunks]
    logger.info(f"Encoding with BGE-M3 (n={len(texts)}; ~5 min)...")
    t0 = time.time()
    dense_vecs = m3.encode(texts, batch_size=4, show_progress_bar=True, normalize_embeddings=True)
    logger.info(f"  ✓ dense done in {time.time()-t0:.1f}s, dim={dense_vecs.shape[1]}")

    # Sparse from current embedder (Qdrant/bm25)
    t1 = time.time()
    sparse_vecs = embed.embed_sparse_batch(texts)
    logger.info(f"  ✓ sparse done in {time.time()-t1:.1f}s")

    # Recreate target collection
    logger.info(f"Recreating collection: {NEW_COLLECTION}")
    if client.collection_exists(NEW_COLLECTION):
        client.delete_collection(NEW_COLLECTION)
    client.create_collection(
        collection_name=NEW_COLLECTION,
        vectors_config={"dense": VectorParams(size=dense_vecs.shape[1], distance=Distance.COSINE)},
        sparse_vectors_config={"sparse": SparseVectorParams(modifier=Modifier.IDF)},
    )

    # Build points
    points = []
    for i, p in enumerate(chunks):
        new_payload = dict(p.payload or {})
        new_payload["embed_model"] = M3_MODEL
        points.append(PointStruct(
            id=p.id,
            vector={
                "dense": dense_vecs[i].tolist(),
                "sparse": SparseVector(
                    indices=sparse_vecs[i]["indices"],
                    values=sparse_vecs[i]["values"],
                ),
            },
            payload=new_payload,
        ))

    # Upsert in batches
    for i in range(0, len(points), 100):
        client.upsert(collection_name=NEW_COLLECTION, points=points[i:i+100])
    logger.info(f"✓ Done. {len(points)} points in '{NEW_COLLECTION}'.")


if __name__ == "__main__":
    main()
