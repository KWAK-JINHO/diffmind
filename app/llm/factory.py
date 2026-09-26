from enum import StrEnum
from typing import assert_never

from app.config import Settings
from app.llm.base import BaseLLMClient
from app.llm.gemini_client import GeminiClient
from app.llm.openai_client import OpenAIClient


class LLMProvider(StrEnum):
    GOOGLE = "google"
    OPENAI = "openai"
    OLLAMA = "ollama"
    CUSTOM = "custom"
    OPENAI_COMPATIBLE = "openai_compatible"


class LLMConfigurationError(ValueError):
    """Raised when the selected provider lacks the required configuration."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        self.message = message
        super().__init__(message)


class UnsupportedLLMProviderError(LLMConfigurationError):
    """Raised when a configured provider is not supported by the factory."""


class LLMFactory:
    """Create the one provider client selected by application settings."""

    @staticmethod
    def create(settings: Settings) -> BaseLLMClient:
        provider_value = settings.LLM_PROVIDER.strip().lower()
        try:
            provider = LLMProvider(provider_value)
        except ValueError as exc:
            raise UnsupportedLLMProviderError(
                provider_value,
                f"Unsupported LLM provider: {provider_value}",
            ) from exc

        match provider:
            case LLMProvider.GOOGLE:
                if not settings.GEMINI_API_KEY:
                    raise LLMConfigurationError(
                        provider.value,
                        "Neither GEMINI_API_KEY nor OPENAI_API_KEY is configured. "
                        "Please configure an API key in .env to use LLM analysis.",
                    )
                return GeminiClient(
                    api_key=settings.GEMINI_API_KEY,
                    model=settings.GEMINI_MODEL,
                )
            case LLMProvider.OPENAI:
                if not settings.OPENAI_API_KEY:
                    raise LLMConfigurationError(
                        provider.value,
                        "OPENAI_API_KEY is required for OpenAI LLM analysis.",
                    )
                return OpenAIClient(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL,
                    model=settings.OPENAI_MODEL,
                )
            case LLMProvider.OLLAMA:
                return OpenAIClient(
                    api_key="ollama",
                    base_url=settings.OLLAMA_BASE_URL,
                    model=settings.OLLAMA_MODEL,
                    provider_name=provider.value,
                )
            case LLMProvider.CUSTOM | LLMProvider.OPENAI_COMPATIBLE:
                return OpenAIClient(
                    api_key=settings.OPENAI_API_KEY or "custom",
                    base_url=settings.OPENAI_BASE_URL,
                    model=settings.OPENAI_MODEL,
                    provider_name=provider.value,
                )
            case unreachable:
                assert_never(unreachable)
