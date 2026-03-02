"""
CCoP PDF Parser using Docling

Parses CCoP 2.0 regulatory documents using Docling DocumentConverter with structure preservation.
"""

import logging
from pathlib import Path
from typing import Dict

from docling.document_converter import DocumentConverter

from rag.ingestion.parsers.ccop_pdf_parser import CCOP_DOCUMENTS

logger = logging.getLogger(__name__)


def parse_ccop_pdf_with_docling(pdf_path: str, document_name: str) -> str:
    """
    Parse a CCoP PDF document to markdown using Docling.

    Uses Docling DocumentConverter with classic pipeline (not VLM) to extract
    markdown while preserving sections, tables, and document hierarchy.

    Args:
        pdf_path: Path to PDF file
        document_name: Human-readable document name

    Returns:
        Markdown text with preserved structure

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF parsing fails
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info(f"Parsing PDF with Docling: {document_name} from {pdf_path}")

    try:
        # Initialize DocumentConverter with default classic pipeline
        converter = DocumentConverter()

        # Convert PDF to DoclingDocument
        result = converter.convert(str(pdf_path))

        # Export to markdown
        md_text = result.document.export_to_markdown()

        # Log parsing statistics
        page_count = getattr(result.document, "page_count", "unknown")
        logger.info(
            f"Parsed {document_name}: {page_count} pages, {len(md_text)} characters"
        )

        return md_text

    except Exception as e:
        logger.error(f"Failed to parse {document_name}: {e}")
        raise


def parse_all_ccop_documents_with_docling(ccop_dir: str) -> Dict[str, str]:
    """
    Parse all 8 CCoP documents using Docling.

    Args:
        ccop_dir: Base directory containing CCoP documents

    Returns:
        Dictionary mapping document name to markdown text

    Raises:
        FileNotFoundError: If ccop_dir doesn't exist or documents are missing
    """
    base_path = Path(ccop_dir)
    if not base_path.exists():
        raise FileNotFoundError(f"CCoP directory not found: {ccop_dir}")

    logger.info(f"Parsing all CCoP documents with Docling from {ccop_dir}")

    parsed_docs = {}

    for doc in CCOP_DOCUMENTS:
        pdf_path = str(base_path / doc.path)
        try:
            markdown = parse_ccop_pdf_with_docling(pdf_path, doc.name)
            parsed_docs[doc.name] = markdown
        except Exception as e:
            logger.error(f"Failed to parse {doc.name}: {e}")
            # Continue with other documents even if one fails
            continue

    logger.info(
        f"Successfully parsed {len(parsed_docs)}/{len(CCOP_DOCUMENTS)} documents"
    )

    return parsed_docs
