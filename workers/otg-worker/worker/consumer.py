"""Consumer: drain the Redis queue, enrich events, and submit them to the API.

Uses a blocking ``BRPOP`` to pull events, batches them up to ``BATCH_SIZE`` (or
``BATCH_TIMEOUT`` seconds), enriches each, and POSTs the batch to
``/api/v1/events``. On API failure the batch is re-queued so no events are lost.
"""

from __future__ import annotations

import json
import logging
import time

import httpx
import redis

from worker.config import Config
from worker.enrichment import enrich_event
from worker.geoip import GeoIP

logger = logging.getLogger("otg.consumer")


def _drain_batch(client: redis.Redis, queue: str, batch_size: int, timeout: float) -> list[dict]:
    """Collect up to ``batch_size`` events, blocking up to ``timeout`` for the first."""
    batch: list[dict] = []

    first = client.brpop([queue], timeout=int(max(1, timeout)))
    if first is None:
        return batch
    batch.append(json.loads(first[1]))

    # Grab whatever else is immediately available without blocking.
    while len(batch) < batch_size:
        item = client.rpop(queue)
        if item is None:
            break
        batch.append(json.loads(item))
    return batch


def _submit(http: httpx.Client, api_url: str, events: list[dict]) -> bool:
    try:
        resp = http.post(f"{api_url}/api/v1/events", json=events)
        resp.raise_for_status()
        accepted = resp.json().get("accepted", 0)
        logger.info("Submitted %d events (%d accepted)", len(events), accepted)
        return True
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Submit failed (%s); re-queueing %d events", exc, len(events))
        return False


def run(config: Config | None = None, max_batches: int | None = None) -> None:
    """Consume and submit forever (or for ``max_batches`` iterations in tests)."""
    cfg = config or Config()
    client = redis.Redis.from_url(cfg.REDIS_URL)
    geoip = GeoIP(cfg.GEOIP_DB_DIR)
    logger.info("Consumer draining %s -> %s", cfg.EVENT_QUEUE, cfg.API_BASE_URL)

    processed = 0
    with httpx.Client(timeout=cfg.HTTP_TIMEOUT) as http:
        while max_batches is None or processed < max_batches:
            batch = _drain_batch(client, cfg.EVENT_QUEUE, cfg.BATCH_SIZE, cfg.BATCH_TIMEOUT)
            if not batch:
                time.sleep(0.1)
                continue

            enriched = [enrich_event(e, geoip) for e in batch]
            if not _submit(http, cfg.API_BASE_URL, enriched):
                # Re-queue (push back to the tail) so events are retried.
                pipe = client.pipeline()
                for event in batch:
                    pipe.lpush(cfg.EVENT_QUEUE, json.dumps(event))
                pipe.execute()
                time.sleep(2.0)
            processed += 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
