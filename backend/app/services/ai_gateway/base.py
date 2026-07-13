"""
Base provider interface for all LLM backends.
Every provider must implement this contract.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list] = None


@dataclass
class CompletionResponse:
    content: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str = "stop"
    raw: dict = field(default_factory=dict)


class BaseProvider(ABC):
    """Abstract base class that every LLM provider must subclass."""

    provider_name: str = "base"

    @abstractmethod
    async def complete(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> CompletionResponse:
        """Return a single completion."""

    @abstractmethod
    async def stream(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Yield token chunks for streaming responses."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return the models available from this provider."""
