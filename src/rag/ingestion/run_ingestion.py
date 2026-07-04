"""
End-to-End CCoP Ingestion Orchestrator

One-time batch script to parse, chunk, and index all CCoP documents.
Routes each document to its configured parser and chunker strategy.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List

from infrastructure.config.settings import Settings, get_settings
from rag.ingestion.chunkers.clause_aware_chunker import chunk_by_clauses
from rag.ingestion.chunkers.section_chunker import chunk_document
from rag.ingestion.models import ChunkerType, CcopChunk
from rag.ingestion.parsers.ccop_pdf_parser import CCOP_DOCUMENTS
from rag.ingestion.parsers.docling_parser import (
    DoclingParseResult,
    parse_all_ccop_documents_with_docling,
)

# Configure logging (standard Python logging, not structlog)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# CCoP 2.0 section-level TOC (5.1 through 5.17).
#
# Source: CCoP---Second-Edition_Revision-One.pdf, Table of Contents (page 4).
# Each entry is the X.Y prefix that must have at least one clause chunk in the index.
# Adjust this list if a future revision of the PDF adds or removes sections.
#
# CORRECTED (Phase 11, D-19): this list previously stopped at 5.12 (the
# page-4 TOC summary's granularity), silently under-checking real sections
# 5.13-5.17 that DO exist in the document body and DO have clause_inventory.json
# entries (883-entry fixture, the authoritative D-06/D-07 source) — a gate
# that only enumerated 5.1-5.12 could never catch a regression dropping
# 5.13-5.17 entirely. Verified against the live re-ingested corpus.
EXPECTED_CCOP_2_SECTIONS = [
    "5.1",
    "5.2",
    "5.3",
    "5.4",
    "5.5",
    "5.6",
    "5.7",
    "5.8",
    "5.9",
    "5.10",
    "5.11",
    "5.12",
    "5.13",
    "5.14",
    "5.15",
    "5.16",
    "5.17",
]


def _create_indexer(settings: Settings):
    """
    Create indexer adapter based on configuration.

    Selection logic:
    - If qdrant_url is set: create QdrantIndexerAdapter
    - Elif databricks_host is set: create DatabricksIndexerAdapter
    - Else: raise ValueError (no indexer configured)
    """
    if settings.qdrant_url:
        from qdrant_client import QdrantClient
        from rag.infrastructure.adapters.qdrant.embedding_service import (
            EmbeddingService,
        )
        from rag.infrastructure.adapters.qdrant.qdrant_indexer_adapter import (
            QdrantIndexerAdapter,
        )

        client = QdrantClient(url=settings.qdrant_url)
        embedding_service = EmbeddingService(
            dense_model_name=settings.qdrant_embedding_model,
            sparse_model_name=settings.qdrant_sparse_model,
        )
        logger.info(f"Using QdrantIndexerAdapter (collection: {settings.qdrant_collection_name})")
        return QdrantIndexerAdapter(
            client=client,
            collection_name=settings.qdrant_collection_name,
            embedding_service=embedding_service,
        )
    elif settings.databricks_host:
        from rag.infrastructure.adapters.databricks.databricks_indexer_adapter import (
            DatabricksIndexerAdapter,
        )

        logger.info("Using DatabricksIndexerAdapter")
        return DatabricksIndexerAdapter(settings=settings)
    else:
        raise ValueError(
            "No indexer configured. Set CCOP_QDRANT_URL or CCOP_DATABRICKS_HOST in .env.local"
        )


def _enrich_with_diagram_captions(
    parsed_docs: Dict[str, DoclingParseResult], settings: Settings
) -> None:
    """
    Enrich parsed documents with diagram captions from GLM-4V.

    Replaces <!-- image --> placeholders in markdown with vision model descriptions.
    Modifies DoclingParseResult.markdown in place.

    Args:
        parsed_docs: Dictionary mapping document name to DoclingParseResult
        settings: Application settings with ZhipuAI configuration
    """
    if not settings.diagram_captioning_enabled:
        logger.info("Diagram captioning disabled (CCOP_DIAGRAM_CAPTIONING_ENABLED=false)")
        return

    if not settings.zhipuai_api_key or settings.zhipuai_api_key == "your_zhipuai_api_key_here":
        logger.warning(
            "Diagram captioning enabled but no API key set. "
            "Diagrams will keep <!-- image --> placeholders."
        )
        return

    from infrastructure.external.zhipuai_client import ZhipuVisionClient
    from rag.ingestion.enrichers.diagram_captioner import caption_diagrams

    vision_client = ZhipuVisionClient(
        api_key=settings.zhipuai_api_key,
        base_url=settings.zhipuai_base_url,
        model=settings.zhipuai_model,
        timeout=settings.zhipuai_timeout,
        max_tokens=settings.zhipuai_max_tokens,
    )

    try:
        for doc_name, parse_result in parsed_docs.items():
            picture_count = len(getattr(parse_result.document, "pictures", []))
            if picture_count == 0:
                logger.info(f"  {doc_name}: 0 diagrams, skipping")
                continue

            logger.info(f"  {doc_name}: captioning {picture_count} diagrams...")
            parse_result.markdown = caption_diagrams(
                parse_result.markdown,
                parse_result.document,
                vision_client,
                settings.diagram_captioning_prompt,
            )
            logger.info(f"  {doc_name}: {picture_count} diagrams captioned")
    finally:
        vision_client.close()


def _chunk_documents(
    parsed_docs: Dict[str, DoclingParseResult], settings: Settings
) -> List[CcopChunk]:
    """
    Route each document to its configured chunker strategy.

    Args:
        parsed_docs: Dictionary mapping document name to DoclingParseResult
        settings: Application settings with chunking parameters

    Returns:
        Combined list of all chunks from all documents
    """
    doc_config_map = {doc.name: doc for doc in CCOP_DOCUMENTS}

    all_chunks = []

    for doc_name, parse_result in parsed_docs.items():
        doc_config = doc_config_map.get(doc_name)
        markdown = parse_result.markdown

        if doc_config is None:
            logger.warning(f"No config found for '{doc_name}', skipping")
            continue

        if doc_config.chunker_type == ChunkerType.CLAUSE_AWARE:
            chunks = chunk_by_clauses(
                markdown, doc_name, preamble_max_words=settings.preamble_max_words
            )
            logger.info(f"  {doc_name}: {len(chunks)} chunks (clause_aware)")
        else:
            chunks = chunk_document(
                markdown,
                doc_name,
                min_tokens=settings.section_chunk_min_tokens,
                max_tokens=settings.section_chunk_max_tokens,
            )
            logger.info(f"  {doc_name}: {len(chunks)} chunks (section_based)")

        # Mark RESPONSE-TO-FEEDBACK chunks as clarifications
        if doc_name == "CCoP Response to Feedback":
            for chunk in chunks:
                chunk.metadata.document_type = "clarification"

        all_chunks.extend(chunks)

    logger.info(f"Total chunks across all documents: {len(all_chunks)}")

    # Chunk size statistics
    token_counts = [len(c.text.split()) for c in all_chunks]
    if token_counts:
        logger.info(
            f"Chunk size stats: min={min(token_counts)}, "
            f"max={max(token_counts)}, "
            f"avg={sum(token_counts) // len(token_counts)}"
        )

    return all_chunks


def _verify_toc_coverage(chunks: List[CcopChunk]) -> None:
    """
    Assert that every expected CCoP 2.0 TOC section has at least one clause chunk.

    Fails loudly (RuntimeError) before the upload step so missing sections are
    caught at ingestion time, not silently at evaluation time (SC #5 requirement,
    bug #10 regression gate).

    Only applied to CCoP 2.0 document chunks. Other documents are not checked.
    Table chunks (type='table') are excluded from the observed section set because
    they inherit their enclosing clause's section — we want clause-level evidence.

    Args:
        chunks: All chunks produced by the chunking step

    Raises:
        RuntimeError: If any EXPECTED_CCOP_2_SECTIONS entry is absent from the index
    """
    from rag.ingestion.models import ChunkMetadata  # already imported at top, but guard

    observed_sections: set = {
        c.metadata.section
        for c in chunks
        if c.metadata.document_source == "CCoP 2.0"
        and c.metadata.type == "clause"
        and c.metadata.section not in ("preamble", "")
    }

    expected_set = set(EXPECTED_CCOP_2_SECTIONS)
    missing = expected_set - observed_sections

    logger.info(f"TOC sanity gate — observed sections: {sorted(observed_sections)}")

    if missing:
        logger.error(
            f"TOC sanity gate FAILED. Missing sections: {sorted(missing)}"
        )
        raise RuntimeError(
            f"TOC sanity gate failed: expected sections missing from index: {sorted(missing)}"
        )

    logger.info(
        f"TOC sanity gate PASSED — all {len(EXPECTED_CCOP_2_SECTIONS)} "
        "expected sections present"
    )


def run_ingestion(ccop_dir: str, settings: Settings, dry_run: bool = False) -> Dict:
    """
    Run end-to-end CCoP document ingestion pipeline.

    Pipeline steps:
    1. Parse all 8 CCoP documents with Docling Classic pipeline
    1.5. Enrich diagrams with GLM-4V captions (if enabled)
    2. Route each document to its configured chunker (clause_aware or section_based)
    3. Upload to vector store and create hybrid vector search index
    4. Verify with sample query

    Args:
        ccop_dir: Path to ccop-official directory containing PDFs
        settings: Application settings with vector store configuration
        dry_run: If True, skip vector store upload and just print statistics

    Returns:
        Summary dict with document_count, chunk_count, index_name, sample_query_results
    """
    logger.info("=" * 80)
    logger.info("CCoP Document Ingestion Pipeline")
    logger.info("=" * 80)

    # Step 1: Parse all CCoP documents
    logger.info("\n[Step 1/5] Parsing all CCoP documents with Docling...")
    logger.info(f"Source directory: {ccop_dir}")

    try:
        parsed_docs = parse_all_ccop_documents_with_docling(ccop_dir)
    except Exception as e:
        logger.error(f"Failed to parse documents: {e}")
        raise

    document_count = len(parsed_docs)
    logger.info(f"Parsed {document_count} documents")

    for i, doc_name in enumerate(parsed_docs.keys(), 1):
        logger.info(f"  {i}. {doc_name}")

    # Step 1.5: Enrich diagrams with captions
    logger.info("\n[Step 1.5/5] Diagram captioning...")
    _enrich_with_diagram_captions(parsed_docs, settings)

    # Step 2: Chunk all documents with per-document routing
    logger.info("\n[Step 2/5] Chunking documents with per-document strategy routing...")

    try:
        chunks = _chunk_documents(parsed_docs, settings)
    except Exception as e:
        logger.error(f"Failed to chunk documents: {e}")
        raise

    chunk_count = len(chunks)
    logger.info(f"Chunking complete: {chunk_count} chunks from {document_count} documents")

    # Step 2.5: TOC sanity gate — fail loudly before upload if sections are missing
    logger.info("\n[Step 2.5/5] TOC sanity gate...")
    try:
        _verify_toc_coverage(chunks)
    except RuntimeError:
        raise

    # Step 3: Log chunk statistics
    logger.info("\n[Step 3/5] Chunk statistics:")
    _log_chunk_statistics(chunks)

    # Step 4: Upload to vector store (unless dry-run)
    if dry_run:
        logger.info("\n[Step 4/5] Dry-run mode: Skipping vector store upload")
        logger.info("Dry-run complete")
        return {
            "document_count": document_count,
            "chunk_count": chunk_count,
            "index_name": None,
            "sample_query_results": None,
            "dry_run": True,
        }

    logger.info("\n[Step 4/5] Uploading to vector store...")
    logger.info(f"Uploading {chunk_count} chunks...")

    try:
        indexer = _create_indexer(settings)
        logger.info("Index creation in progress...")
        index_name = indexer.index_chunks(chunks)
    except Exception as e:
        logger.error(f"Failed to upload to vector store: {e}")
        raise

    logger.info(f"Indexing complete: {index_name}")

    # Step 5: Verify with sample query
    logger.info("\n[Step 5/5] Verifying with sample query...")
    sample_query = "What are the access control requirements for CII?"

    try:
        verification = indexer.verify_index(index_name, sample_query)
        result_count = verification["result_count"]
        logger.info(f"Verification query returned {result_count} results")

        if result_count > 0:
            logger.info("\nTop 3 results:")
            for i, result in enumerate(verification["results"], 1):
                logger.info(
                    f"  {i}. [{result.get('citation_id', 'N/A')}] {result.get('section', 'N/A')}"
                )
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        raise

    logger.info("\n" + "=" * 80)
    logger.info("Ingestion pipeline complete!")
    logger.info("=" * 80)

    return {
        "document_count": document_count,
        "chunk_count": chunk_count,
        "index_name": index_name,
        "sample_query_results": verification,
        "dry_run": False,
    }


def _log_chunk_statistics(chunks: List[CcopChunk]) -> None:
    """Log chunk statistics: per-document counts and size distribution."""
    # Per-document chunk counts
    doc_chunks = {}
    for chunk in chunks:
        doc_name = chunk.metadata.document_source
        doc_chunks[doc_name] = doc_chunks.get(doc_name, 0) + 1

    logger.info("\n  Per-document chunk counts:")
    for doc_name, count in sorted(doc_chunks.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"    {doc_name}: {count} chunks")

    # Chunk size distribution
    token_counts = [len(chunk.text.split()) for chunk in chunks]
    token_counts.sort()

    min_tokens = min(token_counts)
    max_tokens = max(token_counts)
    avg_tokens = sum(token_counts) // len(token_counts)
    median_tokens = token_counts[len(token_counts) // 2]

    logger.info("\n  Chunk size distribution (token counts):")
    logger.info(f"    Min: {min_tokens} tokens")
    logger.info(f"    Max: {max_tokens} tokens")
    logger.info(f"    Avg: {avg_tokens} tokens")
    logger.info(f"    Median: {median_tokens} tokens")

    # Size buckets
    buckets = {
        "< 300": len([t for t in token_counts if t < 300]),
        "300-500": len([t for t in token_counts if 300 <= t < 500]),
        "500-700": len([t for t in token_counts if 500 <= t < 700]),
        "700-900": len([t for t in token_counts if 700 <= t < 900]),
        "900+": len([t for t in token_counts if t >= 900]),
    }

    logger.info("\n  Size buckets:")
    for bucket, count in buckets.items():
        pct = (count / len(token_counts)) * 100
        logger.info(f"    {bucket}: {count} chunks ({pct:.1f}%)")


def main() -> None:
    """CLI entry point for ingestion script."""
    parser = argparse.ArgumentParser(
        description="Ingest CCoP documents into vector store (Qdrant or Databricks)"
    )
    parser.add_argument(
        "--ccop-dir",
        type=str,
        default="../ccop-official",
        help="Path to ccop-official directory (default: ../ccop-official)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and chunk only, skip vector store upload",
    )

    args = parser.parse_args()

    # Resolve ccop_dir to absolute path
    ccop_dir = Path(args.ccop_dir).resolve()

    if not ccop_dir.exists():
        logger.error(f"CCoP directory not found: {ccop_dir}")
        logger.error("Please specify correct path with --ccop-dir")
        sys.exit(1)

    logger.info(f"Using CCoP directory: {ccop_dir}")

    # Load settings
    settings = get_settings()

    # Check vector store configuration if not dry-run
    if not args.dry_run:
        has_qdrant = bool(settings.qdrant_url)
        has_databricks = bool(settings.databricks_host)

        if has_qdrant:
            # Validate Qdrant configuration
            missing = []
            if not settings.qdrant_collection_name:
                missing.append("CCOP_QDRANT_COLLECTION_NAME")
            if not settings.qdrant_embedding_model:
                missing.append("CCOP_QDRANT_EMBEDDING_MODEL")
            if not settings.qdrant_sparse_model:
                missing.append("CCOP_QDRANT_SPARSE_MODEL")

            if missing:
                logger.error("Missing required Qdrant configuration:")
                for var in missing:
                    logger.error(f"  - {var}")
                logger.error("\nPlease configure these in src/config/.env.local")
                logger.error("Or use --dry-run to skip vector store upload")
                sys.exit(1)

        elif has_databricks:
            # Validate Databricks configuration
            missing = []
            if not settings.databricks_token:
                missing.append("CCOP_DATABRICKS_TOKEN")
            if not settings.databricks_catalog:
                missing.append("CCOP_DATABRICKS_CATALOG")
            if not settings.databricks_schema:
                missing.append("CCOP_DATABRICKS_SCHEMA")
            if not settings.databricks_vector_search_endpoint:
                missing.append("CCOP_DATABRICKS_VECTOR_SEARCH_ENDPOINT")
            if not settings.databricks_embedding_endpoint:
                missing.append("CCOP_DATABRICKS_EMBEDDING_ENDPOINT")
            if not settings.databricks_warehouse_id:
                missing.append("CCOP_DATABRICKS_WAREHOUSE_ID")

            if missing:
                logger.error("Missing required Databricks configuration:")
                for var in missing:
                    logger.error(f"  - {var}")
                logger.error("\nPlease configure these in src/config/.env.local")
                logger.error("Or use --dry-run to skip vector store upload")
                sys.exit(1)

        else:
            logger.error("No vector store configured.")
            logger.error("Please configure either Qdrant or Databricks:")
            logger.error("\nFor Qdrant:")
            logger.error("  - CCOP_QDRANT_URL")
            logger.error("  - CCOP_QDRANT_COLLECTION_NAME")
            logger.error("  - CCOP_QDRANT_EMBEDDING_MODEL")
            logger.error("  - CCOP_QDRANT_SPARSE_MODEL")
            logger.error("\nFor Databricks:")
            logger.error("  - CCOP_DATABRICKS_HOST")
            logger.error("  - CCOP_DATABRICKS_TOKEN")
            logger.error("  - CCOP_DATABRICKS_CATALOG")
            logger.error("  - CCOP_DATABRICKS_SCHEMA")
            logger.error("  - CCOP_DATABRICKS_VECTOR_SEARCH_ENDPOINT")
            logger.error("  - CCOP_DATABRICKS_EMBEDDING_ENDPOINT")
            logger.error("  - CCOP_DATABRICKS_WAREHOUSE_ID")
            logger.error("\nOr use --dry-run to skip vector store upload")
            sys.exit(1)

    # Run ingestion
    try:
        result = run_ingestion(str(ccop_dir), settings, dry_run=args.dry_run)

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("Ingestion Summary")
        logger.info("=" * 80)
        logger.info(f"Documents parsed: {result['document_count']}")
        logger.info(f"Chunks created: {result['chunk_count']}")
        if not result["dry_run"]:
            logger.info(f"Index name: {result['index_name']}")
            logger.info(
                f"Sample query results: {result['sample_query_results']['result_count']}"
            )
        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.info("\n\nIngestion interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n\nIngestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
