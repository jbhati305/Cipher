from datetime import UTC, datetime

from core.models.entities import ProjectCreate, ReminderChannel, ReminderCreate, TaskCreate
from storage.sqlite import SQLiteRepository


def test_sqlite_repository_projects_tasks_and_reminders(tmp_path):
    repository = SQLiteRepository(tmp_path / "cipher.sqlite3")

    project = repository.create_project(ProjectCreate(name="Cipher"))
    task = repository.create_task(TaskCreate(title="Wire MemOS", project_id=project.id))
    reminder = repository.create_reminder(
        ReminderCreate(
            title="Reflect",
            trigger_time=datetime(2026, 6, 15, 22, 0, tzinfo=UTC),
            channel=ReminderChannel.IN_APP,
        )
    )

    assert repository.list_projects()[0].name == "Cipher"
    assert repository.list_tasks(project_id=project.id)[0].id == task.id
    assert repository.list_reminders()[0].id == reminder.id
    assert repository.list_audit_events(limit=10)
