from typing import Any

from mcp.server.fastmcp import FastMCP

from apps.mcp.tools import CipherToolRegistry
from core.config import Settings, get_settings


def _clean(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def create_server(settings: Settings | None = None) -> FastMCP:
    registry = CipherToolRegistry(settings or get_settings())
    server = FastMCP(
        "cipher",
        instructions=(
            "Cipher exposes local-first personal OS capabilities backed by MemOS, "
            "SQLite projections, Google Calendar, and Notion paper sync. Hermes owns "
            "conversation, orchestration, scheduling, and delivery."
        ),
    )

    @server.tool(description="Create a Cipher project and write its context into MemOS.")
    def cipher_project_create(
        name: str,
        description: str | None = None,
        status: str = "active",
        priority: str = "medium",
    ) -> dict[str, Any]:
        return registry.call(
            "cipher_project_create",
            _clean(
                {
                    "name": name,
                    "description": description,
                    "status": status,
                    "priority": priority,
                }
            ),
        )

    @server.tool(description="List Cipher project projections from SQLite.")
    def cipher_project_list() -> list[dict[str, Any]]:
        return registry.call("cipher_project_list", {})

    @server.tool(description="Create a Cipher task and write task meaning/history into MemOS.")
    def cipher_task_create(
        title: str,
        description: str | None = None,
        status: str = "pending",
        priority: str = "medium",
        deadline: str | None = None,
        estimated_effort: str | None = None,
        project_id: str | None = None,
        related_entity_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        return registry.call(
            "cipher_task_create",
            _clean(
                {
                    "title": title,
                    "description": description,
                    "status": status,
                    "priority": priority,
                    "deadline": deadline,
                    "estimated_effort": estimated_effort,
                    "project_id": project_id,
                    "related_entity_ids": related_entity_ids,
                }
            ),
        )

    @server.tool(description="List Cipher tasks, optionally filtered by status or project_id.")
    def cipher_task_list(
        status: str | None = None,
        project_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return registry.call("cipher_task_list", _clean({"status": status, "project_id": project_id}))

    @server.tool(description="Update a Cipher task and write the change into MemOS.")
    def cipher_task_update(
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        deadline: str | None = None,
        estimated_effort: str | None = None,
        project_id: str | None = None,
        related_entity_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        return registry.call(
            "cipher_task_update",
            _clean(
                {
                    "task_id": task_id,
                    "title": title,
                    "description": description,
                    "status": status,
                    "priority": priority,
                    "deadline": deadline,
                    "estimated_effort": estimated_effort,
                    "project_id": project_id,
                    "related_entity_ids": related_entity_ids,
                }
            ),
        )

    @server.tool(description="Mark a Cipher task complete and write completion context into MemOS.")
    def cipher_task_complete(task_id: str) -> dict[str, Any]:
        return registry.call("cipher_task_complete", {"task_id": task_id})

    @server.tool(description="Write a memory into MemOS through Cipher and record a local audit event.")
    def cipher_memory_write(
        content: str,
        kind: str = "note",
        source: str = "hermes",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return registry.call(
            "cipher_memory_write",
            _clean(
                {
                    "content": content,
                    "kind": kind,
                    "source": source,
                    "tags": tags,
                    "metadata": metadata,
                }
            ),
        )

    @server.tool(description="Search Cipher memories through MemOS.")
    def cipher_memory_search(query: str, limit: int = 10) -> list[dict[str, Any]]:
        return registry.call("cipher_memory_search", {"query": query, "limit": limit})

    @server.tool(description="Start or store a daily reflection prompt in MemOS.")
    def cipher_daily_reflection_start(prompt: str | None = None) -> dict[str, Any]:
        return registry.call("cipher_daily_reflection_start", _clean({"prompt": prompt}))

    @server.tool(description="Return recent Cipher memory records for daily summary/review.")
    def cipher_daily_summary() -> list[dict[str, Any]]:
        return registry.call("cipher_daily_summary", {})

    @server.tool(description="Create a local reminder projection for Hermes cron/gateway delivery.")
    def cipher_reminder_create(
        title: str,
        trigger_time: str,
        recurrence_rule: str | None = None,
        status: str = "scheduled",
        channel: str = "in_app",
        related_entity_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        return registry.call(
            "cipher_reminder_create",
            _clean(
                {
                    "title": title,
                    "trigger_time": trigger_time,
                    "recurrence_rule": recurrence_rule,
                    "status": status,
                    "channel": channel,
                    "related_entity_ids": related_entity_ids,
                }
            ),
        )

    @server.tool(description="List local reminder projections.")
    def cipher_reminder_list() -> list[dict[str, Any]]:
        return registry.call("cipher_reminder_list", {})

    @server.tool(description="Update a local reminder projection.")
    def cipher_reminder_update(
        reminder_id: str,
        title: str | None = None,
        trigger_time: str | None = None,
        recurrence_rule: str | None = None,
        status: str | None = None,
        channel: str | None = None,
        related_entity_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        return registry.call(
            "cipher_reminder_update",
            _clean(
                {
                    "reminder_id": reminder_id,
                    "title": title,
                    "trigger_time": trigger_time,
                    "recurrence_rule": recurrence_rule,
                    "status": status,
                    "channel": channel,
                    "related_entity_ids": related_entity_ids,
                }
            ),
        )

    @server.tool(description="Snooze a reminder until an ISO datetime.")
    def cipher_reminder_snooze(reminder_id: str, until: str) -> dict[str, Any]:
        return registry.call("cipher_reminder_snooze", {"reminder_id": reminder_id, "until": until})

    @server.tool(description="Dismiss a reminder.")
    def cipher_reminder_dismiss(reminder_id: str) -> dict[str, Any]:
        return registry.call("cipher_reminder_dismiss", {"reminder_id": reminder_id})

    @server.tool(description="List reminders due inside an ISO datetime window for Hermes delivery.")
    def cipher_reminder_due(start: str, end: str) -> list[dict[str, Any]]:
        return registry.call("cipher_reminder_due", {"start": start, "end": end})

    @server.tool(description="List Google Calendar events through Cipher's calendar provider.")
    def cipher_calendar_list_events(
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        return registry.call("cipher_calendar_list_events", _clean({"start": start, "end": end}))

    @server.tool(description="Create a Google Calendar event through Cipher.")
    def cipher_calendar_create_event(
        title: str,
        start_time: str,
        end_time: str,
        location: str | None = None,
        description: str | None = None,
        related_entity_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        return registry.call(
            "cipher_calendar_create_event",
            _clean(
                {
                    "title": title,
                    "start_time": start_time,
                    "end_time": end_time,
                    "location": location,
                    "description": description,
                    "related_entity_ids": related_entity_ids,
                }
            ),
        )

    @server.tool(description="Update a Google Calendar event through Cipher.")
    def cipher_calendar_update_event(
        event_id: str,
        title: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        location: str | None = None,
        description: str | None = None,
        related_entity_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        return registry.call(
            "cipher_calendar_update_event",
            _clean(
                {
                    "event_id": event_id,
                    "title": title,
                    "start_time": start_time,
                    "end_time": end_time,
                    "location": location,
                    "description": description,
                    "related_entity_ids": related_entity_ids,
                }
            ),
        )

    @server.tool(description="Find free calendar slots within an ISO datetime window.")
    def cipher_calendar_find_free_slots(
        start: str,
        end: str,
        duration_minutes: int = 60,
    ) -> list[dict[str, Any]]:
        return registry.call(
            "cipher_calendar_find_free_slots",
            {"start": start, "end": end, "duration_minutes": duration_minutes},
        )

    @server.tool(description="Run read-only Notion paper sync into Cipher projections and MemOS context.")
    def cipher_notion_papers_sync() -> dict[str, Any]:
        return registry.call("cipher_notion_papers_sync", {})

    @server.tool(description="List synced Notion research paper projections.")
    def cipher_notion_papers_list() -> list[dict[str, Any]]:
        return registry.call("cipher_notion_papers_list", {})

    return server


def run() -> None:
    create_server().run(transport="stdio")


if __name__ == "__main__":
    run()
