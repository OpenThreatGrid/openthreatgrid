"""FastAPI application entrypoint for the OpenThreatGrid API."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.v1 import api_router
from app.config import get_settings
from app.store import get_store

logger = logging.getLogger("otg.api")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure the OpenSearch index template exists before serving traffic."""
    try:
        get_store().init()
    except Exception as exc:  # noqa: BLE001 - don't crash-loop if OS is briefly down
        logger.warning("Store init deferred: %s", exc)
    logger.info("OTG API ready (env=%s)", settings.environment)
    yield


API_DESCRIPTION = """\
Ingestion and query API for **OpenThreatGrid** honeypot threat telemetry.

Sensors (Cowrie first) are parsed and enriched by the worker, then submitted
here as normalized **OTG Standard Events**. Events are validated, stored in
OpenSearch (`otg-events-*`), and exposed for dashboards and the weekly threat
report.

### Pipeline

```
Cowrie → parser → Redis → consumer (enrich + GeoIP/ASN) → THIS API → OpenSearch
```

### Conventions

* **Ingestion is idempotent** — submit the same `event_id` twice and the
  duplicate is skipped (reported as not accepted), so a worker can safely retry
  a batch.
* Timestamps are ISO-8601 (UTC). See the
  [event schema](https://github.com/OpenThreatGrid/openthreatgrid/blob/main/docs/event-schema.md).
* Stats endpoints are backed by OpenSearch aggregations and power the
  dashboards and reports.
"""

OPENAPI_TAGS = [
    {
        "name": "events",
        "description": "Ingest and query normalized honeypot events.",
    },
    {
        "name": "stats",
        "description": "Aggregated counts and top-N breakdowns for dashboards and reports.",
    },
    {
        "name": "meta",
        "description": "Liveness and readiness probes.",
    },
]

app = FastAPI(
    title="OpenThreatGrid API",
    summary="Ingestion and query API for honeypot threat telemetry.",
    description=API_DESCRIPTION,
    version=__version__,
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    contact={
        "name": "OpenThreatGrid",
        "url": "https://github.com/OpenThreatGrid/openthreatgrid",
    },
    license_info={
        "name": "Apache-2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
    servers=[
        {"url": "http://localhost:8000", "description": "Local development"},
        {"url": "https://api.openthreatgrid.io", "description": "Production"},
    ],
)

app.include_router(api_router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe — process is up."""
    return {"status": "ok", "version": __version__}


@app.get("/ready", tags=["meta"])
def ready() -> dict[str, object]:
    """Readiness probe — verifies OpenSearch (and Redis if configured) connectivity."""
    checks: dict[str, str] = {}

    try:
        checks["opensearch"] = "ok" if get_store().ping() else "error: unreachable"
    except Exception as exc:  # noqa: BLE001 - report failure to the probe
        checks["opensearch"] = f"error: {exc.__class__.__name__}"

    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        client.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {exc.__class__.__name__}"

    ready = all(v == "ok" for v in checks.values())
    return {"ready": ready, "checks": checks}
