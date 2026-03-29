from core.models.entities import ProjectCreate, ProjectRead
from core.repositories.graph_repository import Neo4jGraphRepository


class ProjectService:
    def __init__(self, repository: Neo4jGraphRepository) -> None:
        self._repository = repository

    def create_project(self, payload: ProjectCreate) -> ProjectRead:
        return self._repository.create_project(payload)

    def list_projects(self) -> list[ProjectRead]:
        return self._repository.list_projects()
