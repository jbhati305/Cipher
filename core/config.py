from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cipher"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    default_timezone: str = "Asia/Kolkata"
    reminder_scheduler_poll_seconds: int = 30
    reminder_scheduler_lookahead_minutes: int = 60
    llm_provider: str | None = Field(default="openai", validation_alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-5.4-nano", validation_alias="LLM_MODEL")
    llm_max_output_tokens: int = Field(default=220, validation_alias="LLM_MAX_OUTPUT_TOKENS")
    llm_max_context_items: int = Field(default=12, validation_alias="LLM_MAX_CONTEXT_ITEMS")
    llm_note_char_limit: int = Field(default=180, validation_alias="LLM_NOTE_CHAR_LIMIT")
    llm_timeout_seconds: float = Field(default=20.0, validation_alias="LLM_TIMEOUT_SECONDS")
    llm_reasoning_effort: str = Field(default="none", validation_alias="LLM_REASONING_EFFORT")
    llm_verbosity: str = Field(default="low", validation_alias="LLM_VERBOSITY")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="OPENAI_BASE_URL",
    )
    google_calendar_client_id: str | None = Field(
        default=None,
        validation_alias="GOOGLE_CALENDAR_CLIENT_ID",
    )
    google_calendar_client_secret: str | None = Field(
        default=None,
        validation_alias="GOOGLE_CALENDAR_CLIENT_SECRET",
    )
    google_calendar_token_file: str = Field(
        default=".secrets/google-calendar-token.json",
        validation_alias="GOOGLE_CALENDAR_TOKEN_FILE",
    )
    google_calendar_id: str = Field(
        default="primary",
        validation_alias="GOOGLE_CALENDAR_ID",
    )

    neo4j_uri: str = Field(default="neo4j://localhost:7687", validation_alias="NEO4J_URI")
    neo4j_username: str | None = Field(default=None, validation_alias="NEO4J_USERNAME")
    neo4j_password: str | None = Field(default=None, validation_alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", validation_alias="NEO4J_DATABASE")
    neo4j_verify_connectivity: bool = Field(
        default=True,
        validation_alias="NEO4J_VERIFY_CONNECTIVITY",
    )
    allow_degraded_startup: bool = Field(
        default=True,
        validation_alias="ALLOW_DEGRADED_STARTUP",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="CIPHER_",
    )

    @property
    def neo4j_configured(self) -> bool:
        return bool(self.neo4j_uri and self.neo4j_username and self.neo4j_password)

    @property
    def google_calendar_configured(self) -> bool:
        return bool(self.google_calendar_client_id and self.google_calendar_client_secret)

    @property
    def llm_configured(self) -> bool:
        provider = (self.llm_provider or "").strip().lower()
        if provider == "openai":
            return bool(self.openai_api_key)
        return False


@lru_cache
def get_settings() -> Settings:
    return Settings()
