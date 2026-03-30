import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from apps.api.routes import assistant, calendar, health, memory, projects, reminders, tasks
from core.config import get_settings
from core.utils.logging import configure_logging
from database.neo4j.client import Neo4jGraphClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)

    client = Neo4jGraphClient(settings)
    app.state.settings = settings
    app.state.neo4j_client = client

    try:
        client.start()
    except Exception:
        logger.exception("Neo4j startup failed.")
        if not settings.allow_degraded_startup:
            raise

    yield

    client.close()


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
    app.include_router(calendar.router)
    app.include_router(projects.router)
    app.include_router(tasks.router)
    app.include_router(reminders.router)
    app.include_router(memory.router)
    app.include_router(assistant.router)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("apps.api.main:app", host="127.0.0.1", port=8181, reload=True)
