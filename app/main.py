# app/main.py
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import SecurityError, get_settings
from app.routers import knowledge_router, project_router
from app.versioning.git_service import GitExecutionError, GitService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("diffmind")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application startup and shutdown lifecycle management.
    Initializes knowledge base storage and Git repository on boot.
    """
    settings = get_settings()
    logger.info("Initializing DiffMind...")
    logger.info(f"Knowledge Base Directory: {settings.resolved_kb_path}")
    logger.info(f"Server configured for {settings.HOST}:{settings.PORT}")

    # Ensure repository and commit author are properly initialized
    try:
        git_service = GitService(kb_path=settings.resolved_kb_path)
        git_service.ensure_repository()
        logger.info("Local Git repository verified and ready.")
    except Exception as e:
        logger.warning(f"Git initialization warning (non-fatal on startup): {e}")

    yield

    logger.info("DiffMind shutting down.")


app = FastAPI(
    title="DiffMind",
    description="Intelligent Markdown Knowledge Base Merging & Git Approval Pipeline",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(SecurityError)
async def security_error_handler(request: Request, exc: SecurityError) -> JSONResponse:
    logger.error(f"Security error during {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "SecurityViolation",
            "message": str(exc),
            "path": request.url.path
        }
    )


@app.exception_handler(GitExecutionError)
async def git_execution_error_handler(request: Request, exc: GitExecutionError) -> JSONResponse:
    logger.error(f"Git execution failure during {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "GitExecutionError",
            "message": str(exc),
            "command": exc.command,
            "returncode": exc.returncode,
            "stderr": exc.stderr,
            "stdout": exc.stdout,
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    logger.warning(f"Validation error during {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "BadRequest",
            "message": str(exc),
            "path": request.url.path
        }
    )


# Mount Static Files
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register API Routers
app.include_router(knowledge_router)
app.include_router(project_router)


@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Serves the interactive single-page web dashboard."""
    index_file = STATIC_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return {
        "system": "DiffMind",
        "status": "online",
        "version": "0.1.0",
        "docs_url": "/docs",
    }


@app.get("/api", tags=["General"])
async def api_info() -> dict[str, str]:
    """Returns API server metadata."""
    return {
        "system": "DiffMind",
        "status": "online",
        "version": "0.1.0",
        "docs_url": "/docs",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/health", tags=["General"])
async def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "healthy",
        "kb_path": str(settings.resolved_kb_path),
        "llm_provider": settings.LLM_PROVIDER,
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False
    )
