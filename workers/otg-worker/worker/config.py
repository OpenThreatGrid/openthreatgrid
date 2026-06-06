"""Worker configuration from environment variables."""

import os


class Config:
    # Redis queue shared with the parser.
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    EVENT_QUEUE = os.getenv("REDIS_EVENT_QUEUE", "otg:events")

    # API the consumer submits enriched events to.
    API_BASE_URL = os.getenv("OTG_API_URL", "http://localhost:8000")

    # Cowrie JSON log the parser tails.
    COWRIE_LOG_PATH = os.getenv("COWRIE_LOG_PATH", "/cowrie/var/log/cowrie/cowrie.json")
    SENSOR_ID = os.getenv("SENSOR_ID", "cowrie-prod-01")

    # Optional GeoIP/ASN enrichment. Point at a directory holding the MaxMind
    # GeoLite2-Country.mmdb / GeoLite2-ASN.mmdb files; empty disables it.
    GEOIP_DB_DIR = os.getenv("GEOIP_DB_DIR", "")

    # Consumer batching / polling.
    BATCH_SIZE = int(os.getenv("WORKER_BATCH_SIZE", "50"))
    BATCH_TIMEOUT = float(os.getenv("WORKER_BATCH_TIMEOUT", "2.0"))
    HTTP_TIMEOUT = float(os.getenv("WORKER_HTTP_TIMEOUT", "10.0"))
