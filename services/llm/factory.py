from core.config import Settings
from services.llm.openai_provider import OpenAIResponsesProvider
from services.llm.provider import LLMNotConfiguredError, StructuredLLMProvider


class DisabledLLMProvider:
    def __init__(self, detail: str) -> None:
        self._detail = detail

    @property
    def provider_name(self) -> str:
        return "disabled"

    @property
    def model_name(self) -> None:
        return None

    def generate_structured_output(self, **kwargs):  # noqa: ANN003, ANN201
        raise LLMNotConfiguredError(self._detail)


def build_llm_provider(settings: Settings) -> StructuredLLMProvider:
    provider = (settings.llm_provider or "").strip().lower()
    if provider == "openai":
        if not settings.openai_api_key:
            return DisabledLLMProvider(
                "OpenAI is not configured. Set OPENAI_API_KEY in .env to enable Phase 3 summaries."
            )
        return OpenAIResponsesProvider(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            base_url=settings.openai_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
            reasoning_effort=settings.llm_reasoning_effort,
            verbosity=settings.llm_verbosity,
        )
    return DisabledLLMProvider(
        f"Unsupported LLM provider '{settings.llm_provider}'. Add a provider implementation first."
    )
