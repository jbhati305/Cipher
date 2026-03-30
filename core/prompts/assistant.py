from datetime import datetime

from core.models.assistant import AssistantContextBundle
from core.models.entities import (
    EventRead,
    FreeSlotRead,
    NoteRead,
    PersonRead,
    ProjectRead,
    ReminderRead,
    TaskRead,
)

PROMPT_VERSION = "phase3.v1"

BASE_INSTRUCTIONS = (
    "You are Cipher's assistant planning layer. "
    "Use only the provided context. "
    "Do not invent entities, dates, or commitments. "
    "Prefer concise wording. "
    "If the context is weak, stay cautious and say what is missing. "
    "Return only valid JSON matching the schema."
)


def build_daily_briefing_prompt(
    bundle: AssistantContextBundle,
    *,
    note_char_limit: int,
) -> tuple[str, str]:
    instructions = (
        f"{BASE_INSTRUCTIONS} "
        "Create a short daily briefing with one compact summary, up to 3 focus bullets, "
        "and up to 2 follow-up bullets."
    )
    return instructions, _render_context(bundle, note_char_limit=note_char_limit)


def build_weekly_review_prompt(
    bundle: AssistantContextBundle,
    *,
    note_char_limit: int,
) -> tuple[str, str]:
    instructions = (
        f"{BASE_INSTRUCTIONS} "
        "Write a concise weekly review with: one summary, up to 3 wins, up to 3 risks, "
        "and up to 3 next actions."
    )
    return instructions, _render_context(bundle, note_char_limit=note_char_limit)


def build_project_summary_prompt(
    bundle: AssistantContextBundle,
    *,
    note_char_limit: int,
) -> tuple[str, str]:
    instructions = (
        f"{BASE_INSTRUCTIONS} "
        "Write a project summary with one short overview, up to 3 priority items, "
        "and up to 3 next actions."
    )
    return instructions, _render_context(bundle, note_char_limit=note_char_limit)


def build_focus_suggestions_prompt(
    bundle: AssistantContextBundle,
    *,
    note_char_limit: int,
) -> tuple[str, str]:
    instructions = (
        f"{BASE_INSTRUCTIONS} "
        "Recommend up to 3 focus blocks. "
        "Prefer overdue or high-value work that fits the available time. "
        "Each suggestion should stay concrete and grounded in the provided entities."
    )
    return instructions, _render_context(bundle, note_char_limit=note_char_limit)


def build_follow_up_suggestions_prompt(
    bundle: AssistantContextBundle,
    *,
    note_char_limit: int,
) -> tuple[str, str]:
    instructions = (
        f"{BASE_INSTRUCTIONS} "
        "Recommend up to 5 follow-ups with concrete reasons and actions. "
        "Only suggest people who are clearly supported by the context."
    )
    return instructions, _render_context(bundle, note_char_limit=note_char_limit)


def _render_context(bundle: AssistantContextBundle, *, note_char_limit: int) -> str:
    lines = [f"Intent: {bundle.intent}"]
    if bundle.date is not None:
        lines.append(f"Date: {bundle.date.isoformat()}")
    if bundle.week_start is not None and bundle.week_end is not None:
        lines.append(f"Week: {bundle.week_start.isoformat()} to {bundle.week_end.isoformat()}")
    if bundle.project is not None:
        lines.extend(["Project:", _format_project(bundle.project)])

    if bundle.metadata:
        metadata_lines = [f"- {key}: {value}" for key, value in sorted(bundle.metadata.items())]
        lines.extend(["Metadata:"] + metadata_lines)

    _append_section(lines, "Events", (_format_event(event) for event in bundle.events))
    _append_section(
        lines,
        "Reminders",
        (_format_reminder(reminder) for reminder in bundle.reminders),
    )
    _append_section(lines, "Due tasks", (_format_task(task) for task in bundle.due_tasks))
    _append_section(
        lines,
        "Overdue tasks",
        (_format_task(task) for task in bundle.overdue_tasks),
    )
    _append_section(
        lines,
        "Completed tasks",
        (_format_task(task) for task in bundle.completed_tasks),
    )
    _append_section(lines, "Open tasks", (_format_task(task) for task in bundle.open_tasks))
    _append_section(
        lines,
        "Blocked tasks",
        (_format_task(task) for task in bundle.blocked_tasks),
    )
    _append_section(
        lines,
        "Projects",
        (_format_project(project) for project in bundle.active_projects),
    )
    _append_section(
        lines,
        "People",
        (_format_person(person) for person in bundle.related_people),
    )
    _append_section(
        lines,
        "Notes",
        (_format_note(note, note_char_limit=note_char_limit) for note in bundle.related_notes),
    )
    _append_section(lines, "Free slots", (_format_slot(slot) for slot in bundle.free_slots))
    return "\n".join(lines)


def _append_section(lines: list[str], heading: str, items) -> None:  # noqa: ANN001
    section_items = [item for item in items if item]
    if not section_items:
        return
    lines.append(f"{heading}:")
    lines.extend(f"- {item}" for item in section_items)


def _format_task(task: TaskRead) -> str:
    parts = [task.code, task.title, f"status={task.status}", f"priority={task.priority}"]
    if task.deadline is not None:
        parts.append(f"deadline={_format_datetime(task.deadline)}")
    if task.estimated_effort:
        parts.append(f"effort={task.estimated_effort}")
    if task.project_id:
        parts.append(f"project={task.project_id}")
    return " | ".join(parts)


def _format_reminder(reminder: ReminderRead) -> str:
    parts = [
        reminder.code,
        reminder.title,
        f"time={_format_datetime(reminder.trigger_time)}",
        f"status={reminder.status}",
    ]
    if reminder.recurrence_rule:
        parts.append(f"recurrence={reminder.recurrence_rule}")
    return " | ".join(parts)


def _format_event(event: EventRead) -> str:
    parts = [
        event.code,
        event.title,
        f"start={_format_datetime(event.start_time)}",
        f"end={_format_datetime(event.end_time)}",
    ]
    if event.location:
        parts.append(f"location={event.location}")
    return " | ".join(parts)


def _format_project(project: ProjectRead) -> str:
    parts = [project.code, project.name, f"status={project.status}", f"priority={project.priority}"]
    if project.description:
        parts.append(f"desc={project.description[:120]}")
    return " | ".join(parts)


def _format_person(person: PersonRead) -> str:
    parts = [person.code, person.name]
    if person.relationship_type:
        parts.append(f"relationship={person.relationship_type}")
    if person.notes:
        parts.append(f"notes={person.notes[:100]}")
    return " | ".join(parts)


def _format_note(note: NoteRead, *, note_char_limit: int) -> str:
    title = note.title or "Untitled note"
    snippet = note.content[:note_char_limit].replace("\n", " ").strip()
    return f"{note.code} | {title} | {snippet}"


def _format_slot(slot: FreeSlotRead) -> str:
    return (
        f"{_format_datetime(slot.start_time)} to {_format_datetime(slot.end_time)} "
        f"({slot.duration_minutes}m)"
    )


def _format_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")
