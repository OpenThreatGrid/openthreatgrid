# OpenCanary sensor

[OpenCanary](https://github.com/thinkst/opencanary) is a multi-service deception
sensor. In OpenThreatGrid it runs as a second honeypot alongside Cowrie and is
ingested through the same pipeline:

```
OpenCanary → opencanary.log → Filebeat (log_type=opencanary) → Logstash → OpenSearch
```

## What it captures

Enabled services in [`opencanary.conf`](opencanary.conf) (high ports so the
container runs non-root): **SSH** (2222), **Telnet** (2323), **FTP** (2121), and
a fake **HTTP** admin login (8080). Each login attempt / connection is written as
a JSON line that the Logstash `opencanary` branch
([`otg.conf`](../../deploy/filebeat-logstash/logstash/pipeline/otg.conf)) maps to
the OTG schema with `sensor_type: "opencanary"` and a `deception` tag.

Other OpenCanary services (MySQL, MSSQL, VNC, RDP, …) are disabled by default;
the Logstash logtype map already understands them, so enabling them in the config
is enough.

## Run

The sensor shares a log volume with a Filebeat sidecar configured for OpenCanary
(`LOG_TYPE=opencanary`, `LOG_PATH=/var/log/opencanary/opencanary.log`).

See [`deploy/k8s/opencanary/`](../../deploy/k8s/opencanary/) for the Kubernetes
deployment (sensor + Filebeat sidecar sharing an `emptyDir`), and
[`docs/sensor-integration.md`](../../docs/sensor-integration.md) for the pattern
to add further sensors.

> The Dockerfile installs OpenCanary from PyPI; pin a version and rebuild if you
> need reproducible images. Keep the sensor isolated (NetworkPolicy: no outbound
> internet) just like Cowrie.
