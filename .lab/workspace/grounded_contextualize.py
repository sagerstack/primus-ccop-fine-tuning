#!/usr/bin/env python3
"""
Grounded contextualization via claude CLI subprocess.

For each chunk:
  1. Build a grounding bundle: chunk text + parent section preamble + sibling clauses
  2. Pass the bundle to `claude -p "..."` as PROVIDED TEXT (no hallucination tolerated)
  3. Allow Read access to the source PDF for additional grounding if Claude wants
  4. Capture the 1-2 sentence context line
  5. Build augmented_text = breadcrumb + grounded_context + original
  6. Re-encode with BGE-large
  7. Write to new collection ccop_clauses_grounded

Cost: free (Claude Code subscription); slow (~10-20 sec per call × 495 = ~2-3 hrs sequential).
Parallelize via subprocess.Popen pool with concurrency limit.
"""
from __future__ import annotations
import json
import logging
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

SRC = Path("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/src")
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

NEW_COLLECTION = "ccop_clauses_grounded"
SOURCE_COLLECTION = "ccop_clauses_contextual"
BASE = "/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc"
CHECKPOINT = f"{BASE}/.lab/workspace/grounded-contexts.json"
SAMPLES = f"{BASE}/.lab/workspace/grounded-samples.json"

# Source-doc → official PDF
DOC_PDF = {
    "CCoP 2.0": "ccop-official/CCoP---Second-Edition_Revision-One.pdf",
    "CCoP Response to Feedback": "ccop-official/RESPONSE-TO-FEEDBACK.pdf",
    "Cybersecurity Act 2018": "ccop-official/references/Cybersecurity Act 2018.pdf",
    "Auditing Guidelines": "ccop-official/supplementary/Guidelines_for_Auditing_Critical_Information_Infrastructure.pdf",
    "Risk Assessment Guide": "ccop-official/supplementary/Guide-to-Conducting-Cybersecurity-Risk-Assessment-for-CII.pdf",
    "Threat Modelling Guide": "ccop-official/supplementary/Guide-to-Cyber-Threat-Modelling.pdf",
    "Security By Design": "ccop-official/supplementary/Security_By_Design_Framework.pdf",
}

PROMPT_TEMPLATE = """You are writing a grounded retrieval context for a regulatory document chunk. Your context will be embedded by a search system; queries will match against it.

GROUNDING CONSTRAINTS — non-negotiable:
1. You may ONLY use information present in the PROVIDED TEXT below or in the source PDF at the SOURCE PATH.
2. Do NOT invent acronym expansions. CIIO = Critical Information Infrastructure Owner (NEVER Chief Information and Innovation Officer or similar).
3. Do NOT invent clause references, organisation names, or regulatory roles.
4. If unsure of an expansion or fact, omit it.

YOUR TASK:
Write a 1-2 sentence context describing this chunk's role in the parent document, using vocabulary a practitioner might search with.
Include 2-3 likely synonyms or query terms a regulatory analyst would type when searching for this content.

DOCUMENT: {document_source}
SOURCE PATH (for verification if needed): {pdf_path}
SECTION PATH: {parent_path}

PROVIDED TEXT (this is the chunk's authoritative content; ground your context here):
\"\"\"
{chunk_text}
\"\"\"

NEIGHBOURING CONTEXT (sibling clauses in the same section, for context):
\"\"\"
{neighbours}
\"\"\"

Output ONLY the 1-2 sentence context. No preamble. No quotation marks. No "Context:" prefix."""


def call_claude(prompt: str, timeout: int = 120) -> str:
    """Invoke claude CLI in non-interactive mode with Read access to source PDFs."""
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt, "--allowedTools", "Read", "Grep"],
            capture_output=True, text=True, timeout=timeout,
            cwd=BASE,
        )
        if proc.returncode != 0:
            return f"__ERROR__ {proc.stderr.strip()[:200]}"
        return proc.stdout.strip()
    except subprocess.TimeoutExpired:
        return "__ERROR__ timeout"
    except Exception as e:
        return f"__ERROR__ {e}"


def main():
    from infrastructure.config.container import get_container

    container = get_container()
    vs = container.vector_store()
    client = vs.client

    logger.info(f"Scrolling source: {SOURCE_COLLECTION}")
    chunks = []
    offset = None
    while True:
        pts, next_off = client.scroll(SOURCE_COLLECTION, limit=300, offset=offset, with_payload=True, with_vectors=False)
        chunks.extend(pts)
        if next_off is None: break
        offset = next_off
    logger.info(f"  → {len(chunks)} chunks")

    # Group by parent_path so we can build neighbours
    by_parent: Dict[str, List] = {}
    for ch in chunks:
        p = ch.payload or {}
        pp = p.get("parent_path") or p.get("section") or p.get("citation_id") or ""
        # Key by everything-up-to-leaf
        parts = pp.split(" > ")
        parent_key = " > ".join(parts[:-1]) if len(parts) > 1 else pp
        by_parent.setdefault(parent_key, []).append(ch)

    # Load checkpoint if exists
    contexts: Dict[str, str] = {}
    if os.path.exists(CHECKPOINT):
        contexts = json.load(open(CHECKPOINT))
        logger.info(f"Loaded {len(contexts)} cached contexts from checkpoint")

    todo = [ch for ch in chunks if str(ch.id) not in contexts]
    logger.info(f"Remaining: {len(todo)} chunks to contextualize")

    def process_one(ch):
        p = ch.payload or {}
        cid = p.get("citation_id", str(ch.id))
        doc = p.get("document_source", "")
        pdf = DOC_PDF.get(doc, "")
        pp = p.get("parent_path", cid)
        original_text = (p.get("original_text") or p.get("text") or "")[:1500]

        # Build neighbours (siblings in same section, excluding self)
        parts = pp.split(" > ")
        parent_key = " > ".join(parts[:-1]) if len(parts) > 1 else pp
        siblings = by_parent.get(parent_key, [])
        neigh_texts = []
        for s in siblings[:5]:
            if s.id == ch.id: continue
            sp = s.payload or {}
            stxt = (sp.get("original_text") or sp.get("text") or "")[:300]
            neigh_texts.append(f"[{sp.get('citation_id')}] {stxt}")
        neighbours = "\n\n".join(neigh_texts) if neigh_texts else "(none)"

        prompt = PROMPT_TEMPLATE.format(
            document_source=doc,
            pdf_path=pdf,
            parent_path=pp,
            chunk_text=original_text,
            neighbours=neighbours,
        )
        ctx = call_claude(prompt)
        return str(ch.id), cid, ctx

    # Run in parallel (limited concurrency)
    t0 = time.time()
    n_done = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(process_one, ch): ch for ch in todo}
        for fut in as_completed(futures):
            try:
                pid, cid, ctx = fut.result()
                contexts[pid] = ctx
            except Exception as e:
                logger.warning(f"future failed: {e}")
            n_done += 1
            if n_done % 25 == 0:
                logger.info(f"  contexts: {n_done}/{len(todo)}  ({time.time()-t0:.0f}s)")
                # Checkpoint
                json.dump(contexts, open(CHECKPOINT, 'w'), indent=2)
    logger.info(f"  ✓ {len(contexts)} total contexts in {time.time()-t0:.1f}s")
    json.dump(contexts, open(CHECKPOINT, 'w'), indent=2)

    # Filter errors
    err_count = sum(1 for v in contexts.values() if v.startswith("__ERROR__"))
    if err_count > 0:
        logger.warning(f"  ⚠ {err_count} contexts had errors (will use empty context for those)")

    # Build augmented text
    from qdrant_client.models import (
        Distance, VectorParams, SparseVectorParams, SparseVector, PointStruct, Modifier
    )
    embed = vs.embedding_service

    new_records = []
    samples_to_save = []
    for ch in chunks:
        p = ch.payload or {}
        cid = p.get("citation_id", "")
        breadcrumb = p.get("breadcrumb", "")
        ctx = contexts.get(str(ch.id), "")
        if ctx.startswith("__ERROR__"):
            ctx = ""
        original = p.get("original_text") or p.get("text", "")
        ctx_block = f"[Context: {ctx}]\n\n" if ctx else ""
        bc_block = f"{breadcrumb}\n\n" if breadcrumb else ""
        augmented_text = bc_block + ctx_block + original
        new_records.append({
            "id": ch.id,
            "augmented_text": augmented_text,
            "context_line": ctx,
            "original_payload": p,
        })
        if len(samples_to_save) < 20:
            samples_to_save.append({
                "citation_id": cid,
                "breadcrumb": breadcrumb,
                "context": ctx,
                "original_preview": original[:200],
            })

    json.dump(samples_to_save, open(SAMPLES, "w"), indent=2)
    logger.info(f"  Samples: {SAMPLES}")

    # Re-encode and write to new collection
    logger.info("Re-encoding via BGE-large + Qdrant/bm25...")
    texts = [r["augmented_text"] for r in new_records]
    t1 = time.time()
    dense_vecs = embed.embed_documents(texts)
    logger.info(f"  dense done in {time.time()-t1:.1f}s")
    t2 = time.time()
    sparse_vecs = embed.embed_sparse_batch(texts)
    logger.info(f"  sparse done in {time.time()-t2:.1f}s")

    if client.collection_exists(NEW_COLLECTION):
        client.delete_collection(NEW_COLLECTION)
    client.create_collection(
        collection_name=NEW_COLLECTION,
        vectors_config={"dense": VectorParams(size=len(dense_vecs[0]), distance=Distance.COSINE)},
        sparse_vectors_config={"sparse": SparseVectorParams(modifier=Modifier.IDF)},
    )

    points = []
    for i, r in enumerate(new_records):
        new_payload = dict(r["original_payload"])
        new_payload["text"] = r["augmented_text"]
        new_payload["context_line_grounded"] = r["context_line"]
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


if __name__ == "__main__":
    main()
