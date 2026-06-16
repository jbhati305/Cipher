from core.models.entities import MemoryWrite, ProjectCreate, ProjectRead
from services.memory.service import MemoryService
from storage.sqlite import SQLiteRepository


class ProjectService:
    def __init__(
        self,
        repository: SQLiteRepository,
        memory_service: MemoryService | None = None,
    ) -> None:
        self._repository = repository
        self._memory_service = memory_service

    def create_project(self, payload: ProjectCreate) -> ProjectRead:
        if self._memory_service is not None:
            self._memory_service.write(
                MemoryWrite(
                    content=f"Project created: {payload.name}. {payload.description or ''}".strip(),
                    kind="project",
                    source="cipher",
                    tags=["project", payload.status.value],
                    metadata=payload.model_dump(mode="json"),
                )
            )
        return self._repository.create_project(payload)

    def list_projects(self) -> list[ProjectRead]:
        return self._repository.list_projects()
