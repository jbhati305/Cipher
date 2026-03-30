from datetime import UTC, datetime

from core.utils.recurrence import is_supported_recurrence_rule, next_recurrence


def test_supported_named_recurrence_rules() -> None:
    assert is_supported_recurrence_rule("daily")
    assert is_supported_recurrence_rule("weekly")
    assert is_supported_recurrence_rule("monthly")
    assert not is_supported_recurrence_rule("yearly-ish")


def test_next_recurrence_for_daily_rule() -> None:
    trigger_time = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)

    result = next_recurrence(trigger_time, "daily")

    assert result == datetime(2026, 4, 2, 9, 0, tzinfo=UTC)


def test_next_recurrence_for_rrule() -> None:
    trigger_time = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)

    result = next_recurrence(trigger_time, "FREQ=WEEKLY;COUNT=3")

    assert result == datetime(2026, 4, 8, 9, 0, tzinfo=UTC)
