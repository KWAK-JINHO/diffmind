# app/routers/settings_router.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings, update_env_settings
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])


def mask_key(key: Optional[str]) -> str:
    if not key:
        return ""
    clean = key.strip()
    if len(clean) <= 8:
        return "••••••••"
    return f"{clean[:6]}...{clean[-4:]}"


@router.get("", response_model=SettingsResponse, summary="현재 LLM 및 API 설정 상태 조회")
async def get_current_settings(settings: Settings = Depends(get_settings)) -> SettingsResponse:
    """
    현재 설정된 LLM 제공자, 모델, API 키 등록 여부 및 마스킹된 키 정보를 반환합니다.
    실제 원본 API 키는 보안상 노출되지 않습니다.
    """
    return SettingsResponse(
        llm_provider=settings.LLM_PROVIDER,
        gemini_api_key_set=bool(settings.GEMINI_API_KEY),
        gemini_api_key_masked=mask_key(settings.GEMINI_API_KEY),
        gemini_model=settings.GEMINI_MODEL,
        openai_api_key_set=bool(settings.OPENAI_API_KEY),
        openai_api_key_masked=mask_key(settings.OPENAI_API_KEY),
        openai_model=settings.OPENAI_MODEL,
        openai_base_url=settings.OPENAI_BASE_URL,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        ollama_model=settings.OLLAMA_MODEL,
    )


@router.post("", response_model=SettingsResponse, summary="LLM 및 API 키 설정 업데이트 (.env 반영)")
async def update_settings(
    payload: SettingsUpdateRequest,
    current_settings: Settings = Depends(get_settings),
) -> SettingsResponse:
    """
    사용자가 UI에서 입력한 API 키 및 설정을 .env 파일에 안전하게 원자적으로 반영하고,
    애플리케이션 메모리 캐시를 즉시 갱신합니다.
    """
    updates: dict[str, str] = {}

    if payload.llm_provider is not None and payload.llm_provider.strip():
        valid_providers = ("google", "openai", "ollama", "custom")
        clean_provider = payload.llm_provider.strip().lower()
        if clean_provider not in valid_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 LLM 제공자입니다. ({', '.join(valid_providers)} 중 선택)"
            )
        updates["LLM_PROVIDER"] = clean_provider

    if payload.gemini_api_key is not None:
        updates["GEMINI_API_KEY"] = payload.gemini_api_key.strip()

    if payload.gemini_model is not None and payload.gemini_model.strip():
        updates["GEMINI_MODEL"] = payload.gemini_model.strip()

    if payload.openai_api_key is not None:
        updates["OPENAI_API_KEY"] = payload.openai_api_key.strip()

    if payload.openai_model is not None and payload.openai_model.strip():
        updates["OPENAI_MODEL"] = payload.openai_model.strip()

    if payload.openai_base_url is not None:
        updates["OPENAI_BASE_URL"] = payload.openai_base_url.strip()

    if payload.ollama_base_url is not None and payload.ollama_base_url.strip():
        updates["OLLAMA_BASE_URL"] = payload.ollama_base_url.strip()

    if payload.ollama_model is not None and payload.ollama_model.strip():
        updates["OLLAMA_MODEL"] = payload.ollama_model.strip()

    if updates:
        try:
            update_env_settings(updates)
            logger.info("Updated .env settings successfully: keys=%s", list(updates.keys()))
        except Exception as e:
            logger.error("Failed to update .env: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f".env 파일 갱신 중 오류가 발생했습니다: {str(e)}"
            )

    new_settings = get_settings()
    return SettingsResponse(
        llm_provider=new_settings.LLM_PROVIDER,
        gemini_api_key_set=bool(new_settings.GEMINI_API_KEY),
        gemini_api_key_masked=mask_key(new_settings.GEMINI_API_KEY),
        gemini_model=new_settings.GEMINI_MODEL,
        openai_api_key_set=bool(new_settings.OPENAI_API_KEY),
        openai_api_key_masked=mask_key(new_settings.OPENAI_API_KEY),
        openai_model=new_settings.OPENAI_MODEL,
        openai_base_url=new_settings.OPENAI_BASE_URL,
        ollama_base_url=new_settings.OLLAMA_BASE_URL,
        ollama_model=new_settings.OLLAMA_MODEL,
    )
