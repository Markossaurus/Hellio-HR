"""Shared LLM provider types."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class LLMRequest:
    """Request to an LLM provider."""
    prompt: str
    system_prompt: str | None = None
    max_tokens: int | None = None
    schema: type[BaseModel] | None = None


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    provider: str
    model: str
    prompt_version: str
    token_estimate_in: int
    token_estimate_out: int
    elapsed_ms: int
    cost_estimate_usd: float


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, request: LLMRequest, prompt_version: str) -> LLMResponse:
        """Generate a response from the LLM."""
        raise NotImplementedError
