# tests/test_file_api.py
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.config import Settings, get_settings
from app.main import app
from app.projects.project_service import ProjectService
from app.routers.knowledge_router import get_project_service


@pytest.fixture
def client_with_files(tmp_path: Path):
    kb_root = tmp_path / "test_kb"
    kb_root.mkdir()
    settings = Settings(KB_PATH=kb_root)
    proj_service = ProjectService(settings=settings)

    # Create a project and some markdown notes
    proj_service.create_project("study-proj")
    proj_path = proj_service.get_project_path("study-proj")

    devops_dir = proj_path / "devops"
    devops_dir.mkdir(parents=True, exist_ok=True)
    docker_file = devops_dir / "docker.md"
    docker_file.write_text(
        "# Docker Containers\n\nOverview of containers.\n\n## Volumes\n\nVolume guide.\n",
        encoding="utf-8"
    )

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_project_service] = lambda: proj_service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_get_file_success(client_with_files):
    resp = client_with_files.get("/api/v1/files?project=study-proj&path=devops/docker.md")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project"] == "study-proj"
    assert data["path"] == "devops/docker.md"
    assert "# Docker Containers" in data["content"]
    assert data["headings"] == ["# Docker Containers", "## Volumes"]
    assert data["size_bytes"] > 0
    assert data["modified_at"] > 0


def test_get_file_not_found(client_with_files):
    resp = client_with_files.get("/api/v1/files?project=study-proj&path=non_existent.md")
    assert resp.status_code == 404
    assert "파일을 찾을 수 없습니다" in resp.json()["detail"]


def test_get_file_path_traversal_blocked(client_with_files):
    resp = client_with_files.get("/api/v1/files?project=study-proj&path=../../etc/passwd")
    assert resp.status_code == 400
    assert "보안 위반" in resp.json()["detail"]
