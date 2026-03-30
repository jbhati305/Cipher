from datetime import date, datetime, time
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from core.config import Settings
from core.models.entities import EventCreate, EventRead, EventUpdate


class CalendarProvider(Protocol):
    def create_event(self, payload: EventCreate) -> EventRead: ...

    def list_events(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[EventRead]: ...

    def update_event(self, event_id: str, payload: EventUpdate) -> EventRead | None: ...


class GoogleCalendarProvider:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_event(self, payload: EventCreate) -> EventRead:
        service = self._build_service()
        event = service.events().insert(
            calendarId=self._settings.google_calendar_id,
            body=self._event_resource_from_create(payload),
        ).execute()
        return self._map_event(event)

    def list_events(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[EventRead]:
        service = self._build_service()
        params = {
            "calendarId": self._settings.google_calendar_id,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if start is not None:
            params["timeMin"] = start.isoformat()
        if end is not None:
            params["timeMax"] = end.isoformat()

        response = service.events().list(**params).execute()
        return [self._map_event(item) for item in response.get("items", [])]

    def update_event(self, event_id: str, payload: EventUpdate) -> EventRead | None:
        service = self._build_service()
        body = self._event_resource_from_update(payload)
        try:
            event = service.events().patch(
                calendarId=self._settings.google_calendar_id,
                eventId=event_id,
                body=body,
            ).execute()
        except self._http_error_type() as exc:
            if getattr(exc, "status_code", None) == 404 or getattr(
                getattr(exc, "resp", None),
                "status",
                None,
            ) == 404:
                return None
            raise
        return self._map_event(event)

    def _build_service(self):
        credentials = load_google_calendar_credentials(self._settings, interactive=False)
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Google Calendar dependencies are missing. Run `uv sync --dev` to install them."
                ),
            ) from exc

        return build("calendar", "v3", credentials=credentials, cache_discovery=False)

    @staticmethod
    def _http_error_type():
        try:
            from googleapiclient.errors import HttpError
        except ImportError:
            return Exception
        return HttpError

    def _map_event(self, event: dict) -> EventRead:
        start_time = self._parse_google_time(event.get("start", {}))
        end_time = self._parse_google_time(event.get("end", {}))
        created_at = self._parse_iso_datetime(event.get("created")) or start_time
        updated_at = self._parse_iso_datetime(event.get("updated")) or created_at
        event_id = event["id"]

        return EventRead(
            id=event_id,
            code=event_id,
            created_at=created_at,
            updated_at=updated_at,
            title=event.get("summary") or "Untitled event",
            start_time=start_time,
            end_time=end_time,
            location=event.get("location"),
            description=event.get("description"),
            related_entity_ids=[],
        )

    def _parse_google_time(self, value: dict) -> datetime:
        if "dateTime" in value:
            return self._parse_iso_datetime(value["dateTime"])
        if "date" in value:
            all_day = date.fromisoformat(value["date"])
            return datetime.combine(
                all_day,
                time.min,
                tzinfo=ZoneInfo(self._settings.default_timezone),
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google Calendar returned an event without a usable time field.",
        )

    @staticmethod
    def _parse_iso_datetime(value: str | None) -> datetime | None:
        if value is None:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _event_resource_from_create(payload: EventCreate) -> dict:
        return {
            "summary": payload.title,
            "location": payload.location,
            "description": payload.description,
            "start": {"dateTime": payload.start_time.isoformat()},
            "end": {"dateTime": payload.end_time.isoformat()},
        }

    @staticmethod
    def _event_resource_from_update(payload: EventUpdate) -> dict:
        updates = payload.model_dump(exclude_unset=True)
        body: dict = {}
        if "title" in updates:
            body["summary"] = updates["title"]
        if "location" in updates:
            body["location"] = updates["location"]
        if "description" in updates:
            body["description"] = updates["description"]
        if "start_time" in updates:
            body["start"] = {"dateTime": updates["start_time"].isoformat()}
        if "end_time" in updates:
            body["end"] = {"dateTime": updates["end_time"].isoformat()}
        return body


def authenticate_google_calendar(settings: Settings) -> Path:
    credentials = load_google_calendar_credentials(settings, interactive=True)
    token_path = Path(settings.google_calendar_token_file)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return token_path


def load_google_calendar_credentials(settings: Settings, *, interactive: bool):
    if not settings.google_calendar_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Google Calendar is not configured. "
                "Set GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET in .env."
            ),
        )
    token_path = Path(settings.google_calendar_token_file)

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Google Calendar dependencies are missing. Run `uv sync --dev` to install them."
            ),
        ) from exc

    credentials = None
    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(
            str(token_path),
            GoogleCalendarProvider.SCOPES,
        )

    if credentials and credentials.valid:
        return credentials

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        return credentials

    if not interactive:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Google Calendar is not authenticated yet. "
                "Run `uv run cipher-google-calendar-auth` "
                "to authorize Cipher before using calendar endpoints."
            ),
        )

    flow = InstalledAppFlow.from_client_config(
        _google_oauth_client_config(settings),
        GoogleCalendarProvider.SCOPES,
    )
    return flow.run_local_server(port=0)


def _google_oauth_client_config(settings: Settings) -> dict:
    return {
        "installed": {
            "client_id": settings.google_calendar_client_id,
            "client_secret": settings.google_calendar_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                "http://localhost",
                "http://localhost:8080",
                "http://localhost:3000",
            ],
        }
    }
