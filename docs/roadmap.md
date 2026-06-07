# OpenThreatGrid Roadmap

## Phase 0: Project Foundation

Goal: prepare the repository for public open-source development.

Deliverables:

- README.md
- LICENSE
- SECURITY.md
- CONTRIBUTING.md
- CODE_OF_CONDUCT.md
- Basic documentation structure
- Initial architecture diagram
- MVP scope definition

## Phase 1: Cowrie Sensor MVP

Goal: run the first honeypot sensor safely on Kubernetes.

Deliverables:

- Cowrie deployment manifest
- Dedicated Kubernetes namespace
- Basic NetworkPolicy
- Persistent volume for logs
- Sample Cowrie log events
- Sensor operation guide

Success criteria:

- Cowrie runs in Kubernetes.
- Logs are generated and accessible.
- Sensor is isolated from production workloads.

## Phase 2: Parser and Event Schema

Goal: normalize Cowrie events into OpenThreatGrid event format.

Deliverables:

- Cowrie log parser
- Normalized event schema
- Example JSON events
- Unit tests for common Cowrie event types

Supported initial event types:

- SSH login attempt
- Failed authentication
- Successful honeypot login
- Command execution
- File download attempt
- Session close

## Phase 3: Ingestion pipeline

Goal: normalize + enrich sensor logs into OpenSearch (topology A).

Deliverables:

- Filebeat (sidecar) shipping sensor logs
- Logstash pipeline (normalize + enrich + GeoIP)
- OpenSearch index template (`otg-events-*`)
- Logstash image (oss + opensearch output) + Kubernetes manifests

## Phase 4: Dashboard

Goal: make the telemetry visible for portfolio and operational use.

Deliverables:

- OpenSearch Dashboards (Threat Overview)
- Attack timeline panel
- Top source IP panel
- Top usernames panel
- Top passwords panel
- Top commands panel
- Daily event count panel

## Phase 5: Weekly Report Generator

Goal: transform telemetry into readable intelligence reports.

Deliverables:

- Markdown report template
- Weekly report generator script
- Sample public report
- Report automation plan

Initial report sections:

- Executive summary
- Event volume
- Top attack sources
- Top usernames and passwords
- Suspicious commands
- Malware delivery attempts
- Suspected botnet patterns
- Defensive recommendations

## Phase 6: Enrichment

Goal: enrich events with useful context.

Possible enrichments:

- GeoIP country
- ASN
- Reverse DNS
- Known scanner tag
- Known cloud provider tag
- Basic IoC extraction from commands

## Phase 7: Multi-sensor Support

Goal: support more honeypot types.

Candidate sensors:

- Dionaea
- Honeytrap
- Conpot
- HTTP fake login honeypot
- Custom TCP trap

## Phase 8: Public Portfolio Release

Goal: make the project presentable as a professional cybersecurity portfolio project.

Deliverables:

- Public demo screenshots
- Architecture documentation
- Deployment guide
- Sample reports
- Security and data policy
- Blog post or project write-up

## Phase 9: Community and Collaboration

Goal: prepare for responsible community participation.

Deliverables:

- Contributor guide
- Sensor registration model
- Data anonymization policy
- Public/private data separation
- Shadowserver collaboration proposal
