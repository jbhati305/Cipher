from datetime import datetime

from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrulestr

SUPPORTED_RECURRENCE_RULES = {"daily", "weekly", "monthly"}


def is_supported_recurrence_rule(rule: str | None) -> bool:
    if rule is None:
        return True

    normalized = rule.strip().lower()
    if normalized in SUPPORTED_RECURRENCE_RULES:
        return True

    try:
        rrulestr(rule, dtstart=datetime.now())
    except Exception:
        return False
    return True


def next_recurrence(trigger_time: datetime, recurrence_rule: str | None) -> datetime | None:
    if recurrence_rule is None:
        return None

    normalized = recurrence_rule.strip().lower()
    if normalized == "daily":
        return trigger_time + relativedelta(days=1)
    if normalized == "weekly":
        return trigger_time + relativedelta(weeks=1)
    if normalized == "monthly":
        return trigger_time + relativedelta(months=1)

    rule = rrulestr(recurrence_rule, dtstart=trigger_time)
    return rule.after(trigger_time)
