from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from apps.api.dependencies import get_briefing_service, get_calendar_service
from apps.api.main import create_app
from core.models.assistant import DailyBriefing
from core.models.entities import (
    EventRead,
    FreeSlotRead,
    ReminderChannel,
    ReminderRead,
    TaskPriority,
    TaskRead,
    TaskStatus,
)
from services.calendar.service import CalendarService


def _event_fixture(
    *,
    start_time: datetime,
    end_time: datetime,
    event_id: str = "event-1",
) -> EventRead:
    return EventRead(
        id=event_id,
        code="EVT-2604-000001",
        created_at=start_time,
        updated_at=start_time,
        title="Planning block",
        start_time=start_time,
        end_time=end_time,
        location="Desk",
        description="Focus block",
        related_entity_ids=[],
    )


class FakeCalendarProvider:
    def create_event(self, payload):  # noqa: ANN001
        now = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
        return _event_fixture(start_time=now, end_time=now.replace(hour=10))

    def list_events(self, *, start=None, end=None):  # noqa: ANN001, ANN201
        return [
            _event_fixture(
                start_time=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
                end_time=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                event_id="event-1",
            ),
            _event_fixture(
                start_time=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
                end_time=datetime(2026, 4, 1, 13, 0, tzinfo=UTC),
                event_id="event-2",
            ),
        ]

    def update_event(self, event_id: str, payload):  # noqa: ANN001
        now = datetime(2026, 4, 1, 11, 0, tzinfo=UTC)
        return _event_fixture(start_time=now, end_time=now.replace(hour=12), event_id=event_id)


class FakeBriefingService:
    def get_daily_briefing(self, *, target_date=None):  # noqa: ANN001, ANN201
        now = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
        return DailyBriefing(
            date=target_date or date(2026, 4, 1),
            timezone="Asia/Kolkata",
            events=[
                _event_fixture(
                    start_time=now,
                    end_time=now.replace(hour=10),
                )
            ],
            reminders=[
                ReminderRead(
                    id="reminder-1",
                    code="REM-2604-000001",
                    created_at=now,
                    updated_at=now,
                    title="Call Rahul",
                    trigger_time=now,
                    recurrence_rule="daily",
                    status="scheduled",
                    channel=ReminderChannel.IN_APP,
                    last_triggered_at=None,
                    trigger_count=0,
                    related_entity_ids=[],
                )
            ],
            due_tasks=[
                TaskRead(
                    id="task-1",
                    code="TSK-2604-000001",
                    created_at=now,
                    updated_at=now,
                    title="Review renewal docs",
                    description=None,
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.HIGH,
                    deadline=now,
                    estimated_effort="30m",
                    project_id=None,
                    related_entity_ids=[],
                )
            ],
            overdue_tasks=[],
            summary_lines=["1 events, 1 reminders, 1 due tasks."],
        )


def test_calendar_service_returns_free_slots_between_events() -> None:
    service = CalendarService(FakeCalendarProvider())

    result = service.get_free_slots(
        start=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        end=datetime(2026, 4, 1, 18, 0, tzinfo=UTC),
        duration_minutes=30,
    )

    assert result == [
        FreeSlotRead(
            start_time=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
            end_time=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
            duration_minutes=60,
        ),
        FreeSlotRead(
            start_time=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            end_time=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
            duration_minutes=120,
        ),
        FreeSlotRead(
            start_time=datetime(2026, 4, 1, 13, 0, tzinfo=UTC),
            end_time=datetime(2026, 4, 1, 18, 0, tzinfo=UTC),
            duration_minutes=300,
        ),
    ]


def test_calendar_events_route_lists_events() -> None:
    app = create_app()
    app.dependency_overrides[get_calendar_service] = lambda: CalendarService(FakeCalendarProvider())

    with TestClient(app) as client:
        response = client.get("/calendar/events")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_daily_briefing_route_returns_structured_agenda() -> None:
    app = create_app()
    app.dependency_overrides[get_briefing_service] = lambda: FakeBriefingService()

    with TestClient(app) as client:
        response = client.get("/assistant/daily-briefing?date=2026-04-01")

    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == "2026-04-01"
    assert payload["summary_lines"] == ["1 events, 1 reminders, 1 due tasks."]
