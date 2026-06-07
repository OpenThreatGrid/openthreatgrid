# HTTP trap

A custom **deception web honeypot** for OpenThreatGrid (plan v0.8). It serves a
fake admin login portal and canary files, recording every interaction as JSON
that the ingestion pipeline picks up:

```
HTTP trap → http-trap.log → Filebeat (log_type=http-trap) → Logstash → OpenSearch
```

## What it captures

- **Fake admin login** (`/`, `/admin`, `/login`, `/wp-login.php`, `/phpmyadmin/`) —
  posted credentials are recorded and always rejected.
- **Canary files** (`/.env`, `/.git/config`, `/wp-config.php.bak`,
  `/.aws/credentials`, `/.ssh/id_rsa`, …) — return decoy content; any request is
  high-signal.
- **Other probes** — recorded as generic requests.

Events are tagged `deception` (+ `credential`/`canary`/`scan`). Source IP honours
`X-Forwarded-For`. `/healthz` is a probe endpoint and is never recorded.

## Run

```bash
cd sensors/http-trap
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
HTTP_TRAP_LOG_PATH=/tmp/http-trap.log uvicorn app.main:app --port 8080
```

Then ship it with a Filebeat to Logstash:

```bash
LOG_TYPE=http-trap LOG_PATH=/tmp/http-trap.log SENSOR_ID=http-trap-01 \
  filebeat -e -c deploy/filebeat-logstash/filebeat/filebeat.yml
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Configuration

| Env | Default | Purpose |
|---|---|---|
| `HTTP_TRAP_LOG_PATH` | `/var/log/http-trap/http-trap.log` | JSON event log Filebeat tails |
| `SENSOR_ID` | `http-trap-01` | Sensor id stamped on events |
| `HTTP_TRAP_PORT` | `8080` | (informational) listen port |

See [`docs/deception-features.md`](../../docs/deception-features.md) for the event
mapping and hunting queries, and [`deploy/k8s/http-trap/`](../../deploy/k8s/http-trap/)
for the Kubernetes deployment (trap + Filebeat sidecar, isolated by NetworkPolicy).
