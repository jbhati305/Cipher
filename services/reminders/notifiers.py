import logging
from typing import Protocol

from core.models.entities import ReminderRead

logger = logging.getLogger(__name__)


class ReminderNotifier(Protocol):
    def send(self, reminder: ReminderRead) -> None: ...


class ConsoleReminderNotifier:
    def send(self, reminder: ReminderRead) -> None:
        logger.info(
            "reminder_triggered | id=%s | code=%s | title=%s | trigger_time=%s | channel=%s",
            reminder.id,
            reminder.code,
            reminder.title,
            reminder.trigger_time.isoformat(),
            reminder.channel.value,
        )
