import logging
from datetime import UTC, date, datetime
from typing import TypeVar
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from core.models.assistant import (
    AssistantLLMMeta,
    DailyBriefing,
    FocusSuggestion,
    FocusSuggestionsResponse,
    FollowUpSuggestion,
    FollowUpSuggestionsResponse,
    ProjectSummary,
    WeeklyReview,
)
from core.prompts import (
    PROMPT_VERSION,
    build_daily_briefing_prompt,
    build_focus_suggestions_prompt,
    build_follow_up_suggestions_prompt,
    build_project_summary_prompt,
    build_weekly_review_prompt,
)
from services.assistant.context import AssistantContextService
from services.llm.provider import LLMProviderError, StructuredLLMProvider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class _DailyBriefingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_summary: str
    suggested_focus: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)


class _WeeklyReviewOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_summary: str
    wins: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class _ProjectSummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_summary: str
    priority_items: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class _FocusSuggestionsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_summary: str
    suggestions: list[FocusSuggestion] = Field(default_factory=list)


class _FollowUpSuggestionsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_summary: str
    suggestions: list[FollowUpSuggestion] = Field(default_factory=list)


class AssistantService:
    def __init__(
        self,
        *,
        context_service: AssistantContextService,
        llm_provider: StructuredLLMProvider,
        default_timezone: str,
        llm_max_output_tokens: int,
        llm_note_char_limit: int,
    ) -> None:
        self._context_service = context_service
        self._llm_provider = llm_provider
        self._default_timezone = default_timezone
        self._llm_max_output_tokens = llm_max_output_tokens
        self._llm_note_char_limit = llm_note_char_limit

    def get_daily_briefing(self, *, target_date: date | None = None) -> DailyBriefing:
        context = self._context_service.build_daily_context(target_date=target_date)
        fallback = self._fallback_daily_briefing(context)
        generated, meta = self._generate_optional_output(
            output_model=_DailyBriefingOutput,
            prompt_name="daily_briefing",
            prompt_builder=lambda: build_daily_briefing_prompt(
                context,
                note_char_limit=self._llm_note_char_limit,
            ),
            fallback=fallback,
            context_items=context.context_item_count(),
        )

        summary_lines = [
            (
                f"{len(context.events)} events, {len(context.reminders)} reminders, "
                f"{len(context.due_tasks)} due tasks."
            ),
        ]
        if context.overdue_tasks:
            summary_lines.append(f"{len(context.overdue_tasks)} overdue tasks need attention.")
        if context.events:
            summary_lines.append(f"First event: {context.events[0].title}")
        elif context.reminders:
            summary_lines.append(f"First reminder: {context.reminders[0].title}")
        elif context.due_tasks:
            summary_lines.append(f"Top due task: {context.due_tasks[0].title}")
        else:
            summary_lines.append("No scheduled items for this day yet.")

        return DailyBriefing(
            date=context.date or self._today(),
            timezone=self._default_timezone,
            events=context.events,
            reminders=context.reminders,
            due_tasks=context.due_tasks,
            overdue_tasks=context.overdue_tasks,
            summary_lines=summary_lines,
            generated_summary=generated.generated_summary,
            suggested_focus=generated.suggested_focus,
            follow_ups=generated.follow_ups,
            llm_meta=meta,
        )

    def get_weekly_review(self, *, target_date: date | None = None) -> WeeklyReview:
        context = self._context_service.build_weekly_context(target_date=target_date)
        fallback = self._fallback_weekly_review(context)
        generated, meta = self._generate_optional_output(
            output_model=_WeeklyReviewOutput,
            prompt_name="weekly_review",
            prompt_builder=lambda: build_weekly_review_prompt(
                context,
                note_char_limit=self._llm_note_char_limit,
            ),
            fallback=fallback,
            context_items=context.context_item_count(),
        )

        return WeeklyReview(
            date=context.date or self._today(),
            week_start=context.week_start or self._today(),
            week_end=context.week_end or self._today(),
            timezone=self._default_timezone,
            completed_tasks=context.completed_tasks,
            overdue_tasks=context.overdue_tasks,
            upcoming_tasks=context.due_tasks,
            active_projects=context.active_projects,
            follow_up_people=context.related_people,
            generated_summary=generated.generated_summary,
            wins=generated.wins,
            risks=generated.risks,
            next_actions=generated.next_actions,
            llm_meta=meta,
        )

    def get_project_summary(self, *, project_reference: str) -> ProjectSummary:
        context = self._context_service.build_project_context(project_reference=project_reference)
        fallback = self._fallback_project_summary(context)
        generated, meta = self._generate_optional_output(
            output_model=_ProjectSummaryOutput,
            prompt_name="project_summary",
            prompt_builder=lambda: build_project_summary_prompt(
                context,
                note_char_limit=self._llm_note_char_limit,
            ),
            fallback=fallback,
            context_items=context.context_item_count(),
        )

        if context.project is None:
            raise RuntimeError("Project context should always include a project.")

        return ProjectSummary(
            project=context.project,
            open_tasks=context.open_tasks,
            blocked_tasks=context.blocked_tasks,
            due_tasks=context.due_tasks,
            related_notes=context.related_notes,
            related_people=context.related_people,
            generated_summary=generated.generated_summary,
            priority_items=generated.priority_items,
            next_actions=generated.next_actions,
            llm_meta=meta,
        )

    def get_focus_suggestions(self, *, target_date: date | None = None) -> FocusSuggestionsResponse:
        context = self._context_service.build_focus_context(target_date=target_date)
        fallback = self._fallback_focus_suggestions(context)
        generated, meta = self._generate_optional_output(
            output_model=_FocusSuggestionsOutput,
            prompt_name="focus_suggestions",
            prompt_builder=lambda: build_focus_suggestions_prompt(
                context,
                note_char_limit=self._llm_note_char_limit,
            ),
            fallback=fallback,
            context_items=context.context_item_count(),
        )

        return FocusSuggestionsResponse(
            date=context.date or self._today(),
            timezone=self._default_timezone,
            candidate_tasks=context.open_tasks,
            free_slots=context.free_slots,
            suggestions=generated.suggestions,
            generated_summary=generated.generated_summary,
            llm_meta=meta,
        )

    def get_follow_up_suggestions(self, *, days: int = 14) -> FollowUpSuggestionsResponse:
        context = self._context_service.build_follow_up_context(days=days)
        fallback = self._fallback_follow_up_suggestions(context)
        generated, meta = self._generate_optional_output(
            output_model=_FollowUpSuggestionsOutput,
            prompt_name="follow_up_suggestions",
            prompt_builder=lambda: build_follow_up_suggestions_prompt(
                context,
                note_char_limit=self._llm_note_char_limit,
            ),
            fallback=fallback,
            context_items=context.context_item_count(),
        )

        generated_at_value = context.metadata.get("generated_at")
        generated_at = (
            datetime.fromisoformat(generated_at_value)
            if generated_at_value
            else self._now()
        )
        return FollowUpSuggestionsResponse(
            generated_at=generated_at,
            suggestions=generated.suggestions,
            generated_summary=generated.generated_summary,
            llm_meta=meta,
        )

    def _generate_optional_output(
        self,
        *,
        output_model: type[T],
        prompt_name: str,
        prompt_builder,
        fallback: T,
        context_items: int,
    ) -> tuple[T, AssistantLLMMeta]:
        if context_items == 0:
            return fallback, self._build_meta(
                prompt_name=prompt_name,
                context_items=context_items,
                used_llm=False,
                fallback_used=True,
            )

        try:
            instructions, input_text = prompt_builder()
            response = self._llm_provider.generate_structured_output(
                schema_name=prompt_name,
                instructions=instructions,
                input_text=input_text,
                json_schema=output_model.model_json_schema(),
                max_output_tokens=self._llm_max_output_tokens,
            )
            parsed = output_model.model_validate(response.payload)
        except (LLMProviderError, ValidationError) as exc:
            logger.info("Assistant fallback for %s: %s", prompt_name, exc)
            return fallback, self._build_meta(
                prompt_name=prompt_name,
                context_items=context_items,
                used_llm=False,
                fallback_used=True,
            )

        logger.info(
            (
                "Assistant LLM prompt=%s provider=%s model=%s context_items=%s "
                "input_tokens=%s output_tokens=%s total_tokens=%s"
            ),
            prompt_name,
            response.provider,
            response.model,
            context_items,
            response.input_tokens,
            response.output_tokens,
            response.total_tokens,
        )
        return parsed, self._build_meta(
            prompt_name=prompt_name,
            context_items=context_items,
            used_llm=True,
            fallback_used=False,
            provider=response.provider,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            total_tokens=response.total_tokens,
        )

    def _build_meta(
        self,
        *,
        prompt_name: str,
        context_items: int,
        used_llm: bool,
        fallback_used: bool,
        provider: str | None = None,
        model: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> AssistantLLMMeta:
        resolved_provider = provider or self._llm_provider.provider_name
        resolved_model = model or self._llm_provider.model_name
        return AssistantLLMMeta(
            prompt_version=f"{PROMPT_VERSION}:{prompt_name}",
            provider=resolved_provider,
            model=resolved_model,
            used_llm=used_llm,
            fallback_used=fallback_used,
            context_items=context_items,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    def _fallback_daily_briefing(self, context) -> _DailyBriefingOutput:  # noqa: ANN001
        focus_items = [task.title for task in (context.overdue_tasks + context.due_tasks)[:3]]
        if not focus_items and context.events:
            focus_items = [f"Prepare for {context.events[0].title}"]
        follow_ups = [
            reminder.title for reminder in context.reminders[:2] if reminder.related_entity_ids
        ]
        summary = (
            f"Today has {len(context.events)} events, {len(context.reminders)} reminders, "
            f"and {len(context.due_tasks)} due tasks."
        )
        if context.overdue_tasks:
            summary += f" {len(context.overdue_tasks)} overdue tasks need attention first."
        return _DailyBriefingOutput(
            generated_summary=summary,
            suggested_focus=focus_items,
            follow_ups=follow_ups,
        )

    def _fallback_weekly_review(self, context) -> _WeeklyReviewOutput:  # noqa: ANN001
        wins = [f"Completed: {task.title}" for task in context.completed_tasks[:3]]
        risks = [f"Overdue: {task.title}" for task in context.overdue_tasks[:3]]
        next_actions = [f"Advance: {task.title}" for task in context.due_tasks[:3]]
        summary = (
            f"This week closed {len(context.completed_tasks)} tasks, "
            f"has {len(context.overdue_tasks)} overdue items, "
            f"and {len(context.due_tasks)} active deadlines."
        )
        return _WeeklyReviewOutput(
            generated_summary=summary,
            wins=wins,
            risks=risks,
            next_actions=next_actions,
        )

    def _fallback_project_summary(self, context) -> _ProjectSummaryOutput:  # noqa: ANN001
        project_name = context.project.name if context.project is not None else "This project"
        priority_items = [
            task.title
            for task in (context.blocked_tasks + context.due_tasks + context.open_tasks)[:3]
        ]
        next_actions = [f"Move {task.title} forward" for task in context.open_tasks[:3]]
        summary = (
            f"{project_name} has {len(context.open_tasks)} open tasks, "
            f"{len(context.blocked_tasks)} blocked tasks, and "
            f"{len(context.due_tasks)} tasks with deadlines."
        )
        return _ProjectSummaryOutput(
            generated_summary=summary,
            priority_items=priority_items,
            next_actions=next_actions,
        )

    def _fallback_focus_suggestions(self, context) -> _FocusSuggestionsOutput:  # noqa: ANN001
        suggestions: list[FocusSuggestion] = []
        slot_minutes = context.free_slots[0].duration_minutes if context.free_slots else None
        for task in context.open_tasks[:3]:
            suggestions.append(
                FocusSuggestion(
                    title=task.title,
                    reason=f"{task.priority.value} priority task with active momentum.",
                    related_entity_ids=[task.id],
                    suggested_duration_minutes=(
                        self._parse_effort_minutes(task.estimated_effort) or slot_minutes
                    ),
                )
            )
        summary = (
            f"Recommended {len(suggestions)} focus blocks based on open tasks and "
            f"{len(context.free_slots)} free slots."
        )
        return _FocusSuggestionsOutput(
            generated_summary=summary,
            suggestions=suggestions,
        )

    def _fallback_follow_up_suggestions(self, context) -> _FollowUpSuggestionsOutput:  # noqa: ANN001
        people_reasons = context.metadata.get("people_reasons", {})
        suggestions = [
            FollowUpSuggestion(
                person_id=person.id,
                person_name=person.name,
                reason=people_reasons.get(
                    person.id,
                    "There is pending work connected to this person.",
                ),
                suggested_action=f"Review pending tasks or reminders involving {person.name}.",
                related_entity_ids=[person.id],
            )
            for person in context.related_people[:5]
        ]
        summary = (
            f"Found {len(suggestions)} people with pending follow-up signals."
            if suggestions
            else "No strong follow-up signals were found in the current graph context."
        )
        return _FollowUpSuggestionsOutput(
            generated_summary=summary,
            suggestions=suggestions,
        )

    @staticmethod
    def _parse_effort_minutes(estimated_effort: str | None) -> int | None:
        if estimated_effort is None:
            return None
        normalized = estimated_effort.strip().lower()
        if normalized.endswith("m") and normalized[:-1].isdigit():
            return int(normalized[:-1])
        if normalized.endswith("h") and normalized[:-1].isdigit():
            return int(normalized[:-1]) * 60
        return None

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def _today(self) -> date:
        return self._now().astimezone(ZoneInfo(self._default_timezone)).date()
