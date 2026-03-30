from datetime import date

from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import (
    get_assistant_service,
    get_briefing_service,
    get_parser_service,
)
from core.models.assistant import (
    DailyBriefing,
    FocusSuggestionsResponse,
    FollowUpSuggestionsResponse,
    ParseCommandRequest,
    ParsedCommand,
    ProjectSummary,
    WeeklyReview,
)
from services.assistant.parser import AssistantParserService
from services.assistant.service import AssistantService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/parse-command", response_model=ParsedCommand)
def parse_command(
    payload: ParseCommandRequest,
    service: AssistantParserService = Depends(get_parser_service),
) -> ParsedCommand:
    return service.parse(payload.text)


@router.get("/daily-briefing", response_model=DailyBriefing)
def daily_briefing(
    target_date: date | None = Query(default=None, alias="date"),
    service: AssistantService = Depends(get_briefing_service),
) -> DailyBriefing:
    return service.get_daily_briefing(target_date=target_date)


@router.get("/weekly-review", response_model=WeeklyReview)
def weekly_review(
    target_date: date | None = Query(default=None, alias="date"),
    service: AssistantService = Depends(get_assistant_service),
) -> WeeklyReview:
    return service.get_weekly_review(target_date=target_date)


@router.get("/project-summary", response_model=ProjectSummary)
def project_summary(
    project: str = Query(min_length=1),
    service: AssistantService = Depends(get_assistant_service),
) -> ProjectSummary:
    return service.get_project_summary(project_reference=project)


@router.get("/focus-suggestions", response_model=FocusSuggestionsResponse)
def focus_suggestions(
    target_date: date | None = Query(default=None, alias="date"),
    service: AssistantService = Depends(get_assistant_service),
) -> FocusSuggestionsResponse:
    return service.get_focus_suggestions(target_date=target_date)


@router.get("/follow-up-suggestions", response_model=FollowUpSuggestionsResponse)
def follow_up_suggestions(
    days: int = Query(default=14, ge=1, le=60),
    service: AssistantService = Depends(get_assistant_service),
) -> FollowUpSuggestionsResponse:
    return service.get_follow_up_suggestions(days=days)
