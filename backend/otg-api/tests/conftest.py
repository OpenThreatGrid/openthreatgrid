"""Shared pytest fixtures: an isolated in-memory SQLite app per test."""

import importlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    """Yield a TestClient backed by a fresh in-memory database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    importlib.import_module("app.models")  # ensure models are registered

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Construct the client WITHOUT a context manager so the app lifespan (which
    # would init the real Postgres engine) is not triggered during tests.
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


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
