import re
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from core.models.assistant import AssistantIntent, ParsedCommand
from core.utils.dates import parse_event_time_window, parse_reminder_datetime


class AssistantParserService:
    def __init__(self, default_timezone: str) -> None:
        self._default_timezone = default_timezone

    def parse(self, text: str) -> ParsedCommand:
        normalized = text.strip()
        lowered = normalized.lower()

        if lowered.startswith(("create a task", "create task", "add task", "task:")):
            title = self._strip_prefix(
                normalized,
                ["create a task to", "create a task", "create task", "add task", "task:"],
            )
            return self._build_response(
                intent=AssistantIntent.CREATE_TASK,
                confidence=0.93,
                raw_text=text,
                payload={
                    "title": title.strip(),
                    "status": "pending",
                    "priority": "medium",
                },
            )

        if lowered.startswith(("schedule", "block")):
            schedule_text, event_title = self._split_schedule_text(normalized)
            start_time, end_time, warnings = parse_event_time_window(
                schedule_text,
                self._default_timezone,
            )
            return self._build_response(
                intent=AssistantIntent.CREATE_EVENT,
                confidence=0.84 if start_time and end_time else 0.58,
                raw_text=text,
                payload={
                    "title": event_title,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                },
                warnings=warnings,
            )

        if lowered.startswith(("add note", "note:", "add a note")):
            content = self._strip_prefix(
                normalized,
                ["add note:", "add note that", "add a note", "note:"],
            )
            title = self._derive_note_title(content)
            return self._build_response(
                intent=AssistantIntent.CREATE_NOTE,
                confidence=0.92,
                raw_text=text,
                payload={
                    "title": title,
                    "content": content.strip(),
                    "source": "chat",
                },
            )

        if lowered.startswith("remind me"):
            schedule_text, reminder_body = self._split_reminder_text(normalized)
            trigger_time, warnings = parse_reminder_datetime(schedule_text, self._default_timezone)
            payload = {
                "title": reminder_body,
                "trigger_time": trigger_time.isoformat() if trigger_time else None,
                "status": "scheduled",
                "channel": "in_app",
            }
            return self._build_response(
                intent=AssistantIntent.CREATE_REMINDER,
                confidence=0.86 if trigger_time else 0.62,
                raw_text=text,
                payload=payload,
                warnings=warnings,
            )

        if lowered.startswith(("move my reminder", "reschedule reminder", "move reminder")):
            trigger_time, warnings = parse_reminder_datetime(normalized, self._default_timezone)
            return self._build_response(
                intent=AssistantIntent.RESCHEDULE_REMINDER,
                confidence=0.78 if trigger_time else 0.5,
                raw_text=text,
                payload={
                    "trigger_time": trigger_time.isoformat() if trigger_time else None,
                },
                warnings=warnings,
            )

        if lowered.startswith(("mark ", "complete task", "finish task")) and any(
            token in lowered for token in (" done", " complete", " completed")
        ):
            title = self._strip_completion_phrase(normalized)
            return self._build_response(
                intent=AssistantIntent.UPDATE_TASK_STATUS,
                confidence=0.82,
                raw_text=text,
                payload={"title": title, "status": "completed"},
            )

        if "reminders" in lowered:
            period = "week" if "week" in lowered else "day"
            return self._build_response(
                intent=AssistantIntent.QUERY_REMINDERS,
                confidence=0.78,
                raw_text=text,
                payload={"period": period},
            )

        if "agenda" in lowered or "calendar" in lowered:
            target_date = self._resolve_relative_date(lowered)
            return self._build_response(
                intent=AssistantIntent.QUERY_AGENDA,
                confidence=0.8,
                raw_text=text,
                payload={"date": target_date.date().isoformat()},
            )

        if "tasks" in lowered and " for " in lowered:
            status = "pending" if "pending" in lowered else None
            return self._build_response(
                intent=AssistantIntent.QUERY_PROJECT_TASKS,
                confidence=0.74,
                raw_text=text,
                payload={
                    "project_query": normalized.rsplit(" for ", maxsplit=1)[-1].strip(" ?"),
                    "status": status,
                },
            )

        return self._build_response(
            intent=AssistantIntent.UNKNOWN,
            confidence=0.25,
            raw_text=text,
            payload={},
            warnings=["No parser rule matched this command yet."],
        )

    @staticmethod
    def _build_response(
        *,
        intent: AssistantIntent,
        confidence: float,
        raw_text: str,
        payload: dict,
        warnings: list[str] | None = None,
    ) -> ParsedCommand:
        return ParsedCommand(
            intent=intent,
            confidence=confidence,
            payload=payload,
            raw_text=raw_text,
            parsed_at=datetime.now(UTC),
            warnings=warnings or [],
        )

    @staticmethod
    def _strip_prefix(text: str, prefixes: list[str]) -> str:
        lowered = text.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                return text[len(prefix) :].strip(" :")
        return text

    @staticmethod
    def _derive_note_title(content: str) -> str:
        title = content.strip().split(".")[0].strip()
        return (title[:60] or "Untitled note").rstrip()

    @staticmethod
    def _split_reminder_text(text: str) -> tuple[str, str]:
        match = re.search(r"\bto\b", text, flags=re.IGNORECASE)
        if not match:
            return text, text

        schedule_text = text[: match.start()].strip()
        reminder_body = text[match.end() :].strip()
        reminder_body = reminder_body or "Untitled reminder"
        return schedule_text, reminder_body

    @staticmethod
    def _split_schedule_text(text: str) -> tuple[str, str]:
        cleaned = re.sub(r"^(schedule|block)\s+", "", text, flags=re.IGNORECASE).strip()
        if " for " not in cleaned.lower():
            return cleaned, "Untitled event"
        schedule_text, event_title = re.split(r"\bfor\b", cleaned, maxsplit=1, flags=re.IGNORECASE)
        return schedule_text.strip(), event_title.strip() or "Untitled event"

    @staticmethod
    def _strip_completion_phrase(text: str) -> str:
        cleaned = re.sub(
            r"^(mark|complete task|finish task)\s+",
            "",
            text,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\b(as )?(done|complete|completed)\b", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip(" :")

    def _resolve_relative_date(self, text: str) -> datetime:
        now = datetime.now(ZoneInfo(self._default_timezone))
        if "tomorrow" in text:
            return now + timedelta(days=1)
        return now
