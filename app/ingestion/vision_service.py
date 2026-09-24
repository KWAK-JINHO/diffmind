# app/ingestion/vision_service.py
import base64
import logging
from typing import Optional
from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

VISION_PROMPT = """
당신은 기술 지식 엔지니어링 전문가입니다.
제공된 이미지(강의 노트, 다이어그램, 코드 스크린샷, 도해 등)를 정밀 분석하여 완성도 높은 마크다운(Markdown) 문서로 변환해 주세요.

작성 규칙:
1. 제목, 소제목을 H1~H3(#, ##, ###)을 활용해 논리적 위계로 정리합니다.
2. 텍스트는 누락 없이 충실하게 전사하되 문맥을 자연스럽게 정돈합니다.
3. 코드나 명령어는 해당 언어의 코드 블록(예: ```python, ```bash 등)으로 작성합니다.
4. 다이어그램이나 도표는 Markdown 표(Table) 또는 순서도/목록 형식으로 구조화합니다.
5. 불필요한 메타 설명 없이 순수 마크다운 본문만 출력하세요.
""".strip()


class VisionService:
    """
    Multimodal OCR and image knowledge extraction service.
    Supports Google GenAI and OpenAI Vision.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def extract_markdown_from_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png"
    ) -> str:
        """
        Extracts structured markdown knowledge from image binary.
        """
        if not image_bytes:
            raise ValueError("Empty image data provided.")

        if not self.settings.GEMINI_API_KEY and not self.settings.OPENAI_API_KEY:
            raise ValueError(
                "Neither GEMINI_API_KEY nor OPENAI_API_KEY is configured in environment. "
                "Please configure an API key in .env to use vision analysis."
            )

        provider = self.settings.LLM_PROVIDER.lower()

        # Check provider availability and route accordingly
        if provider == "google" and self.settings.GEMINI_API_KEY:
            return await self._extract_with_gemini(image_bytes, mime_type)
        elif provider == "openai" and self.settings.OPENAI_API_KEY:
            return await self._extract_with_openai(image_bytes, mime_type)
        elif self.settings.GEMINI_API_KEY:
            return await self._extract_with_gemini(image_bytes, mime_type)
        elif self.settings.OPENAI_API_KEY:
            return await self._extract_with_openai(image_bytes, mime_type)
        else:
            raise ValueError(
                "Neither GEMINI_API_KEY nor OPENAI_API_KEY is configured in environment. "
                "Please configure an API key in .env to use vision analysis."
            )

    async def _extract_with_gemini(self, image_bytes: bytes, mime_type: str) -> str:
        if not self.settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required for Google GenAI vision service.")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
        
        # Prepare multimodal request parts
        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = client.models.generate_content(
            model=self.settings.GEMINI_MODEL,
            contents=[part, VISION_PROMPT]
        )
        return response.text or ""

    async def _extract_with_openai(self, image_bytes: bytes, mime_type: str) -> str:
        if not self.settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI vision service.")

        import openai

        client = openai.OpenAI(api_key=self.settings.OPENAI_API_KEY)
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64_image}"

        response = client.chat.completions.create(
            model=self.settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
