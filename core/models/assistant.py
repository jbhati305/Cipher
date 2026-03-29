from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssistantIntent(StrEnum):
    CREATE_TASK = "create_task"
    CREATE_REMINDER = "create_reminder"
    CREATE_NOTE = "create_note"
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
    parsed_at: datetime
    warnings: list[str] = Field(default_factory=list)
