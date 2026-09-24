# app/routers/__init__.py
from app.routers.knowledge_router import router as knowledge_router
from app.routers.project_router import router as project_router

__all__ = ["knowledge_router", "project_router"]
