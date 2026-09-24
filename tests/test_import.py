# tests/test_import.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.config import SecurityError, Settings
from app.projects.import_service import ImportService
from app.projects.project_service import ProjectService


def test_import_from_local_directory(tmp_path: Path):
    kb_root = tmp_path / "kb_base"
    kb_root.mkdir()
    settings = Settings(KB_PATH=kb_root)
    proj_service = ProjectService(settings=settings)
    import_service = ImportService(project_service=proj_service, settings=settings)

    # 1. Create a target project
    proj_service.create_project("linux-notes")

    # 2. Prepare an external local markdown vault
    external_vault = tmp_path / "external_vault"
    external_vault.mkdir()
    (external_vault / "intro.md").write_text("# Linux Intro\nBasic shell commands.", encoding="utf-8")
    
    kernel_dir = external_vault / "kernel"
    kernel_dir.mkdir()
    (kernel_dir / "modules.md").write_text("# Kernel Modules\n## lsmod\nInspect modules.", encoding="utf-8")

    # Non-markdown file and hidden folder (should be ignored)
    (external_vault / "image.png").write_bytes(b"dummy")
    obsidian_dir = external_vault / ".obsidian"
    obsidian_dir.mkdir()
    (obsidian_dir / "config.json.md").write_text("# Hidden Note", encoding="utf-8")

    # 3. Perform local import
    result = import_service.import_from_local("linux-notes", str(external_vault))

    assert result.success is True
    assert result.project_name == "linux-notes"
    assert result.imported_files == 2
    assert "intro.md" in result.toc
    assert "kernel/modules.md" in result.toc
    assert result.toc["kernel/modules.md"] == ["# Kernel Modules", "## lsmod"]
    assert len(result.commit_hash) >= 4


def test_import_from_local_validation(tmp_path: Path):
    kb_root = tmp_path / "kb_base"
    kb_root.mkdir()
    settings = Settings(KB_PATH=kb_root)
    proj_service = ProjectService(settings=settings)
    import_service = ImportService(project_service=proj_service, settings=settings)

    proj_service.create_project("test-proj")

    # Non-existent path
    with pytest.raises(ValueError, match="does not exist"):
        import_service.import_from_local("test-proj", str(tmp_path / "non_existent_folder"))

    # Empty directory with no markdown files
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    with pytest.raises(ValueError, match="No markdown"):
        import_service.import_from_local("test-proj", str(empty_dir))


def test_import_from_github_url_validation(tmp_path: Path):
    kb_root = tmp_path / "kb_base"
    kb_root.mkdir()
    settings = Settings(KB_PATH=kb_root)
    proj_service = ProjectService(settings=settings)
    import_service = ImportService(project_service=proj_service, settings=settings)

    proj_service.create_project("gh-proj")

    # Insecure or malicious URLs
    with pytest.raises(SecurityError, match="Only secure HTTPS"):
        import_service.import_from_github("gh-proj", "file:///etc/passwd")

    with pytest.raises(SecurityError, match="Only secure HTTPS"):
        import_service.import_from_github("gh-proj", "git@github.com:owner/repo.git")


def test_import_from_github_mocked_clone(tmp_path: Path):
    kb_root = tmp_path / "kb_base"
    kb_root.mkdir()
    settings = Settings(KB_PATH=kb_root)
    proj_service = ProjectService(settings=settings)
    import_service = ImportService(project_service=proj_service, settings=settings)

    proj_service.create_project("cloned-proj")

    def mock_subprocess_run(cmd, *args, **kwargs):
        # Extract target temp directory only from git clone command arguments
        if len(cmd) > 1 and cmd[1] == "clone":
            target_dir = Path(cmd[-1])
            (target_dir / "docs").mkdir(parents=True, exist_ok=True)
            (target_dir / "docs" / "guide.md").write_text("# Cloned Guide\n## Section 1\nText", encoding="utf-8")
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=mock_subprocess_run):
        result = import_service.import_from_github(
            project_name="cloned-proj",
            repo_url="https://github.com/example/my-notes"
        )
        assert result.success is True
        assert result.imported_files == 1
        assert "docs/guide.md" in result.toc
        assert result.toc["docs/guide.md"] == ["# Cloned Guide", "## Section 1"]


def test_browse_local_directories(tmp_path: Path):
    browse_root = tmp_path / "browse_test"
    browse_root.mkdir()

    sub_a = browse_root / "vault_a"
    sub_a.mkdir()
    (sub_a / "note1.md").write_text("# Note 1", encoding="utf-8")
    (sub_a / "note2.md").write_text("# Note 2", encoding="utf-8")

    sub_b = browse_root / "vault_b"
    sub_b.mkdir()

    # Hidden folder should be ignored
    hidden = browse_root / ".secret_folder"
    hidden.mkdir()

    settings = Settings(KB_PATH=tmp_path / "kb")
    import_service = ImportService(settings=settings)

    browse_result = import_service.browse_local_directories(str(browse_root))

    assert browse_result["current_path"] == str(browse_root.resolve())
    dirs = {d["name"]: d for d in browse_result["directories"]}

    assert "vault_a" in dirs
    assert dirs["vault_a"]["md_count"] == 2
    assert "vault_b" in dirs
    assert dirs["vault_b"]["md_count"] == 0
    assert ".secret_folder" not in dirs

