from fastapi import Depends, HTTPException, Request, status

from core.config import Settings
from core.repositories.graph_repository import Neo4jGraphRepository
from database.neo4j.client import Neo4jGraphClient
from services.assistant.parser import AssistantParserService
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


def get_parser_service(settings: Settings = Depends(get_settings)) -> AssistantParserService:
    return AssistantParserService(default_timezone=settings.default_timezone)
