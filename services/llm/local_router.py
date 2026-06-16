import httpx

from core.config import Settings
from services.llm.routing import ModelRoutingPolicy


class LocalFirstLLMRouter:
    def __init__(self, settings: Settings, policy: ModelRoutingPolicy) -> None:
        self._settings = settings
        self._policy = policy

    def health(self) -> dict:
        try:
            response = httpx.get(
                f"{self._settings.ollama_base_url.rstrip('/')}/api/tags",
                timeout=2.0,
            )
            return {"ollama": response.status_code == 200, "status_code": response.status_code}
        except httpx.HTTPError as exc:
            return {"ollama": False, "error": str(exc)}

    def short_reply(self, prompt: str, *, task_class: str = "chat") -> str:
        decision = self._policy.decide(task_class, private_context=True)
        if decision.provider != "ollama":
            return "I can handle that, but this route is configured for a hosted model."
        try:
            response = httpx.post(
                f"{self._settings.ollama_base_url.rstrip('/')}/api/generate",
                json={
                    "model": decision.model or self._settings.llm_model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=self._settings.llm_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return str(data.get("response") or "").strip() or "I processed that locally."
        except httpx.HTTPError:
            return (
                "Cipher is processing this locally. "
                "I may need a moment before I can answer fully."
            )
