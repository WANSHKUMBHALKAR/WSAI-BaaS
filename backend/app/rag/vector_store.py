"""
Qdrant vector store integration.
Manages collections, upserts, and similarity searches.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.core.config import settings
from app.rag.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

_client: Optional[AsyncQdrantClient] = None


def get_qdrant() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    return _client


class VectorStore:
    """
    High-level wrapper around Qdrant.
    Each project gets its own collection: wsai_{project_id}
    """

    def __init__(self, project_id: str, embedding_model: str = "text-embedding-3-small") -> None:
        self.collection_name = f"wsai_{project_id}"
        self._client = get_qdrant()
        self._embedder = EmbeddingService(model=embedding_model)

    async def ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        existing = await self._client.get_collections()
        names = [c.name for c in existing.collections]
        if self.collection_name not in names:
            await self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self._embedder.dimension,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s", self.collection_name)

    async def upsert_chunks(
        self,
        texts: list[str],
        document_id: str,
        extra_payload: dict | None = None,
    ) -> list[str]:
        """Embed and upsert a list of text chunks. Returns list of point IDs."""
        await self.ensure_collection()
        embeddings = await self._embedder.embed_texts(texts)
        point_ids = [str(uuid.uuid4()) for _ in texts]
        points = [
            PointStruct(
                id=pid,
                vector=embedding,
                payload={
                    "text": text,
                    "document_id": document_id,
                    "chunk_index": i,
                    **(extra_payload or {}),
                },
            )
            for i, (pid, text, embedding) in enumerate(zip(point_ids, texts, embeddings))
        ]
        await self._client.upsert(collection_name=self.collection_name, points=points)
        return point_ids

    async def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Semantic search. Optionally filter by document_id.
        Returns list of {text, score, metadata}.
        """
        await self.ensure_collection()
        query_vector = await self._embedder.embed_query(query)

        qdrant_filter = None
        if document_id:
            qdrant_filter = Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            )

        results = await self._client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [
            {
                "text": hit.payload.get("text", ""),
                "score": hit.score,
                "document_id": hit.payload.get("document_id"),
                "chunk_index": hit.payload.get("chunk_index"),
            }
            for hit in results
        ]

    async def delete_document(self, document_id: str) -> None:
        """Remove all vectors associated with a document."""
        from qdrant_client.models import FilterSelector
        await self._client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                )
            ),
        )
