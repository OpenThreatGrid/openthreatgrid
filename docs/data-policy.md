# Data Policy

OpenThreatGrid collects honeypot telemetry for defensive security research and threat intelligence.

## Data Collected

The MVP may collect:

- Timestamp
- Sensor ID
- Sensor type
- Source IP address
- Destination port
- Protocol
- Event type
- Username and password attempts
- Commands executed in the honeypot
- Malware download URLs
- File hashes, when available
- Raw event data, when needed for debugging

## Data Minimization

The project should collect only what is required for:

- Attack trend analysis
- Threat hunting
- Botnet pattern detection
- Malware delivery tracking
- Defensive reporting

## Public Data

Public outputs should be aggregated or sanitized.

Examples of acceptable public outputs:

- Total event counts
- Top usernames
- Top passwords
- Top ports
- Top commands
- Event timeline
- Country-level statistics
- High-level botnet patterns

## Restricted Data

The following should not be published by default:

- Raw logs
- Full source IP lists
- Malware binaries
- Secrets or tokens
- Sensitive infrastructure details
- Data that could harm third parties

## Retention

Suggested MVP retention:

- Raw events: 30 days
- Normalized events: 90 days
- Aggregated statistics: 1 year
- Public reports: indefinite

Retention should be configurable.
