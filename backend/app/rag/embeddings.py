"""
Embedding service.
Supports OpenAI text-embedding-3-small/large and a local sentence-transformers fallback.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM_MAP = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    "local": 384,
}


class EmbeddingService:
    """
    Generates embeddings for texts.
    Falls back to a local sentence-transformers model when no OpenAI key is set.
    """

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self.model = model
        self._local_model = None

    @property
    def dimension(self) -> int:
        return EMBEDDING_DIM_MAP.get(self.model, 1536)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if settings.OPENAI_API_KEY and self.model.startswith("text-embedding"):
            return await self._openai_embed(texts)
        return self._local_embed(texts)

    async def embed_query(self, query: str) -> list[float]:
        results = await self.embed_texts([query])
        return results[0]

    # ------------------------------------------------------------------
    # Backends
    # ------------------------------------------------------------------
    async def _openai_embed(self, texts: list[str]) -> list[list[float]]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        # Batch in groups of 100 to respect API limits
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), 100):
            batch = texts[i: i + 100]
            resp = await client.embeddings.create(model=self.model, input=batch)
            all_embeddings.extend([item.embedding for item in resp.data])
        return all_embeddings

    def _local_embed(self, texts: list[str]) -> list[list[float]]:
        """Use sentence-transformers all-MiniLM-L6-v2 as a local fallback."""
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = self._local_model.encode(texts, show_progress_bar=False)
        return [e.tolist() for e in embeddings]
