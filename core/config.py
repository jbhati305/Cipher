from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cipher"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    default_timezone: str = "Asia/Kolkata"
    cipher_home: str | None = Field(default=None, validation_alias="CIPHER_HOME")
    data_dir: str | None = Field(default=None, validation_alias="CIPHER_DATA_DIR")
    exports_dir: str | None = Field(default=None, validation_alias="CIPHER_EXPORTS_DIR")
    sqlite_path: str | None = Field(default=None, validation_alias="CIPHER_SQLITE_PATH")
    api_host: str = Field(default="127.0.0.1", validation_alias="CIPHER_API_HOST")
    api_port: int = Field(default=8181, validation_alias="CIPHER_API_PORT")
    admin_token: str | None = Field(default=None, validation_alias="CIPHER_ADMIN_TOKEN")
    hermes_token: str | None = Field(default=None, validation_alias="CIPHER_HERMES_TOKEN")
    alexa_token: str | None = Field(default=None, validation_alias="CIPHER_ALEXA_TOKEN")
    auth_required: bool = Field(default=True, validation_alias="CIPHER_AUTH_REQUIRED")
    reminder_scheduler_poll_seconds: int = 30
    reminder_scheduler_lookahead_minutes: int = 60
    llm_provider: str | None = Field(default="nvidia_nim", validation_alias="LLM_PROVIDER")
    llm_model: str = Field(
        default="nvidia/nemotron-3-ultra-550b-a55b",
        validation_alias="LLM_MODEL",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_BASE_URL",
    )
    model_routing_policy_file: str = Field(
        default="config/model-routing.yaml",
        validation_alias="CIPHER_MODEL_ROUTING_POLICY_FILE",
    )
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
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    openrouter_api_key: str | None = Field(default=None, validation_alias="OPENROUTER_API_KEY")
    nvidia_api_key: str | None = Field(default=None, validation_alias="NVIDIA_API_KEY")
    nvidia_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        validation_alias="NVIDIA_BASE_URL",
    )
    memos_base_url: str = Field(default="http://localhost:8000", validation_alias="MEMOS_BASE_URL")
    memos_user_id: str = Field(default="root", validation_alias="MEMOS_USER_ID")
    memos_mem_cube_id: str = Field(default="cipher", validation_alias="MEMOS_MEM_CUBE_ID")
    memos_timeout_seconds: float = Field(default=10.0, validation_alias="MEMOS_TIMEOUT_SECONDS")
    qdrant_url: str = Field(default="http://localhost:6333", validation_alias="QDRANT_URL")
    notion_api_key: str | None = Field(default=None, validation_alias="NOTION_API_KEY")
    notion_papers_database_id: str | None = Field(
        default=None,
        validation_alias="NOTION_PAPERS_DATABASE_ID",
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
    def resolved_cipher_home(self) -> Path:
        if self.cipher_home:
            return Path(self.cipher_home).expanduser()
        if self.environment.lower() in {"prod", "production"}:
            return Path("~/.cipher").expanduser()
        return Path("data")

    @property
    def resolved_data_dir(self) -> Path:
        return Path(self.data_dir).expanduser() if self.data_dir else self.resolved_cipher_home

    @property
    def resolved_exports_dir(self) -> Path:
        if self.exports_dir:
            return Path(self.exports_dir).expanduser()
        return self.resolved_data_dir / "exports"

    @property
    def resolved_sqlite_path(self) -> Path:
        if self.sqlite_path:
            return Path(self.sqlite_path).expanduser()
        return self.resolved_data_dir / "cipher.sqlite3"

    @property
    def google_calendar_configured(self) -> bool:
        return bool(self.google_calendar_client_id and self.google_calendar_client_secret)

    @property
    def llm_configured(self) -> bool:
        provider = (self.llm_provider or "").strip().lower()
        if provider == "ollama":
            return True
        if provider == "openai":
            return bool(self.openai_api_key)
        if provider == "anthropic":
            return bool(self.anthropic_api_key)
        if provider == "gemini":
            return bool(self.gemini_api_key)
        if provider == "openrouter":
            return bool(self.openrouter_api_key)
        if provider == "nvidia_nim":
            return bool(self.nvidia_api_key)
        return False

    @property
    def notion_configured(self) -> bool:
        return bool(self.notion_api_key and self.notion_papers_database_id)


@lru_cache
def get_settings() -> Settings:
    return Settings()
