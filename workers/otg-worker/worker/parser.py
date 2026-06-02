"""Parser: tail the Cowrie JSON log and push normalized events to Redis.

Runs as a sidecar next to Cowrie. It follows ``cowrie.json`` (like ``tail -f``),
maps each line to the OTG schema, and ``LPUSH``es the JSON onto the shared Redis
queue that the consumer drains.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator

import redis

from worker.config import Config
from worker.cowrie_mapper import map_cowrie_event

logger = logging.getLogger("otg.parser")


def follow(path: str, from_start: bool = False, poll_interval: float = 0.5) -> Iterator[str]:
    """Yield lines appended to ``path``, tolerating log rotation/truncation."""
    while not _exists(path):
        logger.info("Waiting for Cowrie log at %s", path)
        time.sleep(poll_interval)

    with open(path, encoding="utf-8", errors="replace") as fh:
        if not from_start:
            fh.seek(0, 2)  # jump to end; only new lines
        while True:
            line = fh.readline()
            if line:
                yield line
                continue
            # No new data — detect truncation (rotation) and reset.
            if _truncated(fh, path):
                fh.seek(0)
            time.sleep(poll_interval)


def _exists(path: str) -> bool:
    import os

    return os.path.exists(path)


def _truncated(fh, path: str) -> bool:
    import os

    try:
        return os.stat(path).st_size < fh.tell()
    except FileNotFoundError:
        return False


def run(config: Config | None = None) -> None:
    """Tail the configured Cowrie log forever, pushing events to Redis."""
    cfg = config or Config()
    client = redis.Redis.from_url(cfg.REDIS_URL)
    logger.info("Parser tailing %s -> queue %s", cfg.COWRIE_LOG_PATH, cfg.EVENT_QUEUE)

    pushed = 0
    for raw in follow(cfg.COWRIE_LOG_PATH):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            logger.debug("Skipping non-JSON line")
            continue
        event = map_cowrie_event(entry, sensor_id=cfg.SENSOR_ID)
        if event is None:
            continue
        client.lpush(cfg.EVENT_QUEUE, json.dumps(event))
        pushed += 1
        if pushed % 100 == 0:
            logger.info("Pushed %d events", pushed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
