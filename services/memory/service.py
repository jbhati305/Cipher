from core.models.entities import (
    MemoryRecord,
    MemorySearchResult,
    MemoryWrite,
    NoteCreate,
    NoteRead,
    PersonCreate,
    PersonRead,
)
from services.memory.memos_client import MemOSClient
from storage.sqlite import SQLiteRepository


class MemoryService:
    def __init__(self, repository: SQLiteRepository, memos_client: MemOSClient) -> None:
        self._repository = repository
        self._memos_client = memos_client

    def write(self, payload: MemoryWrite) -> MemoryRecord:
        record = self._memos_client.write(payload)
        return self._repository.record_memory(record)

    def search(self, *, query: str, limit: int) -> list[MemorySearchResult]:
        return self._memos_client.search(query, limit=limit)

    def recent(self, *, limit: int = 50) -> list[MemoryRecord]:
        return self._repository.list_memory_events(limit=limit)

    def create_note(self, payload: NoteCreate) -> NoteRead:
        record = self.write(
            MemoryWrite(
                content=payload.content,
                kind="note",
                source=payload.source or "cipher",
                tags=["note"],
                metadata={"title": payload.title or self._derive_note_title(payload.content)},
            )
        )
        return NoteRead(
            id=record.id,
            code=record.id,
            title=record.metadata.get("title") or "Untitled note",
            content=record.content,
            source=record.source,
            related_entity_ids=[],
            created_at=record.created_at,
            updated_at=record.created_at,
        )

    def list_notes(self, *, query: str | None = None) -> list[NoteRead]:
        records = self.recent(limit=50)
        if query:
            records = [record for record in records if query.lower() in record.content.lower()]
        return [
            NoteRead(
                id=record.id,
                code=record.id,
                title=record.metadata.get("title") or self._derive_note_title(record.content),
                content=record.content,
                source=record.source,
                related_entity_ids=[],
                created_at=record.created_at,
                updated_at=record.created_at,
            )
            for record in records
            if record.kind == "note"
        ]

    def create_person(self, payload: PersonCreate) -> PersonRead:
        record = self.write(
            MemoryWrite(
                content=f"Person: {payload.name}. {payload.notes or ''}".strip(),
                kind="person",
                source="cipher",
                tags=["person"],
                metadata=payload.model_dump(mode="json"),
            )
        )
        return PersonRead(
            id=record.id,
            code=record.id,
            name=payload.name,
            relationship_type=payload.relationship_type,
            notes=payload.notes,
            created_at=record.created_at,
            updated_at=record.created_at,
        )

    def list_people(self) -> list[PersonRead]:
        return [
            PersonRead(
                id=record.id,
                code=record.id,
                name=record.metadata.get("name") or record.content,
                relationship_type=record.metadata.get("relationship_type"),
                notes=record.metadata.get("notes"),
                created_at=record.created_at,
                updated_at=record.created_at,
            )
            for record in self.recent(limit=100)
            if record.kind == "person"
        ]

    @staticmethod
    def _derive_note_title(content: str) -> str:
        title = content.strip().split(".")[0].strip()
        return (title[:60] or "Untitled note").rstrip()
