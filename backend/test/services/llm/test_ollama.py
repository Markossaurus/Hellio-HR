"""Tests for Ollama LLM provider."""
import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.services.llm import get_provider, LLMRequest


@pytest.mark.asyncio
async def test_get_provider_returns_ollama():
    """Test that get_provider returns OllamaProvider instance."""
    provider = get_provider("ollama")
    assert provider is not None
    assert provider.__class__.__name__ == "OllamaProvider"


@pytest.mark.asyncio
async def test_ollama_provider_generates_response():
    """Test OllamaProvider.generate with mocked HTTP response."""
    provider = get_provider("ollama")
    
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "response": "This is a test response from Ollama"
    }
    mock_response.raise_for_status = AsyncMock()
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        request = LLMRequest(
            prompt="Extract skills from this CV",
            system_prompt="You are a helpful assistant",
            max_tokens=500
        )
        
        response = await provider.generate(request, prompt_version="cv_extraction_v1")
        
        assert response.content == "This is a test response from Ollama"
        assert response.provider == "ollama"
        assert response.model == "llama3.2"
        assert response.prompt_version == "cv_extraction_v1"
        assert response.token_estimate_in > 0
        assert response.token_estimate_out > 0
        assert response.elapsed_ms > 0
        assert response.cost_estimate_usd == 0.0


@pytest.mark.asyncio
async def test_ollama_token_estimation():
    """Test that token estimation works (chars // 4)."""
    provider = get_provider("ollama")
    
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "response": "A" * 100  # 100 chars
    }
    mock_response.raise_for_status = AsyncMock()
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        request = LLMRequest(
            prompt="Test" * 25,  # 100 chars
        )
        
        response = await provider.generate(request, prompt_version="test_v1")
        
        # Should estimate ~25 tokens for 100 chars
        assert response.token_estimate_in == 25
        assert response.token_estimate_out == 25


@pytest.mark.asyncio
async def test_ollama_tracks_elapsed_time():
    """Test that elapsed time is tracked."""
    provider = get_provider("ollama")
    
    mock_response = AsyncMock()
    mock_response.json.return_value = {"response": "test"}
    mock_response.raise_for_status = AsyncMock()
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        request = LLMRequest(prompt="test")
        response = await provider.generate(request, prompt_version="v1")
        
        assert response.elapsed_ms >= 0


@pytest.mark.asyncio
async def test_ollama_connection_error_raises():
    """Test that connection errors are raised properly."""
    provider = get_provider("ollama")
    
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection failed")):
        request = LLMRequest(prompt="test")
        
        with pytest.raises(httpx.ConnectError):
            await provider.generate(request, prompt_version="v1")
