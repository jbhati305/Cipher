from datetime import datetime
from typing import Any

from core.config import Settings
from core.models.entities import (
    EventCreate,
    EventUpdate,
    MemoryWrite,
    ProjectCreate,
    ReminderCreate,
    ReminderSnooze,
    ReminderUpdate,
    TaskCreate,
    TaskStatus,
    TaskUpdate,
)
from services.calendar.provider import GoogleCalendarProvider
from services.calendar.service import CalendarService
from services.memory.memos_client import MemOSClient
from services.memory.service import MemoryService
from services.notion import NotionPaperService
from services.projects.service import ProjectService
from services.reminders.service import ReminderService
from services.tasks.service import TaskService
from storage import SQLiteRepository


class CipherToolRegistry:
    def __init__(self, settings: Settings) -> None:
        repository = SQLiteRepository(settings.resolved_sqlite_path)
        memory = MemoryService(repository, MemOSClient(settings))
        self._repository = repository
        self._memory = memory
        self._projects = ProjectService(repository, memory)
        self._tasks = TaskService(repository, memory)
        self._reminders = ReminderService(repository, memory)
        self._calendar = CalendarService(GoogleCalendarProvider(settings))
        self._notion = NotionPaperService(
            settings=settings,
            repository=repository,
            memory_service=memory,
        )

    def list_tools(self) -> list[str]:
        return sorted(name for name in dir(self) if name.startswith("cipher_"))

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self.list_tools():
            raise ValueError(f"Unknown Cipher tool: {name}")
        return getattr(self, name)(**arguments)

    def cipher_project_create(self, **kwargs) -> dict:
        return self._projects.create_project(ProjectCreate(**kwargs)).model_dump(mode="json")

    def cipher_project_list(self) -> list[dict]:
        return [item.model_dump(mode="json") for item in self._projects.list_projects()]

    def cipher_task_create(self, **kwargs) -> dict:
        return self._tasks.create_task(TaskCreate(**kwargs)).model_dump(mode="json")

    def cipher_task_list(
        self,
        status: str | None = None,
        project_id: str | None = None,
    ) -> list[dict]:
        parsed_status = TaskStatus(status) if status else None
        return [
            item.model_dump(mode="json")
            for item in self._tasks.list_tasks(status=parsed_status, project_id=project_id)
        ]

    def cipher_task_update(self, task_id: str, **kwargs) -> dict:
        return self._tasks.update_task(task_id, TaskUpdate(**kwargs)).model_dump(mode="json")

    def cipher_task_complete(self, task_id: str) -> dict:
        return self._tasks.complete_task(task_id).model_dump(mode="json")

    def cipher_calendar_list_events(
        self,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict]:
        return [
            item.model_dump(mode="json")
            for item in self._calendar.list_events(
                start=datetime.fromisoformat(start) if start else None,
                end=datetime.fromisoformat(end) if end else None,
            )
        ]

    def cipher_calendar_create_event(self, **kwargs) -> dict:
        return self._calendar.create_event(EventCreate(**kwargs)).model_dump(mode="json")

    def cipher_calendar_update_event(self, event_id: str, **kwargs) -> dict:
        return self._calendar.update_event(event_id, EventUpdate(**kwargs)).model_dump(mode="json")

    def cipher_calendar_find_free_slots(
        self,
        start: str,
        end: str,
        duration_minutes: int = 60,
    ) -> list[dict]:
        return [
            item.model_dump(mode="json")
            for item in self._calendar.get_free_slots(
                start=datetime.fromisoformat(start),
                end=datetime.fromisoformat(end),
                duration_minutes=duration_minutes,
            )
        ]

    def cipher_memory_search(self, query: str, limit: int = 10) -> list[dict]:
        return [
            item.model_dump(mode="json") for item in self._memory.search(query=query, limit=limit)
        ]

    def cipher_memory_write(self, **kwargs) -> dict:
        return self._memory.write(MemoryWrite(**kwargs)).model_dump(mode="json")

    def cipher_daily_reflection_start(self, prompt: str | None = None) -> dict:
        content = prompt or "Daily reflection started."
        return self._memory.write(
            MemoryWrite(
                content=content,
                kind="daily_reflection",
                source="cipher",
                tags=["reflection"],
            )
        ).model_dump(mode="json")

    def cipher_daily_summary(self) -> list[dict]:
        return [item.model_dump(mode="json") for item in self._memory.recent(limit=20)]

    def cipher_notion_papers_sync(self) -> dict:
        return self._notion.sync()

    def cipher_notion_papers_list(self) -> list[dict]:
        return [item.model_dump(mode="json") for item in self._notion.list_papers()]

    def cipher_reminder_create(self, **kwargs) -> dict:
        return self._reminders.create_reminder(ReminderCreate(**kwargs)).model_dump(mode="json")

    def cipher_reminder_list(self) -> list[dict]:
        return [item.model_dump(mode="json") for item in self._reminders.list_reminders()]

    def cipher_reminder_update(self, reminder_id: str, **kwargs) -> dict:
        return self._reminders.update_reminder(
            reminder_id,
            ReminderUpdate(**kwargs),
        ).model_dump(mode="json")

    def cipher_reminder_snooze(self, reminder_id: str, until: str) -> dict:
        return self._reminders.snooze_reminder(
            reminder_id,
            ReminderSnooze(until=datetime.fromisoformat(until)),
        ).model_dump(mode="json")

    def cipher_reminder_dismiss(self, reminder_id: str) -> dict:
        return self._reminders.dismiss_reminder(reminder_id).model_dump(mode="json")

    def cipher_reminder_due(self, start: str, end: str) -> list[dict]:
        return [
            item.model_dump(mode="json")
            for item in self._reminders.list_schedulable_reminders(
                start=datetime.fromisoformat(start),
                end=datetime.fromisoformat(end),
            )
        ]
