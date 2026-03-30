from dataclasses import dataclass
from datetime import UTC, datetime

from core.models.entities import ReminderChannel, ReminderRead, ReminderStatus
from services.reminders.scheduler import ReminderScheduler


def _reminder_fixture(
    *,
    reminder_id: str = "reminder-1",
    trigger_time: datetime | None = None,
    recurrence_rule: str | None = None,
    status: ReminderStatus = ReminderStatus.SCHEDULED,
) -> ReminderRead:
    now = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    return ReminderRead(
        id=reminder_id,
        code="REM-2604-000001",
        created_at=now,
        updated_at=now,
        title="Call Rahul",
        trigger_time=trigger_time or now,
        recurrence_rule=recurrence_rule,
        status=status,
        channel=ReminderChannel.CONSOLE,
        last_triggered_at=None,
        trigger_count=0,
        related_entity_ids=[],
    )


@dataclass
class FakeJob:
    id: str
    run_date: datetime | None = None
    args: list[str] | None = None


class FakeSchedulerBackend:
    def __init__(self) -> None:
        self.jobs: dict[str, FakeJob] = {}
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def shutdown(self, wait: bool = False) -> None:  # noqa: FBT001, FBT002
        self.stopped = True

    def add_job(self, func, trigger, **kwargs):  # noqa: ANN001, ANN202
        job_id = kwargs["id"]
        self.jobs[job_id] = FakeJob(
            id=job_id,
            run_date=kwargs.get("run_date"),
            args=kwargs.get("args"),
        )
        return self.jobs[job_id]

    def get_job(self, job_id: str):  # noqa: ANN201
        return self.jobs.get(job_id)

    def get_jobs(self) -> list[FakeJob]:
        return list(self.jobs.values())

    def remove_job(self, job_id: str) -> None:
        self.jobs.pop(job_id, None)


class FakeNotifier:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def send(self, reminder: ReminderRead) -> None:
        self.sent.append(reminder.id)


class FakeReminderService:
    def __init__(self, reminders: list[ReminderRead]) -> None:
        self.reminders = {reminder.id: reminder for reminder in reminders}
        self.recorded: list[tuple[str, datetime | None]] = []

    def list_schedulable_reminders(self, *, start, end):  # noqa: ANN001, ANN201
        return list(self.reminders.values())

    def get_reminder(self, reminder_id: str) -> ReminderRead:
        return self.reminders[reminder_id]

    def record_trigger(self, reminder_id: str, *, triggered_at, next_trigger_time):  # noqa: ANN001, ANN201
        reminder = self.reminders[reminder_id]
        updated = reminder.model_copy(
            update={
                "trigger_time": next_trigger_time or reminder.trigger_time,
                "status": (
                    ReminderStatus.SCHEDULED
                    if next_trigger_time
                    else ReminderStatus.TRIGGERED
                ),
                "last_triggered_at": triggered_at,
                "trigger_count": reminder.trigger_count + 1,
            }
        )
        self.reminders[reminder_id] = updated
        self.recorded.append((reminder_id, next_trigger_time))
        return updated


def test_sync_reminders_registers_jobs() -> None:
    reminder = _reminder_fixture()
    service = FakeReminderService([reminder])
    backend = FakeSchedulerBackend()
    notifier = FakeNotifier()
    scheduler = ReminderScheduler(
        reminder_service=service,
        notifier=notifier,
        timezone="UTC",
        poll_seconds=30,
        lookahead_minutes=60,
        scheduler=backend,
    )

    scheduler.sync_reminders()

    assert ReminderScheduler._job_id(reminder.id) in backend.jobs


def test_fire_reminder_records_trigger_and_reschedules_recurring_reminder() -> None:
    reminder = _reminder_fixture(recurrence_rule="daily")
    service = FakeReminderService([reminder])
    backend = FakeSchedulerBackend()
    notifier = FakeNotifier()
    scheduler = ReminderScheduler(
        reminder_service=service,
        notifier=notifier,
        timezone="UTC",
        poll_seconds=30,
        lookahead_minutes=60,
        scheduler=backend,
    )

    scheduler.fire_reminder(reminder.id)

    assert notifier.sent == [reminder.id]
    assert service.recorded and service.recorded[0][1] is not None
    assert ReminderScheduler._job_id(reminder.id) in backend.jobs


def test_fire_reminder_marks_one_time_reminder_triggered() -> None:
    reminder = _reminder_fixture(recurrence_rule=None)
    service = FakeReminderService([reminder])
    backend = FakeSchedulerBackend()
    notifier = FakeNotifier()
    scheduler = ReminderScheduler(
        reminder_service=service,
        notifier=notifier,
        timezone="UTC",
        poll_seconds=30,
        lookahead_minutes=60,
        scheduler=backend,
    )

    scheduler.fire_reminder(reminder.id)

    assert notifier.sent == [reminder.id]
    assert service.reminders[reminder.id].status == ReminderStatus.TRIGGERED
