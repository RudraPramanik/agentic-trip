from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process settings. Required fields fail fast; optional vendor keys stay unset."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    database_url: str
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    llm_api_key: str | None = None
    cors_allowed_origins: str = "http://localhost:3000"
    environment: str = "local"

    @property
    def cookie_secure(self) -> bool:
        return self.environment != "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
