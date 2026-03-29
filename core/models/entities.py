from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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


class ReminderRead(TimestampedReadModel):
    title: str
    trigger_time: datetime
    recurrence_rule: str | None = None
    status: ReminderStatus
    channel: ReminderChannel
    related_entity_ids: list[str] = Field(default_factory=list)


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
