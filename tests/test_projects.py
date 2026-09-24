# tests/test_projects.py
import pytest
from pathlib import Path
from app.config import SecurityError, Settings
from app.projects.project_service import ProjectService


def test_project_create_and_list(tmp_path: Path):
    settings = Settings(KB_PATH=tmp_path)
    service = ProjectService(settings=settings)

    # Initial state should have 'default'
    projects = service.list_projects()
    assert len(projects) >= 1
    assert projects[0].name == "default"

    # Create project 1
    p1 = service.create_project("k8s-docs", "Kubernetes notes")
    assert p1.name == "k8s-docs"
    assert (tmp_path / "k8s-docs" / ".git").is_dir()
    assert (tmp_path / "k8s-docs" / "README.md").is_file()

    # Create project 2
    p2 = service.create_project("rust-learning")
    assert p2.name == "rust-learning"
    assert (tmp_path / "rust-learning" / ".git").is_dir()

    # Listing should include both
    all_projects = service.list_projects()
    names = [p.name for p in all_projects]
    assert "default" in names
    assert "k8s-docs" in names
    assert "rust-learning" in names


def test_project_isolation(tmp_path: Path):
    settings = Settings(KB_PATH=tmp_path)
    service = ProjectService(settings=settings)

    service.create_project("proj-a")
    service.create_project("proj-b")

    path_a = service.get_project_path("proj-a")
    path_b = service.get_project_path("proj-b")

    # Add file to project A
    (path_a / "note_a.md").write_text("# Note A", encoding="utf-8")

    # Verify project B does NOT see note_a.md
    assert not (path_b / "note_a.md").exists()
    assert (path_a / "note_a.md").exists()


def test_project_name_validation(tmp_path: Path):
    settings = Settings(KB_PATH=tmp_path)
    service = ProjectService(settings=settings)

    # Path traversal attempts
    with pytest.raises(SecurityError):
        service.create_project("../escaped")

    with pytest.raises(SecurityError):
        service.create_project("foo/bar")

    with pytest.raises(SecurityError):
        service.create_project(".hidden")

    # Duplicate creation error
    service.create_project("unique-proj")
    with pytest.raises(ValueError, match="already exists"):
        service.create_project("unique-proj")
