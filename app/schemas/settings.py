# app/schemas/settings.py
from typing import Optional
from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    llm_provider: str = Field(description="현재 설정된 LLM 제공자")
    gemini_api_key_set: bool = Field(description="Gemini API Key 설정 여부")
    gemini_api_key_masked: str = Field(description="마스킹된 Gemini API Key")
    gemini_model: str = Field(description="Gemini 모델")
    openai_api_key_set: bool = Field(description="OpenAI API Key 설정 여부")
    openai_api_key_masked: str = Field(description="마스킹된 OpenAI API Key")
    openai_model: str = Field(description="OpenAI 모델")
    openai_base_url: Optional[str] = Field(default=None, description="OpenAI 호환 Base URL")
    ollama_base_url: str = Field(description="Ollama Base URL")
    ollama_model: str = Field(description="Ollama 모델")


class SettingsUpdateRequest(BaseModel):
    llm_provider: Optional[str] = Field(default=None, description="LLM 제공자 ('google', 'openai', 'ollama', 'custom')")
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API Key (새로 입력할 때만 전송)")
    gemini_model: Optional[str] = Field(default=None, description="Gemini 모델")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key (새로 입력할 때만 전송)")
    openai_model: Optional[str] = Field(default=None, description="OpenAI 모델")
    openai_base_url: Optional[str] = Field(default=None, description="OpenAI 호환 Base URL")
    ollama_base_url: Optional[str] = Field(default=None, description="Ollama Base URL")
    ollama_model: Optional[str] = Field(default=None, description="Ollama 모델")
