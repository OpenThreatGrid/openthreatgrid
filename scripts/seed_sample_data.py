#!/usr/bin/env python3
"""Seed OpenSearch with the sample events in ``examples/`` (topology A).

Dependency-free (stdlib only). Bulk-indexes events directly into daily
``otg-events-YYYY.MM.DD`` indices using the event timestamp, with the document
id set to ``event_id`` and op type ``create`` (idempotent — safe to re-run).
Useful for populating the dashboards without waiting for live attacks.

    python scripts/seed_sample_data.py --opensearch-url http://localhost:9200
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVENTS = REPO_ROOT / "examples" / "sample-events" / "otg-events.json"


def _index_for(timestamp: str, prefix: str = "otg-events") -> str:
    try:
        dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        dt = datetime.now(timezone.utc)
    return f"{prefix}-{dt:%Y.%m.%d}"


def bulk_index(os_url: str, events: list[dict]) -> int:
    """POST a _bulk create request; return the number of accepted (created) docs."""
    lines: list[str] = []
    for ev in events:
        ev = {**ev, "ingested_at": datetime.now(timezone.utc).isoformat()}
        eid = ev.get("event_id") or str(uuid.uuid4())
        ev["event_id"] = eid
        index = _index_for(ev.get("timestamp", ""))
        lines.append(json.dumps({"create": {"_index": index, "_id": eid}}))
        lines.append(json.dumps(ev))
    payload = ("\n".join(lines) + "\n").encode()

    req = urllib.request.Request(
        f"{os_url.rstrip('/')}/_bulk?refresh=true",
        data=payload,
        headers={"Content-Type": "application/x-ndjson"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read())
    created = sum(
        1 for item in body.get("items", [])
        if item.get("create", {}).get("status") in (200, 201)
    )
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opensearch-url", default="http://localhost:9200")
    parser.add_argument("--file", default=str(DEFAULT_EVENTS))
    args = parser.parse_args()

    events = json.loads(Path(args.file).read_text())
    if not isinstance(events, list):
        events = [events]

    try:
        created = bulk_index(args.opensearch_url, events)
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to reach OpenSearch at {args.opensearch_url}: {exc}") from exc

    print(f"Seeded {created} of {len(events)} events into {args.opensearch_url}")


if __name__ == "__main__":
    main()
