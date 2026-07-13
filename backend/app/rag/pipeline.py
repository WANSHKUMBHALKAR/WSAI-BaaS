"""
Full RAG retrieval pipeline.
Combines vector search with context-aware prompt assembly for LLM-ready responses.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.rag.vector_store import VectorStore
from app.services.ai_gateway.gateway import AIGateway
from app.services.ai_gateway.base import ChatMessage

logger = logging.getLogger(__name__)

_SYSTEM_TEMPLATE = """You are a knowledgeable AI assistant. 
Use ONLY the provided context to answer the question. If the answer is not in the context, say so honestly.

CONTEXT:
{context}
"""


class RAGPipeline:
    """
    Orchestrates retrieval + generation for a given project's vector store.
    """

    def __init__(
        self,
        project_id: str,
        model: str = "gpt-4o",
        top_k: int = 5,
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        self.store = VectorStore(project_id=project_id, embedding_model=embedding_model)
        self.gateway = AIGateway()
        self.model = model
        self.top_k = top_k

    async def query(
        self,
        question: str,
        document_id: Optional[str] = None,
        conversation_history: list[ChatMessage] | None = None,
    ) -> dict:
        """
        1. Retrieve top-k relevant chunks from Qdrant
        2. Build an augmented prompt
        3. Run through the AI gateway
        4. Return answer + sources
        """
        # Step 1: Retrieval
        hits = await self.store.search(query=question, top_k=self.top_k, document_id=document_id)

        if not hits:
            context = "No relevant context found in the knowledge base."
        else:
            context = "\n\n---\n\n".join(
                f"[Source {i+1}] {hit['text']}" for i, hit in enumerate(hits)
            )

        # Step 2: Build messages
        system_msg = ChatMessage(role="system", content=_SYSTEM_TEMPLATE.format(context=context))
        user_msg = ChatMessage(role="user", content=question)

        messages: list[ChatMessage] = [system_msg]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append(user_msg)

        # Step 3: Generate
        response = await self.gateway.chat(messages=messages, model=self.model)

        return {
            "answer": response.content,
            "sources": [
                {
                    "text": h["text"][:300],
                    "score": round(h["score"], 4),
                    "document_id": h["document_id"],
                    "chunk_index": h["chunk_index"],
                }
                for h in hits
            ],
            "tokens_used": response.total_tokens,
            "model": response.model,
        }
