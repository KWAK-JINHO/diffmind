from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """Provider-neutral request data for text and multimodal prompts."""

    prompt: str
    image_bytes: bytes | None = None
    mime_type: str = "image/png"
    response_model: type[BaseModel] | None = None
    temperature: float = 0.2


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Normalized provider response metadata used by application services."""

    text: str
    provider: str
    model: str


class BaseLLMClient(ABC):
    """Common contract implemented by every supported LLM provider."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the stable provider identifier."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the configured model identifier."""

    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate one normalized response for a text or image request."""

    @abstractmethod
    def stream_response(self, request: LLMRequest) -> AsyncIterator[str]:
        """Yield response text chunks for a streaming request."""
