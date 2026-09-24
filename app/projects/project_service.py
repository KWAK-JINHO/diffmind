# app/projects/project_service.py
import datetime
import os
from pathlib import Path
import shutil
from typing import Optional

from app.config import (
    Settings,
    get_project_dir,
    get_settings,
    validate_project_name,
)
from app.schemas.project import ProjectInfo
from app.synthesis.scanner import EXCLUDED_DIR_NAMES, scan_knowledge_base
from app.versioning.git_service import GitService


class ProjectService:
    """
    Manages multi-project workspace isolation and metadata.
    Each project is an isolated directory inside KB_BASE_PATH with its own Git repository.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_path = self.settings.resolved_kb_path
        self.ensure_default_project()

    def ensure_default_project(self) -> Path:
        """
        Ensures the 'default' project directory exists and has an initialized Git repository.
        Preserves any pre-existing root markdown files by migrating them into default.
        """
        default_dir = self.base_path / "default"
        if not default_dir.is_dir():
            default_dir.mkdir(parents=True, exist_ok=True)
            
            # Migrate any top-level markdown files into default workspace
            migrated = False
            for f in self.base_path.glob("*.md"):
                if f.is_file() and not f.name.startswith("."):
                    shutil.copy2(f, default_dir / f.name)
                    migrated = True

            welcome_file = default_dir / "welcome.md"
            if not any(default_dir.glob("*.md")):
                welcome_file.write_text(
                    "# Default Knowledge Project\n\n"
                    "DiffMind의 기본 프로젝트 작업공간입니다.\n\n"
                    "## 시작하기\n"
                    "새 지식을 제안하거나, 다른 프로젝트를 생성하여 지식을 독립 격리 관리하세요.\n",
                    encoding="utf-8"
                )

            git_service = GitService(kb_path=default_dir)
            git_service.ensure_repository()
            git_service.add(".")
            git_service.commit("feat: initialize default knowledge project")
        return default_dir

    def get_project_path(self, project_name: str) -> Path:
        """
        Returns the safe, resolved directory for the specified project.
        Raises ValueError if project does not exist (unless project_name is 'default').
        """
        clean_name = validate_project_name(project_name)
        if clean_name == "default":
            return self.ensure_default_project()

        project_dir = get_project_dir(clean_name, self.base_path)
        if not project_dir.is_dir():
            raise ValueError(f"Project '{clean_name}' does not exist.")
        return project_dir

    def list_projects(self) -> list[ProjectInfo]:
        """
        Scans base_path for all project workspace directories and returns their status.
        """
        self.ensure_default_project()
        projects: list[ProjectInfo] = []

        for entry in os.scandir(self.base_path):
            if not entry.is_dir():
                continue
            if entry.name.startswith(".") or entry.name in EXCLUDED_DIR_NAMES:
                continue

            project_path = Path(entry.path)
            # Count markdown documents
            toc = scan_knowledge_base(project_path)
            file_count = len(toc)

            # Check Git commit count
            git_service = GitService(kb_path=project_path)
            commit_count = git_service.get_commit_count()

            # Last modified time
            mtime = entry.stat().st_mtime
            dt_str = datetime.datetime.fromtimestamp(
                mtime, tz=datetime.timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S UTC")

            projects.append(
                ProjectInfo(
                    name=entry.name,
                    path=str(project_path),
                    file_count=file_count,
                    commit_count=commit_count,
                    last_modified=dt_str
                )
            )

        # Sort so 'default' is first, followed by alphabetical order
        projects.sort(key=lambda p: (0 if p.name == "default" else 1, p.name))
        return projects

    def create_project(self, name: str, description: Optional[str] = None) -> ProjectInfo:
        """
        Creates a new isolated project with its own directory and initialized Git repository.
        """
        clean_name = validate_project_name(name)
        project_dir = get_project_dir(clean_name, self.base_path)

        if project_dir.exists():
            raise ValueError(f"Project '{clean_name}' already exists.")

        project_dir.mkdir(parents=True, exist_ok=True)

        # Create initial README
        desc_text = description.strip() if description else f"DiffMind knowledge project '{clean_name}'"
        readme = project_dir / "README.md"
        readme.write_text(
            f"# {clean_name}\n\n{desc_text}\n\n## Overview\nProject initialized with DiffMind.\n",
            encoding="utf-8"
        )

        # Initialize project git repository
        git_service = GitService(kb_path=project_dir)
        git_service.ensure_repository()
        git_service.add("README.md")
        commit_hash = git_service.commit(f"feat: initialize project '{clean_name}'")

        dt_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        return ProjectInfo(
            name=clean_name,
            path=str(project_dir),
            file_count=1,
            commit_count=1,
            last_modified=dt_str
        )

    def get_project_info(self, project_name: str) -> ProjectInfo:
        """
        Retrieves ProjectInfo for a specific project.
        """
        project_path = self.get_project_path(project_name)
        toc = scan_knowledge_base(project_path)
        git_service = GitService(kb_path=project_path)

        stat = project_path.stat()
        dt_str = datetime.datetime.fromtimestamp(
            stat.st_mtime, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S UTC")

        return ProjectInfo(
            name=project_name,
            path=str(project_path),
            file_count=len(toc),
            commit_count=git_service.get_commit_count(),
            last_modified=dt_str
        )
