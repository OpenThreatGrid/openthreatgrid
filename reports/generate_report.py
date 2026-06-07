#!/usr/bin/env python3
"""Generate a weekly OpenThreatGrid threat-intelligence report (Markdown).

The report is built entirely from normalized events for a time window. Events
can come from either:

  * OpenSearch          (``--opensearch-url http://localhost:9200``), or
  * a local JSON file   (``--from-file events.json``) for offline/demo use.

Aggregations (top IPs, credentials, commands, downloads, botnet indicators) are
computed client-side so the report reflects exactly the chosen window.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = Path(__file__).parent / "templates"
DEFAULT_TEMPLATE = "weekly_report.md.j2"

# Tags emitted by the worker's enrichment that indicate automation.
BOTNET_TAGS = ["download", "execution", "persistence", "recon", "miner", "botnet_indicator"]


def _counts(values: list[str | None], limit: int | None = 10) -> list[dict]:
    counter = Counter(v for v in values if v)
    items = counter.most_common(limit)
    return [{"key": k, "count": c} for k, c in items]


def fetch_events_opensearch(os_url: str, since: datetime, until: datetime,
                            page: int = 1000) -> list[dict]:
    """Page through ``otg-events-*`` in OpenSearch for the window via search_after."""
    import httpx

    base = os_url.rstrip("/")
    rng = {"range": {"timestamp": {"gte": since.isoformat(), "lte": until.isoformat()}}}
    events: list[dict] = []
    search_after: list | None = None
    with httpx.Client(timeout=30.0) as http:
        while True:
            body: dict[str, Any] = {
                "size": page,
                "query": rng,
                "sort": [{"timestamp": "asc"}, {"event_id": "asc"}],
            }
            if search_after:
                body["search_after"] = search_after
            resp = http.post(
                f"{base}/otg-events-*/_search",
                json=body,
                params={"ignore_unavailable": "true"},
            )
            resp.raise_for_status()
            hits = resp.json().get("hits", {}).get("hits", [])
            if not hits:
                break
            events.extend(h["_source"] for h in hits)
            if len(hits) < page:
                break
            search_after = hits[-1]["sort"]
    return events


def count_events_opensearch(os_url: str, since: datetime, until: datetime) -> int:
    """Count events in a window (used for the prior-period delta)."""
    import httpx

    rng = {"range": {"timestamp": {"gte": since.isoformat(), "lte": until.isoformat()}}}
    resp = httpx.post(
        f"{os_url.rstrip('/')}/otg-events-*/_count",
        json={"query": rng},
        params={"ignore_unavailable": "true"},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json().get("count", 0)


def load_events_file(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text())
    return data if isinstance(data, list) else [data]


def _within(event: dict, since: datetime, until: datetime) -> bool:
    ts = event.get("timestamp")
    if not ts:
        return True
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return since <= dt <= until


def build_context(events: list[dict], since: datetime, until: datetime,
                  prior_total: int | None = None) -> dict[str, Any]:
    """Compute every value the template needs from a list of OTG events."""
    total = len(events)
    by_type = _counts([e.get("event_type") for e in events], limit=None)

    downloads = [
        {"url": e.get("payload_url"), "hash": e.get("payload_hash")}
        for e in events
        if e.get("event_type") == "file_download" and e.get("payload_url")
    ]

    commands = _counts(
        [e.get("command") for e in events if e.get("event_type") == "command_exec"]
    )

    # Botnet tag frequencies across events.
    tag_counter: Counter[str] = Counter()
    for e in events:
        for tag in e.get("tags") or []:
            if tag in BOTNET_TAGS:
                tag_counter[tag] += 1
    botnet_tags = [{"key": k, "count": c} for k, c in tag_counter.most_common()]

    geo = {e["source_ip"]: e.get("geo_country") for e in events
           if e.get("source_ip") and e.get("geo_country")}

    top_usernames = _counts([e.get("username") for e in events])
    top_passwords = _counts([e.get("password") for e in events])

    days = max(1, (until - since).days)
    daily_average = round(total / days, 1)

    delta_pct = None
    if prior_total:
        delta_pct = round((total - prior_total) / prior_total * 100, 1)

    observations: list[str] = []
    if downloads:
        observations.append(f"{len(downloads)} payload-download attempt(s) captured.")
    if botnet_tags:
        observations.append("Automated command chains consistent with botnet activity observed.")

    summary = {
        "total_events": total,
        "unique_source_ips": len({e.get("source_ip") for e in events if e.get("source_ip")}),
        "unique_sensors": len({e.get("sensor_id") for e in events if e.get("sensor_id")}),
        "events_by_type": by_type,
        "top_source_ips": _counts([e.get("source_ip") for e in events]),
        "top_usernames": top_usernames,
        "top_passwords": top_passwords,
    }

    return {
        "summary": summary,
        "period_start": since.date().isoformat(),
        "period_end": until.date().isoformat(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "daily_average": daily_average,
        "prior_total": prior_total,
        "delta_pct": delta_pct,
        "top_username": top_usernames[0]["key"] if top_usernames else None,
        "top_password": top_passwords[0]["key"] if top_passwords else None,
        "top_commands": commands,
        "downloads": downloads,
        "download_count": len(downloads),
        "botnet_tags": botnet_tags,
        "geo": geo,
        "observations": observations,
    }


def render(context: dict[str, Any], template_name: str = DEFAULT_TEMPLATE) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env.get_template(template_name).render(**context)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a weekly OTG threat report.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--opensearch-url", help="Base URL of OpenSearch (queries otg-events-*)")
    src.add_argument("--from-file", help="Path to a JSON file of OTG events")
    parser.add_argument("--days", type=int, default=7, help="Window length in days")
    parser.add_argument("--output", default="-", help="Output path ('-' for stdout)")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE)
    args = parser.parse_args()

    until = datetime.now(timezone.utc)
    since = until - timedelta(days=args.days)

    if args.opensearch_url:
        events = fetch_events_opensearch(args.opensearch_url, since, until)
        prior_total = count_events_opensearch(
            args.opensearch_url, since - timedelta(days=args.days), since
        )
    else:
        all_events = load_events_file(args.from_file)
        events = [e for e in all_events if _within(e, since, until)]
        # For file input, treat the whole file as the window if nothing matched.
        if not events:
            events = all_events
        prior_total = None

    context = build_context(events, since, until, prior_total=prior_total)
    report = render(context, args.template)

    if args.output == "-":
        print(report)
    else:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report)
        print(f"Wrote {out} ({len(report)} bytes, {len(events)} events)")


if __name__ == "__main__":
    main()
