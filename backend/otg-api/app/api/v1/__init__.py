"""Version 1 of the OpenThreatGrid HTTP API."""

from fastapi import APIRouter

from app.api.v1 import events, stats

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(events.router)
api_router.include_router(stats.router)
