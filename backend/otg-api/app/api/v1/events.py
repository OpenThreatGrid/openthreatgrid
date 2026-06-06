"""Event ingestion and query endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import get_settings
from app.schemas.event_schema import EventBatchResult, EventCreate, EventRead
from app.store import get_store
from app.store.base import EventStore

router = APIRouter(tags=["events"])
settings = get_settings()


@router.post("/events", response_model=EventBatchResult, status_code=201)
def ingest_events(
    payload: EventCreate | list[EventCreate],
    store: Annotated[EventStore, Depends(get_store)],
) -> EventBatchResult:
    """Ingest a single event or a batch of events.

    Accepts either a JSON object or a JSON array. Duplicate ``event_id`` values
    are skipped so a worker can safely retry a batch without creating
    duplicates.
    """
    events = payload if isinstance(payload, list) else [payload]
    if not events:
        raise HTTPException(status_code=422, detail="No events provided")
    if len(events) > settings.max_batch_size:
        raise HTTPException(
            status_code=413,
            detail=f"Batch exceeds max size of {settings.max_batch_size}",
        )

    docs = [e.model_dump(mode="json") for e in events]
    accepted_ids = store.bulk_index(docs)
    return EventBatchResult(accepted=len(accepted_ids), event_ids=accepted_ids)


@router.get("/events", response_model=list[EventRead])
def list_events(
    store: Annotated[EventStore, Depends(get_store)],
    event_type: str | None = None,
    source_ip: str | None = None,
    sensor_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    """Query events with optional filters, newest first."""
    return store.query(
        event_type=event_type,
        source_ip=source_ip,
        sensor_id=sensor_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )


@router.get("/events/{event_id}", response_model=EventRead)
def get_event(
    event_id: str,
    store: Annotated[EventStore, Depends(get_store)],
) -> dict:
    """Fetch a single event by its ``event_id``."""
    event = store.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
