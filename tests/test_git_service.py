# tests/test_git_service.py
import pytest
from pathlib import Path
from app.versioning.git_service import GitService, GitExecutionError


def test_git_service_init_and_commit(tmp_path: Path):
    git_service = GitService(kb_path=tmp_path)
    git_service.ensure_repository()

    # Check git repository was created
    assert (tmp_path / ".git").is_dir()

    # Create and stage a markdown file
    test_file = tmp_path / "overview.md"
    test_file.write_text("# Knowledge Overview\nInitial content.", encoding="utf-8")

    git_service.add("overview.md")
    commit_hash = git_service.commit("feat: initial knowledge commit")

    assert len(commit_hash) >= 4
    assert git_service.get_commit_count() == 1

    # Verify recent diff for first commit
    diff1 = git_service.get_recent_diff()
    assert "overview.md" in diff1
    assert "+# Knowledge Overview" in diff1

    # Update file and make a second commit
    test_file.write_text("# Knowledge Overview\nInitial content.\n## New Section\nSecond line.", encoding="utf-8")
    git_service.add("overview.md")
    commit_hash2 = git_service.commit("docs: add new section")

    assert commit_hash2 != commit_hash
    assert git_service.get_commit_count() == 2

    # Verify recent diff for second commit (HEAD~1 HEAD)
    diff2 = git_service.get_recent_diff()
    assert "+## New Section" in diff2


def test_git_service_error_handling(tmp_path: Path):
    git_service = GitService(kb_path=tmp_path)
    git_service.ensure_repository()

    # Executing invalid git subcommand should raise GitExecutionError
    with pytest.raises(GitExecutionError) as exc_info:
        git_service._run_git(["invalid-command-xyz"])

    assert exc_info.value.returncode != 0
    assert "invalid-command-xyz" in exc_info.value.stderr or "is not a git command" in exc_info.value.stderr
