"""Aggregated statistics endpoints powering the dashboard and reports."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.schemas.stats_schema import Count, StatsSummary
from app.store import get_store
from app.store.base import EventStore

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=StatsSummary)
def stats_summary(store: Annotated[EventStore, Depends(get_store)]) -> StatsSummary:
    """Aggregated counts across all stored events."""
    return StatsSummary(**store.summary())


@router.get("/top-source-ips", response_model=list[Count])
def top_source_ips(
    store: Annotated[EventStore, Depends(get_store)],
    limit: int = Query(default=10, ge=1, le=100),
) -> list[Count]:
    return [Count(**c) for c in store.top("source_ip", limit)]


@router.get("/top-usernames", response_model=list[Count])
def top_usernames(
    store: Annotated[EventStore, Depends(get_store)],
    limit: int = Query(default=10, ge=1, le=100),
) -> list[Count]:
    return [Count(**c) for c in store.top("username", limit)]


@router.get("/top-passwords", response_model=list[Count])
def top_passwords(
    store: Annotated[EventStore, Depends(get_store)],
    limit: int = Query(default=10, ge=1, le=100),
) -> list[Count]:
    return [Count(**c) for c in store.top("password", limit)]


@router.get("/top-commands", response_model=list[Count])
def top_commands(
    store: Annotated[EventStore, Depends(get_store)],
    limit: int = Query(default=10, ge=1, le=100),
) -> list[Count]:
    return [Count(**c) for c in store.top("command", limit)]
