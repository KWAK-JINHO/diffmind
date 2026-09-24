# app/schemas/file.py
from pydantic import BaseModel, Field


class FileContentResponse(BaseModel):
    """Schema for individual knowledge file content and metadata."""
    project: str = Field(..., description="프로젝트 명")
    path: str = Field(..., description="프로젝트 루트 기준 상대 파일 경로")
    content: str = Field(..., description="마크다운 파일 전체 원문 텍스트")
    headings: list[str] = Field(default_factory=list, description="추출된 H1~H3 헤딩 목록")
    size_bytes: int = Field(..., description="파일 크기(바이트)")
    modified_at: float = Field(..., description="최종 수정 시각 타임스탬프")
