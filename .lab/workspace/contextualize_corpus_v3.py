#!/usr/bin/env python3
"""
Contextualize v3 — gpt-4o-mini, instruct to use acronyms WITHOUT expansion.

Combines findings:
- Exp #14 (original gpt-4o-mini): loose style works, but hallucinated CIIO/CSA expansions
- Exp #39 (Claude grounded): too domain-precise, hurt retrieval
- Exp #40 (dictionary constraint): too formulaic, hurt retrieval

v3 strategy: use only acronyms (CIIO, CSA, CCoP, etc.) — never expand them.
Avoids hallucinations entirely without constraining the loose synonym-heavy style.
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

NEW_COLLECTION = "ccop_clauses_contextual_v3"
SOURCE_COLLECTION = "ccop_clauses_contextual"

CONTEXT_PROMPT = """You are processing a chunk from a Singapore regulatory document. Write a 1-2 sentence context for the chunk that explains its role in the parent document and includes likely synonyms/query terms a user might search with.

CRITICAL: Use acronyms (CIIO, CSA, CCoP, CII, CIRT, etc.) WITHOUT expanding them. Do NOT spell out what any acronym stands for. Just use the acronym verbatim.

DOCUMENT: {document_source}
SECTION PATH: {parent_path}

CHUNK:
\"\"\"
{chunk_text}
\"\"\"

Write the context. Use natural language synonyms a reader might use when searching (e.g. "exemption" alongside "waiver", "remediation" alongside "fix", "logging" alongside "audit trail"). Do NOT include the chunk text itself in your response. Do NOT spell out acronyms — leave them as-is. Output ONLY the 1-2 sentence context, nothing else."""


def generate_context(client, model: str, payload: dict) -> str:
    text = (payload.get("original_text") or payload.get("text", ""))[:2000]
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
            max_tokens=250,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning(f"err for {payload.get('citation_id')}: {e}")
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

    or_client = OpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url, timeout=60)
    model_id = "openai/gpt-4o-mini"

    chunks = []
    offset = None
    while True:
        pts, next_off = client.scroll(SOURCE_COLLECTION, limit=300, offset=offset, with_payload=True, with_vectors=False)
        chunks.extend(pts)
        if next_off is None: break
        offset = next_off
    logger.info(f"  → {len(chunks)} chunks")

    contexts = {}
    t0 = time.time()
    n_done = 0
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(generate_context, or_client, model_id, p.payload): p.id for p in chunks}
        for fut in as_completed(futures):
            pid = futures[fut]
            try:
                contexts[pid] = fut.result()
            except Exception as e:
                contexts[pid] = ""
            n_done += 1
            if n_done % 50 == 0:
                logger.info(f"  contexts: {n_done}/{len(chunks)}  ({time.time()-t0:.0f}s)")
    logger.info(f"  ✓ {len(contexts)} contexts in {time.time()-t0:.1f}s")

    new_records = []
    for p in chunks:
        pl = p.payload or {}
        breadcrumb = pl.get("breadcrumb", "")
        ctx = contexts.get(p.id, "").strip()
        original = pl.get("original_text") or pl.get("text", "")
        ctx_block = f"[Context: {ctx}]\n\n" if ctx else ""
        bc_block = f"{breadcrumb}\n\n" if breadcrumb else ""
        augmented_text = bc_block + ctx_block + original
        new_records.append({"id": p.id, "text": augmented_text, "context": ctx, "payload": pl})

    logger.info("Re-encoding...")
    texts = [r["text"] for r in new_records]
    t1 = time.time()
    dense_vecs = embed.embed_documents(texts)
    logger.info(f"  dense done in {time.time()-t1:.1f}s")
    sparse_vecs = embed.embed_sparse_batch(texts)

    if client.collection_exists(NEW_COLLECTION):
        client.delete_collection(NEW_COLLECTION)
    client.create_collection(
        collection_name=NEW_COLLECTION,
        vectors_config={"dense": VectorParams(size=len(dense_vecs[0]), distance=Distance.COSINE)},
        sparse_vectors_config={"sparse": SparseVectorParams(modifier=Modifier.IDF)},
    )
    points = []
    for i, r in enumerate(new_records):
        new_payload = dict(r["payload"])
        new_payload["text"] = r["text"]
        new_payload["context_line_v3"] = r["context"]
        points.append(PointStruct(
            id=r["id"],
            vector={"dense": dense_vecs[i],
                    "sparse": SparseVector(indices=sparse_vecs[i]["indices"], values=sparse_vecs[i]["values"])},
            payload=new_payload,
        ))
    for i in range(0, len(points), 100):
        client.upsert(collection_name=NEW_COLLECTION, points=points[i:i+100])
    logger.info(f"✓ Done. {len(points)} points in '{NEW_COLLECTION}'.")

    sample_path = "/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/.lab/workspace/contextualize-v3-samples.json"
    sample = []
    for r in new_records[:15]:
        sample.append({
            "citation_id": r["payload"].get("citation_id"),
            "context": r["context"],
        })
    json.dump(sample, open(sample_path, "w"), indent=2)
    logger.info(f"  Samples: {sample_path}")


if __name__ == "__main__":
    main()
