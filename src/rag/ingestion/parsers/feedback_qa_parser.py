"""
RESPONSE-TO-FEEDBACK Q&A Parser

Extracts question-answer pairs from the CCoP RESPONSE-TO-FEEDBACK.pdf document.
"""

import logging
import re
from typing import List

from rag.ingestion.models import ChunkMetadata, QAPair

logger = logging.getLogger(__name__)


def parse_feedback_qa(markdown_text: str) -> List[QAPair]:
    """
    Parse RESPONSE-TO-FEEDBACK markdown into Q&A pairs.

    The RESPONSE-TO-FEEDBACK document contains numbered questions with responses.
    This parser extracts each Q&A pair and attempts to link it to CCoP clauses
    mentioned in the response.

    Args:
        markdown_text: Markdown output from RESPONSE-TO-FEEDBACK.pdf

    Returns:
        List of QAPair objects with linked clauses

    Note:
        - Questions are typically numbered (e.g., "1.", "2.", etc.)
        - Responses follow the question
        - Clause references are extracted via regex (e.g., "5.2.1")
        - If no clause found, linked_clause is empty string
    """
    qa_pairs = []

    # Split by question numbers (simplified pattern - may need refinement based on actual format)
    # Pattern: Look for numbered questions like "1. Question text" or "Question 1:"
    question_pattern = r"(?:^|\n)(?:\d+\.|Question \d+:)\s*(.+?)(?=(?:\d+\.|Question \d+:|\Z))"

    # For now, use a simpler approach: split by double newlines and look for Q&A structure
    # This is a heuristic that may need adjustment based on actual document format

    sections = markdown_text.split("\n\n")

    current_question = None
    current_answer = ""

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Check if this looks like a question (starts with number or "Question")
        if re.match(r"^\d+\.|^Question \d+:", section):
            # Save previous Q&A pair if exists
            if current_question:
                qa_pairs.append(
                    _create_qa_pair(current_question, current_answer)
                )

            # Start new question
            current_question = section
            current_answer = ""
        else:
            # Accumulate answer text
            current_answer += "\n\n" + section if current_answer else section

    # Don't forget the last Q&A pair
    if current_question:
        qa_pairs.append(_create_qa_pair(current_question, current_answer))

    logger.info(f"Extracted {len(qa_pairs)} Q&A pairs from RESPONSE-TO-FEEDBACK")

    return qa_pairs


def _create_qa_pair(question: str, answer: str) -> QAPair:
    """
    Create a QAPair object from question and answer text.

    Args:
        question: Question text
        answer: Answer text

    Returns:
        QAPair with extracted clause reference
    """
    # Extract clause number from answer (e.g., "5.2.1", "10.3.2")
    # Look in first 500 chars of answer for clause references
    clause_match = re.search(r"\b(\d+\.\d+\.?\d*)\b", answer[:500])
    linked_clause = clause_match.group(1) if clause_match else ""

    if not linked_clause:
        logger.warning(f"No clause reference found for Q&A: {question[:100]}...")

    metadata = ChunkMetadata(
        document_source="CCoP Response to Feedback",
        section="Q&A",
        subsection="",
        clause=linked_clause,
        citation_id=f"CCoP-Feedback.{linked_clause}" if linked_clause else "CCoP-Feedback",
        document_type="clarification",
    )

    return QAPair(
        question=question.strip(),
        answer=answer.strip(),
        linked_clause=linked_clause,
        metadata=metadata,
    )
