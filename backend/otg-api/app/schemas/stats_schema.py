"""Pydantic schemas for aggregated statistics responses."""

from pydantic import BaseModel


class Count(BaseModel):
    """A single labelled count, used for top-N breakdowns."""

    key: str | None
    count: int


class StatsSummary(BaseModel):
    """Aggregated view of stored events, powering the dashboard and reports."""

    total_events: int
    unique_source_ips: int
    unique_sensors: int
    events_by_type: list[Count]
    top_source_ips: list[Count]
    top_usernames: list[Count]
    top_passwords: list[Count]
    first_event: str | None = None
    last_event: str | None = None
