from datetime import datetime
from typing import Any

import httpx

from core.config import Settings
from core.models.entities import MemoryWrite, PaperRead
from services.memory.service import MemoryService
from storage.sqlite import SQLiteRepository


class NotionPaperService:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: SQLiteRepository,
        memory_service: MemoryService,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._memory_service = memory_service

    def sync(self) -> dict[str, int | bool | str]:
        if not self._settings.notion_configured:
            return {"configured": False, "synced": 0, "detail": "Notion is not configured."}
        papers = self._fetch_papers()
        synced = self._repository.upsert_papers(papers)
        self._memory_service.write(
            MemoryWrite(
                content=f"Synced {synced} research papers from Notion.",
                kind="notion_papers_sync",
                source="cipher",
                tags=["notion", "papers"],
                metadata={"synced": synced},
            )
        )
        return {"configured": True, "synced": synced}

    def list_papers(self) -> list[PaperRead]:
        return self._repository.list_papers()

    def _fetch_papers(self) -> list[PaperRead]:
        url = (
            "https://api.notion.com/v1/databases/"
            f"{self._settings.notion_papers_database_id}/query"
        )
        headers = {
            "Authorization": f"Bearer {self._settings.notion_api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        response = httpx.post(url, headers=headers, json={}, timeout=20.0)
        response.raise_for_status()
        data = response.json()
        return [self._map_page(page) for page in data.get("results", [])]

    def _map_page(self, page: dict[str, Any]) -> PaperRead:
        properties = page.get("properties", {})
        title = self._title(properties) or "Untitled paper"
        return PaperRead(
            id=page["id"],
            notion_page_id=page["id"],
            title=title,
            authors=self._text_property(properties, "Authors")
            or self._text_property(properties, "Author"),
            status=self._select_property(properties, "Status")
            or self._select_property(properties, "Reading Status"),
            url=self._url_property(properties, "URL")
            or self._url_property(properties, "Link")
            or page.get("url"),
            updated_at=self._parse_dt(page.get("last_edited_time")),
        )

    @staticmethod
    def _title(properties: dict[str, Any]) -> str | None:
        for value in properties.values():
            if value.get("type") == "title":
                return "".join(part.get("plain_text", "") for part in value.get("title", []))
        return None

    @staticmethod
    def _text_property(properties: dict[str, Any], name: str) -> str | None:
        value = properties.get(name)
        if not value:
            return None
        if value.get("type") == "rich_text":
            return "".join(part.get("plain_text", "") for part in value.get("rich_text", []))
        if value.get("type") == "multi_select":
            return ", ".join(item.get("name", "") for item in value.get("multi_select", []))
        return None

    @staticmethod
    def _select_property(properties: dict[str, Any], name: str) -> str | None:
        value = properties.get(name)
        if not value:
            return None
        if value.get("type") == "select" and value.get("select"):
            return value["select"].get("name")
        if value.get("type") == "status" and value.get("status"):
            return value["status"].get("name")
        return None

    @staticmethod
    def _url_property(properties: dict[str, Any], name: str) -> str | None:
        value = properties.get(name)
        if value and value.get("type") == "url":
            return value.get("url")
        return None

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None
