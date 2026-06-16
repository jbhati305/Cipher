from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import get_task_service, require_hermes
from core.models.entities import TaskCreate, TaskRead, TaskStatus, TaskUpdate
from services.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=201)
def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
    _: None = Depends(require_hermes),
) -> TaskRead:
    return service.create_task(payload)


@router.get("", response_model=list[TaskRead])
def list_tasks(
    status: TaskStatus | None = None,
    project_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
    _: None = Depends(require_hermes),
) -> list[TaskRead]:
    return service.list_tasks(status=status, project_id=project_id)


@router.get("/overdue", response_model=list[TaskRead])
def list_overdue_tasks(
    service: TaskService = Depends(get_task_service),
    _: None = Depends(require_hermes),
) -> list[TaskRead]:
    return service.list_overdue_tasks()


@router.get("/by-project/{project_id}", response_model=list[TaskRead])
def list_tasks_by_project(
    project_id: str,
    service: TaskService = Depends(get_task_service),
    _: None = Depends(require_hermes),
) -> list[TaskRead]:
    return service.list_tasks(project_id=project_id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    service: TaskService = Depends(get_task_service),
    _: None = Depends(require_hermes),
) -> TaskRead:
    return service.update_task(task_id, payload)


@router.post("/{task_id}/complete", response_model=TaskRead)
def complete_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
    _: None = Depends(require_hermes),
) -> TaskRead:
    return service.complete_task(task_id)
