from datetime import UTC, datetime

from fastapi.testclient import TestClient

from apps.api.dependencies import get_reminder_service, get_task_service
from apps.api.main import create_app
from core.models.entities import (
    ReminderChannel,
    ReminderRead,
    ReminderSnooze,
    ReminderStatus,
    ReminderUpdate,
    TaskPriority,
    TaskRead,
    TaskStatus,
    TaskUpdate,
)


def _task_fixture(
    *,
    status: TaskStatus = TaskStatus.PENDING,
    project_id: str | None = "project-1",
) -> TaskRead:
    now = datetime(2026, 3, 30, 12, 0, tzinfo=UTC)
    return TaskRead(
        id="task-1",
        code="TSK-2603-000001",
        created_at=now,
        updated_at=now,
        title="Follow up with Rahul",
        description="Call back about documents.",
        status=status,
        priority=TaskPriority.HIGH,
        deadline=now,
        estimated_effort="30m",
        project_id=project_id,
        related_entity_ids=["person-1"],
    )


def _reminder_fixture(
    *,
    status: ReminderStatus = ReminderStatus.SCHEDULED,
    trigger_time: datetime | None = None,
) -> ReminderRead:
    now = datetime(2026, 3, 30, 12, 0, tzinfo=UTC)
    return ReminderRead(
        id="reminder-1",
        code="REM-2603-000001",
        created_at=now,
        updated_at=now,
        title="Call Rahul",
        trigger_time=trigger_time or now,
        recurrence_rule=None,
        status=status,
        channel=ReminderChannel.IN_APP,
        related_entity_ids=["person-1", "task-1"],
    )


class FakeTaskService:
    def __init__(self) -> None:
        self.updated: tuple[str, TaskUpdate] | None = None
        self.completed_task_id: str | None = None
        self.list_project_id: str | None = None

    def list_tasks(
        self,
        *,
        status: TaskStatus | None = None,
        project_id: str | None = None,
    ) -> list[TaskRead]:
        self.list_project_id = project_id
        return [_task_fixture(project_id=project_id)]

    def update_task(self, task_id: str, payload: TaskUpdate) -> TaskRead:
        self.updated = (task_id, payload)
        return _task_fixture(status=payload.status or TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str) -> TaskRead:
        self.completed_task_id = task_id
        return _task_fixture(status=TaskStatus.COMPLETED)


class FakeReminderService:
    def __init__(self) -> None:
        self.updated: tuple[str, ReminderUpdate] | None = None
        self.snoozed: tuple[str, ReminderSnooze] | None = None
        self.dismissed_reminder_id: str | None = None

    def update_reminder(self, reminder_id: str, payload: ReminderUpdate) -> ReminderRead:
        self.updated = (reminder_id, payload)
        return _reminder_fixture(
            status=payload.status or ReminderStatus.SCHEDULED,
            trigger_time=payload.trigger_time,
        )

    def snooze_reminder(self, reminder_id: str, payload: ReminderSnooze) -> ReminderRead:
        self.snoozed = (reminder_id, payload)
        return _reminder_fixture(status=ReminderStatus.SNOOZED, trigger_time=payload.until)

    def dismiss_reminder(self, reminder_id: str) -> ReminderRead:
        self.dismissed_reminder_id = reminder_id
        return _reminder_fixture(status=ReminderStatus.DISMISSED)


def test_patch_task_endpoint_updates_task() -> None:
    app = create_app()
    service = FakeTaskService()
    app.dependency_overrides[get_task_service] = lambda: service

    with TestClient(app) as client:
        response = client.patch(
            "/tasks/task-1",
            json={"status": "in_progress", "priority": "urgent", "related_entity_ids": []},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    assert service.updated is not None
    assert service.updated[0] == "task-1"
    assert service.updated[1].model_dump(exclude_unset=True)["related_entity_ids"] == []


def test_complete_task_endpoint_marks_task_completed() -> None:
    app = create_app()
    service = FakeTaskService()
    app.dependency_overrides[get_task_service] = lambda: service

    with TestClient(app) as client:
        response = client.post("/tasks/task-1/complete")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert service.completed_task_id == "task-1"


def test_list_tasks_by_project_endpoint_uses_project_filter() -> None:
    app = create_app()
    service = FakeTaskService()
    app.dependency_overrides[get_task_service] = lambda: service

    with TestClient(app) as client:
        response = client.get("/tasks/by-project/project-42")

    assert response.status_code == 200
    assert response.json()[0]["project_id"] == "project-42"
    assert service.list_project_id == "project-42"


def test_patch_reminder_endpoint_updates_reminder() -> None:
    app = create_app()
    service = FakeReminderService()
    app.dependency_overrides[get_reminder_service] = lambda: service
    trigger_time = "2026-04-01T13:00:00Z"

    with TestClient(app) as client:
        response = client.patch(
            "/reminders/reminder-1",
            json={"status": "scheduled", "trigger_time": trigger_time},
        )

    assert response.status_code == 200
    assert response.json()["trigger_time"] == trigger_time
    assert service.updated is not None
    assert service.updated[0] == "reminder-1"


def test_snooze_reminder_endpoint_updates_status_and_trigger_time() -> None:
    app = create_app()
    service = FakeReminderService()
    app.dependency_overrides[get_reminder_service] = lambda: service
    snooze_until = "2026-04-01T19:00:00Z"

    with TestClient(app) as client:
        response = client.post(
            "/reminders/reminder-1/snooze",
            json={"until": snooze_until},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "snoozed"
    assert response.json()["trigger_time"] == snooze_until
    assert service.snoozed is not None
    assert service.snoozed[0] == "reminder-1"


def test_dismiss_reminder_endpoint_marks_reminder_dismissed() -> None:
    app = create_app()
    service = FakeReminderService()
    app.dependency_overrides[get_reminder_service] = lambda: service

    with TestClient(app) as client:
        response = client.post("/reminders/reminder-1/dismiss")

    assert response.status_code == 200
    assert response.json()["status"] == "dismissed"
    assert service.dismissed_reminder_id == "reminder-1"
