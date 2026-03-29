from core.models.entities import TaskCreate, TaskRead, TaskStatus
from core.repositories.graph_repository import Neo4jGraphRepository


class TaskService:
    def __init__(self, repository: Neo4jGraphRepository) -> None:
        self._repository = repository

    def create_task(self, payload: TaskCreate) -> TaskRead:
        return self._repository.create_task(payload)

    def list_tasks(
        self,
        *,
        status: TaskStatus | None = None,
        project_id: str | None = None,
    ) -> list[TaskRead]:
        return self._repository.list_tasks(status=status, project_id=project_id)

    def list_overdue_tasks(self) -> list[TaskRead]:
        return self._repository.list_overdue_tasks()
