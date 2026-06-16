import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from apps.api.routes import (
    admin,
    calendar,
    dashboard,
    health,
    memory,
    notion,
    projects,
    reminders,
    tasks,
    voice,
)
from core.config import get_settings
from core.utils.logging import configure_logging
from services.llm.local_router import LocalFirstLLMRouter
from services.llm.routing import ModelRoutingPolicy
from services.memory.memos_client import MemOSClient
from storage import SQLiteRepository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)

    settings.resolved_data_dir.mkdir(parents=True, exist_ok=True)
    repository = SQLiteRepository(settings.resolved_sqlite_path)
    memos_client = MemOSClient(settings)
    model_policy = ModelRoutingPolicy(settings)
    llm_router = LocalFirstLLMRouter(settings, model_policy)

    app.state.settings = settings
    app.state.repository = repository
    app.state.memos_client = memos_client
    app.state.model_policy = model_policy
    app.state.llm_router = llm_router

    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started_at = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "%s %s -> %s in %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled application error on %s %s",
            request.method,
            request.url.path,
            exc_info=exc,
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    app.include_router(health.router)
    app.include_router(dashboard.router)
    app.include_router(calendar.router, prefix="/api")
    app.include_router(projects.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(reminders.router, prefix="/api")
    app.include_router(memory.router, prefix="/api")
    app.include_router(notion.router, prefix="/api")
    app.include_router(voice.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")
    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "apps.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
    )
