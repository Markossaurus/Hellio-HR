"""Tests for Ollama LLM provider."""
import pytest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel


class CVExtractionSchema(BaseModel):
    name: str
    value: str


@pytest.fixture(autouse=True)
def mock_ollama_import():
    """Mock ollama import for all tests."""
    mock_chat = MagicMock()
    with patch.dict("sys.modules", {"ollama": MagicMock(chat=mock_chat)}):
        yield mock_chat


@pytest.mark.asyncio
async def test_get_provider_returns_ollama():
    from app.services.llm import get_provider
    
    provider = get_provider("ollama")
    assert provider is not None
    assert provider.__class__.__name__ == "OllamaProvider"


@pytest.mark.asyncio
async def test_ollama_requires_schema():
    from app.services.llm import get_provider, LLMRequest
    
    provider = get_provider("ollama")
    request = LLMRequest(prompt="test")
    
    with pytest.raises(ValueError, match="Schema is required"):
        await provider.generate(request, prompt_version="v1")


@pytest.mark.asyncio
async def test_ollama_generates_json_with_schema(mock_ollama_import):
    from app.services.llm import get_provider, LLMRequest
    
    mock_ollama_import.return_value = {
        "message": {
            "content": '{"name": "test", "value": "result"}'
        }
    }
    
    provider = get_provider("ollama")
    request = LLMRequest(
        prompt="Extract data",
        system_prompt="You are a helper",
        schema=CVExtractionSchema,
        max_tokens=500
    )
    
    response = await provider.generate(request, prompt_version="v1")
    
    assert response.content == '{"name": "test", "value": "result"}'
    assert response.provider == "ollama"
    assert response.model == "llama3.2"
    assert response.token_estimate_in > 0
    assert response.token_estimate_out > 0
    assert response.elapsed_ms >= 0
    assert response.cost_estimate_usd == 0.0
    
    mock_ollama_import.assert_called_once()
    call_kwargs = mock_ollama_import.call_args[1]
    assert call_kwargs["model"] == "llama3.2"
    assert len(call_kwargs["messages"]) == 2
    assert call_kwargs["messages"][0]["role"] == "system"
    assert call_kwargs["messages"][1]["role"] == "user"
    assert "format" in call_kwargs
    assert call_kwargs["options"]["temperature"] == 0


@pytest.mark.asyncio
async def test_ollama_handles_api_errors(mock_ollama_import):
    from app.services.llm import get_provider, LLMRequest
    
    mock_ollama_import.side_effect = ConnectionError("Cannot connect")
    
    provider = get_provider("ollama")
    request = LLMRequest(prompt="test", schema=CVExtractionSchema)
    
    with pytest.raises(RuntimeError, match="Ollama API error"):
        await provider.generate(request, prompt_version="v1")
