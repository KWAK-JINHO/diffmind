# tests/test_settings_api.py
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile

from app.main import app
from app.config import Settings, get_settings, update_env_settings


def test_get_settings_api():
    client = TestClient(app)
    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    data = response.json()
    assert "llm_provider" in data
    assert "gemini_model" in data
    assert "gemini_api_key_set" in data
    assert "gemini_api_key_masked" in data


def test_update_settings_api(tmp_path: Path):
    test_env = tmp_path / ".env"
    test_env.write_text("LLM_PROVIDER=google\nGEMINI_MODEL=gemini-3.5-flash\n", encoding="utf-8")

    # Test update_env_settings directly
    update_env_settings({"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "AIzaSyTestKey12345"}, env_path=test_env)
    content = test_env.read_text(encoding="utf-8")
    assert "GEMINI_MODEL=gemini-3.8-flash" in content
    assert "GEMINI_API_KEY=AIzaSyTestKey12345" in content
