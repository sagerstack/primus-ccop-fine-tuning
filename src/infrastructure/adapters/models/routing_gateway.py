"""
Routing Model Gateway

Routes inference to the correct backend based on model name.
Claude models (sonnet, opus, haiku) → ClaudeCliGateway.
Everything else → OllamaGateway.
"""

from typing import Dict, Optional

from application.ports.output.i_logger import ILogger
from application.ports.output.i_model_gateway import IModelGateway
from domain.entities.model_response import ModelResponse

CLAUDE_MODEL_ALIASES = {"sonnet", "opus", "haiku"}


class RoutingModelGateway(IModelGateway):
    """Routes to ClaudeCliGateway or OllamaGateway based on model name."""

    def __init__(
        self,
        claude_gateway: IModelGateway,
        ollama_gateway: IModelGateway,
        logger: ILogger,
    ) -> None:
        self._claude_gateway = claude_gateway
        self._ollama_gateway = ollama_gateway
        self._logger = logger

    def _resolve_gateway(self, model_name: str) -> IModelGateway:
        if model_name.lower() in CLAUDE_MODEL_ALIASES:
            return self._claude_gateway
        return self._ollama_gateway

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
        gateway = self._resolve_gateway(model_name)
        self._logger.info(
            f"Routing inference to {type(gateway).__name__}",
            model=model_name,
        )
        return await gateway.generate_response(
            prompt=prompt,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            system_prompt=system_prompt,
            metadata=metadata,
        )

    async def is_model_available(self, model_name: str) -> bool:
        gateway = self._resolve_gateway(model_name)
        return await gateway.is_model_available(model_name)

    async def list_available_models(self) -> list[str]:
        claude_models = await self._claude_gateway.list_available_models()
        ollama_models = await self._ollama_gateway.list_available_models()
        return claude_models + ollama_models

    async def get_model_info(self, model_name: str) -> Dict[str, any]:
        gateway = self._resolve_gateway(model_name)
        return await gateway.get_model_info(model_name)
