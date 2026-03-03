"""
LLM Context Assembly

Shared utility to assemble retrieved documents into the context string
format expected by the generation prompt.
"""

from typing import List

from langchain_core.documents import Document


def assemble_llm_context(documents: List[Document]) -> str:
    """
    Assemble retrieved documents into the formatted context string for LLM generation.

    Each document is formatted as:
        [Source: {source}, {section} <c>{citation_id}</c>]
        {document text}

    Documents are joined with '---' separators.

    Args:
        documents: List of LangChain Documents with metadata

    Returns:
        Formatted context string ready for the generation prompt
    """
    context_parts = []
    for doc in documents:
        citation_id = doc.metadata.get("citation_id", "unknown")
        document_source = doc.metadata.get("document_source", "unknown")
        section = doc.metadata.get("section", "")

        context_parts.append(
            f"[Source: {document_source}, {section} <c>{citation_id}</c>]\n{doc.page_content}\n"
        )

    return "\n---\n".join(context_parts)
