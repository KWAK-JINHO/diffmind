# app/projects/import_service.py
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from app.config import SecurityError, Settings, get_settings, validate_safe_path
from app.projects.project_service import ProjectService
from app.schemas.project import ImportResult
from app.synthesis.scanner import EXCLUDED_DIR_NAMES, scan_knowledge_base
from app.versioning.git_service import GitExecutionError, GitService
from fastapi import UploadFile

logger = logging.getLogger(__name__)


class ImportService:
    """
    Handles bulk knowledge imports into isolated project workspaces from:
    1. Remote GitHub / Git repositories
    2. Local directory markdown trees
    """

    def __init__(
        self,
        project_service: Optional[ProjectService] = None,
        settings: Optional[Settings] = None
    ):
        self.settings = settings or get_settings()
        self.project_service = project_service or ProjectService(settings=self.settings)

    def import_from_github(
        self,
        project_name: str,
        repo_url: str,
        branch: Optional[str] = None
    ) -> ImportResult:
        """
        Clones a remote repository to a temporary workspace, copies its markdown documents
        and directory tree into the target project, and commits the imported knowledge.
        """
        clean_url = repo_url.strip()
        if not clean_url.startswith("https://"):
            raise SecurityError("Only secure HTTPS Git repository URLs (https://...) are permitted.")

        project_dir = self.project_service.get_project_path(project_name)
        git_service = GitService(kb_path=project_dir)
        git_service.ensure_repository()

        with tempfile.TemporaryDirectory(prefix="diffmind_clone_") as temp_dir:
            temp_path = Path(temp_dir)
            clone_cmd = ["git", "clone", "--depth", "1"]
            if branch and branch.strip():
                clone_cmd.extend(["--branch", branch.strip()])
            clone_cmd.extend([clean_url, str(temp_path)])

            try:
                subprocess.run(
                    clone_cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=45,
                    check=True,
                    shell=False
                )
            except subprocess.TimeoutExpired as e:
                raise GitExecutionError(
                    command=clone_cmd,
                    returncode=-1,
                    stdout=e.stdout or "",
                    stderr="Git clone timed out after 45 seconds."
                ) from e
            except subprocess.CalledProcessError as e:
                raise GitExecutionError(
                    command=clone_cmd,
                    returncode=e.returncode,
                    stdout=e.stdout or "",
                    stderr=e.stderr or ""
                ) from e

            # Copy markdown files from temp_path to project_dir
            imported_count = self._copy_markdown_tree(temp_path, project_dir)

        if imported_count == 0:
            logger.warning(f"No markdown (.md) files found in cloned repository {clean_url}")

        # Stage and commit in project git repository
        git_service.add(".")
        commit_msg = f"import: bulk knowledge from {clean_url}"
        if branch:
            commit_msg += f" (branch: {branch})"
        commit_hash = git_service.commit(commit_msg)

        # Immediate indexing
        toc = scan_knowledge_base(project_dir)

        return ImportResult(
            success=True,
            project_name=project_name,
            imported_files=imported_count,
            commit_hash=commit_hash,
            message=commit_msg,
            toc=toc
        )

    def import_from_local(
        self,
        project_name: str,
        source_path: str
    ) -> ImportResult:
        """
        Recursively copies all markdown documents and subdirectories from a local directory
        into the specified project, followed by an immediate Git commit and indexing.
        """
        clean_src = source_path.strip()
        src_path = Path(clean_src).resolve()

        if not src_path.exists():
            raise ValueError(f"Local source directory '{clean_src}' does not exist.")
        if not src_path.is_dir():
            raise ValueError(f"Local source path '{clean_src}' is not a directory.")

        project_dir = self.project_service.get_project_path(project_name)
        if project_dir.resolve() == src_path:
            raise ValueError("Source directory cannot be the same as the target project directory.")

        git_service = GitService(kb_path=project_dir)
        git_service.ensure_repository()

        imported_count = self._copy_markdown_tree(src_path, project_dir)

        if imported_count == 0:
            raise ValueError(f"No markdown (.md) files were found in source directory '{clean_src}'.")

        # Stage and commit
        git_service.add(".")
        commit_msg = f"import: local markdown tree from {src_path.name}"
        commit_hash = git_service.commit(commit_msg)

        # Immediate indexing
        toc = scan_knowledge_base(project_dir)

        return ImportResult(
            success=True,
            project_name=project_name,
            imported_files=imported_count,
            commit_hash=commit_hash,
            message=commit_msg,
            toc=toc
        )

    def _copy_markdown_tree(self, source_dir: Path, target_dir: Path) -> int:
        """
        Copies all .md files and their relative directories from source_dir to target_dir.
        Skips system and hidden folders (.git, .obsidian, node_modules, etc.).
        Returns the number of copied markdown files.
        """
        count = 0
        resolved_src = source_dir.resolve()

        for root, dirs, files in os.walk(resolved_src, topdown=True):
            # Prune excluded directories
            dirs[:] = [
                d for d in dirs
                if d not in EXCLUDED_DIR_NAMES and not d.startswith(".")
            ]

            for file_name in files:
                if not file_name.lower().endswith(".md") or file_name.startswith("."):
                    continue

                full_src_file = Path(root) / file_name
                rel_file_path = full_src_file.relative_to(resolved_src)
                full_dest_file = target_dir / rel_file_path

                full_dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(full_src_file, full_dest_file)
                count += 1

        return count

    async def import_uploaded_files(
        self,
        project_name: str,
        files: list[UploadFile],
        paths: list[str]
    ) -> ImportResult:
        """
        Takes uploaded files and their relative path strings (from browser folder selection),
        writes them safely into the target project directory, and performs Git commit & indexing.
        """
        project_dir = self.project_service.get_project_path(project_name)
        git_service = GitService(kb_path=project_dir)
        git_service.ensure_repository()

        imported_count = 0
        for upload_file, rel_path_str in zip(files, paths):
            if not rel_path_str.lower().endswith(".md"):
                continue

            # Strip root container folder name from webkitRelativePath if present
            # e.g. "MyVault/kubernetes/cgroups.md" -> "kubernetes/cgroups.md"
            parts = [p for p in Path(rel_path_str).parts if p not in (".", "..")]
            if len(parts) > 1:
                safe_rel = Path(*parts[1:])
            elif len(parts) == 1:
                safe_rel = Path(parts[0])
            else:
                continue

            dest_file = validate_safe_path(safe_rel, project_dir)
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            content = await upload_file.read()
            dest_file.write_bytes(content)
            imported_count += 1

        if imported_count == 0:
            raise ValueError("선택된 폴더에 마크다운(.md) 파일이 존재하지 않습니다.")

        git_service.add(".")
        commit_hash = git_service.commit(f"import: {imported_count} markdown files uploaded from browser")
        toc = scan_knowledge_base(project_dir)

        return ImportResult(
            success=True,
            project_name=project_name,
            imported_files=imported_count,
            commit_hash=commit_hash,
            message=f"총 {imported_count}개의 마크다운 문서를 성공적으로 임포트했습니다.",
            toc=toc
        )

    def browse_local_directories(self, base_path_str: Optional[str] = None) -> dict:
        """
        Safely inspects local filesystem directories starting from user home or specified path.
        Returns the current path, parent directory, and list of non-hidden subdirectories with md file counts.
        """
        if not base_path_str or not base_path_str.strip():
            current_path = Path.home().resolve()
        else:
            current_path = Path(base_path_str).expanduser().resolve()

        if not current_path.exists() or not current_path.is_dir():
            current_path = Path.home().resolve()

        parent_path = str(current_path.parent) if current_path.parent != current_path else None

        directories = []
        try:
            for entry in os.scandir(current_path):
                try:
                    if not entry.is_dir():
                        continue
                    if entry.name.startswith(".") or entry.name in EXCLUDED_DIR_NAMES:
                        continue

                    # Count markdown files in immediate directory
                    md_count = 0
                    try:
                        for sub in os.scandir(entry.path):
                            if sub.is_file() and sub.name.lower().endswith(".md") and not sub.name.startswith("."):
                                md_count += 1
                    except (PermissionError, OSError):
                        pass

                    directories.append({
                        "name": entry.name,
                        "path": str(Path(entry.path).resolve()),
                        "md_count": md_count
                    })
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            pass

        directories.sort(key=lambda d: d["name"].lower())

        return {
            "current_path": str(current_path),
            "parent_path": parent_path,
            "directories": directories
        }

