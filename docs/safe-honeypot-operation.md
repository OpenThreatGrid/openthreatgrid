# Safe Honeypot Operation

Honeypots attract malicious traffic. They must be operated safely and ethically.

## Core Rules

1. Do not run honeypots inside a production network.
2. Use a dedicated Kubernetes namespace.
3. Apply NetworkPolicy restrictions.
4. Restrict outbound traffic from honeypot pods.
5. Do not store unnecessary personal data.
6. Do not publish raw sensitive logs.
7. Do not execute downloaded malware on the main cluster.
8. Store malware binaries only in a dedicated isolated lab.
9. Prefer storing metadata, URLs, hashes, and commands.
10. Monitor sensor behavior continuously.

## Recommended Isolation

```text
Internet-facing honeypot
        |
        v
Dedicated namespace
        |
        v
Restricted outbound to API only
        |
        v
Aggregated analysis storage
```

## Data Handling

Safe to store for MVP:

- Timestamp
- Sensor ID
- Source IP
- Destination port
- Protocol
- Username/password attempts
- Commands typed into honeypot
- Malware download URLs
- Hashes
- Event type

Handle carefully:

- Source IP addresses
- Full payloads
- Files downloaded by attackers
- Credentials typed by attackers
- Any accidental third-party data

## Public Reporting Rules

Public dashboards and reports should prefer aggregated data:

- Top countries instead of raw IP lists
- Top ASNs instead of raw IP lists
- Top usernames/passwords
- Top commands
- Event counts over time
- Malware URL domains, only when safe

Avoid publishing:

- Full raw logs
- Full attacker payloads that enable abuse
- Malware binaries
- Internal infrastructure details
- Secrets or tokens
