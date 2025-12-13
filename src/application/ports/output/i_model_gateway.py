"""
Model Gateway Port (Interface)

Abstract interface for LLM inference.
Infrastructure layer will implement this for specific models (Ollama, HuggingFace, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from domain.entities.model_response import ModelResponse


class IModelGateway(ABC):
    """
    Port (interface) for model inference operations.

    This is an output port - the application depends on this abstraction,
    and the infrastructure provides concrete implementations.
    """

    @abstractmethod
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
        """
        Generate a response from the model.

        Args:
            prompt: The input prompt
            model_name: Name of the model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            system_prompt: Optional system prompt
            metadata: Optional metadata to include in response

        Returns:
            ModelResponse entity with generated content

        Raises:
            ModelGatewayError: If generation fails
        """
        pass

    @abstractmethod
    async def is_model_available(self, model_name: str) -> bool:
        """
        Check if a model is available for inference.

        Args:
            model_name: Name of the model

        Returns:
            True if model is available
        """
        pass

    @abstractmethod
    async def list_available_models(self) -> list[str]:
        """
        List all available models.

        Returns:
            List of model names
        """
        pass

    @abstractmethod
    async def get_model_info(self, model_name: str) -> Dict[str, any]:
        """
        Get information about a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with model metadata

        Raises:
            ModelNotFoundError: If model doesn't exist
        """
        pass
