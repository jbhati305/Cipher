import logging
from threading import Event

from core.config import get_settings
from core.repositories.graph_repository import Neo4jGraphRepository
from core.utils.logging import configure_logging
from database.neo4j.client import Neo4jGraphClient
from services.reminders.notifiers import ConsoleReminderNotifier
from services.reminders.scheduler import ReminderScheduler
from services.reminders.service import ReminderService

logger = logging.getLogger(__name__)


def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    client = Neo4jGraphClient(settings)
    client.start()
    if not client.is_ready:
        raise SystemExit(client.last_error or "Neo4j is not ready.")

    repository = Neo4jGraphRepository(driver=client.driver, database=settings.neo4j_database)
    reminder_service = ReminderService(repository)
    notifier = ConsoleReminderNotifier()
    scheduler = ReminderScheduler(
        reminder_service=reminder_service,
        notifier=notifier,
        timezone=settings.default_timezone,
        poll_seconds=settings.reminder_scheduler_poll_seconds,
        lookahead_minutes=settings.reminder_scheduler_lookahead_minutes,
    )

    stop_event = Event()

    try:
        scheduler.start()
        logger.info("Cipher worker is running. Press Ctrl+C to stop.")
        stop_event.wait()
    except KeyboardInterrupt:
        logger.info("Stopping Cipher worker after keyboard interrupt.")
    finally:
        scheduler.stop()
        client.close()


if __name__ == "__main__":
    run()
