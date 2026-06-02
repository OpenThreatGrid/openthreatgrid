#!/usr/bin/env python3
"""Seed a running OTG API with the sample events in ``examples/``.

Dependency-free (stdlib only) so it runs anywhere. Useful for populating the
dashboard during local development.

    python scripts/seed_sample_data.py --api-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVENTS = REPO_ROOT / "examples" / "sample-events" / "otg-events.json"


def post_events(api_url: str, events: list[dict]) -> dict:
    data = json.dumps(events).encode()
    req = urllib.request.Request(
        f"{api_url.rstrip('/')}/api/v1/events",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--file", default=str(DEFAULT_EVENTS))
    args = parser.parse_args()

    events = json.loads(Path(args.file).read_text())
    if not isinstance(events, list):
        events = [events]

    try:
        result = post_events(args.api_url, events)
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to reach API at {args.api_url}: {exc}") from exc

    print(f"Seeded {result.get('accepted')} of {len(events)} events into {args.api_url}")


if __name__ == "__main__":
    main()
