"""
CCoP Corpus Source for GraphRAG Build

Reuses the exact Docling-parsed CCoP markdown that the hybrid Qdrant index
consumes, holding the input text constant across both retrieval systems
(D-04). This is deliberately the same parser output, unmodified — no clause
chunker is applied, because isolated clause fragments starve prose-based
entity/relationship extraction (D-05). Chunking for the knowledge graph is
left to neo4j-graphrag's own default text splitter (D-08: pure defaults).
"""

import logging
from typing import Dict

from infrastructure.config.settings import Settings
from rag.ingestion.parsers.ccop_pdf_parser import CCOP_DOCUMENTS
from rag.ingestion.parsers.docling_parser import parse_all_ccop_documents_with_docling

logger = logging.getLogger(__name__)

# Mirrors run_ingestion.py's --ccop-dir default convention (relative to src/).
DEFAULT_CCOP_DIR = "../ccop-official"


def load_ccop_corpus_texts(
    settings: Settings, ccop_dir: str = DEFAULT_CCOP_DIR
) -> Dict[str, str]:
    """
    Load the full Docling-parsed markdown for every CCoP document.

    Args:
        settings: Application settings. Accepted for interface symmetry with
            other corpus/index loaders in this codebase; not currently
            consulted for the CCoP directory path (no such setting exists
            yet — see ccop_dir parameter instead).
        ccop_dir: Base directory containing the CCoP PDFs.

    Returns:
        Dict mapping document name (matches CCOP_DOCUMENTS[].name) to the
        full Docling markdown text for that document — the identical text
        the hybrid stack's clause chunker consumes, held constant here.
    """
    del settings  # unused today; kept for interface symmetry (see docstring)

    parsed_docs = parse_all_ccop_documents_with_docling(ccop_dir)
    texts = {doc_name: result.markdown for doc_name, result in parsed_docs.items()}

    expected_names = {doc.name for doc in CCOP_DOCUMENTS}
    missing = expected_names - set(texts.keys())
    if missing:
        logger.warning(f"CCoP documents missing from corpus load: {sorted(missing)}")

    return texts
