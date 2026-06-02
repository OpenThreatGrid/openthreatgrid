"""Tests for the event ingestion and query endpoints."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ingest_single_event(client, sample_event):
    resp = client.post("/api/v1/events", json=sample_event)
    assert resp.status_code == 201
    body = resp.json()
    assert body["accepted"] == 1
    assert len(body["event_ids"]) == 1


def test_ingest_batch(client, sample_event):
    second = {**sample_event, "username": "admin", "source_ip": "203.0.113.99"}
    resp = client.post("/api/v1/events", json=[sample_event, second])
    assert resp.status_code == 201
    assert resp.json()["accepted"] == 2


def test_ingest_is_idempotent(client, sample_event):
    fixed = {**sample_event, "event_id": "11111111-1111-4111-8111-111111111111"}
    first = client.post("/api/v1/events", json=fixed)
    second = client.post("/api/v1/events", json=fixed)
    assert first.json()["accepted"] == 1
    assert second.json()["accepted"] == 0  # duplicate skipped

    listed = client.get("/api/v1/events").json()
    assert len(listed) == 1


def test_query_and_filter(client, sample_event):
    client.post("/api/v1/events", json=sample_event)
    client.post(
        "/api/v1/events",
        json={**sample_event, "event_type": "command_exec", "command": "wget x"},
    )

    all_events = client.get("/api/v1/events").json()
    assert len(all_events) == 2

    filtered = client.get("/api/v1/events", params={"event_type": "command_exec"}).json()
    assert len(filtered) == 1
    assert filtered[0]["command"] == "wget x"

    by_ip = client.get("/api/v1/events", params={"source_ip": "203.0.113.42"}).json()
    assert len(by_ip) == 2


def test_get_event_by_id(client, sample_event):
    created = client.post("/api/v1/events", json=sample_event).json()
    event_id = created["event_ids"][0]

    resp = client.get(f"/api/v1/events/{event_id}")
    assert resp.status_code == 200
    assert resp.json()["event_id"] == event_id

    missing = client.get("/api/v1/events/does-not-exist")
    assert missing.status_code == 404


def test_invalid_event_rejected(client, sample_event):
    bad = {**sample_event, "event_type": "not_a_real_type"}
    resp = client.post("/api/v1/events", json=bad)
    assert resp.status_code == 422
