from datetime import datetime

from fastapi import HTTPException, status

from core.models.entities import ReminderCreate, ReminderRead, ReminderSnooze, ReminderUpdate
from core.repositories.graph_repository import Neo4jGraphRepository


class ReminderService:
    def __init__(self, repository: Neo4jGraphRepository) -> None:
        self._repository = repository

    def create_reminder(self, payload: ReminderCreate) -> ReminderRead:
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
        reminder = self._repository.update_reminder(reminder_id, payload)
        if reminder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")
        return reminder

    def snooze_reminder(self, reminder_id: str, payload: ReminderSnooze) -> ReminderRead:
        reminder = self._repository.snooze_reminder(reminder_id, payload.until)
        if reminder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")
        return reminder

    def dismiss_reminder(self, reminder_id: str) -> ReminderRead:
        reminder = self._repository.dismiss_reminder(reminder_id)
        if reminder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")
        return reminder

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
