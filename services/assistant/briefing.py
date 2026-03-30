from datetime import date, datetime
from zoneinfo import ZoneInfo

from core.models.assistant import DailyBriefing
from core.utils.dates import day_bounds
from services.calendar.service import CalendarService
from services.reminders.service import ReminderService
from services.tasks.service import TaskService


class AssistantBriefingService:
    def __init__(
        self,
        *,
        calendar_service: CalendarService,
        reminder_service: ReminderService,
        task_service: TaskService,
        default_timezone: str,
    ) -> None:
        self._calendar_service = calendar_service
        self._reminder_service = reminder_service
        self._task_service = task_service
        self._default_timezone = default_timezone

    def get_daily_briefing(self, *, target_date: date | None = None) -> DailyBriefing:
        if target_date is None:
            target_date = datetime.now(ZoneInfo(self._default_timezone)).date()
        start, end = day_bounds(target_date, self._default_timezone)
        events = self._calendar_service.list_events(start=start, end=end)
        reminders = self._reminder_service.list_reminders(start=start, end=end)
        due_tasks = self._task_service.list_tasks_due_between(start=start, end=end)
        overdue_tasks = self._task_service.list_overdue_tasks()

        summary_lines = [
            f"{len(events)} events, {len(reminders)} reminders, {len(due_tasks)} due tasks.",
        ]
        if overdue_tasks:
            summary_lines.append(f"{len(overdue_tasks)} overdue tasks need attention.")
        if events:
            summary_lines.append(f"First event: {events[0].title}")
        elif reminders:
            summary_lines.append(f"First reminder: {reminders[0].title}")
        elif due_tasks:
            summary_lines.append(f"Top due task: {due_tasks[0].title}")
        else:
            summary_lines.append("No scheduled items for this day yet.")

        return DailyBriefing(
            date=target_date,
            timezone=self._default_timezone,
            events=events,
            reminders=reminders,
            due_tasks=due_tasks,
            overdue_tasks=overdue_tasks,
            summary_lines=summary_lines,
        )
