from datetime import datetime

from fastapi import HTTPException, status

from core.models.entities import EventCreate, EventRead, EventUpdate, FreeSlotRead
from services.calendar.provider import CalendarProvider


class CalendarService:
    def __init__(self, provider: CalendarProvider) -> None:
        self._provider = provider

    def create_event(self, payload: EventCreate) -> EventRead:
        return self._provider.create_event(payload)

    def list_events(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[EventRead]:
        return self._provider.list_events(start=start, end=end)

    def update_event(self, event_id: str, payload: EventUpdate) -> EventRead:
        event = self._provider.update_event(event_id, payload)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
        return event

    def get_free_slots(
        self,
        *,
        start: datetime,
        end: datetime,
        duration_minutes: int,
    ) -> list[FreeSlotRead]:
        events = self.list_events(start=start, end=end)
        merged_ranges = self._merge_event_ranges(events, start=start, end=end)
        free_slots: list[FreeSlotRead] = []
        cursor = start

        for event_start, event_end in merged_ranges:
            if event_start > cursor:
                free_slots.extend(
                    self._build_slot_if_long_enough(
                        start=cursor,
                        end=event_start,
                        duration_minutes=duration_minutes,
                    )
                )
            cursor = max(cursor, event_end)

        if cursor < end:
            free_slots.extend(
                self._build_slot_if_long_enough(
                    start=cursor,
                    end=end,
                    duration_minutes=duration_minutes,
                )
            )
        return free_slots

    @staticmethod
    def _merge_event_ranges(
        events: list[EventRead],
        *,
        start: datetime,
        end: datetime,
    ) -> list[tuple[datetime, datetime]]:
        ranges = sorted(
            (
                max(event.start_time, start),
                min(event.end_time, end),
            )
            for event in events
            if event.end_time > start and event.start_time < end
        )
        if not ranges:
            return []

        merged: list[tuple[datetime, datetime]] = [ranges[0]]
        for current_start, current_end in ranges[1:]:
            last_start, last_end = merged[-1]
            if current_start <= last_end:
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                merged.append((current_start, current_end))
        return merged

    @staticmethod
    def _build_slot_if_long_enough(
        *,
        start: datetime,
        end: datetime,
        duration_minutes: int,
    ) -> list[FreeSlotRead]:
        minutes = int((end - start).total_seconds() // 60)
        if minutes < duration_minutes:
            return []
        return [
            FreeSlotRead(
                start_time=start,
                end_time=end,
                duration_minutes=minutes,
            )
        ]
