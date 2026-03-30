from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from apps.api.dependencies import get_assistant_service
from apps.api.main import create_app
from core.models.assistant import (
    AssistantContextBundle,
    FocusSuggestion,
    FocusSuggestionsResponse,
    FollowUpSuggestion,
    FollowUpSuggestionsResponse,
    ProjectSummary,
    WeeklyReview,
)
from core.models.entities import (
    EventRead,
    FreeSlotRead,
    NoteRead,
    PersonRead,
    ProjectRead,
    ProjectStatus,
    ReminderChannel,
    ReminderRead,
    ReminderStatus,
    TaskPriority,
    TaskRead,
    TaskStatus,
)
from services.assistant.service import AssistantService
from services.llm.provider import LLMProviderError, LLMStructuredResponse


def _project_fixture() -> ProjectRead:
    now = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    return ProjectRead(
        id="project-1",
        code="PRJ-2604-000001",
        created_at=now,
        updated_at=now,
        name="Cipher",
        description="Memory-first assistant backend",
        status=ProjectStatus.ACTIVE,
        priority=TaskPriority.HIGH,
    )


def _task_fixture(
    *,
    task_id: str = "task-1",
    title: str = "Review retrieval layer",
    status: TaskStatus = TaskStatus.PENDING,
) -> TaskRead:
    now = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    return TaskRead(
        id=task_id,
        code=f"TSK-2604-00000{task_id[-1]}",
        created_at=now,
        updated_at=now,
        title=title,
        description=None,
        status=status,
        priority=TaskPriority.HIGH,
        deadline=now.replace(hour=18),
        estimated_effort="60m",
        project_id="project-1",
        related_entity_ids=["person-1"],
    )


def _reminder_fixture() -> ReminderRead:
    now = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    return ReminderRead(
        id="reminder-1",
        code="REM-2604-000001",
        created_at=now,
        updated_at=now,
        title="Call Rahul",
        trigger_time=now,
        recurrence_rule=None,
        status=ReminderStatus.SCHEDULED,
        channel=ReminderChannel.IN_APP,
        last_triggered_at=None,
        trigger_count=0,
        related_entity_ids=["person-1"],
    )


def _person_fixture() -> PersonRead:
    now = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    return PersonRead(
        id="person-1",
        code="PER-2604-000001",
        created_at=now,
        updated_at=now,
        name="Rahul",
        relationship_type="friend",
        notes="Waiting on a document update.",
    )


def _daily_context() -> AssistantContextBundle:
    now = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    return AssistantContextBundle(
        intent="daily_briefing",
        date=date(2026, 4, 1),
        events=[
            EventRead(
                id="event-1",
                code="event-1",
                created_at=now,
                updated_at=now,
                title="Planning block",
                start_time=now,
                end_time=now.replace(hour=10),
                location=None,
                description=None,
                related_entity_ids=[],
            )
        ],
        reminders=[_reminder_fixture()],
        due_tasks=[_task_fixture()],
        overdue_tasks=[_task_fixture(task_id="task-2", title="Fix flaky tests")],
    )


def _project_context() -> AssistantContextBundle:
    return AssistantContextBundle(
        intent="project_summary",
        project=_project_fixture(),
        open_tasks=[_task_fixture()],
        blocked_tasks=[
            _task_fixture(
                task_id="task-3",
                title="Decide vendor interface",
                status=TaskStatus.BLOCKED,
            )
        ],
        due_tasks=[_task_fixture()],
        related_notes=[
            NoteRead(
                id="note-1",
                code="NOT-2604-000001",
                created_at=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
                updated_at=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
                title="LLM direction",
                content="Keep prompts short and provider-agnostic.",
                source="chat",
                related_entity_ids=[],
            )
        ],
        related_people=[_person_fixture()],
    )


class FakeContextService:
    def build_daily_context(self, *, target_date=None):  # noqa: ANN001, ANN201
        return _daily_context()

    def build_weekly_context(self, *, target_date=None):  # noqa: ANN001, ANN201
        return AssistantContextBundle(
            intent="weekly_review",
            date=date(2026, 4, 1),
            week_start=date(2026, 3, 30),
            week_end=date(2026, 4, 5),
            completed_tasks=[
                _task_fixture(
                    task_id="task-4",
                    title="Land parser updates",
                    status=TaskStatus.COMPLETED,
                )
            ],
            overdue_tasks=[_task_fixture(task_id="task-5", title="Fix auth flow")],
            due_tasks=[_task_fixture()],
            active_projects=[_project_fixture()],
            related_people=[_person_fixture()],
        )

    def build_project_context(self, *, project_reference):  # noqa: ANN001, ANN201
        return _project_context()

    def build_focus_context(self, *, target_date=None):  # noqa: ANN001, ANN201
        bundle = _daily_context()
        return bundle.model_copy(
            update={
                "intent": "focus_suggestions",
                "open_tasks": [_task_fixture(), _task_fixture(task_id="task-6", title="Add docs")],
                "free_slots": [
                    FreeSlotRead(
                        start_time=datetime(2026, 4, 1, 14, 0, tzinfo=UTC),
                        end_time=datetime(2026, 4, 1, 16, 0, tzinfo=UTC),
                        duration_minutes=120,
                    )
                ],
            }
        )

    def build_follow_up_context(self, *, days=14):  # noqa: ANN001, ANN201
        return AssistantContextBundle(
            intent="follow_up_suggestions",
            related_people=[_person_fixture()],
            open_tasks=[_task_fixture()],
            reminders=[_reminder_fixture()],
            metadata={
                "generated_at": "2026-04-01T10:00:00+00:00",
                "people_reasons": {
                    "person-1": "Reminder 'Call Rahul' is scheduled for 2026-04-01.",
                },
            },
        )


class FailingLLMProvider:
    provider_name = "disabled"
    model_name = None

    def generate_structured_output(self, **kwargs):  # noqa: ANN003, ANN201
        raise LLMProviderError("LLM disabled for test")


class StaticLLMProvider:
    provider_name = "openai"
    model_name = "gpt-5.4-nano"

    def __init__(self) -> None:
        self.last_schema_name: str | None = None

    def generate_structured_output(self, **kwargs):  # noqa: ANN003, ANN201
        self.last_schema_name = kwargs["schema_name"]
        payloads = {
            "project_summary": {
                "generated_summary": (
                    "Cipher is active, but the provider interface "
                    "is the main blocker."
                ),
                "priority_items": ["Resolve the vendor abstraction"],
                "next_actions": ["Finish the OpenAI adapter tests"],
            },
        }
        return LLMStructuredResponse(
            payload=payloads[kwargs["schema_name"]],
            provider=self.provider_name,
            model=self.model_name,
            input_tokens=42,
            output_tokens=18,
            total_tokens=60,
        )


class FakeAssistantRouteService:
    def __init__(self) -> None:
        self.project_reference: str | None = None

    def get_weekly_review(self, *, target_date=None) -> WeeklyReview:  # noqa: ANN001
        return WeeklyReview(
            date=target_date or date(2026, 4, 1),
            week_start=date(2026, 3, 30),
            week_end=date(2026, 4, 5),
            timezone="Asia/Kolkata",
            completed_tasks=[],
            overdue_tasks=[],
            upcoming_tasks=[],
            active_projects=[],
            follow_up_people=[],
            generated_summary="Solid progress this week.",
            wins=["Shipped Phase 3 scaffolding"],
            risks=[],
            next_actions=["Add end-to-end tests"],
        )

    def get_project_summary(self, *, project_reference: str) -> ProjectSummary:
        self.project_reference = project_reference
        return ProjectSummary(
            project=_project_fixture(),
            open_tasks=[],
            blocked_tasks=[],
            due_tasks=[],
            related_notes=[],
            related_people=[],
            generated_summary="Cipher is moving well.",
            priority_items=["Polish assistant prompts"],
            next_actions=["Run integrated testing"],
        )

    def get_focus_suggestions(self, *, target_date=None) -> FocusSuggestionsResponse:  # noqa: ANN001
        return FocusSuggestionsResponse(
            date=target_date or date(2026, 4, 1),
            timezone="Asia/Kolkata",
            candidate_tasks=[],
            free_slots=[],
            suggestions=[
                FocusSuggestion(
                    title="Review retrieval layer",
                    reason="High-priority work with clear next steps.",
                    related_entity_ids=["task-1"],
                    suggested_duration_minutes=60,
                )
            ],
            generated_summary="One strong focus block is enough for today.",
        )

    def get_follow_up_suggestions(self, *, days: int = 14) -> FollowUpSuggestionsResponse:
        return FollowUpSuggestionsResponse(
            generated_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            suggestions=[
                FollowUpSuggestion(
                    person_id="person-1",
                    person_name="Rahul",
                    reason="A reminder is due today.",
                    suggested_action="Send Rahul the pending follow-up.",
                    related_entity_ids=["person-1"],
                )
            ],
            generated_summary=f"Checked the next {days} days for follow-ups.",
        )


def test_assistant_service_falls_back_to_deterministic_daily_briefing() -> None:
    service = AssistantService(
        context_service=FakeContextService(),
        llm_provider=FailingLLMProvider(),
        default_timezone="Asia/Kolkata",
        llm_max_output_tokens=180,
        llm_note_char_limit=160,
    )

    result = service.get_daily_briefing(target_date=date(2026, 4, 1))

    assert result.generated_summary == (
        "Today has 1 events, 1 reminders, and 1 due tasks. "
        "1 overdue tasks need attention first."
    )
    assert result.suggested_focus == ["Fix flaky tests", "Review retrieval layer"]
    assert result.llm_meta is not None
    assert result.llm_meta.used_llm is False
    assert result.llm_meta.fallback_used is True


def test_assistant_service_uses_llm_for_project_summary() -> None:
    llm_provider = StaticLLMProvider()
    service = AssistantService(
        context_service=FakeContextService(),
        llm_provider=llm_provider,
        default_timezone="Asia/Kolkata",
        llm_max_output_tokens=180,
        llm_note_char_limit=160,
    )

    result = service.get_project_summary(project_reference="Cipher")

    assert llm_provider.last_schema_name == "project_summary"
    assert result.generated_summary == (
        "Cipher is active, but the provider interface is the main blocker."
    )
    assert result.priority_items == ["Resolve the vendor abstraction"]
    assert result.llm_meta is not None
    assert result.llm_meta.used_llm is True
    assert result.llm_meta.total_tokens == 60


def test_weekly_review_route_uses_phase3_service() -> None:
    app = create_app()
    route_service = FakeAssistantRouteService()
    app.dependency_overrides[get_assistant_service] = lambda: route_service

    with TestClient(app) as client:
        response = client.get("/assistant/weekly-review?date=2026-04-01")

    assert response.status_code == 200
    payload = response.json()
    assert payload["generated_summary"] == "Solid progress this week."
    assert payload["wins"] == ["Shipped Phase 3 scaffolding"]


def test_project_summary_route_passes_project_reference() -> None:
    app = create_app()
    route_service = FakeAssistantRouteService()
    app.dependency_overrides[get_assistant_service] = lambda: route_service

    with TestClient(app) as client:
        response = client.get("/assistant/project-summary?project=PRJ-2604-000001")

    assert response.status_code == 200
    assert route_service.project_reference == "PRJ-2604-000001"
    assert response.json()["priority_items"] == ["Polish assistant prompts"]


def test_focus_and_follow_up_routes_return_phase3_payloads() -> None:
    app = create_app()
    route_service = FakeAssistantRouteService()
    app.dependency_overrides[get_assistant_service] = lambda: route_service

    with TestClient(app) as client:
        focus_response = client.get("/assistant/focus-suggestions?date=2026-04-01")
        follow_up_response = client.get("/assistant/follow-up-suggestions?days=7")

    assert focus_response.status_code == 200
    assert follow_up_response.status_code == 200
    assert focus_response.json()["suggestions"][0]["title"] == "Review retrieval layer"
    assert (
        follow_up_response.json()["generated_summary"]
        == "Checked the next 7 days for follow-ups."
    )
