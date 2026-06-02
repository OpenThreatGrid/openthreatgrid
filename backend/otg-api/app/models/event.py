"""SQLAlchemy model for normalized OpenThreatGrid events."""

from datetime import UTC, datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Event(Base):
    """A single normalized honeypot event.

    Mirrors the OpenThreatGrid Standard Event documented in
    ``docs/event-schema.md``. Column types are kept portable (``JSON`` rather
    than ``JSONB``, ``String`` rather than ``INET``) so the same model runs on
    PostgreSQL in production and SQLite in the test suite. The production
    migration in ``app/db/migrations`` upgrades these to native PG types.
    """

    __tablename__ = "events"

    # Surrogate primary key for ordering/pagination; event_id is the logical id.
    # SQLite only autoincrements INTEGER PRIMARY KEY, so use an Integer variant
    # there while keeping BIGINT (BIGSERIAL) on PostgreSQL.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    event_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    sensor_id: Mapped[str] = mapped_column(String(128), index=True)
    sensor_type: Mapped[str] = mapped_column(String(64), default="cowrie")
    event_type: Mapped[str] = mapped_column(String(64), index=True)

    source_ip: Mapped[str] = mapped_column(String(45), index=True)
    source_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destination_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    destination_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str | None] = mapped_column(String(16), nullable=True)

    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    command: Mapped[str | None] = mapped_column(String, nullable=True)
    payload_url: Mapped[str | None] = mapped_column(String, nullable=True)
    payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    session_id: Mapped[str | None] = mapped_column(String(128), index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)

    geo_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    geo_asn: Mapped[str | None] = mapped_column(String(32), nullable=True)

    tags: Mapped[list] = mapped_column(JSON, default=list)
    raw_event: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        Index("ix_events_type_timestamp", "event_type", "timestamp"),
        Index("ix_events_source_ip_timestamp", "source_ip", "timestamp"),
    )
