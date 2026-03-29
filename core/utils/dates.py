import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dateutil import parser


def utc_now() -> datetime:
    return datetime.now(ZoneInfo("UTC"))


def parse_reminder_datetime(text: str, timezone: str) -> tuple[datetime | None, list[str]]:
    warnings: list[str] = []
    lowered = text.lower().strip()
    now = datetime.now(ZoneInfo(timezone))

    base = now
    if "day after tomorrow" in lowered:
        base = now + timedelta(days=2)
        lowered = lowered.replace("day after tomorrow", "")
    elif "tomorrow" in lowered:
        base = now + timedelta(days=1)
        lowered = lowered.replace("tomorrow", "")
    elif "today" in lowered:
        lowered = lowered.replace("today", "")

    cleaned = _strip_schedule_fillers(lowered)

    try:
        parsed = parser.parse(cleaned, fuzzy=True, default=base)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo(timezone))
        return parsed, warnings
    except (parser.ParserError, ValueError):
        warnings.append(
            "Could not fully resolve the reminder time. Check the trigger text before execution."
        )
        return None, warnings


def _strip_schedule_fillers(text: str) -> str:
    text = re.sub(r"\b(remind me|to)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
