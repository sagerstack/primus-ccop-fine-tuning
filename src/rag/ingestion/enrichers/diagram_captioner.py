"""
Diagram Captioner

Replaces <!-- image --> placeholders in Docling markdown with GLM-4V descriptions
of the corresponding PictureItem images from the DoclingDocument.
"""

import logging
from collections import Counter

from infrastructure.external.zhipuai_client import ZhipuVisionClient

logger = logging.getLogger(__name__)

IMAGE_PLACEHOLDER = "<!-- image -->"


def caption_diagrams(
    markdown: str,
    document: object,
    vision_client: ZhipuVisionClient,
    prompt: str,
) -> str:
    """
    Replace image placeholders in markdown with diagram descriptions.

    The Nth <!-- image --> placeholder corresponds to the Nth item in
    document.pictures. Each picture's image is sent to the vision client
    for captioning.

    Args:
        markdown: Markdown text from Docling export_to_markdown()
        document: DoclingDocument with .pictures list
        vision_client: ZhipuAI vision client for generating descriptions
        prompt: Prompt to guide the vision model

    Returns:
        Enriched markdown with diagram descriptions replacing placeholders
    """
    pictures = getattr(document, "pictures", [])
    if not pictures:
        return markdown

    placeholder_count = markdown.count(IMAGE_PLACEHOLDER)
    picture_count = len(pictures)

    if placeholder_count != picture_count:
        logger.warning(
            f"Placeholder/picture count mismatch: "
            f"{placeholder_count} placeholders vs {picture_count} pictures"
        )

    result = markdown
    replaced = 0

    for i, picture in enumerate(pictures):
        if IMAGE_PLACEHOLDER not in result:
            break

        image = picture.get_image(document)
        if image is None:
            logger.warning(f"Picture {i}: no image data, keeping placeholder")
            continue

        caption = picture.caption_text(document)
        description = vision_client.describe_image(image, prompt, caption)

        if caption:
            formatted = f"**[Diagram: {caption}]**\n\n{description}"
        else:
            formatted = f"**[Diagram]**\n\n{description}"

        result = result.replace(IMAGE_PLACEHOLDER, formatted, 1)
        replaced += 1
        logger.debug(f"Picture {i}: captioned ({len(description)} chars)")

    logger.info(f"Captioned {replaced}/{picture_count} diagrams")
    return result


def detect_garbled_text(text: str, threshold: int = 5) -> bool:
    """
    Detect garbled/repetitive text from failed VLM parsing.

    Splits text into 3-word n-grams and checks if any n-gram repeats
    more than `threshold` times, indicating garbled output.

    Args:
        text: Text to check
        threshold: Maximum allowed repetitions of any 3-gram

    Returns:
        True if text appears garbled
    """
    words = text.split()
    if len(words) < 6:
        return False

    ngram_size = 3
    ngrams = [
        " ".join(words[j : j + ngram_size])
        for j in range(len(words) - ngram_size + 1)
    ]

    counts = Counter(ngrams)
    most_common_count = counts.most_common(1)[0][1]

    return most_common_count > threshold
