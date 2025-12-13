"""
Setup Model Use Case

Handles model download, conversion, and import to Ollama.
"""

from pathlib import Path

from application.ports.input.i_setup_model_use_case import ISetupModelUseCase
from application.ports.output.i_logger import ILogger
from application.ports.output.i_model_converter import IModelConverter, QuantizationType
from application.ports.output.i_model_gateway import IModelGateway


class SetupModelUseCase(ISetupModelUseCase):
    """
    Use case for setting up models for evaluation.

    Orchestrates:
    1. Checking prerequisites (Ollama installed)
    2. Downloading model from HuggingFace
    3. Converting to GGUF format
    4. Importing to Ollama
    """

    def __init__(
        self,
        model_converter: IModelConverter,
        model_gateway: IModelGateway,
        logger: ILogger,
    ) -> None:
        self._model_converter = model_converter
        self._model_gateway = model_gateway
        self._logger = logger

    async def execute(
        self,
        hf_model_repo: str,
        model_name: str,
        quantization: QuantizationType = QuantizationType.Q5_K_M,
        force_reconvert: bool = False,
    ) -> dict[str, any]:
        """Set up model for evaluation."""
        self._logger.info(
            f"Starting model setup: {hf_model_repo}",
            model_name=model_name,
            quantization=quantization.value
        )

        # Check if model already exists in Ollama
        is_available = await self._model_gateway.is_model_available(model_name)
        if is_available and not force_reconvert:
            self._logger.info(f"Model '{model_name}' already available in Ollama")
            return {
                "status": "success",
                "message": f"Model '{model_name}' already available",
                "model_name": model_name,
                "skipped": True,
            }

        # Check if conversion is needed
        needs_conversion = await self._model_converter.is_conversion_required(hf_model_repo)

        if not needs_conversion and not force_reconvert:
            self._logger.info("Model already converted, skipping conversion")
        else:
            # Convert model
            self._logger.info("Converting model to GGUF format...")
            output_dir = Path("models/gguf").absolute()
            output_dir.mkdir(parents=True, exist_ok=True)

            gguf_path = await self._model_converter.convert_hf_to_gguf(
                hf_model_repo=hf_model_repo,
                output_path=str(output_dir),
                quantization=quantization,
                model_name=model_name,
            )
            self._logger.info(f"Model converted successfully: {gguf_path}")

            # Import to Ollama
            self._logger.info("Importing model to Ollama...")
            success = await self._model_converter.import_to_ollama(
                gguf_file_path=gguf_path,
                model_name=model_name,
                system_prompt=(
                    "You are a cybersecurity compliance expert specializing in "
                    "Singapore's CCoP 2.0 (Cybersecurity Code of Practice) standards "
                    "for Critical Information Infrastructure."
                ),
            )

            if not success:
                raise RuntimeError(f"Failed to import model '{model_name}' to Ollama")

            self._logger.info(f"Model '{model_name}' imported successfully")

        # Verify model is available
        is_available = await self._model_gateway.is_model_available(model_name)
        if not is_available:
            raise RuntimeError(f"Model '{model_name}' not available after setup")

        # Get model info
        model_info = await self._model_gateway.get_model_info(model_name)

        self._logger.info(f"Model setup complete: {model_name}")

        return {
            "status": "success",
            "message": f"Model '{model_name}' ready for evaluation",
            "model_name": model_name,
            "quantization": quantization.value,
            "model_info": model_info,
            "skipped": False,
        }

    async def check_prerequisites(self) -> dict[str, bool]:
        """Check if all prerequisites are met."""
        self._logger.info("Checking prerequisites...")

        checks = {}

        # Check if Ollama is accessible
        try:
            models = await self._model_gateway.list_available_models()
            checks["ollama_running"] = True
            checks["ollama_models_count"] = len(models)
        except Exception as e:
            self._logger.error(f"Ollama check failed: {e}")
            checks["ollama_running"] = False
            checks["error"] = str(e)

        self._logger.info("Prerequisites check complete", **checks)

        return checks
