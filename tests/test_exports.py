from core.models.entities import MemoryRecord
from core.utils.dates import utc_now
from exports import ExportService
from storage.sqlite import SQLiteRepository


def test_export_service_writes_markdown_and_jsonl(tmp_path):
    repository = SQLiteRepository(tmp_path / "cipher.sqlite3")
    repository.record_memory(
        MemoryRecord(
            id="mem-1",
            content="Remember local-first.",
            kind="reflection",
            source="test",
            tags=["test"],
            metadata={},
            created_at=utc_now(),
        )
    )
    settings = __import__("core.config", fromlist=["Settings"]).Settings(
        CIPHER_DATA_DIR=str(tmp_path),
        CIPHER_EXPORTS_DIR=str(tmp_path / "exports"),
    )

    paths = ExportService(settings=settings, repository=repository).export_all()

    assert "Remember local-first." in (tmp_path / "exports").joinpath(
        paths["markdown"].split("/")[-1]
    ).read_text(encoding="utf-8")
    assert (tmp_path / "exports").joinpath(paths["jsonl"].split("/")[-1]).exists()
