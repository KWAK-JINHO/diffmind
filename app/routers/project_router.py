# app/routers/project_router.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.config import Settings, get_settings
from app.projects.import_service import ImportService
from app.projects.project_service import ProjectService
from app.schemas.project import (
    GitHubImportRequest,
    ImportResult,
    LocalImportRequest,
    ProjectCreateRequest,
    ProjectInfo,
)
from app.synthesis.scanner import scan_knowledge_base

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/projects", tags=["Project Management"])


def get_project_service(settings: Settings = Depends(get_settings)) -> ProjectService:
    return ProjectService(settings=settings)


def get_import_service(
    project_service: ProjectService = Depends(get_project_service),
    settings: Settings = Depends(get_settings),
) -> ImportService:
    return ImportService(project_service=project_service, settings=settings)


@router.get("", response_model=list[ProjectInfo], summary="모든 지식 베이스 프로젝트 목록 조회")
async def list_projects(
    project_service: ProjectService = Depends(get_project_service),
) -> list[ProjectInfo]:
    """
    격리된 모든 프로젝트 작업공간 목록과 각 프로젝트의 문서 수, 커밋 수를 반환합니다.
    """
    return project_service.list_projects()


@router.post("", response_model=ProjectInfo, status_code=status.HTTP_201_CREATED, summary="신규 프로젝트 생성")
async def create_project(
    request: ProjectCreateRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectInfo:
    """
    독립된 디렉터리와 자체 Git 저장소를 가진 신규 프로젝트를 생성합니다.
    """
    return project_service.create_project(name=request.name, description=request.description)


@router.get("/{project_name}", summary="특정 프로젝트 상세 정보 및 목차 조회")
async def get_project_details(
    project_name: str,
    project_service: ProjectService = Depends(get_project_service),
) -> dict:
    """
    지정된 프로젝트의 메타데이터와 전체 H1~H3 목차 트리를 반환합니다.
    """
    info = project_service.get_project_info(project_name)
    project_path = project_service.get_project_path(project_name)
    toc = scan_knowledge_base(project_path)
    return {
        "project": info,
        "toc": toc,
    }


@router.post("/{project_name}/import/github", response_model=ImportResult, summary="GitHub 레포지토리 일괄 임포트")
async def import_github_repository(
    project_name: str,
    request: GitHubImportRequest,
    import_service: ImportService = Depends(get_import_service),
) -> ImportResult:
    """
    GitHub URL로부터 마크다운 파일 트리를 클론하여 해당 프로젝트로 일괄 임포트하고 Git 커밋 및 인덱싱을 수행합니다.
    """
    return import_service.import_from_github(
        project_name=project_name,
        repo_url=request.repo_url,
        branch=request.branch
    )


@router.post("/{project_name}/import/local", response_model=ImportResult, summary="로컬 디렉터리 일괄 임포트")
async def import_local_directory(
    project_name: str,
    request: LocalImportRequest,
    import_service: ImportService = Depends(get_import_service),
) -> ImportResult:
    """
    사용자가 지정한 로컬 디렉터리의 마크다운 구조를 프로젝트 내부로 재귀 복사하고 Git 커밋 및 인덱싱을 수행합니다.
    """
    return import_service.import_from_local(
        project_name=project_name,
        source_path=request.source_path
    )


@router.get("/browse/local-dirs", summary="로컬 디렉터리 경로 탐색 (모달 지원)")
async def browse_directories(
    path: Optional[str] = Query(default=None, description="탐색할 디렉터리 경로 (미지정 시 홈 디렉터리)"),
    import_service: ImportService = Depends(get_import_service),
) -> dict:
    """
    사용자의 로컬 파일시스템 디렉터리를 안전하게 조회하여 모달 탐색기에서 하위 폴더 및 마크다운 파일 수를 탐색할 수 있도록 지원합니다.
    """
    return import_service.browse_local_directories(base_path_str=path)


@router.post("/{project_name}/import/files", response_model=ImportResult, summary="브라우저 폴더 선택(Finder) 일괄 업로드")
async def import_folder_files(
    project_name: str,
    files: list[UploadFile] = File(..., description="업로드할 폴더 내 마크다운 파일 목록"),
    paths: list[str] = Form(..., description="각 파일의 상대 경로 목록 (webkitRelativePath)"),
    import_service: ImportService = Depends(get_import_service),
) -> ImportResult:
    """
    브라우저(Finder)에서 선택된 폴더 내의 마크다운 파일들을 상대 경로 구조 그대로 수신하여
    프로젝트 디렉터리에 원자적으로 배치하고 Git 커밋 및 인덱싱을 수행합니다.
    """
    return await import_service.import_uploaded_files(
        project_name=project_name,
        files=files,
        paths=paths
    )

