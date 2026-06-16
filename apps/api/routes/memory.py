from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import get_memory_service, require_hermes
from core.models.entities import MemoryRecord, MemorySearchResult, MemoryWrite, NoteCreate, NoteRead
from services.memory.service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/write", response_model=MemoryRecord, status_code=201)
def write_memory(
    payload: MemoryWrite,
    service: MemoryService = Depends(get_memory_service),
    _: None = Depends(require_hermes),
) -> MemoryRecord:
    return service.write(payload)


@router.get("/search", response_model=list[MemorySearchResult])
def search_memory(
    query: str = Query(min_length=2),
    limit: int = Query(default=10, ge=1, le=50),
    service: MemoryService = Depends(get_memory_service),
    _: None = Depends(require_hermes),
) -> list[MemorySearchResult]:
    return service.search(query=query, limit=limit)


@router.get("/recent", response_model=list[MemoryRecord])
def recent_memory(
    limit: int = Query(default=50, ge=1, le=200),
    service: MemoryService = Depends(get_memory_service),
    _: None = Depends(require_hermes),
) -> list[MemoryRecord]:
    return service.recent(limit=limit)


@router.post("/notes", response_model=NoteRead, status_code=201)
def create_note(
    payload: NoteCreate,
    service: MemoryService = Depends(get_memory_service),
    _: None = Depends(require_hermes),
) -> NoteRead:
    return service.create_note(payload)


@router.get("/notes", response_model=list[NoteRead])
def list_notes(
    query: str | None = Query(default=None, min_length=1),
    service: MemoryService = Depends(get_memory_service),
    _: None = Depends(require_hermes),
) -> list[NoteRead]:
    return service.list_notes(query=query)
