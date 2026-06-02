"""Event ingestion and query endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.models.event import Event
from app.schemas.event_schema import EventBatchResult, EventCreate, EventRead

router = APIRouter(tags=["events"])
settings = get_settings()


@router.post("/events", response_model=EventBatchResult, status_code=201)
def ingest_events(
    payload: EventCreate | list[EventCreate],
    db: Annotated[Session, Depends(get_db)],
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

    incoming_ids = [e.event_id for e in events]
    existing = set(
        db.scalars(
            select(Event.event_id).where(Event.event_id.in_(incoming_ids))
        ).all()
    )

    accepted_ids: list[str] = []
    for event in events:
        if event.event_id in existing:
            continue
        db.add(Event(**event.model_dump()))
        existing.add(event.event_id)
        accepted_ids.append(event.event_id)

    db.commit()
    return EventBatchResult(accepted=len(accepted_ids), event_ids=accepted_ids)


@router.get("/events", response_model=list[EventRead])
def list_events(
    db: Annotated[Session, Depends(get_db)],
    event_type: str | None = None,
    source_ip: str | None = None,
    sensor_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(default=0, ge=0),
) -> list[Event]:
    """Query events with optional filters, newest first."""
    stmt = select(Event)
    if event_type:
        stmt = stmt.where(Event.event_type == event_type)
    if source_ip:
        stmt = stmt.where(Event.source_ip == source_ip)
    if sensor_id:
        stmt = stmt.where(Event.sensor_id == sensor_id)
    if since:
        stmt = stmt.where(Event.timestamp >= since)
    if until:
        stmt = stmt.where(Event.timestamp <= until)

    stmt = stmt.order_by(Event.timestamp.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


@router.get("/events/{event_id}", response_model=EventRead)
def get_event(
    event_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Event:
    """Fetch a single event by its ``event_id``."""
    event = db.scalar(select(Event).where(Event.event_id == event_id))
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
