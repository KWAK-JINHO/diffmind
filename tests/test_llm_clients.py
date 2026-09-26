from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.llm.base import LLMRequest
from app.llm.factory import (
    LLMConfigurationError,
    LLMFactory,
    UnsupportedLLMProviderError,
)
from app.llm.gemini_client import GeminiClient
from app.llm.openai_client import OpenAIClient
from app.schemas.patch import LLMDecision


def test_factory_creates_gemini_client_for_google() -> None:
    settings = Settings(LLM_PROVIDER="google", GEMINI_API_KEY="gemini-test")

    client = LLMFactory.create(settings)

    assert isinstance(client, GeminiClient)
    assert client.model_name == settings.GEMINI_MODEL


@pytest.mark.parametrize("provider", ["openai", "ollama", "custom"])
def test_factory_creates_openai_compatible_client_for_provider(provider: str) -> None:
    settings = Settings(
        LLM_PROVIDER=provider,
        OPENAI_API_KEY="openai-test",
        OLLAMA_BASE_URL="http://localhost:11434/v1",
    )

    client = LLMFactory.create(settings)

    assert isinstance(client, OpenAIClient)


def test_factory_rejects_unknown_provider() -> None:
    settings = Settings(LLM_PROVIDER="unknown")

    with pytest.raises(UnsupportedLLMProviderError):
        LLMFactory.create(settings)


@pytest.mark.parametrize(
    ("provider", "api_key", "base_url", "model", "provider_name"),
    [
        ("openai", "openai-test", "https://api.openai.test/v1", "gpt-test", None),
        ("ollama", "ollama", "http://localhost:11434/v1", "llama-test", "ollama"),
        ("custom", "custom-test", "https://custom.test/v1", "custom-model", "custom"),
    ],
)
def test_factory_routes_openai_compatible_configuration(
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    provider_name: str | None,
) -> None:
    settings = Settings(
        LLM_PROVIDER=provider,
        OPENAI_API_KEY=api_key if provider != "ollama" else None,
        OPENAI_BASE_URL=base_url if provider != "ollama" else None,
        OPENAI_MODEL=model if provider != "ollama" else "gpt-default",
        OLLAMA_BASE_URL=base_url,
        OLLAMA_MODEL=model,
    )

    with patch("app.llm.factory.OpenAIClient") as client_class:
        LLMFactory.create(settings)

    expected = {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
    }
    if provider_name is not None:
        expected["provider_name"] = provider_name
    client_class.assert_called_once_with(**expected)


def test_factory_requires_openai_key() -> None:
    settings = Settings(LLM_PROVIDER="openai", OPENAI_API_KEY=None)

    with pytest.raises(LLMConfigurationError, match="OPENAI_API_KEY"):
        LLMFactory.create(settings)


@pytest.mark.asyncio
async def test_gemini_client_generates_response() -> None:
    mock_client = MagicMock()
    mock_response = MagicMock(text='{"answer": "ok"}')
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        client = GeminiClient(api_key="gemini-test", model="gemini-test-model")
        response = await client.generate_response(LLMRequest(prompt="hello"))

    assert response.text == '{"answer": "ok"}'
    assert response.provider == "google"
    assert response.model == "gemini-test-model"
    mock_client.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_openai_client_generates_structured_response() -> None:
    decision = LLMDecision(
        is_new_file=True,
        target_file_path="notes.md",
        target_heading="# Notes",
        original_snippet="",
        proposed_snippet="content",
        reason="new topic",
    )
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.parsed = decision
    mock_response = MagicMock(choices=[mock_choice])
    mock_client.beta.chat.completions.parse.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        client = OpenAIClient(api_key="openai-test", model="gpt-test")
        response = await client.generate_response(
            LLMRequest(prompt="hello", response_model=LLMDecision)
        )

    assert LLMDecision.model_validate_json(response.text) == decision
    assert response.provider == "openai"
    assert response.model == "gpt-test"
    mock_client.beta.chat.completions.parse.assert_called_once()


@pytest.mark.asyncio
async def test_gemini_client_streams_text_chunks() -> None:
    mock_client = MagicMock()
    mock_client.models.generate_content_stream.return_value = [
        MagicMock(text="one"),
        MagicMock(text="two"),
    ]

    with patch("google.genai.Client", return_value=mock_client):
        client = GeminiClient(api_key="gemini-test", model="gemini-test-model")
        chunks = [
            chunk
            async for chunk in client.stream_response(LLMRequest(prompt="hello"))
        ]

    assert chunks == ["one", "two"]


@pytest.mark.asyncio
async def test_gemini_client_retries_temporary_unavailability() -> None:
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [
        RuntimeError("503 UNAVAILABLE"),
        MagicMock(text="recovered"),
    ]

    with patch("google.genai.Client", return_value=mock_client):
        client = GeminiClient(api_key="gemini-test", model="gemini-test-model")
        response = await client.generate_response(LLMRequest(prompt="hello"))

    assert response.text == "recovered"
    assert response.model == "gemini-3.5-flash"
    assert mock_client.models.generate_content.call_count == 2


@pytest.mark.asyncio
async def test_openai_client_streams_text_chunks() -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="one"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="two"))]),
    ]

    with patch("openai.OpenAI", return_value=mock_client):
        client = OpenAIClient(api_key="openai-test", model="gpt-test")
        chunks = [
            chunk
            async for chunk in client.stream_response(LLMRequest(prompt="hello"))
        ]

    assert chunks == ["one", "two"]
