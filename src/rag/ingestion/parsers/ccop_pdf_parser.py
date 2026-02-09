"""
CCoP PDF Parser

Parses CCoP 2.0 regulatory documents using PyMuPDF4LLM with structure preservation.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import pymupdf4llm

logger = logging.getLogger(__name__)


@dataclass
class CcopDocument:
    """Configuration for a CCoP document."""

    name: str
    path: str


# Document configuration - all 8 CCoP documents
CCOP_DOCUMENTS = [
    CcopDocument(name="CCoP 2.0", path="CCoP---Second-Edition_Revision-One.pdf"),
    CcopDocument(
        name="CCoP Response to Feedback",
        path="RESPONSE-TO-FEEDBACK.pdf",
    ),
    CcopDocument(
        name="Auditing Guidelines",
        path="supplementary/Guidelines_for_Auditing_Critical_Information_Infrastructure.pdf",
    ),
    CcopDocument(
        name="Threat Modelling Guide",
        path="supplementary/Guide-to-Cyber-Threat-Modelling.pdf",
    ),
    CcopDocument(
        name="Risk Assessment Guide",
        path="supplementary/Guide-to-Conducting-Cybersecurity-Risk-Assessment-for-CII.pdf",
    ),
    CcopDocument(
        name="Security By Design",
        path="supplementary/Security_By_Design_Framework.pdf",
    ),
    CcopDocument(
        name="Ensign CCoP Guide",
        path="references/Ensign's_Cybersecurity_Guide_on_CCoP_2_0_for_CII_Sep_2022.pdf",
    ),
    CcopDocument(
        name="Cybersecurity Act 2018",
        path="references/Cybersecurity Act 2018.pdf",
    ),
]


def parse_ccop_pdf(pdf_path: str, document_name: str) -> str:
    """
    Parse a CCoP PDF document to markdown with structure preservation.

    Uses PyMuPDF4LLM to extract markdown while preserving sections, tables,
    and document hierarchy.

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

    logger.info(f"Parsing PDF: {document_name} from {pdf_path}")

    try:
        # Extract markdown with PyMuPDF4LLM
        md_text = pymupdf4llm.to_markdown(
            pdf_path,
            page_chunks=False,  # Full document, not per-page chunks
            write_images=False,  # Don't extract images
        )

        # Get page count for logging
        import pymupdf

        doc = pymupdf.open(pdf_path)
        page_count = len(doc)
        doc.close()

        logger.info(
            f"Parsed {document_name}: {page_count} pages, {len(md_text)} characters"
        )

        return md_text

    except Exception as e:
        logger.error(f"Failed to parse {document_name}: {e}")
        raise


def parse_all_ccop_documents(ccop_dir: str) -> Dict[str, str]:
    """
    Parse all 8 CCoP documents.

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

    logger.info(f"Parsing all CCoP documents from {ccop_dir}")

    parsed_docs = {}

    for doc in CCOP_DOCUMENTS:
        pdf_path = str(base_path / doc.path)
        try:
            markdown = parse_ccop_pdf(pdf_path, doc.name)
            parsed_docs[doc.name] = markdown
        except Exception as e:
            logger.error(f"Failed to parse {doc.name}: {e}")
            # Continue with other documents even if one fails
            continue

    logger.info(f"Successfully parsed {len(parsed_docs)}/{len(CCOP_DOCUMENTS)} documents")

    return parsed_docs
