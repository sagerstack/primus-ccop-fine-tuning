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
        [Source: {document_source}, Clause {clause}]
        {document text}

    Falls back to `Section {section}` when no clause is present (rare;
    preamble chunks). One identifier per chunk — surfacing both section
    and clause leads the model to merge them ("Section 1.6.2") in its
    Sources footer, which complicates downstream lookup.

    Documents are joined with '---' separators.
    """
    context_parts = []
    for doc in documents:
        document_source = doc.metadata.get("document_source", "unknown")
        section = (doc.metadata.get("section") or "").strip()
        clause = (doc.metadata.get("clause") or "").strip()

        header_parts = [f"Source: {document_source}"]
        # Prefer the more specific identifier — clause if present, otherwise
        # section. Surfacing both creates a "Section 1, Clause 1.6.2" shape
        # that the model rewrites as "Section 1.6.2" in its Sources footer,
        # confusing downstream lookup. One identifier per chunk is cleaner.
        if clause:
            header_parts.append(f"Clause {clause}")
        elif section:
            header_parts.append(f"Section {section}")
        header = ", ".join(header_parts)

        context_parts.append(f"[{header}]\n{doc.page_content}\n")

    return "\n---\n".join(context_parts)
