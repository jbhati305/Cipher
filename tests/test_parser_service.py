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
