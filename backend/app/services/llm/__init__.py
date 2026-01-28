"""LLM provider interface and implementations."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMRequest:
    """Request to an LLM provider."""
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = None


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
        pass


def get_provider(name: str) -> LLMProvider:
    """Factory function to get LLM provider by name."""
    if name == "ollama":
        from .ollama import OllamaProvider
        return OllamaProvider()
    raise ValueError(f"Unknown LLM provider: {name}")
