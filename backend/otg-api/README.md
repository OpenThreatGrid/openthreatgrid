# otg-api

FastAPI ingestion and query API for OpenThreatGrid normalized events.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/events` | Ingest a single event or a batch (JSON object or array) |
| `GET` | `/api/v1/events` | Query events (`event_type`, `source_ip`, `sensor_id`, `since`, `until`, `limit`, `offset`) |
| `GET` | `/api/v1/events/{event_id}` | Fetch a single event |
| `GET` | `/api/v1/stats/summary` | Aggregated counts for dashboard/reports |
| `GET` | `/api/v1/stats/top-source-ips` | Top source IPs (`limit`) |
| `GET` | `/api/v1/stats/top-usernames` | Top usernames (`limit`) |
| `GET` | `/api/v1/stats/top-passwords` | Top passwords (`limit`) |
| `GET` | `/api/v1/stats/top-commands` | Top commands (`limit`) |
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness (OpenSearch + Redis connectivity) |

## OpenAPI / interactive docs

The API is described by an OpenAPI 3.1 schema, served live once running:

| URL | Tool |
|---|---|
| `/docs` | Swagger UI (try-it-out) |
| `/redoc` | Redoc |
| `/openapi.json` | Raw OpenAPI schema |

A committed copy of the schema lives at [`docs/openapi.json`](../../docs/openapi.json)
(and `docs/openapi.yaml`) and is rendered on the docs site under **API Reference**.
Regenerate it after changing endpoints or models:

```bash
cd backend/otg-api && pip install -r requirements.txt
python ../../scripts/export_openapi.py
```

## Run locally

From the repo root, the whole pipeline comes up with Docker Compose:

```bash
docker compose up --build
# API: http://localhost:8000/docs
```

Or run just the API against a local OpenSearch/Redis:

```bash
cd backend/otg-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # edit OPENSEARCH_URL / REDIS_URL
uvicorn app.main:app --reload
```

## Tests

```bash
cd backend/otg-api
pip install -r requirements-dev.txt
pytest
```

Tests run against an in-memory event store (`app/store/memory_store.py`), so no
OpenSearch cluster is required.

## Configuration

See [`.env.example`](.env.example). All settings are read from environment
variables via `app/config.py`.

## Storage

The API talks to storage only through the `EventStore` interface
(`app/store/base.py`). The production backend is `OpenSearchStore`
(`app/store/opensearch_store.py`), which writes to daily `otg-events-*` indices
and computes summary/top-N stats with OpenSearch aggregations. The index
template is created on startup; its canonical copy is
`opensearch/index-templates/otg-events.json`. `MemoryStore` provides the same
behaviour in-process for tests.
