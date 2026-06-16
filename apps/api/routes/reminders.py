from datetime import datetime

from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import get_reminder_service, require_hermes
from core.models.entities import ReminderCreate, ReminderRead, ReminderSnooze, ReminderUpdate
from services.reminders.service import ReminderService

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("", response_model=ReminderRead, status_code=201)
def create_reminder(
    payload: ReminderCreate,
    service: ReminderService = Depends(get_reminder_service),
    _: None = Depends(require_hermes),
) -> ReminderRead:
    return service.create_reminder(payload)


@router.get("", response_model=list[ReminderRead])
def list_reminders(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    service: ReminderService = Depends(get_reminder_service),
    _: None = Depends(require_hermes),
) -> list[ReminderRead]:
    return service.list_reminders(start=start, end=end)


@router.patch("/{reminder_id}", response_model=ReminderRead)
def update_reminder(
    reminder_id: str,
    payload: ReminderUpdate,
    service: ReminderService = Depends(get_reminder_service),
    _: None = Depends(require_hermes),
) -> ReminderRead:
    return service.update_reminder(reminder_id, payload)


@router.post("/{reminder_id}/snooze", response_model=ReminderRead)
def snooze_reminder(
    reminder_id: str,
    payload: ReminderSnooze,
    service: ReminderService = Depends(get_reminder_service),
    _: None = Depends(require_hermes),
) -> ReminderRead:
    return service.snooze_reminder(reminder_id, payload)


@router.post("/{reminder_id}/dismiss", response_model=ReminderRead)
def dismiss_reminder(
    reminder_id: str,
    service: ReminderService = Depends(get_reminder_service),
    _: None = Depends(require_hermes),
) -> ReminderRead:
    return service.dismiss_reminder(reminder_id)
