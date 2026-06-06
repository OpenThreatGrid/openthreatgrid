"""Shared pytest fixtures: an isolated in-memory event store per test."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import get_store
from app.store.memory_store import MemoryStore


@pytest.fixture()
def client():
    """Yield a TestClient backed by a fresh in-memory store.

    The store dependency is overridden so the real OpenSearch client is never
    constructed during the test suite.
    """
    store = MemoryStore()
    app.dependency_overrides[get_store] = lambda: store
    # Construct the client WITHOUT a context manager so the app lifespan (which
    # would reach out to OpenSearch) is not triggered during tests.
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_event() -> dict:
    return {
        "timestamp": "2026-06-01T12:34:56.789Z",
        "sensor_id": "cowrie-test-01",
        "sensor_type": "cowrie",
        "event_type": "login_attempt",
        "source_ip": "203.0.113.42",
        "source_port": 54321,
        "destination_port": 2222,
        "protocol": "ssh",
        "username": "root",
        "password": "admin123",
        "success": False,
        "tags": ["ssh", "bruteforce"],
    }
