import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from core.config import Settings


class TaskRoutingRule(BaseModel):
    provider_order: list[str] = Field(default_factory=lambda: ["ollama"])
    allow_api_fallback: bool = False
    share_private_context: bool = False


class ModelRoutingDecision(BaseModel):
    task_class: str
    provider: str
    model: str | None = None
    allow_api_fallback: bool
    share_private_context: bool


class ModelRoutingPolicy:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._raw = self._load_policy(Path(settings.model_routing_policy_file))
        self._task_rules = {
            name: TaskRoutingRule(**value)
            for name, value in self._raw.get("task_classes", {}).items()
            if isinstance(value, dict)
        }

    def decide(
        self,
        task_class: str,
        *,
        private_context: bool = True,
        hard_task: bool = False,
    ) -> ModelRoutingDecision:
        rule = self._task_rules.get(task_class, TaskRoutingRule())
        providers = rule.provider_order or [self._raw.get("default_provider", "ollama")]
        selected = providers[0]
        if hard_task and rule.allow_api_fallback:
            for provider in providers:
                if provider == "ollama" or self._provider_enabled(provider):
                    selected = provider
                    if provider != "ollama":
                        break
        if private_context and not rule.share_private_context:
            selected = "ollama"
        return ModelRoutingDecision(
            task_class=task_class,
            provider=selected,
            model=self._model_for(selected, task_class),
            allow_api_fallback=rule.allow_api_fallback,
            share_private_context=rule.share_private_context,
        )

    def as_dict(self) -> dict[str, Any]:
        return self._raw

    def _provider_enabled(self, provider: str) -> bool:
        providers = self._raw.get("providers", {})
        provider_config = providers.get(provider, {}) if isinstance(providers, dict) else {}
        enabled_env = provider_config.get("enabled_env")
        return bool(enabled_env and os.getenv(enabled_env))

    def _model_for(self, provider: str, task_class: str) -> str | None:
        providers = self._raw.get("providers", {})
        provider_config = providers.get(provider, {}) if isinstance(providers, dict) else {}
        models = provider_config.get("models", {})
        if isinstance(models, dict):
            return models.get(task_class) or models.get("chat")
        if provider == "ollama":
            return self._settings.llm_model
        return None

    @staticmethod
    def _load_policy(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {"default_provider": "ollama", "task_classes": {}}
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"default_provider": "ollama"}
