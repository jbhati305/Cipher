from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import Settings
from exports import ExportService
from services.calendar.provider import GoogleCalendarProvider
from services.calendar.service import CalendarService
from services.llm.local_router import LocalFirstLLMRouter
from services.llm.routing import ModelRoutingPolicy
from services.memory.memos_client import MemOSClient
from services.memory.service import MemoryService
from services.notion import NotionPaperService
from services.projects.service import ProjectService
from services.reminders.service import ReminderService
from services.tasks.service import TaskService
from services.voice import VoiceBridgeService
from storage import SQLiteRepository

security = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_repository(request: Request) -> SQLiteRepository:
    return request.app.state.repository


def get_memos_client(request: Request) -> MemOSClient:
    return request.app.state.memos_client


def get_model_policy(request: Request) -> ModelRoutingPolicy:
    return request.app.state.model_policy


def get_llm_router(request: Request) -> LocalFirstLLMRouter:
    return request.app.state.llm_router


def require_admin(
    settings: Settings = Depends(get_settings),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> None:
    _require_token(settings, credentials, {settings.admin_token})


def require_alexa(
    settings: Settings = Depends(get_settings),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> None:
    _require_token(settings, credentials, {settings.alexa_token, settings.admin_token})


def require_hermes(
    settings: Settings = Depends(get_settings),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> None:
    _require_token(settings, credentials, {settings.hermes_token, settings.admin_token})


def get_memory_service(
    repository: SQLiteRepository = Depends(get_repository),
    memos_client: MemOSClient = Depends(get_memos_client),
) -> MemoryService:
    return MemoryService(repository, memos_client)


def get_project_service(
    repository: SQLiteRepository = Depends(get_repository),
    memory_service: MemoryService = Depends(get_memory_service),
) -> ProjectService:
    return ProjectService(repository, memory_service)


def get_task_service(
    repository: SQLiteRepository = Depends(get_repository),
    memory_service: MemoryService = Depends(get_memory_service),
) -> TaskService:
    return TaskService(repository, memory_service)


def get_reminder_service(
    repository: SQLiteRepository = Depends(get_repository),
    memory_service: MemoryService = Depends(get_memory_service),
) -> ReminderService:
    return ReminderService(repository, memory_service)


def get_calendar_service(settings: Settings = Depends(get_settings)) -> CalendarService:
    return CalendarService(GoogleCalendarProvider(settings))


def get_notion_paper_service(
    settings: Settings = Depends(get_settings),
    repository: SQLiteRepository = Depends(get_repository),
    memory_service: MemoryService = Depends(get_memory_service),
) -> NotionPaperService:
    return NotionPaperService(
        settings=settings,
        repository=repository,
        memory_service=memory_service,
    )


def get_voice_service(
    memory_service: MemoryService = Depends(get_memory_service),
    llm_router: LocalFirstLLMRouter = Depends(get_llm_router),
) -> VoiceBridgeService:
    return VoiceBridgeService(memory_service=memory_service, llm_router=llm_router)


def get_export_service(
    settings: Settings = Depends(get_settings),
    repository: SQLiteRepository = Depends(get_repository),
) -> ExportService:
    return ExportService(settings=settings, repository=repository)


def _require_token(
    settings: Settings,
    credentials: HTTPAuthorizationCredentials | None,
    allowed_tokens: set[str | None],
) -> None:
    if not settings.auth_required:
        return
    configured = {token for token in allowed_tokens if token}
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is enabled but no matching token is configured.",
        )
    if credentials is None or credentials.credentials not in configured:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized.")
