import base64
import logging
from functools import partial

import anyio

from app.llm.base import BaseLLMClient, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI-compatible adapter used by OpenAI, Ollama, and custom endpoints."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        provider_name: str = "openai",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._provider_name = provider_name

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self._model

    def _create_client(self):
        import openai

        return openai.OpenAI(api_key=self._api_key, base_url=self._base_url)

    @staticmethod
    def _build_messages(request: LLMRequest):
        if request.image_bytes is None:
            return [{"role": "user", "content": request.prompt}]
        encoded = base64.b64encode(request.image_bytes).decode("utf-8")
        data_url = f"data:{request.mime_type};base64,{encoded}"
        return [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": request.prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ]

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        client = self._create_client()
        messages = self._build_messages(request)
        if request.response_model is not None:
            try:
                response = await anyio.to_thread.run_sync(
                    partial(
                        client.beta.chat.completions.parse,
                        model=self._model,
                        messages=messages,
                        response_format=request.response_model,
                        temperature=request.temperature,
                    )
                )
                parsed = response.choices[0].message.parsed
                if parsed is not None:
                    return LLMResponse(
                        text=parsed.model_dump_json(),
                        provider=self.provider_name,
                        model=self._model,
                    )
            except Exception as exc:  # noqa: BLE001 - provider SDK boundary
                logger.warning("Structured response failed; using JSON fallback: %s", exc)

        response = await anyio.to_thread.run_sync(
            partial(
                client.chat.completions.create,
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": "Output valid JSON when a schema is requested.",
                    },
                    *messages,
                ],
                response_format={"type": "json_object"}
                if request.response_model is not None
                else None,
                temperature=request.temperature,
            )
        )
        return LLMResponse(
            text=response.choices[0].message.content or "",
            provider=self.provider_name,
            model=self._model,
        )

    async def stream_response(self, request: LLMRequest):
        client = self._create_client()
        stream = await anyio.to_thread.run_sync(
            partial(
                client.chat.completions.create,
                model=self._model,
                messages=self._build_messages(request),
                temperature=request.temperature,
                stream=True,
            )
        )
        for chunk in stream:
            text = chunk.choices[0].delta.content or ""
            if text:
                yield text
