# app/config.py
from functools import lru_cache
from pathlib import Path
import re
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecurityError(Exception):
    """Raised when an operation violates strict path security or containment rules."""
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Knowledge Base Path
    KB_PATH: Path = Field(
        default=Path("./knowledge_base"),
        description="로컬 마크다운 지식 베이스 루트 디렉터리 경로"
    )

    # Server Configuration (Strict Security: default bind to 127.0.0.1)
    HOST: str = Field(default="127.0.0.1", description="서버 바인드 호스트")
    PORT: int = Field(default=8000, description="서버 바인드 포트")

    # LLM Settings (Extensible: Google Gemini, OpenAI, Ollama, Custom OpenAI-compatible)
    LLM_PROVIDER: str = Field(default="google", description="사용할 LLM 제공자 ('google', 'openai', 'ollama', 'custom')")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google GenAI API Key")
    GEMINI_MODEL: str = Field(default="gemini-3.8-flash", description="Gemini 모델 명 (gemini-3.8-flash, gemini-3.7-flash, gemini-3.5-flash)")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI 모델 명")
    OPENAI_BASE_URL: Optional[str] = Field(default=None, description="OpenAI 호환 API 베이스 URL (OpenRouter, vLLM 등)")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434/v1", description="Ollama API 베이스 URL")
    OLLAMA_MODEL: str = Field(default="llama3.2", description="Ollama 로컬 모델 명")

    # Git Settings
    GIT_AUTHOR_NAME: str = Field(default="DiffMind Bot", description="Git 커밋 작성자 이름")
    GIT_AUTHOR_EMAIL: str = Field(default="diffmind@local.internal", description="Git 커밋 작성자 이메일")
    GIT_TIMEOUT_SECONDS: int = Field(default=10, description="Git CLI 명령어 타임아웃(초)")

    @property
    def resolved_kb_path(self) -> Path:
        """Returns the fully resolved absolute Path to the knowledge base."""
        resolved = self.KB_PATH.resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved


@lru_cache
def get_settings() -> Settings:
    return Settings()


def update_env_settings(updates: dict[str, str], env_path: Optional[Path] = None) -> None:
    """
    Safely and atomically updates specific keys in the .env file,
    preserving existing structure, comments, and other variables.
    Clears the get_settings cache so changes are immediately active.
    """
    import tempfile
    import os

    target_path = (env_path or Path(".env")).resolve()
    lines: list[str] = []
    if target_path.is_file():
        lines = target_path.read_text(encoding="utf-8").splitlines()

    updated_keys = set()
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or not stripped or "=" not in stripped:
            new_lines.append(line)
            continue
        key, _, _ = line.partition("=")
        key_clean = key.strip()
        if key_clean in updates:
            new_lines.append(f"{key_clean}={updates[key_clean]}")
            updated_keys.add(key_clean)
        else:
            new_lines.append(line)

    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={val}")

    content = "\n".join(new_lines) + "\n"
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(target_path.parent), delete=False) as tf:
        tf.write(content)
        tf.flush()
        os.fsync(tf.fileno())
        temp_name = tf.name

    os.replace(temp_name, target_path)
    get_settings.cache_clear()


def validate_safe_path(target_rel_path: str | Path, base_dir: Path) -> Path:
    """
    Validates that target_rel_path resolves strictly within base_dir.
    Guards against directory traversal, symlink escape, and forbidden directory access.
    
    Raises:
        SecurityError: If the path traverses outside base_dir or references restricted directories.
    """
    target_str = str(target_rel_path).strip()
    if not target_str:
        raise SecurityError("Target path cannot be empty.")

    base_resolved = base_dir.resolve()
    target_candidate = (base_resolved / target_rel_path).resolve()

    # Verify that target_candidate is strictly inside base_resolved
    try:
        target_candidate.relative_to(base_resolved)
    except ValueError:
        raise SecurityError(
            f"Security Violation: Target path '{target_rel_path}' escapes base directory '{base_resolved}'."
        )

    # Disallow targeting forbidden hidden/system folders
    relative_parts = target_candidate.relative_to(base_resolved).parts
    forbidden_prefixes = (".git", ".obsidian", "node_modules", ".venv", "__pycache__")
    for part in relative_parts:
        if part in forbidden_prefixes or (part.startswith(".") and part not in (".", "..")):
            raise SecurityError(
                f"Security Violation: Access to restricted directory/file '{part}' is forbidden."
            )

    return target_candidate


VALID_PROJECT_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_project_name(name: str) -> str:
    """
    Validates project name format and strictly prevents path traversal characters.
    """
    clean_name = str(name).strip()
    if not clean_name:
        raise SecurityError("Project name cannot be empty.")
    if not VALID_PROJECT_NAME_REGEX.match(clean_name):
        raise SecurityError(
            f"Invalid project name '{clean_name}'. Only alphanumeric characters, underscores, and hyphens are permitted."
        )
    return clean_name


def get_project_dir(project_name: str, base_kb_path: Path) -> Path:
    """
    Returns the resolved Path for a project directory within base_kb_path.
    Guarantees strict isolation within base_kb_path.
    """
    clean_name = validate_project_name(project_name)
    base_resolved = base_kb_path.resolve()
    target_dir = (base_resolved / clean_name).resolve()
    try:
        target_dir.relative_to(base_resolved)
    except ValueError:
        raise SecurityError(f"Project directory traversal detected for project '{project_name}'.")
    return target_dir

