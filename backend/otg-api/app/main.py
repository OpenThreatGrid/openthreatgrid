"""FastAPI application entrypoint for the OpenThreatGrid API."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app import __version__
from app.api.v1 import api_router
from app.config import get_settings
from app.db.session import engine, init_db

logger = logging.getLogger("otg.api")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure the schema exists before serving traffic (dev/local convenience)."""
    init_db()
    logger.info("OTG API ready (env=%s)", settings.environment)
    yield


app = FastAPI(
    title="OpenThreatGrid API",
    description="Ingestion and query API for honeypot threat telemetry.",
    version=__version__,
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe — process is up."""
    return {"status": "ok", "version": __version__}


@app.get("/ready", tags=["meta"])
def ready() -> dict[str, object]:
    """Readiness probe — verifies database (and Redis if configured) connectivity."""
    checks: dict[str, str] = {}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001 - report failure to the probe
        checks["database"] = f"error: {exc.__class__.__name__}"

    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        client.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {exc.__class__.__name__}"

    ready = all(v == "ok" for v in checks.values())
    return {"ready": ready, "checks": checks}
