"""Pydantic v2 schemas for event ingestion and querying."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventType(str, Enum):
    """Supported OpenThreatGrid event types (see docs/event-schema.md)."""

    login_attempt = "login_attempt"
    login_success = "login_success"
    command_exec = "command_exec"
    file_download = "file_download"
    session_start = "session_start"
    session_close = "session_close"
    connection = "connection"


class EventBase(BaseModel):
    """Fields shared between ingestion input and query output."""

    timestamp: datetime
    sensor_id: str = Field(..., max_length=128)
    sensor_type: str = Field(default="cowrie", max_length=64)
    event_type: EventType

    source_ip: str = Field(..., max_length=45)
    source_port: int | None = Field(default=None, ge=0, le=65535)
    destination_ip: str | None = Field(default=None, max_length=45)
    destination_port: int | None = Field(default=None, ge=0, le=65535)
    protocol: str | None = Field(default=None, max_length=16)

    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=255)
    command: str | None = None
    payload_url: str | None = None
    payload_hash: str | None = Field(default=None, max_length=128)

    session_id: str | None = Field(default=None, max_length=128)
    success: bool = False

    geo_country: str | None = Field(default=None, max_length=2)
    geo_asn: str | None = Field(default=None, max_length=32)

    tags: list[str] = Field(default_factory=list)
    raw_event: dict[str, Any] = Field(default_factory=dict)


class EventCreate(EventBase):
    """Schema for ingesting an event.

    ``event_id`` is optional on input — if the producer (worker) does not set
    one, the API generates a UUIDv4 so events are idempotently identifiable.
    """

    event_id: str | None = Field(default=None, max_length=36, validate_default=True)

    @field_validator("event_id")
    @classmethod
    def default_event_id(cls, v: str | None) -> str:
        return v or str(uuid4())


class EventRead(EventBase):
    """Schema returned when querying events."""

    model_config = ConfigDict(from_attributes=True)

    event_id: str
    ingested_at: datetime | None = None


class EventBatchResult(BaseModel):
    """Response for a (possibly batched) ingestion request."""

    accepted: int
    event_ids: list[str]
