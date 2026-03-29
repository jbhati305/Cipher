from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import get_task_service
from core.models.entities import TaskCreate, TaskRead, TaskStatus
from services.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=201)
def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    return service.create_task(payload)


@router.get("", response_model=list[TaskRead])
def list_tasks(
    status: TaskStatus | None = None,
    project_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> list[TaskRead]:
    return service.list_tasks(status=status, project_id=project_id)


@router.get("/overdue", response_model=list[TaskRead])
def list_overdue_tasks(
    service: TaskService = Depends(get_task_service),
) -> list[TaskRead]:
    return service.list_overdue_tasks()
