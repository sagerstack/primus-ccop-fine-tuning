"""
Unit tests for the GraphRAG corpus source loader (D-04/D-05).

Mocks the Docling parser so these tests never touch the real CCoP PDFs.
"""
from unittest.mock import MagicMock, patch

from rag.graph.build.corpus_source import load_ccop_corpus_texts
from rag.ingestion.parsers.ccop_pdf_parser import CCOP_DOCUMENTS
from rag.ingestion.parsers.docling_parser import DoclingParseResult


def _fake_parsed_docs() -> dict:
    """Two synthetic Docling parse results — one long, one short."""
    return {
        "CCoP 2.0": DoclingParseResult(markdown="X" * 6000, document=object()),
        "CCoP Response to Feedback": DoclingParseResult(markdown="Y" * 100, document=object()),
    }


class TestLoadCcopCorpusTexts:
    """load_ccop_corpus_texts reuses the Docling parser, no clause chunking."""

    @patch("rag.graph.build.corpus_source.parse_all_ccop_documents_with_docling")
    def test_returns_non_empty_mapping_matching_document_names(self, mock_parse):
        mock_parse.return_value = _fake_parsed_docs()
        settings = MagicMock()

        texts = load_ccop_corpus_texts(settings)

        assert texts
        expected_names = {doc.name for doc in CCOP_DOCUMENTS}
        assert set(texts.keys()) <= expected_names
        assert "CCoP 2.0" in texts

    @patch("rag.graph.build.corpus_source.parse_all_ccop_documents_with_docling")
    def test_returns_full_markdown_not_clause_chunked(self, mock_parse):
        mock_parse.return_value = _fake_parsed_docs()
        settings = MagicMock()

        texts = load_ccop_corpus_texts(settings)

        # D-05: full prose text, well above a single-clause length — no
        # clause-level chunker has been applied.
        assert len(texts["CCoP 2.0"]) > 5000
        assert texts["CCoP 2.0"] == "X" * 6000

    @patch("rag.graph.build.corpus_source.parse_all_ccop_documents_with_docling")
    def test_calls_docling_parser_with_ccop_dir(self, mock_parse):
        mock_parse.return_value = _fake_parsed_docs()
        settings = MagicMock()

        load_ccop_corpus_texts(settings, ccop_dir="/custom/ccop-dir")

        mock_parse.assert_called_once_with("/custom/ccop-dir")

    @patch("rag.graph.build.corpus_source.parse_all_ccop_documents_with_docling")
    def test_default_ccop_dir_used_when_not_specified(self, mock_parse):
        mock_parse.return_value = _fake_parsed_docs()
        settings = MagicMock()

        load_ccop_corpus_texts(settings)

        mock_parse.assert_called_once()
        called_dir = mock_parse.call_args[0][0]
        assert "ccop-official" in called_dir
