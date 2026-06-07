# Deception Features

Beyond passive honeypots, OpenThreatGrid ships an active **deception** sensor:
the HTTP trap. Deception assets are designed so that *any* interaction is
inherently suspicious — legitimate users never request a `.env` file or post to a
fake admin login — which makes the resulting telemetry high-signal.

## HTTP trap

[`sensors/http-trap`](../sensors/http-trap) is a small FastAPI honeypot that:

- Serves a **fake admin login portal** at `/`, `/admin`, `/login`,
  `/wp-login.php`, `/phpmyadmin/`. Posted credentials are recorded and always
  rejected.
- Serves **canary files** — `/.env`, `/.git/config`, `/wp-config.php.bak`,
  `/.aws/credentials`, `/.ssh/id_rsa`, … — returning decoy content.
- Records every other probe as a generic request.

Each interaction is written as one JSON line and ingested through the standard
pipeline; the Logstash `http-trap` branch maps it to the OTG schema:

```
HTTP trap → http-trap.log → Filebeat (log_type=http-trap) → Logstash → OpenSearch
```

### Event mapping

| Trap event | OTG `event_type` | Tags |
|---|---|---|
| `login_attempt` (creds posted) | `login_attempt` | `http`, `deception`, `credential` |
| `canary` (decoy file requested) | `connection` | `http`, `deception`, `canary` |
| `request` (other probe) | `connection` | `http`, `deception`, `scan` |

The requested path is stored as `payload_url`, the source IP honours
`X-Forwarded-For` (so it works behind Traefik), and logins never succeed.

### Run

- **Local:** `cd sensors/http-trap && pip install -r requirements.txt && uvicorn app.main:app --port 8080`,
  then point a Filebeat at the log (`LOG_TYPE=http-trap`,
  `LOG_PATH=…/http-trap.log`) shipping to Logstash.
- **Kubernetes (raw):** uncomment the `http-trap/*` entries in
  [`deploy/k8s/kustomization.yaml`](../deploy/k8s/kustomization.yaml).
- **Helm:** `--set httpTrap.enabled=true` (off by default).

## Hunting deception hits

Because deception events carry the `deception` tag, the **Threat Hunting** and
**Malware & Payload** dashboards surface them directly. Useful KQL:

```text
tags:"canary"                 # decoy-file access — almost always malicious
tags:"deception" and event_type:"login_attempt"   # fake-portal credential stuffing
sensor_type:"http-trap"       # everything the trap saw
```

## Safety

The trap captures, it never serves anything real: credentials are rejected,
canary files are decoys, nothing executes. Still treat it like any sensor — run
isolated with **no outbound internet** (the `http-trap-isolation` NetworkPolicy),
and publish only aggregated or sanitized intelligence. See
[Safe Honeypot Operation](safe-honeypot-operation.md).
