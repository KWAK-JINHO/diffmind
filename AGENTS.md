# Repository Guidelines

## Project Structure & Module Organization

DiffMind is a Python 3.12+ FastAPI application. Runtime code is under `app/`: `routers/` defines HTTP endpoints, `schemas/` contains Pydantic models, `projects/` manages knowledge-base projects and imports, `synthesis/` generates Markdown merge proposals, `ingestion/` handles image-to-Markdown input, and `versioning/` wraps Git operations. The browser UI lives in `app/static/`. Tests are in `tests/` and use temporary directories for filesystem behavior. `knowledge_base/` is local workspace data and is ignored by Git.

## Build, Test, and Development Commands

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest                         # run the full test suite
pytest tests/test_api.py -q    # run one focused test module
uvicorn app.main:app --reload  # run the local API and web UI
```

The application defaults to `http://127.0.0.1:8000`; FastAPI documentation is available at `/docs`. Configure local LLM credentials and paths in `.env` when needed. Do not commit `.env` files or API keys.

## Coding Style & Naming Conventions

Use four spaces, type annotations, and descriptive docstrings for public services and endpoints. Follow existing Python naming: `snake_case` for functions, variables, and modules; `PascalCase` for Pydantic models and service classes; `UPPER_SNAKE_CASE` for constants. Keep HTTP concerns in routers and business logic in services. No formatter or linter is configured, so preserve the surrounding style and keep imports organized.

## Testing Guidelines

Tests use pytest with `pytest-asyncio` in auto mode and `httpx` for API clients. Name files `test_*.py` and test functions `test_*`. Add or update tests for endpoint behavior, path-security rules, Git operations, and LLM fallback behavior when changing those areas. Run `pytest` before submitting changes; tests must not depend on real external LLM calls or committed credentials.

## Commit & Pull Request Guidelines

Recent commits use Conventional Commit prefixes with concise descriptions, for example `feat: ...` and Korean feature summaries. Follow that pattern (`fix:`, `test:`, `docs:`, or `refactor:` as appropriate). Pull requests should explain the behavior change, list validation commands and results, identify configuration or security implications, and include screenshots for `app/static/` UI changes. Keep unrelated refactors out of the change.

## Security & Configuration

Keep API keys in ignored `.env` files. Preserve `validate_safe_path` and project-name validation when handling user paths, and use the existing Git service rather than shell interpolation for Git commands. Treat `knowledge_base/` as user data: tests and development tools should avoid modifying real workspace content.
