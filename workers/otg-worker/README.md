# otg-worker

Parser + enrichment worker for OpenThreatGrid. A single image runs in two roles:

- **parser** — tails the Cowrie `cowrie.json` log, maps each entry to the OTG
  event schema, and `LPUSH`es it onto a Redis queue. Runs as a sidecar next to
  Cowrie.
- **consumer** — `BRPOP`s events off the queue, enriches them (tagging,
  botnet-indicator detection, optional GeoIP/ASN), and POSTs batches to
  `POST /api/v1/events`. Failed batches are re-queued.

```
Cowrie cowrie.json ──(parser)──► Redis queue ──(consumer)──► otg-api ──► OpenSearch
```

## Run

```bash
python -m worker parser     # sidecar role
python -m worker consumer   # enrichment role (default)
```

Configuration is via environment variables — see `worker/config.py`
(`REDIS_URL`, `REDIS_EVENT_QUEUE`, `OTG_API_URL`, `COWRIE_LOG_PATH`,
`SENSOR_ID`, `WORKER_BATCH_SIZE`, `GEOIP_DB_DIR`, ...).

### GeoIP / ASN enrichment (optional)

Point `GEOIP_DB_DIR` at a directory containing MaxMind `GeoLite2-Country.mmdb`
and `GeoLite2-ASN.mmdb` to populate `geo_country` / `geo_asn` on each event. The
databases are licensed and not bundled — get them free from
[MaxMind GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data).
When the directory or databases are absent, enrichment self-disables and the
pipeline runs unchanged.

## Modules

| Module | Responsibility |
|---|---|
| `cowrie_mapper.py` | Cowrie eventid → OTG `event_type`, field normalization |
| `enrichment.py` | Tagging, botnet-indicator detection, optional GeoIP/ASN |
| `geoip.py` | MaxMind GeoLite2 lookups (self-disabling) |
| `parser.py` | Tail Cowrie log → Redis |
| `consumer.py` | Redis → enrich → API, with re-queue on failure |

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

`cowrie_mapper` and `enrichment` are pure functions with full unit coverage and
no external services required.
