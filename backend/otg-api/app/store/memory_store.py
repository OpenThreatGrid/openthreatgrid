"""In-memory :class:`EventStore` for tests and offline/demo use.

Keeps the same observable behaviour as :class:`OpenSearchStore` — idempotent
ingestion, newest-first queries, and identical summary/top-N shapes — without
requiring a cluster.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from app.store.base import TOP_FIELDS, EventStore


def _parse_ts(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


class MemoryStore(EventStore):
    def __init__(self) -> None:
        self._events: dict[str, dict[str, Any]] = {}

    def init(self) -> None:  # nothing to provision
        return None

    def ping(self) -> bool:
        return True

    def bulk_index(self, events: list[dict[str, Any]]) -> list[str]:
        now = datetime.now(UTC).isoformat()
        accepted: list[str] = []
        for ev in events:
            eid = ev["event_id"]
            if eid in self._events:
                continue  # duplicate — skip, matches create-op semantics
            self._events[eid] = {**ev, "ingested_at": ev.get("ingested_at") or now}
            accepted.append(eid)
        return accepted

    def get(self, event_id: str) -> dict[str, Any] | None:
        return self._events.get(event_id)

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
        rows = list(self._events.values())
        if event_type:
            rows = [e for e in rows if e.get("event_type") == event_type]
        if source_ip:
            rows = [e for e in rows if e.get("source_ip") == source_ip]
        if sensor_id:
            rows = [e for e in rows if e.get("sensor_id") == sensor_id]
        if since:
            rows = [e for e in rows if _parse_ts(e["timestamp"]) >= since]
        if until:
            rows = [e for e in rows if _parse_ts(e["timestamp"]) <= until]

        rows.sort(key=lambda e: _parse_ts(e["timestamp"]), reverse=True)
        return rows[offset : offset + limit]

    def _counts(self, field: str, limit: int | None = 10) -> list[dict[str, Any]]:
        counter = Counter(
            e[field] for e in self._events.values() if e.get(field) is not None
        )
        return [{"key": str(k), "count": c} for k, c in counter.most_common(limit)]

    def top(self, field: str, limit: int = 10) -> list[dict[str, Any]]:
        if field not in TOP_FIELDS:
            raise ValueError(f"Unsupported top field: {field}")
        return self._counts(field, limit)

    def summary(self) -> dict[str, Any]:
        events = list(self._events.values())
        timestamps = [_parse_ts(e["timestamp"]) for e in events if e.get("timestamp")]
        return {
            "total_events": len(events),
            "unique_source_ips": len({e["source_ip"] for e in events if e.get("source_ip")}),
            "unique_sensors": len({e["sensor_id"] for e in events if e.get("sensor_id")}),
            "events_by_type": self._counts("event_type", limit=None),
            "top_source_ips": self._counts("source_ip"),
            "top_usernames": self._counts("username"),
            "top_passwords": self._counts("password"),
            "first_event": min(timestamps).isoformat() if timestamps else None,
            "last_event": max(timestamps).isoformat() if timestamps else None,
        }
