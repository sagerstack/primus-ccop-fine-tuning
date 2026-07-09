"""
OpenRouter Model Gateway.

`IModelGateway` over the OpenRouter (OpenAI-compatible) API, wrapping the
existing `OpenRouterClient` the LLM-Judge already uses. Introduced for the
Phase-11 Compliance-Unit build (classification + 4-tuple extraction) so it no
longer depends on the local `claude -p` subscription, which was exhausting the
Claude daily/monthly token limits mid-build (2026-07-05). OpenRouter is billed
on OpenRouter credits, decoupled from the Claude subscription.

The blocking, retrying `OpenRouterClient.call` is off-loaded to a worker thread
(`asyncio.to_thread`) so the async CU batch loop is not blocked. Any API
failure propagates (the CU classifier/extractor translate it into a
`GatewayUnavailableError` and SKIP the unit for a resume pass — never a
wrong-value write).
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from application.ports.output.i_logger import ILogger
from application.ports.output.i_model_gateway import IModelGateway
from domain.entities.model_response import ModelResponse
from infrastructure.external.openrouter_client import OpenRouterClient


class OpenRouterGateway(IModelGateway):
    """`IModelGateway` backed by OpenRouter (via `OpenRouterClient`)."""

    def __init__(self, client: OpenRouterClient, logger: Optional[ILogger] = None) -> None:
        self._client = client
        self._logger = logger

    async def generate_response(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.9,
        top_k: int = 40,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, any]] = None,
    ) -> ModelResponse:
        start = datetime.now(timezone.utc)
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        try:
            content = await asyncio.to_thread(
                self._client.call,
                full_prompt,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            if self._logger:
                self._logger.error(f"OpenRouter call failed: {e}", model=model_name)
            raise
        end = datetime.now(timezone.utc)
        response_metadata = metadata or {}
        response_metadata["gateway"] = "openrouter"
        return ModelResponse(
            response_id=uuid4(),
            content=content,
            model_name=model_name,
            tokens_used=0,
            latency_ms=int((end - start).total_seconds() * 1000),
            temperature=temperature,
            created_at=end,
            metadata=response_metadata,
        )

    async def is_model_available(self, model_name: str) -> bool:
        return True

    async def list_available_models(self) -> list[str]:
        return []

    async def get_model_info(self, model_name: str) -> Dict[str, any]:
        return {"name": model_name, "provider": "openrouter"}
