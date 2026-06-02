"""Map raw Cowrie JSON log entries to the OpenThreatGrid event schema.

Cowrie emits one JSON object per line to its ``cowrie.json`` log. Each object
has an ``eventid`` (e.g. ``cowrie.login.failed``) plus event-specific fields.
This module translates the subset of events OTG cares about into the normalized
schema documented in ``docs/event-schema.md``.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

# Cowrie eventid -> OTG event_type. Events not in this map are ignored.
EVENTID_MAP: dict[str, str] = {
    "cowrie.session.connect": "connection",
    "cowrie.login.failed": "login_attempt",
    "cowrie.login.success": "login_success",
    "cowrie.command.input": "command_exec",
    "cowrie.command.failed": "command_exec",
    "cowrie.session.file_download": "file_download",
    "cowrie.session.file_upload": "file_download",
    "cowrie.session.closed": "session_close",
}

# Cowrie reports the listening port; map it to a coarse protocol label.
_PORT_PROTOCOL = {2222: "ssh", 22: "ssh", 2223: "telnet", 23: "telnet"}


def _protocol(entry: dict[str, Any]) -> str | None:
    proto = entry.get("protocol")
    if proto:
        return str(proto).lower()
    dst_port = entry.get("dst_port")
    if isinstance(dst_port, int):
        return _PORT_PROTOCOL.get(dst_port)
    return None


def map_cowrie_event(entry: dict[str, Any], sensor_id: str | None = None) -> dict | None:
    """Convert a single Cowrie log object to an OTG event dict.

    Returns ``None`` for Cowrie events that have no OTG mapping so callers can
    cheaply skip them.
    """
    eventid = entry.get("eventid")
    event_type = EVENTID_MAP.get(eventid) if isinstance(eventid, str) else None
    if event_type is None:
        return None

    event: dict[str, Any] = {
        "event_id": str(uuid4()),
        "timestamp": entry.get("timestamp"),
        "sensor_id": sensor_id or entry.get("sensor") or "cowrie-unknown",
        "sensor_type": "cowrie",
        "event_type": event_type,
        "source_ip": entry.get("src_ip"),
        "source_port": entry.get("src_port"),
        "destination_ip": entry.get("dst_ip"),
        "destination_port": entry.get("dst_port"),
        "protocol": _protocol(entry),
        "username": entry.get("username"),
        "password": entry.get("password"),
        "command": entry.get("input"),
        "payload_url": entry.get("url"),
        "payload_hash": entry.get("shasum"),
        "session_id": entry.get("session"),
        "success": event_type == "login_success",
        "tags": [],
        "raw_event": entry,
    }
    return event


def map_cowrie_lines(lines: list[str], sensor_id: str | None = None) -> list[dict]:
    """Map a list of raw JSON log lines, skipping blanks and unmapped events."""
    import json

    events: list[dict] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        mapped = map_cowrie_event(entry, sensor_id=sensor_id)
        if mapped is not None:
            events.append(mapped)
    return events
