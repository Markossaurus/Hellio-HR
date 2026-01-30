"""LLM provider interface and implementations."""
from app.services.llm.base import LLMProvider, LLMRequest, LLMResponse


def get_provider(name: str) -> LLMProvider:
    """Get LLM provider by name."""
    if name == "ollama":
        from app.services.llm.ollama import OllamaProvider
        return OllamaProvider()
    raise ValueError(f"Unknown LLM provider: {name}")


__all__ = ["LLMProvider", "LLMRequest", "LLMResponse", "get_provider"]
