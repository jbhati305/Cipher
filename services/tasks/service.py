from datetime import datetime

from fastapi import HTTPException, status

from core.models.entities import TaskCreate, TaskRead, TaskStatus, TaskUpdate
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

    def list_tasks_due_between(self, *, start: datetime, end: datetime) -> list[TaskRead]:
        return self._repository.list_tasks_due_between(start=start, end=end)

    def update_task(self, task_id: str, payload: TaskUpdate) -> TaskRead:
        task = self._repository.update_task(task_id, payload)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        return task

    def complete_task(self, task_id: str) -> TaskRead:
        task = self._repository.complete_task(task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        return task
