# app/schemas/patch.py
from typing import Optional
from pydantic import BaseModel, Field


class PatchProposal(BaseModel):
    is_new_file: bool = Field(description="새 파일 생성 여부")
    target_file_path: str = Field(description="지식 베이스 루트 기준 대상 파일 상대 경로 (예: kubernetes/cgroups.md)")
    target_heading: str = Field(description="삽입/수정 대상 헤딩 (예: ## cgroups v2 리소스 격리)")
    original_snippet: str = Field(description="기존 내용 중 기준이 되는 앵커 문단 (새 파일이거나 섹션 맨 뒤 추가 시 빈 문자열)")
    proposed_snippet: str = Field(description="새로 병합/수정될 완성형 마크다운 문단")
    unified_diff: str = Field(description="사용자 리뷰용 표준 Git Unified Diff 텍스트")
    reason: str = Field(description="해당 파일 및 헤딩을 선정한 AI의 분석 근거")


class PatchAcceptRequest(BaseModel):
    proposal: PatchProposal
    commit_message: Optional[str] = Field(default=None, description="커스텀 커밋 메시지 (미지정 시 자동 생성)")


class CommitResult(BaseModel):
    success: bool
    commit_hash: str
    message: str
    file_path: str


class LLMDecision(BaseModel):
    """Internal model for structured output from LLMs during patch synthesis."""
    is_new_file: bool = Field(
        description="True if a new markdown file should be created because no existing file fits."
    )
    target_file_path: str = Field(
        description="Relative file path within knowledge base (e.g., 'docker/storage.md' or existing file)."
    )
    target_heading: str = Field(
        description="Heading (e.g., '# Docker Overview' or '## Volume Driver') under which content should be placed."
    )
    original_snippet: str = Field(
        default="",
        description="Existing paragraph or block to be replaced. Empty string if appending to the heading or creating a new file."
    )
    proposed_snippet: str = Field(
        description="The full, well-structured markdown snippet to insert, replace, or initialize with."
    )
    reason: str = Field(
        description="Clear engineering explanation of why this file and heading location was chosen."
    )


class RecentDiffResponse(BaseModel):
    diff: str = Field(description="최근 Git 커밋의 diff 내용")


class TOCResponse(BaseModel):
    toc: dict[str, list[str]] = Field(description="지식 베이스 전체 파일 상대 경로와 각 파일의 H1~H3 헤딩 목록")
