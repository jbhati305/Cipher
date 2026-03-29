from datetime import datetime

from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import get_reminder_service
from core.models.entities import ReminderCreate, ReminderRead
from services.reminders.service import ReminderService

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("", response_model=ReminderRead, status_code=201)
def create_reminder(
    payload: ReminderCreate,
    service: ReminderService = Depends(get_reminder_service),
) -> ReminderRead:
    return service.create_reminder(payload)


@router.get("", response_model=list[ReminderRead])
def list_reminders(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    service: ReminderService = Depends(get_reminder_service),
) -> list[ReminderRead]:
    return service.list_reminders(start=start, end=end)
