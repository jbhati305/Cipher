import json

import httpx
import pytest

from services.llm.openai_provider import OpenAIResponsesProvider
from services.llm.provider import LLMNotConfiguredError


def test_openai_provider_parses_structured_response_and_usage() -> None:
    captured_request: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["url"] = str(request.url)
        captured_request["json"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "id": "resp_123",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": (
                                    '{"generated_summary":"Keep prompts short.",'
                                    '"priority_items":["Limit context"],'
                                    '"next_actions":["Add tests"]}'
                                ),
                            }
                        ],
                    }
                ],
                "usage": {
                    "input_tokens": 31,
                    "output_tokens": 14,
                    "total_tokens": 45,
                },
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAIResponsesProvider(
        api_key="test-key",
        model="gpt-5.4-nano",
        base_url="https://api.openai.com/v1",
        timeout_seconds=10,
        reasoning_effort="none",
        verbosity="low",
        http_client=client,
    )

    response = provider.generate_structured_output(
        schema_name="project_summary",
        instructions="Return a project summary.",
        input_text="Project context goes here.",
        json_schema={
            "type": "object",
            "properties": {
                "generated_summary": {"type": "string"},
                "priority_items": {"type": "array", "items": {"type": "string"}},
                "next_actions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["generated_summary", "priority_items", "next_actions"],
            "additionalProperties": False,
        },
        max_output_tokens=150,
    )

    assert captured_request["url"] == "https://api.openai.com/v1/responses"
    assert captured_request["json"]["model"] == "gpt-5.4-nano"
    assert captured_request["json"]["store"] is False
    assert captured_request["json"]["text"]["format"]["type"] == "json_schema"
    assert captured_request["json"]["reasoning"]["effort"] == "none"
    assert response.payload["generated_summary"] == "Keep prompts short."
    assert response.input_tokens == 31
    assert response.output_tokens == 14
    assert response.total_tokens == 45


def test_openai_provider_requires_api_key() -> None:
    provider = OpenAIResponsesProvider(
        api_key=None,
        model="gpt-5.4-nano",
        base_url="https://api.openai.com/v1",
        timeout_seconds=10,
        reasoning_effort="none",
        verbosity="low",
    )

    with pytest.raises(LLMNotConfiguredError):
        provider.generate_structured_output(
            schema_name="daily_briefing",
            instructions="Return a briefing.",
            input_text="Context",
            json_schema={"type": "object", "properties": {}, "additionalProperties": False},
            max_output_tokens=100,
        )
