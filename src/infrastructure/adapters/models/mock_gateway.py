"""
Mock Model Gateway

Mock implementation for testing.
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from application.ports.output.i_model_gateway import IModelGateway
from domain.entities.model_response import ModelResponse


class MockModelGateway(IModelGateway):
    """Mock model gateway for testing."""

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
        """Generate mock response."""
        return ModelResponse(
            response_id=uuid4(),
            content=f"Mock response for: {prompt[:50]}...",
            model_name=model_name,
            tokens_used=100,
            latency_ms=500,
            temperature=temperature,
            created_at=datetime.utcnow(),
            metadata=metadata or {},
        )

    async def is_model_available(self, model_name: str) -> bool:
        """Always return True for mock."""
        return True

    async def list_available_models(self) -> list[str]:
        """Return mock model list."""
        return ["mock-model", "primus-reasoning"]

    async def get_model_info(self, model_name: str) -> Dict[str, any]:
        """Return mock model info."""
        return {
            "name": model_name,
            "type": "mock",
            "description": "Mock model for testing",
        }
