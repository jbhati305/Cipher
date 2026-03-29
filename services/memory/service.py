from fastapi import HTTPException, status

from core.models.entities import (
    EntityDetail,
    NoteCreate,
    NoteRead,
    PersonCreate,
    PersonRead,
    RelatedEntity,
)
from core.repositories.graph_repository import Neo4jGraphRepository


class MemoryService:
    def __init__(self, repository: Neo4jGraphRepository) -> None:
        self._repository = repository

    def create_note(self, payload: NoteCreate) -> NoteRead:
        title = payload.title or self._derive_note_title(payload.content)
        return self._repository.create_note(payload.model_copy(update={"title": title}))

    def list_notes(self, *, query: str | None = None) -> list[NoteRead]:
        return self._repository.list_notes(query=query)

    def create_person(self, payload: PersonCreate) -> PersonRead:
        return self._repository.create_person(payload)

    def list_people(self) -> list[PersonRead]:
        return self._repository.list_people()

    def search(self, *, query: str, limit: int) -> list[EntityDetail]:
        return self._repository.search(query=query, limit=limit)

    def get_entity(self, entity_id: str) -> EntityDetail:
        entity = self._repository.get_entity(entity_id)
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found.")
        return entity

    def get_related_entities(self, entity_id: str) -> list[RelatedEntity]:
        self.get_entity(entity_id)
        return self._repository.get_related_entities(entity_id)

    @staticmethod
    def _derive_note_title(content: str) -> str:
        title = content.strip().split(".")[0].strip()
        return (title[:60] or "Untitled note").rstrip()
