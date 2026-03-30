import json
from typing import Any

import httpx

from services.llm.provider import LLMNotConfiguredError, LLMProviderError, LLMStructuredResponse


class OpenAIResponsesProvider:
    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        base_url: str,
        timeout_seconds: float,
        reasoning_effort: str,
        verbosity: str,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._reasoning_effort = reasoning_effort
        self._verbosity = verbosity
        self._http_client = http_client

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    def generate_structured_output(
        self,
        *,
        schema_name: str,
        instructions: str,
        input_text: str,
        json_schema: dict[str, Any],
        max_output_tokens: int,
    ) -> LLMStructuredResponse:
        if not self._api_key:
            raise LLMNotConfiguredError("OpenAI is not configured. Set OPENAI_API_KEY in .env.")

        body: dict[str, Any] = {
            "model": self._model,
            "instructions": instructions,
            "input": input_text,
            "store": False,
            "temperature": 0,
            "max_output_tokens": max_output_tokens,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": json_schema,
                    "strict": True,
                },
                "verbosity": self._verbosity,
            },
        }
        if self._reasoning_effort:
            body["reasoning"] = {"effort": self._reasoning_effort}

        response = self._post(body)
        usage = response.get("usage", {})
        output_text = response.get("output_text") or self._extract_output_text(
            response.get("output")
        )
        if not output_text:
            raise LLMProviderError("OpenAI did not return any text output.")

        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(
                "OpenAI returned invalid JSON for a structured response."
            ) from exc

        return LLMStructuredResponse(
            payload=payload,
            provider=self.provider_name,
            model=self.model_name,
            response_id=response.get("id"),
            input_tokens=self._coerce_int(usage.get("input_tokens")),
            output_tokens=self._coerce_int(usage.get("output_tokens")),
            total_tokens=self._coerce_int(usage.get("total_tokens")),
        )

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self._base_url}/responses"

        try:
            if self._http_client is not None:
                response = self._http_client.post(url, headers=headers, json=body)
            else:
                response = httpx.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=self._timeout_seconds,
                )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = self._extract_error_detail(exc.response)
            raise LLMProviderError(f"OpenAI request failed: {detail}") from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"OpenAI request failed: {exc}") from exc

        try:
            return response.json()
        except ValueError as exc:
            raise LLMProviderError("OpenAI returned a non-JSON response.") from exc

    @staticmethod
    def _extract_output_text(output: Any) -> str | None:
        if not isinstance(output, list):
            return None

        chunks: list[str] = []
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content_item in item.get("content", []):
                if content_item.get("type") == "output_text" and content_item.get("text"):
                    chunks.append(content_item["text"])
        if not chunks:
            return None
        return "\n".join(chunks)

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text
        error = payload.get("error", {})
        message = error.get("message")
        if message:
            return str(message)
        return response.text

    @staticmethod
    def _coerce_int(value: Any) -> int | None:
        if isinstance(value, int):
            return value
        return None
