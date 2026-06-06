#!/usr/bin/env python3
"""Export the OpenThreatGrid API's OpenAPI schema to a static file.

FastAPI serves the live schema at ``/openapi.json``; this dumps the same schema
to a committed file so it can be version-controlled, diffed in review, rendered
by the docs site (Redoc), and fed to client generators — without a running
server.

    # from the repo root, with the API deps installed:
    cd backend/otg-api && pip install -r requirements.txt
    python ../../scripts/export_openapi.py

Writes ``docs/openapi.json`` (and ``docs/openapi.yaml`` if PyYAML is available).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
API_DIR = REPO_ROOT / "backend" / "otg-api"
OUT_JSON = REPO_ROOT / "docs" / "openapi.json"
OUT_YAML = REPO_ROOT / "docs" / "openapi.yaml"


def main() -> None:
    # Make the API package importable without installing it.
    sys.path.insert(0, str(API_DIR))
    try:
        from app.main import app
    except ModuleNotFoundError as exc:  # pragma: no cover - helpful error
        raise SystemExit(
            f"Cannot import the API ({exc}). Install its deps first:\n"
            f"  cd {API_DIR} && pip install -r requirements.txt"
        ) from exc

    schema = app.openapi()

    OUT_JSON.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Wrote {OUT_JSON.relative_to(REPO_ROOT)} "
          f"(OpenAPI {schema.get('openapi')}, {len(schema.get('paths', {}))} paths)")

    try:
        import yaml
    except ImportError:
        print("(PyYAML not installed — skipping openapi.yaml)")
        return
    OUT_YAML.write_text(yaml.safe_dump(schema, sort_keys=False))
    print(f"Wrote {OUT_YAML.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
