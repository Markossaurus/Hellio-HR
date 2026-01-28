"""Ollama LLM provider implementation."""
import time
import httpx
from typing import Optional

from . import LLMProvider, LLMRequest, LLMResponse
from ...config import settings


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    async def generate(self, request: LLMRequest, prompt_version: str) -> LLMResponse:
        """Generate a response using Ollama API."""
        start_time = time.time()
        
        # Prepare the prompt
        full_prompt = request.prompt
        if request.system_prompt:
            full_prompt = f"{request.system_prompt}\n\n{request.prompt}"
        
        # Estimate tokens (rough approximation: chars / 4)
        token_estimate_in = len(full_prompt) // 4
        
        # Call Ollama API
        payload = {
            "model": settings.llm_model,
            "prompt": full_prompt,
            "stream": False,
        }
        
        if request.max_tokens:
            payload["options"] = {"num_predict": request.max_tokens}
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        content = result.get("response", "")
        token_estimate_out = len(content) // 4
        
        return LLMResponse(
            content=content,
            provider="ollama",
            model=settings.llm_model,
            prompt_version=prompt_version,
            token_estimate_in=token_estimate_in,
            token_estimate_out=token_estimate_out,
            elapsed_ms=elapsed_ms,
            cost_estimate_usd=0.0,  # Ollama is free
        )
