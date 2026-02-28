"""
End-to-End CCoP Ingestion Orchestrator

One-time batch script to parse, chunk, and index all CCoP documents.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List

from infrastructure.config.settings import Settings, get_settings
from rag.ingestion.chunkers.section_chunker import chunk_all_documents
from rag.ingestion.models import CcopChunk
from rag.ingestion.parsers.ccop_pdf_parser import parse_all_ccop_documents

# Configure logging (standard Python logging, not structlog)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


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


def run_ingestion(ccop_dir: str, settings: Settings, dry_run: bool = False) -> Dict:
    """
    Run end-to-end CCoP document ingestion pipeline.

    Pipeline steps:
    1. Parse all 8 CCoP documents with PyMuPDF4LLM
    2. Chunk documents with section-level semantic chunking
    3. Upload to Databricks Delta table and create hybrid vector search index
    4. Verify with sample query

    Args:
        ccop_dir: Path to ccop-official directory containing PDFs
        settings: Application settings with Databricks configuration
        dry_run: If True, skip Databricks upload and just print statistics

    Returns:
        Summary dict with document_count, chunk_count, index_name, sample_query_results
    """
    logger.info("=" * 80)
    logger.info("CCoP Document Ingestion Pipeline")
    logger.info("=" * 80)

    # Step 1: Parse all CCoP documents
    logger.info("\n[Step 1/4] Parsing all CCoP documents...")
    logger.info(f"Source directory: {ccop_dir}")

    try:
        parsed_docs = parse_all_ccop_documents(ccop_dir)
    except Exception as e:
        logger.error(f"Failed to parse documents: {e}")
        raise

    document_count = len(parsed_docs)
    logger.info(f"✓ Parsed {document_count} documents")

    for i, doc_name in enumerate(parsed_docs.keys(), 1):
        logger.info(f"  {i}. {doc_name}")

    # Step 2: Chunk all documents
    logger.info("\n[Step 2/4] Chunking documents with section-level semantic splitting...")

    try:
        chunks = chunk_all_documents(parsed_docs, ccop_dir)
    except Exception as e:
        logger.error(f"Failed to chunk documents: {e}")
        raise

    chunk_count = len(chunks)
    logger.info(f"✓ Chunking complete: {chunk_count} chunks from {document_count} documents")

    # Step 3: Log chunk statistics
    logger.info("\n[Step 3/4] Chunk statistics:")
    _log_chunk_statistics(chunks)

    # Step 4: Upload to vector store (unless dry-run)
    if dry_run:
        logger.info("\n[Step 4/4] Dry-run mode: Skipping vector store upload")
        logger.info("✓ Dry-run complete")
        return {
            "document_count": document_count,
            "chunk_count": chunk_count,
            "index_name": None,
            "sample_query_results": None,
            "dry_run": True,
        }

    logger.info("\n[Step 4/4] Uploading to vector store...")
    logger.info(f"Uploading {chunk_count} chunks...")

    try:
        indexer = _create_indexer(settings)
        logger.info("Index creation in progress... (this may take 5-10 minutes)")
        index_name = indexer.index_chunks(chunks)
    except Exception as e:
        logger.error(f"Failed to upload to vector store: {e}")
        raise

    logger.info(f"✓ Indexing complete: {index_name}")

    # Step 5: Verify with sample query
    logger.info("\n[Step 5/5] Verifying with sample query...")
    sample_query = "What are the access control requirements for CII?"

    try:
        verification = indexer.verify_index(index_name, sample_query)
        result_count = verification["result_count"]
        logger.info(f"✓ Verification query returned {result_count} results")

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
    logger.info("✓ Ingestion pipeline complete!")
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
