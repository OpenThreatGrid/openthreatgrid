"""OpenSearch-backed :class:`EventStore`.

Events are written to daily indices (``otg-events-YYYY.MM.DD``) governed by an
index template, and read back through the ``otg-events-*`` wildcard. The document
``_id`` is the event's ``event_id`` and writes use the ``create`` op type, so a
worker can safely retry a batch: duplicates raise a 409 conflict and are reported
as "not accepted" rather than overwriting existing telemetry.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from opensearchpy import OpenSearch, helpers

from app.store.base import TOP_FIELDS, EventStore

logger = logging.getLogger("otg.api.store")

# Index template applied at startup. Mirrors docs/event-schema.md; string fields
# that drive aggregations are ``keyword`` so top-N queries are exact.
INDEX_TEMPLATE: dict[str, Any] = {
    "index_patterns": ["otg-events-*"],
    "template": {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "event_id": {"type": "keyword"},
                "timestamp": {"type": "date"},
                "ingested_at": {"type": "date"},
                "sensor_id": {"type": "keyword"},
                "sensor_type": {"type": "keyword"},
                "event_type": {"type": "keyword"},
                "source_ip": {"type": "ip"},
                "source_port": {"type": "integer"},
                "destination_ip": {"type": "ip"},
                "destination_port": {"type": "integer"},
                "protocol": {"type": "keyword"},
                "username": {"type": "keyword"},
                "password": {"type": "keyword"},
                "command": {"type": "keyword", "ignore_above": 1024},
                "payload_url": {"type": "keyword", "ignore_above": 2048},
                "payload_hash": {"type": "keyword"},
                "session_id": {"type": "keyword"},
                "success": {"type": "boolean"},
                "geo_country": {"type": "keyword"},
                "geo_asn": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "raw_event": {"type": "object", "enabled": False},
            }
        },
    },
}

_TEMPLATE_NAME = "otg-events"


def _index_for(timestamp: Any, prefix: str) -> str:
    """Daily index name derived from an event timestamp (ISO string or datetime)."""
    if isinstance(timestamp, datetime):
        dt = timestamp
    else:
        try:
            dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            dt = datetime.now(UTC)
    return f"{prefix}-{dt:%Y.%m.%d}"


class OpenSearchStore(EventStore):
    def __init__(
        self,
        client: OpenSearch,
        index_prefix: str = "otg-events",
        *,
        refresh: bool = True,
    ) -> None:
        self.client = client
        self.prefix = index_prefix
        self.pattern = f"{index_prefix}-*"
        # ``wait_for`` makes a just-indexed event searchable before the request
        # returns — important for the bursty honeypot pipeline and for tests.
        self.refresh: bool | str = "wait_for" if refresh else False

    def init(self) -> None:
        self.client.indices.put_index_template(name=_TEMPLATE_NAME, body=INDEX_TEMPLATE)
        logger.info("Ensured OpenSearch index template %s", _TEMPLATE_NAME)

    def ping(self) -> bool:
        return bool(self.client.ping())

    def bulk_index(self, events: list[dict[str, Any]]) -> list[str]:
        now = datetime.now(UTC).isoformat()
        actions = []
        for ev in events:
            doc = {**ev, "ingested_at": ev.get("ingested_at") or now}
            actions.append(
                {
                    "_op_type": "create",
                    "_index": _index_for(doc.get("timestamp"), self.prefix),
                    "_id": doc["event_id"],
                    "_source": doc,
                }
            )

        # raise_on_error=False so 409 conflicts (duplicates) don't abort the batch.
        _, errors = helpers.bulk(
            self.client, actions, raise_on_error=False, refresh=self.refresh
        )

        rejected: set[str] = set()
        for err in errors or []:
            info = next(iter(err.values()))
            status = info.get("status")
            doc_id = info.get("_id")
            if status == 409:  # duplicate event_id — expected on retry
                rejected.add(doc_id)
            else:  # genuine failure — surface it
                logger.warning("Bulk index error for %s: %s", doc_id, info.get("error"))
                rejected.add(doc_id)

        return [ev["event_id"] for ev in events if ev["event_id"] not in rejected]

    def get(self, event_id: str) -> dict[str, Any] | None:
        resp = self.client.search(
            index=self.pattern,
            body={"query": {"term": {"event_id": event_id}}, "size": 1},
            ignore_unavailable=True,
        )
        hits = resp["hits"]["hits"]
        return hits[0]["_source"] if hits else None

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
        filters: list[dict] = []
        if event_type:
            filters.append({"term": {"event_type": event_type}})
        if source_ip:
            filters.append({"term": {"source_ip": source_ip}})
        if sensor_id:
            filters.append({"term": {"sensor_id": sensor_id}})
        if since or until:
            rng: dict[str, Any] = {}
            if since:
                rng["gte"] = since.isoformat()
            if until:
                rng["lte"] = until.isoformat()
            filters.append({"range": {"timestamp": rng}})

        query = {"bool": {"filter": filters}} if filters else {"match_all": {}}
        resp = self.client.search(
            index=self.pattern,
            body={
                "query": query,
                "sort": [{"timestamp": {"order": "desc"}}],
                "from": offset,
                "size": limit,
            },
            ignore_unavailable=True,
        )
        return [hit["_source"] for hit in resp["hits"]["hits"]]

    def top(self, field: str, limit: int = 10) -> list[dict[str, Any]]:
        os_field = TOP_FIELDS.get(field)
        if os_field is None:
            raise ValueError(f"Unsupported top field: {field}")
        resp = self.client.search(
            index=self.pattern,
            body={
                "size": 0,
                "aggs": {"top": {"terms": {"field": os_field, "size": limit}}},
            },
            ignore_unavailable=True,
        )
        buckets = resp.get("aggregations", {}).get("top", {}).get("buckets", [])
        return [{"key": str(b["key"]), "count": b["doc_count"]} for b in buckets]

    def summary(self) -> dict[str, Any]:
        resp = self.client.search(
            index=self.pattern,
            body={
                "size": 0,
                "aggs": {
                    "unique_source_ips": {"cardinality": {"field": "source_ip"}},
                    "unique_sensors": {"cardinality": {"field": "sensor_id"}},
                    "by_type": {"terms": {"field": "event_type", "size": 50}},
                    "first_event": {"min": {"field": "timestamp"}},
                    "last_event": {"max": {"field": "timestamp"}},
                    "top_source_ips": {"terms": {"field": "source_ip", "size": 10}},
                    "top_usernames": {"terms": {"field": "username", "size": 10}},
                    "top_passwords": {"terms": {"field": "password", "size": 10}},
                },
            },
            ignore_unavailable=True,
        )
        aggs = resp.get("aggregations", {})
        total = resp["hits"]["total"]["value"]

        def _buckets(name: str) -> list[dict[str, Any]]:
            return [
                {"key": str(b["key"]), "count": b["doc_count"]}
                for b in aggs.get(name, {}).get("buckets", [])
            ]

        def _ts(name: str) -> str | None:
            return aggs.get(name, {}).get("value_as_string")

        return {
            "total_events": total,
            "unique_source_ips": aggs.get("unique_source_ips", {}).get("value", 0),
            "unique_sensors": aggs.get("unique_sensors", {}).get("value", 0),
            "events_by_type": _buckets("by_type"),
            "top_source_ips": _buckets("top_source_ips"),
            "top_usernames": _buckets("top_usernames"),
            "top_passwords": _buckets("top_passwords"),
            "first_event": _ts("first_event"),
            "last_event": _ts("last_event"),
        }
