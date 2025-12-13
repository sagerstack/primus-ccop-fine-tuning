"""
Setup Model Use Case Port (Interface)

Abstract interface for model setup use case.
"""

from abc import ABC, abstractmethod
from typing import Optional

from application.ports.output.i_model_converter import QuantizationType


class ISetupModelUseCase(ABC):
    """
    Port (interface) for model setup use case.

    This use case handles downloading, converting, and importing models.
    """

    @abstractmethod
    async def execute(
        self,
        hf_model_repo: str,
        model_name: str,
        quantization: QuantizationType = QuantizationType.Q5_K_M,
        force_reconvert: bool = False,
    ) -> dict[str, any]:
        """
        Set up model for evaluation.

        Downloads from HuggingFace, converts to GGUF, and imports to Ollama.

        Args:
            hf_model_repo: HuggingFace repository
            model_name: Name to register in Ollama
            quantization: Quantization type
            force_reconvert: Force reconversion even if model exists

        Returns:
            Dictionary with setup results

        Raises:
            SetupError: If setup fails
        """
        pass

    @abstractmethod
    async def check_prerequisites(self) -> dict[str, bool]:
        """
        Check if all prerequisites are met (Ollama installed, etc.).

        Returns:
            Dictionary with prerequisite check results
        """
        pass
