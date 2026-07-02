"""
LLM client abstraction. Claude is the default and recommended provider for
this codebase, called through Anthropic's official SDK. The interface is
intentionally minimal (one method: complete(prompt) -> text) so OPENAI,
GEMINI, or a local OLLAMA model can be dropped in by implementing the same
contract -- see OpenAIClient / OllamaClient below for the shape a swap-in
would take.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from app.config import get_settings
from app.utils.helpers import setup_logger

settings = get_settings()
logger = setup_logger("llm_service.claude_client")


class BaseLLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, max_tokens: int = 800) -> Tuple[str, int]:
        """Return (response_text, latency_ms)."""
        raise NotImplementedError


class ClaudeClient(BaseLLMClient):
    def __init__(self):
        from anthropic import Anthropic

        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    def complete(self, prompt: str, max_tokens: int = 800) -> Tuple[str, int]:
        start = time.time()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = int((time.time() - start) * 1000)
        text = "".join(block.text for block in response.content if block.type == "text")
        return text, latency_ms


class OpenAIClient(BaseLLMClient):  # pragma: no cover - optional path
    def __init__(self):
        from openai import OpenAI

        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def complete(self, prompt: str, max_tokens: int = 800) -> Tuple[str, int]:
        start = time.time()
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = int((time.time() - start) * 1000)
        return response.choices[0].message.content, latency_ms


class OllamaClient(BaseLLMClient):  # pragma: no cover - optional local path
    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def complete(self, prompt: str, max_tokens: int = 800) -> Tuple[str, int]:
        import httpx

        start = time.time()
        resp = httpx.post(
            f"{self.host}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=60.0,
        )
        latency_ms = int((time.time() - start) * 1000)
        return resp.json().get("response", ""), latency_ms


_client_instance: Optional[BaseLLMClient] = None


def get_llm_client() -> Optional[BaseLLMClient]:
    """Returns None (rather than raising) when no provider is configured, so
    callers can fall back to the deterministic reasoning generator instead
    of crashing a demo that hasn't set an API key yet."""
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    provider = settings.LLM_PROVIDER.lower()
    try:
        if provider == "claude" and settings.ANTHROPIC_API_KEY:
            _client_instance = ClaudeClient()
        elif provider == "openai" and settings.OPENAI_API_KEY:
            _client_instance = OpenAIClient()
        elif provider == "ollama":
            _client_instance = OllamaClient()
        else:
            logger.warning("No LLM provider configured -- falling back to rule-based reasoning.")
            return None
    except Exception as e:  # noqa: BLE001
        logger.warning(f"LLM client init failed ({e}); falling back to rule-based reasoning.")
        return None
    return _client_instance
