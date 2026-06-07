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
2. Ship its logs with Filebeat (sidecar) to Logstash.
3. Normalize + enrich into the OpenThreatGrid event schema in Logstash.
4. Store normalized events in OpenSearch (`otg-events-*`).
5. Visualize telemetry with OpenSearch Dashboards.
6. Generate weekly Markdown threat reports.

## Architecture

Ingestion uses **topology A**: each sensor's log is shipped by **Filebeat** to a
single **Logstash** that normalizes + enriches and writes straight to OpenSearch
(Apache-2.0 `-oss` builds; Logstash carries the `logstash-output-opensearch`
plugin).

```text
Internet
   |
   v
[Honeypot Sensors]  (Cowrie, OpenCanary, HTTP trap)
   |  cowrie.json / opencanary.log / http-trap.log
   v
[Filebeat sidecar] ──► [Logstash]  (normalize + enrich + GeoIP)
                           |
                           v
                  [OpenSearch  (otg-events-*)]
                           |
              +------------+------------+
              v                         v
   [OpenSearch Dashboards]   [Weekly Report Generator]
```

See [`docs/architecture.md`](docs/architecture.md) and
[`docs/filebeat-logstash.md`](docs/filebeat-logstash.md) for details.

## Quick Start (local)

The full pipeline — Cowrie → Filebeat → Logstash → OpenSearch → Dashboards —
runs locally with Docker Compose:

```bash
./scripts/run_local.sh
```

`run_local.sh` brings up OpenSearch, installs the index template, imports the
dashboards (`./scripts/bootstrap_opensearch.sh`), seeds sample data, then starts
Logstash + Cowrie + Filebeat.

- Dashboards:  http://localhost:5601  (Threat Overview)
- OpenSearch:  http://localhost:9200
- Poke the honeypot:  `ssh -p 2222 root@localhost`

Run the Python test suites without Docker:

```bash
cd reports           && pip install -r requirements-dev.txt && pytest
cd sensors/http-trap && pip install -r requirements-dev.txt && pytest
```

Validate the Logstash pipeline:

```bash
docker run --rm ghcr.io/openthreatgrid/otg-logstash:main \
  logstash -t -f /usr/share/logstash/pipeline/otg.conf
```

See [`docs/deployment-guide.md`](docs/deployment-guide.md) for Kubernetes/Helm
and production bring-up.

## Repository Layout

```text
openthreatgrid/
├── sensors/                Cowrie, OpenCanary, HTTP trap (+ mmproxy) images/config
├── deploy/filebeat-logstash/  Logstash image (oss + opensearch output) + pipeline + filebeat config
├── reports/                Weekly Jinja2 threat-intel report generator (reads OpenSearch)
├── opensearch/             Index template + Dashboards saved objects (NDJSON)
├── deploy/
│   ├── edge/               DO VPS: HAProxy + Tailscale + UFW bootstrap
│   ├── k8s/                Namespace, Traefik, OpenSearch, Dashboards, Logstash,
│   │                       sensors (Filebeat sidecars), reports, NetworkPolicies, kustomize
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

- `cowrie` (sensor + Filebeat sidecar)
- `logstash`
- `opensearch`
- `opensearch-dashboards`

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
