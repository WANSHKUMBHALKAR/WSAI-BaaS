"""Gemini provider via google-generativeai SDK."""
import logging
from typing import AsyncIterator

import google.generativeai as genai

from app.core.config import settings
from .base import BaseProvider, ChatMessage, CompletionResponse

logger = logging.getLogger(__name__)

SUPPORTED_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
]

class GeminiProvider(BaseProvider):
    provider_name = "gemini"

    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured; GeminiProvider will be unavailable")
            self._configured = False
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._configured = True

    @staticmethod
    def _convert_messages(messages: list[ChatMessage]) -> tuple[str, list[dict]]:
        """Separate system prompt from conversation history."""
        system_parts: list[str] = []
        history: list[dict] = []
        for m in messages:
            if m.role == "system":
                system_parts.append(m.content)
            elif m.role == "user":
                history.append({"role": "user", "parts": [m.content]})
            elif m.role == "assistant":
                history.append({"role": "model", "parts": [m.content]})
        system_instruction = "\n".join(system_parts) if system_parts else None
        return system_instruction, history

    async def complete(
        self,
        messages: list[ChatMessage],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> CompletionResponse:
        if not getattr(self, "_configured", True):
            raise RuntimeError("Gemini provider not configured. Set GEMINI_API_KEY to enable it.")

        system_instruction, history = self._convert_messages(messages)
        cfg = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        gemini_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction,
            generation_config=cfg,
        )
        chat = gemini_model.start_chat(history=history[:-1] if history else [])
        last_message = history[-1]["parts"][0] if history else ""
        response = await chat.send_message_async(last_message)

        prompt_tokens = response.usage_metadata.prompt_token_count or 0
        completion_tokens = response.usage_metadata.candidates_token_count or 0
        return CompletionResponse(
            content=response.text,
            model=model,
            provider=self.provider_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            finish_reason="stop",
            raw={},
        )

    async def stream(
        self,
        messages: list[ChatMessage],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        system_instruction, history = self._convert_messages(messages)
        cfg = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        gemini_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction,
            generation_config=cfg,
        )
        chat = gemini_model.start_chat(history=history[:-1] if history else [])
        last_message = history[-1]["parts"][0] if history else ""
        async for chunk in await chat.send_message_async(last_message, stream=True):
            if chunk.text:
                yield chunk.text

    def list_models(self) -> list[str]:
        return SUPPORTED_MODELS
