from __future__ import annotations

import logging
import os

import httpx

from config import env_flag

from .config import env_float


logger = logging.getLogger(__name__)


class MemoryEmbeddingService:
    def __init__(self, *, enabled: bool | None = None, model_name: str | None = None) -> None:
        self.is_enabled = (
            enabled
            if enabled is not None
            else env_flag("MEMORY_EMBEDDINGS_ENABLED", False)
        )
        self.model_name = (
            model_name
            or os.getenv("MEMORY_EMBEDDING_MODEL", "text-embedding-3-small")
        ).strip()
        self.base_url = os.getenv("MEMORY_EMBEDDING_API_BASE_URL", "").strip()
        self.api_key = os.getenv("MEMORY_EMBEDDING_API_KEY", "").strip()
        self.timeout_seconds = env_float(
            "MEMORY_EMBEDDING_TIMEOUT_SECONDS",
            10.0,
            minimum=1.0,
            maximum=120.0,
        )

    def embed(self, text: str) -> list[float] | None:
        if not self.is_enabled or not self.base_url:
            return None

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            with httpx.Client(
                base_url=self.base_url.rstrip("/"),
                timeout=self.timeout_seconds,
            ) as client:
                response = client.post(
                    "/embeddings",
                    json={"model": self.model_name, "input": text},
                    headers=headers,
                )
                response.raise_for_status()
            payload = response.json()
            embedding = payload["data"][0]["embedding"]
            if not isinstance(embedding, list):
                return None
            return [float(value) for value in embedding]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            logger.exception("Failed to generate memory embedding.")
            return None
