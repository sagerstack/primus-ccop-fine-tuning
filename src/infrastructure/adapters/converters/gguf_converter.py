"""
GGUF Converter

Converts HuggingFace models to GGUF format and imports to Ollama.
"""

from pathlib import Path
from typing import Optional

from application.ports.output.i_logger import ILogger
from application.ports.output.i_model_converter import IModelConverter, QuantizationType
from infrastructure.external.huggingface_client import HuggingFaceClient
from infrastructure.external.ollama_client import OllamaClient


class GGUFConverter(IModelConverter):
    """Converter for HuggingFace models to GGUF format."""

    def __init__(
        self,
        ollama_client: OllamaClient,
        hf_client: HuggingFaceClient,
        cache_dir: Path,
        logger: ILogger,
    ) -> None:
        self._ollama = ollama_client
        self._hf = hf_client
        self._cache_dir = Path(cache_dir)
        self._logger = logger

    async def convert_hf_to_gguf(
        self,
        hf_model_repo: str,
        output_path: str,
        quantization: QuantizationType = QuantizationType.Q5_K_M,
        model_name: Optional[str] = None,
    ) -> str:
        """
        Convert HuggingFace model to GGUF (stub - calls external script).

        In production, this would call the conversion scripts or use llama.cpp.
        For now, assumes conversion is done manually via scripts/convert_to_gguf.sh
        """
        self._logger.info(
            f"Conversion placeholder: {hf_model_repo} → GGUF {quantization.value}"
        )

        # Stub: return expected path
        output_dir = Path(output_path)
        model_filename = f"{model_name or 'model'}-{quantization.value}.gguf"
        gguf_path = output_dir / model_filename

        self._logger.warning(
            "Automated conversion not implemented. "
            "Please use scripts/convert_to_gguf.sh manually."
        )

        return str(gguf_path)

    async def import_to_ollama(
        self,
        gguf_file_path: str,
        model_name: str,
        system_prompt: Optional[str] = None,
        template: Optional[str] = None,
    ) -> bool:
        """Import GGUF to Ollama."""
        # Create Modelfile
        modelfile = f"FROM {gguf_file_path}\n"

        if system_prompt:
            modelfile += f'SYSTEM """{system_prompt}"""\n'

        if template:
            modelfile += f'TEMPLATE """{template}"""\n'
        else:
            # Default Llama 3.1 template
            modelfile += '''TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{{ .System }}<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{{ .Prompt }}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""
'''

        modelfile += 'PARAMETER stop "<|eot_id|>"\n'
        modelfile += 'PARAMETER stop "<|end_of_text|>"\n'

        # Create model in Ollama
        try:
            await self._ollama.create_model(model_name, modelfile)
            self._logger.info(f"Model imported to Ollama: {model_name}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to import model: {e}")
            return False

    async def is_conversion_required(self, hf_model_repo: str) -> bool:
        """Check if conversion is needed (stub)."""
        return True  # Always assume conversion needed for now
