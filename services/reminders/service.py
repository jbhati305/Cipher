from datetime import datetime

from fastapi import HTTPException, status

from core.models.entities import (
    MemoryWrite,
    ReminderCreate,
    ReminderRead,
    ReminderSnooze,
    ReminderUpdate,
)
from services.memory.service import MemoryService
from storage.sqlite import SQLiteRepository


class ReminderService:
    def __init__(
        self,
        repository: SQLiteRepository,
        memory_service: MemoryService | None = None,
    ) -> None:
        self._repository = repository
        self._memory_service = memory_service

    def create_reminder(self, payload: ReminderCreate) -> ReminderRead:
        self._write_memory(
            f"Reminder created: {payload.title} at {payload.trigger_time.isoformat()}",
            tags=["reminder", payload.status.value],
            metadata=payload.model_dump(mode="json"),
        )
        return self._repository.create_reminder(payload)

    def list_reminders(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[ReminderRead]:
        return self._repository.list_reminders(start=start, end=end)

    def list_schedulable_reminders(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[ReminderRead]:
        return self._repository.list_schedulable_reminders(start=start, end=end)

    def get_reminder(self, reminder_id: str) -> ReminderRead:
        reminder = self._repository.get_reminder(reminder_id)
        if reminder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")
        return reminder

    def update_reminder(self, reminder_id: str, payload: ReminderUpdate) -> ReminderRead:
        self._write_memory(
            f"Reminder updated: {reminder_id}",
            tags=["reminder", "updated"],
            metadata={
                "reminder_id": reminder_id,
                "updates": payload.model_dump(exclude_unset=True, mode="json"),
            },
        )
        reminder = self._repository.update_reminder(reminder_id, payload)
        if reminder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")
        return reminder

    def snooze_reminder(self, reminder_id: str, payload: ReminderSnooze) -> ReminderRead:
        self._write_memory(
            f"Reminder snoozed: {reminder_id} until {payload.until.isoformat()}",
            tags=["reminder", "snoozed"],
            metadata={"reminder_id": reminder_id, "until": payload.until.isoformat()},
        )
        reminder = self._repository.snooze_reminder(reminder_id, payload.until)
        if reminder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")
        return reminder

    def dismiss_reminder(self, reminder_id: str) -> ReminderRead:
        self._write_memory(
            f"Reminder dismissed: {reminder_id}",
            tags=["reminder", "dismissed"],
            metadata={"reminder_id": reminder_id},
        )
        reminder = self._repository.dismiss_reminder(reminder_id)
        if reminder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")
        return reminder

    def _write_memory(self, content: str, *, tags: list[str], metadata: dict) -> None:
        if self._memory_service is None:
            return
        self._memory_service.write(
            MemoryWrite(
                content=content,
                kind="reminder",
                source="cipher",
                tags=tags,
                metadata=metadata,
            )
        )

    def record_trigger(
        self,
        reminder_id: str,
        *,
        triggered_at: datetime,
        next_trigger_time: datetime | None,
    ) -> ReminderRead:
        reminder = self._repository.record_reminder_trigger(
            reminder_id,
            triggered_at=triggered_at,
            next_trigger_time=next_trigger_time,
        )
        if reminder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")
        return reminder
