"""
Model Converter Port (Interface)

Abstract interface for converting models between formats (e.g., HF → GGUF).
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class QuantizationType(str, Enum):
    """Supported quantization types."""
    Q4_K_M = "Q4_K_M"
    Q5_K_M = "Q5_K_M"
    Q6_K = "Q6_K"
    Q8_0 = "Q8_0"
    F16 = "F16"


class IModelConverter(ABC):
    """
    Port (interface) for model format conversion operations.

    Used for converting models from HuggingFace format to GGUF for Ollama.
    """

    @abstractmethod
    async def convert_hf_to_gguf(
        self,
        hf_model_repo: str,
        output_path: str,
        quantization: QuantizationType = QuantizationType.Q5_K_M,
        model_name: Optional[str] = None,
    ) -> str:
        """
        Convert HuggingFace model to GGUF format.

        Args:
            hf_model_repo: HuggingFace repository (e.g., "trendmicro-ailab/Llama-Primus-Reasoning")
            output_path: Directory to save GGUF file
            quantization: Quantization type
            model_name: Optional custom model name

        Returns:
            Path to converted GGUF file

        Raises:
            ConversionError: If conversion fails
        """
        pass

    @abstractmethod
    async def import_to_ollama(
        self,
        gguf_file_path: str,
        model_name: str,
        system_prompt: Optional[str] = None,
        template: Optional[str] = None,
    ) -> bool:
        """
        Import GGUF model to Ollama.

        Args:
            gguf_file_path: Path to GGUF file
            model_name: Name to register in Ollama
            system_prompt: Optional system prompt
            template: Optional prompt template

        Returns:
            True if successful

        Raises:
            ImportError: If import fails
        """
        pass

    @abstractmethod
    async def is_conversion_required(self, hf_model_repo: str) -> bool:
        """
        Check if model needs conversion (not already in Ollama).

        Args:
            hf_model_repo: HuggingFace repository

        Returns:
            True if conversion needed
        """
        pass
