from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import get_memory_service
from core.models.entities import (
    EntityDetail,
    NoteCreate,
    NoteRead,
    PersonCreate,
    PersonRead,
    RelatedEntity,
)
from services.memory.service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/notes", response_model=NoteRead, status_code=201)
def create_note(
    payload: NoteCreate,
    service: MemoryService = Depends(get_memory_service),
) -> NoteRead:
    return service.create_note(payload)


@router.get("/notes", response_model=list[NoteRead])
def list_notes(
    query: str | None = Query(default=None, min_length=1),
    service: MemoryService = Depends(get_memory_service),
) -> list[NoteRead]:
    return service.list_notes(query=query)


@router.post("/people", response_model=PersonRead, status_code=201)
def create_person(
    payload: PersonCreate,
    service: MemoryService = Depends(get_memory_service),
) -> PersonRead:
    return service.create_person(payload)


@router.get("/people", response_model=list[PersonRead])
def list_people(
    service: MemoryService = Depends(get_memory_service),
) -> list[PersonRead]:
    return service.list_people()


@router.get("/search", response_model=list[EntityDetail])
def search_memory(
    query: str = Query(min_length=2),
    limit: int = Query(default=10, ge=1, le=50),
    service: MemoryService = Depends(get_memory_service),
) -> list[EntityDetail]:
    return service.search(query=query, limit=limit)


@router.get("/entities/{entity_id}", response_model=EntityDetail)
def get_entity(
    entity_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> EntityDetail:
    return service.get_entity(entity_id)


@router.get("/entities/{entity_id}/related", response_model=list[RelatedEntity])
def get_related_entities(
    entity_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> list[RelatedEntity]:
    return service.get_related_entities(entity_id)
