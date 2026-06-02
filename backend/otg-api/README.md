# otg-api

FastAPI ingestion and query API for OpenThreatGrid normalized events.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/events` | Ingest a single event or a batch (JSON object or array) |
| `GET` | `/api/v1/events` | Query events (`event_type`, `source_ip`, `sensor_id`, `since`, `until`, `limit`, `offset`) |
| `GET` | `/api/v1/events/{event_id}` | Fetch a single event |
| `GET` | `/api/v1/stats/summary` | Aggregated counts for dashboard/reports |
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness (DB + Redis connectivity) |

Interactive docs at `/docs` once running.

## Run locally

From the repo root, the whole pipeline comes up with Docker Compose:

```bash
docker compose up --build
# API: http://localhost:8000/docs
```

Or run just the API against a local Postgres/Redis:

```bash
cd backend/otg-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # edit DATABASE_URL / REDIS_URL
uvicorn app.main:app --reload
```

## Tests

```bash
cd backend/otg-api
pip install -r requirements-dev.txt
pytest
```

Tests run against an in-memory SQLite database, so no external services are
required.

## Configuration

See [`.env.example`](.env.example). All settings are read from environment
variables via `app/config.py`.

## Schema / migrations

The portable ORM model lives in `app/models/event.py`. The authoritative
PostgreSQL DDL (using `INET`, `JSONB`, native indexes) is in
`app/db/migrations/0001_init.sql` and is applied by the Postgres init container
in `docker-compose.yml` / the StatefulSet init job in production.
