#!/usr/bin/env python3
"""
Contextual Chunking — Anthropic-style + breadcrumb augmentation.

For each chunk in `ccop_clauses_hybrid`:
  1. Build a deterministic breadcrumb from metadata (Document > Chapter > Section > Subsection)
  2. Generate a 1-2 sentence context line via gpt-4o-mini that explains the chunk's
     role in the parent document and lists likely synonym/query terms
  3. Build augmented_text = [breadcrumb] + [context] + [original_text]
  4. Re-embed (BGE-large dense + Qdrant/bm25 sparse)
  5. Write to new collection `ccop_clauses_contextual` (preserves original)

Cost: ~$0.20 (gpt-4o-mini × 700 chunks). Time: ~5-10 min with parallel LLM calls.

Usage:
    cd src && poetry run python ../.lab/workspace/contextualize_corpus.py
"""
from __future__ import annotations
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SRC = Path("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/src")
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

NEW_COLLECTION = "ccop_clauses_contextual"
SOURCE_COLLECTION = "ccop_clauses_hybrid"

CONTEXT_PROMPT = """You are processing a chunk from a regulatory document. Write a 1-2 sentence context for this chunk that explains its role in the parent document and includes likely synonyms/query terms a user might search with.

DOCUMENT: {document_source}
SECTION PATH: {parent_path}

CHUNK:
\"\"\"
{chunk_text}
\"\"\"

Write the context. Use natural language synonyms a reader might use when searching (e.g. "exemption" alongside "waiver", "remediation" alongside "fix", "logging" alongside "audit trail"). Do NOT include the chunk text itself in your response. Output ONLY the 1-2 sentence context, nothing else."""


def build_breadcrumb(payload: dict) -> str:
    """Deterministic structural breadcrumb from chunk metadata."""
    parts = []
    doc = payload.get("document_source") or "Document"
    parts.append(f"Doc: {doc}")
    if payload.get("chapter"):
        parts.append(f"Ch: {payload['chapter']}")
    if payload.get("section"):
        parts.append(f"Sec: {payload['section']}")
    if payload.get("subsection"):
        parts.append(f"Subsec: {payload['subsection']}")
    return "[" + " | ".join(parts) + "]"


def generate_context(client, model: str, payload: dict) -> str:
    """Single LLM call to generate context line for a chunk."""
    text = (payload.get("text") or "")[:2000]
    if not text.strip():
        return ""
    prompt = CONTEXT_PROMPT.format(
        document_source=payload.get("document_source", "Unknown"),
        parent_path=payload.get("parent_path", payload.get("citation_id", "")),
        chunk_text=text,
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning(f"Context gen failed for {payload.get('citation_id')}: {e}")
        return ""


def main():
    from infrastructure.config.container import get_container
    from infrastructure.config.settings import get_settings
    from openai import OpenAI
    from qdrant_client.models import (
        Distance, VectorParams, SparseVectorParams, SparseVector, PointStruct, Modifier
    )

    settings = get_settings()
    container = get_container()
    vs = container.vector_store()
    client = vs.client
    embed = vs.embedding_service

    if not settings.openrouter_api_key:
        raise SystemExit("CCOP_OPENROUTER_API_KEY not set")

    or_client = OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=60,
    )
    model_id = "openai/gpt-4o-mini"

    logger.info(f"Scrolling source collection: {SOURCE_COLLECTION}")
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

    # Generate contexts in parallel
    logger.info(f"Generating contexts via {model_id} (parallel)...")
    contexts: dict[str, str] = {}
    t0 = time.time()
    n_done = 0
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {
            pool.submit(generate_context, or_client, model_id, p.payload): p.id
            for p in chunks
        }
        for fut in as_completed(futures):
            pid = futures[fut]
            try:
                contexts[pid] = fut.result()
            except Exception as e:
                contexts[pid] = ""
                logger.warning(f"context error pid={pid}: {e}")
            n_done += 1
            if n_done % 50 == 0:
                logger.info(f"  contexts: {n_done}/{len(chunks)}  ({time.time()-t0:.0f}s)")
    logger.info(f"  ✓ {len(contexts)} contexts in {time.time()-t0:.1f}s")

    # Build augmented chunks: breadcrumb + context + original_text
    augmented_records = []
    for p in chunks:
        breadcrumb = build_breadcrumb(p.payload)
        ctx = contexts.get(p.id, "").strip()
        orig_text = p.payload.get("text", "")
        if ctx:
            augmented_text = f"{breadcrumb}\n\n[Context: {ctx}]\n\n{orig_text}"
        else:
            augmented_text = f"{breadcrumb}\n\n{orig_text}"
        augmented_records.append({
            "id": p.id,
            "augmented_text": augmented_text,
            "context_line": ctx,
            "breadcrumb": breadcrumb,
            "original_payload": p.payload,
        })

    # Re-embed (dense + sparse) with augmented text
    logger.info("Re-encoding with BGE-large + Qdrant/bm25 (augmented text)...")
    texts = [r["augmented_text"] for r in augmented_records]
    t1 = time.time()
    dense_vecs = embed.embed_documents(texts)
    logger.info(f"  dense done in {time.time()-t1:.1f}s")
    t2 = time.time()
    sparse_vecs = embed.embed_sparse_batch(texts)
    logger.info(f"  sparse done in {time.time()-t2:.1f}s")

    # Recreate target collection
    logger.info(f"Recreating collection: {NEW_COLLECTION}")
    if client.collection_exists(NEW_COLLECTION):
        client.delete_collection(NEW_COLLECTION)
    client.create_collection(
        collection_name=NEW_COLLECTION,
        vectors_config={
            "dense": VectorParams(size=len(dense_vecs[0]), distance=Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(modifier=Modifier.IDF),
        },
    )

    # Upsert points
    logger.info(f"Upserting {len(augmented_records)} points...")
    points = []
    for i, r in enumerate(augmented_records):
        # Update payload with new fields, but ALSO retain original text under a different key
        new_payload = dict(r["original_payload"])
        new_payload["text"] = r["augmented_text"]  # main text now augmented
        new_payload["original_text"] = r["original_payload"].get("text", "")
        new_payload["context_line"] = r["context_line"]
        new_payload["breadcrumb"] = r["breadcrumb"]
        points.append(PointStruct(
            id=r["id"],
            vector={
                "dense": dense_vecs[i],
                "sparse": SparseVector(
                    indices=sparse_vecs[i]["indices"],
                    values=sparse_vecs[i]["values"],
                ),
            },
            payload=new_payload,
        ))

    # Upsert in batches of 100
    for i in range(0, len(points), 100):
        client.upsert(collection_name=NEW_COLLECTION, points=points[i:i+100])

    logger.info(f"✓ Done. {len(points)} points in '{NEW_COLLECTION}'.")
    logger.info(f"  Source collection '{SOURCE_COLLECTION}' is unchanged.")

    # Save sample contexts for inspection
    sample_path = Path("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/.lab/workspace/contextualize-samples.json")
    sample = []
    for r in augmented_records[:20]:
        sample.append({
            "citation_id": r["original_payload"].get("citation_id"),
            "breadcrumb": r["breadcrumb"],
            "context": r["context_line"],
            "original_text_preview": r["original_payload"].get("text", "")[:300],
            "augmented_text_preview": r["augmented_text"][:600],
        })
    sample_path.write_text(json.dumps(sample, indent=2))
    logger.info(f"  Sample augmentations: {sample_path}")


if __name__ == "__main__":
    main()
