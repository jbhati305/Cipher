from datetime import datetime

from fastapi import HTTPException, status

from core.models.entities import MemoryWrite, TaskCreate, TaskRead, TaskStatus, TaskUpdate
from services.memory.service import MemoryService
from storage.sqlite import SQLiteRepository


class TaskService:
    def __init__(
        self,
        repository: SQLiteRepository,
        memory_service: MemoryService | None = None,
    ) -> None:
        self._repository = repository
        self._memory_service = memory_service

    def create_task(self, payload: TaskCreate) -> TaskRead:
        self._write_memory(
            f"Task created: {payload.title}. {payload.description or ''}".strip(),
            tags=["task", payload.status.value, payload.priority.value],
            metadata=payload.model_dump(mode="json"),
        )
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
        self._write_memory(
            f"Task updated: {task_id}",
            tags=["task", "updated"],
            metadata={
                "task_id": task_id,
                "updates": payload.model_dump(exclude_unset=True, mode="json"),
            },
        )
        task = self._repository.update_task(task_id, payload)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        return task

    def complete_task(self, task_id: str) -> TaskRead:
        self._write_memory(
            f"Task completed: {task_id}",
            tags=["task", "completed"],
            metadata={"task_id": task_id},
        )
        task = self._repository.complete_task(task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        return task

    def _write_memory(self, content: str, *, tags: list[str], metadata: dict) -> None:
        if self._memory_service is None:
            return
        self._memory_service.write(
            MemoryWrite(
                content=content,
                kind="task",
                source="cipher",
                tags=tags,
                metadata=metadata,
            )
        )
