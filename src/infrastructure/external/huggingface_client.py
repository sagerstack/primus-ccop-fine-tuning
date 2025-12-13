"""
HuggingFace Client

Client for downloading models from HuggingFace Hub.
"""

from pathlib import Path
from typing import Optional

from huggingface_hub import snapshot_download


class HuggingFaceClient:
    """Client for HuggingFace Hub operations."""

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self.cache_dir = cache_dir or Path.home() / ".cache" / "huggingface"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def download_model(
        self,
        repo_id: str,
        local_dir: Optional[Path] = None,
        token: Optional[str] = None,
    ) -> str:
        """
        Download model from HuggingFace Hub.

        Args:
            repo_id: Repository ID (e.g., "trendmicro-ailab/Llama-Primus-Reasoning")
            local_dir: Local directory to save model
            token: Optional HuggingFace token

        Returns:
            Path to downloaded model directory
        """
        if local_dir is None:
            local_dir = self.cache_dir / repo_id.replace("/", "--")

        local_dir.mkdir(parents=True, exist_ok=True)

        # Download model files
        path = snapshot_download(
            repo_id=repo_id,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            token=token,
        )

        return path
