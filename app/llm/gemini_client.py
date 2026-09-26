import logging
from functools import partial
from typing import Final

import anyio

from app.llm.base import BaseLLMClient, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

FALLBACK_MODEL: Final = "gemini-3.5-flash"


class GeminiClient(BaseLLMClient):
    """Google Gemini adapter for structured, text, and image requests."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def model_name(self) -> str:
        return self._model

    def _build_contents(self, request: LLMRequest):
        from google.genai import types

        if request.image_bytes is None:
            return [request.prompt]
        part = types.Part.from_bytes(
            data=request.image_bytes,
            mime_type=request.mime_type,
        )
        return [part, request.prompt]

    def _build_config(self, request: LLMRequest):
        from google.genai import types

        config = {"temperature": request.temperature}
        if request.response_model is not None:
            config.update(
                response_mime_type="application/json",
                response_schema=request.response_model,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            )
        return types.GenerateContentConfig(**config)

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        from google import genai

        client = genai.Client(api_key=self._api_key)
        contents = self._build_contents(request)
        config = self._build_config(request)
        try:
            response = await anyio.to_thread.run_sync(
                partial(
                    client.models.generate_content,
                    model=self._model,
                    contents=contents,
                    config=config,
                )
            )
            return LLMResponse(
                text=response.text or "",
                provider=self.provider_name,
                model=self._model,
            )
        except Exception as exc:  # noqa: BLE001 - provider SDK boundary
            if not self._is_temporary_unavailable(exc):
                raise
            logger.warning(
                "%s is unavailable; retrying with %s",
                self._model,
                FALLBACK_MODEL,
            )
            response = await anyio.to_thread.run_sync(
                partial(
                    client.models.generate_content,
                    model=FALLBACK_MODEL,
                    contents=contents,
                    config=config,
                )
            )
            return LLMResponse(
                text=response.text or "",
                provider=self.provider_name,
                model=FALLBACK_MODEL,
            )

    async def stream_response(self, request: LLMRequest):
        from google import genai

        client = genai.Client(api_key=self._api_key)
        stream = await anyio.to_thread.run_sync(
            partial(
                client.models.generate_content_stream,
                model=self._model,
                contents=self._build_contents(request),
                config=self._build_config(request),
            )
        )
        for chunk in stream:
            text = chunk.text or ""
            if text:
                yield text

    @staticmethod
    def _is_temporary_unavailable(error: Exception) -> bool:
        message = str(error)
        return "503" in message or "UNAVAILABLE" in message
