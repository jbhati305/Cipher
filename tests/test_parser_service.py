from services.assistant.parser import AssistantParserService


def test_parse_create_task_command() -> None:
    service = AssistantParserService(default_timezone="Asia/Kolkata")

    result = service.parse("Create a task to set up Neo4j")

    assert result.intent == "create_task"
    assert result.payload["title"] == "set up Neo4j"


def test_parse_create_note_command() -> None:
    service = AssistantParserService(default_timezone="Asia/Kolkata")

    result = service.parse("Add note: Cipher should stay memory-first.")

    assert result.intent == "create_note"
    assert result.payload["content"] == "Cipher should stay memory-first."


def test_parse_reminder_command() -> None:
    service = AssistantParserService(default_timezone="Asia/Kolkata")

    result = service.parse("Remind me tomorrow at 8 PM to call Rahul")

    assert result.intent == "create_reminder"
    assert result.payload["title"] == "call Rahul"
    assert result.payload["trigger_time"] is not None


def test_parse_create_event_command() -> None:
    service = AssistantParserService(default_timezone="Asia/Kolkata")

    result = service.parse("Schedule 2 hours tonight for backend planning")

    assert result.intent == "create_event"
    assert result.payload["title"] == "backend planning"
    assert result.payload["start_time"] is not None
    assert result.payload["end_time"] is not None


def test_parse_agenda_query_command() -> None:
    service = AssistantParserService(default_timezone="Asia/Kolkata")

    result = service.parse("What's on my calendar tomorrow?")

    assert result.intent == "query_agenda"
    assert result.payload["date"] is not None


def test_parse_update_task_status_command() -> None:
    service = AssistantParserService(default_timezone="Asia/Kolkata")

    result = service.parse("Mark Neo4j setup as done")

    assert result.intent == "update_task_status"
    assert result.payload["status"] == "completed"


def test_parse_reschedule_reminder_command() -> None:
    service = AssistantParserService(default_timezone="Asia/Kolkata")

    result = service.parse("Move my reminder to 9 PM")

    assert result.intent == "reschedule_reminder"
    assert result.payload["trigger_time"] is not None
