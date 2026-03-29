from fastapi import APIRouter, Depends

from apps.api.dependencies import get_project_service
from core.models.entities import ProjectCreate, ProjectRead
from services.projects.service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(
    payload: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    return service.create_project(payload)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    service: ProjectService = Depends(get_project_service),
) -> list[ProjectRead]:
    return service.list_projects()
