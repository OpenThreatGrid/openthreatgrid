"""Event storage backends and the FastAPI dependency that exposes them."""

from __future__ import annotations

from app.config import get_settings
from app.store.base import EventStore

_store: EventStore | None = None


def build_store() -> EventStore:
    """Construct the configured OpenSearch-backed store."""
    from opensearchpy import OpenSearch

    from app.store.opensearch_store import OpenSearchStore

    settings = get_settings()
    http_auth = (
        (settings.opensearch_username, settings.opensearch_password)
        if settings.opensearch_username
        else None
    )
    client = OpenSearch(
        hosts=[settings.opensearch_url],
        http_auth=http_auth,
        use_ssl=settings.opensearch_url.startswith("https"),
        verify_certs=settings.opensearch_verify_certs,
        ssl_show_warn=settings.opensearch_verify_certs,
        timeout=10,
        max_retries=3,
        retry_on_timeout=True,
    )
    return OpenSearchStore(client, settings.opensearch_index_prefix)


def get_store() -> EventStore:
    """FastAPI dependency returning the process-wide store singleton.

    Tests override this dependency with an in-memory store, so the real
    OpenSearch client is never constructed during the test suite.
    """
    global _store
    if _store is None:
        _store = build_store()
    return _store
