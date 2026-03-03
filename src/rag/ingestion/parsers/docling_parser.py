"""
CCoP PDF Parser using Docling

Parses CCoP 2.0 regulatory documents using Docling DocumentConverter (Classic pipeline)
with picture image extraction for downstream diagram captioning.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from rag.ingestion.parsers.ccop_pdf_parser import CCOP_DOCUMENTS

logger = logging.getLogger(__name__)


@dataclass
class DoclingParseResult:
    """Result from Docling PDF parsing, carrying both markdown and the raw document."""

    markdown: str
    document: object  # DoclingDocument — typed as object to avoid heavy import at module level


def _create_converter() -> DocumentConverter:
    """
    Build a Docling DocumentConverter using the Classic pipeline.

    Enables picture image extraction so downstream enrichers can access
    diagram images via PictureItem.get_image(doc).

    Returns:
        Configured DocumentConverter instance
    """
    pipeline_options = PdfPipelineOptions(generate_picture_images=True)

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
            )
        }
    )


def parse_ccop_pdf_with_docling(
    pdf_path: str,
    document_name: str,
    converter: DocumentConverter | None = None,
) -> DoclingParseResult:
    """
    Parse a CCoP PDF document to markdown using Docling.

    Args:
        pdf_path: Path to PDF file
        document_name: Human-readable document name
        converter: Pre-built converter (reused across documents for efficiency)

    Returns:
        DoclingParseResult with markdown text and the raw DoclingDocument

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF parsing fails
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info(f"Parsing PDF with Docling (classic): {document_name} from {pdf_path}")

    try:
        if converter is None:
            converter = _create_converter()

        start_time = time.time()
        result = converter.convert(str(pdf_path))
        elapsed = time.time() - start_time

        md_text = result.document.export_to_markdown()
        picture_count = len(result.document.pictures)

        page_count = getattr(result.document, "page_count", "unknown")
        logger.info(
            f"Parsed {document_name}: {page_count} pages, "
            f"{len(md_text)} characters, {picture_count} pictures, {elapsed:.1f}s"
        )

        return DoclingParseResult(markdown=md_text, document=result.document)

    except Exception as e:
        logger.error(f"Failed to parse {document_name}: {e}")
        raise


def parse_all_ccop_documents_with_docling(ccop_dir: str) -> Dict[str, DoclingParseResult]:
    """
    Parse all 8 CCoP documents using Docling Classic pipeline.

    Reuses a single converter instance across all documents for efficiency.

    Args:
        ccop_dir: Base directory containing CCoP documents

    Returns:
        Dictionary mapping document name to DoclingParseResult

    Raises:
        FileNotFoundError: If ccop_dir doesn't exist or documents are missing
    """
    base_path = Path(ccop_dir)
    if not base_path.exists():
        raise FileNotFoundError(f"CCoP directory not found: {ccop_dir}")

    logger.info(f"Parsing all CCoP documents with Docling (classic) from {ccop_dir}")
    logger.info(f"  {len(CCOP_DOCUMENTS)} documents to parse")

    converter = _create_converter()
    parsed_docs: Dict[str, DoclingParseResult] = {}

    for doc in CCOP_DOCUMENTS:
        pdf_path = str(base_path / doc.path)
        try:
            parse_result = parse_ccop_pdf_with_docling(
                pdf_path, doc.name, converter=converter
            )
            parsed_docs[doc.name] = parse_result
        except Exception as e:
            logger.error(f"Failed to parse {doc.name}: {e}")
            continue

    logger.info(
        f"Successfully parsed {len(parsed_docs)}/{len(CCOP_DOCUMENTS)} documents"
    )

    return parsed_docs
