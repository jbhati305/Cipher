from datetime import datetime

from core.models.entities import ReminderCreate, ReminderRead
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
