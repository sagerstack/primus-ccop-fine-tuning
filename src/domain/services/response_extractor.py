"""
Utility for extracting final answers from reasoning model outputs.

Handles chain-of-thought output from models like Llama-Primus-Reasoning
by extracting content after "Final Answer:" marker.
"""

import re


def extract_final_answer(response_text: str) -> str:
    """
    Extract final answer from chain-of-thought reasoning output.

    Searches for "Final Answer:" marker (case-insensitive) and returns
    everything after it. If no marker found, returns the full response
    (model may not use chain-of-thought).

    Args:
        response_text: Raw response from reasoning model

    Returns:
        Extracted final answer text (stripped)

    Examples:
        >>> extract_final_answer("Thinking...\nFinal Answer: The answer is X")
        'The answer is X'
        >>> extract_final_answer("No marker here")
        'No marker here'
    """
    # Case-insensitive search for "Final Answer:" marker
    match = re.search(r"final answer:\s*", response_text, re.IGNORECASE)

    if match:
        # Return everything after the marker
        return response_text[match.end():].strip()
    else:
        # No marker found, return full response
        return response_text.strip()
