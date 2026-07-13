"""
Provider factory + gateway router.

Responsibilities:
  - Build the correct provider from a model name or explicit provider tag
  - Execute completions with automatic fallback
  - Log every request to the usage_logs table
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

from sqlalchemy.orm import Session

from .base import BaseProvider, ChatMessage, CompletionResponse
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .claude_provider import ClaudeProvider
from .ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model → provider routing table
# ---------------------------------------------------------------------------
_MODEL_ROUTING: dict[str, str] = {
    # OpenAI
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    "gpt-4-turbo": "openai",
    "gpt-4": "openai",
    "gpt-3.5-turbo": "openai",
    "o1": "openai",
    "o1-mini": "openai",
    # Gemini
    "gemini-1.5-pro": "gemini",
    "gemini-1.5-flash": "gemini",
    "gemini-2.0-flash": "gemini",
    "gemini-2.5-pro": "gemini",
    "gemini-2.5-flash": "gemini",
    # Claude
    "claude-opus-4-5": "claude",
    "claude-sonnet-4-5": "claude",
    "claude-haiku-3-5": "claude",
    "claude-3-5-sonnet-20241022": "claude",
}

# Fallback chain: if primary fails, try these in order
_FALLBACK_CHAIN: list[tuple[str, str]] = [
     ("gemini", "gemini-2.5-flash"),
    ("openai", "gpt-4o"),
    ("ollama", "llama3"),
]


class ProviderFactory:
    """Singleton-ish factory — creates provider instances on demand."""

    _instances: dict[str, BaseProvider] = {}

    @classmethod
    def get(cls, provider_name: str) -> BaseProvider:
        if provider_name not in cls._instances:
            cls._instances[provider_name] = cls._create(provider_name)
        return cls._instances[provider_name]

    @staticmethod
    def _create(name: str) -> BaseProvider:
        providers: dict[str, type[BaseProvider]] = {
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
            "claude": ClaudeProvider,
            "ollama": OllamaProvider,
        }
        klass = providers.get(name)
        if not klass:
            raise ValueError(f"Unknown provider: {name}")
        return klass()

    @staticmethod
    def resolve_provider(model: str) -> str:
        return _MODEL_ROUTING.get(model, "ollama")


class AIGateway:
    """
    Unified entrypoint for all LLM interactions.

    Usage:
        gw = AIGateway(db)
        response = await gw.chat(messages, model="gpt-4o", project_id=...)
    """

    def __init__(self, db: Optional[Session] = None) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str = "gpt-4o",
        project_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        fallback: bool = True,
        **kwargs,
    ) -> CompletionResponse:
        provider_name = ProviderFactory.resolve_provider(model)
        start = time.perf_counter()

        try:
            provider = ProviderFactory.get(provider_name)
            response = await provider.complete(
                messages, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs
            )
        except Exception as primary_exc:
            logger.warning("Primary provider %s failed: %s", provider_name, primary_exc)
            if not fallback:
                raise
            response = await self._try_fallback(messages, primary_exc, temperature, max_tokens, **kwargs)

        latency_ms = int((time.perf_counter() - start) * 1000)
        await self._log_usage(response, project_id, user_id, latency_ms)
        return response

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        provider_name = ProviderFactory.resolve_provider(model)
        provider = ProviderFactory.get(provider_name)
        async for chunk in provider.stream(
            messages, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs
        ):
            yield chunk

    def list_all_models(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for name in ("openai", "gemini", "claude", "ollama"):
            try:
                result[name] = ProviderFactory.get(name).list_models()
            except Exception:
                result[name] = []
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    async def _try_fallback(
        self,
        messages: list[ChatMessage],
        original_error: Exception,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> CompletionResponse:
        for fb_provider, fb_model in _FALLBACK_CHAIN:
            try:
                logger.info("Trying fallback: %s / %s", fb_provider, fb_model)
                provider = ProviderFactory.get(fb_provider)
                return await provider.complete(
                    messages, model=fb_model, temperature=temperature, max_tokens=max_tokens, **kwargs
                )
            except Exception as exc:
                logger.warning("Fallback %s / %s also failed: %s", fb_provider, fb_model, exc)
        raise RuntimeError("All providers failed") from original_error

    async def _log_usage(
        self,
        response: CompletionResponse,
        project_id: Optional[uuid.UUID],
        user_id: Optional[uuid.UUID],
        latency_ms: int,
    ) -> None:
        """Persist usage to DB if a session is available."""
        if self._db is None:
            return
        try:
            from app.models.usage import UsageLog  # lazy import to avoid circular deps
            log = UsageLog(
                project_id=project_id,
                user_id=user_id,
                provider=response.provider,
                model=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                total_tokens=response.total_tokens,
                latency_ms=latency_ms,
                created_at=datetime.now(timezone.utc),
            )
            self._db.add(log)
            self._db.commit()
        except Exception as exc:
            logger.error("Usage logging failed: %s", exc)
