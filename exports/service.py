import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.config import Settings
from storage.sqlite import SQLiteRepository


class ExportService:
    def __init__(self, *, settings: Settings, repository: SQLiteRepository) -> None:
        self._settings = settings
        self._repository = repository

    def export_all(self) -> dict[str, str]:
        export_dir = self._settings.resolved_exports_dir
        export_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        jsonl_path = export_dir / f"cipher-export-{stamp}.jsonl"
        markdown_path = export_dir / f"cipher-export-{stamp}.md"

        payload = {
            "projects": [item.model_dump(mode="json") for item in self._repository.list_projects()],
            "tasks": [item.model_dump(mode="json") for item in self._repository.list_tasks()],
            "reminders": [
                item.model_dump(mode="json") for item in self._repository.list_reminders()
            ],
            "papers": [item.model_dump(mode="json") for item in self._repository.list_papers()],
            "memory_events": [
                item.model_dump(mode="json")
                for item in self._repository.list_memory_events(limit=500)
            ],
            "audit_events": self._repository.list_audit_events(limit=500),
        }
        self._write_jsonl(jsonl_path, payload)
        self._write_markdown(markdown_path, payload)
        return {"jsonl": str(jsonl_path), "markdown": str(markdown_path)}

    @staticmethod
    def _write_jsonl(path: Path, payload: dict[str, list[dict[str, Any]]]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for kind, rows in payload.items():
                for row in rows:
                    handle.write(json.dumps({"kind": kind, **row}, sort_keys=True) + "\n")

    @staticmethod
    def _write_markdown(path: Path, payload: dict[str, list[dict[str, Any]]]) -> None:
        lines = ["# Cipher Export", ""]
        for kind, rows in payload.items():
            lines.extend([f"## {kind.replace('_', ' ').title()}", ""])
            if not rows:
                lines.extend(["_No records._", ""])
                continue
            for row in rows:
                title = (
                    row.get("title")
                    or row.get("name")
                    or row.get("event_type")
                    or row.get("id")
                )
                lines.append(f"- **{title}**")
                details = {
                    key: value
                    for key, value in row.items()
                    if key not in {"title", "name", "content"} and value not in (None, "", [], {})
                }
                if row.get("content"):
                    lines.append(f"  - {row['content']}")
                if details:
                    lines.append(f"  - `{json.dumps(details, sort_keys=True)}`")
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
