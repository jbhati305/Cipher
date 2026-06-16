from core.config import Settings
from services.llm.routing import ModelRoutingPolicy


def test_private_context_forces_ollama(tmp_path):
    policy_path = tmp_path / "routing.yaml"
    policy_path.write_text(
        """
default_provider: ollama
providers:
  ollama:
    models:
      chat: llama3.1:8b
  openrouter:
    enabled_env: OPENROUTER_API_KEY
task_classes:
  research:
    provider_order: [ollama, openrouter]
    allow_api_fallback: true
    share_private_context: false
""",
        encoding="utf-8",
    )
    settings = Settings(CIPHER_MODEL_ROUTING_POLICY_FILE=str(policy_path))

    decision = ModelRoutingPolicy(settings).decide(
        "research",
        private_context=True,
        hard_task=True,
    )

    assert decision.provider == "ollama"
    assert decision.model == "llama3.1:8b"
