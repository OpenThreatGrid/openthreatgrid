# Sensor Integration

OpenThreatGrid is multi-sensor. Every sensor flows through the same pipeline —
only the **Logstash mapping branch** (sensor log → OTG event) differs:

```
Sensor → <sensor>.log → Filebeat (log_type=<type>) → Logstash → OpenSearch
```

A Filebeat sidecar in each sensor pod tags lines with `log_type`; the single
Logstash pipeline branches on it to normalize that sensor's records.

## Supported sensors

| Sensor | `log_type` | Notes |
|---|---|---|
| Cowrie | `cowrie` | SSH/Telnet (MVP sensor) |
| OpenCanary | `opencanary` | Multi-service deception (SSH/Telnet/FTP/HTTP/…); events tagged `deception` |
| HTTP trap | `http-trap` | Custom fake admin login + canary files; see [Deception Features](deception-features.md) |

The mapping lives in one place:
[`deploy/filebeat-logstash/logstash/pipeline/otg.conf`](../deploy/filebeat-logstash/logstash/pipeline/otg.conf).

## Running a sensor

Each sensor pod runs the honeypot plus a **Filebeat sidecar** (shared log
volume) configured by env: `LOG_TYPE`, `LOG_PATH`, `SENSOR_ID` (see
`deploy/k8s/filebeat/configmap.yaml`).

- **Cowrie** ships by default.
- **OpenCanary / HTTP trap:** opt-in — uncomment them in
  [`deploy/k8s/kustomization.yaml`](../deploy/k8s/kustomization.yaml), or Helm
  `--set opencanary.enabled=true` / `--set httpTrap.enabled=true`.

The sensor pod's NetworkPolicy permits egress only to Logstash (`:5044`) + DNS —
no outbound internet.

## Adding a new sensor

1. **Emit JSON logs** from the sensor to a file.
2. **Package it** under `sensors/<sensor>/` (Dockerfile + config) and add it to
   the `docker-build.yml` image matrix.
3. **Add a Filebeat sidecar** to its Deployment with `LOG_TYPE=<type>` and
   `LOG_PATH` pointing at the log (mirror `deploy/k8s/cowrie/deployment.yaml`),
   plus an isolation NetworkPolicy (egress to Logstash + DNS only).
4. **Add a Logstash branch** in `otg.conf`: `else if [log_type] == "<type>"`
   that maps the sensor's fields to the OTG schema (set `sensor_type`, a valid
   `event_type`, source/dest fields, and `ts_raw`). The shared section handles
   `event_id`, time, GeoIP, tagging, and output.

The dashboards split by `sensor_type` (Sensor Health, Source IP Intelligence), so
a new sensor appears without dashboard changes.

> **Dionaea** (malware-capture, v0.6 roadmap) is not yet integrated — its logging
> (SQLite / multiple sinks) needs a small JSON shipper before the file-tail
> pattern fits. Tracked as follow-up.

## Safety

Treat every sensor like Cowrie: run isolated, **block all outbound internet**
with NetworkPolicy, never store real credentials, and publish only aggregated or
sanitized intelligence. See [Safe Honeypot Operation](safe-honeypot-operation.md).
