"""Embedding service for OpenAI text embeddings (text-embedding-3-small)."""

from __future__ import annotations

import asyncio
import logging
from typing import List, Sequence

import numpy as np
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Asynchronous wrapper around OpenAI's embedding API."""

    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self._client: AsyncOpenAI | None = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> AsyncOpenAI:
        if self._client:
            return self._client

        async with self._lock:
            if self._client:
                return self._client

            logger.info(
                "Initializing OpenAI embedding client for model '%s'", self.model_name
            )
            self._client = AsyncOpenAI()
        return self._client

    async def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        """Embed a batch of texts; returns an ndarray of shape (len(texts), dim)."""
        filtered = [text.strip() for text in texts if text and text.strip()]
        if not filtered:
            return np.zeros((0, 0))

        client = await self._get_client()
        logger.debug("Requesting embeddings for %d texts", len(filtered))
        response = await client.embeddings.create(
            model=self.model_name, input=list(filtered)
        )
        vectors = np.array([data.embedding for data in response.data], dtype=float)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-9
        return vectors / norms

    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text and return a JSON-serializable list of floats."""
        embeddings = await self.embed_texts([text])
        if embeddings.size == 0:
            return []
        return embeddings[0].astype(float).tolist()


def create_embedding_service(model_name: str = "text-embedding-3-small") -> EmbeddingService:
    return EmbeddingService(model_name=model_name)


__all__ = ["EmbeddingService", "create_embedding_service"]
