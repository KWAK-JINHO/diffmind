# app/routers/knowledge_router.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.config import SecurityError, Settings, get_settings, validate_safe_path
from app.ingestion.vision_service import VisionService
from app.projects.project_service import ProjectService
from app.schemas.file import FileContentResponse
from app.schemas.patch import (
    CommitResult,
    PatchAcceptRequest,
    PatchProposal,
    RecentDiffResponse,
    TOCResponse,
)
from app.synthesis.scanner import extract_headings, scan_knowledge_base
from app.synthesis.synthesis_service import SynthesisService
from app.versioning.git_service import GitService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Knowledge Pipeline"])


def get_project_service(settings: Settings = Depends(get_settings)) -> ProjectService:
    return ProjectService(settings=settings)


def get_vision_service(settings: Settings = Depends(get_settings)) -> VisionService:
    return VisionService(settings=settings)


@router.post(
    "/propose",
    response_model=PatchProposal,
    summary="새 지식에 대한 파일 위치 선정 및 Git Unified Diff 제안 생성"
)
async def propose_patch(
    content: Optional[str] = Form(default=None, description="마크다운 텍스트 내용"),
    file: Optional[UploadFile] = File(default=None, description=".md 또는 텍스트 문서 파일"),
    image: Optional[UploadFile] = File(default=None, description="강의 노트나 다이어그램 스크린샷 이미지"),
    project: str = Form(default="default", description="대상 프로젝트 명"),
    project_service: ProjectService = Depends(get_project_service),
    vision_service: VisionService = Depends(get_vision_service),
    settings: Settings = Depends(get_settings),
) -> PatchProposal:
    """
    텍스트 본문(content), 마크다운 파일(file), 이미지 스크린샷(image) 중 제공된 입력을 분석하여
    지정된 프로젝트 지식 베이스의 최적 위치를 찾고 정밀한 Unified Diff 제안을 반환합니다.
    """
    accumulated_content: list[str] = []

    # 1. Process image input if provided
    if image is not None and image.filename:
        image_bytes = await image.read()
        if image_bytes:
            mime_type = image.content_type or "image/png"
            extracted_md = await vision_service.extract_markdown_from_image(image_bytes, mime_type)
            if extracted_md.strip():
                accumulated_content.append(extracted_md.strip())

    # 2. Process file input if provided
    if file is not None and file.filename:
        file_bytes = await file.read()
        if file_bytes:
            text_md = file_bytes.decode("utf-8", errors="replace").strip()
            if text_md:
                accumulated_content.append(text_md)

    # 3. Process direct text content if provided
    if content and content.strip():
        accumulated_content.append(content.strip())

    if not accumulated_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="적어도 하나의 유효한 입력('content' 텍스트, 'file' 마크다운 파일, 'image' 이미지)을 제공해야 합니다."
        )

    # Scoped project resolution
    project_path = project_service.get_project_path(project)
    synthesis_service = SynthesisService(kb_path=project_path, settings=settings)

    final_markdown = "\n\n".join(accumulated_content)
    proposal = await synthesis_service.propose_patch(final_markdown)
    return proposal


@router.post(
    "/accept",
    response_model=CommitResult,
    summary="검토된 PatchProposal 승인 및 원자적 파일 패치, Git 커밋 수행"
)
async def accept_patch(
    request: PatchAcceptRequest,
    project: str = Query(default="default", description="대상 프로젝트 명"),
    project_service: ProjectService = Depends(get_project_service),
    settings: Settings = Depends(get_settings),
) -> CommitResult:
    """
    사용자가 승인한 제안을 바탕으로 대상 프로젝트 내부의 원본 마크다운 파일을 원자적으로 수정/생성하고,
    해당 프로젝트의 Git CLI를 호출하여 스테이징(add) 및 커밋(commit)을 수행합니다.
    """
    proposal = request.proposal
    project_path = project_service.get_project_path(project)
    synthesis_service = SynthesisService(kb_path=project_path, settings=settings)
    git_service = GitService(kb_path=project_path)

    # 1. Apply atomic patch to filesystem within project
    synthesis_service.apply_patch(proposal)

    # 2. Stage file in project Git
    git_service.add(proposal.target_file_path)

    # 3. Generate meaningful commit message if not explicitly provided
    if request.commit_message and request.commit_message.strip():
        commit_msg = request.commit_message.strip()
    else:
        action = "create" if proposal.is_new_file else "update"
        commit_msg = f"docs: {action} {proposal.target_file_path} under '{proposal.target_heading}'"

    commit_hash = git_service.commit(commit_msg)

    return CommitResult(
        success=True,
        commit_hash=commit_hash,
        message=commit_msg,
        file_path=proposal.target_file_path
    )


@router.get(
    "/recent-diff",
    response_model=RecentDiffResponse,
    summary="가장 최근 Git 커밋된 Diff 내역 조회"
)
async def get_recent_diff(
    project: str = Query(default="default", description="대상 프로젝트 명"),
    project_service: ProjectService = Depends(get_project_service),
) -> RecentDiffResponse:
    """
    지정된 프로젝트 저장소의 최신 커밋 내역(git diff HEAD~1 HEAD)을 조회합니다.
    """
    project_path = project_service.get_project_path(project)
    git_service = GitService(kb_path=project_path)
    diff_text = git_service.get_recent_diff()
    return RecentDiffResponse(diff=diff_text)


@router.get(
    "/toc",
    response_model=TOCResponse,
    summary="현재 지식 베이스의 모든 마크다운 파일과 H1~H3 목차 목록 조회"
)
async def get_toc(
    project: str = Query(default="default", description="대상 프로젝트 명"),
    project_service: ProjectService = Depends(get_project_service),
) -> TOCResponse:
    """
    지정된 프로젝트 디렉터리의 모든 .md 파일과 H1~H3 헤딩 구조 트리를 반환합니다.
    """
    project_path = project_service.get_project_path(project)
    toc = scan_knowledge_base(project_path)
    return TOCResponse(toc=toc)


@router.get(
    "/files",
    response_model=FileContentResponse,
    summary="프로젝트 내 특정 마크다운 파일 원문 및 메타데이터 조회"
)
async def get_file(
    path: str = Query(..., description="조회할 파일의 상대 경로 (예: devops/docker.md)"),
    project: str = Query(default="default", description="대상 프로젝트 명"),
    project_service: ProjectService = Depends(get_project_service),
) -> FileContentResponse:
    """
    프로젝트 내의 특정 마크다운 파일의 전체 내용(Markdown), H1~H3 헤딩 목록, 파일 크기 및 수정 시각을 반환합니다.
    """
    project_path = project_service.get_project_path(project)
    try:
        safe_path = validate_safe_path(path, project_path)
    except SecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"보안 위반: {str(e)}"
        )

    if not safe_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"파일을 찾을 수 없습니다: '{path}'"
        )

    try:
        content = safe_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일을 읽는 도중 오류가 발생했습니다: {str(e)}"
        )

    headings = extract_headings(content)
    stat = safe_path.stat()

    return FileContentResponse(
        project=project,
        path=path,
        content=content,
        headings=headings,
        size_bytes=stat.st_size,
        modified_at=stat.st_mtime
    )

