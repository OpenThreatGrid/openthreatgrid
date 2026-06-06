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

    # OpenSearch — the primary event store. Events land in daily indices under
    # ``otg-events-*``. Local dev runs the cluster with the security plugin
    # disabled, so no auth/TLS is required out of the box.
    opensearch_url: str = "http://localhost:9200"
    opensearch_index_prefix: str = "otg-events"
    opensearch_username: str | None = None
    opensearch_password: str | None = None
    opensearch_verify_certs: bool = False

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
