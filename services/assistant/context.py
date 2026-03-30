from datetime import UTC, date, datetime, timedelta
from typing import TypeVar
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from core.models.assistant import AssistantContextBundle
from core.models.entities import (
    EntityType,
    NoteRead,
    PersonRead,
    ProjectRead,
    ProjectStatus,
    TaskPriority,
    TaskRead,
    TaskStatus,
)
from core.utils.dates import day_bounds
from services.calendar.service import CalendarService
from services.memory.service import MemoryService
from services.projects.service import ProjectService
from services.reminders.service import ReminderService
from services.tasks.service import TaskService

T = TypeVar("T")


class AssistantContextService:
    def __init__(
        self,
        *,
        calendar_service: CalendarService,
        reminder_service: ReminderService,
        task_service: TaskService,
        project_service: ProjectService,
        memory_service: MemoryService,
        default_timezone: str,
        max_context_items: int,
    ) -> None:
        self._calendar_service = calendar_service
        self._reminder_service = reminder_service
        self._task_service = task_service
        self._project_service = project_service
        self._memory_service = memory_service
        self._default_timezone = default_timezone
        self._max_context_items = max(6, max_context_items)

    def build_daily_context(self, *, target_date: date | None = None) -> AssistantContextBundle:
        resolved_date = self._resolve_date(target_date)
        start, end = day_bounds(resolved_date, self._default_timezone)
        events = self._calendar_service.list_events(start=start, end=end)
        reminders = self._reminder_service.list_reminders(start=start, end=end)
        due_tasks = self._task_service.list_tasks_due_between(start=start, end=end)
        overdue_tasks = self._task_service.list_overdue_tasks()
        open_tasks = self._open_tasks(self._task_service.list_tasks())
        free_slots = self._calendar_service.get_free_slots(
            start=start,
            end=end,
            duration_minutes=45,
        )
        projects = self._rank_projects(self._project_service.list_projects(), open_tasks)

        return AssistantContextBundle(
            intent="daily_briefing",
            date=resolved_date,
            events=self._limit(events, 3),
            reminders=self._limit(reminders, 3),
            due_tasks=self._limit(self._rank_tasks_for_focus(due_tasks, start, end), 4),
            overdue_tasks=self._limit(self._rank_tasks_for_focus(overdue_tasks, start, end), 3),
            active_projects=self._limit(projects, 3),
            free_slots=self._limit(free_slots, 3),
            metadata={
                "timezone": self._default_timezone,
                "available_focus_minutes": sum(slot.duration_minutes for slot in free_slots[:2]),
            },
        )

    def build_weekly_context(self, *, target_date: date | None = None) -> AssistantContextBundle:
        resolved_date = self._resolve_date(target_date)
        week_start, week_end = self._week_bounds(resolved_date)
        start, _ = day_bounds(week_start, self._default_timezone)
        _, end = day_bounds(week_end, self._default_timezone)
        all_tasks = self._task_service.list_tasks()
        open_tasks = self._open_tasks(all_tasks)
        completed_tasks = [
            task
            for task in all_tasks
            if task.status == TaskStatus.COMPLETED and start <= task.updated_at < end
        ]
        overdue_tasks = self._task_service.list_overdue_tasks()
        upcoming_tasks = self._task_service.list_tasks_due_between(start=start, end=end)
        active_projects = self._rank_projects(self._project_service.list_projects(), open_tasks)
        follow_up_context = self.build_follow_up_context(days=14)

        return AssistantContextBundle(
            intent="weekly_review",
            date=resolved_date,
            week_start=week_start,
            week_end=week_end,
            completed_tasks=self._limit(
                sorted(completed_tasks, key=lambda task: task.updated_at, reverse=True),
                5,
            ),
            overdue_tasks=self._limit(self._rank_tasks_for_focus(overdue_tasks, start, end), 4),
            due_tasks=self._limit(self._rank_tasks_for_focus(upcoming_tasks, start, end), 4),
            active_projects=self._limit(active_projects, 4),
            related_people=self._limit(follow_up_context.related_people, 4),
            metadata={
                "timezone": self._default_timezone,
                "completed_count": len(completed_tasks),
                "open_count": len(open_tasks),
            },
        )

    def build_project_context(self, *, project_reference: str) -> AssistantContextBundle:
        project = self._resolve_project(project_reference)
        tasks = self._task_service.list_tasks(project_id=project.id)
        open_tasks = [
            task
            for task in tasks
            if task.status not in {TaskStatus.COMPLETED, TaskStatus.ARCHIVED}
        ]
        blocked_tasks = [task for task in open_tasks if task.status == TaskStatus.BLOCKED]
        due_tasks = [task for task in open_tasks if task.deadline is not None]
        related_entities = self._memory_service.get_related_entities(project.id)
        related_notes: list[NoteRead] = []
        related_people: list[PersonRead] = []

        for related in related_entities:
            entity = related.entity
            if entity.entity_type == EntityType.NOTE:
                related_notes.append(NoteRead(**entity.properties))
            elif entity.entity_type == EntityType.PERSON:
                related_people.append(PersonRead(**entity.properties))

        return AssistantContextBundle(
            intent="project_summary",
            project=project,
            open_tasks=self._limit(self._rank_project_tasks(open_tasks), 5),
            blocked_tasks=self._limit(self._rank_project_tasks(blocked_tasks), 3),
            due_tasks=self._limit(
                sorted(
                    due_tasks,
                    key=lambda task: task.deadline or datetime.max.replace(tzinfo=UTC),
                ),
                4,
            ),
            related_notes=self._limit(
                sorted(related_notes, key=lambda note: note.updated_at, reverse=True),
                3,
            ),
            related_people=self._limit(
                sorted(related_people, key=lambda person: person.updated_at, reverse=True),
                4,
            ),
            metadata={"project_reference": project_reference},
        )

    def build_focus_context(self, *, target_date: date | None = None) -> AssistantContextBundle:
        daily = self.build_daily_context(target_date=target_date)
        start, end = day_bounds(daily.date or self._resolve_date(None), self._default_timezone)
        open_tasks = self._open_tasks(self._task_service.list_tasks())
        candidate_tasks = self._rank_tasks_for_focus(open_tasks, start, end)

        return daily.model_copy(
            update={
                "intent": "focus_suggestions",
                "open_tasks": self._limit(candidate_tasks, 5),
            }
        )

    def build_follow_up_context(self, *, days: int = 14) -> AssistantContextBundle:
        now = datetime.now(ZoneInfo(self._default_timezone))
        end = now + timedelta(days=days)
        people = self._memory_service.list_people()
        tasks = self._open_tasks(self._task_service.list_tasks())
        reminders = self._reminder_service.list_reminders(start=now - timedelta(days=1), end=end)
        scored_people: list[tuple[int, PersonRead, list[str]]] = []
        selected_task_ids: set[str] = set()
        selected_reminder_ids: set[str] = set()

        for person in people:
            score = 0
            reasons: list[str] = []
            for task in tasks:
                if person.id not in task.related_entity_ids:
                    continue
                selected_task_ids.add(task.id)
                score += self._task_priority_weight(task) + 15
                if task.deadline is not None and task.deadline <= end:
                    reasons.append(
                        "Task "
                        f"'{task.title}' is pending before {task.deadline.date().isoformat()}."
                    )
                    score += 20
                elif task.status == TaskStatus.BLOCKED:
                    reasons.append(f"Task '{task.title}' is blocked.")
                    score += 10
            for reminder in reminders:
                if person.id not in reminder.related_entity_ids:
                    continue
                selected_reminder_ids.add(reminder.id)
                reasons.append(
                    "Reminder "
                    f"'{reminder.title}' is scheduled for "
                    f"{reminder.trigger_time.date().isoformat()}."
                )
                score += 25
            if reasons:
                scored_people.append((score, person, reasons[:2]))

        ranked_people = sorted(
            scored_people,
            key=lambda item: (-item[0], item[1].updated_at),
        )
        top_people = [person for _, person, _ in ranked_people[:5]]
        people_reasons = {
            person.id: " ".join(reasons)
            for _, person, reasons in ranked_people[:5]
        }

        return AssistantContextBundle(
            intent="follow_up_suggestions",
            related_people=top_people,
            open_tasks=self._limit(
                [task for task in tasks if task.id in selected_task_ids],
                5,
            ),
            reminders=self._limit(
                [reminder for reminder in reminders if reminder.id in selected_reminder_ids],
                5,
            ),
            metadata={
                "generated_at": now.isoformat(),
                "people_reasons": people_reasons,
            },
        )

    def _resolve_date(self, target_date: date | None) -> date:
        if target_date is not None:
            return target_date
        return datetime.now(ZoneInfo(self._default_timezone)).date()

    def _resolve_project(self, project_reference: str) -> ProjectRead:
        normalized = project_reference.strip().lower()
        projects = self._project_service.list_projects()

        exact_matches = [
            project
            for project in projects
            if normalized in {project.id.lower(), project.code.lower(), project.name.lower()}
        ]
        if exact_matches:
            return exact_matches[0]

        partial_matches = [
            project
            for project in projects
            if normalized in project.name.lower() or normalized in project.code.lower()
        ]
        if partial_matches:
            return partial_matches[0]

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_reference}' was not found.",
        )

    def _week_bounds(self, target_date: date) -> tuple[date, date]:
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start, week_end

    def _rank_tasks_for_focus(
        self,
        tasks: list[TaskRead],
        start: datetime,
        end: datetime,
    ) -> list[TaskRead]:
        unique_tasks = self._dedupe(tasks, key=lambda task: task.id)
        return sorted(
            unique_tasks,
            key=lambda task: (
                -self._task_focus_score(task, start, end),
                task.deadline or datetime.max.replace(tzinfo=UTC),
                task.updated_at,
            ),
        )

    def _rank_project_tasks(self, tasks: list[TaskRead]) -> list[TaskRead]:
        start = datetime.now(ZoneInfo(self._default_timezone))
        end = start + timedelta(days=14)
        return self._rank_tasks_for_focus(tasks, start, end)

    def _rank_projects(
        self,
        projects: list[ProjectRead],
        tasks: list[TaskRead],
    ) -> list[ProjectRead]:
        tasks_by_project: dict[str, list[TaskRead]] = {}
        for task in tasks:
            if task.project_id is None:
                continue
            tasks_by_project.setdefault(task.project_id, []).append(task)

        return sorted(
            projects,
            key=lambda project: (
                -self._project_score(project, tasks_by_project.get(project.id, [])),
                project.updated_at,
            ),
        )

    def _project_score(self, project: ProjectRead, tasks: list[TaskRead]) -> int:
        status_weights = {
            ProjectStatus.ACTIVE: 40,
            ProjectStatus.PLANNING: 15,
            ProjectStatus.ON_HOLD: 5,
            ProjectStatus.COMPLETED: -20,
            ProjectStatus.ARCHIVED: -40,
        }
        score = status_weights[project.status]
        priority_weights = {
            TaskPriority.LOW: 5,
            TaskPriority.MEDIUM: 10,
            TaskPriority.HIGH: 20,
            TaskPriority.URGENT: 30,
        }
        score += priority_weights[project.priority]
        score += min(len(tasks), 5) * 5
        if any(task.status == TaskStatus.BLOCKED for task in tasks):
            score += 10
        if any(task.deadline is not None for task in tasks):
            score += 15
        return score

    def _task_focus_score(self, task: TaskRead, start: datetime, end: datetime) -> int:
        score = self._task_priority_weight(task)
        status_weights = {
            TaskStatus.PENDING: 20,
            TaskStatus.IN_PROGRESS: 35,
            TaskStatus.BLOCKED: 5,
            TaskStatus.COMPLETED: -50,
            TaskStatus.ARCHIVED: -100,
        }
        score += status_weights[task.status]
        if task.deadline is not None:
            if task.deadline < start:
                score += 80
            elif start <= task.deadline <= end:
                score += 55
            else:
                score += 10
        return score

    @staticmethod
    def _task_priority_weight(task: TaskRead) -> int:
        return {
            TaskPriority.LOW: 5,
            TaskPriority.MEDIUM: 15,
            TaskPriority.HIGH: 30,
            TaskPriority.URGENT: 45,
        }[task.priority]

    @staticmethod
    def _open_tasks(tasks: list[TaskRead]) -> list[TaskRead]:
        return [
            task for task in tasks if task.status not in {TaskStatus.COMPLETED, TaskStatus.ARCHIVED}
        ]

    @staticmethod
    def _dedupe(items: list[T], *, key) -> list[T]:  # noqa: ANN001
        seen: set[str] = set()
        unique_items: list[T] = []
        for item in items:
            item_key = key(item)
            if item_key in seen:
                continue
            seen.add(item_key)
            unique_items.append(item)
        return unique_items

    def _limit(self, items: list[T], limit: int) -> list[T]:
        effective_limit = min(limit, self._max_context_items)
        return items[:effective_limit]
