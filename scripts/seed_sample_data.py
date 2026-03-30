import json
from datetime import timedelta
from zoneinfo import ZoneInfo

from core.config import get_settings
from core.models.entities import (
    NoteCreate,
    PersonCreate,
    ProjectCreate,
    ReminderChannel,
    ReminderCreate,
    TaskCreate,
    TaskPriority,
)
from core.repositories.graph_repository import Neo4jGraphRepository
from core.utils.dates import utc_now
from database.neo4j.client import Neo4jGraphClient
from services.memory.service import MemoryService
from services.projects.service import ProjectService
from services.reminders.service import ReminderService
from services.tasks.service import TaskService


def main() -> None:
    settings = get_settings()
    client = Neo4jGraphClient(settings)
    client.start()

    if not client.is_ready:
        raise SystemExit(client.last_error or "Neo4j is not ready.")

    try:
        repository = Neo4jGraphRepository(driver=client.driver, database=settings.neo4j_database)
        memory_service = MemoryService(repository)
        project_service = ProjectService(repository)
        task_service = TaskService(repository)
        reminder_service = ReminderService(repository)

        timezone = ZoneInfo(settings.default_timezone)
        now = utc_now().astimezone(timezone)

        person = memory_service.create_person(
            PersonCreate(
                name="Rahul Sharma",
                relationship_type="friend",
                notes="Rahul works at Infosys and prefers evening calls.",
            )
        )
        project = project_service.create_project(
            ProjectCreate(
                name="Health Insurance Renewal",
                description="Renew family health insurance before the due date.",
                priority=TaskPriority.HIGH,
            )
        )
        task = task_service.create_task(
            TaskCreate(
                title="Call Rahul about insurance documents",
                description="Ask Rahul to send the required PDF documents.",
                priority=TaskPriority.URGENT,
                deadline=now + timedelta(days=3),
                estimated_effort="30m",
                project_id=project.id,
                related_entity_ids=[person.id],
            )
        )
        reminder = reminder_service.create_reminder(
            ReminderCreate(
                title="Follow up with Rahul tomorrow evening",
                trigger_time=now + timedelta(days=1, hours=1),
                recurrence_rule="daily",
                channel=ReminderChannel.IN_APP,
                related_entity_ids=[person.id, task.id],
            )
        )
        note = memory_service.create_note(
            NoteCreate(
                title="Insurance renewal context",
                content=(
                    "Rahul said the salary slip and Aadhaar copy will be shared by tonight. "
                    "Renewal must be completed this week."
                ),
                source="seed-script",
                related_entity_ids=[person.id, project.id, task.id],
            )
        )

        print(
            json.dumps(
                {
                    "seeded": {
                        "person": {"id": person.id, "code": person.code, "name": person.name},
                        "project": {"id": project.id, "code": project.code, "name": project.name},
                        "task": {"id": task.id, "code": task.code, "title": task.title},
                        "reminder": {
                            "id": reminder.id,
                            "code": reminder.code,
                            "title": reminder.title,
                        },
                        "note": {"id": note.id, "code": note.code, "title": note.title},
                    }
                },
                indent=2,
            )
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
