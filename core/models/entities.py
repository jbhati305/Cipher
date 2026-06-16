from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.utils.recurrence import is_supported_recurrence_rule


class EntityType(StrEnum):
    USER = "User"
    PERSON = "Person"
    PROJECT = "Project"
    TASK = "Task"
    REMINDER = "Reminder"
    EVENT = "Event"
    NOTE = "Note"
    GOAL = "Goal"


class ProjectStatus(StrEnum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ReminderStatus(StrEnum):
    SCHEDULED = "scheduled"
    TRIGGERED = "triggered"
    SNOOZED = "snoozed"
    DISMISSED = "dismissed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReminderChannel(StrEnum):
    IN_APP = "in_app"
    CONSOLE = "console"


class ModelBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EntityDetail(ModelBase):
    id: str
    entity_type: EntityType
    properties: dict[str, Any]


class RelatedEntity(ModelBase):
    relation_type: str
    direction: Literal["incoming", "outgoing"]
    entity: EntityDetail


class TimestampedReadModel(ModelBase):
    id: str
    code: str
    created_at: datetime
    updated_at: datetime


class ProjectCreate(ModelBase):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    priority: TaskPriority = TaskPriority.MEDIUM


class ProjectRead(TimestampedReadModel):
    name: str
    description: str | None = None
    status: ProjectStatus
    priority: TaskPriority


class PersonCreate(ModelBase):
    name: str = Field(min_length=1, max_length=200)
    relationship_type: str | None = None
    notes: str | None = None


class PersonRead(TimestampedReadModel):
    name: str
    relationship_type: str | None = None
    notes: str | None = None


class TaskCreate(ModelBase):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: datetime | None = None
    estimated_effort: str | None = None
    project_id: str | None = None
    related_entity_ids: list[str] = Field(default_factory=list)


class TaskUpdate(ModelBase):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    deadline: datetime | None = None
    estimated_effort: str | None = None
    project_id: str | None = None
    related_entity_ids: list[str] | None = None

    @model_validator(mode="after")
    def validate_required_fields_when_present(self) -> "TaskUpdate":
        for field_name in ("title", "status", "priority"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null when provided.")
        return self


class TaskRead(TimestampedReadModel):
    title: str
    description: str | None = None
    status: TaskStatus
    priority: TaskPriority
    deadline: datetime | None = None
    estimated_effort: str | None = None
    project_id: str | None = None
    related_entity_ids: list[str] = Field(default_factory=list)


class ReminderCreate(ModelBase):
    title: str = Field(min_length=1, max_length=200)
    trigger_time: datetime
    recurrence_rule: str | None = None
    status: ReminderStatus = ReminderStatus.SCHEDULED
    channel: ReminderChannel = ReminderChannel.IN_APP
    related_entity_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_recurrence(self) -> "ReminderCreate":
        if not is_supported_recurrence_rule(self.recurrence_rule):
            raise ValueError("Unsupported recurrence_rule. Use daily, weekly, monthly, or RRULE.")
        return self


class ReminderUpdate(ModelBase):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    trigger_time: datetime | None = None
    recurrence_rule: str | None = None
    status: ReminderStatus | None = None
    channel: ReminderChannel | None = None
    related_entity_ids: list[str] | None = None

    @model_validator(mode="after")
    def validate_required_fields_when_present(self) -> "ReminderUpdate":
        for field_name in ("title", "trigger_time", "status", "channel"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null when provided.")
        if "recurrence_rule" in self.model_fields_set and not is_supported_recurrence_rule(
            self.recurrence_rule
        ):
            raise ValueError("Unsupported recurrence_rule. Use daily, weekly, monthly, or RRULE.")
        return self


class ReminderSnooze(ModelBase):
    until: datetime


class ReminderRead(TimestampedReadModel):
    title: str
    trigger_time: datetime
    recurrence_rule: str | None = None
    status: ReminderStatus
    channel: ReminderChannel
    last_triggered_at: datetime | None = None
    trigger_count: int = 0
    related_entity_ids: list[str] = Field(default_factory=list)


class EventCreate(ModelBase):
    title: str = Field(min_length=1, max_length=200)
    start_time: datetime
    end_time: datetime
    location: str | None = None
    description: str | None = None
    related_entity_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_time_range(self) -> "EventCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time.")
        return self


class EventUpdate(ModelBase):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str | None = None
    description: str | None = None
    related_entity_ids: list[str] | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> "EventUpdate":
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            raise ValueError("end_time must be after start_time.")
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title cannot be null when provided.")
        return self


class EventRead(TimestampedReadModel):
    title: str
    start_time: datetime
    end_time: datetime
    location: str | None = None
    description: str | None = None
    related_entity_ids: list[str] = Field(default_factory=list)


class FreeSlotRead(ModelBase):
    start_time: datetime
    end_time: datetime
    duration_minutes: int


class NoteCreate(ModelBase):
    title: str | None = Field(default=None, max_length=200)
    content: str = Field(min_length=1)
    source: str | None = None
    related_entity_ids: list[str] = Field(default_factory=list)


class NoteRead(TimestampedReadModel):
    title: str
    content: str
    source: str | None = None
    related_entity_ids: list[str] = Field(default_factory=list)


class MemoryWrite(ModelBase):
    content: str = Field(min_length=1)
    kind: str = Field(default="note", min_length=1, max_length=80)
    source: str = Field(default="cipher", min_length=1, max_length=80)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryRecord(ModelBase):
    id: str
    content: str
    kind: str
    source: str
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class MemorySearchResult(ModelBase):
    id: str | None = None
    content: str
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaperRead(ModelBase):
    id: str
    title: str
    authors: str | None = None
    status: str | None = None
    url: str | None = None
    notion_page_id: str
    updated_at: datetime | None = None


class VoiceMessage(ModelBase):
    session_id: str | None = None
    utterance: str = Field(min_length=1)
    source: str = Field(default="alexa")
    allow_api_fallback: bool = False


class VoiceReply(ModelBase):
    session_id: str
    reply: str
    stored_summary: str | None = None
    used_async_processing: bool = False


class ReflectionRequest(ModelBase):
    prompt: str | None = None
    include_today: bool = True


class ReflectionSummary(ModelBase):
    id: str
    summary: str
    created_at: datetime
