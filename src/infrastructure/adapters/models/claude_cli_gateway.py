"""
Claude CLI Model Gateway

Implementation of IModelGateway using the Claude CLI (`claude -p`).
"""

import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from application.ports.output.i_logger import ILogger
from application.ports.output.i_model_gateway import IModelGateway
from domain.entities.model_response import ModelResponse


class ClaudeCliGateway(IModelGateway):
    """Claude CLI implementation of model gateway."""

    def __init__(self, logger: ILogger, timeout: int = 120) -> None:
        self._logger = logger
        self._timeout = timeout

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
        """Generate response via Claude CLI."""
        start_time = datetime.utcnow()

        cmd = ["claude", "-p", "--model", model_name]
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Claude CLI error: {result.stderr}")

            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)

            response_metadata = metadata or {}
            response_metadata["gateway"] = "claude_cli"

            return ModelResponse(
                response_id=uuid4(),
                content=result.stdout,
                model_name=model_name,
                tokens_used=0,
                latency_ms=latency_ms,
                temperature=temperature,
                created_at=end_time,
                metadata=response_metadata,
            )

        except subprocess.TimeoutExpired:
            self._logger.error(
                f"Claude CLI timed out after {self._timeout}s",
                model=model_name,
            )
            raise
        except Exception as e:
            self._logger.error(f"Failed to generate response: {e}", model=model_name)
            raise

    async def is_model_available(self, model_name: str) -> bool:
        """Always returns True — CLI validates at generation time."""
        return True

    async def list_available_models(self) -> list[str]:
        """List known Claude model aliases."""
        return ["sonnet", "opus", "haiku"]

    async def get_model_info(self, model_name: str) -> Dict[str, any]:
        """Return basic model info."""
        return {
            "name": model_name,
            "provider": "anthropic",
            "gateway": "claude_cli",
        }
