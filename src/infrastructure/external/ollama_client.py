"""
Ollama Client

Low-level HTTP client for Ollama API.
"""

import httpx
from typing import Any, Dict, List, Optional


class OllamaClient:
    """HTTP client for Ollama API."""

    def __init__(self, host: str = "http://localhost:11434", timeout: int = 300) -> None:
        self.host = host.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Generate completion from Ollama."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        url = f"{self.host}/api/tags"
        response = await self._client.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("models", [])

    async def show_model(self, name: str) -> Dict[str, Any]:
        """Get model information."""
        url = f"{self.host}/api/show"
        response = await self._client.post(url, json={"name": name})
        response.raise_for_status()
        return response.json()

    async def create_model(
        self,
        name: str,
        modelfile: str
    ) -> bool:
        """Create model from Modelfile."""
        url = f"{self.host}/api/create"
        payload = {"name": name, "modelfile": modelfile, "stream": False}
        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        return True

    async def delete_model(self, name: str) -> bool:
        """Delete a model."""
        url = f"{self.host}/api/delete"
        response = await self._client.delete(url, json={"name": name})
        response.raise_for_status()
        return True

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
