"""
Ollama Model Gateway

Implementation of IModelGateway for Ollama.
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from application.ports.output.i_logger import ILogger
from application.ports.output.i_model_gateway import IModelGateway
from domain.entities.model_response import ModelResponse
from infrastructure.external.ollama_client import OllamaClient


class OllamaGateway(IModelGateway):
    """Ollama implementation of model gateway."""

    def __init__(self, client: OllamaClient, logger: ILogger) -> None:
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
        """Generate response from Ollama model."""
        start_time = datetime.utcnow()

        # Normalize model name: if no tag specified, add :latest
        ollama_model_name = model_name if ":" in model_name else f"{model_name}:latest"

        try:
            response_data = await self._client.generate(
                model=ollama_model_name,
                prompt=prompt,
                system=system_prompt,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_tokens=max_tokens,
            )

            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)

            prompt_tokens = response_data.get("prompt_eval_count", 0)
            completion_tokens = response_data.get("eval_count", 0)
            total_tokens = prompt_tokens + completion_tokens

            return ModelResponse(
                response_id=uuid4(),
                content=response_data.get("response", ""),
                model_name=model_name,
                tokens_used=response_data.get("eval_count", 0),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                temperature=temperature,
                created_at=end_time,
                metadata=metadata or {},
            )

        except Exception as e:
            self._logger.error(f"Failed to generate response: {e}", model=model_name)
            raise

    async def is_model_available(self, model_name: str) -> bool:
        """Check if model is available in Ollama."""
        try:
            models = await self._client.list_models()
            model_names = [m.get("name", "") for m in models]

            # Check exact match first
            if model_name in model_names:
                return True

            # If no exact match, try with :latest tag
            if f"{model_name}:latest" in model_names:
                return True

            return False
        except Exception:
            return False

    async def list_available_models(self) -> list[str]:
        """List all available models in Ollama."""
        try:
            models = await self._client.list_models()
            return [m.get("name", "") for m in models]
        except Exception as e:
            self._logger.error(f"Failed to list models: {e}")
            return []

    async def get_model_info(self, model_name: str) -> Dict[str, any]:
        """Get model information from Ollama."""
        try:
            info = await self._client.show_model(model_name)
            return {
                "name": model_name,
                "modelfile": info.get("modelfile", ""),
                "parameters": info.get("parameters", ""),
                "template": info.get("template", ""),
            }
        except Exception as e:
            self._logger.error(f"Failed to get model info: {e}", model=model_name)
            raise
