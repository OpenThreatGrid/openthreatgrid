# OpenThreatGrid Architecture

OpenThreatGrid is a Kubernetes-native honeynet and threat intelligence platform. It collects attack telemetry from honeypot sensors, normalizes the data, stores it, visualizes it, and generates intelligence reports.

## High-level Architecture

```text
Internet
   |
   v
+-----------------------+
| Honeypot Sensor Layer |
| - Cowrie              |
| - Dionaea             |
| - HTTP trap           |
+-----------------------+
   |
   v
+-----------------------+
| Parser / Log Shipper  |
| - Read raw logs       |
| - Normalize events    |
| - Send to API         |
+-----------------------+
   |
   v
+-----------------------+
| Ingestion API         |
| - FastAPI             |
| - Auth token          |
| - Event validation    |
+-----------------------+
   |
   v
+-----------------------+
| Storage Layer         |
| - PostgreSQL MVP      |
| - ClickHouse future   |
+-----------------------+
   |
   +---------------------> Grafana Dashboard
   |
   +---------------------> Weekly Report Generator
   |
   +---------------------> Threat Hunting Queries
```

## Component Overview

### 1. Honeypot Sensor Layer

The sensor layer contains one or more honeypots exposed to the internet. The MVP starts with Cowrie because it is useful for collecting SSH and Telnet brute-force activity.

Initial sensor:

- Cowrie SSH/Telnet honeypot

Future sensors:

- Dionaea for malware delivery attempts
- Conpot for ICS-style telemetry
- Honeytrap for multi-protocol traps
- Custom HTTP fake login honeypot

### 2. Parser / Log Shipper

The parser reads raw logs from honeypot sensors and converts them into OpenThreatGrid's normalized event schema.

Responsibilities:

- Read raw JSON logs.
- Map sensor-specific fields into common fields.
- Tag events.
- Remove unnecessary sensitive data.
- Send normalized events to the ingestion API.

### 3. Ingestion API

The API validates incoming events and writes them to storage.

Initial stack:

- Python
- FastAPI
- Pydantic
- PostgreSQL

Initial endpoints:

```text
POST /api/v1/events
GET  /api/v1/events
GET  /api/v1/stats/summary
GET  /api/v1/stats/top-usernames
GET  /api/v1/stats/top-passwords
GET  /api/v1/stats/top-commands
```

### 4. Storage Layer

The MVP uses PostgreSQL to keep the system simple.

Future improvement:

- Move high-volume event storage to ClickHouse.
- Keep PostgreSQL for configuration, users, sensors, and metadata.

### 5. Dashboard Layer

The initial dashboard uses Grafana connected to PostgreSQL.

Panels:

- Total events
- Events over time
- Top source IPs
- Top usernames
- Top passwords
- Top commands
- Malware URL attempts
- Sensor health

### 6. Report Generator

The report generator creates weekly Markdown reports from stored telemetry.

Report output:

- `reports/generated/YYYY-WW-weekly-threat-report.md`

Possible future output:

- HTML report
- PDF report
- GitHub release note
- Blog post template

## Kubernetes Layout

Recommended namespace:

```text
otg-system
```

Initial workloads:

```text
otg-cowrie-sensor
otg-api
otg-worker
postgres
grafana
```

## Security Architecture

Core safety controls:

- Dedicated namespace for honeypot workloads.
- NetworkPolicy to restrict outbound traffic.
- Separate service accounts.
- No access to production secrets.
- No shared hostPath unless strictly required.
- Raw malware binaries disabled by default.
- Dashboard exposes aggregated data only.

## Data Flow

1. Attacker connects to Cowrie.
2. Cowrie writes a raw event log.
3. Parser reads the raw event.
4. Parser normalizes and tags the event.
5. API receives the event.
6. API validates and stores the event.
7. Dashboard queries aggregated statistics.
8. Report generator creates weekly intelligence output.

## MVP Design Decision

OpenThreatGrid intentionally starts small:

- One sensor type.
- One database.
- One dashboard.
- One report generator.

This keeps the solo developer scope manageable while still demonstrating a complete cybersecurity platform.
