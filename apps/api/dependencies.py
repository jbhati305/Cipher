from fastapi import Depends, HTTPException, Request, status

from core.config import Settings
from core.repositories.graph_repository import Neo4jGraphRepository
from database.neo4j.client import Neo4jGraphClient
from services.assistant.context import AssistantContextService
from services.assistant.parser import AssistantParserService
from services.assistant.service import AssistantService
from services.calendar.provider import GoogleCalendarProvider
from services.calendar.service import CalendarService
from services.llm import build_llm_provider
from services.memory.service import MemoryService
from services.projects.service import ProjectService
from services.reminders.service import ReminderService
from services.tasks.service import TaskService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_graph_client(request: Request) -> Neo4jGraphClient:
    return request.app.state.neo4j_client


def get_repository(
    client: Neo4jGraphClient = Depends(get_graph_client),
    settings: Settings = Depends(get_settings),
) -> Neo4jGraphRepository:
    if not client.is_ready:
        detail = client.last_error or "Neo4j is not configured or available."
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    return Neo4jGraphRepository(driver=client.driver, database=settings.neo4j_database)


def get_project_service(
    repository: Neo4jGraphRepository = Depends(get_repository),
) -> ProjectService:
    return ProjectService(repository)


def get_task_service(repository: Neo4jGraphRepository = Depends(get_repository)) -> TaskService:
    return TaskService(repository)


def get_reminder_service(
    repository: Neo4jGraphRepository = Depends(get_repository),
) -> ReminderService:
    return ReminderService(repository)


def get_memory_service(
    repository: Neo4jGraphRepository = Depends(get_repository),
) -> MemoryService:
    return MemoryService(repository)


def get_calendar_service(settings: Settings = Depends(get_settings)) -> CalendarService:
    return CalendarService(GoogleCalendarProvider(settings))


def get_parser_service(settings: Settings = Depends(get_settings)) -> AssistantParserService:
    return AssistantParserService(default_timezone=settings.default_timezone)


def get_assistant_service(
    settings: Settings = Depends(get_settings),
    calendar_service: CalendarService = Depends(get_calendar_service),
    reminder_service: ReminderService = Depends(get_reminder_service),
    task_service: TaskService = Depends(get_task_service),
    project_service: ProjectService = Depends(get_project_service),
    memory_service: MemoryService = Depends(get_memory_service),
) -> AssistantService:
    context_service = AssistantContextService(
        calendar_service=calendar_service,
        reminder_service=reminder_service,
        task_service=task_service,
        project_service=project_service,
        memory_service=memory_service,
        default_timezone=settings.default_timezone,
        max_context_items=settings.llm_max_context_items,
    )
    return AssistantService(
        context_service=context_service,
        llm_provider=build_llm_provider(settings),
        default_timezone=settings.default_timezone,
        llm_max_output_tokens=settings.llm_max_output_tokens,
        llm_note_char_limit=settings.llm_note_char_limit,
    )


def get_briefing_service(
    assistant_service: AssistantService = Depends(get_assistant_service),
) -> AssistantService:
    return assistant_service
