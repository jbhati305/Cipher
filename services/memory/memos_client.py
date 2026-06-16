from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx

from core.config import Settings
from core.models.entities import MemoryRecord, MemorySearchResult, MemoryWrite
from core.utils.dates import utc_now


class MemOSClientError(RuntimeError):
    pass


class MemOSClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def health(self) -> dict[str, Any]:
        try:
            response = httpx.get(
                f"{self._settings.memos_base_url.rstrip('/')}/health",
                timeout=min(self._settings.memos_timeout_seconds, 1.0),
            )
            return {"ok": response.status_code < 500, "status_code": response.status_code}
        except httpx.HTTPError as exc:
            return {"ok": False, "error": str(exc)}

    def write(self, payload: MemoryWrite) -> MemoryRecord:
        record = MemoryRecord(
            id=str(uuid4()),
            content=payload.content,
            kind=payload.kind,
            source=payload.source,
            tags=payload.tags,
            metadata=payload.metadata,
            created_at=utc_now(),
        )
        body = {
            "user_id": self._settings.memos_user_id,
            "mem_cube_id": self._settings.memos_mem_cube_id,
            "messages": [{"role": "user", "content": self._format_record(record)}],
            "async_mode": "sync",
        }
        self._post_best_effort("/product/add", body)
        return record

    def search(self, query: str, *, limit: int = 10) -> list[MemorySearchResult]:
        body = {
            "query": query,
            "user_id": self._settings.memos_user_id,
            "mem_cube_id": self._settings.memos_mem_cube_id,
            "top_k": limit,
        }
        data = self._post_json("/product/search", body)
        raw_results = data.get("data") or data.get("results") or data.get("memories") or []
        results: list[MemorySearchResult] = []
        if isinstance(raw_results, list):
            for item in raw_results[:limit]:
                if isinstance(item, str):
                    results.append(MemorySearchResult(content=item))
                elif isinstance(item, dict):
                    results.append(
                        MemorySearchResult(
                            id=item.get("id") or item.get("memory_id"),
                            content=(
                                item.get("content")
                                or item.get("memory")
                                or item.get("text")
                                or str(item)
                            ),
                            score=item.get("score"),
                            metadata=item,
                        )
                    )
        return results

    def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._settings.memos_base_url.rstrip('/')}{path}"
        try:
            response = httpx.post(url, json=body, timeout=self._settings.memos_timeout_seconds)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {"data": data}
        except httpx.HTTPError as exc:
            raise MemOSClientError(str(exc)) from exc

    def _post_best_effort(self, path: str, body: dict[str, Any]) -> None:
        try:
            self._post_json(path, body)
        except MemOSClientError:
            # Cipher keeps an auditable SQLite projection even when MemOS is booting or offline.
            # Reconciliation can replay these memory_events later.
            return

    @staticmethod
    def _format_record(record: MemoryRecord) -> str:
        tags = f" tags={','.join(record.tags)}" if record.tags else ""
        timestamp = datetime.isoformat(record.created_at)
        return f"[{record.kind} from {record.source} at {timestamp}{tags}] {record.content}"
