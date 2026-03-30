from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class LLMStructuredResponse:
    payload: dict[str, Any]
    provider: str
    model: str | None
    response_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class LLMProviderError(RuntimeError):
    """Raised when an LLM request cannot be completed successfully."""


class LLMNotConfiguredError(LLMProviderError):
    """Raised when a provider is requested but not configured."""


class StructuredLLMProvider(Protocol):
    @property
    def provider_name(self) -> str: ...

    @property
    def model_name(self) -> str | None: ...

    def generate_structured_output(
        self,
        *,
        schema_name: str,
        instructions: str,
        input_text: str,
        json_schema: dict[str, Any],
        max_output_tokens: int,
    ) -> LLMStructuredResponse: ...
