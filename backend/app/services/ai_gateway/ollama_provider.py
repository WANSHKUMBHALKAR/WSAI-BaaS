"""Ollama provider for locally-hosted open-source models."""
import logging
from typing import AsyncIterator

import httpx

from app.core.config import settings
from .base import BaseProvider, ChatMessage, CompletionResponse

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_BASE = "http://localhost:11434"


class OllamaProvider(BaseProvider):
    provider_name = "ollama"

    def __init__(self) -> None:
        self._base_url = getattr(settings, "OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE)

    @staticmethod
    def _to_ollama_messages(messages: list[ChatMessage]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def list_models(self) -> list[str]:
        """Synchronously fetch model list from local Ollama daemon."""
        try:
            resp = httpx.get(f"{self._base_url}/api/tags", timeout=5.0)
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    async def complete(
        self,
        messages: list[ChatMessage],
        model: str = "llama3",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> CompletionResponse:
        payload = {
            "model": model,
            "messages": self._to_ollama_messages(messages),
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()

        content = data["message"]["content"]
        prompt_eval = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)
        return CompletionResponse(
            content=content,
            model=model,
            provider=self.provider_name,
            prompt_tokens=prompt_eval,
            completion_tokens=eval_count,
            total_tokens=prompt_eval + eval_count,
            finish_reason="stop",
            raw=data,
        )

    async def stream(
        self,
        messages: list[ChatMessage],
        model: str = "llama3",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        import json as _json

        payload = {
            "model": model,
            "messages": self._to_ollama_messages(messages),
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=120.0,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = _json.loads(line)
                            chunk = data.get("message", {}).get("content", "")
                            if chunk:
                                yield chunk
                        except Exception:
                            continue
