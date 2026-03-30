from datetime import datetime

from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import get_calendar_service
from core.models.entities import EventCreate, EventRead, EventUpdate, FreeSlotRead
from services.calendar.service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/events", response_model=EventRead, status_code=201)
def create_event(
    payload: EventCreate,
    service: CalendarService = Depends(get_calendar_service),
) -> EventRead:
    return service.create_event(payload)


@router.get("/events", response_model=list[EventRead])
def list_events(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    service: CalendarService = Depends(get_calendar_service),
) -> list[EventRead]:
    return service.list_events(start=start, end=end)


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(
    event_id: str,
    payload: EventUpdate,
    service: CalendarService = Depends(get_calendar_service),
) -> EventRead:
    return service.update_event(event_id, payload)


@router.get("/free-slots", response_model=list[FreeSlotRead])
def get_free_slots(
    start: datetime,
    end: datetime,
    duration_minutes: int = Query(default=60, ge=1, le=1440),
    service: CalendarService = Depends(get_calendar_service),
) -> list[FreeSlotRead]:
    return service.get_free_slots(start=start, end=end, duration_minutes=duration_minutes)
