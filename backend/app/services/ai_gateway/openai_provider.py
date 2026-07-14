"""OpenAI provider — supports GPT-4o, o1, and any future chat-completions model."""
import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import settings
from .base import BaseProvider, ChatMessage, CompletionResponse

logger = logging.getLogger(__name__)

SUPPORTED_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    "o1",
    "o1-mini",
]


class OpenAIProvider(BaseProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured; OpenAIProvider will be unavailable")
            self._client = None
        else:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _to_openai_messages(messages: list[ChatMessage]) -> list[dict]:
        out = []
        for m in messages:
            msg: dict = {"role": m.role, "content": m.content}
            if m.tool_calls:
                msg["tool_calls"] = m.tool_calls
            if m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            out.append(msg)
        return out

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def complete(
        self,
        messages: list[ChatMessage],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> CompletionResponse:
        if not self._client:
            raise RuntimeError("OpenAI provider not configured. Set OPENAI_API_KEY to enable it.")

        response = await self._client.chat.completions.create(
            model=model,
            messages=self._to_openai_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        choice = response.choices[0]
        usage = response.usage
        return CompletionResponse(
            content=choice.message.content or "",
            model=response.model,
            provider=self.provider_name,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            finish_reason=choice.finish_reason or "stop",
            raw=response.model_dump(),
        )

    async def stream(
        self,
        messages: list[ChatMessage],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=model,
            messages=self._to_openai_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def list_models(self) -> list[str]:
        return SUPPORTED_MODELS
