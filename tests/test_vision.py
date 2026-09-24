# tests/test_vision.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.config import Settings
from app.ingestion.vision_service import VisionService


@pytest.mark.asyncio
async def test_vision_service_no_key_error():
    settings = Settings(
        KB_PATH="./knowledge_base",
        LLM_PROVIDER="google",
        GEMINI_API_KEY="",
        OPENAI_API_KEY=""
    )
    service = VisionService(settings=settings)

    with pytest.raises(ValueError, match="Neither GEMINI_API_KEY nor OPENAI_API_KEY is configured"):
        await service.extract_markdown_from_image(b"fake_image_bytes", "image/png")


@pytest.mark.asyncio
async def test_vision_service_empty_bytes():
    settings = Settings(
        KB_PATH="./knowledge_base",
        GEMINI_API_KEY="dummy_key"
    )
    service = VisionService(settings=settings)

    with pytest.raises(ValueError, match="Empty image data"):
        await service.extract_markdown_from_image(b"", "image/png")


@pytest.mark.asyncio
async def test_vision_service_gemini_flow():
    settings = Settings(
        KB_PATH="./knowledge_base",
        LLM_PROVIDER="google",
        GEMINI_API_KEY="test_gemini_key",
        GEMINI_MODEL="gemini-2.5-flash"
    )
    service = VisionService(settings=settings)

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "# Extracted Markdown\n## Subtopic\nNotes from diagram."
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        result = await service.extract_markdown_from_image(b"png_data", "image/png")
        assert "# Extracted Markdown" in result
        assert "Notes from diagram." in result


@pytest.mark.asyncio
async def test_vision_service_openai_flow():
    settings = Settings(
        KB_PATH="./knowledge_base",
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="test_openai_key",
        OPENAI_MODEL="gpt-4o"
    )
    service = VisionService(settings=settings)

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "# OpenAI Extracted\nOCR content."
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_resp

    with patch("openai.OpenAI", return_value=mock_client):
        result = await service.extract_markdown_from_image(b"jpeg_data", "image/jpeg")
        assert "# OpenAI Extracted" in result


@pytest.mark.asyncio
async def test_vision_service_ollama_flow():
    settings = Settings(
        KB_PATH="./knowledge_base",
        LLM_PROVIDER="ollama",
        OLLAMA_BASE_URL="http://localhost:11434/v1",
        OLLAMA_MODEL="llama3.2-vision"
    )
    service = VisionService(settings=settings)

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "# Ollama Vision Extracted"
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_resp

    with patch("openai.OpenAI", return_value=mock_client) as mock_openai_cls:
        result = await service.extract_markdown_from_image(b"png_data", "image/png")
        assert "# Ollama Vision Extracted" in result
        mock_openai_cls.assert_called_with(api_key="ollama", base_url="http://localhost:11434/v1")
