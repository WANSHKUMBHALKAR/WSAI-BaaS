import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ai_gateway.base import ChatMessage, CompletionResponse
from app.services.ai_gateway.openai_provider import OpenAIProvider
from app.services.ai_gateway.gemini_provider import GeminiProvider
from app.services.ai_gateway.claude_provider import ClaudeProvider
from app.services.ai_gateway.gateway import AIGateway

@pytest.mark.asyncio
async def test_openai_provider_complete():
    provider = OpenAIProvider()
    
    mock_choice = MagicMock()
    mock_choice.message.content = "Hello from OpenAI"
    mock_choice.finish_reason = "stop"
    
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 15
    mock_usage.total_tokens = 25
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    mock_response.model = "gpt-4o"
    mock_response.model_dump.return_value = {"id": "chatcmpl-123"}
    
    # Mock the AsyncOpenAI chat completions create method
    provider._client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    messages = [ChatMessage(role="user", content="Hi")]
    res = await provider.complete(messages=messages, model="gpt-4o")
    
    assert isinstance(res, CompletionResponse)
    assert res.content == "Hello from OpenAI"
    assert res.prompt_tokens == 10
    assert res.completion_tokens == 15
    assert res.total_tokens == 25
    assert res.provider == "openai"

@pytest.mark.asyncio
async def test_gemini_provider_complete():
    with patch("google.generativeai.configure") as mock_conf:
        provider = GeminiProvider()
        
        mock_response = MagicMock()
        mock_response.text = "Hello from Gemini"
        mock_response.usage_metadata.prompt_token_count = 5
        mock_response.usage_metadata.candidates_token_count = 8
        
        mock_chat = MagicMock()
        mock_chat.send_message_async = AsyncMock(return_value=mock_response)
        
        with patch("google.generativeai.GenerativeModel") as mock_model:
            mock_model.return_value.start_chat.return_value = mock_chat
            
            messages = [ChatMessage(role="user", content="Hi")]
            res = await provider.complete(messages=messages, model="gemini-1.5-flash")
            
            assert res.content == "Hello from Gemini"
            assert res.prompt_tokens == 5
            assert res.completion_tokens == 8
            assert res.total_tokens == 13
            assert res.provider == "gemini"

@pytest.mark.asyncio
async def test_claude_provider_complete():
    provider = ClaudeProvider()
    
    mock_response_data = {
        "content": [{"text": "Hello from Claude"}],
        "usage": {"input_tokens": 12, "output_tokens": 18},
        "stop_reason": "end_turn",
        "model": "claude-sonnet-4-5"
    }
    
    # Mock httpx AsyncClient post
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response_data
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp
        
        messages = [ChatMessage(role="user", content="Hi")]
        res = await provider.complete(messages=messages, model="claude-sonnet-4-5")
        
        assert res.content == "Hello from Claude"
        assert res.prompt_tokens == 12
        assert res.completion_tokens == 18
        assert res.total_tokens == 30
        assert res.provider == "claude"
