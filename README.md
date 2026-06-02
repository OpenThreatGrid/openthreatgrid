# OpenThreatGrid

**OpenThreatGrid** is an open-source honeynet-powered platform for threat hunting, malware analysis, and cyber threat intelligence.

OpenThreatGrid collects telemetry from distributed honeypot sensors, normalizes attack events, stores them for analysis, and generates threat intelligence reports from real-world attacker behavior.

> Status: early-stage 

## Why OpenThreatGrid?

Modern internet-facing systems are constantly scanned, brute-forced, exploited, and abused by automated malware and botnet infrastructure. OpenThreatGrid is built to help researchers, defenders, and communities observe that activity safely using honeynet telemetry.

The project combines four core areas:

- **Threat Hunting**: investigate attacker behavior from real telemetry.
- **Threat Intelligence**: transform raw events into useful indicators and reports.
- **Honeynet**: run distributed honeypot sensors as a telemetry grid.
- **Malware Analysis**: identify malware delivery attempts, botnet patterns, and suspicious payloads.

## MVP Scope

The first public version focuses on a simple end-to-end pipeline:

1. Deploy a Cowrie SSH/Telnet honeypot sensor on Kubernetes.
2. Parse Cowrie logs into a normalized OpenThreatGrid event schema.
3. Send events to a FastAPI ingestion API.
4. Store normalized events in PostgreSQL.
5. Visualize telemetry with Grafana.
6. Generate weekly Markdown threat reports.

## Architecture

```text
Internet
   |
   v
[Honeypot Sensors]
   |
   v
[Log Shipper / Parser]
   |
   v
[OpenThreatGrid API]
   |
   v
[PostgreSQL]
   |
   +--> [Grafana Dashboard]
   |
   +--> [Weekly Report Generator]
```

See [`docs/architecture.md`](docs/architecture.md) for details.

## Quick Start (local)

The full pipeline — Cowrie → parser → Redis → consumer → API → PostgreSQL →
Grafana — runs locally with Docker Compose:

```bash
./scripts/run_local.sh         # or: docker compose up --build
```

- API docs:  http://localhost:8000/docs
- Stats:     http://localhost:8000/api/v1/stats/summary
- Grafana:   http://localhost:3000  (admin / admin)
- Poke the honeypot:  `ssh -p 2222 root@localhost`

Run the test suites without Docker:

```bash
cd backend/otg-api  && pip install -r requirements-dev.txt && pytest
cd workers/otg-worker && pip install -r requirements-dev.txt && pytest
```

See [`docs/deployment-guide.md`](docs/deployment-guide.md) for Kubernetes/Helm
and production bring-up.

## Repository Layout

```text
openthreatgrid/
├── backend/otg-api/        FastAPI ingestion + query API (events, stats, health)
├── workers/otg-worker/     Cowrie→OTG parser + enrichment consumer
├── sensors/cowrie/         Cowrie honeypot image + config overrides
├── reports/                Weekly Jinja2 threat-intel report generator
├── dashboard/grafana/      Provisioned datasource + 10-panel dashboard
├── deploy/
│   ├── edge/               DO VPS: HAProxy + Tailscale + UFW bootstrap
│   ├── k8s/                Namespace, Traefik, Postgres, Redis, Cowrie, API,
│   │                       worker, Grafana, reports, NetworkPolicies, kustomize
│   └── helm/               Helm chart (openthreatgrid)
├── examples/               Sample Cowrie logs + normalized OTG events
├── scripts/                run_local, seed_sample_data, test_proxy_protocol
└── docs/                   Architecture, infrastructure, event schema, deployment,
                            data policy, safe operation, Shadowserver, roadmap
```

## Normalized Event Example

```json
{
  "timestamp": "2026-06-01T12:00:00Z",
  "sensor_id": "otg-cowrie-01",
  "sensor_type": "cowrie",
  "source_ip": "203.0.113.10",
  "destination_port": 22,
  "protocol": "ssh",
  "event_type": "login_attempt",
  "username": "root",
  "password": "admin123",
  "command": null,
  "tags": ["ssh", "bruteforce"],
  "raw_event": {}
}
```

## Kubernetes-first Design

OpenThreatGrid is designed to run on Kubernetes from the beginning. The initial deployment targets a small cluster and can later scale into a distributed honeynet.

Recommended MVP services:

- `otg-cowrie-sensor`
- `otg-api`
- `otg-worker`
- `postgres`
- `grafana`

## Safety Principles

Running honeypots requires careful isolation. OpenThreatGrid follows these principles:

- Run honeypots in a dedicated namespace.
- Apply Kubernetes NetworkPolicy.
- Restrict outbound traffic from honeypot pods.
- Never expose internal production networks.
- Do not publish raw sensitive data.
- Store malware binaries only in a dedicated isolated malware lab, not in the default MVP.
- Prefer storing hashes, URLs, commands, and metadata.

See [`docs/safe-honeypot-operation.md`](docs/safe-honeypot-operation.md).

## Roadmap

See [`docs/roadmap.md`](docs/roadmap.md).

## Shadowserver Collaboration Plan

OpenThreatGrid is inspired by community-scale internet defense projects and aims to produce safe, anonymized, and useful regional telemetry. The long-term goal is to prepare data formats and operational practices that could support collaboration with organizations such as Shadowserver Foundation.

See [`docs/shadowserver-collaboration.md`](docs/shadowserver-collaboration.md).

## License

This project is planned to use the Apache-2.0 License.

## Disclaimer

OpenThreatGrid is for defensive security research, threat intelligence, education, and community protection. Do not use this project to attack, compromise, or disrupt systems you do not own or have permission to test.
