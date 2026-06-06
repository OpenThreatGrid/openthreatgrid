"""Storage abstraction for normalized OpenThreatGrid events.

The API is OpenSearch-native (see ``opensearch_store.OpenSearchStore``), but it
talks to storage only through this :class:`EventStore` interface. That keeps the
endpoints backend-agnostic and lets the test suite swap in a fast in-memory
implementation (see ``memory_store.MemoryStore``) instead of standing up a real
cluster.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

# Top-N stats are only meaningful over a known set of keyword fields. Mapping
# the public field name keeps callers from injecting arbitrary aggregation
# targets and documents what the dashboards/reports can ask for.
TOP_FIELDS: dict[str, str] = {
    "source_ip": "source_ip",
    "username": "username",
    "password": "password",
    "command": "command",
    "geo_country": "geo_country",
    "geo_asn": "geo_asn",
}


class EventStore(ABC):
    """Backend-agnostic interface for persisting and querying events."""

    @abstractmethod
    def init(self) -> None:
        """Create indices/templates if missing (idempotent, called at startup)."""

    @abstractmethod
    def ping(self) -> bool:
        """Return True if the backend is reachable (readiness probe)."""

    @abstractmethod
    def bulk_index(self, events: list[dict[str, Any]]) -> list[str]:
        """Index events, skipping any whose ``event_id`` already exists.

        Returns the list of ``event_id`` values that were newly stored. The
        caller guarantees each event dict carries a non-null ``event_id``.
        """

    @abstractmethod
    def get(self, event_id: str) -> dict[str, Any] | None:
        """Return a single event by ``event_id`` or ``None`` if absent."""

    @abstractmethod
    def query(
        self,
        *,
        event_type: str | None = None,
        source_ip: str | None = None,
        sensor_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return matching events, newest first."""

    @abstractmethod
    def summary(self) -> dict[str, Any]:
        """Return aggregate counts powering the dashboard/report summary."""

    @abstractmethod
    def top(self, field: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return the most frequent non-null values of ``field`` as ``{key,count}``."""
