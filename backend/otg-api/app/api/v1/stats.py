"""Aggregated statistics endpoints powering the dashboard and reports."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.schemas.stats_schema import Count, StatsSummary

router = APIRouter(prefix="/stats", tags=["stats"])


def _top(db: Session, column, limit: int = 10) -> list[Count]:
    """Return the top ``limit`` non-null values of ``column`` by frequency."""
    rows = db.execute(
        select(column, func.count().label("c"))
        .where(column.isnot(None))
        .group_by(column)
        .order_by(func.count().desc())
        .limit(limit)
    ).all()
    return [Count(key=str(value), count=count) for value, count in rows]


@router.get("/summary", response_model=StatsSummary)
def stats_summary(db: Annotated[Session, Depends(get_db)]) -> StatsSummary:
    """Aggregated counts across all stored events."""
    total = db.scalar(select(func.count()).select_from(Event)) or 0
    unique_ips = db.scalar(select(func.count(func.distinct(Event.source_ip)))) or 0
    unique_sensors = db.scalar(select(func.count(func.distinct(Event.sensor_id)))) or 0

    by_type_rows = db.execute(
        select(Event.event_type, func.count())
        .group_by(Event.event_type)
        .order_by(func.count().desc())
    ).all()
    events_by_type = [Count(key=t, count=c) for t, c in by_type_rows]

    first_event = db.scalar(select(func.min(Event.timestamp)))
    last_event = db.scalar(select(func.max(Event.timestamp)))

    return StatsSummary(
        total_events=total,
        unique_source_ips=unique_ips,
        unique_sensors=unique_sensors,
        events_by_type=events_by_type,
        top_source_ips=_top(db, Event.source_ip),
        top_usernames=_top(db, Event.username),
        top_passwords=_top(db, Event.password),
        first_event=first_event.isoformat() if first_event else None,
        last_event=last_event.isoformat() if last_event else None,
    )
