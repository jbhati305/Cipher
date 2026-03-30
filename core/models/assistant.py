from __future__ import annotations

from datetime import date as date_type
from datetime import datetime as datetime_type
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.models.entities import (
    EventRead,
    FreeSlotRead,
    NoteRead,
    PersonRead,
    ProjectRead,
    ReminderRead,
    TaskRead,
)


class AssistantIntent(StrEnum):
    CREATE_TASK = "create_task"
    CREATE_REMINDER = "create_reminder"
    CREATE_NOTE = "create_note"
    CREATE_EVENT = "create_event"
    QUERY_AGENDA = "query_agenda"
    QUERY_PROJECT_TASKS = "query_project_tasks"
    QUERY_REMINDERS = "query_reminders"
    UPDATE_TASK_STATUS = "update_task_status"
    RESCHEDULE_REMINDER = "reschedule_reminder"
    UNKNOWN = "unknown"


class ParseCommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)


class ParsedCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: AssistantIntent
    confidence: float = Field(ge=0.0, le=1.0)
    payload: dict[str, Any]
    raw_text: str
    parsed_at: datetime_type
    warnings: list[str] = Field(default_factory=list)


class AssistantLLMMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt_version: str | None = None
    provider: str | None = None
    model: str | None = None
    used_llm: bool = False
    fallback_used: bool = False
    context_items: int = Field(default=0, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class AssistantContextBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str
    date: date_type | None = None
    week_start: date_type | None = None
    week_end: date_type | None = None
    project: ProjectRead | None = None
    events: list[EventRead] = Field(default_factory=list)
    reminders: list[ReminderRead] = Field(default_factory=list)
    due_tasks: list[TaskRead] = Field(default_factory=list)
    overdue_tasks: list[TaskRead] = Field(default_factory=list)
    completed_tasks: list[TaskRead] = Field(default_factory=list)
    open_tasks: list[TaskRead] = Field(default_factory=list)
    blocked_tasks: list[TaskRead] = Field(default_factory=list)
    related_notes: list[NoteRead] = Field(default_factory=list)
    related_people: list[PersonRead] = Field(default_factory=list)
    active_projects: list[ProjectRead] = Field(default_factory=list)
    free_slots: list[FreeSlotRead] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def context_item_count(self) -> int:
        return (
            len(self.events)
            + len(self.reminders)
            + len(self.due_tasks)
            + len(self.overdue_tasks)
            + len(self.completed_tasks)
            + len(self.open_tasks)
            + len(self.blocked_tasks)
            + len(self.related_notes)
            + len(self.related_people)
            + len(self.active_projects)
            + len(self.free_slots)
            + (1 if self.project is not None else 0)
        )


class DailyBriefing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date_type
    timezone: str
    events: list[EventRead] = Field(default_factory=list)
    reminders: list[ReminderRead] = Field(default_factory=list)
    due_tasks: list[TaskRead] = Field(default_factory=list)
    overdue_tasks: list[TaskRead] = Field(default_factory=list)
    summary_lines: list[str] = Field(default_factory=list)
    generated_summary: str | None = None
    suggested_focus: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)
    llm_meta: AssistantLLMMeta | None = None


class WeeklyReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date_type
    week_start: date_type
    week_end: date_type
    timezone: str
    completed_tasks: list[TaskRead] = Field(default_factory=list)
    overdue_tasks: list[TaskRead] = Field(default_factory=list)
    upcoming_tasks: list[TaskRead] = Field(default_factory=list)
    active_projects: list[ProjectRead] = Field(default_factory=list)
    follow_up_people: list[PersonRead] = Field(default_factory=list)
    generated_summary: str
    wins: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    llm_meta: AssistantLLMMeta | None = None


class ProjectSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project: ProjectRead
    open_tasks: list[TaskRead] = Field(default_factory=list)
    blocked_tasks: list[TaskRead] = Field(default_factory=list)
    due_tasks: list[TaskRead] = Field(default_factory=list)
    related_notes: list[NoteRead] = Field(default_factory=list)
    related_people: list[PersonRead] = Field(default_factory=list)
    generated_summary: str
    priority_items: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    llm_meta: AssistantLLMMeta | None = None


class FocusSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    reason: str
    related_entity_ids: list[str] = Field(default_factory=list)
    suggested_duration_minutes: int | None = Field(default=None, ge=1)


class FocusSuggestionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date_type
    timezone: str
    candidate_tasks: list[TaskRead] = Field(default_factory=list)
    free_slots: list[FreeSlotRead] = Field(default_factory=list)
    suggestions: list[FocusSuggestion] = Field(default_factory=list)
    generated_summary: str
    llm_meta: AssistantLLMMeta | None = None


class FollowUpSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person_id: str | None = None
    person_name: str
    reason: str
    suggested_action: str
    related_entity_ids: list[str] = Field(default_factory=list)


class FollowUpSuggestionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime_type
    suggestions: list[FollowUpSuggestion] = Field(default_factory=list)
    generated_summary: str
    llm_meta: AssistantLLMMeta | None = None
