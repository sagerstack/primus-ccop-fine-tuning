"""
ZhipuAI Vision Client

Synchronous HTTP client for GLM-4V diagram captioning via OpenAI-compatible API.
"""

import base64
import io
import logging

import httpx
from PIL import Image

logger = logging.getLogger(__name__)

FALLBACK_DESCRIPTION = "[Diagram description unavailable]"


class ZhipuVisionClient:
    """Synchronous client for ZhipuAI GLM-4V vision API."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int = 60,
        max_tokens: int = 512,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._max_tokens = max_tokens
        self._client = httpx.Client(timeout=timeout)

    def describe_image(
        self, image: Image.Image, prompt: str, caption: str = ""
    ) -> str:
        """
        Generate a text description of an image using GLM-4V.

        Args:
            image: PIL Image to describe
            prompt: System prompt guiding the description
            caption: Existing caption from the document (included as context)

        Returns:
            Description text, or fallback string on failure
        """
        b64_image = self._encode_image(image)

        text_content = prompt
        if caption:
            text_content = f"{prompt}\n\nCaption: {caption}"

        payload = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_content},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}"
                            },
                        },
                    ],
                }
            ],
        }

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self._client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            description = data["choices"][0]["message"]["content"]
            return description.strip()

        except httpx.TimeoutException:
            logger.warning("ZhipuAI request timed out")
            return FALLBACK_DESCRIPTION
        except httpx.HTTPStatusError as e:
            logger.error(f"ZhipuAI API error: {e.response.status_code} - {e.response.text}")
            return FALLBACK_DESCRIPTION
        except Exception as e:
            logger.error(f"ZhipuAI request failed: {e}")
            return FALLBACK_DESCRIPTION

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    @staticmethod
    def _encode_image(image: Image.Image) -> str:
        """Convert PIL Image to base64-encoded PNG string."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
