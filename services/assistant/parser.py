import re
from datetime import UTC, datetime

from core.models.assistant import AssistantIntent, ParsedCommand
from core.utils.dates import parse_reminder_datetime


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

        return self._build_response(
            intent=AssistantIntent.UNKNOWN,
            confidence=0.25,
            raw_text=text,
            payload={},
            warnings=["No Phase 1 parser rule matched this command yet."],
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
