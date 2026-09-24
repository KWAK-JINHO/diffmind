# tests/test_synthesis_llm.py
import pytest
from unittest.mock import MagicMock, patch
from app.config import Settings
from app.schemas.patch import LLMDecision
from app.synthesis.synthesis_service import SynthesisService


@pytest.mark.asyncio
async def test_synthesis_gemini_structured():
    settings = Settings(
        KB_PATH="./knowledge_base",
        LLM_PROVIDER="google",
        GEMINI_API_KEY="test_key",
        GEMINI_MODEL="gemini-2.5-flash"
    )
    service = SynthesisService(settings=settings)

    mock_decision_json = """{
        "is_new_file": false,
        "target_file_path": "kubernetes/cgroups.md",
        "target_heading": "## cgroups v2 리소스 격리",
        "original_snippet": "",
        "proposed_snippet": "### CPU Weight\\nCPU shares are replaced by cpu.weight.",
        "reason": "Topical fit under cgroups v2."
    }"""

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = mock_decision_json
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        decision = await service.decide_patch_with_llm(
            content="CPU shares are replaced by cpu.weight in v2.",
            toc_map={"kubernetes/cgroups.md": ["# cgroups", "## cgroups v2 리소스 격리"]}
        )
        assert decision.is_new_file is False
        assert decision.target_file_path == "kubernetes/cgroups.md"
        assert decision.target_heading == "## cgroups v2 리소스 격리"
        assert "CPU Weight" in decision.proposed_snippet


@pytest.mark.asyncio
async def test_synthesis_openai_structured():
    settings = Settings(
        KB_PATH="./knowledge_base",
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="test_openai_key",
        OPENAI_MODEL="gpt-4o"
    )
    service = SynthesisService(settings=settings)

    expected_decision = LLMDecision(
        is_new_file=True,
        target_file_path="security/selinux.md",
        target_heading="# SELinux Policies",
        original_snippet="",
        proposed_snippet="SELinux enforces mandatory access control.",
        reason="No existing security document found."
    )

    mock_client = MagicMock()
    mock_parsed_choice = MagicMock()
    mock_parsed_choice.message.parsed = expected_decision
    mock_resp = MagicMock()
    mock_resp.choices = [mock_parsed_choice]
    mock_client.beta.chat.completions.parse.return_value = mock_resp

    with patch("openai.OpenAI", return_value=mock_client):
        decision = await service.decide_patch_with_llm(
            content="SELinux details...",
            toc_map={}
        )
        assert decision.is_new_file is True
        assert decision.target_file_path == "security/selinux.md"
        assert "# SELinux Policies" in decision.target_heading


@pytest.mark.asyncio
async def test_synthesis_ollama_structured():
    settings = Settings(
        KB_PATH="./knowledge_base",
        LLM_PROVIDER="ollama",
        OLLAMA_BASE_URL="http://localhost:11434/v1",
        OLLAMA_MODEL="llama3.2"
    )
    service = SynthesisService(settings=settings)

    expected_decision = LLMDecision(
        is_new_file=False,
        target_file_path="docker/network.md",
        target_heading="## Overlay Networks",
        original_snippet="",
        proposed_snippet="Overlay network config.",
        reason="Matches network topic."
    )

    mock_client = MagicMock()
    mock_parsed_choice = MagicMock()
    mock_parsed_choice.message.parsed = expected_decision
    mock_resp = MagicMock()
    mock_resp.choices = [mock_parsed_choice]
    mock_client.beta.chat.completions.parse.return_value = mock_resp

    with patch("openai.OpenAI", return_value=mock_client) as mock_openai_cls:
        decision = await service.decide_patch_with_llm(
            content="Overlay network config.",
            toc_map={"docker/network.md": ["# Docker", "## Overlay Networks"]}
        )
        assert decision.target_file_path == "docker/network.md"
        # Verify client initialized with Ollama URL
        mock_openai_cls.assert_called_with(api_key="ollama", base_url="http://localhost:11434/v1")
