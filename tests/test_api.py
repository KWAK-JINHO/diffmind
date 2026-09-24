# tests/test_api.py
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


@pytest.fixture
def test_app(tmp_path: Path):
    """
    Overrides the KB_PATH setting to use an isolated temporary directory for testing.
    """
    kb_dir = tmp_path / "test_kb"
    kb_dir.mkdir()

    # Pre-populate one markdown file
    os_file = kb_dir / "os.md"
    os_file.write_text("# Operating Systems\n## Virtual Memory\nPaging mechanisms.", encoding="utf-8")

    test_settings = Settings(
        KB_PATH=kb_dir,
        HOST="127.0.0.1",
        PORT=8000,
        LLM_PROVIDER="google",
        GEMINI_API_KEY="",
        OPENAI_API_KEY=""
    )

    app.dependency_overrides[get_settings] = lambda: test_settings

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_root_and_health(test_app: TestClient):
    # Verify web frontend HTML is served at root
    res_root = test_app.get("/")
    assert res_root.status_code == 200
    assert "text/html" in res_root.headers.get("content-type", "")
    assert "DiffMind" in res_root.text
    assert "지식 소스 (Sources)" in res_root.text

    # Verify JSON API metadata endpoint
    res_api = test_app.get("/api")
    assert res_api.status_code == 200
    assert res_api.json()["system"] == "DiffMind"

    # Verify Health endpoint
    res_health = test_app.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"


def test_get_toc(test_app: TestClient):
    res = test_app.get("/api/v1/toc")
    assert res.status_code == 200
    toc = res.json()["toc"]
    assert "os.md" in toc
    assert toc["os.md"] == ["# Operating Systems", "## Virtual Memory"]


def test_propose_and_accept_flow(test_app: TestClient):
    # 1. Propose patch with text content matching existing os.md
    new_knowledge = "## Virtual Memory\nPage fault handling occurs when a page is not resident."
    res_propose = test_app.post(
        "/api/v1/propose",
        data={"content": new_knowledge}
    )
    assert res_propose.status_code == 200
    proposal = res_propose.json()

    assert proposal["target_file_path"] == "os.md"
    assert "unified_diff" in proposal
    assert proposal["unified_diff"] != ""
    assert "--- a/os.md" in proposal["unified_diff"]

    # 2. Accept proposal
    accept_payload = {
        "proposal": proposal,
        "commit_message": "docs: add page fault handling details"
    }
    res_accept = test_app.post("/api/v1/accept", json=accept_payload)
    assert res_accept.status_code == 200
    commit_res = res_accept.json()

    assert commit_res["success"] is True
    assert len(commit_res["commit_hash"]) >= 4
    assert commit_res["message"] == "docs: add page fault handling details"
    assert commit_res["file_path"] == "os.md"

    # 3. Check recent-diff
    res_diff = test_app.get("/api/v1/recent-diff")
    assert res_diff.status_code == 200
    diff_data = res_diff.json()
    assert "Page fault handling" in diff_data["diff"]


def test_propose_file_upload(test_app: TestClient):
    # Propose via uploaded file
    file_bytes = b"# Distributed Systems\n## Consensus\nRaft and Paxos algorithms."
    files = {"file": ("consensus.md", file_bytes, "text/markdown")}

    res_propose = test_app.post(
        "/api/v1/propose",
        files=files
    )
    assert res_propose.status_code == 200
    proposal = res_propose.json()
    assert proposal["is_new_file"] is True
    assert "unified_diff" in proposal


def test_propose_empty_input_error(test_app: TestClient):
    res = test_app.post("/api/v1/propose")
    assert res.status_code == 400
    assert "적어도 하나의 유효한 입력" in res.json()["detail"]


def test_accept_path_traversal_blocked(test_app: TestClient):
    malicious_proposal = {
        "proposal": {
            "is_new_file": False,
            "target_file_path": "../../etc/shadow",
            "target_heading": "# Exploit",
            "original_snippet": "",
            "proposed_snippet": "root:hacked",
            "unified_diff": "diff",
            "reason": "Attack test"
        },
        "commit_message": "exploit"
    }
    res = test_app.post("/api/v1/accept", json=malicious_proposal)
    assert res.status_code == 403
    assert res.json()["error"] == "SecurityViolation"


def test_project_api_endpoints(test_app: TestClient):
    # 1. List projects
    res_list = test_app.get("/api/v1/projects")
    assert res_list.status_code == 200
    projects = res_list.json()
    assert len(projects) >= 1
    assert any(p["name"] == "default" for p in projects)

    # 2. Create new project
    res_create = test_app.post(
        "/api/v1/projects",
        json={"name": "backend-infra", "description": "Backend knowledge base"}
    )
    assert res_create.status_code == 201
    created = res_create.json()
    assert created["name"] == "backend-infra"

    # 3. Get project details and TOC
    res_detail = test_app.get("/api/v1/projects/backend-infra")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["project"]["name"] == "backend-infra"
    assert "README.md" in detail["toc"]

    # 4. Propose in new project
    res_propose = test_app.post(
        "/api/v1/propose",
        data={"content": "## Database\nPostgreSQL replication setup.", "project": "backend-infra"}
    )
    assert res_propose.status_code == 200
    proposal = res_propose.json()
    assert proposal["unified_diff"] != ""

