import logging
from datetime import timedelta
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler

from core.models.entities import ReminderStatus
from core.utils.dates import utc_now
from core.utils.recurrence import next_recurrence
from services.reminders.notifiers import ReminderNotifier
from services.reminders.service import ReminderService

logger = logging.getLogger(__name__)


class ReminderScheduler:
    SYNC_JOB_ID = "cipher:sync-reminders"
    REMINDER_JOB_PREFIX = "cipher:reminder:"

    def __init__(
        self,
        *,
        reminder_service: ReminderService,
        notifier: ReminderNotifier,
        timezone: str,
        poll_seconds: int,
        lookahead_minutes: int,
        scheduler: Any | None = None,
    ) -> None:
        self._reminder_service = reminder_service
        self._notifier = notifier
        self._timezone = timezone
        self._poll_seconds = poll_seconds
        self._lookahead_minutes = lookahead_minutes
        self._scheduler = scheduler or BackgroundScheduler(timezone=timezone)

    def start(self) -> None:
        self._scheduler.start()
        self.sync_reminders()
        self._scheduler.add_job(
            self.sync_reminders,
            "interval",
            seconds=self._poll_seconds,
            id=self.SYNC_JOB_ID,
            replace_existing=True,
        )
        logger.info(
            "Reminder scheduler started with poll=%ss lookahead=%sm",
            self._poll_seconds,
            self._lookahead_minutes,
        )

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Reminder scheduler stopped.")

    def sync_reminders(self) -> None:
        now = utc_now()
        start = now - timedelta(minutes=1)
        end = now + timedelta(minutes=self._lookahead_minutes)
        reminders = self._reminder_service.list_schedulable_reminders(start=start, end=end)
        active_job_ids = {self._job_id(reminder.id) for reminder in reminders}

        for reminder in reminders:
            self._schedule_reminder(reminder.id, reminder.trigger_time)

        for job in self._scheduler.get_jobs():
            if job.id.startswith(self.REMINDER_JOB_PREFIX) and job.id not in active_job_ids:
                self._scheduler.remove_job(job.id)

        logger.info("Reminder scheduler synced %s reminders.", len(reminders))

    def fire_reminder(self, reminder_id: str) -> None:
        reminder = self._reminder_service.get_reminder(reminder_id)
        if reminder.status not in {ReminderStatus.SCHEDULED, ReminderStatus.SNOOZED}:
            logger.info(
                "Skipping reminder %s because status is %s.",
                reminder.id,
                reminder.status,
            )
            return

        self._notifier.send(reminder)
        next_trigger_time = next_recurrence(reminder.trigger_time, reminder.recurrence_rule)
        updated = self._reminder_service.record_trigger(
            reminder_id,
            triggered_at=utc_now(),
            next_trigger_time=next_trigger_time,
        )

        if next_trigger_time is not None:
            self._schedule_reminder(updated.id, updated.trigger_time)
        else:
            job_id = self._job_id(reminder_id)
            if self._scheduler.get_job(job_id) is not None:
                self._scheduler.remove_job(job_id)

        logger.info(
            "Processed reminder %s; next_trigger_time=%s",
            reminder_id,
            next_trigger_time.isoformat() if next_trigger_time else None,
        )

    def _schedule_reminder(self, reminder_id: str, trigger_time) -> None:
        self._scheduler.add_job(
            self.fire_reminder,
            "date",
            run_date=trigger_time,
            id=self._job_id(reminder_id),
            replace_existing=True,
            args=[reminder_id],
        )

    @classmethod
    def _job_id(cls, reminder_id: str) -> str:
        return f"{cls.REMINDER_JOB_PREFIX}{reminder_id}"
