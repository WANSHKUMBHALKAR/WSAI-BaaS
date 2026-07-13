"""
Memory Manager — dual-layer memory system.

Short-term memory  → Redis (fast, sliding window of recent messages)
Long-term memory   → Qdrant (semantic vector search) + Postgres (metadata)
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.memory import Memory
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Each agent/user pair gets a Redis key with a sliding window of N messages
SHORT_TERM_WINDOW = 20
SHORT_TERM_TTL = 60 * 60 * 24  # 24 hours


class MemoryManager:
    """
    Manages both short-term (Redis) and long-term (Qdrant + Postgres) memory.
    """

    def __init__(self, agent_id: str, user_id: str, db: Session) -> None:
        self.agent_id = agent_id
        self.user_id = user_id
        self._db = db
        self._redis: Optional[aioredis.Redis] = None
        self._store = VectorStore(project_id=f"mem_{agent_id}", embedding_model="text-embedding-3-small")
        self._embedder = EmbeddingService()

    # ------------------------------------------------------------------
    # Redis short-term memory
    # ------------------------------------------------------------------
    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    def _st_key(self) -> str:
        return f"stm:{self.agent_id}:{self.user_id}"

    async def add_short_term(self, role: str, content: str) -> None:
        r = await self._get_redis()
        key = self._st_key()
        message = json.dumps({"role": role, "content": content})
        await r.rpush(key, message)
        await r.ltrim(key, -SHORT_TERM_WINDOW, -1)
        await r.expire(key, SHORT_TERM_TTL)

    async def get_short_term(self) -> list[dict]:
        r = await self._get_redis()
        raw = await r.lrange(self._st_key(), 0, -1)
        return [json.loads(m) for m in raw]

    async def clear_short_term(self) -> None:
        r = await self._get_redis()
        await r.delete(self._st_key())

    # ------------------------------------------------------------------
    # Qdrant + Postgres long-term memory
    # ------------------------------------------------------------------
    async def add_long_term(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
    ) -> Memory:
        # Store in Qdrant
        await self._store.ensure_collection()
        point_ids = await self._store.upsert_chunks(
            texts=[content],
            document_id=self.agent_id,
            extra_payload={"user_id": self.user_id, "memory_type": memory_type},
        )

        # Persist metadata to Postgres
        mem = Memory(
            id=uuid.uuid4(),
            agent_id=self.agent_id,
            user_id=self.user_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            qdrant_id=point_ids[0] if point_ids else None,
            last_accessed=datetime.now(timezone.utc),
        )
        self._db.add(mem)
        self._db.commit()
        self._db.refresh(mem)
        return mem

    async def search_long_term(self, query: str, top_k: int = 5) -> list[dict]:
        await self._store.ensure_collection()
        return await self._store.search(query=query, top_k=top_k)

    async def get_relevant_context(self, query: str, top_k: int = 5) -> str:
        """Compose a memory context string for the agent system prompt."""
        short = await self.get_short_term()
        long = await self.search_long_term(query, top_k=top_k)

        parts = []
        if short:
            parts.append("RECENT CONVERSATION:\n" + "\n".join(
                f"{m['role'].upper()}: {m['content']}" for m in short[-5:]
            ))
        if long:
            parts.append("RELEVANT MEMORIES:\n" + "\n".join(
                f"- {h['text'][:200]}" for h in long
            ))
        return "\n\n".join(parts) if parts else ""
