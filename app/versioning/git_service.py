# app/versioning/git_service.py
import subprocess
from pathlib import Path
from typing import Optional
from app.config import get_settings


class GitExecutionError(Exception):
    """Raised when a Git command execution fails."""

    def __init__(self, command: list[str], returncode: int, stdout: str, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        cmd_str = " ".join(command)
        super().__init__(
            f"Git command '{cmd_str}' failed with exit code {returncode}.\n"
            f"STDERR: {stderr.strip()}\n"
            f"STDOUT: {stdout.strip()}"
        )


class GitService:
    """
    Direct OS Git CLI runner using Python subprocess.run(shell=False).
    Enforces security isolation, explicit cwd, timeouts, and error capturing.
    """

    def __init__(self, kb_path: Optional[Path] = None, timeout: Optional[int] = None):
        settings = get_settings()
        self.kb_path = (kb_path or settings.resolved_kb_path).resolve()
        self.timeout = timeout or settings.GIT_TIMEOUT_SECONDS
        self.author_name = settings.GIT_AUTHOR_NAME
        self.author_email = settings.GIT_AUTHOR_EMAIL

    def _run_git(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
        """
        Executes a git command with strict subprocess constraints.
        shell=False, argument list, explicit cwd, and timeout.
        """
        command = ["git"] + args
        try:
            result = subprocess.run(
                command,
                cwd=str(self.kb_path),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                shell=False,
                check=False
            )
        except subprocess.TimeoutExpired as e:
            raise GitExecutionError(
                command=command,
                returncode=-1,
                stdout=e.stdout or "" if isinstance(e.stdout, str) else "",
                stderr=f"Command timed out after {self.timeout} seconds."
            ) from e
        except FileNotFoundError as e:
            raise GitExecutionError(
                command=command,
                returncode=-1,
                stdout="",
                stderr="Git executable not found on host system."
            ) from e

        if check and result.returncode != 0:
            raise GitExecutionError(
                command=command,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )

        return result

    def ensure_repository(self) -> None:
        """
        Initializes git repository if .git does not exist, and configures local author if needed.
        """
        self.kb_path.mkdir(parents=True, exist_ok=True)
        git_dir = self.kb_path / ".git"
        if not git_dir.is_dir():
            self._run_git(["init"])
            # Configure repository local author to prevent git commit failures when global user is unset
            self._run_git(["config", "user.name", self.author_name])
            self._run_git(["config", "user.email", self.author_email])
        else:
            # Check if user.name is configured, set if missing
            check_user = self._run_git(["config", "user.name"], check=False)
            if check_user.returncode != 0 or not check_user.stdout.strip():
                self._run_git(["config", "user.name", self.author_name])
                self._run_git(["config", "user.email", self.author_email])

    def add(self, relative_file_path: str | Path) -> None:
        """Stages the specified file path."""
        self.ensure_repository()
        rel_str = str(relative_file_path)
        self._run_git(["add", "--", rel_str])

    def commit(self, message: str) -> str:
        """
        Commits staged changes and returns the short commit hash.
        """
        self.ensure_repository()
        clean_msg = message.strip()
        if not clean_msg:
            clean_msg = "docs: automated update via DiffMind"

        self._run_git(["commit", "-m", clean_msg])
        return self.get_short_head()

    def get_short_head(self) -> str:
        """Retrieves the short commit hash of HEAD."""
        result = self._run_git(["rev-parse", "--short", "HEAD"])
        return result.stdout.strip()

    def get_commit_count(self) -> int:
        """Returns the number of commits in the current branch."""
        result = self._run_git(["rev-list", "--count", "HEAD"], check=False)
        if result.returncode != 0:
            return 0
        try:
            return int(result.stdout.strip())
        except ValueError:
            return 0

    def get_recent_diff(self) -> str:
        """
        Retrieves the unified diff of the most recent commit.
        If multiple commits exist, uses 'git diff HEAD~1 HEAD'.
        If only the root commit exists, uses 'git show -p HEAD' or diffs against empty tree.
        """
        self.ensure_repository()
        count = self.get_commit_count()
        if count == 0:
            return "No commits found in knowledge base repository."

        if count >= 2:
            res = self._run_git(["diff", "HEAD~1", "HEAD"])
            return res.stdout
        else:
            # First commit diff against empty tree
            res = self._run_git(["diff", "4b825dc642cb6eb9a060e54bf8d69288fbee4904", "HEAD"], check=False)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout
            # Fallback to git show
            res_show = self._run_git(["show", "--stat", "-p", "HEAD"])
            return res_show.stdout
