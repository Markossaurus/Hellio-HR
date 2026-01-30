"""Ollama LLM provider with structured JSON output."""
import time
from typing import Any

from ollama import Client
from pydantic import BaseModel

from app.config import settings
from app.services.llm.base import LLMProvider, LLMRequest, LLMResponse


class OllamaProvider(LLMProvider):
    """Ollama provider with enforced JSON schema output."""

    def __init__(self):
        self.client = Client(host=settings.ollama_base_url)

    async def generate(self, request: LLMRequest, prompt_version: str) -> LLMResponse:
        """Generate JSON response using Ollama with schema enforcement."""
        start_time = time.time()

        if not request.schema:
            raise ValueError("Schema is required - Ollama must always return structured JSON")

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        full_prompt = f"{request.system_prompt}\n\n{request.prompt}" if request.system_prompt else request.prompt
        token_estimate_in = len(full_prompt) // 4

        options: dict[str, Any] = {"temperature": 0.3}
        if request.max_tokens:
            options["num_predict"] = request.max_tokens

        try:
            response_data = self.client.chat(
                model=settings.llm_model,
                messages=messages,
                format=request.schema.model_json_schema(),
                options=options,
            )
            
            content = response_data["message"]["content"]
            
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}") from e

        elapsed_ms = int((time.time() - start_time) * 1000)
        token_estimate_out = len(content) // 4

        return LLMResponse(
            content=content,
            provider="ollama",
            model=settings.llm_model,
            prompt_version=prompt_version,
            token_estimate_in=token_estimate_in,
            token_estimate_out=token_estimate_out,
            elapsed_ms=elapsed_ms,
            cost_estimate_usd=0.0,
        )
