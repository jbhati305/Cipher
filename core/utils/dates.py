import re
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from dateutil import parser


def utc_now() -> datetime:
    return datetime.now(UTC)


def day_bounds(target_date: date, timezone: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(timezone)
    start = datetime.combine(target_date, time.min, tzinfo=tz)
    end = start + timedelta(days=1)
    return start, end


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
    elif "tonight" in lowered:
        base = now.replace(hour=20, minute=0, second=0, microsecond=0)
        lowered = lowered.replace("tonight", "")

    cleaned = _strip_schedule_fillers(lowered)
    if not cleaned:
        return base, warnings

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


def parse_event_time_window(
    text: str,
    timezone: str,
    *,
    default_duration_minutes: int = 60,
) -> tuple[datetime | None, datetime | None, list[str]]:
    warnings: list[str] = []
    duration_minutes = parse_duration_minutes(text) or default_duration_minutes
    schedule_text = re.sub(r"\b\d+\s*hours?\b", " ", text, flags=re.IGNORECASE)
    schedule_text = re.sub(r"\b\d+\s*minutes?\b", " ", schedule_text, flags=re.IGNORECASE)
    schedule_text = re.sub(r"\s+", " ", schedule_text).strip() or text

    start_time, parse_warnings = parse_reminder_datetime(schedule_text, timezone)
    warnings.extend(parse_warnings)
    if start_time is None:
        return None, None, warnings

    return start_time, start_time + timedelta(minutes=duration_minutes), warnings


def parse_duration_minutes(text: str) -> int | None:
    hour_match = re.search(r"(\d+)\s*hour", text, flags=re.IGNORECASE)
    minute_match = re.search(r"(\d+)\s*minute", text, flags=re.IGNORECASE)
    if hour_match:
        return int(hour_match.group(1)) * 60
    if minute_match:
        return int(minute_match.group(1))
    return None


def _strip_schedule_fillers(text: str) -> str:
    text = re.sub(r"\b(remind me|to)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
