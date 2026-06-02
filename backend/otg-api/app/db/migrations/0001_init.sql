-- OpenThreatGrid — initial schema (PostgreSQL 16)
-- Source of truth for production. The ORM's create_all() mirrors this for
-- local/dev and tests using portable column types.

CREATE TABLE IF NOT EXISTS events (
    id               BIGSERIAL PRIMARY KEY,
    event_id         UUID        NOT NULL UNIQUE,
    timestamp        TIMESTAMPTZ NOT NULL,
    ingested_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    sensor_id        TEXT        NOT NULL,
    sensor_type      TEXT        NOT NULL DEFAULT 'cowrie',
    event_type       TEXT        NOT NULL,

    source_ip        INET        NOT NULL,
    source_port      INTEGER,
    destination_ip   INET,
    destination_port INTEGER,
    protocol         TEXT,

    username         TEXT,
    password         TEXT,
    command          TEXT,
    payload_url      TEXT,
    payload_hash     TEXT,

    session_id       TEXT,
    success          BOOLEAN     NOT NULL DEFAULT FALSE,

    geo_country      CHAR(2),
    geo_asn          TEXT,

    tags             JSONB       NOT NULL DEFAULT '[]'::jsonb,
    raw_event        JSONB       NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_events_timestamp           ON events (timestamp);
CREATE INDEX IF NOT EXISTS ix_events_event_type          ON events (event_type);
CREATE INDEX IF NOT EXISTS ix_events_source_ip           ON events (source_ip);
CREATE INDEX IF NOT EXISTS ix_events_sensor_id           ON events (sensor_id);
CREATE INDEX IF NOT EXISTS ix_events_session_id          ON events (session_id);
CREATE INDEX IF NOT EXISTS ix_events_type_timestamp      ON events (event_type, timestamp);
CREATE INDEX IF NOT EXISTS ix_events_source_ip_timestamp ON events (source_ip, timestamp);
