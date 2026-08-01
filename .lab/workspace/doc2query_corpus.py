#!/usr/bin/env python3
"""
Doc2Query — bake synthetic user questions into each chunk's indexed text.

For each chunk in ccop_clauses_contextual:
  1. Use gpt-4o-mini to generate 3-5 likely user questions about the chunk's content
  2. Build augmented_text = breadcrumb + context + [questions] + original_text
  3. Re-embed (BGE-large dense + Qdrant/bm25 sparse)
  4. Write to new collection `ccop_clauses_doc2query`

Builds on top of contextual chunking (Exp 14). Adds the third augmentation layer.

Cost: ~$0.50 (gpt-4o-mini × 495 chunks × ~150 tokens each).
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

NEW_COLLECTION = "ccop_clauses_doc2query"
SOURCE_COLLECTION = "ccop_clauses_contextual"  # use contextualized as base

QUESTION_PROMPT = """You are creating training data for a regulatory document retrieval system. Given the CCoP 2.0 clause text and its document context below, write 3-5 likely user questions that a regulatory analyst, auditor, or risk manager might search with to find this clause. The questions should:

- Use varied vocabulary (synonyms, paraphrases) — NOT just the words in the clause
- Cover different angles: definitional ("what is..."), prescriptive ("must..."), scenario-based ("if X happens..."), evidence-based ("how to demonstrate...")
- Be natural and conversational, like a real practitioner would type into a search bar

DOCUMENT: {document_source}
SECTION: {parent_path}

CLAUSE TEXT:
\"\"\"
{chunk_text}
\"\"\"

Output ONLY the 3-5 questions, one per line. No numbering, no preamble, just the questions."""


def gen_questions(client, model: str, payload: dict) -> list[str]:
    """One LLM call per chunk; return list of 3-5 question strings."""
    text = (payload.get("original_text") or payload.get("text") or "")[:1500]
    if not text.strip():
        return []
    prompt = QUESTION_PROMPT.format(
        document_source=payload.get("document_source", "Unknown"),
        parent_path=payload.get("parent_path", payload.get("citation_id", "")),
        chunk_text=text,
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        out = (resp.choices[0].message.content or "").strip()
        # Split into lines, filter empty, take up to 5
        lines = [ln.strip().rstrip("?") + "?" if ln.strip() else "" for ln in out.split("\n")]
        return [ln for ln in lines if ln and len(ln) > 10][:5]
    except Exception as e:
        logger.warning(f"q-gen failed for {payload.get('citation_id')}: {e}")
        return []


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
    or_client = OpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url, timeout=60)
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

    logger.info(f"Generating questions via {model_id} (parallel)...")
    questions: dict = {}
    t0 = time.time()
    n_done = 0
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(gen_questions, or_client, model_id, p.payload): p.id for p in chunks}
        for fut in as_completed(futures):
            pid = futures[fut]
            try:
                questions[pid] = fut.result()
            except Exception as e:
                questions[pid] = []
                logger.warning(f"q error pid={pid}: {e}")
            n_done += 1
            if n_done % 50 == 0:
                logger.info(f"  questions: {n_done}/{len(chunks)}  ({time.time()-t0:.0f}s)")
    logger.info(f"  ✓ {sum(1 for q in questions.values() if q)} chunks with questions in {time.time()-t0:.1f}s")

    # Build new texts
    new_records = []
    for p in chunks:
        pl = p.payload
        breadcrumb = pl.get("breadcrumb", "")
        context = pl.get("context_line", "")
        original = pl.get("original_text") or pl.get("text", "")
        qs = questions.get(p.id, [])
        q_block = ""
        if qs:
            q_block = "[Likely questions:\n" + "\n".join(f"- {q}" for q in qs) + "]\n\n"
        ctx_block = f"[Context: {context}]\n\n" if context else ""
        bc_block = f"{breadcrumb}\n\n" if breadcrumb else ""
        augmented_text = bc_block + ctx_block + q_block + original

        new_records.append({
            "id": p.id,
            "augmented_text": augmented_text,
            "questions": qs,
            "original_payload": pl,
        })

    logger.info("Re-encoding (BGE-large dense + Qdrant/bm25)...")
    texts = [r["augmented_text"] for r in new_records]
    t1 = time.time()
    dense_vecs = embed.embed_documents(texts)
    logger.info(f"  dense done in {time.time()-t1:.1f}s")
    t2 = time.time()
    sparse_vecs = embed.embed_sparse_batch(texts)
    logger.info(f"  sparse done in {time.time()-t2:.1f}s")

    logger.info(f"Recreating collection: {NEW_COLLECTION}")
    if client.collection_exists(NEW_COLLECTION):
        client.delete_collection(NEW_COLLECTION)
    client.create_collection(
        collection_name=NEW_COLLECTION,
        vectors_config={"dense": VectorParams(size=len(dense_vecs[0]), distance=Distance.COSINE)},
        sparse_vectors_config={"sparse": SparseVectorParams(modifier=Modifier.IDF)},
    )

    logger.info(f"Upserting {len(new_records)} points...")
    points = []
    for i, r in enumerate(new_records):
        new_payload = dict(r["original_payload"])
        # Set the chunk text used by retriever to augmented; keep original_text in payload
        new_payload["text"] = r["augmented_text"]
        # Make sure original_text is preserved (already in source payload, but be explicit)
        if "original_text" not in new_payload:
            new_payload["original_text"] = r["original_payload"].get("original_text") or r["original_payload"].get("text", "")
        new_payload["d2q_questions"] = r["questions"]
        points.append(PointStruct(
            id=r["id"],
            vector={
                "dense": dense_vecs[i],
                "sparse": SparseVector(indices=sparse_vecs[i]["indices"], values=sparse_vecs[i]["values"]),
            },
            payload=new_payload,
        ))

    for i in range(0, len(points), 100):
        client.upsert(collection_name=NEW_COLLECTION, points=points[i:i+100])

    logger.info(f"✓ Done. {len(points)} points in '{NEW_COLLECTION}'.")
    sample_path = Path("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/.lab/workspace/doc2query-samples.json")
    sample = []
    for r in new_records[:15]:
        sample.append({
            "citation_id": r["original_payload"].get("citation_id"),
            "questions": r["questions"],
            "augmented_preview": r["augmented_text"][:800],
        })
    sample_path.write_text(json.dumps(sample, indent=2))
    logger.info(f"  Samples: {sample_path}")


if __name__ == "__main__":
    main()
