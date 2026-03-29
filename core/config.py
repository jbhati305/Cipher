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


@lru_cache
def get_settings() -> Settings:
    return Settings()
