"""Anthropic Claude provider."""
import logging
from typing import AsyncIterator

import httpx

from app.core.config import settings
from .base import BaseProvider, ChatMessage, CompletionResponse

logger = logging.getLogger(__name__)

SUPPORTED_MODELS = [
    "claude-opus-4-5",
    "claude-sonnet-4-5",
    "claude-haiku-3-5",
    "claude-3-5-sonnet-20241022",
]

ANTHROPIC_API_BASE = "https://api.anthropic.com/v1"


class ClaudeProvider(BaseProvider):
    provider_name = "claude"

    def __init__(self) -> None:
        self._api_key = settings.CLAUDE_API_KEY
        if not self._api_key:
            logger.warning("Claude API key not configured; ClaudeProvider will be unavailable")
            self._available = False
            self._headers = {
                "x-api-key": "",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
        else:
            self._available = True
            self._headers = {
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

    @staticmethod
    def _split_messages(messages: list[ChatMessage]) -> tuple[str, list[dict]]:
        system_parts = [m.content for m in messages if m.role == "system"]
        convo = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        return "\n".join(system_parts), convo

    async def complete(
        self,
        messages: list[ChatMessage],
        model: str = "claude-sonnet-4-5",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> CompletionResponse:
        if not getattr(self, "_available", True) and settings.ENVIRONMENT.lower() == "production":
            raise RuntimeError("Claude provider not configured. Set CLAUDE_API_KEY to enable it.")

        system, convo = self._split_messages(messages)
        payload = {
            "model": model,
            "system": system,
            "messages": convo,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{ANTHROPIC_API_BASE}/messages",
                headers=self._headers,
                json=payload,
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()

        content = data["content"][0]["text"]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)
        return CompletionResponse(
            content=content,
            model=model,
            provider=self.provider_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            finish_reason=data.get("stop_reason", "end_turn"),
            raw=data,
        )

    async def stream(
        self,
        messages: list[ChatMessage],
        model: str = "claude-sonnet-4-5",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        system, convo = self._split_messages(messages)
        payload = {
            "model": model,
            "system": system,
            "messages": convo,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{ANTHROPIC_API_BASE}/messages",
                headers=self._headers,
                json=payload,
                timeout=120.0,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data:"):
                        import json
                        try:
                            event = json.loads(line[5:].strip())
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                        except Exception:
                            continue

    def list_models(self) -> list[str]:
        return SUPPORTED_MODELS
