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
    llm_model: str = "nvidia_nim/nvidia/nemotron-3-nano-30b-a3b"
    llm_api_base: str | None = None
    llm_model_fallbacks: str | None = None
    gemini_api_key: str | None = None
    embedding_model: str = "gemini/gemini-embedding-2"
    cors_allowed_origins: str = "http://localhost:3000"
    environment: str = "local"
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    nominatim_user_agent: str = "agentic-trip/0.1 (local; contact: dev@localhost)"
    nominatim_timeout_seconds: float = 5.0
    dialogue_prefer_postgres_checkpointer: bool = False
    apply_schema_on_boot: bool = False
    redis_url: str = "redis://localhost:6379"
    overpass_base_url: str = "https://overpass-api.de/api/interpreter"
    overpass_timeout_seconds: float = 20.0
    otm_base_url: str = "https://api.opentripmap.com/0.1/en/places/bbox"
    otm_api_key: str | None = None
    otm_timeout_seconds: float = 15.0
    places_user_agent: str = "agentic-trip/0.1 (local; contact: dev@localhost)"
    acquire_max_tries: int = 3
    catalog_enqueue_inline: bool = False
    generate_timeout_seconds: float = 120.0
    revise_max_loops: int = 3
    revise_timeout_seconds: float = 120.0

    @property
    def cookie_secure(self) -> bool:
        return self.environment != "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
