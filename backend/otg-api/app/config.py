"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the OTG API.

    Values are read from environment variables (see ``.env.example``). The
    defaults point at the services declared in ``docker-compose.yml`` so the
    stack runs out of the box for local development.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Service identity
    app_name: str = "openthreatgrid-api"
    environment: str = "development"

    # Database
    database_url: str = "postgresql+psycopg://otg:otg@localhost:5432/otg"

    # Redis (used for readiness checks and the ingestion queue)
    redis_url: str = "redis://localhost:6379/0"
    redis_event_queue: str = "otg:events"

    # API behaviour
    max_batch_size: int = 1000
    default_page_size: int = 100
    max_page_size: int = 1000


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
