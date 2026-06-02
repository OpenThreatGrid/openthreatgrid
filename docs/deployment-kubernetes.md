# Kubernetes Deployment Guide

This document describes the planned Kubernetes deployment model for OpenThreatGrid MVP.

## Recommended Cluster

Minimum for development:

```text
4 CPU cores
8 GB RAM
50 GB storage
```

Recommended for public-facing MVP:

```text
8-12 CPU cores
12-16 GB RAM
100+ GB storage
```

The author's available cluster target:

```text
32 CPU cores
32 GB RAM
```

## Namespace

```bash
kubectl create namespace otg-system
```

## Planned Services

```text
otg-cowrie-sensor
otg-api
otg-worker
postgres
grafana
```

## Resource Planning

Suggested MVP resource requests:

```text
cowrie-sensor   500m CPU   512Mi RAM
api             500m CPU   512Mi RAM
worker          500m CPU   512Mi RAM
postgres        1 CPU      2Gi RAM
grafana         250m CPU   512Mi RAM
```

Suggested MVP resource limits:

```text
cowrie-sensor   1 CPU      1Gi RAM
api             1 CPU      1Gi RAM
worker          1 CPU      1Gi RAM
postgres        4 CPU      8Gi RAM
grafana         1 CPU      1Gi RAM
```

## Network Policy

Honeypot pods should be restricted carefully:

- Allow inbound traffic only to exposed honeypot ports.
- Allow outbound only to the API or log collector.
- Deny access to Kubernetes API from honeypot pods unless required.
- Deny access to internal namespaces.

## Exposure Model

For MVP:

- Expose Cowrie using a LoadBalancer or NodePort mapped to SSH/Telnet-like ports.
- Expose Grafana behind authentication.
- Keep the API internal unless remote sensors are used.

## Future Helm Chart

A Helm chart will later manage:

- Configurable sensor deployment
- API deployment
- Worker deployment
- PostgreSQL or external DB settings
- Grafana dashboard provisioning
- NetworkPolicy templates
