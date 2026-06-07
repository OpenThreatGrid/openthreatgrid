"""Tests for the HTTP-trap app: it records the right events and serves decoys."""

import json

import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture()
def client(tmp_path, monkeypatch):
    log = tmp_path / "http-trap.log"
    monkeypatch.setattr(main, "LOG_PATH", str(log))
    return TestClient(main.app), log


def _events(log):
    return [json.loads(line) for line in log.read_text().splitlines() if line]


def test_healthz_not_logged(client):
    c, log = client
    assert c.get("/healthz").status_code == 200
    assert not log.exists() or _events(log) == []


def test_login_post_records_credentials(client):
    c, log = client
    resp = c.post("/admin/login", data={"username": "root", "password": "secret"})
    assert resp.status_code == 401
    events = _events(log)
    assert len(events) == 1
    ev = events[0]
    assert ev["trap_event"] == "login_attempt"
    assert ev["username"] == "root"
    assert ev["password"] == "secret"
    assert ev["path"] == "/admin/login"


def test_canary_file_recorded(client):
    c, log = client
    resp = c.get("/.env")
    assert resp.status_code == 200
    ev = _events(log)[0]
    assert ev["trap_event"] == "canary"
    assert ev["path"] == "/.env"


def test_login_page_served_and_recorded(client):
    c, log = client
    resp = c.get("/admin")
    assert resp.status_code == 200
    assert "Administration" in resp.text
    assert _events(log)[0]["trap_event"] == "request"


def test_forwarded_for_used_as_source_ip(client):
    c, log = client
    c.get("/phpmyadmin/", headers={"X-Forwarded-For": "198.51.100.7, 10.0.0.1"})
    assert _events(log)[0]["src_ip"] == "198.51.100.7"
