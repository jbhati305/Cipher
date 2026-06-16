import json

import typer

from apps.mcp.server import run as run_mcp
from apps.mcp.tools import CipherToolRegistry
from core.config import get_settings
from core.models.entities import MemoryWrite
from exports import ExportService
from services.memory.memos_client import MemOSClient
from services.memory.service import MemoryService
from storage import SQLiteRepository

app = typer.Typer(help="Cipher local-first personal AI OS.")
sync_app = typer.Typer(help="Sync external sources.")
memory_app = typer.Typer(help="Memory operations.")
app.add_typer(sync_app, name="sync")
app.add_typer(memory_app, name="memory")


@app.command()
def dev() -> None:
    typer.echo(
        "Run `uv run cipher-api` for the FastAPI dev server "
        "and `uv run cipher-mcp` for tools."
    )


@app.command()
def serve() -> None:
    from apps.api.main import run

    run()


@app.command()
def mcp() -> None:
    run_mcp()


@app.command()
def doctor() -> None:
    settings = get_settings()
    repository = SQLiteRepository(settings.resolved_sqlite_path)
    typer.echo(json.dumps({
        "data_dir": str(settings.resolved_data_dir),
        "sqlite": repository.health(),
        "memos": MemOSClient(settings).health(),
    }, indent=2))


@app.command()
def reflect(prompt: str = typer.Option("Daily reflection started.")) -> None:
    registry = CipherToolRegistry(get_settings())
    typer.echo(json.dumps(registry.cipher_daily_reflection_start(prompt=prompt), indent=2))


@sync_app.command("notion-papers")
def sync_notion_papers() -> None:
    registry = CipherToolRegistry(get_settings())
    typer.echo(json.dumps(registry.cipher_notion_papers_sync(), indent=2))


@memory_app.command("export")
def export_memory() -> None:
    settings = get_settings()
    repository = SQLiteRepository(settings.resolved_sqlite_path)
    paths = ExportService(settings=settings, repository=repository).export_all()
    typer.echo(json.dumps(paths, indent=2))


@memory_app.command("write")
def write_memory(content: str, kind: str = "note", source: str = "cli") -> None:
    settings = get_settings()
    repository = SQLiteRepository(settings.resolved_sqlite_path)
    service = MemoryService(repository, MemOSClient(settings))
    record = service.write(
        MemoryWrite(
            content=content,
            kind=kind,
            source=source,
        )
    )
    typer.echo(json.dumps(record.model_dump(mode="json"), indent=2))


def main() -> None:
    app()
