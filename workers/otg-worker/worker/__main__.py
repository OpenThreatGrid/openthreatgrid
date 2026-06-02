"""Worker entrypoint: ``python -m worker [parser|consumer]``.

A single image runs in two roles selected by the first argument (or the
``WORKER_ROLE`` env var), so the parser sidecar and the enrichment consumer
share one build.
"""

import logging
import os
import sys


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    role = sys.argv[1] if len(sys.argv) > 1 else os.getenv("WORKER_ROLE", "consumer")

    if role == "parser":
        from worker.parser import run
    elif role == "consumer":
        from worker.consumer import run
    else:
        sys.exit(f"Unknown role '{role}'. Use 'parser' or 'consumer'.")

    run()


if __name__ == "__main__":
    main()
