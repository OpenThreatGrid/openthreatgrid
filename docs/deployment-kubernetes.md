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
opensearch
opensearch-dashboards
```

## Resource Planning

Suggested MVP resource requests:

```text
cowrie-sensor   500m CPU   512Mi RAM
api             250m CPU   256Mi RAM
worker          250m CPU   256Mi RAM
opensearch      500m CPU   1.5Gi RAM
dashboards      250m CPU   512Mi RAM
```

Suggested MVP resource limits:

```text
cowrie-sensor   1 CPU      1Gi RAM
api             500m CPU   512Mi RAM
worker          500m CPU   512Mi RAM
opensearch      2 CPU      2Gi RAM
dashboards      1 CPU      1Gi RAM
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
- Expose OpenSearch Dashboards behind authentication; never expose OpenSearch
  (`:9200`) directly.
- Keep the API internal unless remote sensors are used.

## Future Helm Chart

A Helm chart will later manage:

- Configurable sensor deployment
- API deployment
- Worker deployment
- OpenSearch settings (storage, JVM heap, security)
- OpenSearch Dashboards saved-object provisioning
- NetworkPolicy templates
