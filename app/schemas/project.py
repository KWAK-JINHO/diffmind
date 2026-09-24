# app/schemas/project.py
from typing import Optional
from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    name: str = Field(description="프로젝트 고유 식별자/이름")
    path: str = Field(description="프로젝트 로컬 파일시스템 경로")
    file_count: int = Field(description="프로젝트 내 마크다운(.md) 파일 개수")
    commit_count: int = Field(description="프로젝트 Git 커밋 총 개수")
    last_modified: Optional[str] = Field(default=None, description="최근 수정 일시")


class ProjectCreateRequest(BaseModel):
    name: str = Field(
        description="생성할 프로젝트 이름 (영문자, 숫자, 밑줄, 하이픈만 허용)",
        min_length=1,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_\-]+$"
    )
    description: Optional[str] = Field(default=None, description="프로젝트 설명")


class GitHubImportRequest(BaseModel):
    repo_url: str = Field(description="GitHub 저장소 URL (예: https://github.com/owner/repo)")
    branch: Optional[str] = Field(default=None, description="임포트할 브랜치 명 (기본값: 원격 기본 브랜치)")


class LocalImportRequest(BaseModel):
    source_path: str = Field(description="임포트할 로컬 디렉터리 절대 경로 (예: /Users/username/ObsidianNotes)")


class ImportResult(BaseModel):
    success: bool
    project_name: str
    imported_files: int
    commit_hash: str
    message: str
    toc: dict[str, list[str]] = Field(description="임포트 완료 후 즉시 갱신된 H1~H3 목차 맵")
