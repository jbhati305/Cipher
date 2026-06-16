import logging
from threading import Event

from apscheduler.schedulers.background import BackgroundScheduler

from core.config import get_settings
from core.models.entities import MemoryWrite
from core.utils.logging import configure_logging
from exports import ExportService
from services.memory.memos_client import MemOSClient
from services.memory.service import MemoryService
from services.notion import NotionPaperService
from storage import SQLiteRepository

logger = logging.getLogger(__name__)


def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    repository = SQLiteRepository(settings.resolved_sqlite_path)
    memory = MemoryService(repository, MemOSClient(settings))
    notion = NotionPaperService(settings=settings, repository=repository, memory_service=memory)
    exports = ExportService(settings=settings, repository=repository)

    scheduler = BackgroundScheduler(timezone=settings.default_timezone)
    scheduler.add_job(
        lambda: _run_nightly(memory, notion, exports),
        "cron",
        hour=23,
        minute=30,
        id="cipher:nightly-consolidation",
        replace_existing=True,
    )
    stop_event = Event()
    try:
        scheduler.start()
        logger.info("Cipher worker is running. Hermes remains responsible for reminder delivery.")
        stop_event.wait()
    except KeyboardInterrupt:
        logger.info("Stopping Cipher worker after keyboard interrupt.")
    finally:
        scheduler.shutdown(wait=False)


def _run_nightly(
    memory: MemoryService,
    notion: NotionPaperService,
    exports: ExportService,
) -> None:
    sync_result = notion.sync()
    export_paths = exports.export_all()
    memory.write(
        MemoryWrite(
            content=(
                "Nightly Cipher consolidation completed. "
                f"Notion sync: {sync_result}. Exports: {export_paths}."
            ),
            kind="daily_consolidation",
            source="cipher-worker",
            tags=["reflection", "nightly"],
            metadata={"notion": sync_result, "exports": export_paths},
        )
    )


if __name__ == "__main__":
    run()
