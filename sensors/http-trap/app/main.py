"""OpenThreatGrid HTTP trap — a custom deception web honeypot.

Serves a fake admin login portal and a set of canary files (``.env``,
``wp-config.php.bak``, …). Every interesting interaction is written as one JSON
line to ``HTTP_TRAP_LOG_PATH``, which a Filebeat sidecar tails (``LOG_TYPE=http-trap``)
and ships to Logstash (the ``http-trap`` branch in ``otg.conf`` maps it).

It captures, never serves real anything: posted credentials are always rejected,
canary files return decoy content, and nothing executes. Keep it isolated with
NetworkPolicy like any other sensor.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from app import __version__

LOG_PATH = os.getenv("HTTP_TRAP_LOG_PATH", "/var/log/http-trap/http-trap.log")
SENSOR_ID = os.getenv("SENSOR_ID", "http-trap-01")
LISTEN_PORT = int(os.getenv("HTTP_TRAP_PORT", "8080"))

logger = logging.getLogger("otg.http-trap")

# Decoy files that only an attacker/scanner would request.
CANARY_PATHS = {
    "/.env", "/.git/config", "/backup.sql", "/database.sql", "/config.php.bak",
    "/wp-config.php.bak", "/.aws/credentials", "/.ssh/id_rsa", "/server-status",
}
# Paths that render the fake login portal.
LOGIN_PATHS = {"/", "/admin", "/admin/", "/login", "/admin/login", "/wp-login.php", "/phpmyadmin/"}

LOGIN_HTML = """<!doctype html><html><head><title>Admin Login</title></head>
<body style="font-family:sans-serif;max-width:320px;margin:80px auto">
<h2>Administration</h2>
<form method="post" action="/admin/login">
  <p><input name="username" placeholder="Username" style="width:100%;padding:8px"></p>
  <p><input name="password" type="password" placeholder="Password"
     style="width:100%;padding:8px"></p>
  <p><button type="submit" style="width:100%;padding:8px">Sign in</button></p>
</form></body></html>"""

app = FastAPI(title="OpenThreatGrid HTTP Trap", version=__version__, docs_url=None, redoc_url=None)


def _client_ip(request: Request) -> tuple[str | None, int | None]:
    """Real client IP/port, honouring X-Forwarded-For from a fronting proxy."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip(), None
    client = request.client
    return (client.host, client.port) if client else (None, None)


def _record(trap_event: str, request: Request, path: str,
            username: str | None = None, password: str | None = None) -> None:
    """Append one JSON event line to the trap log (and stdout)."""
    src_ip, src_port = _client_ip(request)
    rec: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "sensor_id": SENSOR_ID,
        "trap_event": trap_event,
        "src_ip": src_ip,
        "src_port": src_port,
        "method": request.method,
        "path": path,
        "host": request.headers.get("host"),
        "user_agent": request.headers.get("user-agent"),
        "username": username,
        "password": password,
    }
    line = json.dumps(rec)
    try:
        p = Path(LOG_PATH)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError as exc:  # never let logging break the response
        logger.warning("Failed writing trap log: %s", exc)
    logger.info("trap %s %s %s", trap_event, request.method, path)


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    """Liveness probe — not recorded as attacker activity."""
    return {"status": "ok"}


@app.api_route("/{full_path:path}", methods=["GET", "POST", "HEAD"], include_in_schema=False)
async def trap(full_path: str, request: Request):
    path = "/" + full_path

    if request.method == "POST":
        username = password = None
        try:
            form = await request.form()
            username = form.get("username") or form.get("user") or form.get("email")
            password = form.get("password") or form.get("pass") or form.get("pwd")
        except Exception:  # noqa: BLE001 - malformed body is itself suspicious
            pass
        if username or password:
            _record("login_attempt", request, path,
                     username=str(username) if username else None,
                     password=str(password) if password else None)
            return HTMLResponse(LOGIN_HTML, status_code=401)
        _record("request", request, path)
        return HTMLResponse(LOGIN_HTML, status_code=200)

    # GET / HEAD
    if path in CANARY_PATHS or path.endswith((".env", ".bak", ".sql")):
        _record("canary", request, path)
        return PlainTextResponse("# (decoy)\n", status_code=200)

    _record("request", request, path)
    status = 200 if path in LOGIN_PATHS else 404
    return HTMLResponse(LOGIN_HTML, status_code=status)
